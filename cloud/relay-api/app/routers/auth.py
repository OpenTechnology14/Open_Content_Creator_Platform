"""
Authentication router.

Handles:
- App store purchase verification → JWT
- Stripe subscription management → JWT
- Self-hosted API key generation
- Token refresh
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..middleware.auth import create_token, get_current_tenant, TokenData
from ..models import PurchaseVerification, SubscriptionTier
from ..unavailable import feature_unavailable

router = APIRouter()


class AuthResponse(BaseModel):
    jwt: str
    tenant_id: str
    tier: str
    expires_in: int


class SelfHostedKeyRequest(BaseModel):
    name: str


class SelfHostedKeyResponse(BaseModel):
    api_key: str
    name: str


@router.post("/verify-purchase", response_model=AuthResponse)
async def verify_purchase(body: PurchaseVerification):
    """Verify an app store purchase receipt and return a JWT.

    Flow:
    1. App sends receipt from Apple/Google/Microsoft store
    2. We validate with the respective store API
    3. Create or find tenant
    4. Return JWT with tenant_id
    """
    feature_unavailable("purchase_verification")


@router.post("/subscribe", response_model=AuthResponse)
async def subscribe(
    tier: SubscriptionTier,
    tenant: TokenData = Depends(get_current_tenant),
):
    """Upgrade subscription tier via Stripe.

    The Tauri app opens a Stripe Checkout session. After payment,
    Stripe webhook updates the tenant tier. This endpoint returns
    a new JWT with the updated tier.
    """
    feature_unavailable("subscription_checkout")


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(tenant: TokenData = Depends(get_current_tenant)):
    """Refresh an existing JWT before it expires."""
    token = create_token(
        tenant_id=tenant.tenant_id,
        tier=tenant.tier,
        device_id=tenant.device_id,
    )

    return AuthResponse(
        jwt=token,
        tenant_id=tenant.tenant_id,
        tier=tenant.tier.value,
        expires_in=720 * 3600,
    )


@router.post("/self-hosted-key", response_model=SelfHostedKeyResponse)
async def create_self_hosted_key(
    body: SelfHostedKeyRequest,
    tenant: TokenData = Depends(get_current_tenant),
):
    """Generate an API key for self-hosted relay connections.

    Self-hosted users run their own relay and need API keys
    for their devices to authenticate.
    """
    feature_unavailable("self_hosted_key_issuance")
