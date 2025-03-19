from typing import Optional
from pydantic import BaseModel, UUID4

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

class TokenData(BaseModel):
    user_id: UUID4
    email: str
    is_verified: bool
    profile_type: str