from sqlalchemy import Column, String, Boolean, Integer, Enum
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.base_class import Base

class User(Base):
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    profile_type = Column(Enum('Free', 'Gold', name='profile_types'), default='Free')
    
    # OAuth related fields
    oauth_provider = Column(String, nullable=True)  # 'google', etc.
    oauth_id = Column(String, nullable=True)  # ID from the OAuth provider
    
    # Relationships
    roles = relationship("UserRole", back_populates="user")
    videos = relationship("Video", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"