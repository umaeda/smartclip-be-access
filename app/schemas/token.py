from typing import Optional, Any
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    profile: Optional[str] = None