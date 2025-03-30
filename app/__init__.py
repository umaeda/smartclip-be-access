from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes import api_router
from app.core.config import settings
from app.core.logger import app_logger, RequestLoggingMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.csrf import CSRFMiddleware
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
    app_logger.debug(f"CORS origin: {origin}")
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Add CSRF protection middleware
app.add_middleware(CSRFMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

for route in app.router.routes:
    app_logger.debug(f"Registered route - Path: {route.path}, Name: {route.name}")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Include API router
app.include_router(api_router, prefix=settings.API_STR)

# Log application startup
app_logger.info(f"Application {settings.PROJECT_NAME} initialized with API at {settings.API_STR}")


# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}