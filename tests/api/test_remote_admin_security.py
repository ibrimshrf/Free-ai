import pytest
from fastapi import HTTPException
from starlette.requests import Request

from free_claude_code.api.admin_security import require_loopback_admin


def _request(*, trusted: bool = False) -> Request:
    headers = [(b"host", b"free-ai.example.com"), (b"origin", b"https://free-ai.example.com")]
    if trusted:
        headers.append((b"x-fcc-trusted-proxy", b"cloudflare"))
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "https",
            "path": "/admin",
            "raw_path": b"/admin",
            "query_string": b"",
            "headers": headers,
            "client": ("203.0.113.10", 44321),
            "server": ("free-ai.example.com", 443),
            "root_path": "",
        }
    )


def test_remote_admin_stays_blocked_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FCC_REMOTE_ADMIN", raising=False)
    with pytest.raises(HTTPException) as exc:
        require_loopback_admin(_request(trusted=True))
    assert exc.value.status_code == 403


def test_remote_admin_requires_trusted_gateway_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FCC_REMOTE_ADMIN", "1")
    with pytest.raises(HTTPException) as exc:
        require_loopback_admin(_request(trusted=False))
    assert exc.value.status_code == 403


def test_remote_admin_allows_trusted_gateway_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FCC_REMOTE_ADMIN", "1")
    require_loopback_admin(_request(trusted=True))
