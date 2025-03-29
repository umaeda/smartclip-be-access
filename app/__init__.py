from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes import api_router
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.db.base import Base
from fastapi.routing import APIRoute
# Create database tables
# Comentar esta linha para produção, pois o Azure Functions não deve criar tabelas automaticamente
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FastAPI backend with JWT authentication and role-based access control",
    version="0.1.0",
    openapi_url=f"{settings.API_STR}/openapi.json"
)

# Set up CORS middleware
origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
for origin in origins:
    print(f"origin: {origin}")
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

for route in app.router.routes:
    print(f"Path: {route.path}, Name: {route.name}")

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