"use client";
import { useState } from "react";
import { ChevronDown, Plus, Trash2 } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Basis, Skill } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Button, ButtonLink, Card, Empty, ErrorNote, Notice, PageSkeleton } from "@/components/ui";
import { LEVEL_INFO, LevelBadge } from "@/components/labels";

type Data = { basis: Basis; counts: Record<string, number>; total: number; groups: { category: string; skills: Skill[] }[] };

function SkillRow({ s, onRemove }: { s: Skill; onRemove: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="border-b border-line last:border-0">
      <button onClick={() => setOpen(!open)} aria-expanded={open} className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-paper/60">
        <span className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium">{s.name}</span>
          <LevelBadge level={s.level} />
          <span className="text-xs text-ink-muted">{s.confidence} confidence</span>
        </span>
        <ChevronDown className={clsx("h-4 w-4 shrink-0 text-ink-faint transition-transform", open && "rotate-180")} aria-hidden />
      </button>
      {open && (
        <div className="space-y-3 px-4 pb-4">
          <ul className="space-y-2">
            {s.evidence.map((e, i) => (
              <li key={i} className="rounded-md border border-line bg-paper/60 px-3 py-2 text-[13px]">
                <p className="text-xs font-medium text-ink-muted">{e.source}</p>
                <p className="mt-0.5 text-ink-soft">&ldquo;{e.quote}&rdquo;</p>
              </li>
            ))}
          </ul>
          {s.needs_validation && <p className="text-[13px] text-ink-soft"><b className="font-medium">Still to show:</b> {s.needs_validation}</p>}
          <p className="text-[13px] text-ink-soft"><b className="font-medium">Next step:</b> {s.next_step}</p>
          <button onClick={onRemove} className="inline-flex items-center gap-1 text-xs text-ink-muted hover:text-danger"><Trash2 className="h-3.5 w-3.5" /> Remove this skill</button>
        </div>
      )}
    </li>
  );
}

export default function SkillsPage() {
  const { data, error, loading, reload, setData } = useApi<Data>("/api/skills");
  const [name, setName] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  if (loading && !data) return <PageSkeleton />;
  if (error) return <ErrorNote message={error.message} onRetry={reload} />;
  if (!data) return null;
  if (!data.total) return (<><PageHeader eyebrow="Skill intelligence" title="Your skills" /><Empty title="No skills yet" action={<ButtonLink href="/resume/">Upload resume</ButtonLink>}>We build this from your resume.</Empty></>);

  const add = async () => {
    if (!name.trim()) return;
    try { await api("/api/skills", { body: { name } }); setName(""); setMsg(null); reload(); } catch (e) { setMsg(e instanceof Error ? e.message : String(e)); }
  };
  const remove = async (id: number) => { await api(`/api/skills/${id}`, { method: "DELETE" }); reload(); };
  const rebuild = async () => setData(await api<Data>("/api/skills/rebuild", { method: "POST" }));

  return (
    <>
      <PageHeader eyebrow="Skill intelligence" title="How strong is the evidence for each skill?"
        actions={<Button variant="secondary" size="sm" onClick={rebuild}>Recalculate</Button>}>
        Listing a skill is a claim. A project that uses it is evidence. Answering questions on it validates it. We keep these apart so you know what an interviewer is likely to probe.
      </PageHeader>
      <Notice tone={data.basis.limited_info ? "blue" : "green"} className="mb-5">{data.basis.note}</Notice>
      {data.basis.unavailable.map((u) => <Notice key={u.kind} tone="amber" className="mb-3">{u.kind}: {u.note}</Notice>)}

      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        {(["validated", "project", "claimed", "inferred"] as const).map((lv) => (
          <Card key={lv} className="p-4">
            <div className="flex items-center justify-between"><LevelBadge level={lv} /><span className="font-serif text-2xl font-semibold">{data.counts[lv]}</span></div>
            <p className="mt-2 text-xs leading-snug text-ink-muted">{LEVEL_INFO[lv].help}</p>
          </Card>
        ))}
      </div>

      <div className="grid items-start gap-5 lg:grid-cols-2">
        {data.groups.map((g) => (
          <Card key={g.category} className="overflow-hidden">
            <div className="flex items-center justify-between border-b border-line bg-paper/50 px-4 py-2.5">
              <h2 className="text-sm font-semibold">{g.category}</h2><Badge>{g.skills.length}</Badge>
            </div>
            <ul>{g.skills.map((s) => <SkillRow key={s.id} s={s} onRemove={() => remove(s.id)} />)}</ul>
          </Card>
        ))}
      </div>

      <Card className="mt-6 flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
        <p className="text-sm text-ink-soft sm:flex-1">Missing a skill? Add it. It will count as claimed until a project or practice backs it up.</p>
        <div className="flex gap-2">
          <input className="input w-48" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Docker" aria-label="Skill name" onKeyDown={(e) => e.key === "Enter" && add()} />
          <Button variant="secondary" onClick={add}><Plus className="h-4 w-4" /> Add</Button>
        </div>
      </Card>
      {msg && <div className="mt-2"><ErrorNote message={msg} /></div>}
    </>
  );
}
