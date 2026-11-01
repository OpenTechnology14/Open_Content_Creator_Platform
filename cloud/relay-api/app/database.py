"""
Database connection pool and session management.

Uses asyncpg for async Postgres access with connection pooling.
Row-level security is enforced at the Postgres level — every query
runs with a bound set_config tenant context.
"""
from __future__ import annotations

import asyncpg
from loguru import logger
from typing import Optional
from uuid import UUID
from .config import settings

pool: Optional[asyncpg.Pool] = None


TENANT_TABLES = ("devices", "sync_data", "metrics", "api_keys", "team_members", "notification_log")


async def init_db() -> None:
    """Initialize the connection pool."""
    global pool
    candidate = await asyncpg.create_pool(
        settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
        min_size=5,
        max_size=20,
        command_timeout=30,
    )

    try:
        async with candidate.acquire() as conn:
            bypass = await conn.fetchval(
                "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user"
            )
            if bypass is not False:
                raise RuntimeError("Relay database role must be non-superuser without BYPASSRLS")
            for table in TENANT_TABLES:
                if not await conn.fetchval("SELECT row_security_active($1::regclass)", table):
                    raise RuntimeError("Relay database role must enforce row security on every tenant table")
    except BaseException:
        await candidate.close()
        raise
    pool = candidate
    logger.info("Relay database connected with enforced tenant row security")


async def get_conn(tenant_id: Optional[str] = None) -> asyncpg.Connection:
    """
    Get a connection from the pool.

    If tenant_id is provided, sets the RLS context so all queries
    are automatically scoped to that tenant.
    """
    tenant = str(UUID(tenant_id)) if tenant_id is not None else ""
    if pool is None:
        raise RuntimeError("Relay database is not initialized")
    conn = await pool.acquire()
    try:
        # SET does not accept bind parameters. set_config does, without string interpolation.
        await conn.execute("SELECT set_config('app.tenant_id', $1, false)", tenant)
        return conn
    except BaseException:
        await pool.release(conn)
        raise


async def release_conn(conn: asyncpg.Connection) -> None:
    """Release a connection back to the pool."""
    # Reset the tenant context
    if pool is None:
        raise RuntimeError("Relay database is not initialized")
    try:
        await conn.execute("RESET app.tenant_id")
    finally:
        # asyncpg additionally resets/rolls back on release, including aborted transactions.
        await pool.release(conn)


class TenantConnection:
    """Async context manager for tenant-scoped database connections."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.conn = None

    async def __aenter__(self):
        self.conn = await get_conn(self.tenant_id)
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            await release_conn(self.conn)
