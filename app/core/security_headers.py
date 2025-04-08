from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
from app.core.logger import get_logger

logger = get_logger("security_headers")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware para adicionar headers de segurança a todas as respostas HTTP
    para proteção contra XSS, clickjacking e outros ataques.
    """
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        logger.info("SecurityHeadersMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Processa a requisição normalmente
        response = await call_next(request)
        
        # Adiciona headers de segurança
        
        # Previne que o navegador faça MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Previne clickjacking - impede que o site seja carregado em um iframe
        response.headers["X-Frame-Options"] = "DENY"
        
        # Habilita proteção XSS no navegador
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Define política de segurança de conteúdo (CSP)
        # Política ajustada para permitir requisições necessárias e acesso mobile
        csp_value = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "font-src 'self'; "
            "connect-src 'self' http: https: *; "
            "frame-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self';"
            "worker-src 'self';"
        )
        
        # Verifica se a requisição vem de um dispositivo móvel
        user_agent = request.headers.get("user-agent", "")
        from app.services.genvideo import is_mobile_device
        
        # Se for um dispositivo móvel, usa uma política CSP mais permissiva
        if is_mobile_device(user_agent):
            csp_value = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"
            
        response.headers["Content-Security-Policy"] = csp_value
        
        # Previne que o navegador armazene dados sensíveis em cache
        response.headers["Cache-Control"] = "no-store, max-age=0"
        
        # Força HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Controla quais recursos podem ser carregados
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Controla quais recursos podem ser carregados
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        return response