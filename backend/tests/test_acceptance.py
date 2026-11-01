"""
THE acceptance test from the project brief (section 27):
create an account, upload a resume, skip every optional external profile, and still get
career recommendations, select a company, view its hiring guide, generate a plan,
practise questions and use mock interviews.
"""
import time

from tests.conftest import register, upload_sample


def test_resume_only_student_journey(client):
    h = register(client, "acceptance@example.com", "Ananya Rao")

    # 1. mandatory basic profile
    r = client.put("/api/profile", headers=h, json={"college": "Sample Institute of Technology", "degree": "B.E.",
                                                    "branch": "CSE", "graduation_year": 2027})
    assert r.status_code == 200

    # 2. upload the (synthetic) resume
    r = upload_sample(client, h)
    assert r.status_code == 201, r.text
    resume = r.json()
    assert "Python" in resume["parsed"]["skills"]
    assert len(resume["projects"]) == 3

    # 3. skip every optional link
    assert client.post("/api/profile/optional-done", headers=h).status_code == 200
    assert client.get("/api/profile", headers=h).json()["links"] == []

    # 4. skills + career recommendations from the resume alone
    skills = client.get("/api/skills", headers=h).json()
    assert skills["basis"]["limited_info"] is True and skills["total"] > 10
    careers = client.get("/api/careers", headers=h).json()
    assert len(careers["roles"]) >= 5 and careers["roles"][0]["match_pct"] > 0
    top = careers["roles"][0]
    assert top["why"] and "missing" in top
    assert client.post("/api/careers/select", headers=h, json={"role_key": "backend_developer"}).status_code == 200

    # 5. select a company and view its hiring guide with sources
    companies = client.get("/api/companies", headers=h).json()["companies"]
    assert any(c["slug"] == "accenture" for c in companies)
    guide = client.get("/api/companies/accenture", headers=h).json()
    assert len(guide["stages"]) >= 4
    for stage in guide["stages"]:
        for line in stage["format"]:
            assert line["source"] in guide["sources"], "every format claim must point to a source"
    assert client.post("/api/companies/accenture/select", headers=h, json={}).status_code == 200

    # 6. gap analysis + preparation plan (timed for the impact section)
    gap = client.post("/api/gaps", headers=h, json={"role_key": "backend_developer", "company_id": guide["id"]}).json()
    assert gap["summary"]["total"] > 0 and gap["items"][0]["reasons"]
    t0 = time.perf_counter()
    plan = client.post("/api/roadmap/generate", headers=h, json={"weekly_hours": 10}).json()
    elapsed = time.perf_counter() - t0
    assert plan["total"] > 5 and plan["company_name"] == "Accenture"
    assert plan["plan_type"] == "Company-specific plan"
    assert elapsed < 5, f"plan generation took {elapsed:.2f}s"
    task = plan["tasks"][0]
    assert task["why"] and task["est_minutes"] > 0
    assert client.patch(f"/api/roadmap/tasks/{task['id']}", headers=h, json={"status": "done"}).json()["status"] == "done"

    # 7. practise questions
    qs = client.get("/api/questions", headers=h, params={"company": "accenture", "qtype": "mcq"}).json()
    assert qs["total"] > 20
    q = qs["items"][0]
    res = client.post(f"/api/questions/{q['id']}/attempt", headers=h, json={"response": q["options"][0]}).json()
    assert "correct" in res

    # 8. mock interview, one question at a time, ending in a report
    mi = client.post("/api/interviews", headers=h, json={"itype": "mixed", "difficulty": "easy", "duration_min": 9}).json()
    assert mi["current_question"] and mi["total_questions"] == 3
    for _ in range(mi["total_questions"]):
        mi = client.post(f"/api/interviews/{mi['id']}/answer", headers=h, json={
            "answer": "I built a REST API with FastAPI and MySQL because we needed fast search. For example, I used joins "
                      "and indexes, which reduced query time. The result was a 40% faster search."}).json()
    assert mi["status"] == "completed" and mi["report"]["overall"] > 0
    assert "disclaimer" in mi["report"]

    # 9. progress + dashboard read real data
    dash = client.get("/api/dashboard", headers=h).json()
    assert dash["roadmap"]["done"] == 1 and dash["last_interview"]
    steps = {s["key"]: s["done"] for s in dash["journey"]}
    assert all(steps.values()), steps
    print(f"\nIMPACT: plan generated in {elapsed * 1000:.0f} ms with {plan['total']} tasks; "
          f"gap items {gap['summary']['total']} (missing {gap['summary']['missing']}, partial {gap['summary']['partial']})")
