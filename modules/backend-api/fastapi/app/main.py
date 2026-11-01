"""
Open Content Creator Platform — FastAPI backend.

Single ASGI app with per-domain routers.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.deps import close_resources, init_resources
from app.routers import automation, events, health, overlays, streams, ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Open Content Creator Platform API")
    logger.info("DB={}", settings.database_url.split("@")[-1])
    logger.info("Redis={}", settings.redis_url)
    logger.info("S3 endpoint={}", settings.minio_endpoint)
    await init_resources()
    yield
    await close_resources()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Open Content Creator Platform API",
    version="0.1.0",
    description="Internal API for the Open Content Creator Platform. See CLAUDE.md.",
    lifespan=lifespan,
)

# Routers — keep these in dependency order
app.include_router(health.router, tags=["health"])
app.include_router(streams.router, prefix="/streams", tags=["streams"])
app.include_router(overlays.router, prefix="/overlays", tags=["overlays"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(automation.router, prefix="/automation", tags=["automation"])
app.include_router(ws.router, prefix="/ws", tags=["websocket"])

# Prometheus metrics at /metrics
Instrumentator().instrument(app).expose(app)
