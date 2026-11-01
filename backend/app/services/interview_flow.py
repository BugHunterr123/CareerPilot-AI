"""Start a mock interview, take answers one by one, and write the final report."""
from sqlalchemy.orm import Session

from app.models import Company, FeedbackReport, InterviewResponse, MockInterview, ProgressEvent
from app.services.interviewer import build_plan, score
from app.services.llm import llm_enabled

STRUCTURES = {
    "technical": "Definition in one line -> how it works -> a small example -> one trade-off or comparison.",
    "project": "Problem -> your role -> tech and why -> one challenge and how you solved it -> result with a number.",
    "hr": "STAR: Situation -> Task -> Action (what YOU did) -> Result (and what you learned).",
}


def start(db: Session, user_id: int, role_key: str, company_id: int | None, itype: str,
          difficulty: str, duration_min: int) -> MockInterview:
    n = max(3, min(8, duration_min // 3))
    company = db.get(Company, company_id) if company_id else None
    plan = build_plan(db, user_id, role_key, itype, difficulty, n, company)
    mi = MockInterview(user_id=user_id, role_key=role_key, company_id=company_id, itype=itype, difficulty=difficulty,
                       duration_min=duration_min, plan=plan, scoring_mode="llm" if llm_enabled() else "rubric-rules")
    db.add(mi)
    db.commit()
    return mi


def answer(db: Session, mi: MockInterview, text: str) -> InterviewResponse:
    item = mi.plan[mi.current_index]
    result = score(item, text)
    total = round(sum(v["score"] for v in result["scores"].values()) / 4, 2)
    resp = InterviewResponse(interview_id=mi.id, index=mi.current_index, question=item["q"], answer=text,
                             scores=result["scores"], total=total,
                             feedback={"good": result["good"], "missing": result["missing"], "engine": result["engine"],
                                       "quote": result.get("quote", ""), "better_answer": result.get("better_answer", ""),
                                       "structure_tip": STRUCTURES[item["kind"] if item["kind"] in STRUCTURES else "technical"]})
    mi.responses.append(resp)
    mi.current_index += 1
    if mi.current_index >= len(mi.plan):
        finish(db, mi)
    db.commit()
    return resp


def finish(db: Session, mi: MockInterview) -> FeedbackReport:
    rs = list(mi.responses)  # ONLY this session's answers
    crit = {k: round(sum(r.scores[k]["score"] for r in rs) / max(1, len(rs)), 2)
            for k in ("concepts", "depth", "structure", "clarity")}
    overall = round(sum(crit.values()) / 4, 2) if rs else 0
    mi.overall = overall
    mi.status = "completed"
    names = {"concepts": "covering key concepts", "depth": "giving examples and reasons",
             "structure": "structuring answers", "clarity": "clear, well-sized answers"}
    strengths = [f"Good at {names[k]} ({v}/5)" for k, v in crit.items() if v >= 3.5]
    improve = [f"Work on {names[k]} ({v}/5)" for k, v in crit.items() if v < 3]
    missing = list(dict.fromkeys(m for r in rs for m in r.feedback.get("missing", [])))[:12]
    weak_topics = list(dict.fromkeys(mi.plan[r.index].get("topic", "") for r in rs if r.total < 3))
    engines = {r.feedback.get("engine", "rules") for r in rs}
    content = {
        "interview_id": mi.id, "overall": overall, "out_of": 5, "criteria": crit,
        "engine": "llm" if engines == {"llm"} else "rules" if engines == {"rules"} else "mixed",
        "questions": [{"q": r.question, "answer_summary": (r.answer[:180] + ("..." if len(r.answer) > 180 else "")),
                       "score": r.total, "good": r.feedback.get("good", []), "missing": r.feedback.get("missing", []),
                       "quote": r.feedback.get("quote", ""), "better_answer": r.feedback.get("better_answer", ""),
                       "engine": r.feedback.get("engine", "rules")} for r in rs],
        "strengths": strengths or ["You completed the interview. That alone builds confidence."],
        "missing_concepts": missing, "improvements": improve or ["Keep practising harder questions."],
        "suggested_structures": STRUCTURES, "revision_topics": [t for t in weak_topics if t],
        "next_steps": ["Practise the revision topics in the question bank (filter by subject).",
                       "Redo this interview type in 2-3 days and compare scores on the Progress page."],
        "answered": len(rs), "asked": len(mi.plan),
        "disclaimer": "This is practice feedback from a rubric. It is not a prediction of any real interview result.",
    }
    rep = FeedbackReport(interview_id=mi.id, content=content)
    mi.report = rep
    db.add(ProgressEvent(user_id=mi.user_id, kind="interview_done",
                         detail={"interview_id": mi.id, "overall": overall, "type": mi.itype}))
    return rep
