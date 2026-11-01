"""Mock interviews: per-session reports, fresh questions per session, AI scoring with verified quotes."""
import json


def _start(client, h, **kw):
    body = {"itype": "mixed", "difficulty": "medium", "duration_min": 9, **kw}
    r = client.post("/api/interviews", headers=h, json=body)
    assert r.status_code in (200, 201), r.text
    return r.json()


def _answer(client, h, mi, text):
    return client.post(f"/api/interviews/{mi['id']}/answer", headers=h, json={"answer": text}).json()


def test_report_only_contains_this_sessions_answers(client, student):
    a = _start(client, student)
    a = _answer(client, student, a, "First session answer about OOP: encapsulation keeps state private, for example a BankAccount class.")
    a = client.post(f"/api/interviews/{a['id']}/finish", headers=student).json()
    b = _start(client, student)
    b = _answer(client, student, b, "Second session: I handled a team conflict by listening first and splitting the work by strengths.")
    b = client.post(f"/api/interviews/{b['id']}/finish", headers=student).json()
    assert b["report"]["interview_id"] == b["id"] and a["report"]["interview_id"] == a["id"]
    assert b["report"]["answered"] == 1 and len(b["report"]["questions"]) == 1
    assert "Second session" in json.dumps(b["responses"]) and "First session" not in json.dumps(b["report"])
    hist = client.get("/api/interviews", headers=student).json()
    assert {a["id"], b["id"]} <= {h["id"] for h in hist}


def test_new_sessions_avoid_recent_questions(client, student):
    seen = []
    for _ in range(2):
        mi = _start(client, student, itype="technical", role_key="software_developer")
        seen.append({x["q"] for x in mi["plan"]} if "plan" in mi else {mi["current_question"]["q"]})
    assert seen[0] != seen[1]


def test_role_and_company_shape_the_questions(client, student):
    cid = next(c["id"] for c in client.get("/api/companies", headers=student).json()["companies"] if c["slug"] == "infosys")
    mi = _start(client, student, role_key="data_engineer", company_id=cid, itype="technical", duration_min=24)
    assert mi["company_name"] == "Infosys" and mi["role_key"] == "data_engineer"
    assert mi["current_question"]["origin"]


def test_ai_scoring_uses_rubric_and_verified_quote(client, student, fake_llm):
    answer = "Normalisation removes redundancy. For example I split a students table into students and courses because names repeated."

    def handler(body):
        prompt = json.dumps(body["messages"])
        if "question set" in prompt:
            return json.dumps({"questions": [{"question": "Explain normalisation with an example.", "kind": "technical", "topic": "DBMS",
                                              "key_points": ["redundancy", "anomalies", "1NF 2NF 3NF"]}] * 1})
        return json.dumps({"concepts": {"score": 3, "reason": "Mentions redundancy."}, "depth": {"score": 3, "reason": "Has an example."},
                           "structure": {"score": 4, "reason": "Definition then example."}, "clarity": {"score": 4, "reason": "Clear."},
                           "good": ["Gave a concrete example"], "missing": ["update anomalies"],
                           "quote": "I split a students table into students and courses", "better_answer": "Define it, name 1NF to 3NF, give the example."})

    fake_llm.handler = handler
    mi = _start(client, student, duration_min=9)
    assert mi["scoring_mode"] == "llm"
    assert mi["current_question"]["q"] == "Explain normalisation with an example."
    mi = _answer(client, student, mi, answer)
    fb = mi["responses"][0]["feedback"]
    assert fb["engine"] == "llm" and fb["quote"] in answer and "update anomalies" in fb["missing"]
    assert mi["responses"][0]["scores"]["structure"]["score"] == 4


def test_ai_quote_not_in_answer_is_dropped(client, student, fake_llm):
    def handler(body):
        if "question set" in json.dumps(body["messages"]):
            return "not json"  # plan fails twice -> bank questions
        return json.dumps({"concepts": {"score": 2, "reason": "x"}, "depth": {"score": 2, "reason": "x"},
                           "structure": {"score": 2, "reason": "x"}, "clarity": {"score": 2, "reason": "x"},
                           "good": [], "missing": [], "quote": "words the student never said", "better_answer": ""})
    fake_llm.handler = handler
    mi = _start(client, student)
    assert len(mi["plan"] if "plan" in mi else [1]) >= 1 and mi["total_questions"] == 3
    mi = _answer(client, student, mi, "I would use a hash map to count frequencies in one pass.")
    assert not mi["responses"][0]["feedback"].get("quote")


def test_ai_failure_falls_back_to_rule_scoring(client, student, fake_llm):
    import httpx
    fake_llm.handler = lambda body: httpx.Response(503, text="overloaded")
    mi = _start(client, student)
    mi = _answer(client, student, mi, "Encapsulation means keeping data private and exposing methods, for example a BankAccount class.")
    assert mi["responses"][0]["feedback"]["engine"] == "rules"
