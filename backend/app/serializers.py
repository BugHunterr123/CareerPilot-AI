"""Turn ORM objects into JSON-friendly dicts (one place, so every page sees the same shape)."""
from app.models import Company, HiringStage, MockInterview, PracticeQuestion, Roadmap, RoadmapTask, Skill, StudentProfile, User
from app.services.roles import role_title


def user_out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "full_name": u.full_name}


def profile_out(p: StudentProfile | None) -> dict:
    if not p:
        return {}
    keys = ["college", "degree", "branch", "graduation_year", "cgpa", "interests", "preferred_roles", "preferred_locations",
            "job_type", "weekly_hours", "certifications", "achievements", "target_role_key", "target_company_id",
            "optional_step_done"]
    out = {k: getattr(p, k) for k in keys}
    out["target_date"] = p.target_date.isoformat() if p.target_date else None
    out["target_role_title"] = role_title(p.target_role_key) if p.target_role_key else None
    return out


def skill_out(s: Skill) -> dict:
    return {"id": s.id, "name": s.name, "category": s.category, "level": s.level, "confidence": s.confidence,
            "needs_validation": s.needs_validation, "next_step": s.next_step, "user_added": s.user_added,
            "evidence": [{"kind": e.kind, "source": e.source, "quote": e.quote} for e in s.evidence]}


def source_map(c: Company) -> dict:
    return {s.key: {"url": s.url, "title": s.title, "publisher": s.publisher, "date": s.date, "label": s.label,
                    "accessed": s.accessed} for s in c.sources}


def stage_out(st: HiringStage) -> dict:
    return {"id": st.id, "order": st.order, "name": st.name, "kind": st.kind, "what": st.what, "format": st.format,
            "evaluates": st.evaluates, "study": st.study, "tips": st.tips, "before_next": st.before_next, "label": st.label}


def company_summary(c: Company, question_count: int = 0) -> dict:
    labels = sorted({s.label for s in c.sources})
    return {"id": c.id, "slug": c.slug, "name": c.name, "overview": c.overview, "stage_count": len(c.stages),
            "role_titles": [r.title for r in c.roles], "source_count": len(c.sources), "source_labels": labels,
            "question_count": question_count, "research_date": c.research_date}


def company_detail(c: Company) -> dict:
    return {**company_summary(c), "careers_url": c.careers_url, "variation_note": c.variation_note,
            "overview_source": c.overview_source_key,
            "roles": [{"id": r.id, "title": r.title, "description": r.description, "role_key": r.role_key,
                       "role_title": role_title(r.role_key), "skills": r.skills, "eligibility": r.eligibility,
                       "compensation": r.compensation} for r in c.roles],
            "stages": [stage_out(s) for s in c.stages], "sources": source_map(c)}


def question_out(q: PracticeQuestion, source=None, saved: bool = False, stats: dict | None = None,
                 hide_answer: bool = False, company_name: str | None = None) -> dict:
    """hide_answer=True is used inside a timed test: answers/solutions stay on the server until submitted."""
    tests = q.tests or []
    return {"id": q.id, "company_id": q.company_id, "company_name": company_name, "stage_kind": q.stage_kind,
            "subject": q.subject, "qtype": q.qtype, "title": q.title or "",
            "difficulty": q.difficulty, "question": q.question, "code": q.code, "options": q.options,
            "answer": "" if hide_answer else q.answer, "explanation": "" if hide_answer else q.explanation,
            "hints": q.hints, "concepts": q.concepts, "sample_io": q.sample_io,
            "solution": "" if hide_answer else q.solution,
            "solutions_other": {} if hide_answer else (q.solutions_other or {}),
            "runnable": bool(tests), "starter_code": q.starter_code or "", "io_format": q.io_format or {},
            "visible_tests": [{"input": t["input"], "output": t["output"]} for t in tests if not t.get("hidden")],
            "hidden_test_count": sum(1 for t in tests if t.get("hidden")),
            "label": q.label, "source_note": q.source_note,
            "source": {"url": source.url, "title": source.title, "publisher": source.publisher, "date": source.date,
                       "label": source.label} if source else None,
            "saved": saved, "stats": stats or {"attempts": 0, "correct": 0, "last_correct": None}}


def task_out(t: RoadmapTask) -> dict:
    return {"id": t.id, "week": t.week, "due_date": t.due_date.isoformat(), "topic": t.topic, "skill": t.skill,
            "explanation": t.explanation, "why": t.why, "resources": t.resources, "practice": t.practice,
            "est_minutes": t.est_minutes, "priority": t.priority, "status": t.status,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None}


def roadmap_out(r: Roadmap, company_name: str | None = None) -> dict:
    done = sum(t.status == "done" for t in r.tasks)
    return {"id": r.id, "role_key": r.role_key, "role_title": role_title(r.role_key), "company_id": r.company_id,
            "company_name": company_name, "weekly_hours": r.weekly_hours, "start_date": r.start_date.isoformat(),
            "target_date": r.target_date.isoformat() if r.target_date else None, "plan_type": r.plan_type,
            "notes": r.notes, "generation_ms": r.generation_ms, "created_at": r.created_at.isoformat(),
            "total": len(r.tasks), "done": done, "tasks": [task_out(t) for t in r.tasks]}


def interview_out(mi: MockInterview, company_name: str | None = None) -> dict:
    current = mi.plan[mi.current_index] if mi.status == "active" and mi.current_index < len(mi.plan) else None
    return {"id": mi.id, "role_key": mi.role_key, "role_title": role_title(mi.role_key), "company_id": mi.company_id,
            "company_name": company_name, "itype": mi.itype, "difficulty": mi.difficulty, "duration_min": mi.duration_min,
            "status": mi.status, "scoring_mode": mi.scoring_mode, "total_questions": len(mi.plan),
            "current_index": mi.current_index, "overall": mi.overall, "created_at": mi.created_at.isoformat(),
            "current_question": {"q": current["q"], "kind": current["kind"], "topic": current.get("topic"),
                                 "origin": current.get("origin", "")} if current else None,
            "question_source": (mi.plan[0].get("source", "bank") if mi.plan else "bank"),
            "responses": [{"index": r.index, "question": r.question, "answer": r.answer, "scores": r.scores,
                           "feedback": r.feedback, "total": r.total} for r in mi.responses],
            "report": mi.report.content if mi.report else None}
