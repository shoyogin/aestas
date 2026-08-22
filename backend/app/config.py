"""Application configuration from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from env (e.g. .env or Docker env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "Aestas API"
    frontend_origin: str = "http://localhost:5173"
    backend_public_url: str = "http://localhost:8000"  # For OAuth redirect_uri
    log_level: str = "INFO"

    # Cookies. Set COOKIE_SECURE=true whenever the app is served over HTTPS.
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    # Database
    database_url: str = "postgresql://aestas:aestas@localhost:5432/aestas"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Sessions
    session_ttl_days: int = 7

    # Rate limits, as "<max calls>/<window seconds>" per user or client IP.
    rate_limit_search: str = "30/60"
    rate_limit_follow_write: str = "20/300"
    rate_limit_auth: str = "20/300"

    # Google OAuth (from Google Cloud Console)
    google_client_id: str = ""
    google_client_secret: str = ""


settings = Settings()
