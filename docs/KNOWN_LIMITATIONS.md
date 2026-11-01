# Known limitations (v2)

Written so that judges, mentors and students know exactly where the edges are.

## Data
- **Hiring processes change.** Company guides come from public pages checked in October/November 2026. Many
  details (round order, question counts, cutoffs) are candidate-reported and differ by year, college and role.
  Each line links to its source; the app never claims a process is guaranteed.
- **Accenture is the deepest guide.** The other nine have 4-6 stages and their own question sets.
- **AI practice questions** (including most of the runnable coding problems) were written for practice on topics
  candidates report for that company. They are labelled and never presented as previously asked. Converted
  candidate-reported problems keep their label and source.
- Source links can go stale. There is no automated link checker.

## AI
- **The public deployment has no AI key.** There, interview questions come from the role/company question bank,
  answers are scored by the rule-based rubric and the assistant answers from search. Add `GEMINI_API_KEY` (or an
  OpenAI-compatible provider) to switch the AI paths on; nothing else changes.
- The rule-based scorer checks key points, examples and reasons, structure and length. It is consistent and
  explainable but cannot judge whether an explanation is actually correct.
- AI output is validated (JSON schema, quotes must appear in the student's answer), but an AI can still be wrong
  about general concepts. Company facts are restricted to the cited sources.
- Assistant retrieval is BM25 keyword search over guides, questions and the student's data, not vector search.

## Code runner
- **Python only.** Java and C++ solutions are shown for reading (they were compiled and tested offline on the same
  cases) but the server runs Python.
- **It is a practice sandbox, not a hardened online judge.** Student code runs in a separate process with CPU,
  memory, file-size, open-file and process limits, an import allowlist and an audit hook that blocks files,
  network and subprocesses. For a large public deployment, also run the app in a container without network egress,
  or move execution to a dedicated judge (for example Judge0).
- At most 2 programs run at once per server process; a burst of submissions waits in line.
- Time limits are generous (4 s per test) and not tuned per problem, so very slow approaches can still pass.

## Accounts and operations
- No email verification and no "forgot password" (there is no mail service). Users can change their password
  while logged in; an admin can reset it in the database.
- Rate limits and code-runner slots are in memory, so run a single worker process (or move limits to Redis or the
  proxy). The limiter trusts the first `X-Forwarded-For` address, which a platform proxy sets.
- Uploaded resume files are stored on local disk (`UPLOAD_DIR`); mount a volume to keep them across redeploys.
- SQLite is the zero-setup default; use PostgreSQL for anything shared (Render/Railway guides in the README).

## Features not built
- No voice in mock interviews; answers are typed.
- LinkedIn and LeetCode are not read automatically (no scraping, no passwords). GitHub is read through its public API.
- No applying on the student's behalf and no placement-portal integration; applications are tracked by hand.
- Resume parsing works best on text-based, single-column resumes. Scanned PDFs are refused (no OCR).
