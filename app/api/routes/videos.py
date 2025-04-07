from typing import List, Any, Dict
import uuid
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from app.core.logger import get_logger

logger = get_logger("videos")

from app.api.deps import get_db, has_permission, get_current_verified_user
from app.core.exceptions import VideoNotValidatedException, VideoServiceException, VideoGenerationException, DomainException, map_domain_exception_to_http
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
    """Cria um novo vídeo
    
    Args:
        db: Sessão do banco de dados
        video_in: Dados do vídeo a ser criado
        current_user: Usuário com permissão para criar vídeos
        
    Returns:
        O vídeo criado
        
    Raises:
        HTTPException: Quando ocorre um erro na validação dos dados ou na criação do vídeo
    """
    
    from app.services.video_service import create_video as create_video_service
    from app.services.credit_service import InsufficientCreditsException
    
    # Armazena o ID do usuário no início da função para evitar problemas de acesso após falhas no banco de dados
    user_id = getattr(current_user, 'id', None)
    user_email = getattr(current_user, 'email', None)
    request_id = str(uuid.uuid4())
    
    logger.info(
        "Iniciando criação de vídeo",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "user_email": user_email,
            "video_title": getattr(video_in, 'title', None),
            "video_duration": getattr(video_in, 'duration', None),
            "operation": "create_video"
        }
    )
    
    try:
        # Recarrega o usuário da sessão para garantir que os atributos estejam atualizados
        current_user = db.merge(current_user)
        db.refresh(current_user)
        
        # Delega a criação do vídeo para o serviço
        video = create_video_service(db, video_in, current_user)
        
        logger.info(
            "Vídeo criado com sucesso",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "video_id": video.id,
                "operation": "create_video_success"
            }
        )
        
        return video
    except RequestValidationError as e:
        # Tratamento específico para erros de validação
        logger.warning(
            "Erro de validação ao criar vídeo",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "validation_errors": e.errors(),
                "operation": "create_video_validation_error"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "invalid_input",
                "message": "Dados de entrada inválidos",
                "errors": e.errors()
            }
        )
    except InsufficientCreditsException as e:
        # Tratamento específico para créditos insuficientes
        logger.warning(
            "Créditos insuficientes para criar vídeo",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "user_email": user_email,
                "operation": "create_video_insufficient_credits"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "insufficient_credits",
                "message": "Créditos insuficientes para criar o vídeo",
                "detail": str(e)
            }
        )
    except VideoNotValidatedException as e:
        # Tratamento específico para vídeos não validados
        logger.warning(
            "Vídeo não validado",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "error_message": str(e),
                "operation": "create_video_not_validated"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "video_not_validated",
                "message": "O vídeo não pôde ser validado",
                "detail": str(e)
            }
        )
    except VideoGenerationException as e:
        # Tratamento específico para erros na geração do vídeo
        error_id = getattr(e, 'error_id', str(uuid.uuid4()))
        logger.error(
            "Erro na geração do vídeo",
            extra={
                "request_id": request_id,
                "error_id": error_id,
                "user_id": user_id,
                "error_message": str(e),
                "operation": "create_video_generation_error"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "video_generation_failed",
                "message": "Falha na geração do vídeo",
                "error_id": error_id
            }
        )
    except DomainException as e:
        # Mapeia outras exceções de domínio para exceções HTTP
        logger.warning(
            "Exceção de domínio ao criar vídeo",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "operation": "create_video_domain_exception"
            }
        )
        raise map_domain_exception_to_http(e)
    except Exception as e:
        # Tratamento genérico para outros erros não esperados
        error_id = str(uuid.uuid4())
        error_stack = traceback.format_exc()
        logger.error(
            "Erro não tratado ao criar vídeo",
            extra={
                "request_id": request_id,
                "error_id": error_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_stack": error_stack,
                "user_id": user_id,
                "user_email": user_email,
                "operation": "create_video_unhandled_error"
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

@router.get("/", response_model=Dict[str, Any])
def get_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    skip: int = 0,
    limit: int = 100,
    order_by: str = "id",
    order_direction: str = "desc"
) -> Any:
    """Obtém todos os vídeos do usuário atual com paginação e ordenação
    
    Args:
        db: Sessão do banco de dados
        current_user: Usuário autenticado atual
        skip: Número de registros para pular (para paginação)
        limit: Número máximo de registros a retornar
        order_by: Campo para ordenação (id, title, created_at)
        order_direction: Direção da ordenação (asc, desc)
        
    Returns:
        Dicionário contendo a lista de vídeos e metadados de paginação
    """
    request_id = str(uuid.uuid4())
    user_id = getattr(current_user, 'id', None)
    user_email = getattr(current_user, 'email', None)
    
    logger.info(
        "Listando vídeos do usuário",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "user_email": user_email,
            "skip": skip,
            "limit": limit,
            "order_by": order_by,
            "order_direction": order_direction,
            "operation": "list_videos"
        }
    )
    
    try:
        # Recarrega o usuário da sessão para garantir que os atributos estejam atualizados
        current_user = db.merge(current_user)
        db.refresh(current_user)
        
        # Validação dos parâmetros de ordenação
        valid_order_fields = {"id": Video.id, "title": Video.title, "created_at": Video.data_registro}
        valid_directions = {"asc": "asc", "desc": "desc"}
        
        # Usa valores padrão se os parâmetros não forem válidos
        order_field = valid_order_fields.get(order_by.lower(), Video.id)
        direction = valid_directions.get(order_direction.lower(), "desc")
        
        # Aplica a ordenação conforme a direção
        if direction == "desc":
            order_clause = order_field.desc()
        else:
            order_clause = order_field.asc()
        
        # Consulta base com filtro por usuário
        base_query = db.query(Video).filter(Video.user_id == current_user.id)
        
        # Contagem total de registros para metadados de paginação
        total_count = base_query.count()
        
        # Consulta com filtro, paginação e ordenação
        videos = base_query.order_by(order_clause).offset(skip).limit(limit).all()
        
        # Calcula metadados de paginação
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        logger.info(
            "Vídeos listados com sucesso",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "total_videos": total_count,
                "operation": "list_videos_success"
            }
        )
        
        # Converte os objetos Video do SQLAlchemy para o schema VideoSchema antes de retornar
        # Usando o método correto para Pydantic v2
        video_schemas = [VideoSchema.model_validate(video, from_attributes=True) for video in videos]
        
        # Retorna os resultados com metadados de paginação
        return {
            "items": video_schemas,
            "pagination": {
                "total": total_count,
                "page": current_page,
                "pages": total_pages,
                "size": limit
            }
        }
    except Exception as e:
        # Tratamento genérico para erros não esperados
        error_id = str(uuid.uuid4())
        error_stack = traceback.format_exc()
        logger.error(
            "Erro não tratado ao listar vídeos",
            extra={
                "request_id": request_id,
                "error_id": error_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_stack": error_stack,
                "user_id": user_id,
                "user_email": user_email,
                "operation": "list_videos_unhandled_error"
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

@router.get("/{video_id}", response_model=VideoSchema)
def get_video(
    *,
    db: Session = Depends(get_db),
    video_id: str,
    current_user: User = Depends(get_current_verified_user)
) -> Any:
    """Obtém um vídeo específico pelo ID ou UID
    
    Args:
        db: Sessão do banco de dados
        video_id: ID ou UID do vídeo a ser obtido
        current_user: Usuário autenticado atual
        
    Returns:
        O vídeo solicitado
        
    Raises:
        HTTPException: Quando o vídeo não é encontrado ou ocorre outro erro
    """
    request_id = str(uuid.uuid4())
    user_id = getattr(current_user, 'id', None)
    user_email = getattr(current_user, 'email', None)
    
    logger.info(
        "Buscando vídeo por ID ou UID",
        extra={
            "request_id": request_id,
            "video_id": video_id,
            "user_id": user_id,
            "operation": "get_video"
        }
    )
    
    try:
        # Recarrega o usuário da sessão para garantir que os atributos estejam atualizados
        current_user = db.merge(current_user)
        db.refresh(current_user)
        
        # Tenta converter para inteiro para compatibilidade com IDs numéricos
        try:
            numeric_id = int(video_id)
            video = db.query(Video).filter(Video.id == numeric_id, Video.user_id == current_user.id).first()
        except ValueError:
            # Se não for um número, assume que é um UID
            video = db.query(Video).filter(Video.uid == video_id, Video.user_id == current_user.id).first()
        if not video:
            logger.warning(
                "Vídeo não encontrado",
                extra={
                    "request_id": request_id,
                    "video_id": video_id,
                    "user_id": user_id,
                    "operation": "get_video_not_found"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "video_not_found",
                    "message": "Vídeo não encontrado"
                }
            )
            
        logger.info(
            "Vídeo encontrado com sucesso",
            extra={
                "request_id": request_id,
                "video_id": video_id,
                "user_id": user_id,
                "operation": "get_video_success"
            }
        )
        return video
    except HTTPException:
        # Re-lança exceções HTTP já tratadas
        raise
    except Exception as e:
        # Tratamento genérico para outros erros não esperados
        error_id = str(uuid.uuid4())
        error_stack = traceback.format_exc()
        logger.error(
            "Erro não tratado ao buscar vídeo",
            extra={
                "request_id": request_id,
                "error_id": error_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_stack": error_stack,
                "video_id": video_id,
                "user_id": user_id,
                "user_email": user_email,
                "operation": "get_video_unhandled_error"
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


@router.get("/download/{video_guid}")
def download_video(
    *,
    db: Session = Depends(get_db),
    video_guid: str,
    current_user: User = Depends(get_current_verified_user)
) -> Any:
    """Gera um link de download para um vídeo específico
    
    Args:
        db: Sessão do banco de dados
        video_guid: UID do vídeo a ser baixado
        current_user: Usuário autenticado atual
        
    Returns:
        Um objeto com a URL de download do vídeo
        
    Raises:
        HTTPException: Quando o vídeo não é encontrado ou ocorre outro erro
    """
    request_id = str(uuid.uuid4())
    user_id = getattr(current_user, 'id', None)
    user_email = getattr(current_user, 'email', None)
    
    logger.info(
        "Gerando link de download para vídeo",
        extra={
            "request_id": request_id,
            "video_guid": video_guid,
            "user_id": user_id,
            "operation": "download_video"
        }
    )
    
    try:
        # Recarrega o usuário da sessão para garantir que os atributos estejam atualizados
        current_user = db.merge(current_user)
        db.refresh(current_user)
        
        # Verifica se o vídeo existe e pertence ao usuário atual
        video = db.query(Video).filter(Video.guid == video_guid, Video.user_id == current_user.id).first()
        if not video:
            logger.warning(
                "Vídeo não encontrado para download",
                extra={
                    "request_id": request_id,
                    "video_guid": video_guid,
                    "user_id": user_id,
                    "operation": "download_video_not_found"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "video_not_found",
                    "message": "Vídeo não encontrado"
                }
            )
        
        # Importa o serviço de vídeo para gerar a URL de download
        from app.services.video_service import get_video_download_url
        
        # Gera a URL de download
        download_url = get_video_download_url(db, video_guid, current_user.id)
        
        if not download_url:
            logger.warning(
                "Não foi possível gerar URL de download para o vídeo",
                extra={
                    "request_id": request_id,
                    "video_guid": video_guid,
                    "user_id": user_id,
                    "operation": "download_video_url_generation_failed"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "download_url_generation_failed",
                    "message": "Não foi possível gerar o link de download para este vídeo"
                }
            )
        
        logger.info(
            "URL de download gerada com sucesso",
            extra={
                "request_id": request_id,
                "video_guid": video_guid,
                "user_id": user_id,
                "operation": "download_video_success"
            }
        )
        
        # Retorna a URL de download
        return {
            "download_url": download_url,
            "expires_in": "24 horas"
        }
    except HTTPException:
        # Re-lança exceções HTTP já tratadas
        raise
    except Exception as e:
        # Tratamento genérico para outros erros não esperados
        error_id = str(uuid.uuid4())
        error_stack = traceback.format_exc()
        logger.error(
            "Erro não tratado ao gerar link de download",
            extra={
                "request_id": request_id,
                "error_id": error_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_stack": error_stack,
                "video_guid": video_guid,
                "user_id": user_id,
                "user_email": user_email,
                "operation": "download_video_unhandled_error"
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