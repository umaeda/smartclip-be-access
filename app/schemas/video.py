from typing import Optional
from pydantic import BaseModel

# Shared properties
class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None
    url: Optional[str] = None

# Properties to receive via API on creation
class VideoCreate(VideoBase):
    title: str
    duration: int
    url: Optional[str] = None

# Properties to return via API
class Video(VideoBase):
    id: int
    is_validated: bool
    user_id: int
    duration: Optional[int] = None
    generation_time: Optional[float] = None
    
    class Config:
        from_attributes = True