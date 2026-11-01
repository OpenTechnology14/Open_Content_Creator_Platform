"""
Multi-device sync router.

Stores settings, presets, and workflows in Postgres (per-tenant).
Requires Pro tier ($12/mo) or higher.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
import json

from ..middleware.auth import get_current_tenant, require_pro, TokenData
from ..database import TenantConnection

router = APIRouter()

# Second, defense-in-depth layer under the global BodySizeLimitMiddleware —
# `value` is arbitrary JSON, so it's the one field in this router the global
# byte cap alone doesn't meaningfully bound the *shape* of.
MAX_SYNC_VALUE_BYTES = 65_536  # 64 KiB


class SyncEntry(BaseModel):
    key: str
    value: dict
    version: int

    @field_validator("value")
    @classmethod
    def _bounded_value(cls, v: dict) -> dict:
        size = len(json.dumps(v).encode("utf-8"))
        if size > MAX_SYNC_VALUE_BYTES:
            raise ValueError(f"value exceeds {MAX_SYNC_VALUE_BYTES} bytes serialized ({size})")
        return v


class SyncResponse(BaseModel):
    key: str
    value: dict
    version: int
    updated_at: str


@router.get("/{key:path}", response_model=SyncResponse)
async def get_sync_entry(
    key: str,
    tenant: TokenData = Depends(require_pro),
):
    """Get a sync entry by key."""
    async with TenantConnection(tenant.tenant_id) as conn:
        row = await conn.fetchrow(
            "SELECT key, value, version, updated_at FROM sync_data "
            "WHERE tenant_id = $1 AND key = $2",
            tenant.tenant_id, key,
        )

    if not row:
        raise HTTPException(status_code=404, detail=f"Key not found: {key}")

    return SyncResponse(
        key=row["key"],
        value=json.loads(row["value"]),
        version=row["version"],
        updated_at=str(row["updated_at"]),
    )


@router.put("/{key:path}", response_model=SyncResponse)
async def put_sync_entry(
    key: str,
    body: SyncEntry,
    tenant: TokenData = Depends(require_pro),
):
    """Create or update a sync entry. Last-write-wins with version tracking."""
    async with TenantConnection(tenant.tenant_id) as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO sync_data (tenant_id, key, value, version, device_id)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (tenant_id, key) DO UPDATE
            SET value = EXCLUDED.value,
                version = EXCLUDED.version,
                device_id = EXCLUDED.device_id,
                updated_at = NOW()
            WHERE sync_data.version < EXCLUDED.version
            RETURNING key, value, version, updated_at
            """,
            tenant.tenant_id, key,
            json.dumps(body.value),
            body.version,
            tenant.device_id or "",
        )

    if not row:
        raise HTTPException(
            status_code=409,
            detail="Version conflict — remote version is newer",
        )

    return SyncResponse(
        key=row["key"],
        value=json.loads(row["value"]),
        version=row["version"],
        updated_at=str(row["updated_at"]),
    )


@router.get("/", response_model=list[SyncResponse])
async def list_sync_entries(
    prefix: Optional[str] = None,
    tenant: TokenData = Depends(require_pro),
):
    """List all sync entries for the tenant, optionally filtered by prefix."""
    async with TenantConnection(tenant.tenant_id) as conn:
        if prefix:
            rows = await conn.fetch(
                "SELECT key, value, version, updated_at FROM sync_data "
                "WHERE tenant_id = $1 AND key LIKE $2 ORDER BY key",
                tenant.tenant_id, f"{prefix}%",
            )
        else:
            rows = await conn.fetch(
                "SELECT key, value, version, updated_at FROM sync_data "
                "WHERE tenant_id = $1 ORDER BY key",
                tenant.tenant_id,
            )

    return [
        SyncResponse(
            key=r["key"],
            value=json.loads(r["value"]),
            version=r["version"],
            updated_at=str(r["updated_at"]),
        )
        for r in rows
    ]
