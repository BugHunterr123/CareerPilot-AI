# Using IBM Bob on CareerPilot AI

The Bobathon asks for **genuine** examples of IBM Bob helping development. This repository does not contain
any Bob output and the README does not claim any. This guide lists real, useful tasks on this codebase that you
can run in Bob yourself, so the evidence you show is your own.

## How to record evidence
1. Open the repository folder in IBM Bob.
2. Before each task, start a screen recording (or take screenshots of the prompt and the result).
3. Commit Bob's changes on their own, with a message such as `bob: add LeetCode CSV import`, so `git log`
   shows exactly what came from the session.
4. After each task, fill in one row of the "How we used IBM Bob" table in the README:
   task, prompt, what Bob produced, what you changed.

Use whichever Bob mode fits (asking about code, planning, or editing). Always run the tests after a change:
`cd backend && python -m pytest -q`.

## Tasks, by Bobathon category

### 1. Project planning
> Read README.md, docs/ARCHITECTURE.md and docs/KNOWN_LIMITATIONS.md. Propose a prioritised plan for the next
> two weeks that would make CareerPilot more useful for students at a tier-3 college. For each item give the files
> to change and how we would test it.

### 2. Architecture
> Explain how a resume upload flows through the backend, from routers/resume.py to the skills and role
> recommendations. Draw it as a sequence diagram in Mermaid and point out any step that could be slow with a
> 20-page PDF.

### 3. Frontend
> In frontend/app/(app)/practice/page.tsx, add a "Timed set" mode: pick 10 questions matching the current
> filters, show a countdown (default 15 minutes), and show a score summary at the end. Reuse QuestionCard and the
> existing design tokens; no new colours. Keep it accessible (keyboard, screen reader labels).

### 4. Backend
> Add an endpoint POST /api/profile/leetcode-csv that accepts a CSV of solved problems (title, difficulty, tags),
> stores the counts in the existing manual_details field of the LeetCode link, and lets skills_engine.py treat
> tags like "hash-table" or "two-pointers" as evidence for Data Structures. Add a pytest for it.

### 5. Database models
> Review backend/app/models/. Suggest indexes for the queries in routers/questions.py and routers/progress.py,
> then write an Alembic migration (0002) that adds them. Make sure it works on both SQLite and PostgreSQL.

### 6. AI workflows
> In services/profile_analysis.py the LLM extraction is validated by Pydantic and filtered by a hallucination
> guard. Write a small evaluation script (backend/scripts/eval_extraction.py) that runs the extractor on the sample
> resume and reports precision and recall of skills against a hand-written expected list. Then suggest prompt changes.

> Configure LLM_BASE_URL / LLM_API_KEY / LLM_MODEL for an IBM Granite model on watsonx.ai (through an
> OpenAI-compatible endpoint) and check that services/llm.py structured() still returns valid JSON. Fix anything
> that breaks.

### 7. Debugging
Pick a real bug you hit. If you have none, try these:
> Uploading a resume whose skills section uses a two-column table loses some skills. Find out why in
> services/resume_parser.py and fix it, with a test using a generated DOCX.

> The mock interview's rule-based clarity score punishes very short but correct answers. Look at
> services/interviewer.py and propose a fairer rule, with before/after scores on three example answers.

### 8. Testing
> Read backend/tests/. Which important behaviours are not covered? Write tests for: the roadmap dropping
> low-priority topics when hours are too few, the GitHub link SSRF guard rejecting http://127.0.0.1, and the
> assistant refusing to invent a cutoff score.

### 9. Documentation
> Update docs/API.md from the live OpenAPI schema at http://localhost:8000/openapi.json, keeping the notes column.
> Then write a one-page "For placement officers" document explaining what the tool does and does not do.

## Company data refresh (a good live demo)
> Open backend/app/seed/data/companies/wipro.json. For each stage, check whether the linked sources still say the
> same thing. Where a source has changed, update the text, keep the label honest (Official / Candidate-reported /
> Third-party), and set "date" to the page's date. Do not invent facts that are not on the page.

Restart the server afterwards; the seed loader notices the changed file and updates the database.

## What not to do
- Do not paste Bob output into the README that you did not produce in a real session.
- Do not describe hand-written code as Bob-generated, or the other way round.
