from typing import Dict, Any
import uuid
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.logger import get_logger

logger = get_logger("assistir")

from app.api.deps import get_db, get_current_verified_user
from app.models.user import User
from app.models.video import Video

router = APIRouter()

@router.get("/{video_guid}")
def assistir_video(
    video_guid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
) -> Dict[str, Any]:
    """Gera um link de streaming para um vídeo específico
    
    Args:
        video_guid: GUID do vídeo
        db: Sessão do banco de dados
        current_user: Usuário autenticado atual
        
    Returns:
        Um objeto com a URL de streaming do vídeo
        
    Raises:
        HTTPException: Se o vídeo não for encontrado ou se ocorrer um erro ao gerar a URL
    """
    request_id = str(uuid.uuid4())
    user_id = getattr(current_user, 'id', None)
    user_email = getattr(current_user, 'email', None)
    
    logger.info(
        "Gerando link de streaming para vídeo",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "user_email": user_email,
            "video_guid": video_guid,
            "operation": "assistir_video"
        }
    )
    
    try:
        # Recarrega o usuário da sessão para garantir que os atributos estejam atualizados
        current_user = db.merge(current_user)
        db.refresh(current_user)
        
        # Verifica se o vídeo existe e pertence ao usuário
        video = db.query(Video).filter(Video.guid == video_guid, Video.user_id == current_user.id).first()
        
        if not video:
            logger.warning(
                "Vídeo não encontrado para streaming",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "video_guid": video_guid,
                    "operation": "assistir_video_not_found"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "video_not_found",
                    "message": "Vídeo não encontrado"
                }
            )
        
        # Importa o serviço de vídeo para gerar a URL de streaming
        from app.services.video_service import get_video_streaming_url
        
        # Gera a URL de streaming
        streaming_url = get_video_streaming_url(db, video_guid, current_user.id)
        
        if not streaming_url:
            logger.warning(
                "Não foi possível gerar URL de streaming para o vídeo",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "video_guid": video_guid,
                    "operation": "assistir_video_url_generation_failed"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "streaming_url_generation_failed",
                    "message": "Não foi possível gerar o link de streaming para este vídeo"
                }
            )
        
        logger.info(
            "URL de streaming gerada com sucesso",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "video_guid": video_guid,
                "operation": "assistir_video_success"
            }
        )
        
        # Retorna a URL de streaming com informações adicionais do vídeo
        return {
            "streaming_url": streaming_url,
            "video_title": video.title,
            "video_duration": video.duration,
            "video_content": video.conteudo,
            "video_hashtags": video.hashtags
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Tratamento genérico para outros erros não esperados
        error_id = str(uuid.uuid4())
        error_stack = traceback.format_exc()
        logger.error(
            "Erro não tratado ao gerar link de streaming",
            extra={
                "request_id": request_id,
                "error_id": error_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_stack": error_stack,
                "user_id": user_id,
                "user_email": user_email,
                "video_guid": video_guid,
                "operation": "assistir_video_unhandled_error"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "internal_server_error",
                "message": "Erro interno do servidor",
                "error_id": error_id
            }
        )