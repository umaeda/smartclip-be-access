from fastapi import HTTPException, status

class VideoNotValidatedException(HTTPException):
    def __init__(self, detail: str = "Video has not been validated yet"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class PermissionDeniedException(HTTPException):
    def __init__(self, permission: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission: {permission}"
        )