import os
from dotenv import load_dotenv

load_dotenv()

print(f'DATABASE_URL: {os.getenv("DATABASE_URL")}')
print(f'SQLALCHEMY_DATABASE_URI: {os.getenv("SQLALCHEMY_DATABASE_URI")}')