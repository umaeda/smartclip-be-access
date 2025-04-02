from typing import Optional, Dict, Any
import uuid

from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from app.models.video import Video
from app.models.user import User
from app.schemas.video import VideoCreate
from app.core.exceptions import VideoNotValidatedException, VideoGenerationException
from app.core.logger import get_logger
from app.services.credit_service import consume_credit, refund_credit, InsufficientCreditsException

logger = get_logger("video_service")


def generate_video(assunto: str, duracao_segundos: int) -> Optional[str]:
    """
    Gera um vídeo com base no assunto e duração fornecidos.
    Retorna a URL do vídeo gerado ou None em caso de falha.
    
    Esta é uma implementação mockada inicial que sempre retorna uma URL fixa.
    """
    # TODO: Implementar lógica real de geração de vídeo
    return "https://example.com/video/mock"


def create_video(db: Session, video_in: VideoCreate, current_user: User) -> Video:
    """
    Cria um novo vídeo no sistema.
    
    Args:
        db: Sessão do banco de dados
        video_in: Dados do vídeo a ser criado
        current_user: Usuário atual que está criando o vídeo
        
    Returns:
        Video: O objeto de vídeo criado
        
    Raises:
        VideoNotValidatedException: Se o vídeo não for validado
        InsufficientCreditsException: Se o usuário não tiver créditos suficientes
        RequestValidationError: Se os dados de entrada forem inválidos
        HTTPException: Para outros erros internos
    """
    # Variável para controlar se o crédito foi consumido
    credit_consumed = False
    transaction_id = None
    
    # Tratamento específico para InsufficientCreditsException
    # Esta exceção deve ser propagada diretamente, sem ser capturada pelo bloco genérico
    try:
        # Verifica e consome um crédito do usuário
        try:
            credit, transaction = consume_credit(db, current_user.id)
            credit_consumed = True
            transaction_id = transaction.id
            
            logger.info(
                "Crédito consumido para geração de vídeo",
                extra={
                    "user_id": current_user.id,
                    "user_email": current_user.email,
                    "transaction_id": transaction.id,
                    "remaining_balance": credit.balance,
                    "operation": "create_video"
                }
            )
            
            try:
                # Gera o vídeo usando o serviço
                video_url = generate_video(video_in.title, video_in.duration)
                
                # Create video object
                video = Video(
                    title=video_in.title,
                    description=video_in.description,
                    url=video_url,
                    is_validated=True,
                    user_id=current_user.id
                )
                
                db.add(video)
                db.commit()
                db.refresh(video)
                
                logger.info(
                    "Video criado com sucesso",
                    extra={
                        "video_id": video.id,
                        "user_id": current_user.id,
                        "user_email": current_user.email,
                        "video_title": video.title,
                        "operation": "create_video"
                    }
                )
            
                # Business logic: Raise exception if video is not validated
                if not video.is_validated:
                    logger.warning(
                        "Video não validado",
                        extra={
                            "video_id": video.id,
                            "validation_status": video.is_validated,
                            "user_id": current_user.id,
                            "operation": "video_validation"
                        }
                    )
                    # Estorna o crédito se o vídeo não for validado
                    refund_credit(db, current_user.id, description=f"Estorno por vídeo não validado (ID: {video.id})")
                    logger.info(
                        "Crédito estornado por vídeo não validado",
                        extra={
                            "user_id": current_user.id,
                            "video_id": video.id,
                            "operation": "refund_credit"
                        }
                    )
                    # Marca que o crédito já foi estornado para evitar estorno duplo
                    credit_consumed = False
                    raise VideoNotValidatedException()
                    
            except Exception as video_error:
                # Se ocorrer um erro na geração do vídeo após o consumo do crédito, estorna o crédito
                if credit_consumed:
                    refund_credit(db, current_user.id, description="Estorno por falha na geração de vídeo")
                    logger.info(
                        "Crédito estornado por falha na geração de vídeo",
                        extra={
                            "user_id": current_user.id,
                            "transaction_id": transaction_id,
                            "operation": "refund_credit"
                        }
                    )
                # Re-lança a exceção original
                raise video_error
                
        except InsufficientCreditsException as e:
            logger.warning(
                "Tentativa de criar vídeo sem créditos suficientes",
                extra={
                    "user_id": current_user.id,
                    "user_email": current_user.email,
                    "operation": "create_video_insufficient_credits"
                }
            )
            # Propaga a exceção diretamente para o controlador
            raise
        
        return video
    except RequestValidationError as e:
        logger.warning(
            "Validação falhou",
            extra={
                "validation_errors": e.errors(),
                "user_id": current_user.id,
                "operation": "create_video"
            }
        )
        raise
    except InsufficientCreditsException:
        # Propaga a exceção de créditos insuficientes sem modificá-la
        raise
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro interno ao processar vídeo",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": current_user.id,
                "video_title": video_in.title,
                "video_duration": video_in.duration,
                "operation": "create_video"
            }
        )
        raise VideoGenerationException(
            detail="Falha na geração do vídeo",
            error_id=error_id
        )