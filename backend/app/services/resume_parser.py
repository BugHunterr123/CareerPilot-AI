"""
Step 2 of resume analysis (rule-based, used in demo mode and as the LLM fallback):
split the resume text into sections and pull out structured fields.

It only copies what is written in the resume. If a section is missing we leave it
empty and say so in the report; we never fill gaps with made-up details.
"""
import re

from app.services.taxonomy import PATTERNS, canonical, category_of

HEADINGS = {
    "summary": ["summary", "profile", "objective", "career objective", "about me", "professional summary"],
    "education": ["education", "academic details", "academics", "educational qualification", "qualifications"],
    "skills": ["skills", "technical skills", "key skills", "skills & tools", "technologies", "tech stack", "core competencies"],
    "projects": ["projects", "academic projects", "personal projects", "key projects", "project work"],
    "experience": ["experience", "work experience", "internships", "internship", "professional experience", "employment"],
    "certifications": ["certifications", "certificates", "courses", "certifications & courses", "licenses & certifications"],
    "achievements": ["achievements", "awards", "accomplishments", "honors", "achievements & awards",
                     "extracurricular", "extra-curricular activities", "positions of responsibility", "activities"],
}
BULLET = re.compile(r"^\s*[•\-\*▪●◦‣·–]\s*")
YEAR = re.compile(r"(?:19|20)\d{2}")
SCORE = re.compile(r"(?:cgpa|gpa|sgpa|percentage|score)\s*[:\-]?\s*\d+(?:\.\d+)?(?:\s*/\s*10)?|\d{2}(?:\.\d+)?\s*%", re.I)
DEGREE = re.compile(r"\b(b\.?\s?e\.?|b\.?\s?tech|bachelor|m\.?\s?tech|master|m\.?\s?sc|b\.?\s?sc|bca|mca|mba|diploma|"
                    r"class\s?(?:xii|x|12|10)|12th|10th|puc|sslc|hsc|ssc|pre-university)\b", re.I)
INSTITUTE = re.compile(r"(college|university|institute|school|iit|nit|iiit|academy|vidyalaya)", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"(?:\+?\d[\d\s-]{8,}\d)")
URL = re.compile(r"(?:https?://)?(?:www\.)?(?:github\.com|linkedin\.com|leetcode\.com|[\w-]+\.(?:dev|me|io|app|vercel\.app|netlify\.app))/?[\w./-]*", re.I)
TECH_LINE = re.compile(r"^(?:tech(?:nologies|nology)?(?:\s*stack)?|tools|stack|built with)\s*[:\-]\s*", re.I)


def _heading_of(line: str) -> str | None:
    clean = re.sub(r"[^a-z& \-]", "", line.lower()).strip()
    if not clean or len(clean) > 40:
        return None
    for key, names in HEADINGS.items():
        if clean in names:
            return key
    return None


def normalise(text: str) -> str:
    """PDF extractors turn bullet glyphs into '(cid:127)' and similar; make them real bullets."""
    text = re.sub(r"\(cid:\d+\)", "•", text)
    return text.replace("\uf0b7", "•").replace("\u2022", "•")


def split_sections(text: str) -> dict[str, list[str]]:
    text = normalise(text)
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        head = _heading_of(line)
        if head:
            current = head
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _skill_tokens(lines: list[str]) -> list[str]:
    tokens: list[str] = []
    for line in lines:
        line = BULLET.sub("", line)
        if ":" in line:  # "Languages: Python, Java"
            line = line.split(":", 1)[1]
        for tok in re.split(r"[,|;/•·]|\s{2,}", line):
            tok = tok.strip(" .()")
            if 1 <= len(tok) <= 40:
                tokens.append(tok)
    return list(dict.fromkeys(tokens))


def _entries(lines: list[str]) -> list[dict]:
    """Group lines into entries: a non-bullet title line followed by bullet lines."""
    entries: list[dict] = []
    for line in lines:
        is_bullet = bool(BULLET.match(line))
        tech = TECH_LINE.match(line)
        prev = entries[-1]["lines"][-1] if entries and entries[-1]["lines"] else ""
        wrapped = bool(prev) and not is_bullet and not prev.rstrip().endswith((".", "!", "?", ":"))
        if wrapped and not tech:  # a bullet that the PDF wrapped onto two lines
            entries[-1]["lines"][-1] = prev + " " + line
        elif entries and tech:
            entries[-1]["tech_line"] = line[tech.end():]
        elif is_bullet or (entries and line[:1].islower()):
            if not entries:
                entries.append({"title": "", "lines": []})
            entries[-1]["lines"].append(BULLET.sub("", line))
        else:
            entries.append({"title": line, "lines": []})
    return entries


def _techs(text: str) -> list[str]:
    found = [name for name, pats in PATTERNS.items() if any(p.search(text) for p in pats)]
    # behavioural words (team, led...) are evidence, but not "technologies"
    return [f for f in found if category_of(f) != "Communication and Behavioural"]


def parse_projects(lines: list[str]) -> list[dict]:
    out = []
    for e in _entries(lines):
        title = e["title"]
        parts = re.split(r"\s+[|–—-]\s+", title, maxsplit=1)
        name = parts[0].strip(" :")
        desc = " ".join(e["lines"]).strip()
        tech_text = " ".join([e.get("tech_line", ""), parts[1] if len(parts) > 1 else ""])
        techs = [canonical(t) or t.strip() for t in re.split(r"[,|/]", tech_text) if t.strip()]
        techs = list(dict.fromkeys([t for t in techs if t] + _techs(desc + " " + tech_text)))
        if name or desc:
            out.append({"name": name or "Untitled project", "description": desc, "technologies": techs})
    return out


def parse_experience(lines: list[str]) -> list[dict]:
    out = []
    for e in _entries(lines):
        title = e["title"]
        period = " ".join(YEAR.findall(title))
        out.append({"title": title, "period": period, "description": " ".join(e["lines"]).strip()})
    return [x for x in out if x["title"] or x["description"]]


def parse_education(lines: list[str]) -> list[dict]:
    out: list[dict] = []
    for line in lines:
        line = BULLET.sub("", line)
        deg, inst = DEGREE.search(line), INSTITUTE.search(line)
        if deg or not out:
            out.append({"degree": "", "institution": "", "year": "", "score": "", "raw": line})
        entry = out[-1]
        if deg and not entry["degree"]:
            entry["degree"] = line.split("|")[0].split(",")[0].strip()
        if inst and not entry["institution"]:
            entry["institution"] = next((p.strip() for p in re.split(r"[|,]", line) if INSTITUTE.search(p)), line)
        years = YEAR.findall(line)
        if years:
            entry["year"] = years[-1]
        sc = SCORE.search(line)
        if sc:
            entry["score"] = sc.group(0)
        if line != entry["raw"]:
            entry["raw"] += " / " + line
    return out


def parse_resume(text: str) -> dict:
    s = split_sections(text)
    header = s.get("header", [])
    return {
        "name": header[0] if header else "",
        "email_found": bool(EMAIL.search(text)),
        "phone_found": bool(PHONE.search(" ".join(header[:6]))),
        "links": list(dict.fromkeys(m.group(0) for m in URL.finditer(text)))[:8],
        "summary": " ".join(s.get("summary", []))[:800],
        "education": parse_education(s.get("education", [])),
        "skills": _skill_tokens(s.get("skills", [])),
        "projects": parse_projects(s.get("projects", [])),
        "experience": parse_experience(s.get("experience", [])),
        "certifications": [BULLET.sub("", x) for x in s.get("certifications", [])],
        "achievements": [BULLET.sub("", x) for x in s.get("achievements", [])],
        "sections_found": [k for k in s if k != "header"],
    }
