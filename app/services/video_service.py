from typing import Optional, Dict, Any
import uuid
import os
import math
from datetime import datetime

from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from app.models.video import Video
from app.models.user import User
from app.schemas.video import VideoCreate
from app.core.exceptions import VideoNotValidatedException, VideoGenerationException
from app.core.logger import get_logger
from app.services.credit_service import consume_credit, refund_credit, InsufficientCreditsException

# Importações para geração de vídeo
from app.services.genvideo.core.social_post import SistemaPostsAutomaticos
from app.services.genvideo.gerador_texto import GeradorTexto
from app.services.genvideo.ag_gerador_imagem import GeradorImagens
from app.services.genvideo.gerador_narracao import GeradorNarracao
from app.services.genvideo.ag_editor_video import EditorVideo
from app.services.genvideo.ag_editor_audio import EditorAudio
from app.services.genvideo import config

# Configuração do ambiente para o ImageMagick
os.environ["IMAGEMAGICK_BINARY"] = config.IMAGEMAGICK_BINARY

logger = get_logger("video_service")


def generate_video(assunto: str, duracao_segundos: int) -> Optional[Dict[str, Any]]:
    """
    Gera um vídeo com base no assunto e duração fornecidos.
    Retorna um dicionário com informações do vídeo gerado ou None em caso de falha.
    
    Args:
        assunto: Tema ou assunto do vídeo
        duracao_segundos: Duração desejada do vídeo em segundos
        
    Returns:
        Dict[str, Any]: Dicionário com informações do vídeo gerado ou None em caso de falha
    """
    try:
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        logger.info(
            "Iniciando geração de vídeo",
            extra={
                "request_id": request_id,
                "assunto": assunto,
                "duracao": duracao_segundos,
                "operation": "generate_video",
                "component": "video_generation_start",
                "timestamp": start_time.isoformat()
            }
        )
        
        # Inicializa o sistema de posts automáticos com todos os componentes necessários
        sistema = SistemaPostsAutomaticos(
            gerador_texto=GeradorTexto(),
            gerador_imagens=GeradorImagens(),
            gerador_narracao=GeradorNarracao(),
            editor_video=EditorVideo(1080, 720),
            editor_audio=EditorAudio()
        )
        
        # Calcula a quantidade de imagens com base na duração (1 imagem a cada 10 segundos)
        qtd_imagens = math.ceil(duracao_segundos / 10)
        
        # Executa o fluxo de geração de vídeo
        # Importante: o identificador não é usado pelo sistema de geração de vídeos
        # O sistema gera seu próprio identificador internamente
        arquivo_video = sistema.executar_fluxo(
            tema=assunto, 
            modelo='gemini',  # Modelo padrão para geração de texto
            duracao=duracao_segundos, 
            qtd_imagens=qtd_imagens
        )
        
        try:
            # Carrega os dados do último registro salvo
            # O sistema de geração de vídeos salva os dados no arquivo dados.json
            from app.services.genvideo.save_data import load_data_from_json
            dados = load_data_from_json()
            print(arquivo_video)
            if dados and len(dados) > 0:
                # Pega o último registro salvo (o mais recente)
                post_data = dados[-1]
                arquivo_video = post_data["arquivo_video"]
                
                # Garante que o caminho é absoluto
                arquivo_video = os.path.abspath(arquivo_video)
                
                # Calcula o tempo de geração em segundos
                end_time = datetime.now()
                generation_time = (end_time - start_time).total_seconds()
                
                logger.info(
                    "Vídeo gerado com sucesso",
                    extra={
                        "request_id": request_id,
                        "assunto": assunto,
                        "duracao": duracao_segundos,
                        "arquivo_video": arquivo_video,
                        "tempo_geracao": generation_time,
                        "operation": "generate_video",
                        "component": "video_generation_complete",
                        "timestamp": end_time.isoformat()
                    }
                )
                
                # Retorna um dicionário com as informações do vídeo
                return {
                    "url": arquivo_video,
                    "duration": duracao_segundos,
                    "generation_time": generation_time,
                    "post_data": post_data  # Inclui os dados completos do post
                }
            else:
                error_id = str(uuid.uuid4())
                logger.error(
                    "Nenhum registro de vídeo encontrado após geração",
                    extra={
                        "request_id": request_id,
                        "error_id": error_id,
                        "assunto": assunto,
                        "duracao": duracao_segundos,
                        "operation": "generate_video",
                        "component": "video_data_validation",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                return None
        except Exception as e:
            import traceback
            error_stack = traceback.format_exc()
            error_id = str(uuid.uuid4())
            
            logger.error(
                "Erro ao recuperar dados do vídeo gerado",
                extra={
                    "request_id": request_id,
                    "error_id": error_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "error_stack": error_stack,
                    "assunto": assunto,
                    "duracao": duracao_segundos,
                    "operation": "generate_video",
                    "component": "video_data_retrieval",
                    "timestamp": datetime.now().isoformat()
                }
            )
            return None
    except Exception as e:
        import traceback
        error_stack = traceback.format_exc()
        error_id = str(uuid.uuid4())
        
        logger.error(
            "Erro ao gerar vídeo",
            extra={
                "request_id": request_id,
                "error_id": error_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_stack": error_stack,
                "assunto": assunto,
                "duracao": duracao_segundos,
                "operation": "generate_video",
                "component": "video_generation",
                "timestamp": datetime.now().isoformat()
            }
        )
        return None


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
            
            # Gera o vídeo usando o serviço
            if 1 == 2:
                from app.services.mock_data import mock_video_data
                video_result = mock_video_data("assunto", 10)
            else:
                video_result = generate_video(video_in.title, video_in.duration)
                
                if not video_result:
                    raise VideoGenerationException(detail="Falha na geração do vídeo")
                
            # Create video object com as informações adicionais
            # Extrai os dados do post_data para salvar no banco de dados
            post_data = video_result.get("post_data", {})
            
            # Cria o objeto de vídeo com os dados básicos
            video = Video(
                title=video_in.title,
                description=video_in.description,
                url=video_result["url"],  # URL local temporária
                is_validated=True,
                user_id=current_user.id,
                duration=video_result["duration"],
                generation_time=video_result["generation_time"],
                # Campos adicionais do vídeo
                solicitacao=post_data.get("solicitacao"),
                roteiro=post_data.get("roteiro"),
                frases=post_data.get("frases"),
                hashtags=post_data.get("hashtags"),
                conteudo=post_data.get("conteudo"),
                imagens=post_data.get("imagens"),
                narracao_marcada=post_data.get("narracao_marcada"),
                arquivo_narracao_raw=post_data.get("arquivo_narracao_raw"),
                arquivo_narracao_remix=post_data.get("arquivo_narracao_remix"),
                arquivo_video=post_data.get("arquivo_video")
            )
            
            # Salva o vídeo no banco de dados para obter o ID
            db.add(video)
            db.commit()
            db.refresh(video)
            
            # Faz upload do vídeo para o Azure Blob Storage
            from app.services.storage_service import upload_video_to_blob_storage
            
            # Obtém o caminho do arquivo de vídeo
            arquivo_video_path = post_data.get("arquivo_video")
            if arquivo_video_path and os.path.exists(arquivo_video_path):
                # Faz upload do vídeo para o Azure Blob Storage
                blob_url = upload_video_to_blob_storage(arquivo_video_path, video.id)
                
                if blob_url:
                    # Atualiza a URL do vídeo no banco de dados com a URL do blob
                    video.url = blob_url
                    db.commit()
                    db.refresh(video)
                    
                    logger.info(
                        "URL do vídeo atualizada com a URL do blob",
                        extra={
                            "video_id": video.id,
                            "user_id": current_user.id,
                            "operation": "upload_video_to_blob"
                        }
                    )
                else:
                    logger.warning(
                        "Falha ao fazer upload do vídeo para o Azure Blob Storage",
                        extra={
                            "video_id": video.id,
                            "user_id": current_user.id,
                            "operation": "upload_video_to_blob_failed"
                        }
                    )
            else:
                logger.warning(
                    "Arquivo de vídeo não encontrado para upload",
                    extra={
                        "video_id": video.id,
                        "arquivo_video_path": arquivo_video_path,
                        "user_id": current_user.id,
                        "operation": "upload_video_to_blob_file_not_found"
                    }
                )
            
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
        import traceback
        error_stack = traceback.format_exc()
        error_id = str(uuid.uuid4())
        
        # Preparando informações de log que são seguras de acessar
        log_extra = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "error_stack": error_stack,
            "error_id": error_id,
            "user_id": current_user.id,
            "operation": "create_video",
            "component": "video_creation",
            "timestamp": datetime.now().isoformat()
        }
        
        # Adiciona informações do vídeo se disponíveis
        if video_in:
            log_extra["video_title"] = video_in.title
            log_extra["video_duration"] = video_in.duration
        
        logger.error(
            "Erro interno ao processar vídeo",
            extra=log_extra
        )
        
        # Se o crédito foi consumido, tenta estornar
        if credit_consumed and transaction_id:
            try:
                refund_credit(db, current_user.id, description="Estorno por erro interno na geração de vídeo")
                logger.info(
                    "Crédito estornado por erro interno",
                    extra={
                        "user_id": current_user.id,
                        "transaction_id": transaction_id,
                        "operation": "refund_credit"
                    }
                )
            except Exception as refund_error:
                logger.error(
                    "Falha ao estornar crédito após erro interno",
                    extra={
                        "user_id": current_user.id,
                        "transaction_id": transaction_id,
                        "error_message": str(refund_error),
                        "operation": "refund_credit_failed"
                    }
                )
        
        raise VideoGenerationException(
            detail="Falha na geração do vídeo",
            error_id=error_id
        )


def get_video_download_url(db: Session, video_guid: str, user_id: int) -> Optional[str]:
    """
    Gera uma URL de download para um vídeo específico
    
    Args:
        db: Sessão do banco de dados
        video_guid: GUID do vídeo
        user_id: ID do usuário que está solicitando o download
        
    Returns:
        Optional[str]: URL de download do vídeo ou None se não for encontrado
        
    Raises:
        Exception: Se ocorrer um erro ao gerar a URL de download
    """
    try:
        # Busca o vídeo pelo GUID e usuário
        video = db.query(Video).filter(Video.guid == video_guid, Video.user_id == user_id).first()
        
        if not video:
            return None
        
        # Verifica se o vídeo tem uma URL do blob storage
        if not video.url or not video.url.startswith("https://"):
            return None
        
        # Gera uma URL de download temporária
        from app.services.storage_service import generate_download_url
        download_url = generate_download_url(video.url, video.id)
        
        return download_url
    except Exception as e:
        logger.error(
            "Erro ao gerar URL de download para vídeo",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "video_guid": video_guid,
                "user_id": user_id,
                "operation": "get_video_download_url"
            }
        )
        return None


def get_video_streaming_url(db: Session, video_guid: str, user_id: int) -> Optional[str]:
    """Gera uma URL de streaming para um vídeo específico
    
    Args:
        db: Sessão do banco de dados
        video_guid: GUID do vídeo
        user_id: ID do usuário que está solicitando o streaming
        
    Returns:
        Optional[str]: URL de streaming do vídeo ou None se não for encontrado
        
    Raises:
        Exception: Se ocorrer um erro ao gerar a URL de streaming
    """
    try:
        # Busca o vídeo pelo GUID e usuário
        video = db.query(Video).filter(Video.guid == video_guid, Video.user_id == user_id).first()
        
        if not video:
            return None
        
        # Verifica se o vídeo tem uma URL do blob storage
        if not video.url or not video.url.startswith("https://"):
            return None
        
        # Gera uma URL de streaming temporária
        from app.services.storage_service import generate_streaming_url
        streaming_url = generate_streaming_url(video.url, video.id)
        
        return streaming_url
    except Exception as e:
        logger.error(
            "Erro ao gerar URL de streaming para vídeo",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "video_guid": video_guid,
                "user_id": user_id,
                "operation": "get_video_streaming_url"
            }
        )
        return None
