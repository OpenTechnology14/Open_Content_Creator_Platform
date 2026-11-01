"""Global request body size limit — ASGI middleware.

Rejects a request whose declared `Content-Length` exceeds
`settings.max_request_body_bytes` before any route handler (or body
parsing) runs. Covers every route, including future ones, without
per-router edits.

Known, accepted gap: a request with no `Content-Length` (chunked transfer
encoding) isn't caught here — enforcing that properly means wrapping
Starlette's ASGI `receive` callable, which reaches into private internals
that change across versions and isn't worth the fragility for this API's
threat model (structured JSON clients, not arbitrary uploads). The
per-route `Field(max_length=...)` constraints on the free-form payload
models (sync/metrics/notifications) are the second, independent layer
that still applies regardless of transfer encoding, once the body is
actually parsed into a Pydantic model.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..config import settings


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                too_large = int(content_length) > settings.max_request_body_bytes
            except ValueError:
                too_large = False  # malformed header — let the framework reject it downstream
            if too_large:
                return JSONResponse({"detail": "request body too large"}, status_code=413)

        return await call_next(request)
