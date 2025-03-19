from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Role(Base):
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    # Relationships
    users = relationship("UserRole", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role")
    
    def __repr__(self):
        return f"<Role {self.name}>"