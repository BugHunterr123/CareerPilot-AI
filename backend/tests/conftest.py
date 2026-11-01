"""
Test setup: a fresh SQLite database (or TEST_DATABASE_URL) in a temp folder, seeded with the real seed data.
No network and no LLM key are used; tests that need the AI path replace the network call with a fake.
"""
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="careerpilot-test-")
# TEST_DATABASE_URL lets the same suite run against PostgreSQL (the database is wiped first)
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{TMP}/test.db"
os.environ["UPLOAD_DIR"] = f"{TMP}/uploads"
os.environ["LLM_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["LLM_PROVIDER"] = "none"
os.environ["RATE_LIMIT_AUTH"] = "1000/minute"
os.environ["RATE_LIMIT_AI"] = "1000/minute"
os.environ["RATE_LIMIT_CODE"] = "1000/minute"
os.environ["GITHUB_ENABLED"] = "false"
os.environ["FRONTEND_DIR"] = f"{TMP}/no-frontend"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
import app.models  # noqa: E402,F401
from app.main import app  # noqa: E402
from app.services.seed import seed_all  # noqa: E402

SAMPLE = Path(__file__).resolve().parent.parent / "sample_data"

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
with SessionLocal() as _db:
    seed_all(_db)


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _fresh_cookies(client):
    client.cookies.clear()
    yield
    client.cookies.clear()


def register(client, email: str, name: str = "Test Student") -> dict:
    r = client.post("/api/auth/register", json={"email": email, "password": "secret123", "full_name": name})
    assert r.status_code == 201, r.text
    client.cookies.clear()  # tests authenticate with the Bearer header; cookie flow has its own tests
    return {"Authorization": f"Bearer {r.json()['token']}"}


def upload_sample(client, headers, kind: str = "pdf"):
    path = SAMPLE / f"sample_resume.{kind}"
    with open(path, "rb") as f:
        return client.post("/api/resume", headers=headers, files={"file": (path.name, f.read(), "application/octet-stream")})


@pytest.fixture
def student(client):
    import uuid
    headers = register(client, f"student-{uuid.uuid4().hex[:8]}@example.com")
    r = upload_sample(client, headers)
    assert r.status_code == 201, r.text
    return headers


class FakeLLM:
    """Replaces the HTTP call to the AI provider. `handler(body) -> str | httpx.Response` decides the reply."""

    def __init__(self):
        self.calls: list[dict] = []
        self.handler = lambda body: "ok"

    def __call__(self, url, headers, body, timeout):
        import httpx
        self.calls.append({"url": url, "headers": headers, "body": body})
        out = self.handler(body)
        if isinstance(out, httpx.Response):
            return out
        return httpx.Response(200, json={"choices": [{"message": {"content": out}}]})


@pytest.fixture
def fake_llm(monkeypatch):
    """Turn the AI layer on (Gemini provider, fake key) with the network call replaced."""
    from app.config import settings
    from app.services import llm
    fake = FakeLLM()
    monkeypatch.setattr(settings, "llm_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(llm, "_send", fake)
    monkeypatch.setattr(llm.time, "sleep", lambda s: None, raising=False)
    return fake


def cookie_session(client, email: str, password: str = "secret123"):
    """Log in the way the browser does: cookie + the X-Requested-With header."""
    client.cookies.clear()
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"X-Requested-With": "careerpilot"}
