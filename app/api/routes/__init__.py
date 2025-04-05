from fastapi import APIRouter

api_router = APIRouter()

# Import the routers after creating api_router
from app.api.routes.auth import router as auth_router
from app.api.routes.videos import router as videos_router
from app.api.routes.credits import router as credits_router
from app.api.routes.assistir import router as assistir_router

# Include the routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(videos_router, prefix="/videos", tags=["videos"])
api_router.include_router(credits_router, prefix="/credits", tags=["credits"])
api_router.include_router(assistir_router, prefix="/assistir", tags=["videos"])