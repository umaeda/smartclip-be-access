from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyCookie
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable, Optional, List
import secrets
import time
from jose import jwt

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Constantes para o CSRF
CSRF_SECRET = settings.SECRET_KEY  # Usando a mesma chave secreta do JWT
CSRF_TOKEN_HEADER = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_TOKEN_EXPIRY = 3600  # 1 hora em segundos

# Métodos que modificam dados e precisam de proteção CSRF
CSRF_PROTECTED_METHODS = ["POST", "PUT", "DELETE", "PATCH"]

# Rotas que não precisam de proteção CSRF (como login)
CSRF_EXEMPT_ROUTES = ["/api/auth/login", "/api/auth/refresh"]


def generate_csrf_token() -> str:
    """
    Gera um token CSRF seguro usando secrets
    """
    return secrets.token_urlsafe(32)


def encode_csrf_token(token: str) -> str:
    """
    Codifica o token CSRF com JWT para adicionar expiração
    """
    payload = {
        "token": token,
        "exp": time.time() + CSRF_TOKEN_EXPIRY
    }
    return jwt.encode(payload, CSRF_SECRET, algorithm="HS256")


def decode_csrf_token(encoded_token: str) -> Optional[str]:
    """
    Decodifica e valida o token CSRF
    """
    try:
        payload = jwt.decode(encoded_token, CSRF_SECRET, algorithms=["HS256"])
        return payload.get("token")
    except Exception as e:
        logger.error(f"Erro ao decodificar token CSRF: {e}")
        return None


def validate_csrf_token(request_token: str, stored_token: str) -> bool:
    """
    Valida se o token CSRF da requisição corresponde ao token armazenado
    """
    if not request_token or not stored_token:
        return False
    
    decoded_stored = decode_csrf_token(stored_token)
    if not decoded_stored:
        return False
    
    # Comparação de tempo constante para evitar timing attacks
    return secrets.compare_digest(request_token, decoded_stored)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware para proteção CSRF que verifica tokens em requisições que modificam dados
    """
    
    def __init__(self, app):
        super().__init__(app)
        logger.info("CSRFMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Verifica se a rota está isenta de proteção CSRF
        path = request.url.path
        if any(path.startswith(exempt_route) for exempt_route in CSRF_EXEMPT_ROUTES):
            response = await call_next(request)
            # Gera e adiciona token CSRF mesmo em rotas isentas
            new_token = generate_csrf_token()
            encoded_token = encode_csrf_token(new_token)
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=encoded_token,
                max_age=CSRF_TOKEN_EXPIRY,
                httponly=True,
                samesite="Lax"
            )
            response.headers[CSRF_TOKEN_HEADER] = new_token
            return response
        
        # Verifica se o método precisa de proteção CSRF
        if request.method in CSRF_PROTECTED_METHODS:
            # Obtém o token CSRF do cabeçalho
            csrf_token = request.headers.get(CSRF_TOKEN_HEADER)
            # Obtém o token CSRF do cookie
            csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
            
            # Valida o token CSRF
            if not csrf_token or not csrf_cookie or not validate_csrf_token(csrf_token, csrf_cookie):
                logger.warning(f"Falha na validação CSRF para {request.url.path}")
                return Response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content="CSRF token inválido ou ausente",
                )
        
        # Processa a requisição normalmente
        response = await call_next(request)
        
        # Para respostas bem-sucedidas em rotas de autenticação, gera um novo token CSRF
        if path.startswith("/api/auth/login") and response.status_code == status.HTTP_200_OK:
            # Gera um novo token CSRF
            token = generate_csrf_token()
            encoded_token = encode_csrf_token(token)
            
            # Define o token no cookie
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=encoded_token,
                httponly=True,  # Não acessível via JavaScript
                secure=True,    # Apenas em HTTPS
                samesite="lax", # Proteção contra CSRF em navegadores modernos
                max_age=CSRF_TOKEN_EXPIRY
            )
            
            # Adiciona o token ao cabeçalho para que o frontend possa usá-lo
            response.headers[CSRF_TOKEN_HEADER] = token
        
        return response


# Dependência para verificar o token CSRF em rotas específicas
csrf_cookie = APIKeyCookie(name=CSRF_COOKIE_NAME, auto_error=False)


def csrf_protect():
    """
    Dependência para proteção CSRF em rotas específicas
    """
    def csrf_dependency(request: Request, csrf_cookie_token: str = Depends(csrf_cookie)):
        if request.method in CSRF_PROTECTED_METHODS:
            csrf_header_token = request.headers.get(CSRF_TOKEN_HEADER)
            
            if not csrf_header_token or not csrf_cookie_token or not validate_csrf_token(csrf_header_token, csrf_cookie_token):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token inválido ou ausente"
                )
    
    return csrf_dependency