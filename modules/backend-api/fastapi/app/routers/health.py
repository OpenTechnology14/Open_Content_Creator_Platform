"""Liveness + readiness endpoints."""
from fastapi import APIRouter

from app.deps import RedisDep, SessionDep
from sqlalchemy import text

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness — always 200 if process is up."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(session: SessionDep, redis: RedisDep) -> dict[str, str]:
    """Readiness — confirms deps are reachable."""
    checks: dict[str, str] = {}

    try:
        await session.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"fail: {e!s}"

    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"fail: {e!s}"

    return {"status": "ok" if all(v == "ok" for v in checks.values()) else "degraded", **checks}
