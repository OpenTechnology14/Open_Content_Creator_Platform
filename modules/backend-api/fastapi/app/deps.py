"""Shared resources: DB engine, Redis client, MinIO client, auth dependency."""
import hmac
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Header, HTTPException, Query, status
from loguru import logger
from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Module-level resource handles initialized at startup.
_engine = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None
_redis: aioredis.Redis | None = None
_minio: Minio | None = None


async def init_resources() -> None:
    global _engine, _sessionmaker, _redis, _minio

    _engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)

    _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        await _redis.ping()
    except Exception as e:
        logger.error("Redis ping failed: {}", e)

    _minio = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
        region=settings.minio_region,
    )


async def close_resources() -> None:
    if _redis is not None:
        await _redis.close()
    if _engine is not None:
        await _engine.dispose()


# ─── Dependency functions ─────────────────────────────────────────


async def get_session() -> AsyncSession:
    assert _sessionmaker is not None, "DB not initialized"
    async with _sessionmaker() as session:
        yield session


def get_redis() -> aioredis.Redis:
    assert _redis is not None, "Redis not initialized"
    return _redis


async def get_redis_client() -> aioredis.Redis:
    """Plain accessor for non-Depends contexts (e.g. WebSocket handlers)."""
    assert _redis is not None, "Redis not initialized"
    return _redis


def get_minio() -> Minio:
    assert _minio is not None, "MinIO not initialized"
    return _minio


def _keys_match(candidate: str | None) -> bool:
    # hmac.compare_digest, not `==` — a naive equality check short-circuits on
    # the first mismatched byte, so response time leaks how many leading
    # characters of the guess are correct. compare_digest runs in time
    # dependent only on the length of its inputs.
    if not candidate:
        return False
    return hmac.compare_digest(candidate, settings.api_key)


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    if not _keys_match(x_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")


def require_api_key_ws(
    x_api_key: Annotated[str | None, Header()] = None,
    api_key: Annotated[str | None, Query()] = None,
) -> bool:
    """Same check as `require_api_key`, for the WebSocket route.

    Browser WebSocket clients cannot set custom headers, so this also
    accepts `?api_key=`; a native client can still use the header. Returns
    a bool instead of raising — `websocket.accept()` has not happened yet
    at dependency-resolution time, so the route handles rejection itself
    (closing with policy-violation) rather than this dependency raising an
    HTTPException the WebSocket protocol has no way to render.
    """
    return _keys_match(x_api_key) or _keys_match(api_key)


SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]
MinioDep = Annotated[Minio, Depends(get_minio)]
AuthDep = Annotated[None, Depends(require_api_key)]
WsAuthDep = Annotated[bool, Depends(require_api_key_ws)]
