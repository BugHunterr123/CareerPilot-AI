"""Companies, question filters, gaps, roadmap edits, interview flow, assistant grounding, migrations."""
from tests.conftest import register


def test_ten_companies_seeded_with_resolvable_sources(client, student):
    comps = client.get("/api/companies", headers=student).json()["companies"]
    assert len(comps) == 10
    for c in comps:
        d = client.get(f"/api/companies/{c['slug']}", headers=student).json()
        assert d["stages"] and d["sources"]
        for st in d["stages"]:
            assert st["label"] in {"Official", "Candidate-reported", "Third-party", "AI practice"}
            for f in st["format"]:
                assert f["source"] in d["sources"], (c["slug"], f)
        for s in d["sources"].values():
            assert s["url"].startswith("http") and s["label"]
    assert client.get("/api/companies/not-a-company", headers=student).status_code == 404


def test_question_filters(client, student):
    tcs = client.get("/api/questions?company=tcs", headers=student).json()
    assert tcs["total"] > 0
    mcq = client.get("/api/questions?qtype=mcq&difficulty=easy", headers=student).json()
    assert all(q["qtype"] == "mcq" and q["difficulty"] == "easy" for q in mcq["items"])
    ai = client.get("/api/questions?label=AI%20practice", headers=student).json()
    assert all(q["label"] == "AI practice" for q in ai["items"])
    q = mcq["items"][0]
    wrong = next(o for o in q["options"] if not q["answer"].strip().upper().startswith("ABCD"[q["options"].index(o)]))
    r = client.post(f"/api/questions/{q['id']}/attempt", headers=student, json={"response": wrong}).json()
    assert r["correct"] is False
    assert any(x["id"] == q["id"] for x in client.get("/api/questions?incorrect=true", headers=student).json()["items"])
    client.post(f"/api/questions/{q['id']}/save", headers=student)
    assert client.get("/api/questions?saved=true", headers=student).json()["total"] == 1


def test_gaps_with_job_description(client, student):
    r = client.post("/api/gaps", headers=student, json={"role_key": "data_analyst", "job_description": "Must know Tableau and Power BI."}).json()
    skills = {i["skill"]: i for i in r["items"]}
    assert r["job_description_used"] and "Power BI" in skills
    assert skills["Power BI"]["status"] == "missing" and skills["Power BI"]["priority"] in {"high", "medium"}


def test_general_plan_without_company_and_task_edits(client):
    h = register(client, "plain@example.com")
    from tests.conftest import upload_sample
    upload_sample(client, h)
    plan = client.post("/api/roadmap/generate", headers=h, json={"weekly_hours": 6, "use_target_company": False}).json()
    assert plan["plan_type"] == "General role-based plan" and plan["tasks"]
    t = plan["tasks"][0]
    assert client.patch(f"/api/roadmap/tasks/{t['id']}", headers=h, json={"status": "done"}).json()["status"] == "done"
    assert client.patch(f"/api/roadmap/tasks/{t['id']}", headers=h, json={"status": "bogus"}).status_code == 422
    again = client.post("/api/roadmap/generate", headers=h, json={"weekly_hours": 6, "use_target_company": False}).json()
    assert t["topic"] not in [x["topic"] for x in again["tasks"]]  # finished work is not re-planned


def test_interview_flow_and_report(client, student):
    mi = client.post("/api/interviews", headers=student, json={"itype": "technical", "duration_min": 9}).json()
    n = mi["total_questions"]
    for _ in range(n):
        mi = client.post(f"/api/interviews/{mi['id']}/answer", headers=student,
                         json={"answer": "First, a primary key uniquely identifies a row. For example, in my project I used it. Because it avoids duplicates."}).json()
    assert mi["status"] == "completed"
    rep = mi["report"]
    assert set(rep["criteria"]) == {"concepts", "depth", "structure", "clarity"} and "disclaimer" in rep
    assert client.post(f"/api/interviews/{mi['id']}/answer", headers=student, json={"answer": "late"}).status_code == 409


def test_assistant_is_grounded_and_admits_unknowns(client, student):
    r = client.post("/api/assistant", headers=student, json={"message": "What should I study today?"}).json()
    assert r["role"] == "assistant" and r["content"]
    r2 = client.post("/api/assistant", headers=student, json={"message": "What is the exact cutoff score for Thales in 2031?"}).json()
    assert any(w in r2["content"].lower() for w in ["not", "don't", "do not", "no "])
    assert len(client.get("/api/assistant", headers=student).json()) == 4


def test_alembic_migration_builds_schema(tmp_path):
    import subprocess, sys, os
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{tmp_path}/m.db"}
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    import sqlite3
    tables = {x[0] for x in sqlite3.connect(tmp_path / "m.db").execute("select name from sqlite_master where type='table'")}
    assert {"users", "resumes", "skills", "companies", "roadmap_tasks", "mock_interviews"} <= tables
