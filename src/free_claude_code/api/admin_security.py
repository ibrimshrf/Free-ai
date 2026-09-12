"""Shared security boundary for Admin product surfaces."""

import base64
import hmac
import ipaddress
import os
from urllib.parse import urlsplit

from fastapi import HTTPException, Request

_REMOTE_ADMIN_ENV = "FCC_REMOTE_ADMIN"
_WEB_USER_ENV = "FCC_WEB_USER"
_WEB_PASSWORD_ENV = "FCC_WEB_PASSWORD"
_TRUSTED_PROXY_HEADER = "x-fcc-trusted-proxy"
_TRUSTED_PROXY_VALUE = "cloudflare"
_BASIC_REALM = "Free AI Admin"


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


def _remote_admin_mode() -> str:
    return os.getenv(_REMOTE_ADMIN_ENV, "").strip().lower()


def _trusted_remote_admin(request: Request) -> bool:
    mode = _remote_admin_mode()
    if mode not in {"1", "true", "yes", "on", "cloudflare"}:
        return False
    marker = request.headers.get(_TRUSTED_PROXY_HEADER)
    return marker is not None and hmac.compare_digest(marker, _TRUSTED_PROXY_VALUE)


def _basic_remote_admin(request: Request) -> bool:
    if _remote_admin_mode() not in {"basic", "railway"}:
        return False

    expected_user = os.getenv(_WEB_USER_ENV)
    expected_password = os.getenv(_WEB_PASSWORD_ENV)
    if not expected_user or not expected_password:
        return False

    authorization = request.headers.get("authorization")
    if not authorization:
        return False

    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "basic" or not token:
        return False

    try:
        raw = base64.b64decode(token, validate=True)
    except (ValueError, TypeError):
        return False

    supplied_user, separator, supplied_password = raw.partition(b":")
    if not separator:
        return False

    user_ok = hmac.compare_digest(supplied_user, expected_user.encode("utf-8"))
    password_ok = hmac.compare_digest(
        supplied_password,
        expected_password.encode("utf-8"),
    )
    return user_ok and password_ok


def _raise_basic_auth_required() -> None:
    if _remote_admin_mode() in {"basic", "railway"}:
        if os.getenv(_WEB_USER_ENV) and os.getenv(_WEB_PASSWORD_ENV):
            raise HTTPException(
                status_code=401,
                detail="Admin authentication required",
                headers={"WWW-Authenticate": f'Basic realm="{_BASIC_REALM}"'},
            )
        raise HTTPException(
            status_code=503,
            detail="Remote Admin credentials are not configured",
        )


def require_loopback_admin(request: Request) -> None:
    """Allow local Admin access or an explicitly authenticated remote gateway."""

    if _trusted_remote_admin(request) or _basic_remote_admin(request):
        return

    client_host = request.client.host if request.client else None
    if not _is_loopback_host(client_host):
        _raise_basic_auth_required()
        raise HTTPException(status_code=403, detail="Admin UI is local-only")
    if not _authority_is_local(request.headers.get("host")):
        _raise_basic_auth_required()
        raise HTTPException(status_code=403, detail="Admin UI is local-only")
    if not _origin_is_local(request.headers.get("origin")):
        _raise_basic_auth_required()
        raise HTTPException(status_code=403, detail="Admin UI is local-only")
