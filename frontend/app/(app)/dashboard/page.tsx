"use client";
import Link from "next/link";
import { ArrowRight, CalendarCheck } from "lucide-react";
import { useApi } from "@/lib/hooks";
import type { Task } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { ButtonLink, Card, Empty, ErrorNote, Meter, PageSkeleton } from "@/components/ui";
import { PriorityBadge } from "@/components/labels";

type Dash = {
  name: string; profile_completion: number; next_step: { label: string; href: string } | null;
  resume: { filename: string; status: string; reviewed: boolean; strengths: string[] } | null;
  skills: { total: number; validated: number; project: number; claimed: number; inferred: number; top: string[] };
  roles: { role_key: string; title: string; match_pct: number }[];
  target: { role: string | null; company: string | null; company_slug: string | null };
  gap: { shown: number; partial: number; missing: number; top: string[] } | null;
  roadmap: { total: number; done: number; plan_type: string; upcoming: Task[] } | null;
  saved_questions: number; last_interview: { id: number; overall: number; type: string; date: string } | null;
  readiness: { indicators: { name: string; value: number; unit: string; explain: string }[]; next: string[] };
};

const NEXT_COPY: Record<string, string> = {
  Resume: "Upload your resume to get started", Skills: "Check the skills we found", Roles: "Pick a target role",
  Company: "Choose a company to prepare for", Plan: "Generate your preparation plan", Practice: "Answer a few practice questions",
  Interview: "Try your first mock interview", Progress: "Complete a task from your roadmap",
};

export default function Dashboard() {
  const { data: d, error, loading, reload } = useApi<Dash>("/api/dashboard");
  if (loading && !d) return <PageSkeleton />;
  if (error) return <ErrorNote message={error.message} onRetry={reload} />;
  if (!d) return null;
  const pct = d.roadmap ? Math.round((100 * d.roadmap.done) / Math.max(1, d.roadmap.total)) : 0;
  return (
    <>
      <PageHeader eyebrow="Dashboard" title={`Hi ${d.name}.`}
        actions={d.next_step && <ButtonLink href={d.next_step.href + "/"}>{NEXT_COPY[d.next_step.label] ?? "Continue"} <ArrowRight className="h-4 w-4" /></ButtonLink>}>
        {d.target.company ? <>You are preparing for <b className="text-ink">{d.target.company}</b>{d.target.role && <> as a <b className="text-ink">{d.target.role}</b></>}.</>
          : "Pick a target company when you are ready. Everything else works without one."}
      </PageHeader>

      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        {d.readiness.indicators.map((i) => (
          <Card key={i.name} className="p-4">
            <p className="text-[13px] text-ink-muted">{i.name}</p>
            <p className="mt-1 font-serif text-[28px] font-semibold leading-none">{i.value}<span className="ml-0.5 text-base font-normal text-ink-muted">{i.unit}</span></p>
            <p className="mt-2 text-xs leading-snug text-ink-muted">{i.explain}</p>
          </Card>
        ))}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-lg font-semibold">Up next</h2>
            {d.roadmap && <Link href="/roadmap/" className="text-sm text-accent hover:underline">Full roadmap</Link>}
          </div>
          {d.roadmap ? (
            <>
              <div className="mt-3 flex items-center gap-3 text-xs text-ink-muted"><Meter value={pct} /><span className="shrink-0">{d.roadmap.done}/{d.roadmap.total} done</span></div>
              <ul className="mt-4 divide-y divide-line">
                {d.roadmap.upcoming.map((t) => (
                  <li key={t.id} className="flex items-start justify-between gap-3 py-3">
                    <div className="flex items-start gap-3">
                      <CalendarCheck className="mt-0.5 h-4 w-4 shrink-0 text-ink-faint" aria-hidden />
                      <div><p className="text-sm font-medium">{t.topic}</p><p className="text-xs text-ink-muted">{new Date(t.due_date).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })} · {t.est_minutes} min</p></div>
                    </div>
                    <PriorityBadge p={t.priority} />
                  </li>
                ))}
              </ul>
            </>
          ) : <div className="mt-4"><Empty title="No plan yet" action={<ButtonLink href="/roadmap/" size="sm">Create my plan</ButtonLink>}>Your plan turns skill gaps into dated tasks that fit your week.</Empty></div>}
        </Card>

        <div className="space-y-6">
          <Card className="p-5">
            <h2 className="font-serif text-lg font-semibold">Skills</h2>
            {d.skills.total ? (
              <>
                <p className="mt-1 text-sm text-ink-muted">{d.skills.total} skills: {d.skills.project + d.skills.validated} shown in projects or practice, {d.skills.claimed} only listed.</p>
                <div className="mt-3 flex flex-wrap gap-1.5">{d.skills.top.map((s) => <span key={s} className="rounded border border-line bg-paper px-2 py-0.5 text-xs">{s}</span>)}</div>
                <Link href="/skills/" className="mt-3 inline-block text-sm text-accent hover:underline">See evidence</Link>
              </>
            ) : <p className="mt-2 text-sm text-ink-muted">Upload your resume to see your skills.</p>}
          </Card>
          <Card className="p-5">
            <h2 className="font-serif text-lg font-semibold">Roles that fit now</h2>
            {d.roles.length ? d.roles.map((r) => (
              <div key={r.role_key} className="mt-3">
                <div className="flex justify-between text-sm"><span>{r.title}</span><span className="tabular-nums text-ink-muted">{Math.round(r.match_pct)}%</span></div>
                <Meter value={r.match_pct} className="mt-1" />
              </div>
            )) : <p className="mt-2 text-sm text-ink-muted">Appears after your resume is analysed.</p>}
          </Card>
          <Card className="p-5 text-sm">
            <h2 className="font-serif text-lg font-semibold">Practice and interviews</h2>
            <p className="mt-2 text-ink-muted">{d.saved_questions} saved question(s).</p>
            <p className="mt-1 text-ink-muted">{d.last_interview ? <>Last mock interview: <b className="text-ink">{d.last_interview.overall}/5</b> ({d.last_interview.type}).</> : "No mock interview yet."}</p>
            {d.readiness.next.length > 0 && <ul className="mt-3 list-disc space-y-1 pl-4 text-ink-soft">{d.readiness.next.map((n) => <li key={n}>{n}</li>)}</ul>}
          </Card>
        </div>
      </div>
    </>
  );
}
