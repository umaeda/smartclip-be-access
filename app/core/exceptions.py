from fastapi import HTTPException, status

# Exceções de domínio base
class DomainException(Exception):
    """Exceção base para todas as exceções de domínio"""
    pass

class VideoServiceException(DomainException):
    """Exceção base para erros relacionados ao serviço de vídeo"""
    pass

# Exceções de domínio específicas
class VideoNotValidatedException(VideoServiceException):
    """Lançada quando um vídeo não foi validado"""
    def __init__(self, detail: str = "Video has not been validated yet"):
        self.detail = detail
        super().__init__(self.detail)

class VideoGenerationException(VideoServiceException):
    """Lançada quando ocorre um erro na geração do vídeo"""
    def __init__(self, detail: str = "Failed to generate video", error_id: str = None):
        self.detail = detail
        self.error_id = error_id
        super().__init__(self.detail)

# Exceções HTTP - Usadas apenas na camada de API
class PermissionDeniedException(HTTPException):
    def __init__(self, permission: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission: {permission}"
        )

# Mapeadores de exceções de domínio para HTTP
def map_domain_exception_to_http(exception: DomainException) -> HTTPException:
    """Mapeia exceções de domínio para exceções HTTP apropriadas"""
    if isinstance(exception, VideoNotValidatedException):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "video_not_validated",
                "message": exception.detail
            }
        )
    elif isinstance(exception, VideoGenerationException):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "video_generation_failed",
                "message": exception.detail,
                "error_id": exception.error_id
            }
        )
    else:
        # Exceção de domínio genérica
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "internal_error",
                "message": str(exception)
            }
        )