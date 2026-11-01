"""
Career Recommendation Service.

Match % is fully explainable:
    each required skill has a weight (core 3, important 2, nice 1)
    your evidence earns part of that weight:
        validated 100%, project 80%, claimed 40%, AI-inferred 25%, missing 0%
    match % = earned weight / total weight   (+ up to 5 points if it matches your stated interests)
No hidden model, no "placement probability".
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CareerRecommendation, LearningResource, ProfileLink, Skill, StudentProfile
from app.services.roles import ROLES, WEIGHT_WORD

CREDIT = {"validated": 1.0, "project": 0.8, "claimed": 0.4, "inferred": 0.25}


def score_role(key: str, skills: dict[str, Skill], interests: list[str]) -> dict:
    role = ROLES[key]
    req = dict(role["skills"])
    for group in role.get("any_of", []):  # "one of these frameworks" counts as one core skill
        best = max(group, key=lambda s: CREDIT.get(skills[s].level, 0) if s in skills else 0)
        req[best] = 3
    total = sum(req.values())
    earned, relevant, missing, partial = 0.0, [], [], []
    for name, w in sorted(req.items(), key=lambda kv: -kv[1]):
        s = skills.get(name)
        credit = CREDIT.get(s.level, 0) if s else 0
        earned += w * credit
        if s and s.level in ("validated", "project"):
            relevant.append({"skill": name, "level": s.level, "weight": WEIGHT_WORD[w]})
        elif s:
            partial.append({"skill": name, "level": s.level, "weight": WEIGHT_WORD[w]})
        else:
            missing.append({"skill": name, "weight": WEIGHT_WORD[w]})
    pct = 100 * earned / total if total else 0
    text = " ".join(interests).lower()
    interest_hit = any(word in text for word in role["interests"])
    if interest_hit:
        pct = min(100, pct + 5)
    why = []
    if relevant:
        why.append(f"Your projects already show {', '.join(r['skill'] for r in relevant[:4])}.")
    if interest_hit:
        why.append("It matches an interest you told us about (+5 points).")
    if not why:
        why.append("Some of your listed skills overlap with this role, but none are shown in projects yet.")
    return {
        "role_key": key, "title": role["title"], "summary": role["summary"], "match_pct": round(pct, 1),
        "why": why, "relevant": relevant, "partial": partial, "missing": missing,
        "learn": [m["skill"] for m in missing if m["weight"] != "nice to have"][:5] + [p["skill"] for p in partial[:2]],
        "projects": role["projects"], "formula": {"earned": round(earned, 2), "total": total,
                                                  "interest_bonus": 5 if interest_hit else 0},
    }


def recommend(db: Session, user_id: int) -> list[CareerRecommendation]:
    skills = {s.name: s for s in db.scalars(select(Skill).where(Skill.user_id == user_id))}
    prof = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    interests = (prof.interests + prof.preferred_roles) if prof else []
    has_links = db.scalar(select(ProfileLink.id).where(ProfileLink.user_id == user_id, ProfileLink.status == "ok")) is not None
    limited = not has_links
    scored = sorted((score_role(k, skills, interests) for k in ROLES), key=lambda r: -r["match_pct"])
    db.query(CareerRecommendation).filter(CareerRecommendation.user_id == user_id).delete()
    out = []
    for r in scored:
        res = db.scalars(select(LearningResource).where(LearningResource.topic.in_(r["learn"][:3])).limit(4)).all()
        r["resources"] = [{"title": x.title, "url": x.url, "provider": x.provider} for x in res]
        rec = CareerRecommendation(user_id=user_id, role_key=r["role_key"], title=r["title"],
                                   match_pct=r["match_pct"], details=r, limited_info=limited)
        db.add(rec)
        out.append(rec)
    db.commit()
    return out
