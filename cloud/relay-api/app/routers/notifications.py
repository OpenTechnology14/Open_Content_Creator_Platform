"""
Push notification router.

Sends push notifications to mobile devices via APNs (iOS) and FCM (Android).
Requires Connect tier ($5/mo) or higher.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import json

from ..middleware.auth import require_connect, TokenData
from ..unavailable import feature_unavailable

router = APIRouter()

# Second, defense-in-depth layer under the global BodySizeLimitMiddleware —
# `data` is arbitrary JSON, the one field here the global byte cap alone
# doesn't meaningfully bound the *shape* of.
MAX_NOTIFICATION_DATA_BYTES = 8_192  # 8 KiB — push payloads are small by nature


class NotificationRequest(BaseModel):
    title: str = Field(max_length=256)
    body: str = Field(max_length=2_048)
    channel: str = "general"  # "stream", "render", "error", "general"
    data: Optional[dict] = None
    device_id: Optional[str] = None  # None = send to all devices

    @field_validator("data")
    @classmethod
    def _bounded_data(cls, v: Optional[dict]) -> Optional[dict]:
        if v is None:
            return v
        size = len(json.dumps(v).encode("utf-8"))
        if size > MAX_NOTIFICATION_DATA_BYTES:
            raise ValueError(f"data exceeds {MAX_NOTIFICATION_DATA_BYTES} bytes serialized ({size})")
        return v


class NotificationResponse(BaseModel):
    sent_to: int
    failed: int


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    body: NotificationRequest,
    tenant: TokenData = Depends(require_connect),
):
    """Send a push notification to the tenant's mobile devices."""
    feature_unavailable("push_delivery")


@router.post("/register-device")
async def register_device(
    device_id: str,
    push_token: str,
    platform: str,
    tenant: TokenData = Depends(require_connect),
):
    """Register a device's push token for notifications."""
    feature_unavailable("push_registration")


async def _send_apns(token: str, title: str, body: str, data: Optional[dict]):
    """Send via Apple Push Notification service."""
    raise NotImplementedError("APNs delivery is unavailable")


async def _send_fcm(token: str, title: str, body: str, data: Optional[dict]):
    """Send via Firebase Cloud Messaging."""
    raise NotImplementedError("FCM delivery is unavailable")
