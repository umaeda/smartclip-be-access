from app.core.config import settings

print("Database URI:", settings.SQLALCHEMY_DATABASE_URI)
print("CORS Origins:", settings.BACKEND_CORS_ORIGINS)
print("Project Name:", settings.PROJECT_NAME)
print("Secret Key:", settings.SECRET_KEY)