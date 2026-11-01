"""
Tenant model — represents a subscriber (person or team).
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class SubscriptionTier(str, Enum):
    FREE = "free"
    CONNECT = "connect"
    PRO = "pro"
    TEAM = "team"


class Tenant(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    tier: SubscriptionTier = SubscriptionTier.FREE
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class Device(BaseModel):
    id: str
    tenant_id: str
    name: str
    product: str  # "stream_extend" or "creator_extend"
    platform: str  # "macos", "windows", "linux", "ios", "android"
    push_token: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime


class TenantCreate(BaseModel):
    email: str
    name: Optional[str] = None


class PurchaseVerification(BaseModel):
    receipt: str
    store: str  # "apple", "google", "microsoft"
    product: str  # "stream_extend" or "creator_extend"


class SubscriptionUpdate(BaseModel):
    tier: SubscriptionTier
    stripe_subscription_id: Optional[str] = None
