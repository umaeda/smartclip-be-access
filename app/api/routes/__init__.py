import azure.functions as func

from fastapi import APIRouter

# Importar os routers primeiro
from app.api.routes.auth import router as auth_router
from app.api.routes.videos import router as videos_router
from app.api.routes.credits import router as credits_router
from app.api.routes.credits import router as credits_router
from app.api.routes.assistir import router as assistir_router

api_router = APIRouter()

# Incluir os routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(videos_router, prefix="/videos", tags=["videos"])
api_router.include_router(credits_router, prefix="/credits", tags=["credits"])
api_router.include_router(assistir_router, prefix="/assistir", tags=["videos"])