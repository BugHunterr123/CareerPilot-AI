"""Production basics: health, headers, database URL handling, SPA serving safety, no demo leftovers."""
from pathlib import Path


def test_health_checks_database(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["database"] == "ok" and r.json()["version"].startswith("2.")


def test_security_headers(client):
    r = client.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "referrer-policy" in r.headers


def test_postgres_url_is_normalised():
    from app.config import Settings
    s = Settings(database_url="postgres://u:p@host:5432/db", secret_key="x" * 40)
    assert s.db_url.startswith("postgresql+psycopg://") or s.db_url.startswith("postgresql://")


def test_production_requires_secret_key(monkeypatch):
    import pytest
    from app.config import Settings, get_settings
    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "")
    try:
        with pytest.raises(Exception):
            get_settings()
    finally:
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-pytest-only")
        get_settings.cache_clear()
    assert Settings(secret_key="abc").secret_key == "abc"


def test_no_demo_mode_left_in_frontend():
    root = Path(__file__).resolve().parents[2] / "frontend"
    if not root.exists():
        return
    hits = []
    for p in list((root / "app").rglob("*.tsx")) + list((root / "lib").rglob("*.ts")) + list((root / "components").rglob("*.tsx")):
        text = p.read_text()
        if "DEMO_STATIC" in text or "demo_mode" in text or "tokenStore" in text:
            hits.append(str(p))
    assert not hits, hits


def test_unknown_api_route_is_json_404(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404 and r.headers["content-type"].startswith("application/json")
