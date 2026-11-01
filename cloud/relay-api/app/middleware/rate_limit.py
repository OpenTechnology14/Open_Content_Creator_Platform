"""Per-tenant API rate limiting — an in-memory token bucket.

Wires up `settings.api_rate_limit_per_minute`, which was declared but never
enforced anywhere. Per-process only, same accepted trade-off as
`ws_max_connections_per_tenant` (relay.py) — not shared across
horizontally-scaled instances via Redis. A real cross-instance limiter is
bigger, separate work.

Pure function, no FastAPI/auth imports — `auth.get_current_tenant` calls
this directly so every tier-gated dependency built on top of it
(`require_connect`/`require_pro`/`require_team`) is rate-limited for free,
without a second dependency layer or a circular import between this module
and `auth.py`.
"""
from __future__ import annotations

import time

from fastapi import HTTPException, status

from ..config import settings

# tenant_id -> (tokens_remaining, last_refill_monotonic_seconds)
_buckets: dict[str, tuple[float, float]] = {}


def check_rate_limit(tenant_id: str, now: float | None = None) -> None:
    """Refill by elapsed time, raise 429 if the bucket is empty, else spend one token.

    No `await` between read and write, so this needs no lock — a single
    asyncio worker's event loop never interleaves two calls to a plain
    synchronous function.
    """
    limit = settings.api_rate_limit_per_minute
    now = time.monotonic() if now is None else now

    tokens, last_refill = _buckets.get(tenant_id, (float(limit), now))
    elapsed = max(0.0, now - last_refill)
    tokens = min(float(limit), tokens + elapsed * (limit / 60.0))

    if tokens < 1.0:
        _buckets[tenant_id] = (tokens, now)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="rate limit exceeded",
        )

    _buckets[tenant_id] = (tokens - 1.0, now)
