"use client";
import { useState } from "react";
import { Check, ExternalLink } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Basis, RoleRec } from "@/lib/types";
import { useShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Button, ButtonLink, Card, Empty, ErrorNote, Meter, Notice, PageSkeleton } from "@/components/ui";

type Data = { basis: Basis; selected: string | null; method: string; roles: RoleRec[] };

function Chips({ items, tone }: { items: string[]; tone: "green" | "amber" | "red" }) {
  if (!items.length) return <span className="text-xs text-ink-faint">None</span>;
  return <span className="flex flex-wrap gap-1">{items.map((s) => <Badge key={s} tone={tone}>{s}</Badge>)}</span>;
}

function RoleCard({ r, selected, onSelect, compare, onCompare }: { r: RoleRec; selected: boolean; onSelect: () => void; compare: boolean; onCompare: () => void }) {
  return (
    <Card className={clsx("p-5", selected && "border-accent ring-1 ring-accent")}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-serif text-xl font-semibold">{r.title}</h2>
          <p className="mt-0.5 text-sm text-ink-muted">{r.summary}</p>
        </div>
        <div className="text-right">
          <p className="font-serif text-3xl font-semibold leading-none tabular-nums">{Math.round(r.match_pct)}%</p>
          <p className="mt-1 text-[11px] text-ink-muted">{r.formula.earned} of {r.formula.total} weight{r.formula.interest_bonus ? " + interest" : ""}</p>
        </div>
      </div>
      <Meter value={r.match_pct} className="mt-3" />
      <ul className="mt-4 space-y-1 text-sm text-ink-soft">{r.why.map((w) => <li key={w}>{w}</li>)}</ul>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <div><dt className="label-sm mb-1">Already shown</dt><dd><Chips items={r.relevant.map((x) => x.skill)} tone="green" /></dd></div>
        <div><dt className="label-sm mb-1">Listed, not shown</dt><dd><Chips items={r.partial.map((x) => x.skill)} tone="amber" /></dd></div>
        <div><dt className="label-sm mb-1">Not demonstrated yet</dt><dd><Chips items={r.missing.map((x) => x.skill)} tone="red" /></dd></div>
      </dl>
      <div className="mt-4 grid gap-4 border-t border-line pt-4 text-sm sm:grid-cols-2">
        <div>
          <p className="label-sm mb-1">Project that would help</p>
          <ul className="list-disc space-y-1 pl-4 text-ink-soft">{r.projects.map((p) => <li key={p}>{p}</li>)}</ul>
        </div>
        <div>
          <p className="label-sm mb-1">Start with</p>
          {r.resources.length ? r.resources.map((x) => (
            <a key={x.url} href={x.url} target="_blank" rel="noreferrer" className="flex items-center gap-1 py-0.5 text-accent hover:underline">{x.title} <span className="text-ink-faint">({x.provider})</span><ExternalLink className="h-3 w-3" /></a>
          )) : <p className="text-ink-muted">You already cover the core skills. Practise and interview.</p>}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button size="sm" variant={selected ? "secondary" : "primary"} onClick={onSelect} disabled={selected}>
          {selected ? <><Check className="h-4 w-4" /> Your target role</> : "Set as my target role"}
        </Button>
        <Button size="sm" variant="ghost" onClick={onCompare} aria-pressed={compare}>{compare ? "Remove from compare" : "Compare"}</Button>
      </div>
    </Card>
  );
}

export default function CareersPage() {
  const { data, error, loading, reload, setData } = useApi<Data>("/api/careers");
  const { refresh } = useShell();
  const [cmp, setCmp] = useState<string[]>([]);
  const [all, setAll] = useState(false);
  if (loading && !data) return <PageSkeleton />;
  if (error) return <ErrorNote message={error.message} onRetry={reload} />;
  if (!data) return null;
  if (!data.roles.length) return (<><PageHeader eyebrow="Career recommendations" title="Roles that fit you" /><Empty title="Nothing to recommend yet" action={<ButtonLink href="/resume/">Upload resume</ButtonLink>}>Recommendations come from the skills in your resume.</Empty></>);
  const select = async (key: string) => { await api("/api/careers/select", { body: { role_key: key } }); setData({ ...data, selected: key }); refresh(); };
  const toggle = (k: string) => setCmp(cmp.includes(k) ? cmp.filter((x) => x !== k) : [...cmp, k].slice(-3));
  const shown = all ? data.roles : data.roles.slice(0, 4);
  const compared = data.roles.filter((r) => cmp.includes(r.role_key));
  return (
    <>
      <PageHeader eyebrow="Career recommendations" title="Roles that fit your current evidence">
        These are suggestions, not limits. Pick any role you want to aim for; the gap analysis will tell you what it needs.
      </PageHeader>
      <Notice tone="blue" className="mb-3">{data.basis.note}</Notice>
      <details className="mb-6 rounded-md border border-line bg-white px-4 py-3 text-sm">
        <summary className="cursor-pointer font-medium">How the match % is calculated</summary>
        <p className="mt-2 leading-relaxed text-ink-soft">{data.method}</p>
      </details>
      {compared.length > 1 && (
        <Card className="mb-6 overflow-x-auto p-0">
          <table className="w-full min-w-[560px] text-sm">
            <caption className="px-4 pt-3 text-left font-serif text-lg font-semibold">Side by side</caption>
            <thead><tr className="border-b border-line text-left text-xs text-ink-muted"><th className="px-4 py-2 font-medium">&nbsp;</th>{compared.map((r) => <th key={r.role_key} className="px-4 py-2 font-medium">{r.title}</th>)}</tr></thead>
            <tbody>
              <tr className="border-b border-line"><td className="px-4 py-2 text-ink-muted">Match</td>{compared.map((r) => <td key={r.role_key} className="px-4 py-2 font-medium">{Math.round(r.match_pct)}%</td>)}</tr>
              <tr className="border-b border-line"><td className="px-4 py-2 text-ink-muted">Shown</td>{compared.map((r) => <td key={r.role_key} className="px-4 py-2">{r.relevant.length}</td>)}</tr>
              <tr className="border-b border-line"><td className="px-4 py-2 text-ink-muted">Still missing</td>{compared.map((r) => <td key={r.role_key} className="px-4 py-2">{r.missing.map((m) => m.skill).join(", ") || "None"}</td>)}</tr>
              <tr><td className="px-4 py-2 text-ink-muted">Learn first</td>{compared.map((r) => <td key={r.role_key} className="px-4 py-2">{r.learn.slice(0, 3).join(", ")}</td>)}</tr>
            </tbody>
          </table>
        </Card>
      )}
      <div className="grid gap-5 xl:grid-cols-2">
        {shown.map((r) => <RoleCard key={r.role_key} r={r} selected={data.selected === r.role_key} onSelect={() => select(r.role_key)} compare={cmp.includes(r.role_key)} onCompare={() => toggle(r.role_key)} />)}
      </div>
      {!all && data.roles.length > 4 && <div className="mt-5 text-center"><Button variant="secondary" onClick={() => setAll(true)}>Show all {data.roles.length} roles</Button></div>}
    </>
  );
}
