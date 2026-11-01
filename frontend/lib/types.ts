/** Shapes of the JSON the backend returns (kept loose where pages only display values). */
export type User = { id: number; email: string; full_name: string };
export type Meta = { ai_configured: boolean; ai_provider: string | null; ai_model: string | null; github_api: boolean; max_upload_mb: number;
  code_runner: { language: string; timeout_seconds: number }; version: string };
export type JourneyStep = { key: string; label: string; done: boolean; href: string };

export type Profile = {
  college: string; degree: string; branch: string; graduation_year: number | null; cgpa: string | null;
  interests: string[]; preferred_roles: string[]; preferred_locations: string[]; job_type: string | null;
  weekly_hours: number | null; target_date: string | null; certifications: string[]; achievements: string[];
  target_role_key: string | null; target_role_title: string | null; target_company_id: number | null; optional_step_done: boolean;
};
export type Link = { id: number; kind: string; url: string; consent: boolean; status: string; note: string;
  manual_details: string; summary: Record<string, unknown>; last_checked: string | null };

export type Evidence = { kind: string; source: string; quote: string };
export type Skill = { id: number; name: string; category: string; level: string; confidence: string;
  needs_validation: string; next_step: string; user_added: boolean; evidence: Evidence[] };
export type Basis = { has_resume: boolean; sources_used: string[]; limited_info: boolean; note: string;
  unavailable: { kind: string; note: string }[] };

export type Project = { id?: number; name: string; description: string; technologies: string[]; source?: string };
export type Education = { degree: string; institution: string; year: string; score: string };
export type Resume = {
  id: number; filename: string; size_bytes: number; uploaded_at: string; parse_status: string; warnings: string[];
  reviewed: boolean; engine: string; text_preview: string; projects: Project[];
  parsed: { skills: string[]; projects: Project[]; education: Education[]; certifications: string[]; achievements: string[];
    links: string[]; sections_found: string[]; summary: string; experience: { title: string; description: string }[] };
  analysis: { strengths: string[]; missing: string[]; suggestions: string[]; skill_count: number; project_count: number };
};

export type RoleRec = { role_key: string; title: string; summary: string; match_pct: number; why: string[];
  relevant: { skill: string; level: string; weight: string }[]; partial: { skill: string; level: string; weight: string }[];
  missing: { skill: string; weight: string }[]; learn: string[]; projects: string[];
  resources: { title: string; url: string; provider: string }[]; formula: { earned: number; total: number; interest_bonus: number } };

export type FormatLine = { text: string; source: string };
export type Stage = { id: number; order: number; name: string; kind: string; what: string; format: FormatLine[];
  evaluates: string[]; study: string[]; tips: string[]; before_next: string; label: string };
export type Source = { url: string; title: string; publisher: string; date: string | null; label: string; accessed: string };
export type CompanySummary = { id: number; slug: string; name: string; overview: string; stage_count: number;
  role_titles: string[]; source_count: number; source_labels: string[]; question_count: number; research_date: string };
export type CompanyDetail = CompanySummary & { careers_url: string | null; variation_note: string; overview_source: string | null;
  roles: { id: number; title: string; description: string; role_key: string; role_title: string; skills: string[];
    eligibility: FormatLine[]; compensation: FormatLine[] }[];
  stages: Stage[]; sources: Record<string, Source>; selected: boolean };

export type GapSource = { url: string; title: string; publisher: string; label: string; date: string | null };
export type CompanyTopic = { topic: string; stage: string; stage_order: number; label: string; sources: GapSource[] };
export type GapItem = { skill: string; category: string; status: "shown" | "partial" | "missing"; evidence_level: string | null;
  origin: "role" | "company" | "both" | "jd"; role_weight: number | null; company_topics: CompanyTopic[];
  weight: number; priority: string; points: number; reasons: string[]; tested_in: string[]; why: string; order?: number;
  resources: { title: string; url: string; provider: string; minutes: number }[]; practice_subject: string | null };
export type CompanyStageTopics = { order: number; name: string; kind: string; label: string; format: string[];
  topics: { topic: string; skill: string }[]; sources: GapSource[] };
export type GapReport = { id: number; role_key: string; company_id: number | null; created_at: string; job_description_used: boolean;
  items: GapItem[]; summary: { role: string; role_key: string; company: string | null; company_id: number | null; shown: number; partial: number;
    missing: number; total: number; from_role: number; from_company: number; from_both: number; from_jd: number;
    role_requirements: { skill: string; weight: number; level: string }[]; company_stages: CompanyStageTopics[];
    projects: string[]; formula: string } };

export type Task = { id: number; week: number; due_date: string; topic: string; skill: string; explanation: string; why: string;
  resources: { title: string; url: string; provider: string; minutes?: number }[]; practice: Record<string, string | number>;
  est_minutes: number; priority: string; status: string; completed_at: string | null };
export type Roadmap = { id: number; role_key: string; role_title: string; company_id: number | null; company_name: string | null;
  weekly_hours: number; start_date: string; target_date: string | null; plan_type: string; notes: string[];
  generation_ms: number; created_at: string; total: number; done: number; tasks: Task[] };

export type Question = { id: number; company_id: number | null; stage_kind: string; subject: string; qtype: string; difficulty: string;
  question: string; code: string; options: string[] | null; answer: string; explanation: string; hints: string[];
  concepts: string[]; sample_io: string; solution: string; label: string; source_note: string;
  source: { url: string; title: string; publisher: string; date: string | null; label: string } | null;
  saved: boolean; stats: { attempts: number; correct: number; last_correct: boolean | null };
  title: string; company_name: string | null; runnable: boolean; starter_code: string; solutions_other: Record<string, string>;
  io_format: { input_format?: string; output_format?: string; constraints?: string };
  visible_tests: { input: string; output: string }[]; hidden_test_count: number;
  my_answer?: { code?: string; choice?: string; passed?: number; total?: number; correct?: boolean }; correct_option?: string | null };
export type TestCaseResult = { index: number; hidden: boolean; passed: boolean; status: string; time_ms: number;
  input?: string; expected?: string; output?: string; error?: string };
export type TestRun = { passed: number; total: number; all_passed: boolean; results: TestCaseResult[] };
export type RunResult = { status: string; stdout: string; stderr: string; time_ms: number };
export type PracticeTest = { id: number; kind: "coding" | "mcq"; company_id: number | null; company_name: string | null; difficulty: string;
  minutes: number; status: string; score: number | null; started_at: string; ends_at: string; finished_at: string | null;
  answered: number; questions: Question[]; note?: string };

export type Score = { score: number; reason: string };
export type InterviewResponse = { index: number; question: string; answer: string; scores: Record<string, Score>;
  feedback: { good: string[]; missing: string[]; engine: string; structure_tip: string; quote?: string; better_answer?: string }; total: number };
export type Interview = { id: number; role_key: string; role_title: string; company_name: string | null; itype: string;
  difficulty: string; duration_min: number; status: string; scoring_mode: string; total_questions: number; current_index: number;
  overall: number | null; created_at: string; current_question: { q: string; kind: string; topic: string; origin?: string } | null; question_source?: string;
  responses: InterviewResponse[]; report: Record<string, any> | null; last_feedback?: InterviewResponse & { question: string } };
