"""Practice bank: filters, tested coding coverage per company, the code runner and hidden tests."""
import json
from pathlib import Path

import pytest

from app.services.code_runner import run_python

PRACTICE = Path(__file__).resolve().parent.parent / "app" / "seed" / "data" / "practice"
SLUGS = sorted(p.stem for p in PRACTICE.glob("*.json"))


def _solution(title: str) -> str:
    for p in PRACTICE.glob("*.json"):
        for q in json.loads(p.read_text())["coding"]:
            if q["title"] == title:
                return q["solution"]
    raise KeyError(title)


def test_rahuls_filter_combination_returns_questions(client, student):
    """Infosys + Coding + medium + AI practice used to return 'No questions'."""
    r = client.get("/api/questions", headers=student, params={"company": "infosys", "qtype": "coding", "difficulty": "medium", "label": "AI practice"})
    assert r.status_code == 200 and r.json()["total"] > 0
    assert all(q["runnable"] for q in r.json()["items"])


@pytest.mark.parametrize("slug", SLUGS)
def test_every_company_has_runnable_easy_medium_hard(client, student, slug):
    items = client.get("/api/questions", headers=student, params={"company": slug, "qtype": "coding", "page_size": 50}).json()["items"]
    runnable = [q for q in items if q["runnable"]]
    for level in ("easy", "medium", "hard"):
        assert sum(q["difficulty"] == level for q in runnable) >= 2, (slug, level)


def test_facets_only_offer_existing_values(client, student):
    f = client.get("/api/questions/facets", headers=student, params={"company": "infosys", "qtype": "coding"}).json()
    for s in f["subject_counts"]:
        n = client.get("/api/questions", headers=student, params={"company": "infosys", "qtype": "coding", "subject": s["value"]}).json()["total"]
        assert n == s["count"] > 0


def test_language_is_not_a_filter(client, student):
    """Solutions come in several languages, but the list never hides questions by language."""
    base = client.get("/api/questions", headers=student, params={"company": "tcs", "qtype": "coding"}).json()["total"]
    with_lang = client.get("/api/questions", headers=student, params={"company": "tcs", "qtype": "coding", "language": "java"}).json()["total"]
    assert base == with_lang > 0
    q = client.get("/api/questions", headers=student, params={"company": "tcs", "qtype": "coding"}).json()["items"][0]
    assert {"java", "cpp"} <= set(q["solutions_other"])


def test_run_shows_visible_tests_and_hides_hidden_data(client, student):
    q = client.get("/api/questions", headers=student, params={"company": "infosys", "qtype": "coding", "difficulty": "easy"}).json()["items"][0]
    assert q["visible_tests"] and q["hidden_test_count"] >= 1
    assert "tests" not in q  # hidden test data never reaches the browser
    r = client.post(f"/api/questions/{q['id']}/run", headers=student, json={"code": q["starter_code"]}).json()
    assert r["total"] == len(q["visible_tests"]) and all(not x["hidden"] for x in r["results"])


def test_submit_reference_solution_passes_all_tests(client, student):
    q = client.get("/api/questions", headers=student, params={"company": "wipro", "qtype": "coding", "difficulty": "hard"}).json()["items"][0]
    r = client.post(f"/api/questions/{q['id']}/submit", headers=student, json={"code": _solution(q["title"])}).json()
    assert r["all_passed"] and r["total"] > len(q["visible_tests"])
    hidden = [x for x in r["results"] if x["hidden"]]
    assert hidden and all("input" not in x and "expected" not in x for x in hidden)
    stats = client.get("/api/questions/facets", headers=student).json()["mine"]
    assert stats["attempts"] >= 1


def test_wrong_code_fails_with_details(client, student):
    q = client.get("/api/questions", headers=student, params={"company": "infosys", "qtype": "coding"}).json()["items"][0]
    r = client.post(f"/api/questions/{q['id']}/run", headers=student, json={"code": "print('definitely wrong')"}).json()
    assert r["passed"] == 0 and r["results"][0]["output"].strip() == "definitely wrong"


def test_custom_input_run(client, student):
    q = client.get("/api/questions", headers=student, params={"company": "infosys", "qtype": "coding"}).json()["items"][0]
    r = client.post(f"/api/questions/{q['id']}/run", headers=student, json={"code": "print(input()[::-1])", "stdin": "abc"}).json()
    assert r["status"] == "ok" and r["stdout"].strip() == "cba"


@pytest.mark.parametrize("code,status", [
    ("while True:\n    pass", "timeout"),
    ("print(open('/etc/passwd').read())", "blocked"),
    ("open('x.txt', 'w').write('hi')", "blocked"),
    ("import os\nos.system('ls')", "error"),
    ("import socket", "error"),
    ("print(1", "error"),
])
def test_sandbox_blocks_dangerous_code(code, status):
    r = run_python(code, "", timeout=2)
    assert r["status"] == status, r


def test_mcq_attempt_returns_correct_option(client, student):
    q = client.get("/api/questions", headers=student, params={"company": "tcs", "qtype": "mcq"}).json()["items"][0]
    r = client.post(f"/api/questions/{q['id']}/attempt", headers=student, json={"response": q["options"][0]}).json()
    assert r["correct_option"] in q["options"]
    assert r["correct"] == (r["correct_option"] == q["options"][0])
