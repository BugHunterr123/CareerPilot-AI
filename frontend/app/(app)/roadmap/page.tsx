"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAction, useApi } from "@/lib/hooks";
import type { Profile, Roadmap, Task } from "@/lib/types";
import { useShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Button, Card, ErrorNote, Field, Meter, Notice, PageSkeleton } from "@/components/ui";
import { TaskRow } from "@/components/roadmap/TaskRow";

export default function RoadmapPage() {
  const rm = useApi<Roadmap>("/api/roadmap");
  const prof = useApi<{ profile: Profile }>("/api/profile");
  const { refresh } = useShell();
  const act = useAction();
  const [show, setShow] = useState<"all" | "todo" | "done">("all");
  const [edit, setEdit] = useState(false);
  const [opts, setOpts] = useState({ weekly_hours: "8", target_date: "", use_target_company: true });

  useEffect(() => {
    const p = prof.data?.profile;
    if (p) setOpts((o) => ({ ...o, weekly_hours: String(p.weekly_hours ?? 8), target_date: p.target_date ?? "" }));
  }, [prof.data]);

  if ((rm.loading && !rm.data) || prof.loading) return <PageSkeleton />;
  const p = prof.data?.profile;
  const generate = () => act.run(async () => {
    const r = await api<Roadmap>("/api/roadmap/generate", { body: { weekly_hours: Number(opts.weekly_hours) || 8, target_date: opts.target_date || null, use_target_company: opts.use_target_company } });
    rm.setData(r); setEdit(false); refresh();
  });
  const setTask = (t: Task) => { if (rm.data) { rm.setData({ ...rm.data, tasks: rm.data.tasks.map((x) => (x.id === t.id ? t : x)), done: rm.data.tasks.filter((x) => (x.id === t.id ? t : x).status === "done").length }); refresh(); } };

  const settings = (
    <Card className="mb-6 p-5">
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Hours per week you can give" htmlFor="hours"><input id="hours" type="number" min={1} max={60} className="input" value={opts.weekly_hours} onChange={(e) => setOpts({ ...opts, weekly_hours: e.target.value })} /></Field>
        <Field label="Test or interview date" htmlFor="date" optional hint="Leave empty for a 4-week plan."><input id="date" type="date" className="input" value={opts.target_date} onChange={(e) => setOpts({ ...opts, target_date: e.target.value })} /></Field>
        <div className="flex items-end"><Button busy={act.busy} onClick={generate} className="w-full sm:w-auto">{rm.data ? "Regenerate plan" : "Generate my plan"}</Button></div>
      </div>
      <label className="mt-3 flex items-center gap-2 text-sm text-ink-soft">
        <input type="checkbox" className="accent-[#1F5C46]" checked={opts.use_target_company} onChange={(e) => setOpts({ ...opts, use_target_company: e.target.checked })} />
        Include my target company&apos;s hiring stages{p?.target_company_id ? "" : " (none selected yet)"}
      </label>
      <p className="mt-2 text-xs text-ink-muted">Role: {p?.target_role_title ?? "Software Developer (default, change it in Career Recommendations)"}. Finished tasks are kept out of a regenerated plan.</p>
      <div className="mt-3"><ErrorNote message={act.error} /></div>
    </Card>
  );

  if (!rm.data) return (<><PageHeader eyebrow="Preparation roadmap" title="Build your preparation plan">We order your gaps by priority, add your target company&apos;s stages, and spread the work over the time you have. One rest day a week is kept free.</PageHeader>{settings}</>);
  const r = rm.data;
  const tasks = r.tasks.filter((t) => show === "all" || (show === "done" ? t.status === "done" : t.status !== "done"));
  const weeks = Array.from(new Set(tasks.map((t) => t.week)));
  return (
    <>
      <PageHeader eyebrow="Preparation roadmap" title={`${r.role_title}${r.company_name ? ` · ${r.company_name}` : ""}`}
        actions={<Button variant="secondary" size="sm" onClick={() => setEdit(!edit)}>{edit ? "Close" : "Change schedule"}</Button>}>
        <span className="flex flex-wrap items-center gap-2">
          <Badge tone={r.plan_type.startsWith("Company") ? "green" : "neutral"}>{r.plan_type}</Badge>
          <span>{new Date(r.start_date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })} to {r.target_date && new Date(r.target_date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })} · {r.weekly_hours} h/week · generated in {r.generation_ms} ms</span>
        </span>
      </PageHeader>
      {edit && settings}
      {r.notes.map((n) => <Notice key={n} tone="amber" className="mb-3">{n}</Notice>)}
      <div className="mb-5 flex flex-wrap items-center gap-4">
        <div className="flex min-w-[220px] flex-1 items-center gap-3 text-sm"><Meter value={(100 * r.done) / Math.max(1, r.total)} /><span className="shrink-0 tabular-nums text-ink-muted">{r.done} of {r.total} done</span></div>
        <div className="flex rounded-md border border-line bg-white p-0.5 text-sm" role="tablist" aria-label="Filter tasks">
          {(["all", "todo", "done"] as const).map((k) => <button key={k} role="tab" aria-selected={show === k} onClick={() => setShow(k)} className={`rounded px-3 py-1 ${show === k ? "bg-accent-soft font-medium text-accent" : "text-ink-muted"}`}>{k === "all" ? "All" : k === "todo" ? "To do" : "Done"}</button>)}
        </div>
      </div>
      {weeks.map((w) => (
        <section key={w} className="mb-5">
          <h2 className="label-sm mb-2">Week {w}</h2>
          <Card className="overflow-hidden"><ul>{tasks.filter((t) => t.week === w).map((t) => <TaskRow key={t.id} t={t} onChange={setTask} />)}</ul></Card>
        </section>
      ))}
      {!tasks.length && <p className="text-sm text-ink-muted">Nothing here.</p>}
    </>
  );
}
