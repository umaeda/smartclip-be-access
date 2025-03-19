from typing import Optional
from pydantic import BaseModel

# Shared properties
class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None
    url: str

# Properties to receive via API on creation
class VideoCreate(VideoBase):
    pass

# Properties to return via API
class Video(VideoBase):
    id: int
    is_validated: bool
    user_id: int
    
    class Config:
        orm_mode = True