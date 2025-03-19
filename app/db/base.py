# Import the Base class from base_class.py
from app.db.base_class import Base

# Import all the models after Base is defined
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission