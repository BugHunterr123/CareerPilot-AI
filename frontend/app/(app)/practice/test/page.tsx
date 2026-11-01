"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import clsx from "clsx";
import { Code2, ListChecks } from "lucide-react";
import { api } from "@/lib/api";
import { useAction, useApi } from "@/lib/hooks";
import type { CompanySummary, PracticeTest } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Button, Card, Empty, ErrorNote, Field } from "@/components/ui";

type Hist = { id: number; kind: string; company_name: string | null; difficulty: string; status: string; score: number | null; questions: number; answered: number; created_at: string };

export default function TestSetup() {
  const router = useRouter();
  const comps = useApi<{ companies: CompanySummary[] }>("/api/companies");
  const hist = useApi<Hist[]>("/api/tests");
  const [opt, setOpt] = useState({ kind: "coding", company_id: "", difficulty: "mixed", count: 3 });
  const act = useAction();
  const start = () => act.run(async () => {
    const t = await api<PracticeTest>("/api/tests", { body: { kind: opt.kind, company_id: opt.company_id ? Number(opt.company_id) : null, difficulty: opt.difficulty, count: opt.count } });
    router.push(`/practice/test/session/?id=${t.id}`);
  });
  const counts = opt.kind === "coding" ? [1, 2, 3, 4, 5] : [10, 15, 20, 30];
  return (
    <>
      <PageHeader eyebrow="Timed tests" title="Sit a practice test like the real one">
        Pick a company and difficulty. Coding questions run against hidden test cases on the server; MCQ answers are checked when you finish. Every answer is saved to your progress.
      </PageHeader>
      <Card className="mb-10 p-6">
        <p className="mb-2 text-sm font-medium">Test type</p>
        <div className="grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label="Test type">
          {[["coding", "Coding test", "Write Python, run it on test cases, get pass/fail per case", Code2], ["mcq", "Aptitude and MCQ test", "Quant, reasoning, pseudocode and CS fundamentals, timed", ListChecks]].map(([k, t, d, Icon]) => {
            const I = Icon as typeof Code2;
            return (
              <button key={k as string} role="radio" aria-checked={opt.kind === k} onClick={() => setOpt({ ...opt, kind: k as string, count: k === "coding" ? 3 : 15 })}
                className={clsx("flex items-start gap-3 rounded-md border px-4 py-3.5 text-left transition-colors", opt.kind === k ? "border-accent bg-accent-soft" : "border-line hover:bg-paper")}>
                <I className="mt-0.5 h-5 w-5 shrink-0 text-accent" aria-hidden /><span><span className="block text-sm font-medium">{t as string}</span><span className="block text-xs text-ink-muted">{d as string}</span></span>
              </button>
            );
          })}
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-4">
          <Field label="Company" htmlFor="tcomp"><select id="tcomp" className="input" value={opt.company_id} onChange={(e) => setOpt({ ...opt, company_id: e.target.value })}><option value="">Any company</option>{comps.data?.companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
          <Field label="Difficulty" htmlFor="tdiff"><select id="tdiff" className="input" value={opt.difficulty} onChange={(e) => setOpt({ ...opt, difficulty: e.target.value })}>{["mixed", "easy", "medium", "hard"].map((d) => <option key={d} value={d}>{d === "mixed" ? "Mixed (easy to hard)" : d}</option>)}</select></Field>
          <Field label="Questions" htmlFor="tcount"><select id="tcount" className="input" value={opt.count} onChange={(e) => setOpt({ ...opt, count: Number(e.target.value) })}>{counts.map((c) => <option key={c} value={c}>{c}</option>)}</select></Field>
          <div className="flex items-end"><Button busy={act.busy} onClick={start} className="w-full" data-testid="start-test">Start test</Button></div>
        </div>
        <p className="mt-3 text-xs text-ink-muted">Time: {opt.kind === "coding" ? "15 / 20 / 30 minutes per easy / medium / hard question" : "1 minute per question"}. The timer keeps running if you leave the page.</p>
        <div className="mt-3"><ErrorNote message={act.error} /></div>
      </Card>
      <h2 className="mb-3 font-serif text-xl font-semibold">Past tests</h2>
      {hist.data && hist.data.length ? (
        <Card className="overflow-hidden"><ul className="divide-y divide-line">
          {hist.data.map((h) => (
            <li key={h.id}><Link href={`/practice/test/session/?id=${h.id}`} className="flex items-center justify-between gap-3 px-5 py-3.5 hover:bg-paper/60">
              <span><span className="text-sm font-medium">{h.kind === "coding" ? "Coding" : "MCQ"} test · {h.company_name ?? "Any company"} · {h.difficulty}</span>
                <span className="block text-xs text-ink-muted">{new Date(h.created_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })} · {h.questions} questions</span></span>
              {h.status === "completed" ? <span className="font-serif text-lg font-semibold">{Math.round(h.score ?? 0)}<span className="text-sm text-ink-muted">%</span></span> : <Badge tone="amber">In progress {h.answered}/{h.questions}</Badge>}
            </Link></li>
          ))}
        </ul></Card>
      ) : <Empty title="No tests yet">Your first test gives you a baseline score to beat.</Empty>}
    </>
  );
}
