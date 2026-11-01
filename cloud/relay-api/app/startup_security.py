"""Startup security posture — production-secret and CORS-origin validation.

Deliberately zero framework imports (no pydantic, no fastapi) so this stays
testable without the relay's full dependency set installed. `main.py` wires
both functions in at import time, before the app is constructed.
"""
from __future__ import annotations

# Substring, not exact match: the codebase has two different placeholder
# conventions that both need catching — the compose file's inline default
# ("change-me-in-production") and .env.example's own documented placeholder
# ("change-me-use-at-least-32-random-characters"). An exact-match set would
# silently pass a user who copied .env.example and never touched the value.
WEAK_SECRET_MARKER = "change-me"

# Neither Tauri app configures a custom protocol scheme in its tauri.conf.json,
# so both use Tauri's own default production origin: `tauri://localhost` on
# macOS/Linux, `https://tauri.localhost` on Windows.
PRODUCTION_ORIGINS = (
    "tauri://localhost",
    "https://tauri.localhost",
)

# Each app's tauri.conf.json `build.devUrl` — where Tauri's WebView loads
# from (and the real Origin header it sends) outside of production.
DEV_ORIGINS = (
    "http://localhost:5173",  # apps/stream-extend
    "http://localhost:5174",  # apps/creator-extend
)


def is_weak_secret(secret: str) -> bool:
    return not secret or WEAK_SECRET_MARKER in secret.lower()


def assert_safe_for_production(environment: str, jwt_secret: str, database_url: str) -> None:
    """Fail closed: refuse to start in production with a placeholder secret
    or an unconfigured (default/localhost) database URL.

    HCP-007's own acceptance evidence is "Startup refuses weak production
    secrets" — nothing enforced this before. Both checks only gate on
    `environment == "production"` so a bare `python -m uvicorn` in local dev
    (where `Settings.environment` defaults to `"development"`) still works
    with no secret or real database configured.

    The database check matches `PROPOSAL_RELEASE_GAP_CLOSURE.md` §7.2's own
    example spec verbatim ("Production database URL must be explicit") —
    `Settings.database_url`'s own field default points at `localhost`, so a
    deployment that forgot to set `RELAY_DATABASE_URL` would otherwise start
    up talking to nothing.
    """
    if environment != "production":
        return
    if is_weak_secret(jwt_secret):
        raise RuntimeError(
            "RELAY_JWT_SECRET is unset or still the placeholder value. "
            "Set a real secret in the environment before starting in "
            "production — see cloud/.env.example."
        )
    if "localhost" in database_url:
        raise RuntimeError(
            "RELAY_DATABASE_URL still points at localhost — set the real "
            "production database URL before starting in production."
        )


def allowed_origins(environment: str) -> list[str]:
    """CORS origins for the two Tauri apps — never a wildcard.

    `allow_origins=["*"]` with `allow_credentials=True` is meaningless per
    the CORS spec (browsers require the server to echo the exact requesting
    origin when credentials are involved, not `*`) and provides no boundary
    at all for non-browser HTTP clients, which don't enforce CORS.
    """
    origins = list(PRODUCTION_ORIGINS)
    if environment != "production":
        origins += DEV_ORIGINS
    return origins
