"""Portable imports, explicit admission for the existing POSIX-only runtime."""

from __future__ import annotations

import os

try:
    import fcntl
except ModuleNotFoundError as error:
    if error.name != "fcntl":
        raise
    fcntl = None


def supports_posix() -> bool:
    """Availability is a prerequisite, never an alternative locking implementation."""
    return os.name == "posix" and fcntl is not None and hasattr(os, "O_NOFOLLOW")


def require_posix() -> None:
    """Fail before root, disk or process access when the runtime cannot keep its guards."""
    if not supports_posix():
        # Local import avoids coupling portable module initialization to filesystem classes.
        from .safety import Fault

        raise Fault("platform_unavailable")
