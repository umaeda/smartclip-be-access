from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Permission(Base):
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    # Relationships
    roles = relationship("RolePermission", back_populates="permission")
    
    def __repr__(self):
        return f"<Permission {self.name}>"