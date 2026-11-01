"""
Cloud Relay API — Multi-tenant FastAPI relay for Stream Extend + Creator Extend.

Runs on a single DigitalOcean droplet. Handles:
- WebSocket relay between desktop ↔ mobile apps
- Subscription verification (Stripe + app store receipts)
- Push notification forwarding (APNs / FCM)
- Metric persistence (write path for cloud Grafana)
- Multi-device sync (settings, presets, workflows)
- Multi-user team access

Data isolation:
- Every table has a tenant_id column with row-level security
- S3/Spaces paths are prefix-isolated: s3://hcp-assets/{tenant_id}/...
- JWT carries tenant_id claim; middleware enforces isolation

Subscription tiers:
- Free:    All local features (no relay needed)
- Connect: Remote access + push notifications ($5/mo)
- Pro:     + metric persistence + multi-device sync ($12/mo)
- Team:    + multi-user access ($25/mo)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .startup_security import allowed_origins, assert_safe_for_production
from .middleware.body_size_limit import BodySizeLimitMiddleware
from .routers import auth, health, relay, sync, notifications, metrics, tenants

# Fail closed before the app is even constructed — HCP-007's acceptance
# evidence is "Startup refuses weak production secrets," not "logs a warning."
assert_safe_for_production(settings.environment, settings.jwt_secret, settings.database_url)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown."""
    # Startup
    from .database import init_db
    await init_db()
    print(f"Relay API started — {settings.environment} mode")
    yield
    # Shutdown
    print("Relay API shutting down")


app = FastAPI(
    title="Creator Platform Cloud Relay",
    version="0.1.0",
    description="Multi-tenant relay for Stream Extend + Creator Extend",
    lifespan=lifespan,
)

# CORS — the two Tauri apps' real origins (tauri.conf.json), not a wildcard.
# See startup_security.allowed_origins for why "*" was never actually safe here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(settings.environment),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejects an oversized body by Content-Length before any route/parsing runs.
# Added after CORS so it wraps outermost (Starlette applies middleware in
# reverse registration order) — a request is size-checked before anything
# else touches it.
app.add_middleware(BodySizeLimitMiddleware)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(relay.router, prefix="/api/v1/relay", tags=["relay"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["tenants"])


# WebSocket endpoint is on the root for relay connections
@app.websocket("/ws")
async def websocket_relay(websocket: WebSocket):
    """Main WebSocket relay endpoint.

    Apps connect here for real-time bidirectional communication.
    First message must be an Auth message with a valid JWT.

    The `websocket: WebSocket` type annotation is not decorative — FastAPI's
    routing (unlike bare Starlette) needs it to recognize this parameter as
    the connection object rather than failing to resolve it. Without it,
    every connection attempt closes immediately after accept, before this
    function's own body ever runs — confirmed by direct reproduction; there
    was no test anywhere that would have caught this (see
    tests/cloud_relay/test_ws_auth.py, P-053).
    """
    from .routers.relay import handle_websocket
    await handle_websocket(websocket)
