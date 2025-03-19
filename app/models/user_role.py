from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class UserRole(Base):
    user_id = Column(Integer, ForeignKey("tb_user.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("tb_role.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
    
    def __repr__(self):
        return f"<UserRole user_id={self.user_id} role_id={self.role_id}>"