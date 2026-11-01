"""Application settings loaded from environment."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://hcp:hcp@postgres:5432/hcp"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MinIO / S3
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "hcpadmin"
    minio_secret_key: str = "change-me"
    minio_secure: bool = False
    minio_region: str = "us-east-1"

    # Auth
    api_key: str = "change-me"

    # Logging
    log_level: str = "INFO"


settings = Settings()
