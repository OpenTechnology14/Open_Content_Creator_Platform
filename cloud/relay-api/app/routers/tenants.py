"""
Tenant management router.

Admin operations for tenant provisioning and subscription management.
"""

from fastapi import APIRouter, Depends

from ..middleware.auth import get_current_tenant, require_team, TokenData
from ..database import TenantConnection
from ..unavailable import feature_unavailable

router = APIRouter()


@router.get("/me")
async def get_current_tenant_info(
    tenant: TokenData = Depends(get_current_tenant),
):
    """Get current tenant info and subscription status."""
    async with TenantConnection(tenant.tenant_id) as conn:
        row = await conn.fetchrow(
            "SELECT id, email, name, tier, created_at, is_active FROM tenants "
            "WHERE id = $1",
            tenant.tenant_id,
        )

    if not row:
        return {
            "tenant_id": tenant.tenant_id,
            "tier": tenant.tier.value,
            "note": "Tenant not yet provisioned in database",
        }

    return {
        "tenant_id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "tier": row["tier"],
        "created_at": str(row["created_at"]),
        "is_active": row["is_active"],
    }


@router.get("/me/devices")
async def list_devices(
    tenant: TokenData = Depends(get_current_tenant),
):
    """List all registered devices for the current tenant."""
    async with TenantConnection(tenant.tenant_id) as conn:
        rows = await conn.fetch(
            "SELECT id, name, product, platform, last_seen_at, created_at "
            "FROM devices WHERE tenant_id = $1 ORDER BY last_seen_at DESC",
            tenant.tenant_id,
        )

    return [
        {
            "id": r["id"],
            "name": r["name"],
            "product": r["product"],
            "platform": r["platform"],
            "last_seen_at": str(r["last_seen_at"]) if r["last_seen_at"] else None,
            "created_at": str(r["created_at"]),
        }
        for r in rows
    ]


@router.get("/me/usage")
async def get_usage(
    tenant: TokenData = Depends(get_current_tenant),
):
    """Get resource usage for the current tenant."""
    async with TenantConnection(tenant.tenant_id) as conn:
        # Count sync entries
        sync_count = await conn.fetchval(
            "SELECT COUNT(*) FROM sync_data WHERE tenant_id = $1",
            tenant.tenant_id,
        )
        # Count stored metrics
        metric_count = await conn.fetchval(
            "SELECT COUNT(*) FROM metrics WHERE tenant_id = $1",
            tenant.tenant_id,
        )
        # Count devices
        device_count = await conn.fetchval(
            "SELECT COUNT(*) FROM devices WHERE tenant_id = $1",
            tenant.tenant_id,
        )

    return {
        "sync_entries": sync_count or 0,
        "metric_points": metric_count or 0,
        "devices": device_count or 0,
    }


@router.post("/me/team/invite")
async def invite_team_member(
    email: str,
    role: str = "member",
    tenant: TokenData = Depends(require_team),
):
    """Invite a team member (Team tier only)."""
    feature_unavailable("team_invitation")
