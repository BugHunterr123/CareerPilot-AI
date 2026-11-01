# CareerPilot AI API

Base URL: `http://localhost:8000`. Interactive docs with request/response schemas: `/docs` (Swagger) and `/redoc`.

Auth: every route except register, login, health and meta needs `Authorization: Bearer <token>`. Another user's record always answers **404**, never 403, so ids cannot be probed.

Errors: `{"detail": "plain-English message"}`. 401 = not signed in, 404 = not found or not yours, 409 = conflict, 422 = invalid input.


## Auth

| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/register` | Body `{email, password, full_name}`. Password: 8+ chars with a letter and a number. Returns `{token, user}`. 409 if the email exists. |
| POST | `/api/auth/login` | Body `{email, password}`. Returns `{token, user}`. 401 on wrong credentials. |
| GET | `/api/auth/me` | Current user. |

## Profile

| Method | Path | Notes |
|---|---|---|
| GET | `/api/profile` | `{user, profile, links}`. |
| PUT | `/api/profile` | Partial update: college, degree, branch, graduation_year, cgpa, interests, preferred_roles, preferred_locations, job_type, weekly_hours, target_date, full_name. |
| POST | `/api/profile/optional-done` | The student finished (or skipped) the optional links step. |
| POST | `/api/profile/links` | Body `{kind: github|linkedin|leetcode|portfolio, url, consent, manual_details}`. GitHub is read through the public API; LinkedIn/LeetCode are never scraped. |
| POST | `/api/profile/links/{link_id}/check` | Re-read a link. |
| DELETE | `/api/profile/links/{link_id}` | Delete Link |

## Resume

| Method | Path | Notes |
|---|---|---|
| GET | `/api/resume` | Active resume, or `null` if none yet. |
| POST | `/api/resume` | Multipart `file` (PDF/DOCX, max 5 MB). 422 with a plain-English reason for wrong type, fake extension, empty, oversized, or scanned (too little text). 201 with parsed data and the analysis report. |
| DELETE | `/api/resume` | Delete |
| PUT | `/api/resume/review` | Body `{skills, projects, education, certifications, achievements}`. Rebuilds skills and role matches. |
| GET | `/api/resume/file` | Download the original file (owner only). |

## Skills & careers

| Method | Path | Notes |
|---|---|---|
| GET | `/api/skills` | Skills grouped by category with level, confidence, evidence quotes and next step. |
| POST | `/api/skills` | Body `{name}`. Adds a claimed skill. |
| DELETE | `/api/skills/{skill_id}` | Remove Skill |
| POST | `/api/skills/rebuild` | Rebuild |
| GET | `/api/careers` | Role recommendations with the formula, relevant/partial/missing skills, projects and resources. |
| POST | `/api/careers/refresh` | Refresh |
| POST | `/api/careers/select` | Body `{role_key}`. Sets the target role. |
| GET | `/api/roles` | All 11 roles. |

## Companies

| Method | Path | Notes |
|---|---|---|
| GET | `/api/companies` | Company summaries (stage, question and source counts, labels present). |
| GET | `/api/companies/{slug}` | Full guide: roles (eligibility and compensation lines, each with a source key), stages, and a `sources` map (url, publisher, title, date, label, accessed). |
| POST | `/api/companies/{slug}/select` | Body `{role_key?}`. Sets target company. |

## Gap & roadmap

| Method | Path | Notes |
|---|---|---|
| POST | `/api/gaps` | Body `{role_key, company_id?, job_description?}`. Returns prioritised items with points, reasons, stages that test them and resources. |
| GET | `/api/gaps/latest` | Latest report, or `null`. |
| POST | `/api/roadmap/generate` | Body `{weekly_hours?, target_date?, use_target_company?}`. Returns the plan with `generation_ms` and `plan_type`. Finished tasks are not re-planned. |
| GET | `/api/roadmap` | Active roadmap, or `null`. |
| PATCH | `/api/roadmap/tasks/{task_id}` | Body `{status?: todo|done|skipped, due_date?}`. |

## Questions

| Method | Path | Notes |
|---|---|---|
| GET | `/api/questions` | Query: `q, company (slug or 'general'), subject, qtype, difficulty, label, saved, incorrect, page`. |
| GET | `/api/questions/facets` | Filter values and the user's attempt counts. |
| POST | `/api/questions/{qid}/attempt` | Body `{response, self_correct?}`. MCQs are auto-checked; other types use the student's self-assessment. |
| POST | `/api/questions/{qid}/save` | Save |
| DELETE | `/api/questions/{qid}/save` | Unsave |

## Mock interviews

| Method | Path | Notes |
|---|---|---|
| GET | `/api/interviews` | History |
| POST | `/api/interviews` | Body `{itype: mixed|technical|coding|project|hr|behavioural, difficulty, duration_min}`. |
| GET | `/api/interviews/{iid}` | Get |
| POST | `/api/interviews/{iid}/answer` | Body `{answer}`. Scores the answer and returns the next question, or the final report when done. 409 after completion. |
| POST | `/api/interviews/{iid}/finish` | End early and build the report from the answers so far. |

## Progress & dashboard

| Method | Path | Notes |
|---|---|---|
| GET | `/api/journey` | The 8-step tracker state. |
| GET | `/api/progress` | Indicators, daily activity, subject accuracy, interview trend, applications. |
| POST | `/api/applications` | Body `{company_name, role?, status?, applied_on?, interview_date?, outcome?, notes?}`. |
| PUT | `/api/applications/{aid}` | Edit App |
| DELETE | `/api/applications/{aid}` | Delete App |
| GET | `/api/dashboard` | Everything the dashboard shows in one call. |

## Assistant

| Method | Path | Notes |
|---|---|---|
| GET | `/api/assistant` | History |
| POST | `/api/assistant` | Body `{message}`. Reply with `meta.citations`, `meta.actions` and `meta.engine` (llm or rules). |
| DELETE | `/api/assistant` | Clear |

## Privacy

| Method | Path | Notes |
|---|---|---|
| GET | `/api/privacy/export` | All of the user's data as JSON. |
| DELETE | `/api/privacy/account` | Body `{password}`. Deletes the account, the resume file and every linked row. |

## System

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | Health |
| GET | `/api/meta` | Tells the UI whether AI is configured (provider and model, never the key), the code runner limits and the version, so every page can label which engine produced a result. |
