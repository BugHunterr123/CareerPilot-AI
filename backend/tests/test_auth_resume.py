"""Registration/login rules, mandatory resume upload, invalid resume handling, parsing and editing."""
import io
import uuid

from tests.conftest import SAMPLE, register, upload_sample


def _email():
    return f"u-{uuid.uuid4().hex[:8]}@example.com"


def test_register_login_and_me(client):
    email = _email()
    h = register(client, email)
    assert client.get("/api/auth/me", headers=h).json()["email"] == email
    assert client.post("/api/auth/register", json={"email": email, "password": "secret123", "full_name": "X Y"}).status_code == 409
    assert client.post("/api/auth/login", json={"email": email, "password": "wrong-pass1"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": email.upper(), "password": "secret123"}).status_code == 200


def test_register_validation(client):
    assert client.post("/api/auth/register", json={"email": "not-an-email", "password": "secret123", "full_name": "A B"}).status_code == 422
    assert client.post("/api/auth/register", json={"email": _email(), "password": "short1", "full_name": "A B"}).status_code == 422
    assert client.post("/api/auth/register", json={"email": _email(), "password": "onlyletters", "full_name": "A B"}).status_code == 422


def test_protected_routes_need_token(client):
    for path in ["/api/profile", "/api/skills", "/api/dashboard", "/api/roadmap", "/api/questions"]:
        assert client.get(path).status_code == 401
    assert client.get("/api/profile", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_password_is_hashed(client):
    from app.db import SessionLocal
    from app.models import User
    email = _email()
    register(client, email)
    with SessionLocal() as db:
        u = db.query(User).filter_by(email=email).one()
        assert u.password_hash.startswith("$2") and "secret123" not in u.password_hash


def test_docx_resume_parses(client):
    h = register(client, _email())
    r = upload_sample(client, h, "docx")
    assert r.status_code == 201
    body = r.json()
    assert {"Python", "FastAPI", "MySQL"} <= set(body["parsed"]["skills"])
    assert [p["name"] for p in body["projects"]] == ["Smart Notes API", "Loan Default Predictor", "Campus Events Portal"]
    assert body["parsed"]["education"][0]["score"].startswith("CGPA")


def _upload(client, h, name, data):
    return client.post("/api/resume", headers=h, files={"file": (name, data, "application/octet-stream")})


def test_invalid_resumes_are_rejected_with_clear_messages(client):
    h = register(client, _email())
    cases = [
        ("notes.txt", b"hello world " * 50, "PDF or DOCX"),
        ("fake.pdf", b"MZ this is not a pdf" * 20, "not a real PDF"),
        ("empty.pdf", b"", "empty"),
        ("fake.docx", b"plain text pretending", "not a Word document"),
        ("huge.pdf", b"%PDF-1.4\n" + b"0" * (6 * 1024 * 1024), "larger than"),
    ]
    for name, data, phrase in cases:
        r = _upload(client, h, name, data)
        assert r.status_code == 422, name
        assert phrase.lower() in r.json()["detail"].lower(), (name, r.json())
    # nothing was stored for this user
    assert client.get("/api/resume", headers=h).json() is None


def test_scanned_pdf_without_text_is_refused_not_guessed(client):
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.rect(50, 50, 400, 600, fill=1)  # an "image-only" page: no extractable text
    c.save()
    h = register(client, _email())
    r = _upload(client, h, "scan.pdf", buf.getvalue())
    assert r.status_code == 422 and "scanned" in r.json()["detail"]


def test_review_edits_win_and_update_skills(client, student):
    r = client.get("/api/resume", headers=student).json()
    skills = [s for s in r["parsed"]["skills"] if s != "Java"] + ["Docker"]
    projects = r["parsed"]["projects"] + [{"name": "Docker Deploy", "description": "Containerised the notes API with Docker.", "technologies": ["Docker"]}]
    out = client.put("/api/resume/review", headers=student, json={"skills": skills, "projects": projects,
                                                                  "education": r["parsed"]["education"], "certifications": [], "achievements": []})
    assert out.status_code == 200 and out.json()["reviewed"]
    names = {s["name"]: s["level"] for g in client.get("/api/skills", headers=student).json()["groups"] for s in g["skills"]}
    assert "Java" not in names
    assert names["Docker"] == "project"


def test_profile_and_optional_preferences(client, student):
    r = client.put("/api/profile", headers=student, json={"college": "X", "graduation_year": 2027, "weekly_hours": 12,
                                                          "interests": ["backend", " "], "job_type": "full-time"})
    assert r.status_code == 200 and r.json()["profile"]["interests"] == ["backend"]
    assert client.put("/api/profile", headers=student, json={"graduation_year": 1800}).status_code == 422
    assert client.put("/api/profile", headers=student, json={"job_type": "freelance"}).status_code == 422


def test_resume_delete(client):
    h = register(client, _email())
    upload_sample(client, h)
    assert client.delete("/api/resume", headers=h).status_code == 200
    assert client.get("/api/resume", headers=h).json() is None
