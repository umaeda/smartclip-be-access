from typing import Generator, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import JWT_ALGORITHM
from app.db.session import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.schemas.token import TokenPayload

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_STR}/auth/login"
)

# Database dependency
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Current user dependency
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    user = db.query(User).filter(User.guid == token_data.sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return user

# Active user dependency
def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user

# Verified user dependency
def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email not verified"
        )
    return current_user

# Permission check dependency
def has_permission(required_permission: str):
    def permission_checker(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_verified_user)
    ) -> User:
        # Get all user roles
        user_roles = [user_role.role for user_role in current_user.roles]
        
        # Get all permissions from user roles
        user_permissions = []
        for role in user_roles:
            role_permissions = [rp.permission for rp in role.permissions]
            user_permissions.extend(role_permissions)
        
        # Check if user has the required permission
        if not any(p.name == required_permission for p in user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have permission: {required_permission}"
            )
        
        return current_user
    
    return permission_checker

# Profile type check dependency
def has_profile_type(required_profile_type: str):
    def profile_type_checker(
        current_user: User = Depends(get_current_verified_user)
    ) -> User:
        if current_user.profile_type != required_profile_type:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required profile type: {required_profile_type}"
            )
        
        return current_user
    
    return profile_type_checker