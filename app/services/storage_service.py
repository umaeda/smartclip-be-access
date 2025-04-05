from typing import Optional
import os
import uuid
from datetime import datetime, timedelta

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas, BlobSasPermissions
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("storage_service")

def get_blob_service_client() -> BlobServiceClient:
    """Obtém um cliente do serviço de Blob Storage do Azure
    
    Returns:
        BlobServiceClient: Cliente do serviço de Blob Storage
        
    Raises:
        Exception: Se não for possível conectar ao serviço de Blob Storage
    """
    try:
        # Cria um cliente do serviço de Blob Storage usando a string de conexão
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        return blob_service_client
    except Exception as e:
        logger.error(
            "Erro ao conectar ao serviço de Blob Storage",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "operation": "get_blob_service_client"
            }
        )
        raise

def upload_video_to_blob_storage(file_path: str, video_id: int) -> Optional[str]:
    """Faz upload de um vídeo para o Azure Blob Storage
    
    Args:
        file_path: Caminho local do arquivo de vídeo
        video_id: ID do vídeo no banco de dados
        
    Returns:
        str: URL do blob no Azure Storage ou None em caso de falha
        
    Raises:
        Exception: Se ocorrer um erro durante o upload
    """
    if not os.path.exists(file_path):
        logger.error(
            "Arquivo de vídeo não encontrado",
            extra={
                "file_path": file_path,
                "video_id": video_id,
                "operation": "upload_video_to_blob_storage"
            }
        )
        return None
    
    try:
        # Gera um nome único para o blob baseado no ID do vídeo
        blob_name = f"video_{video_id}_{uuid.uuid4()}.mp4"
        
        # Obtém o cliente do serviço de Blob Storage
        blob_service_client = get_blob_service_client()
        
        # Obtém o cliente do container
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_NAME)
        
        # Verifica se o container existe, se não, cria
        try:
            container_client.get_container_properties()
        except Exception:
            container_client.create_container()
            logger.info(
                f"Container {settings.AZURE_STORAGE_CONTAINER_NAME} criado com sucesso",
                extra={"operation": "create_container"}
            )
        
        # Obtém o cliente do blob
        blob_client = container_client.get_blob_client(blob_name)
        
        # Faz upload do arquivo para o blob
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        # Retorna a URL do blob
        blob_url = blob_client.url
        
        logger.info(
            "Vídeo enviado para o Blob Storage com sucesso",
            extra={
                "video_id": video_id,
                "blob_name": blob_name,
                "operation": "upload_video_to_blob_storage_success"
            }
        )
        
        return blob_url
    except Exception as e:
        logger.error(
            "Erro ao fazer upload do vídeo para o Blob Storage",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "file_path": file_path,
                "video_id": video_id,
                "operation": "upload_video_to_blob_storage_error"
            }
        )
        return None

def generate_download_url(blob_url: str, video_id: int, expiry_hours: int = 24) -> Optional[str]:
    """Gera uma URL de download com SAS (Shared Access Signature) para um blob
    
    Args:
        blob_url: URL do blob no Azure Storage
        video_id: ID do vídeo no banco de dados
        expiry_hours: Número de horas até a expiração da URL (padrão: 24)
        
    Returns:
        str: URL de download com SAS ou None em caso de falha
        
    Raises:
        Exception: Se ocorrer um erro ao gerar a URL
    """
    try:
        # Extrai o nome do container e do blob da URL
        # Formato da URL: https://<storage-account>.blob.core.windows.net/<container>/<blob>
        blob_service_client = get_blob_service_client()
        account_name = blob_service_client.account_name
        
        # Extrai o nome do blob da URL
        parts = blob_url.split(f"{account_name}.blob.core.windows.net/")
        if len(parts) != 2:
            logger.error(
                "Formato de URL de blob inválido",
                extra={
                    "blob_url": blob_url,
                    "video_id": video_id,
                    "operation": "generate_download_url"
                }
            )
            return None
        
        container_blob_path = parts[1]
        container_name, blob_name = container_blob_path.split("/", 1)
        
        # Obtém o cliente do blob
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        # Define as permissões e o tempo de expiração
        sas_permissions = BlobSasPermissions(read=True)
        expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        # Gera a SAS
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=sas_permissions,
            expiry=expiry_time
        )
        
        # Constrói a URL de download com a SAS
        download_url = f"{blob_client.url}?{sas_token}"
        
        logger.info(
            "URL de download gerada com sucesso",
            extra={
                "video_id": video_id,
                "expiry_hours": expiry_hours,
                "operation": "generate_download_url_success"
            }
        )
        
        return download_url
    except Exception as e:
        logger.error(
            "Erro ao gerar URL de download",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "blob_url": blob_url,
                "video_id": video_id,
                "operation": "generate_download_url_error"
            }
        )
        return None

def generate_streaming_url(blob_url: str, video_id: int, expiry_hours: int = 2) -> Optional[str]:
    """Gera uma URL de streaming com SAS (Shared Access Signature) para um blob
    
    Args:
        blob_url: URL do blob no Azure Storage
        video_id: ID do vídeo no banco de dados
        expiry_hours: Número de horas até a expiração da URL (padrão: 2)
        
    Returns:
        str: URL de streaming com SAS ou None em caso de falha
        
    Raises:
        Exception: Se ocorrer um erro ao gerar a URL
    """
    try:
        # Extrai o nome do container e do blob da URL
        # Formato da URL: https://<storage-account>.blob.core.windows.net/<container>/<blob>
        blob_service_client = get_blob_service_client()
        account_name = blob_service_client.account_name
        
        # Extrai o nome do blob da URL
        parts = blob_url.split(f"{account_name}.blob.core.windows.net/")
        if len(parts) != 2:
            logger.error(
                "Formato de URL de blob inválido",
                extra={
                    "blob_url": blob_url,
                    "video_id": video_id,
                    "operation": "generate_streaming_url"
                }
            )
            return None
        
        container_blob_path = parts[1]
        container_name, blob_name = container_blob_path.split("/", 1)
        
        # Obtém o cliente do blob
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        # Define as permissões e o tempo de expiração
        # Para streaming, precisamos apenas da permissão de leitura
        sas_permissions = BlobSasPermissions(read=True)
        expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        # Gera a SAS
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=sas_permissions,
            expiry=expiry_time
        )
        
        # Constrói a URL de streaming com a SAS
        streaming_url = f"{blob_client.url}?{sas_token}"
        
        logger.info(
            "URL de streaming gerada com sucesso",
            extra={
                "video_id": video_id,
                "expiry_hours": expiry_hours,
                "operation": "generate_streaming_url_success"
            }
        )
        
        return streaming_url
    except Exception as e:
        logger.error(
            "Erro ao gerar URL de streaming",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "blob_url": blob_url,
                "video_id": video_id,
                "operation": "generate_streaming_url_error"
            }
        )
        return None