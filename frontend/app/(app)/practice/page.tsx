"use client";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { Search, Timer } from "lucide-react";
import { useApi } from "@/lib/hooks";
import type { Question } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Button, ButtonLink, Card, Empty, ErrorNote, PageSkeleton, Skeleton } from "@/components/ui";
import { QuestionCard } from "@/components/practice/QuestionCard";

type Count = { value: string; count: number };
type Facets = { subjects: string[]; subject_counts: Count[]; types: string[]; difficulty_counts: Count[]; label_counts: Count[]; total: number;
  companies: { slug: string; name: string; id: number }[]; mine: { attempts: number; correct: number; saved: number } };
type Page = { total: number; page: number; page_size: number; items: Question[] };
const TYPE_NAMES: Record<string, string> = { mcq: "MCQ", coding: "Coding", sql: "SQL", short: "Short answer", hr: "HR" };
const EMPTY = { q: "", company: "", subject: "", qtype: "", difficulty: "", label: "", saved: false, incorrect: false };

function Practice() {
  const sp = useSearchParams();
  const single = sp.get("q");
  const [f, setF] = useState({ ...EMPTY, company: sp.get("company") ?? "", subject: sp.get("subject") ?? "", qtype: sp.get("qtype") ?? "" });
  const [lang, setLang] = useState("python");
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  // Facets depend on company + type, so the Subject / Difficulty / Source lists only offer values that exist.
  const facets = useApi<Facets>(`/api/questions/facets?company=${encodeURIComponent(f.company)}&qtype=${encodeURIComponent(f.qtype)}`);
  const one = useApi<Question>(single ? `/api/questions/${single}` : null);

  useEffect(() => {  // a roadmap task links here with company_id; translate it to the slug filter
    const cid = sp.get("company_id");
    const c = cid && facets.data?.companies.find((x) => String(x.id) === cid);
    if (c) setF((s) => ({ ...s, company: c.slug }));
  }, [sp, facets.data]);

  useEffect(() => {  // drop a subject/difficulty/source that no longer exists for the new company or type
    const d = facets.data;
    if (!d) return;
    setF((s) => ({ ...s,
      subject: s.subject && !d.subject_counts.some((x) => x.value === s.subject) ? "" : s.subject,
      difficulty: s.difficulty && !d.difficulty_counts.some((x) => x.value === s.difficulty) ? "" : s.difficulty,
      label: s.label && !d.label_counts.some((x) => x.value === s.label) ? "" : s.label }));
  }, [facets.data]);

  const path = useMemo(() => {
    const p = new URLSearchParams();
    Object.entries({ ...f, q: search }).forEach(([k, v]) => { if (v) p.set(k, String(v)); });
    p.set("page", String(page));
    return `/api/questions?${p}`;
  }, [f, search, page]);
  const list = useApi<Page>(single ? null : path);
  const set = (k: keyof typeof f, v: string | boolean) => { setF({ ...f, [k]: v }); setPage(1); };
  const m = facets.data?.mine;

  const select = (k: "company" | "subject" | "qtype" | "difficulty" | "label", label: string, options: { v: string; t: string }[]) => (
    <label className="block"><span className="label-sm mb-1 block">{label}</span>
      <select className="input h-10 py-1 text-[13.5px]" value={f[k]} onChange={(e) => set(k, e.target.value)} aria-label={label}>
        <option value="">All</option>{options.map((o) => <option key={o.v} value={o.v}>{o.t}</option>)}
      </select></label>
  );
  const withCount = (c: Count[] = []) => c.map((x) => ({ v: x.value, t: `${x.value} (${x.count})` }));

  if (single) {
    return (
      <>
        <PageHeader eyebrow="Practice questions" title="Question" actions={<ButtonLink href="/practice/" variant="secondary">All questions</ButtonLink>} />
        <ErrorNote message={one.error?.message} />
        {one.data ? <QuestionCard q={one.data} n={1} lang={lang} /> : <Skeleton className="h-48" />}
      </>
    );
  }
  return (
    <>
      <PageHeader eyebrow="Practice questions" title="Practise, then check"
        actions={<ButtonLink href="/practice/test/"><Timer className="h-4 w-4" aria-hidden />Start a timed test</ButtonLink>}>
        Candidate-reported questions were reported by students for that company. AI practice questions were written for CareerPilot on reported topics and tested. Coding problems run in a real Python runner.
      </PageHeader>
      {m && (
        <div className="mb-6 grid grid-cols-3 gap-3 sm:max-w-lg">
          {[["Attempts", m.attempts], ["Accuracy", m.attempts ? `${Math.round((100 * m.correct) / m.attempts)}%` : "-"], ["Saved", m.saved]].map(([k, v]) => (
            <Card key={k as string} className="px-4 py-3"><p className="text-xs text-ink-muted">{k}</p><p className="font-serif text-xl font-semibold">{v}</p></Card>
          ))}
        </div>
      )}
      <Card className="mb-6 space-y-4 p-5">
        <form className="relative" onSubmit={(e) => { e.preventDefault(); setSearch(f.q); setPage(1); }}>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" aria-hidden />
          <input className="input pl-9" placeholder="Search questions, then press Enter" value={f.q} onChange={(e) => setF({ ...f, q: e.target.value })} aria-label="Search questions" />
        </form>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
          {select("company", "Company", [{ v: "general", t: "General (no company)" }, ...(facets.data?.companies ?? []).map((c) => ({ v: c.slug, t: c.name }))])}
          {select("qtype", "Type", (facets.data?.types ?? []).map((s) => ({ v: s, t: TYPE_NAMES[s] ?? s })))}
          {select("difficulty", "Difficulty", withCount(facets.data?.difficulty_counts))}
          {select("subject", "Subject", withCount(facets.data?.subject_counts))}
          {select("label", "Source", withCount(facets.data?.label_counts))}
          <label className="block"><span className="label-sm mb-1 block">Solution language</span>
            <select className="input h-10 py-1 text-[13.5px]" value={lang} onChange={(e) => setLang(e.target.value)} aria-label="Solution language">
              <option value="python">Python</option><option value="java">Java</option><option value="cpp">C++</option>
            </select></label>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <label className="flex items-center gap-2"><input type="checkbox" className="accent-[#1F5C46]" checked={f.saved} onChange={(e) => set("saved", e.target.checked)} /> Saved only</label>
          <label className="flex items-center gap-2"><input type="checkbox" className="accent-[#1F5C46]" checked={f.incorrect} onChange={(e) => set("incorrect", e.target.checked)} /> Got wrong last time</label>
          {JSON.stringify({ ...f, q: "" }) !== JSON.stringify(EMPTY) && <button className="text-accent hover:underline" onClick={() => { setF(EMPTY); setSearch(""); setPage(1); }}>Clear filters</button>}
          <span className="ml-auto text-xs text-ink-muted">Language only changes which solution is shown; coding problems are the same in every language.</span>
        </div>
      </Card>
      <ErrorNote message={list.error?.message} onRetry={list.reload} />
      {list.loading && !list.data ? <div className="space-y-4">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-40" />)}</div> : list.data && (
        list.data.items.length ? (
          <>
            <p className="mb-3 text-sm text-ink-muted" data-testid="question-total">{list.data.total} question(s)</p>
            <div className="space-y-5">{list.data.items.map((q, i) => <QuestionCard key={q.id} q={q} n={(page - 1) * list.data!.page_size + i + 1} lang={lang} />)}</div>
            <div className="mt-8 flex items-center justify-between">
              <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
              <span className="text-sm text-ink-muted">Page {page} of {Math.max(1, Math.ceil(list.data.total / list.data.page_size))}</span>
              <Button variant="secondary" size="sm" disabled={page * list.data.page_size >= list.data.total} onClick={() => setPage(page + 1)}>Next</Button>
            </div>
          </>
        ) : <Empty title="No questions match these filters" action={<Button variant="secondary" size="sm" onClick={() => { setF(EMPTY); setSearch(""); }}>Clear filters</Button>}>{f.incorrect ? "Nothing marked wrong yet. Nice." : "Try removing a filter."}</Empty>
      )}
    </>
  );
}

export default function Page() {
  return <Suspense fallback={<PageSkeleton />}><Practice /></Suspense>;
}
