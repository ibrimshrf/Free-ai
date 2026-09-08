"""Shared security boundary for Admin product surfaces."""

import hmac
import ipaddress
import os
from urllib.parse import urlsplit

from fastapi import HTTPException, Request

_REMOTE_ADMIN_ENV = "FCC_REMOTE_ADMIN"
_TRUSTED_PROXY_HEADER = "x-fcc-trusted-proxy"
_TRUSTED_PROXY_VALUE = "cloudflare"


def _is_loopback_host(host: str | None) -> bool:
    if host is None:
        return False
    normalized = host.strip().strip("[]").lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _origin_is_local(origin: str | None) -> bool:
    if not origin:
        return True
    try:
        parsed = urlsplit(origin)
        _ = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and parsed.username is None
        and parsed.password is None
        and not parsed.path
        and not parsed.query
        and not parsed.fragment
        and _is_loopback_host(parsed.hostname)
    )


def _authority_is_local(authority: str | None) -> bool:
    if not authority:
        return False
    try:
        parsed = urlsplit(f"//{authority}")
        _ = parsed.port
    except ValueError:
        return False
    return (
        parsed.username is None
        and parsed.password is None
        and not parsed.path
        and not parsed.query
        and not parsed.fragment
        and _is_loopback_host(parsed.hostname)
    )


def _trusted_remote_admin(request: Request) -> bool:
    enabled = os.getenv(_REMOTE_ADMIN_ENV, "").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return False
    marker = request.headers.get(_TRUSTED_PROXY_HEADER)
    return marker is not None and hmac.compare_digest(marker, _TRUSTED_PROXY_VALUE)


def require_loopback_admin(request: Request) -> None:
    """Allow local Admin access or an explicitly trusted deployment gateway."""

    if _trusted_remote_admin(request):
        return

    client_host = request.client.host if request.client else None
    if not _is_loopback_host(client_host):
        raise HTTPException(status_code=403, detail="Admin UI is local-only")
    if not _authority_is_local(request.headers.get("host")):
        raise HTTPException(status_code=403, detail="Admin UI is local-only")
    if not _origin_is_local(request.headers.get("origin")):
        raise HTTPException(status_code=403, detail="Admin UI is local-only")
