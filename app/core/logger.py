import logging
import sys
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings

# Criar diretório de logs se não existir
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Função para sanitizar dados sensíveis nos logs
def sanitize_log_message(message):
    """Remove ou mascara informações sensíveis das mensagens de log"""
    if not isinstance(message, str):
        return message
        
    # Mascarar emails
    message = re.sub(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', '***@***.***', message)
    
    # Mascarar tokens JWT
    message = re.sub(r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', '[TOKEN_REDACTED]', message)
    
    # Mascarar senhas que possam aparecer em logs
    message = re.sub(r'password["\':\s=]+[^\s,;]+', 'password=[REDACTED]', message, flags=re.IGNORECASE)
    
    # Mascarar IDs de usuário
    message = re.sub(r'user (\d+)', 'user [ID_REDACTED]', message)
    message = re.sub(r'user_id["\':=\s]+(\d+)', 'user_id=[ID_REDACTED]', message)
    message = re.sub(r'ID: (\d+)', 'ID: [ID_REDACTED]', message)
    
    # Mascarar GUIDs
    message = re.sub(r'guid["\':=\s]+([a-f0-9-]+)', 'guid=[GUID_REDACTED]', message, flags=re.IGNORECASE)
    
    return message

# Configuração do logger
# Criar uma classe de filtro para sanitizar mensagens de log
class SensitiveDataFilter(logging.Filter):
    """Filtro para sanitizar informações sensíveis em logs"""
    
    def __init__(self, sanitize_enabled=True):
        super().__init__()
        self.sanitize_enabled = sanitize_enabled
    
    def filter(self, record):
        if self.sanitize_enabled and isinstance(record.msg, str):
            record.msg = sanitize_log_message(record.msg)
        return True

def setup_logger(name: str = "app"):
    """Configura e retorna um logger com handlers para console e arquivo"""
    logger = logging.getLogger(name)
    
    # Evitar duplicação de handlers se o logger já foi configurado
    if logger.handlers:
        return logger
    
    # Definir nível de log baseado na configuração
    log_level_name = settings.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logger.setLevel(log_level)
    
    # Adicionar filtro para sanitizar dados sensíveis apenas se configurado
    logger.addFilter(SensitiveDataFilter(not settings.LOG_SENSITIVE_DATA))
    
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
        
        # Sanitizar o caminho da requisição para remover informações sensíveis
        # Por exemplo, tokens ou IDs em URLs como /api/users/123 ou /api/reset-password?token=xyz
        sanitized_path = sanitize_log_message(path)
        
        # Verificar se a rota contém endpoints sensíveis que não devem ser logados
        sensitive_endpoints = ["/api/auth/login", "/api/auth/register", "/api/auth/reset-password"]
        is_sensitive = any(endpoint in path for endpoint in sensitive_endpoints)
        
        # Log the request, omitindo detalhes para endpoints sensíveis
        if is_sensitive and not settings.LOG_SENSITIVE_DATA:
            app_logger.info(f"Request to sensitive endpoint: {method} [PATH_REDACTED]")
        else:
            app_logger.info(f"Request: {method} {sanitized_path}")
        
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
            if is_sensitive and not settings.LOG_SENSITIVE_DATA:
                app_logger.info(f"Response to sensitive endpoint: {response_status}")
            else:
                app_logger.info(f"Response: {method} {sanitized_path} - {response_status}")
        
        return