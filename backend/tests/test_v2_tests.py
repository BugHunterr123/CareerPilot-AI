"""Timed practice tests: coding and MCQ, company scoping, no answer leaks, scoring, expiry."""
from datetime import timedelta

from app.db import SessionLocal
from app.models import PracticeTest
from tests.test_v2_practice import _solution


def _cid(client, h, slug):
    return next(c["id"] for c in client.get("/api/companies", headers=h).json()["companies"] if c["slug"] == slug)


def test_coding_test_flow_and_score(client, student):
    cid = _cid(client, student, "infosys")
    t = client.post("/api/tests", headers=student, json={"kind": "coding", "company_id": cid, "difficulty": "mixed", "count": 3}).json()
    assert len(t["questions"]) == 3 and t["status"] == "active"
    assert [q["difficulty"] for q in t["questions"]] == ["easy", "medium", "hard"]
    assert all(q["company_id"] in (cid, None) for q in t["questions"])
    assert all(not q.get("solution") for q in t["questions"]), "no solutions while the test runs"
    q = t["questions"][0]
    ran = client.post(f"/api/tests/{t['id']}/run", headers=student, params={"qid": q["id"]}, json={"code": _solution(q["title"])}).json()
    assert ran["all_passed"]
    ans = client.post(f"/api/tests/{t['id']}/answer", headers=student, json={"question_id": q["id"], "code": _solution(q["title"])}).json()
    assert ans["passed"] == ans["total"]
    done = client.post(f"/api/tests/{t['id']}/finish", headers=student).json()
    assert done["status"] == "completed" and round(done["score"]) == 33
    assert done["questions"][0]["solution"], "solutions are shown after finishing"
    hist = client.get("/api/tests", headers=student).json()
    assert hist[0]["id"] == t["id"] and hist[0]["status"] == "completed"


def test_mcq_test_hides_answers_until_finish(client, student):
    t = client.post("/api/tests", headers=student, json={"kind": "mcq", "company_id": _cid(client, student, "tcs"), "difficulty": "mixed", "count": 10}).json()
    assert len(t["questions"]) == 10
    assert all(not q["answer"] and not q.get("correct_option") and not q.get("explanation") for q in t["questions"])
    q0 = t["questions"][0]
    client.post(f"/api/tests/{t['id']}/answer", headers=student, json={"question_id": q0["id"], "choice": q0["options"][0]})
    done = client.post(f"/api/tests/{t['id']}/finish", headers=student).json()
    first = done["questions"][0]
    assert first["correct_option"] in first["options"]
    expected = 10.0 if first["my_answer"]["correct"] else 0.0
    assert done["score"] == expected


def test_answer_after_expiry_is_rejected_and_test_auto_finishes(client, student):
    t = client.post("/api/tests", headers=student, json={"kind": "mcq", "company_id": None, "difficulty": "easy", "count": 10}).json()
    with SessionLocal() as db:
        row = db.get(PracticeTest, t["id"])
        row.created_at = row.created_at - timedelta(minutes=row.minutes + 10)
        db.commit()
    q0 = t["questions"][0]
    r = client.post(f"/api/tests/{t['id']}/answer", headers=student, json={"question_id": q0["id"], "choice": q0["options"][0]})
    assert r.status_code in (400, 409)
    assert client.get(f"/api/tests/{t['id']}", headers=student).json()["status"] == "completed"


def test_other_users_cannot_open_my_test(client, student):
    from tests.conftest import register
    t = client.post("/api/tests", headers=student, json={"kind": "mcq", "difficulty": "mixed", "count": 10}).json()
    other = register(client, "test-intruder@example.com")
    assert client.get(f"/api/tests/{t['id']}", headers=other).status_code == 404
