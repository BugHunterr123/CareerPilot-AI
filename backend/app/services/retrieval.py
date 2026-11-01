"""
Small, explainable retrieval (the "R" in RAG) over CareerPilot's own content:
company guides (overview, roles, stages), the question bank, learning resources,
and the signed-in student's profile. BM25 ranking, no external services.

The public index is cached and rebuilt when the seeded content changes.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Company, LearningResource, PracticeQuestion

STOP = set("a an the and or of to in on for with is are was were be been this that it its as at by from what how why "
           "when which who whom your you can could will would should about into than then them they their there these "
           "those have has had do does did not but also more most such each other some any all me my i we our us tell "
           "explain give please want need know get make like".split())
SYNONYMS = {"dbms": ["database"], "oops": ["oop", "object"], "os": ["operating"], "dsa": ["data", "structure", "algorithm"],
            "js": ["javascript"], "ml": ["machine", "learning"], "ai": ["artificial", "intelligence"],
            "hr": ["behavioural", "interview"], "aptitude": ["quant", "reasoning"], "sql": ["query", "join"]}


def stem(w: str) -> str:
    for suf in ("ing", "ies", "ed", "es", "s"):
        if len(w) > 4 and w.endswith(suf):
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def tokens(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9+#]+", text.lower()):
        if w in STOP or len(w) < 2:
            continue
        out.append(stem(w))
        out.extend(SYNONYMS.get(w, []))
    return out


@dataclass
class Doc:
    kind: str  # stage / role / overview / question / resource / profile
    title: str
    text: str
    url: str | None = None
    label: str = ""
    company: str | None = None
    href: str | None = None  # link inside the app
    extra: dict = field(default_factory=dict)


class Index:
    def __init__(self, docs: list[Doc]):
        self.docs = docs
        self.tf = [Counter(tokens(d.title + " " + d.title + " " + d.text)) for d in docs]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.len) / max(1, len(self.len))
        df = Counter()
        for c in self.tf:
            df.update(c.keys())
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int = 5, companies: set[str] | None = None, kinds: set[str] | None = None) -> list[tuple[float, Doc]]:
        q = tokens(query)
        if not q:
            return []
        # The rarest query words carry the topic ("deadlock" in "what is a deadlock in operating systems");
        # documents that contain them are boosted so common words cannot outvote them.
        known = [t for t in set(q) if t in self.idf]
        top = max((self.idf[t] for t in known), default=0)
        focus = {t for t in known if self.idf[t] >= top - 0.05}
        scored = []
        for i, d in enumerate(self.docs):
            if kinds and d.kind not in kinds:
                continue
            if companies and d.company and d.company not in companies:
                continue
            tf, ln, s = self.tf[i], self.len[i], 0.0
            for t in q:
                f = tf.get(t)
                if f:
                    s += self.idf.get(t, 0) * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * ln / self.avg))
            if s > 0:
                if focus and focus & tf.keys():
                    s *= 1.8
                if companies and d.company in companies:
                    s *= 1.6
                scored.append((s, d))
        scored.sort(key=lambda x: -x[0])
        return scored[:k]


_cache: dict = {"key": None, "index": None}


def public_index(db: Session) -> Index:
    key = (db.scalar(select(func.count(PracticeQuestion.id))), db.scalar(select(func.max(Company.updated_at))),
           db.scalar(select(func.count(LearningResource.id))))
    if _cache["key"] == key and _cache["index"] is not None:
        return _cache["index"]
    docs: list[Doc] = []
    names = {}
    for c in db.scalars(select(Company)):
        names[c.id] = c.name
        src = {s.key: s for s in c.sources}
        ov = src.get(c.overview_source_key)
        docs.append(Doc("overview", f"{c.name}: overview", f"{c.name} {c.overview} {c.variation_note}",
                        ov.url if ov else c.careers_url, ov.label if ov else "", c.name, f"/companies/view/?slug={c.slug}"))
        for r in c.roles:
            facts = [e["text"] for e in r.eligibility] + [e["text"] for e in r.compensation]
            first = src.get((r.eligibility or r.compensation or [{}])[0].get("source", ""))
            docs.append(Doc("role", f"{c.name}: {r.title}", f"{c.name} {r.title} {r.description} skills {' '.join(r.skills)} "
                            f"eligibility package salary {' '.join(facts)}", first.url if first else c.careers_url,
                            first.label if first else "", c.name, f"/companies/view/?slug={c.slug}",
                            {"facts": facts, "skills": r.skills}))
        for st in c.stages:
            first = src.get(st.format[0]["source"]) if st.format else None
            fmt = [f["text"] for f in st.format]
            docs.append(Doc("stage", f"{c.name}: {st.name}", f"{c.name} hiring round stage {st.name} {st.kind.replace('_', ' ')} "
                            f"{st.what} {' '.join(fmt)} study {' '.join(st.study)} tips {' '.join(st.tips)}",
                            first.url if first else None, st.label, c.name, f"/companies/view/?slug={c.slug}",
                            {"what": st.what, "format": fmt, "study": st.study, "tips": st.tips}))
    for q in db.scalars(select(PracticeQuestion)):
        comp = names.get(q.company_id)
        title = q.title or q.question[:90]
        docs.append(Doc("question", f"{comp + ': ' if comp else ''}{title}",
                        f"{comp or ''} {q.subject} {q.qtype} {q.title} {q.question} {q.answer} {q.explanation} {' '.join(q.concepts or [])}",
                        None, q.label, comp, f"/practice/?q={q.id}",
                        {"question": q.question, "answer": q.answer, "explanation": q.explanation, "subject": q.subject,
                         "qtype": q.qtype, "options": q.options, "id": q.id, "runnable": bool(q.tests)}))
    for r in db.scalars(select(LearningResource)):
        docs.append(Doc("resource", r.title, f"{r.topic} {r.title} {r.provider} {r.kind}", r.url, "Learning resource",
                        None, None, {"topic": r.topic, "provider": r.provider, "minutes": r.minutes}))
    _cache.update(key=key, index=Index(docs))
    return _cache["index"]


def mentioned_companies(db: Session, text: str) -> set[str]:
    t = text.lower()
    out = set()
    for c in db.scalars(select(Company)):
        if c.name.lower() in t or c.slug.replace("-", " ") in t or c.slug in t:
            out.add(c.name)
    return out
