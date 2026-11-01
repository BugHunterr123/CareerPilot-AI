"""One student must never see or change another student's data."""
import uuid

from tests.conftest import register, upload_sample


def _student(client):
    h = register(client, f"iso-{uuid.uuid4().hex[:8]}@example.com")
    upload_sample(client, h)
    return h


def test_users_cannot_touch_each_others_data(client):
    a, b = _student(client), _student(client)
    plan = client.post("/api/roadmap/generate", headers=a, json={}).json()
    task_id = plan["tasks"][0]["id"]
    mi = client.post("/api/interviews", headers=a, json={"itype": "hr", "duration_min": 9}).json()
    app_ = client.post("/api/applications", headers=a, json={"company_name": "Acme"}).json()
    link = client.post("/api/profile/links", headers=a, json={"kind": "linkedin", "url": "https://linkedin.com/in/a", "consent": True}).json()
    skill_id = client.get("/api/skills", headers=a).json()["groups"][0]["skills"][0]["id"]

    # B gets 404 (not 403) so B cannot even learn that A's records exist
    assert client.patch(f"/api/roadmap/tasks/{task_id}", headers=b, json={"status": "done"}).status_code == 404
    assert client.get(f"/api/interviews/{mi['id']}", headers=b).status_code == 404
    assert client.post(f"/api/interviews/{mi['id']}/answer", headers=b, json={"answer": "hi"}).status_code == 404
    assert client.put(f"/api/applications/{app_['id']}", headers=b, json={"company_name": "Hacked"}).status_code == 404
    assert client.delete(f"/api/applications/{app_['id']}", headers=b).status_code == 404
    assert client.delete(f"/api/profile/links/{link['id']}", headers=b).status_code == 404
    assert client.delete(f"/api/skills/{skill_id}", headers=b).status_code == 404

    # B's own lists never include A's records
    assert client.get("/api/interviews", headers=b).json() == []
    assert client.get("/api/profile", headers=b).json()["links"] == []
    assert client.get("/api/roadmap", headers=b).json() is None
    # A's data is untouched
    assert client.get(f"/api/interviews/{mi['id']}", headers=a).status_code == 200
    assert client.get("/api/progress", headers=a).json()["applications"][0]["company_name"] == "Acme"


def test_delete_account_removes_everything(client):
    from app.db import SessionLocal
    from app.models import Resume, Skill, User
    email = f"bye-{uuid.uuid4().hex[:8]}@example.com"
    h = register(client, email)
    upload_sample(client, h)
    client.post("/api/roadmap/generate", headers=h, json={})
    assert client.request("DELETE", "/api/privacy/account", headers=h, json={"password": "wrong-pass1"}).status_code == 403
    export = client.get("/api/privacy/export", headers=h).json()
    assert export["user"]["email"] == email and export["skills"]
    with SessionLocal() as db:
        uid = db.query(User).filter_by(email=email).one().id
        path = db.query(Resume).filter_by(user_id=uid).one().stored_path
    assert client.request("DELETE", "/api/privacy/account", headers=h, json={"password": "secret123"}).status_code == 200
    with SessionLocal() as db:
        assert db.query(User).filter_by(email=email).count() == 0
        assert db.query(Skill).filter_by(user_id=uid).count() == 0
        assert db.query(Resume).filter_by(user_id=uid).count() == 0
    import os
    assert not os.path.exists(path)
