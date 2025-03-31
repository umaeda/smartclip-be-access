from typing import List, Any, Dict
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from app.core.logger import get_logger

logger = get_logger("videos")

from app.api.deps import get_db, has_permission, get_current_verified_user
from app.core.exceptions import VideoNotValidatedException, VideoServiceException, DomainException, map_domain_exception_to_http
from app.core.csrf import csrf_protect
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoCreate, Video as VideoSchema

router = APIRouter()



@router.post("/", response_model=VideoSchema, dependencies=[Depends(csrf_protect())])
def create_video(
    *,
    db: Session = Depends(get_db),
    video_in: VideoCreate,
    current_user: User = Depends(has_permission("criar_videos"))
) -> Any:
    """Create a new video"""
    
    from app.services.video_service import create_video as create_video_service
    
    try:
        # Delega a criação do vídeo para o serviço
        video = create_video_service(db, video_in, current_user)
        return video
    except RequestValidationError as e:
        # Tratamento específico para erros de validação
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "invalid_input",
                "message": "Dados de entrada inválidos",
                "errors": e.errors()
            }
        )
    except DomainException as e:
        # Mapeia exceções de domínio para exceções HTTP
        raise map_domain_exception_to_http(e)
    except Exception as e:
        # Tratamento genérico para outros erros não esperados
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro não tratado ao criar vídeo",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": current_user.id,
                "operation": "create_video"
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

@router.get("/", response_model=List[VideoSchema])
def get_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """Get all videos for the current user"""
    logger.info(
        "Listando vídeos do usuário",
        extra={
            "user_id": current_user.id,
            "user_email": current_user.email,
            "skip": skip,
            "limit": limit,
            "operation": "list_videos"
        }
    )
    videos = db.query(Video).filter(Video.user_id == current_user.id).offset(skip).limit(limit).all()
    return videos

@router.get("/{video_id}", response_model=VideoSchema)
def get_video(
    *,
    db: Session = Depends(get_db),
    video_id: int,
    current_user: User = Depends(get_current_verified_user)
) -> Any:
    """Get a specific video by ID"""
    logger.info(
        "Buscando vídeo por ID",
        extra={
            "video_id": video_id,
            "user_id": current_user.id,
            "operation": "get_video"
        }
    )
    video = db.query(Video).filter(Video.id == video_id, Video.user_id == current_user.id).first()
    if not video:
        logger.warning(
            "Vídeo não encontrado",
            extra={
                "video_id": video_id,
                "user_id": current_user.id,
                "operation": "get_video"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "video_not_found",
                "message": "Vídeo não encontrado"
            }
        )
    return video