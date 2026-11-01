"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/v1/health")
async def health():
    """Health check for relay availability.

    Used by:
    - Tauri apps to validate self-hosted relay URLs
    - Load balancers / uptime monitoring
    - DO droplet health checks
    """
    return {
        "status": "ok",
        "service": "creator-platform-relay",
        "version": "0.1.0",
    }


@router.get("/api/v1/health/db")
async def health_db():
    """Database connectivity check."""
    from ..database import pool
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
