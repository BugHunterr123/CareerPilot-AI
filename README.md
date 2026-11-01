# CareerPilot AI

A placement-preparation platform for engineering students. Create an account, upload a resume, see which skills it
actually proves, compare roles, read a source-backed hiring guide for a target company, find the gaps between you
and a role at that company, then practise: coding problems that run against real test cases, timed tests, mock
interviews with a report per session, and a career assistant you can ask anything.

Built for the IBM Bobathon 2026. Version 2.

**Live:** https://careerpilot-ai.sites.tab.bot/ (sign up with any email; the server runs without an AI key, so
AI features use their labelled rule-based engines there. See "AI" below.)

![Skill gap: Data Engineer at Infosys](docs/screenshots/desktop_03_skill_gap.png)

Screenshots of every step (desktop and mobile) are in `docs/screenshots/`, taken by the browser journey on the live site.

## What it does

| Area | What the student gets |
|---|---|
| Account | Sign up, log in, log out (sidebar menu and Settings), change password, delete account. httpOnly cookie session |
| Resume | PDF/DOCX upload, extraction of skills, projects, education; a review screen to correct everything |
| Skills | Each skill marked validated / project evidence / claimed / inferred, with the quote it came from |
| Roles | 12 entry-level roles ranked by a published match formula |
| Companies | Hiring guides for Accenture, TCS, Infosys, Wipro, Capgemini, Cognizant, IBM, Deloitte, Tiger Analytics, Thales. Every fact has a source link and a label: Official, Candidate-reported, Third-party, AI practice |
| Skill gap | Requirements from the role's skill matrix merged with the topics the company's hiring stages test (with sources), plus an optional job description. Each requirement says where it came from. Updates when you change role or company |
| Plan | Dated tasks that fit weekly hours and test date |
| Practice | 104 runnable coding problems (at least 2 easy, 2 medium, 2 hard per company), each with visible and hidden test cases, starter code and solutions in Python, Java and C++; 130+ MCQs; filters that only offer combinations that exist |
| Code runner | CodeMirror editor, run on sample tests or your own input, submit against hidden tests. Python 3 in a sandbox (time, memory, process and file limits, import allowlist, audit hook) |
| Timed tests | Coding or aptitude/MCQ, per company and difficulty, with a timer, auto-finish and a scored review |
| Interviews | Questions generated per session for your role, company and projects (AI, or the role/company question bank). Each answer scored on a 4-part rubric (AI with a quote from your answer, or rules). The report uses only that session's answers. History list |
| Assistant | Ask anything. With AI: answers grounded in the company guides and your profile, with [n] citations. Without AI: an honest search of the guides, question bank and your data, with links |
| Progress | Completion, accuracy by subject, interview trend, application tracker |

## AI

AI is optional and configured only through environment variables.

| Provider | Settings |
|---|---|
| Google Gemini (recommended, free tier) | `LLM_PROVIDER=gemini`, `GEMINI_API_KEY=...` (from https://aistudio.google.com/apikey), optional `GEMINI_MODEL` (default `gemini-flash-latest`) |
| Any OpenAI-compatible API (OpenAI, IBM watsonx/Granite gateway, Groq, Together, Ollama) | `LLM_PROVIDER=openai_compatible`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` |
| None | leave the keys empty |

Every AI call has a timeout, retries on 429/5xx with backoff, JSON output validated by Pydantic (one repair
attempt), and a readable error. When a call fails the feature falls back to its rule-based engine and the UI says
so. `GET /api/meta` shows whether AI is configured (never the key).

With AI on: interview questions are written per session, answers are scored with a quote and a stronger answer,
the assistant answers free-form questions, and resume analysis is cross-checked against the resume text.

## Run it locally (about 5 minutes)

Requirements: Python 3.11+, Node 20+.

```bash
cp .env.example .env                      # add GEMINI_API_KEY if you have one
cd backend
python3 -m venv .venv && source .venv/bin/activate      # Windows: py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ../frontend && npm ci && npm run build && cd ../backend
uvicorn app.main:app --port 8000
```

Open http://localhost:8000 and create an account. FastAPI serves the built frontend and the API on one port.
Alembic creates the tables and the company data and question bank are seeded on start. API docs: /docs.
For frontend hot reload run `cd frontend && npm run dev` and open http://localhost:3000.

A synthetic test resume (a made-up student) can be downloaded from the upload screen or found in
`backend/sample_data/`.

## Run it with Docker (PostgreSQL)

```bash
cp .env.example .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env
docker compose up --build        # http://localhost:8000
```

## Deploy

The app is one container (or one Python process) plus a database. Production settings:
`ENVIRONMENT=production`, a long random `SECRET_KEY`, `DATABASE_URL` pointing at PostgreSQL, and optionally
`GEMINI_API_KEY`. Health check: `GET /api/health` (checks the database). Cookies are `Secure` in production, so
serve it over HTTPS (both platforms below do).

### Render

1. Push this repo to GitHub.
2. Render dashboard: New > PostgreSQL (free plan is fine). Copy its **Internal Database URL**.
3. New > Web Service > your repo. Runtime: **Docker** (uses the root `Dockerfile`). Health check path: `/api/health`.
4. Environment variables:
   - `ENVIRONMENT=production`
   - `SECRET_KEY` = output of `python -c "import secrets; print(secrets.token_urlsafe(48))"`
   - `DATABASE_URL` = the Internal Database URL (a `postgres://` URL is converted automatically)
   - `LLM_PROVIDER=gemini` and `GEMINI_API_KEY` = your key (optional)
5. Deploy. Migrations and seed data run on start. Render sets `$PORT`; the image listens on it.

Note: resume files are stored on local disk (`UPLOAD_DIR`). Add a Render disk mounted at `/data` if you want
uploaded files to survive redeploys (the extracted resume data is in PostgreSQL either way).

### Railway

1. New Project > Deploy from GitHub repo (Railway detects the `Dockerfile`).
2. In the project: New > Database > PostgreSQL.
3. On the app service, Variables:
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (reference variable)
   - `ENVIRONMENT=production`, `SECRET_KEY=<long random string>`
   - `LLM_PROVIDER=gemini`, `GEMINI_API_KEY=<key>` (optional)
4. Settings > Networking > Generate Domain. Settings > Deploy > Healthcheck path `/api/health`.
5. Optional: add a volume mounted at `/data` for resume files.

### Any VM

`ENVIRONMENT=production SECRET_KEY=... DATABASE_URL=... uvicorn app.main:app --host 0.0.0.0 --port 8000
--proxy-headers` behind nginx or Caddy for HTTPS. Use one worker process: the rate limiter and the code-runner
slots are in memory (see docs/KNOWN_LIMITATIONS.md).

## Configuration

All settings are environment variables, documented in `.env.example`: environment, secret key and cookie
options, database, AI provider, rate limits (`RATE_LIMIT_AUTH`, `RATE_LIMIT_AI`, `RATE_LIMIT_CODE`), code runner
limits, upload size and GitHub options.

## Tests

```bash
cd backend && python -m pytest -q        # 90 tests, about 30 s, SQLite, no network (also 90/90 on PostgreSQL 15)
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/test_db python -m pytest -q   # on PostgreSQL
BASE_URL=http://localhost:8000 python ../e2e/journey.py   # browser journey (pip install playwright; playwright install chromium)
```

The suite covers: cookie login/logout, CSRF header, password change signing out old sessions, rate limits;
different role and company combinations giving different skill-gap results with sources; the practice filter
combination that used to return nothing; every company having runnable easy/medium/hard problems; hidden test data
never reaching the browser; sandbox blocks (file access, imports, infinite loops); timed tests (scoring, answers
hidden until finish, expiry); interview reports per session; AI scoring with verified quotes and fallback; the
assistant with and without AI; the LLM layer (retries, JSON repair, provider selection); health and headers.
AI tests replace the network call with a fake, so no key is needed.

## Project layout
```
backend/   FastAPI app (app/routers, app/services, app/models), Alembic migrations, seed data, tests
frontend/  Next.js App Router + TypeScript + Tailwind, exported as static files and served by FastAPI
e2e/       Playwright journey and screenshots
docs/      ARCHITECTURE, API, DEMO_SCRIPT, IBM_BOB_GUIDE, KNOWN_LIMITATIONS
```

## Data honesty
- Company facts come from public pages; each links to its source with a label and date (or "page undated").
- **Candidate-reported** questions were reported by students online. **AI practice** questions were written for
  practice on reported topics, tested, and never presented as previously asked.
- Match percentages and interview scores are practice indicators, not hiring predictions.

## How we used IBM Bob
> Fill this in with what you actually did. See `docs/IBM_BOB_GUIDE.md`.

| Task | Prompt used | What Bob produced | What we changed |
|---|---|---|---|
| | | | |

## Licence
MIT for the code. Company names belong to their owners; linked sources belong to their publishers.
