from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes import api_router
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Create database tables
# Comentar esta linha para produção, pois o Azure Functions não deve criar tabelas automaticamente
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FastAPI backend with JWT authentication and role-based access control",
    version="0.1.0",
    openapi_url=f"{settings.API_STR}/openapi.json",
    # Adicionar root_path para compatibilidade com Azure Functions
    root_path="/api"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Include API router
app.include_router(api_router, prefix=settings.API_STR)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)