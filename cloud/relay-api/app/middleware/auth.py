"""
JWT authentication middleware.

Every authenticated request carries a JWT with:
- tenant_id: scopes all database queries via RLS
- tier: subscription tier (free/connect/pro/team)
- device_id: originating device
- exp: expiration timestamp
"""

import hmac
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timezone
from typing import Annotated, Optional
from pydantic import BaseModel

from ..config import settings
from ..models import SubscriptionTier
from .rate_limit import check_rate_limit

security = HTTPBearer()


class TokenData(BaseModel):
    tenant_id: str
    tier: SubscriptionTier
    device_id: Optional[str] = None
    exp: int


def create_token(tenant_id: str, tier: SubscriptionTier, device_id: Optional[str] = None) -> str:
    """Create a JWT for a tenant."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=settings.jwt_expire_hours)

    payload = {
        "tenant_id": tenant_id,
        "tier": tier.value,
        "device_id": device_id or "",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": "relay.streamextend.com",
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        return TokenData(
            tenant_id=payload["tenant_id"],
            tier=SubscriptionTier(payload["tier"]),
            device_id=payload.get("device_id"),
            exp=payload["exp"],
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )


async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """Dependency: extract and validate tenant from JWT.

    Also rate-limits — every tier-gated dependency built on top of this one
    (`require_connect`/`require_pro`/`require_team`) inherits the check for
    free, so `api_rate_limit_per_minute` covers every protected route
    without editing each router individually.
    """
    token_data = decode_token(credentials.credentials)

    # Check expiration
    now = int(datetime.now(timezone.utc).timestamp())
    if token_data.exp < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    check_rate_limit(token_data.tenant_id)

    return token_data


def require_tier(minimum: SubscriptionTier):
    """Dependency factory: require a minimum subscription tier."""
    tier_order = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.CONNECT: 1,
        SubscriptionTier.PRO: 2,
        SubscriptionTier.TEAM: 3,
    }

    async def check_tier(tenant: TokenData = Depends(get_current_tenant)) -> TokenData:
        if tier_order.get(tenant.tier, 0) < tier_order[minimum]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {minimum.value} tier or higher. "
                       f"Current tier: {tenant.tier.value}. "
                       f"Upgrade at streamextend.com or creatorextend.com.",
            )
        return tenant

    return check_tier


# Convenience dependencies
require_connect = require_tier(SubscriptionTier.CONNECT)
require_pro = require_tier(SubscriptionTier.PRO)
require_team = require_tier(SubscriptionTier.TEAM)


def _admin_token_matches(candidate: Optional[str]) -> bool:
    # hmac.compare_digest, not `==` — same reasoning as backend-api's
    # require_api_key (modules/backend-api/fastapi/app/deps.py): a naive
    # equality check leaks how many leading characters of a guess are
    # correct via response time. An unset settings.admin_token means this
    # can never match — the route stays unreachable, fail-closed by
    # default, same philosophy as startup_security.py's production checks.
    if not candidate or not settings.admin_token:
        return False
    return hmac.compare_digest(candidate, settings.admin_token)


def require_admin_token(x_admin_token: Annotated[Optional[str], Header()] = None) -> None:
    if not _admin_token_matches(x_admin_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid admin token")
