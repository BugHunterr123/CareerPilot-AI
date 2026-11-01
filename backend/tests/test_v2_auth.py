"""v2 auth: httpOnly cookie sessions, logout, CSRF header, password change, protected routes."""
import uuid

from tests.conftest import cookie_session, register


def _email():
    return f"auth-{uuid.uuid4().hex[:8]}@example.com"


def test_login_sets_httponly_cookie_and_me_works(client):
    email = _email()
    register(client, email)
    r = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    assert r.status_code == 200
    cookie = r.headers["set-cookie"]
    assert "cp_session=" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie.replace("Lax", "lax")
    me = client.get("/api/auth/me")
    assert me.status_code == 200 and me.json()["email"] == email


def test_logout_clears_session(client):
    email = _email()
    register(client, email)
    h = cookie_session(client, email)
    assert client.post("/api/auth/logout", headers=h).status_code == 204
    client.cookies.clear()  # the browser drops the cookie when told to (Max-Age=0)
    assert client.get("/api/auth/me").status_code == 401


def test_logout_response_expires_cookie(client):
    email = _email()
    register(client, email)
    h = cookie_session(client, email)
    r = client.post("/api/auth/logout", headers=h)
    assert 'cp_session=""' in r.headers["set-cookie"] or "Max-Age=0" in r.headers["set-cookie"]


def test_cookie_post_without_csrf_header_is_rejected(client):
    email = _email()
    register(client, email)
    cookie_session(client, email)
    r = client.post("/api/assistant", json={"message": "hello"})
    assert r.status_code == 403
    r = client.post("/api/assistant", json={"message": "hello"}, headers={"X-Requested-With": "careerpilot"})
    assert r.status_code == 200


def test_protected_routes_need_login(client):
    for path in ["/api/auth/me", "/api/profile", "/api/dashboard", "/api/tests", "/api/interviews", "/api/assistant"]:
        assert client.get(path).status_code == 401, path


def test_password_change_signs_out_old_sessions(client):
    email = _email()
    old_bearer = register(client, email)
    h = cookie_session(client, email)
    bad = client.post("/api/auth/password", headers=h, json={"current_password": "wrong-one", "new_password": "newsecret456"})
    assert bad.status_code == 400
    ok = client.post("/api/auth/password", headers=h, json={"current_password": "secret123", "new_password": "newsecret456"})
    assert ok.status_code == 200
    assert client.get("/api/auth/me").status_code == 200  # this browser got a fresh cookie
    client.cookies.clear()
    assert client.get("/api/auth/me", headers=old_bearer).status_code == 401  # older tokens stop working
    assert client.post("/api/auth/login", json={"email": email, "password": "secret123"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": email, "password": "newsecret456"}).status_code == 200


def test_duplicate_signup_and_bad_login_messages(client):
    email = _email()
    register(client, email)
    r = client.post("/api/auth/register", json={"email": email, "password": "secret123", "full_name": "Again"})
    assert r.status_code == 409
    r = client.post("/api/auth/login", json={"email": email, "password": "nope-nope"})
    assert r.status_code == 401 and "password" in r.json()["detail"].lower()


def test_auth_rate_limit(client, monkeypatch):
    from app import ratelimit
    monkeypatch.setattr(ratelimit.settings, "rate_limit_auth", "3/minute")
    ratelimit.reset()
    codes = [client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x" * 8}).status_code for _ in range(5)]
    ratelimit.reset()
    assert codes[:3] == [401, 401, 401] and codes[-1] == 429


def test_session_endpoint_never_401s(client):
    r = client.get("/api/auth/session")
    assert r.status_code == 200 and r.json() == {"authenticated": False, "user": None}
    email = _email()
    register(client, email)
    cookie_session(client, email)
    s = client.get("/api/auth/session").json()
    assert s["authenticated"] and s["user"]["email"] == email
