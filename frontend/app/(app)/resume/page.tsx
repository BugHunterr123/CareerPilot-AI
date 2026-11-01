"use client";
import { ArrowRight, Download } from "lucide-react";
import { useState } from "react";
import { api, API_BASE } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Resume } from "@/lib/types";
import { useShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { ResumeDrop } from "@/components/ResumeDrop";
import { ReviewForm } from "@/components/resume/ReviewForm";
import { Badge, Button, ButtonLink, Card, ErrorNote, Notice, PageSkeleton } from "@/components/ui";

function ReportList({ title, items, tone }: { title: string; items: string[]; tone: "green" | "amber" | "neutral" }) {
  const dot = { green: "bg-accent", amber: "bg-amber", neutral: "bg-ink-faint" }[tone];
  return (
    <div>
      <h3 className="text-sm font-semibold">{title}</h3>
      {items.length ? (
        <ul className="mt-2 space-y-2">{items.map((s) => <li key={s} className="flex gap-2.5 text-sm leading-relaxed text-ink-soft"><span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${dot}`} />{s}</li>)}</ul>
      ) : <p className="mt-2 text-sm text-ink-muted">Nothing to note.</p>}
    </div>
  );
}

export default function ResumePage() {
  const { data, error, loading, setData } = useApi<Resume>("/api/resume");
  const { refresh, meta } = useShell();
  const [replace, setReplace] = useState(false);
  const done = (r: Resume) => { setData(r); setReplace(false); refresh(); };

  async function download() {
    const res = await fetch(`${API_BASE}/api/resume/file`, { credentials: "include" });
    const url = URL.createObjectURL(await res.blob());
    const a = document.createElement("a"); a.href = url; a.download = data?.filename ?? "resume"; a.click();
  }

  if (loading && !data) return <PageSkeleton />;
  if (error && error.status !== 404) return <ErrorNote message={error.message} />;
  if (!data || replace) {
    return (
      <>
        <PageHeader eyebrow="Resume analysis" title={replace ? "Upload a new version" : "Upload your resume"}>
          Your resume is the only required document. We read it, then you check and correct what we found.
        </PageHeader>
        <Card className="max-w-2xl p-6"><ResumeDrop onDone={done} maxMb={meta?.max_upload_mb ?? 5} /></Card>
        {replace && <Button variant="ghost" className="mt-3" onClick={() => setReplace(false)}>Cancel</Button>}
      </>
    );
  }
  const a = data.analysis;
  return (
    <>
      <PageHeader eyebrow="Resume analysis" title="What your resume shows"
        actions={<>
          <Button variant="secondary" size="sm" onClick={download}><Download className="h-4 w-4" /> Original</Button>
          <Button variant="secondary" size="sm" onClick={() => setReplace(true)}>Replace resume</Button>
        </>}>
        <span className="inline-flex flex-wrap items-center gap-2">
          <span>{data.filename}</span>
          <Badge tone={data.engine === "llm" ? "blue" : "neutral"}>{data.engine === "llm" ? "AI-assisted extraction, checked against your text" : "Read by rule-based parser"}</Badge>
          {data.reviewed ? <Badge tone="green">Reviewed by you</Badge> : <Badge tone="amber">Not reviewed yet</Badge>}
        </span>
      </PageHeader>

      {data.warnings.map((w) => <Notice key={w} tone="amber" className="mb-3">{w}</Notice>)}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="p-5"><ReportList title="Strengths" items={a.strengths} tone="green" /></Card>
        <Card className="p-5"><ReportList title="Missing or unclear" items={a.missing} tone="amber" /></Card>
        <Card className="p-5"><ReportList title="Suggestions" items={a.suggestions} tone="neutral" /></Card>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-white px-5 py-4">
        <p className="text-sm text-ink-soft">{a.skill_count} skills and {a.project_count} projects found. See how strong the evidence is for each skill, and which roles they point to.</p>
        <div className="flex gap-2">
          <ButtonLink href="/skills/" variant="secondary" size="sm">Skill evidence</ButtonLink>
          <ButtonLink href="/careers/" size="sm">Possible roles <ArrowRight className="h-4 w-4" /></ButtonLink>
        </div>
      </div>

      <div className="mt-6"><ReviewForm key={data.id} resume={data} onSaved={done} /></div>
    </>
  );
}
