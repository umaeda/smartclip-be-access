from typing import Generator, List, Optional, Tuple, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import datetime

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

# Helper function to validate JWT token
def validate_token(token: str) -> Tuple[str, Dict[str, Any]]:
    """
    Validates a JWT token and returns the user_id and payload if valid.
    Raises HTTPException if token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Log token information for debugging
        print(f"Validating token: {token[:10]}...")
        print(f"Using SECRET_KEY: {settings.SECRET_KEY[:5]}...")
        print(f"Using JWT_ALGORITHM: {JWT_ALGORITHM}")
        
        # Decode token        
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        
        # Log successful decode
        print(f"Token decoded successfully")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            print("Token missing 'sub' claim")
            raise credentials_exception
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp is None:
            print("Token missing 'exp' claim")
            raise credentials_exception
        
        # Convert exp to datetime and check if it's expired
        current_time = datetime.utcnow().timestamp()
        if current_time > exp:
            print(f"Token expired: {exp} < {current_time}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print(f"Token valid for user_id: {user_id}")
        return user_id, payload
            
    except JWTError as e:
        print(f"JWT Error: {str(e)}")
        print(f"Token: {token[:10]}...")
        print(f"SECRET_KEY: {settings.SECRET_KEY[:5]}...")
        print(f"JWT_ALGORITHM: {JWT_ALGORITHM}")
        
        # Try to decode without verification for debugging
        try:
            # This is just for debugging - never use unverified tokens in production
            header = jwt.get_unverified_header(token)
            print(f"Token header: {header}")
        except Exception as header_error:
            print(f"Could not parse token header: {str(header_error)}")
            
        raise credentials_exception

# Current user dependency
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    print("get_current_user function called")  # Debug print
    
    # Validate token and get user_id
    user_id, _ = validate_token(token)
    
    # Get user from database
    user = db.query(User).filter(User.guid == user_id).first()
    if user is None:
        print(f"User not found with guid: {user_id}")  # Debug print
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"User authenticated: {user.email}")  # Debug print
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