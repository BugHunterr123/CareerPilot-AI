"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAction, useApi } from "@/lib/hooks";
import type { CompanySummary, Interview, Profile } from "@/lib/types";
import { useShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Button, Card, Empty, ErrorNote, Field, Notice } from "@/components/ui";

const TYPES = [
  ["mixed", "Mixed", "HR opener, a project question, technical questions"], ["technical", "Technical", "OOP, DBMS, OS, networks, SQL, ML"],
  ["coding", "Coding approach", "Explain how you would solve a problem"], ["project", "Project deep dive", "Questions built from your own projects"],
  ["hr", "HR", "Introduction, strengths, why this company"], ["behavioural", "Behavioural", "Teamwork, conflict, learning fast"],
];
type Hist = { id: number; itype: string; difficulty: string; status: string; overall: number | null; created_at: string; questions: number; answered: number; company_name: string | null };

export default function InterviewSetup() {
  const router = useRouter();
  const { meta } = useShell();
  const hist = useApi<Hist[]>("/api/interviews");
  const roles = useApi<{ role_key: string; title: string }[]>("/api/roles");
  const comps = useApi<{ companies: CompanySummary[] }>("/api/companies");
  const prof = useApi<{ profile: Profile }>("/api/profile");
  const [opt, setOpt] = useState({ itype: "mixed", difficulty: "medium", duration_min: 15, role_key: "", company_id: "" });
  useEffect(() => {
    const p = prof.data?.profile;
    if (p) setOpt((o) => ({ ...o, role_key: o.role_key || p.target_role_key || "software_developer",
      company_id: o.company_id || (p.target_company_id ? String(p.target_company_id) : "") }));
  }, [prof.data]);
  const act = useAction();
  const start = () => act.run(async () => {
    const mi = await api<Interview>("/api/interviews", { body: { itype: opt.itype, difficulty: opt.difficulty, duration_min: opt.duration_min,
      role_key: opt.role_key || null, company_id: opt.company_id ? Number(opt.company_id) : null } });
    router.push(`/interview/session/?id=${mi.id}`);
  });
  return (
    <>
      <PageHeader eyebrow="Mock interviews" title="Practise out loud, one question at a time">
        Type your answer as you would say it. Each answer is scored on four things: key concepts, depth, structure and clarity.
      </PageHeader>
      {meta && (meta.ai_configured
        ? <Notice tone="green" className="mb-6">Every new session gets fresh questions written by the AI for your role, company and resume projects, and each answer is scored by the AI against the rubric.</Notice>
        : <Notice tone="blue" className="mb-6">AI is not configured on this server, so questions come from CareerPilot&apos;s question bank (role and company specific, avoiding your recent questions) and answers are scored by a transparent rule-based rubric. Every session still gets its own report from its own answers.</Notice>)}
      <Card className="mb-10 p-6">
        <p className="mb-2 text-sm font-medium">Interview type</p>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3" role="radiogroup" aria-label="Interview type">
          {TYPES.map(([k, t, d]) => (
            <button key={k} role="radio" aria-checked={opt.itype === k} onClick={() => setOpt({ ...opt, itype: k })}
              className={`rounded-md border px-3 py-2.5 text-left transition-colors ${opt.itype === k ? "border-accent bg-accent-soft" : "border-line hover:bg-paper"}`}>
              <p className="text-sm font-medium">{t}</p><p className="text-xs text-ink-muted">{d}</p>
            </button>
          ))}
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <Field label="Target role" htmlFor="irole"><select id="irole" className="input" value={opt.role_key} onChange={(e) => setOpt({ ...opt, role_key: e.target.value })}>{roles.data?.map((r) => <option key={r.role_key} value={r.role_key}>{r.title}</option>)}</select></Field>
          <Field label="Company" htmlFor="icomp" optional><select id="icomp" className="input" value={opt.company_id} onChange={(e) => setOpt({ ...opt, company_id: e.target.value })}><option value="">No specific company</option>{comps.data?.companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <Field label="Difficulty" htmlFor="diff"><select id="diff" className="input" value={opt.difficulty} onChange={(e) => setOpt({ ...opt, difficulty: e.target.value })}>{["easy", "medium", "hard", "mixed"].map((d) => <option key={d}>{d}</option>)}</select></Field>
          <Field label="Length" htmlFor="len" hint={`${Math.max(3, Math.min(8, Math.floor(opt.duration_min / 3)))} questions`}><select id="len" className="input" value={opt.duration_min} onChange={(e) => setOpt({ ...opt, duration_min: Number(e.target.value) })}>{[9, 15, 24].map((m) => <option key={m} value={m}>{m} minutes</option>)}</select></Field>
          <div className="flex items-end"><Button busy={act.busy} onClick={start} className="w-full sm:w-auto">Start interview</Button></div>
        </div>
        <div className="mt-2"><ErrorNote message={act.error} /></div>
      </Card>
      <h2 className="mb-3 font-serif text-xl font-semibold">Past interviews</h2>
      {hist.data && hist.data.length ? (
        <Card className="overflow-hidden"><ul className="divide-y divide-line">
          {hist.data.map((h) => (
            <li key={h.id}><Link href={`/interview/session/?id=${h.id}`} className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-paper/60">
              <span><span className="text-sm font-medium"><span className="text-ink-muted">#{h.id}</span> <span className="capitalize">{h.itype} · {h.difficulty}</span></span><span className="block text-xs text-ink-muted">{new Date(h.created_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}{h.company_name ? ` · ${h.company_name}` : ""}</span></span>
              {h.status === "completed" ? <span className="flex items-center gap-3"><span className="hidden text-xs text-ink-muted sm:inline">Open report</span><span className="font-serif text-lg font-semibold">{h.overall}<span className="text-sm text-ink-muted">/5</span></span></span> : <Badge tone="amber">In progress {h.answered}/{h.questions}</Badge>}
            </Link></li>
          ))}
        </ul></Card>
      ) : <Empty title="No interviews yet">Your first one sets a baseline you can compare against later.</Empty>}
    </>
  );
}
