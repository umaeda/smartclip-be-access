from typing import List, Optional
from pydantic import BaseModel, EmailStr, UUID4

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    is_active: Optional[bool] = True
    is_verified: Optional[bool] = False
    profile_type: Optional[str] = "Free"

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

# Properties to return via API
class User(UserBase):
    id: int
    guid: UUID4
    
    class Config:
        orm_mode = True

# Properties to return via API with roles
class UserWithRoles(User):
    roles: List[str] = []
    permissions: List[str] = []