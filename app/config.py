from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://radiususer:radiuspass@localhost:5432/radius"
    admin_db_url: str = ""  # optional separate DB for admin tables; defaults to database_url

    jwt_secret: str = "change-me-to-a-real-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

if not settings.admin_db_url:
    settings.admin_db_url = settings.database_url
