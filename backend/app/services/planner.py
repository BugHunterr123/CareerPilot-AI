"""
Preparation Planning Service: gap report + company stages + your time -> dated tasks.

Rules (kept simple on purpose so a student can trust it):
  * daily budget = weekly hours / 6 (one rest/revision day a week)
  * high-priority gaps first, then medium, then low
  * company stages add stage-specific practice + a mock interview in the last week
  * if time runs out, low-priority topics are dropped and we SAY which ones
"""
import time
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Project, Roadmap, RoadmapTask, SkillGapReport, StudentProfile
from app.services.gap_analysis import STAGE_DEFAULT
from app.services.roles import role_title


def _skill_tasks(item: dict) -> list[dict]:
    base = {"skill": item["skill"], "priority": item["priority"], "resources": item["resources"],
            "practice": {"subject": item["practice_subject"]} if item["practice_subject"] else {}}
    why = "; ".join(item["reasons"][:2] + item.get("tested_in", [])[:1])
    topics = list(dict.fromkeys(t["topic"] for t in item.get("company_topics", []) if t["topic"] != item["skill"]))[:4]
    if topics:  # company-specific subtopics from the hiring guide, e.g. "Time and work, Speed and distance"
        item = {**item, "skill": f"{item['skill']} ({', '.join(topics)})"}
    if item["category"] == "Aptitude":
        return [{**base, "topic": f"{item['skill']}: timed drill of 20 questions", "est_minutes": 40, "why": why,
                 "explanation": f"{item['why']} Set a timer (about 1 minute per question) and review every mistake."}]
    if item["category"] == "Communication and Behavioural":
        return [{**base, "topic": f"{item['skill']}: record and review a 2-minute answer", "est_minutes": 30, "why": why,
                 "explanation": f"{item['why']} Record yourself answering 'Tell me about yourself', listen once, "
                                "and fix filler words and missing structure."}]
    if item["status"] == "missing":
        return [
            {**base, "topic": f"Learn the basics of {item['skill']}", "est_minutes": 60, "why": why,
             "explanation": f"{item['why']} Read one resource below and write short notes in your own words."},
            {**base, "topic": f"Practise {item['skill']}: 10 questions", "est_minutes": 45, "why": why,
             "explanation": "Do the questions without looking at answers first. Note every mistake."},
        ]
    return [{**base, "topic": f"Revise and practise {item['skill']}", "est_minutes": 45, "why": why,
             "explanation": f"You list {item['skill']} but nothing shows it yet. {item['why']} "
                            "Answer 5-10 practice questions to validate it."}]


def _stage_tasks(company: Company) -> list[dict]:
    out = []
    for st in company.stages:
        subject = {"aptitude": "Quant", "game_based": "Logical", "coding": "Coding", "technical_mcq": "Pseudocode",
                   "communication": "Verbal", "hr_interview": "HR", "technical_interview": "OOP"}.get(st.kind)
        out.append({"topic": f"{company.name} stage {st.order}: {st.name}", "skill": STAGE_DEFAULT.get(st.kind, ""),
                    "priority": "high" if st.kind in ("aptitude", "coding", "technical_mcq", "game_based") else "medium",
                    "est_minutes": 40, "resources": [],
                    "practice": {"company_id": company.id, **({"subject": subject} if subject else {})},
                    "why": f"This is a real stage of {company.name}'s process ({st.label}).",
                    "explanation": (st.what[:300] + " Read the stage guide in Company Explorer, then practise.").strip()})
    return out


def generate(db: Session, user_id: int, role_key: str, company_id: int | None,
             weekly_hours: int | None = None, target_date: date | None = None) -> Roadmap:
    t0 = time.perf_counter()
    prof = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    weekly = weekly_hours or (prof.weekly_hours if prof and prof.weekly_hours else 8)
    start = date.today()
    target = target_date or (prof.target_date if prof and prof.target_date and prof.target_date > start else None)
    days = max(7, min(84, ((target - start).days if target else 28)))
    company = db.get(Company, company_id) if company_id else None
    gap = db.scalar(select(SkillGapReport).where(SkillGapReport.user_id == user_id, SkillGapReport.role_key == role_key,
                    SkillGapReport.company_id == company_id).order_by(SkillGapReport.id.desc()))
    if gap is None:
        from app.services.gap_analysis import analyse
        gap = analyse(db, user_id, role_key, company_id)

    old = db.scalar(select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active.is_(True)))
    done_topics = {t.topic for t in old.tasks if t.status == "done"} if old else set()
    if old:
        old.is_active = False

    order = {"high": 0, "medium": 1, "low": 2}
    items = sorted([i for i in gap.items if i["priority"] != "done"], key=lambda i: (order[i["priority"]], -i["points"]))
    queue = [t for i in items for t in _skill_tasks(i)]
    stage = _stage_tasks(company) if company else []
    queue = queue[:4] + stage[:3] + queue[4:] + stage[3:]  # mix company stages in early
    for p in db.scalars(select(Project).where(Project.user_id == user_id).limit(2)):
        queue.append({"topic": f"Prepare a 2-minute explanation of '{p.name}'", "skill": "Communication",
                      "priority": "medium", "est_minutes": 30, "resources": [], "practice": {"subject": "Project"},
                      "why": "Interviewers almost always start with your projects.",
                      "explanation": "Cover: problem, your role, tech used and why, one challenge, one result with a number."})
    queue.append({"topic": "Full mock interview (mixed)", "skill": "Communication", "priority": "high",
                  "est_minutes": 30, "resources": [], "practice": {"mock": "mixed"}, "final": True,
                  "why": "Practising out loud is the fastest way to find weak answers.",
                  "explanation": "Run a mixed mock interview in CareerPilot and read the report."})
    queue = [q for q in queue if q["topic"] not in done_topics]

    budget = round(weekly * 60 / 6)
    capacity = budget * (days - days // 7)
    total, kept, dropped = 0, [], []
    for q in queue:
        if total + q["est_minutes"] <= capacity or q["priority"] == "high" or q.get("final"):
            kept.append(q)
            total += q["est_minutes"]
        else:
            dropped.append(q["topic"])
    plan_type = "Company-specific plan" if company and company.stages else "General role-based plan"
    notes = []
    if not company:
        notes.append("No company selected, so this is a general plan for the role. Pick a company to add its real hiring stages.")
    elif not company.stages:
        notes.append(f"We have no verified hiring stages for {company.name}, so this is a general role-based plan.")
    if dropped:
        notes.append(f"Your time is short, so these lower-priority topics were left out: {', '.join(dropped[:6])}.")
    if done_topics:
        notes.append(f"{len(done_topics)} task(s) you already completed were not repeated.")
    rm = Roadmap(user_id=user_id, role_key=role_key, company_id=company_id, weekly_hours=weekly, start_date=start,
                 target_date=start + timedelta(days=days), plan_type=plan_type, notes=notes)
    day, used = 0, 0
    for q in kept:
        if used and used + q["est_minutes"] > budget:
            day, used = day + 1, 0
            if (day + 1) % 7 == 0:  # rest / revision day
                day += 1
        if q.get("final"):
            day = max(day, days - 2)
        used += q["est_minutes"]
        d = start + timedelta(days=min(day, days - 1))
        rm.tasks.append(RoadmapTask(user_id=user_id, week=min(day, days - 1) // 7 + 1, due_date=d, topic=q["topic"][:160],
                                    skill=q.get("skill", ""), explanation=q["explanation"], why=q["why"],
                                    resources=q["resources"], practice=q["practice"], est_minutes=q["est_minutes"],
                                    priority=q["priority"]))
    db.add(rm)
    db.flush()
    rm.generation_ms = int((time.perf_counter() - t0) * 1000)
    db.commit()
    return rm


def describe(rm: Roadmap) -> str:
    return f"{rm.plan_type} for {role_title(rm.role_key)}"
