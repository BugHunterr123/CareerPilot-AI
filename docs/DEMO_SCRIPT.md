# Demo script (6 minutes)

Follows the Bobathon demo order (spec section 29). Before you start: server running, browser at
http://localhost:8000 in a fresh profile, `backend/sample_data/sample_resume.pdf` ready, zoom 100%.
Times are targets; rehearse once with a stopwatch.

| # | Time | Show | Say (in your own words) |
|---|---|---|---|
| 1 | 0:00-0:40 | Landing page | "Placement portals tell students a company is coming. They don't tell them what to study, what the rounds look like this year, or what their own resume is missing. Students piece it together from Reddit and seniors." |
| 2 | 0:40-1:10 | Create account, onboarding: education, then **Skip** on optional links | "Only the resume is required. GitHub, LinkedIn and LeetCode are optional and never block anything." |
| 3 | 1:10-2:00 | Upload the sample resume. Resume page: strengths, missing items, suggestions. Remove one skill in the review form and save | "The student checks what we read. Their corrections win." Point at the **Read by rule-based parser** badge: "Demo mode is labelled everywhere." |
| 4 | 2:00-2:30 | Skill Intelligence. Expand Python, then a skill marked Claimed | "Listing a skill is a claim; a project is evidence; answering questions validates it. That's what an interviewer probes." |
| 5 | 2:30-3:00 | Career Recommendations. Open "How the match % is calculated". Set Software Developer as target | "No black box: earned weight over total weight, and you can see exactly what's missing." |
| 6 | 3:00-3:50 | Company Explorer, Accenture. Scroll the stages; hover a source link; show the label chips and the Sources table. Click **Prepare for Accenture** | "Every line has a link, a date and a label: Official, Candidate-reported, Third-party. Where reports disagree, we show both." |
| 7 | 3:50-4:30 | Skill Gap Analysis, run it; expand the top item. Then Roadmap, Generate. Tick one task | "Gaps are ranked by a points formula: role weight times gap, plus one if a hiring stage tests it. The plan fits 8 hours a week and was generated in about 20 milliseconds." (read the real number off the header) |
| 8 | 4:30-5:15 | Mock Interviews, HR, start. Answer one question (paste a prepared answer). Show the feedback card, then **End and see report** | "One question at a time, scored on four visible criteria. It's practice feedback, not a hiring prediction." |
| 9 | 5:15-5:40 | Progress page, then Assistant: "What should I study today?" | "Everything here is computed from what the student actually did." |
| 10 | 5:40-6:00 | README "Impact" and "How we used IBM Bob" | Measured numbers only (test suite: 20 tests pass; plan generation time from the acceptance test). Then your real Bob examples. |

## Measured impact you can quote
Run these yourself just before the demo and quote what they print:
```bash
cd backend && python -m pytest -q -s tests/test_acceptance.py   # prints IMPACT plan_generation_ms=...
python -m pytest -q                                               # pass count
python ../e2e/journey.py                                          # full journey time per viewport, console errors
```
Do not quote user numbers (time saved, placement rates) unless you measured them with real students.

## IBM Bob segment (only what really happened)
Pick 2 or 3 tasks you actually ran from `docs/IBM_BOB_GUIDE.md`. For each, show the prompt, what Bob produced,
and what you kept or changed. A screen recording of the Bob session is the strongest evidence.

## Backup plan
- If the network is down: everything runs locally in demo mode; company source links will not open, but the
  guide content is stored locally.
- If the upload fails on stage, use the DOCX version of the sample resume.
- Keep a second browser tab already signed in with a finished journey.
