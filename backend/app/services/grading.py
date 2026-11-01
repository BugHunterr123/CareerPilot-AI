"""Small grading helpers shared by the question bank and timed tests."""
import re

from app.models import PracticeQuestion

_LETTER = re.compile(r"^\(?([A-Ha-h])[).:\s]")


def _strip_letter(text: str) -> str:
    m = _LETTER.match(text.strip())
    return text.strip()[m.end():].strip() if m else text.strip()


def correct_option_index(q: PracticeQuestion) -> int | None:
    """Answers are stored either as the exact option text or like "B) 16" / "B". Find the option."""
    opts = q.options or []
    ans = (q.answer or "").strip()
    if len(ans) > 1 and ans[0] in "'\"" and ans.find(ans[0], 1) > 0:
        ans = ans[1:ans.find(ans[0], 1)].strip()  # answer written as 'option text' plus an explanation
    if not opts or not ans:
        return None
    if ans in opts:
        return opts.index(ans)
    norm = [_strip_letter(o).lower() for o in opts]
    body = _strip_letter(ans).lower()
    m = _LETTER.match(ans + " ")
    if m:
        idx = "abcdefgh".index(m.group(1).lower())
        if idx < len(opts) and (not body or body == norm[idx] or norm[idx].startswith(body) or body.startswith(norm[idx])):
            return idx
    for i, o in enumerate(norm):
        if body == o:
            return i
    # answer like "72 km/h. Speed = ..." -> the longest option it starts with, ending at a word boundary
    cands = [i for i, o in enumerate(norm) if o and body.startswith(o) and (len(body) == len(o) or not body[len(o)].isalnum())]
    if cands:
        return max(cands, key=lambda i: len(norm[i]))
    return None


def mcq_is_correct(q: PracticeQuestion, chosen: str) -> bool:
    idx = correct_option_index(q)
    chosen = (chosen or "").strip()
    if idx is None:
        return False
    opts = q.options or []
    if chosen in opts:
        return opts.index(chosen) == idx
    if len(chosen) == 1 and chosen.upper() in "ABCDEFGH":
        return "ABCDEFGH".index(chosen.upper()) == idx
    return _strip_letter(chosen).lower() == _strip_letter(opts[idx]).lower()
