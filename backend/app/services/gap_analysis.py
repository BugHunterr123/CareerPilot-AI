"""
Skill Gap Service.

Requirements come from TWO places, and every item says which:
  1. the ROLE skill matrix (app/services/roles.py)      -> origin "role"
  2. the COMPANY's hiring stages (seeded, source-backed) -> origin "company"
     each stage's study topics are mapped to a skill (e.g. "Time and work" -> Quantitative
     Aptitude) and kept word for word with the stage name and its source links.
An item needed by both is origin "both". A pasted job description adds origin "jd".

Priority is a visible formula (no hidden AI score):
    points = weight (core 3 / important 2 / nice 1; company-tested only = 2)
             x gap (missing 1.0, partial 0.5, shown 0)
             + 1 if the company's hiring stages test it (and it is not shown yet)
    High >= 3, Medium >= 1.5, Low > 0
"""
import re

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import Company, LearningResource, PracticeQuestion, QuestionAttempt, Skill, SkillGapReport
from app.services.roles import ROLES, WEIGHT_WORD, role_title
from app.services.taxonomy import PATTERNS, canonical, category_of

# Company study topic (free text from the guide) -> skill. First match wins.
TOPIC_RULES: list[tuple[str, str]] = [
    (r"pseudo-?code|output tracing|code output|predict the output", "Pseudocode"),
    (r"\bxor\b|bitwise|bit shift|bit manipulation", "Bit Manipulation"),
    (r"permutation|combination|probabilit|percentage|profit|loss|time and work|speed|distance|ratio|average|"
     r"interest|number system|mensuration|bubble math|arithmetic|\bquant|numerical|data interpretation|lcm|hcf", "Quantitative Aptitude"),
    (r"syllogism|arrangement|seating|blood relation|coding[- ]decoding|series|puzzle|reasoning|abstract|"
     r"deductive|inductive|cognitive game|game", "Logical Reasoning"),
    (r"grammar|reading|comprehension|vocabulary|sentence|english|para ?jumble|verbal|essay|email writing|email", "Verbal Ability"),
    (r"\bsql\b|join|nth highest|second highest|group by|query|queries", "SQL"),
    (r"dbms|normali[sz]|transaction|acid|indexing|keys", "DBMS"),
    (r"\boops?\b|object[- ]oriented|inheritance|polymorphism|class(es)?\b|pillars", "OOP"),
    (r"operating system|\bos\b|deadlock|process|thread|scheduling|paging|memory management", "Operating Systems"),
    (r"network|osi|tcp|udp|\bdns\b|http\b|subnet", "Computer Networks"),
    (r"cloud|aws|azure|iaas|paas|saas", "Cloud Computing"),
    (r"security|encryption|phishing|firewall|malware", "Cyber Security"),
    (r"dynamic programming|\bdp\b|greedy|graph|bfs|dfs|sort|search|recursion|backtrack|segment tree|algorithm", "Algorithms"),
    (r"array|string|hash|linked list|stack|queue|tree|heap|matrix|data structure|dsa", "Data Structures"),
    (r"sdlc|agile|scrum|waterfall", "Agile"),
    (r"html", "HTML"), (r"\bcss\b", "CSS"), (r"javascript|\bjs\b|frontend|front-end|\bdom\b", "JavaScript"),
    (r"pandas|numpy", "Pandas"), (r"statistic", "Statistics"), (r"machine learning|\bml\b|model", "Machine Learning"),
    (r"excel", "Excel"), (r"power ?bi|tableau|dashboard", "Data Visualization"),
    (r"project|tech stack|resume", "Project discussion"),
    (r"tell me about yourself|why (join|this company|\w+\?)|relocat|strength|weakness|hr\b|behaviou?ral|situational|"
     r"time management|teamwork|conflict|goals", "HR answers"),
    (r"communicat|speaking|listening|pronunciation|versant|spoken", "Communication"),
    (r"python", "Python"), (r"\bjava\b", "Java"), (r"c\+\+", "C++"),
]
_TOPIC_RX = [(re.compile(p, re.I), skill) for p, skill in TOPIC_RULES]

# Stage kinds whose name alone says what they test (used when a stage lists no study topics)
STAGE_DEFAULT = {"aptitude": "Quantitative Aptitude", "game_based": "Logical Reasoning", "coding": "Algorithms",
                 "technical_mcq": "Pseudocode", "communication": "Communication", "essay": "Verbal Ability",
                 "group_discussion": "Communication", "hr_interview": "HR answers", "technical_interview": "Project discussion"}

SKILL_TO_SUBJECT = {
    "SQL": "SQL", "DBMS": "DBMS", "OOP": "OOP", "Operating Systems": "OS", "Computer Networks": "Networks",
    "Data Structures": "Coding", "Algorithms": "Coding", "Bit Manipulation": "Coding", "Pseudocode": "Pseudocode",
    "Quantitative Aptitude": "Quant", "Logical Reasoning": "Logical", "Verbal Ability": "Verbal", "Communication": "HR",
    "HR answers": "HR", "Project discussion": "Project", "Python": "Python", "Cloud Computing": "Cloud",
    "Cyber Security": "Security", "Machine Learning": "ML", "Java": "Java", "HTML": "Web", "CSS": "Web", "JavaScript": "Web",
}
EXTRA_CATEGORY = {"HR answers": "Communication and Behavioural", "Project discussion": "Communication and Behavioural"}

WHY = {
    "Data Structures": "Almost every coding round and technical interview is built on arrays, strings, hashing and lists.",
    "Algorithms": "Coding rounds check whether you can pick the right approach (sorting, greedy, DP, BFS/DFS) in time.",
    "SQL": "Most technical rounds ask at least one query (joins, GROUP BY); data roles use it daily.",
    "DBMS": "Normalisation, keys, transactions and indexing are standard interview questions.",
    "OOP": "Classes, inheritance and polymorphism come up in nearly every fresher technical interview.",
    "Operating Systems": "Processes, threads, deadlock and memory are common MCQ and interview topics.",
    "Computer Networks": "OSI layers, TCP vs UDP and HTTP basics appear in MCQ rounds.",
    "Quantitative Aptitude": "Most service-company online tests start with aptitude, and it is often an elimination round.",
    "Logical Reasoning": "Reasoning questions and games filter large numbers of candidates early.",
    "Verbal Ability": "Reading, grammar and writing tasks still appear in many online tests.",
    "Communication": "Interviews and communication rounds judge how clearly you explain your work.",
    "Pseudocode": "Pseudocode output questions are a large part of several online tests; they reward careful tracing.",
    "Bit Manipulation": "XOR and shift questions are reported in recent online tests.",
    "HR answers": "The HR round checks fit, clarity and honesty; prepared stories make it easy.",
    "Project discussion": "Interviewers spend most of the technical round on the projects in your resume.",
    "ETL": "Data engineers spend most of their time building and fixing extract-transform-load pipelines.",
    "Apache Spark": "Spark is the standard engine for processing data that does not fit on one machine.",
    "Data Modelling": "Good tables (facts, dimensions, keys) decide whether queries stay simple and fast.",
    "Data Warehousing": "Analytics teams query warehouses; you should know how data is loaded and organised there.",
    "REST APIs": "Backend work is mostly designing and calling APIs.",
    "Git": "Teams expect you to use version control from day one.",
    "Selenium": "UI test automation is the core daily work of a QA automation engineer.",
    "Troubleshooting": "Support roles are judged on how calmly and methodically you find the cause of a problem.",
}


def practice_accuracy(db: Session, user_id: int) -> dict[str, tuple[int, int]]:
    """subject -> (attempts, correct) from the student's recorded practice."""
    rows = db.execute(
        select(PracticeQuestion.subject, func.count(QuestionAttempt.id),
               func.sum(case((QuestionAttempt.is_correct.is_(True), 1), else_=0)))
        .join(PracticeQuestion, PracticeQuestion.id == QuestionAttempt.question_id)
        .where(QuestionAttempt.user_id == user_id).group_by(PracticeQuestion.subject)).all()
    return {s: (int(n), int(c or 0)) for s, n, c in rows}


def topic_skill(topic: str) -> str:
    for rx, skill in _TOPIC_RX:
        if rx.search(topic):
            return skill
    return canonical(topic) or topic.strip()


def company_stage_topics(company: Company) -> list[dict]:
    """Each hiring stage with its study topics (word for word) and source links."""
    src = {s.key: s for s in company.sources}
    out = []
    for st in company.stages:
        keys = list(dict.fromkeys(f.get("source") for f in st.format if f.get("source")))
        sources = [{"url": src[k].url, "title": src[k].title or src[k].publisher, "publisher": src[k].publisher,
                    "label": src[k].label, "date": src[k].date} for k in keys if k in src]
        topics = [{"topic": t, "skill": topic_skill(t)} for t in st.study] or \
                 ([{"topic": st.name, "skill": STAGE_DEFAULT[st.kind]}] if st.kind in STAGE_DEFAULT else [])
        out.append({"order": st.order, "name": st.name, "kind": st.kind, "label": st.label,
                    "format": [f["text"] for f in st.format], "topics": topics, "sources": sources})
    return out


def required_skills(db: Session, role_key: str, company: Company | None, jd: str) -> dict[str, dict]:
    role = ROLES[role_key]
    req: dict[str, dict] = {}
    for name, wgt in role["skills"].items():
        req[name] = {"weight": wgt, "role_weight": wgt, "origins": {"role"}, "company_topics": [],
                     "reasons": [f"{WEIGHT_WORD[wgt].capitalize()} skill for a {role['title']}"]}
    for group in role.get("any_of", []):
        req.setdefault(group[0], {"weight": 2, "role_weight": 2, "origins": {"role"}, "company_topics": [],
                                  "reasons": [f"A {role['title']} needs one of: {', '.join(group)}"]})
    if company:
        for jr in company.roles:
            if jr.role_key != role_key:
                continue
            for sname in jr.skills:
                c = canonical(sname) or sname
                e = req.setdefault(c, {"weight": 2, "role_weight": None, "origins": set(), "company_topics": [], "reasons": []})
                e["origins"].add("company")
                e["reasons"].append(f"Listed by {company.name} for {jr.title}")
        for st in company_stage_topics(company):
            for t in st["topics"]:
                e = req.setdefault(t["skill"], {"weight": 2, "role_weight": None, "origins": set(), "company_topics": [], "reasons": []})
                e["origins"].add("company")
                e["company_topics"].append({"topic": t["topic"], "stage": st["name"], "stage_order": st["order"],
                                            "label": st["label"], "sources": st["sources"]})
    if jd.strip():
        for name, pats in PATTERNS.items():
            hits = sum(len(p.findall(jd)) for p in pats)
            if hits:
                e = req.setdefault(name, {"weight": 2, "role_weight": None, "origins": set(), "company_topics": [], "reasons": []})
                e["weight"] = max(e["weight"], 3 if hits > 1 else 2)
                e["origins"].add("jd")
                e["reasons"].append("Mentioned in the job description you pasted")
    return req


def _origin_word(origins: set[str]) -> str:
    if {"role", "company"} <= origins:
        return "both"
    if "role" in origins:
        return "role"
    if "company" in origins:
        return "company"
    return "jd"


def analyse(db: Session, user_id: int, role_key: str, company_id: int | None = None, jd: str = "") -> SkillGapReport:
    company = db.get(Company, company_id) if company_id else None
    skills = {s.name: s for s in db.scalars(select(Skill).where(Skill.user_id == user_id))}
    acc = practice_accuracy(db, user_id)
    items = []
    for name, info in required_skills(db, role_key, company, jd).items():
        s = skills.get(name)
        subject = SKILL_TO_SUBJECT.get(name)
        n_att, n_ok = acc.get(subject, (0, 0)) if subject else (0, 0)
        if s and s.level in ("validated", "project"):
            status, evidence = "shown", f"Shown in your work ({s.level})"
        elif n_att >= 5 and n_ok / n_att >= 0.6:
            status, evidence = "shown", f"Practice: {n_ok} of {n_att} {subject} questions correct"
        elif s:
            status, evidence = "partial", f"Only {s.level} so far, not shown in a project"
        elif n_att:
            status, evidence = "partial", f"Practice started: {n_ok} of {n_att} {subject} questions correct"
        else:
            status, evidence = "missing", "Not found in your resume, projects or practice"
        gap = {"shown": 0, "partial": 0.5, "missing": 1.0}[status]
        tested = bool(info["company_topics"])
        points = info["weight"] * gap + (1 if tested and gap else 0)
        prio = "high" if points >= 3 else "medium" if points >= 1.5 else "low" if points > 0 else "done"
        reasons = list(dict.fromkeys(info["reasons"]))
        if tested:
            stages = sorted({(t["stage_order"], t["stage"]) for t in info["company_topics"]})
            reasons.append(f"Tested in {company.name}: " + "; ".join(n for _, n in stages))
        reasons.append(evidence)
        res = db.scalars(select(LearningResource).where(LearningResource.topic == name).limit(3)).all()
        items.append({
            "skill": name, "category": EXTRA_CATEGORY.get(name) or (category_of(name) if category_of(name) != "Other" else "Company topic"),
            "origin": _origin_word(info["origins"]), "role_weight": info["role_weight"],
            "company_topics": info["company_topics"], "status": status, "evidence_level": s.level if s else None,
            "weight": info["weight"], "priority": prio, "points": round(points, 2), "reasons": reasons,
            "tested_in": [f"{company.name}: {t['stage']} ({t['label']})" for t in info["company_topics"]] if company else [],
            "why": WHY.get(name, f"Commonly expected for a {role_title(role_key)}." if "role" in info["origins"]
                           else f"Listed in {company.name}'s hiring stages." if company else "Mentioned in your job description."),
            "resources": [{"title": r.title, "url": r.url, "provider": r.provider, "minutes": r.minutes} for r in res],
            "practice_subject": subject,
        })
    items.sort(key=lambda i: (-i["points"], -i["weight"], i["skill"]))
    for n, it in enumerate([i for i in items if i["priority"] != "done"], start=1):
        it["order"] = n
    count = lambda k, v: sum(1 for i in items if i[k] == v)  # noqa: E731
    summary = {
        "role": role_title(role_key), "role_key": role_key,
        "company": company.name if company else None, "company_id": company.id if company else None,
        "shown": count("status", "shown"), "partial": count("status", "partial"), "missing": count("status", "missing"),
        "total": len(items), "from_role": count("origin", "role"), "from_company": count("origin", "company"),
        "from_both": count("origin", "both"), "from_jd": count("origin", "jd"),
        "role_requirements": [{"skill": k, "weight": v, "level": WEIGHT_WORD[v]} for k, v in ROLES[role_key]["skills"].items()],
        "company_stages": company_stage_topics(company) if company else [],
        "projects": ROLES[role_key]["projects"],
        "formula": "points = weight (core 3, important 2, nice 1; company-tested only 2) x gap (missing 1, partial 0.5) + 1 if the company tests it",
    }
    rep = SkillGapReport(user_id=user_id, role_key=role_key, company_id=company_id, job_description=jd[:5000],
                         items=items, summary=summary)
    db.add(rep)
    db.commit()
    return rep
