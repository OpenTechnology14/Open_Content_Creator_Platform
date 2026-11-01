"""
Relay API configuration — loaded from environment variables.
"""

from pathlib import Path

from pydantic_settings import BaseSettings
from typing import Optional

# Anchored to this file's own directory, not CWD — `env_file = ".env"`
# alone resolves relative to wherever the process happens to be launched
# from. Running anything relay-related from the repo root (as every test
# in tests/ does) would otherwise load the platform's own root `.env`
# instead, which carries unrelated vars (POSTGRES_PORT, MINIO_*, ...) that
# crash BaseSettings' extra="forbid" default — found while adding
# tests/cloud_relay/test_auth.py (P-053).
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """All configuration from environment variables."""

    # Environment
    environment: str = "development"
    debug: bool = False

    # Database (Managed Postgres on DigitalOcean)
    database_url: str = "postgresql+asyncpg://relay:relay@localhost:5432/relay"

    # Redis (for pub/sub between WebSocket connections)
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "CHANGE-ME-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 720  # 30 days

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_connect: Optional[str] = None  # $5/mo price ID
    stripe_price_pro: Optional[str] = None       # $12/mo price ID
    stripe_price_team: Optional[str] = None      # $25/mo price ID

    # App Store verification
    apple_shared_secret: Optional[str] = None
    google_service_account_json: Optional[str] = None

    # DigitalOcean Spaces (S3-compatible, per-tenant asset storage)
    spaces_endpoint: str = "https://nyc3.digitaloceanspaces.com"
    spaces_region: str = "nyc3"
    spaces_bucket: str = "hcp-assets"
    spaces_access_key: Optional[str] = None
    spaces_secret_key: Optional[str] = None

    # Push notifications
    apns_key_path: Optional[str] = None
    apns_key_id: Optional[str] = None
    apns_team_id: Optional[str] = None
    fcm_credentials_json: Optional[str] = None

    # Rate limiting
    ws_max_connections_per_tenant: int = 10
    api_rate_limit_per_minute: int = 60

    # Request size limits
    max_request_body_bytes: int = 1_048_576  # 1 MiB

    # Admin
    admin_token: Optional[str] = None  # unset = /connections stays unreachable

    class Config:
        env_file = _ENV_FILE
        env_prefix = "RELAY_"


settings = Settings()
