"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { ArrowLeft, ExternalLink } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { CompanyDetail } from "@/lib/types";
import { useShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Button, ButtonLink, Card, ErrorNote, Notice, PageSkeleton } from "@/components/ui";
import { SourceLabel, SourceLink } from "@/components/labels";
import { StageCard } from "@/components/company/StageCard";

function CompanyView() {
  const slug = useSearchParams().get("slug") ?? "";
  const router = useRouter();
  const { refresh } = useShell();
  const { data: c, error, loading, setData } = useApi<CompanyDetail>(slug ? `/api/companies/${slug}` : null);
  const [roleKey, setRoleKey] = useState<string>("");
  const [busy, setBusy] = useState(false);
  if (!slug) return <ErrorNote message="No company selected." />;
  if (loading && !c) return <PageSkeleton />;
  if (error) return <ErrorNote message={error.message} />;
  if (!c) return null;

  const choose = async () => {
    setBusy(true);
    await api(`/api/companies/${slug}/select`, { body: { role_key: roleKey || c.roles[0]?.role_key || null } });
    setData({ ...c, selected: true });
    refresh();
    setBusy(false);
  };
  const overviewSrc = c.overview_source ? c.sources[c.overview_source] : null;

  return (
    <>
      <Link href="/companies/" className="mb-3 inline-flex items-center gap-1 text-sm text-ink-muted hover:text-ink"><ArrowLeft className="h-4 w-4" /> All companies</Link>
      <PageHeader eyebrow="Hiring guide" title={c.name}
        actions={c.selected ? <ButtonLink href="/gaps/">See my gaps for {c.name}</ButtonLink> : (
          <div className="flex flex-wrap gap-2">
            {c.roles.length > 1 && (
              <select className="input h-10 w-auto" value={roleKey} onChange={(e) => setRoleKey(e.target.value)} aria-label="Role to prepare for">
                {c.roles.map((r) => <option key={r.id} value={r.role_key}>{r.title}</option>)}
              </select>
            )}
            <Button busy={busy} onClick={choose}>Prepare for {c.name}</Button>
          </div>
        )}>
        <p>{c.overview}</p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <SourceLink src={overviewSrc} />
          {c.careers_url && <a href={c.careers_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-accent hover:underline">Official careers page <ExternalLink className="h-3 w-3" /></a>}
        </div>
      </PageHeader>
      {c.selected && <Notice tone="green" className="mb-4">{c.name} is your target company. Your gap analysis and plan will include these stages. <button className="underline" onClick={() => router.push("/roadmap/")}>Open roadmap</button></Notice>}
      <Notice tone="amber" className="mb-6">{c.variation_note || "Hiring processes vary by role, location, year and college."}</Notice>

      <h2 className="mb-3 font-serif text-xl font-semibold">Roles</h2>
      <div className="mb-8 grid gap-4 md:grid-cols-2">
        {c.roles.map((r) => (
          <Card key={r.id} className="p-5">
            <h3 className="font-semibold">{r.title}</h3>
            <p className="mt-1 text-sm text-ink-muted">{r.description}</p>
            {r.skills.length > 0 && <div className="mt-3 flex flex-wrap gap-1">{r.skills.map((s) => <Badge key={s}>{s}</Badge>)}</div>}
            {[["Eligibility", r.eligibility], ["Compensation", r.compensation]].map(([label, lines]) => (lines as typeof r.eligibility).length > 0 && (
              <div key={label as string} className="mt-3">
                <p className="label-sm mb-1">{label as string}</p>
                {(lines as typeof r.eligibility).map((l, i) => (
                  <div key={i} className="flex flex-col gap-0.5 py-0.5 text-sm sm:flex-row sm:justify-between sm:gap-3"><span>{l.text}</span><SourceLink src={c.sources[l.source]} compact /></div>
                ))}
              </div>
            ))}
          </Card>
        ))}
      </div>

      <div className="mb-3 flex items-end justify-between">
        <h2 className="font-serif text-xl font-semibold">Recruitment stages</h2>
        <Link href={`/practice/?company=${c.slug}`} className="text-sm text-accent hover:underline">{c.question_count} practice questions</Link>
      </div>
      {c.stages.length ? (
        <ol>{c.stages.map((s, i) => <StageCard key={s.id} stage={s} sources={c.sources} slug={c.slug} last={i === c.stages.length - 1} />)}</ol>
      ) : <Notice>We have no verified stage information for {c.name}. Use a general role-based plan instead.</Notice>}

      <h2 className="mb-3 mt-4 font-serif text-xl font-semibold">Sources ({Object.keys(c.sources).length})</h2>
      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead><tr className="border-b border-line text-xs text-ink-muted"><th className="px-4 py-2 font-medium">Source</th><th className="px-4 py-2 font-medium">Label</th><th className="px-4 py-2 font-medium">Page date</th><th className="px-4 py-2 font-medium">Checked</th></tr></thead>
          <tbody>
            {Object.entries(c.sources).map(([k, s]) => (
              <tr key={k} className="border-b border-line last:border-0">
                <td className="px-4 py-2.5"><a href={s.url} target="_blank" rel="noreferrer" className="text-ink hover:text-accent">{s.title || s.url}</a><p className="text-xs text-ink-muted">{s.publisher}</p></td>
                <td className="px-4 py-2.5"><SourceLabel label={s.label} /></td>
                <td className="px-4 py-2.5 text-ink-muted">{s.date ?? "Not shown"}</td>
                <td className="px-4 py-2.5 text-ink-muted">{s.accessed}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}

export default function Page() {
  return <Suspense fallback={<PageSkeleton />}><CompanyView /></Suspense>;
}
