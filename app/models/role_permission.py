from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class RolePermission(Base):
    role_id = Column(Integer, ForeignKey("tb_role.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("tb_permission.id"), nullable=False)
    
    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")
    
    def __repr__(self):
        return f"<RolePermission role_id={self.role_id} permission_id={self.permission_id}>"