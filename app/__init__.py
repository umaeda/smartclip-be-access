from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from app.api.routes import api_router
from app.core.config import settings
from app.core.logger import app_logger, RequestLoggingMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.csrf import CSRFMiddleware
from app.db.session import engine, SessionLocal
from app.db.base import Base
from fastapi.routing import APIRoute
from fastapi.exceptions import RequestValidationError

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
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-csrf-token", "set-cookie", "*"],
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


from fastapi.exceptions import RequestValidationError

async def validation_exception_handler(request, exc: RequestValidationError):
    # Log detalhado no nível ERROR para garantir visibilidade dos erros de validação
    formatted_validation_errors = []
    missing_fields = []
    type_errors = []
    other_errors = []
    
    for error in exc.errors():
        error_type = error.get("type")
        loc = error.get("loc", [])
        field = loc[-1] if len(loc) > 0 else ""
        msg = error.get("msg", "")
        formatted_error = f"{field}: {msg} (tipo: {error_type})"
        formatted_validation_errors.append(formatted_error)
        
        # Separar erros por tipo para melhor visualização
        if error_type == "missing":
            missing_fields.append(field)
        elif error_type.startswith("type_error"):
            type_errors.append(f"{field}: {msg}")
        else:
            other_errors.append(f"{field}: {msg}")
    
    # Construir mensagem de log com seções separadas
    log_message = f"ERRO DE VALIDAÇÃO - Path: {request.url.path} - Method: {request.method}\n"
    
    if missing_fields:
        log_message += f"\nCAMPOS OBRIGATÓRIOS FALTANDO:\n" + "\n".join([f"- {field}" for field in missing_fields])
    
    if type_errors:
        log_message += f"\nERROS DE TIPO:\n" + "\n".join([f"- {err}" for err in type_errors])
    
    if other_errors:
        log_message += f"\nOUTROS ERROS:\n" + "\n".join([f"- {err}" for err in other_errors])
    
    # Log com nível ERROR para garantir que seja sempre exibido no console
    app_logger.error(
        log_message,
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
            "request_body": exc.body,
            "validation_errors": exc.errors(),
            "formatted_errors": formatted_validation_errors,
            "missing_fields": missing_fields,
            "type_errors": type_errors,
            "other_errors": other_errors
        }
    )
    
    # Log adicional com os dados brutos para depuração
    app_logger.debug(
        "Dados brutos do erro de validação",
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
            "raw_errors": exc.errors()
        }
    )
    
    # Formatar os erros de validação de forma mais amigável e detalhada
    formatted_errors = []
    error_fields = {}
    
    for error in exc.errors():
        error_type = error.get("type")
        loc = error.get("loc", [])
        field = loc[-1] if len(loc) > 0 else ""
        msg = error.get("msg", "")
        
        # Agrupar erros por campo para melhor visualização
        if field not in error_fields:
            error_fields[field] = []
            
        if error_type == "missing":
            error_message = f"Campo obrigatório"
        elif error_type == "type_error":
            error_message = f"Tipo inválido: {msg}"
        else:
            error_message = msg
            
        error_fields[field].append(error_message)
        formatted_errors.append(f"{field}: {error_message} (tipo: {error_type})")
    
    # Criar resposta estruturada com erros agrupados por campo
    structured_errors = [{
        "field": field,
        "messages": messages
    } for field, messages in error_fields.items()]
    
    from fastapi.responses import JSONResponse
    from fastapi import status
    
    # Preparar resposta com seções específicas para cada tipo de erro
    response_content = {
        "code": "validation_error",
        "message": "Erro de validação nos dados de entrada",
        "errors": structured_errors,
        "error_details": formatted_errors
    }
    
    # Adicionar seção específica para campos obrigatórios faltando
    if missing_fields:
        response_content["missing_required_fields"] = missing_fields
    
    # Adicionar seção específica para erros de tipo
    if type_errors:
        response_content["type_errors"] = type_errors
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_content
    )

app.add_exception_handler(RequestValidationError, validation_exception_handler)