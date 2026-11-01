"use client";
import Link from "next/link";
import { useState } from "react";
import { Search } from "lucide-react";
import { useApi } from "@/lib/hooks";
import type { CompanySummary } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Card, Empty, ErrorNote, PageSkeleton } from "@/components/ui";
import { SourceLabel } from "@/components/labels";

export default function Companies() {
  const [q, setQ] = useState("");
  const { data, error, loading, reload } = useApi<{ selected_id: number | null; companies: CompanySummary[] }>("/api/companies");
  if (loading && !data) return <PageSkeleton />;
  if (error) return <ErrorNote message={error.message} onRetry={reload} />;
  if (!data) return null;
  const list = data.companies.filter((c) => !q.trim() || (c.name + " " + c.overview + " " + c.role_titles.join(" ")).toLowerCase().includes(q.toLowerCase()));
  return (
    <>
      <PageHeader eyebrow="Company explorer" title="Pick a company to prepare for">
        Each guide lists the hiring stages we could find, with a link and a trust label on every claim. Processes change by year and college, so treat them as a strong hint, not a promise.
      </PageHeader>
      <div className="relative mb-5 max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" aria-hidden />
        <input className="input pl-9" placeholder="Search companies or roles" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search companies" />
      </div>
      {list.length ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {list.map((c) => (
            <Link key={c.id} href={`/companies/view/?slug=${c.slug}`} className="group">
              <Card className="h-full p-5 transition-colors group-hover:border-ink-faint">
                <div className="flex items-start justify-between gap-2">
                  <h2 className="font-serif text-xl font-semibold group-hover:text-accent">{c.name}</h2>
                  {data.selected_id === c.id && <Badge tone="green">Your target</Badge>}
                </div>
                <p className="mt-1.5 line-clamp-2 text-sm text-ink-muted">{c.overview}</p>
                <p className="mt-3 text-xs text-ink-soft">{c.role_titles.slice(0, 2).join(" · ")}{c.role_titles.length > 2 ? ` +${c.role_titles.length - 2}` : ""}</p>
                <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-line pt-3 text-xs text-ink-muted">
                  <span>{c.stage_count} stages</span><span>{c.question_count} questions</span><span>{c.source_count} sources</span>
                  <span className="flex gap-1">{c.source_labels.map((l) => <SourceLabel key={l} label={l} />)}</span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      ) : <Empty title="No company matches that search">We do not have a guide for it yet. You can still build a general role-based plan from the Roadmap page.</Empty>}
    </>
  );
}
