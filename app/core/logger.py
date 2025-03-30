import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings

# Criar diretório de logs se não existir
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configuração do logger
def setup_logger(name: str = "app"):
    """Configura e retorna um logger com handlers para console e arquivo"""
    logger = logging.getLogger(name)
    
    # Evitar duplicação de handlers se o logger já foi configurado
    if logger.handlers:
        return logger
    
    # Definir nível de log baseado no ambiente
    log_level = logging.DEBUG if os.getenv("ENVIRONMENT", "development").lower() == "development" else logging.INFO
    logger.setLevel(log_level)
    
    # Formato do log
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    return logger

# Logger principal da aplicação
app_logger = setup_logger("smartclip")

# Função para obter um logger para um módulo específico
def get_logger(name: str):
    """Retorna um logger para um módulo específico"""
    return logging.getLogger(f"smartclip.{name}")

# Middleware para logging de requisições HTTP
class RequestLoggingMiddleware:
    """Middleware para logging de requisições HTTP"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        # Extract request details from scope
        method = scope.get("method", "")
        path = scope.get("path", "")
        
        # Log the request
        app_logger.info(f"Request: {method} {path}")
        
        # Process the request
        response_status = None
        
        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
        
        # Log the response
        if response_status:
            app_logger.info(f"Response: {response_status}")
        
        return