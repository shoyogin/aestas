"""Application configuration from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings loaded from env (e.g. .env or Docker env)."""

    # App
    app_name: str = "Aestas API"
    frontend_origin: str = "http://localhost:5173"
    backend_public_url: str = "http://localhost:8000"  # For OAuth redirect_uri
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql://aestas:aestas@localhost:5432/aestas"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Google OAuth (from Google Cloud Console)
    google_client_id: str = ""
    google_client_secret: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
