from fastapi.testclient import TestClient

from tests.api.support import create_test_app


def _remote_client(app) -> TestClient:
    return TestClient(
        app,
        base_url="https://free-ai.up.railway.app",
        client=("203.0.113.10", 50000),
    )


def test_railway_admin_requires_basic_auth(monkeypatch):
    monkeypatch.setenv("FCC_REMOTE_ADMIN", "basic")
    monkeypatch.setenv("FCC_WEB_USER", "admin")
    monkeypatch.setenv("FCC_WEB_PASSWORD", "secret")

    response = _remote_client(create_test_app()).get("/admin")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Basic realm="Free AI Admin"'


def test_railway_admin_rejects_wrong_basic_auth(monkeypatch):
    monkeypatch.setenv("FCC_REMOTE_ADMIN", "basic")
    monkeypatch.setenv("FCC_WEB_USER", "admin")
    monkeypatch.setenv("FCC_WEB_PASSWORD", "secret")

    response = _remote_client(create_test_app()).get(
        "/admin",
        auth=("admin", "wrong"),
    )

    assert response.status_code == 401


def test_railway_admin_accepts_valid_basic_auth(monkeypatch):
    monkeypatch.setenv("FCC_REMOTE_ADMIN", "basic")
    monkeypatch.setenv("FCC_WEB_USER", "admin")
    monkeypatch.setenv("FCC_WEB_PASSWORD", "secret")

    response = _remote_client(create_test_app()).get(
        "/admin/code",
        auth=("admin", "secret"),
    )

    assert response.status_code == 200


def test_railway_mode_does_not_trust_cloudflare_header(monkeypatch):
    monkeypatch.setenv("FCC_REMOTE_ADMIN", "basic")
    monkeypatch.setenv("FCC_WEB_USER", "admin")
    monkeypatch.setenv("FCC_WEB_PASSWORD", "secret")

    response = _remote_client(create_test_app()).get(
        "/admin",
        headers={"x-fcc-trusted-proxy": "cloudflare"},
    )

    assert response.status_code == 401


def test_cloudflare_mode_keeps_trusted_proxy_behavior(monkeypatch):
    monkeypatch.setenv("FCC_REMOTE_ADMIN", "cloudflare")

    response = _remote_client(create_test_app()).get(
        "/admin",
        headers={"x-fcc-trusted-proxy": "cloudflare"},
    )

    assert response.status_code == 200
