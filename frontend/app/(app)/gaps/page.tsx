"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import clsx from "clsx";
import { ExternalLink } from "lucide-react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { CompanySummary, GapItem, GapReport, GapSource, Profile } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Badge, ButtonLink, Card, ErrorNote, Field, PageSkeleton } from "@/components/ui";
import { PriorityBadge, SourceLabel } from "@/components/labels";

const STATUS = { shown: { tone: "green", text: "Shown" }, partial: { tone: "amber", text: "Partly" }, missing: { tone: "red", text: "Missing" } } as const;
const ORIGIN = { role: { tone: "neutral", text: "Role" }, company: { tone: "blue", text: "Company stage" }, both: { tone: "green", text: "Role + company" }, jd: { tone: "outline", text: "Job description" } } as const;

function Sources({ list }: { list: GapSource[] }) {
  if (!list.length) return null;
  return (
    <span className="inline-flex flex-wrap gap-x-3 gap-y-1">
      {list.slice(0, 3).map((s) => (
        <a key={s.url} href={s.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-ink-muted hover:text-accent">
          {s.publisher || s.title}{s.date ? ` · ${s.date}` : ""}<ExternalLink className="h-3 w-3" aria-hidden /><span className="sr-only">(opens in a new tab)</span>
        </a>
      ))}
    </span>
  );
}

function GapRow({ it }: { it: GapItem }) {
  const [open, setOpen] = useState(false);
  const topics = Array.from(new Set(it.company_topics.map((t) => t.topic))).filter((t) => t !== it.skill);
  return (
    <li className="border-b border-line last:border-0" data-testid="gap-row">
      <button className="grid w-full grid-cols-[28px_1fr_auto] items-center gap-3 px-5 py-3.5 text-left hover:bg-paper/60 sm:grid-cols-[28px_1.5fr_0.9fr_0.6fr_auto]" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="font-mono text-xs text-ink-faint">{it.order ?? "-"}</span>
        <span className="min-w-0">
          <span className="text-sm font-medium">{it.skill}</span>
          {topics.length > 0 && <span className="mt-0.5 block truncate text-xs text-ink-muted">{topics.slice(0, 4).join(" · ")}</span>}
        </span>
        <span className="hidden sm:block"><Badge tone={ORIGIN[it.origin].tone}>{ORIGIN[it.origin].text}</Badge></span>
        <span className="hidden sm:block"><Badge tone={STATUS[it.status].tone}>{STATUS[it.status].text}</Badge></span>
        <PriorityBadge p={it.priority} />
      </button>
      {open && (
        <div className="grid gap-5 px-5 pb-5 text-sm sm:pl-[60px] md:grid-cols-2">
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1.5 sm:hidden"><Badge tone={ORIGIN[it.origin].tone}>{ORIGIN[it.origin].text}</Badge><Badge tone={STATUS[it.status].tone}>{STATUS[it.status].text}</Badge></div>
            <p className="text-ink-soft">{it.why}</p>
            <p className="label-sm">Why this priority ({it.points} points)</p>
            <ul className="list-disc space-y-0.5 pl-4 text-ink-soft">{it.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
          </div>
          <div className="space-y-3">
            {it.company_topics.length > 0 && (
              <div>
                <p className="label-sm mb-1">From the company&apos;s hiring stages</p>
                <ul className="space-y-1.5">
                  {it.company_topics.map((t) => (
                    <li key={t.stage + t.topic} className="text-ink-soft">
                      <span className="font-medium text-ink">{t.topic}</span> <span className="text-ink-muted">· {t.stage}</span> <SourceLabel label={t.label} />
                      <div><Sources list={t.sources} /></div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {it.resources.length > 0 && <div><p className="label-sm mb-1">Learn</p>{it.resources.map((r) => <a key={r.url} href={r.url} target="_blank" rel="noreferrer" className="block text-accent hover:underline">{r.title} <span className="text-ink-faint">· {r.provider} · ~{r.minutes} min</span></a>)}</div>}
            {it.practice_subject && <Link href={`/practice/?subject=${encodeURIComponent(it.practice_subject)}`} className="inline-block text-accent hover:underline">Practise {it.practice_subject} questions</Link>}
          </div>
        </div>
      )}
    </li>
  );
}

export default function GapsPage() {
  const roles = useApi<{ role_key: string; title: string }[]>("/api/roles");
  const comps = useApi<{ companies: CompanySummary[] }>("/api/companies");
  const prof = useApi<{ profile: Profile }>("/api/profile");
  const [form, setForm] = useState({ role_key: "", company_id: "", job_description: "" });
  const [report, setReport] = useState<GapReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reqId = useRef(0);

  useEffect(() => {
    const p = prof.data?.profile;
    if (p && !form.role_key) setForm((f) => ({ ...f, role_key: p.target_role_key || "software_developer", company_id: p.target_company_id ? String(p.target_company_id) : "" }));
  }, [prof.data, form.role_key]);

  const run = useCallback(async (f: typeof form) => {
    const id = ++reqId.current; // only the newest request may update the page (no stale results)
    setBusy(true);
    setError(null);
    try {
      const r = await api<GapReport>("/api/gaps", { body: { role_key: f.role_key, company_id: f.company_id ? Number(f.company_id) : null, job_description: f.job_description } });
      if (id === reqId.current) setReport(r);
    } catch (e) {
      if (id === reqId.current) setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (id === reqId.current) setBusy(false);
    }
  }, []);

  // Re-run automatically whenever the role or company changes, so the result always matches the selection.
  useEffect(() => {
    if (!form.role_key) return;
    const t = setTimeout(() => run(form), 150);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.role_key, form.company_id, run]);

  if (roles.loading || prof.loading) return <PageSkeleton />;
  const s = report?.summary;
  const roleTitle = roles.data?.find((r) => r.role_key === form.role_key)?.title;
  const compName = comps.data?.companies.find((c) => String(c.id) === form.company_id)?.name;
  const stale = !!s && (s.role_key !== form.role_key || String(s.company_id ?? "") !== form.company_id);
  return (
    <>
      <PageHeader eyebrow="Skill gap analysis" title="What stands between you and the role?">
        Requirements come from two places: the skills the role needs, and the topics the company&apos;s hiring stages test (with sources). Change either and the list updates.
      </PageHeader>
      <Card className="mb-8 p-6">
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Target role" htmlFor="role"><select id="role" className="input" value={form.role_key} onChange={(e) => setForm({ ...form, role_key: e.target.value })}>{roles.data?.map((r) => <option key={r.role_key} value={r.role_key}>{r.title}</option>)}</select></Field>
          <Field label="Company" htmlFor="company" optional><select id="company" className="input" value={form.company_id} onChange={(e) => setForm({ ...form, company_id: e.target.value })}><option value="">No specific company</option>{comps.data?.companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
        </div>
        <details className="mt-4">
          <summary className="cursor-pointer text-sm font-medium text-ink-soft">Add a job description (optional)</summary>
          <textarea className="input mt-2 min-h-[110px]" value={form.job_description} onChange={(e) => setForm({ ...form, job_description: e.target.value })} placeholder="Paste the JD from your placement portal. Skills it mentions are added to the requirements." aria-label="Job description" />
          <button className="mt-2 text-sm font-medium text-accent hover:underline" onClick={() => run(form)}>Apply job description</button>
        </details>
        <div className="mt-3"><ErrorNote message={error} onRetry={() => run(form)} /></div>
      </Card>
      {s && report ? (
        <div className={clsx("transition-opacity", (busy || stale) && "opacity-50")} aria-busy={busy}>
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-serif text-2xl font-semibold" data-testid="gap-title">{s.role}{s.company ? ` at ${s.company}` : ""}</h2>
              <p className="mt-1 text-sm text-ink-muted">
                {busy || stale ? `Updating for ${roleTitle ?? ""}${compName ? ` at ${compName}` : ""}…` :
                  `${s.total} requirements: ${s.from_role} from the role, ${s.from_company} from ${s.company ?? "the company"}'s stages, ${s.from_both} from both. ${s.shown} shown, ${s.partial} partly, ${s.missing} missing.`}
              </p>
            </div>
            <ButtonLink href="/roadmap/">Turn this into a plan</ButtonLink>
          </div>
          <div className="mb-6 flex h-2.5 overflow-hidden rounded-full" aria-hidden>
            {(["shown", "partial", "missing"] as const).map((k) => <div key={k} className={clsx(k === "shown" ? "bg-accent" : k === "partial" ? "bg-amber" : "bg-danger/70")} style={{ width: `${(100 * s[k]) / Math.max(1, s.total)}%` }} />)}
          </div>
          <div className="grid gap-6 xl:grid-cols-[1fr_340px]">
            <div>
              <h3 className="mb-3 text-sm font-semibold">Priority order</h3>
              <Card className="overflow-hidden"><ul>{report.items.map((it) => <GapRow key={it.skill} it={it} />)}</ul></Card>
              <p className="mt-3 text-xs text-ink-muted">Priority formula: {s.formula}. High = 3+ points, medium = 1.5+, low = above 0.</p>
            </div>
            <div className="space-y-6">
              <Card className="p-5">
                <h3 className="text-sm font-semibold">What a {s.role} needs</h3>
                <p className="mt-1 text-xs text-ink-muted">CareerPilot&apos;s role skill matrix for entry-level roles.</p>
                <ul className="mt-3 flex flex-wrap gap-1.5">{s.role_requirements.map((r) => <li key={r.skill}><Badge tone={r.weight === 3 ? "green" : "neutral"} title={r.level}>{r.skill}</Badge></li>)}</ul>
              </Card>
              {s.company_stages.length > 0 ? (
                <Card className="p-5" data-testid="company-stages">
                  <h3 className="text-sm font-semibold">What {s.company}&apos;s hiring stages test</h3>
                  <ol className="mt-3 space-y-4">
                    {s.company_stages.map((st) => (
                      <li key={st.order}>
                        <p className="text-sm font-medium">{st.order}. {st.name} <SourceLabel label={st.label} /></p>
                        <p className="mt-1 text-xs leading-relaxed text-ink-soft">{st.topics.map((t) => t.topic).join(" · ")}</p>
                        <div className="mt-1"><Sources list={st.sources} /></div>
                      </li>
                    ))}
                  </ol>
                </Card>
              ) : <Card className="p-5 text-sm text-ink-muted">Pick a company to add its hiring-stage topics (aptitude, pseudocode, coding level, interview focus) to this list.</Card>}
            </div>
          </div>
        </div>
      ) : busy ? <PageSkeleton /> : null}
    </>
  );
}
