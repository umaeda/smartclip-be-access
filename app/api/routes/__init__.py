from fastapi import APIRouter

from app.api.routes import auth, videos

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])

# Add more routers here as needed
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(roles.router, prefix="/roles", tags=["roles"])