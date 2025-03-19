from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.responses import RedirectResponse

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash, brute_force_protection
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.schemas.token import Token
from app.schemas.user import UserCreate

router = APIRouter()

# Set up Google OAuth
config = Config()
config.environ["GOOGLE_CLIENT_ID"] = settings.GOOGLE_CLIENT_ID
config.environ["GOOGLE_CLIENT_SECRET"] = settings.GOOGLE_CLIENT_SECRET

oauth = OAuth(config)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests"""
    # Check if account is locked due to too many failed attempts
    identifier = form_data.username  # Use email as identifier
    is_locked, unlock_time = brute_force_protection.check_account_status(identifier)
    
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Account locked due to too many failed attempts. Try again after {unlock_time}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Check authentication
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Record failed attempt
        attempts_remaining, is_now_locked = brute_force_protection.record_failed_attempt(identifier)
        
        if is_now_locked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account locked due to too many failed attempts",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect email or password. Attempts remaining: {attempts_remaining}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    
    # Reset failed attempts counter on successful login
    brute_force_protection.reset_attempts(identifier)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            subject=str(user.guid), expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=Token)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """Register a new user and return an access token"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_verified=False,  # Require email verification
        profile_type="Free",
    )
    db.add(user)
    db.flush()
    
    # Assign default role
    default_role = db.query(Role).filter(Role.name == "user").first()
    if default_role:
        user_role = UserRole(user_id=user.id, role_id=default_role.id)
        db.add(user_role)
    
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            subject=str(user.guid), expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/google")
async def login_google(request: Request):
    """Redirect to Google for authentication"""
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    """Process Google OAuth callback"""
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    
    if not user_info or not user_info.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not get user info from Google",
        )
    
    # Check if user exists
    user = db.query(User).filter(User.email == user_info["email"]).first()
    
    if not user:
        # Create new user
        user = User(
            email=user_info["email"],
            is_active=True,
            is_verified=True,  # Google accounts are pre-verified
            profile_type="Free",
            oauth_provider="google",
            oauth_id=user_info["sub"],
        )
        db.add(user)
        db.flush()
        
        # Assign default role
        default_role = db.query(Role).filter(Role.name == "user").first()
        if default_role:
            user_role = UserRole(user_id=user.id, role_id=default_role.id)
            db.add(user_role)
        
        db.commit()
        db.refresh(user)
    else:
        # Update OAuth info if user already exists
        user.oauth_provider = "google"
        user.oauth_id = user_info["sub"]
        user.is_verified = True
        db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.guid), expires_delta=access_token_expires
    )
    
    # Redirect to frontend with token
    response = RedirectResponse(url=f"/auth/callback?token={access_token}")
    return response