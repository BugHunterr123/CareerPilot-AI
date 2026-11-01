# Architecture

```
 Browser (Next.js static export, TypeScript, Tailwind, Recharts)
    |  fetch /api/*  (JWT in Authorization header)
    v
 FastAPI  -- routers/ --> services/ --> SQLAlchemy models --> SQLite or PostgreSQL
    |                       |
    |                       +--> llm.py  (optional, any OpenAI-compatible endpoint)
    |                       +--> GitHub public API (optional, with SSRF guard)
    +-- serves frontend/out at "/" (one port in production)
```

One process serves both the API and the built frontend. In development the frontend can also run on
`npm run dev` (port 3000) and call the API on port 8000 (CORS is configured for that).

## Backend (`backend/app`)
| Layer | Files | Job |
|---|---|---|
| Config | `config.py` | pydantic-settings; every value from env or `.env`. `llm_ready` is true when a provider and key are set (Gemini or any OpenAI-compatible API) |
| Data | `db.py`, `models/` (25 tables) | users, profiles, links, resumes, projects, skills + evidence, companies, roles, stages, sources, questions, attempts, gap reports, roadmaps + tasks, interviews + responses, events, applications, assistant messages |
| Security | `security.py`, `deps.py` | bcrypt hashes, JWT, `get_current_user`; `owned()` returns 404 for anything that is not the caller's |
| Routers | `routers/*.py` | thin HTTP layer, one file per area (see docs/API.md) |
| Services | `services/*.py` | all the logic, described below |
| Migrations | `alembic/` | run automatically at startup (`alembic upgrade head`) |
| Seed | `seed/data/`, `services/seed.py` | companies, questions, resources; idempotent via a content hash per company |

## The engines
**Resume files** (`resume_files.py`): checks extension, real file signature (`%PDF`, ZIP for DOCX), size limit,
empty file, and at least 150 characters of extractable text (so scanned PDFs are refused with a reason instead of guessed).

**Resume parser** (`resume_parser.py`): pdfplumber/pypdf/python-docx text, section detection, project blocks,
education rows, certifications. Optional LLM pass (`profile_analysis.py`) returns Pydantic-validated JSON; any skill
the model returns that does not appear in the resume text is dropped (hallucination guard).

**Skill intelligence** (`skills_engine.py`, `taxonomy.py`): a taxonomy of skills with regex patterns and categories.
Levels: validated (correct practice answers) > project (used in a project, internship or repo) > claimed (listed) >
inferred (implied, e.g. Flask implies Python). Every skill keeps the quote that produced it.

**Role recommender** (`recommender.py`, `roles.py`): 11 roles, each a weighted skill list (core 3, important 2, nice 1).
Evidence earns a share of the weight: validated 100%, project 80%, claimed 40%, inferred 25%.
Match % = earned / total, plus up to 5 points for a stated interest. The formula is shown in the UI.

**Gap analysis** (`gap_analysis.py`): requirements = role skills + company role skills + skills tested by each
hiring stage (`STAGE_SKILLS`) + skills found in a pasted job description.
`points = weight x gap (missing 1, partial 0.5) + 1 if a stage tests it`. High >= 3, medium >= 1.5.

**Planner** (`planner.py`): daily budget = weekly hours / 6 (one rest day). High-priority gaps first, company stage
practice woven in, a mock interview in the last week. If time runs out, low-priority topics are dropped and listed
in the plan notes. Measures its own generation time.

**Question bank** (`seed/data`): 200 Accenture questions, 117 more across the other nine companies, and 36 general
AI practice questions. Labels: Candidate-reported, AI practice, Third-party.

**Mock interviewer** (`interview_bank.py`, `interviewer.py`, `interview_flow.py`): builds a question plan from the
type, role, company and the student's own projects. Each answer is scored 0-5 on concepts, depth, structure and
clarity, by rules (keyword coverage, example/reason words, STAR or definition-example structure, length) or by the LLM
with the same rubric. The final report carries a disclaimer.

**Assistant** (`assistant.py`): retrieves the student's next tasks, gaps, roles and the relevant company stages
(keyword retrieval). With an LLM key it answers from that context only; without one, the best BM25 matches are shown with links and a note that AI is off.
Questions the data cannot answer (cutoffs, guarantees) get a plain "the sources do not say".

## Frontend (`frontend/`)
- App Router with a static export (`output: "export"`), served by FastAPI from the same origin
  (cookie auth, no CORS needed in production).
- `components/AppShell.tsx`: sidebar with user menu (log out, account), mobile drawer, step tracker, login guard via /api/auth/me.
- `lib/api.ts`: one fetch wrapper (token, errors as readable messages, 401 -> login).
- Design tokens in `tailwind.config.ts`: warm paper background, one deep-green accent, Source Serif 4 headings,
  Inter body, 8px spacing grid. Every data page has loading skeletons, empty states and retryable errors.

## Privacy and security
- Passwords hashed with bcrypt; tokens are JWTs signed with `JWT_SECRET`.
- Every query filters by the current user; foreign ids answer 404. Covered by `tests/test_isolation.py`.
- Resume files are stored under `UPLOAD_DIR` with random names; download is owner-only.
- Export all data as JSON, or delete the account (removes the file and every linked row).
- External links: http(s) only, private and loopback addresses blocked before any request.
- No personal characteristics (gender, religion, caste, age) are collected or used.


## v2 additions
- **Auth** (`security.py`, `routers/auth.py`): JWT in an httpOnly `cp_session` cookie (Secure in production,
  SameSite=Lax) or a Bearer header for API clients. Cookie-authenticated writes must send
  `X-Requested-With: careerpilot` (CSRF guard). Tokens carry the user's `token_version`, bumped on password change
  so every older session stops working.
- **LLM layer** (`services/llm.py`): one OpenAI-compatible client for Gemini or any compatible provider; timeouts,
  retries, JSON mode with fallback, Pydantic validation with one repair attempt, `LLMError(user_message)`.
- **Retrieval** (`services/retrieval.py`): BM25 over company overviews, roles, stages, questions and resources,
  cached per seed; `services/assistant.py` grounds AI answers in it with [n] citations.
- **Skill gap** (`services/gap_analysis.py`): role matrix + company stage topics (mapped to skills by
  `TOPIC_RULES`, with stage sources) + JD skills; each requirement has an origin (role, company, both, jd).
- **Interviews** (`services/interviewer.py`, `interview_flow.py`): per-session plans (AI or bank, avoiding the
  last 3 sessions' questions), AI scoring with a verified quote, rule scoring fallback, report per session.
- **Code runner** (`services/code_runner.py`, `sandbox_harness.py`): separate Python process per test with
  rlimits, new session, import allowlist and audit hook; `run_tests` hides hidden test data.
- **Timed tests** (`routers/tests.py`, model `PracticeTest`): question selection per company/difficulty, server-side
  deadline, MCQ grading at finish, attempts recorded for progress.
- **Rate limits** (`ratelimit.py`): in-memory sliding window per IP for auth, AI and code buckets.
- **Content** (`seed/data/practice/<company>.json`): runnable problems with tests and multi-language solutions,
  and MCQs; upserted by stable `qkey` so ids survive reseeding.
