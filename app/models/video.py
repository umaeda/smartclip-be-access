from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.base_class import Base

class Video(Base):
    title = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    url = Column(String, nullable=True)
    is_validated = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("tb_user.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="videos")
    
    def __repr__(self):
        return f"<Video {self.title}>"