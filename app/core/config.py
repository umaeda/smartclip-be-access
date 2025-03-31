from typing import List, Optional, Union, Any
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
import secrets
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env se existir
load_dotenv(dotenv_path=".env.dev")

class Settings(BaseSettings):
    API_STR: str = os.getenv("API_STR", "/api")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "FastAPI Backend")
    
    # Secret key for JWT
    # Obtém a chave secreta das variáveis de ambiente
    # Gera uma chave aleatória apenas para desenvolvimento se não estiver definida
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))

    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 8))
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://localhost:8080,http://localhost:4200")

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if not v or v.strip() in ('""', "''", "[]"):
                return []
            # Remove aspas extras que podem estar presentes no valor da variável de ambiente
            v = v.strip('"\'')
            if v.startswith('[') and v.endswith(']'):
                try:
                    # Try to parse as JSON apenas se estiver entre colchetes
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Se não for JSON válido, split por vírgula
            return [i.strip() for i in v.split(",") if i.strip()]
        return v or []

    # Database settings
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "app_db")
    SQLALCHEMY_DATABASE_URI: Optional[str] = os.getenv("SQLALCHEMY_DATABASE_URI")
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB')}"
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        # If SQLALCHEMY_DATABASE_URI is set, use that value
        if values.get("SQLALCHEMY_DATABASE_URI"):
            return values.get("SQLALCHEMY_DATABASE_URI")
        # Otherwise construct from individual settings
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB')}"
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    
    # Rate limiting settings
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Configurações de logging
    LOG_SENSITIVE_DATA: bool = os.getenv("LOG_SENSITIVE_DATA", "False").lower() == "true"
    # Definindo o nível de log padrão como DEBUG para melhorar a visibilidade dos erros
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()