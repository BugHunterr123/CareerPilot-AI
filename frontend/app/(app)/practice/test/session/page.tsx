"use client";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import clsx from "clsx";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { Check, Clock, X } from "lucide-react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { PracticeTest, Question } from "@/lib/types";
import { useShell } from "@/components/AppShell";
import { Badge, Button, ButtonLink, Card, ErrorNote, Notice, PageSkeleton } from "@/components/ui";
import { SourceLabel } from "@/components/labels";
import { CodingWorkbench } from "@/components/practice/CodingWorkbench";
import { ProblemStatement } from "@/components/practice/QuestionCard";
import { SolutionTabs } from "@/components/practice/SolutionTabs";

function useCountdown(endsAt: string | undefined, active: boolean) {
  const [left, setLeft] = useState<number | null>(null);
  useEffect(() => {
    if (!endsAt || !active) return;
    const tick = () => setLeft(Math.max(0, Math.round((new Date(endsAt).getTime() - Date.now()) / 1000)));
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, [endsAt, active]);
  return left;
}

function Results({ t }: { t: PracticeTest }) {
  return (
    <>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="label-sm">Test result · {t.kind === "coding" ? "Coding" : "MCQ"} · {t.company_name ?? "Any company"} · {t.difficulty}</p>
          <h1 className="h-display mt-1 text-[34px]" data-testid="test-score">{Math.round(t.score ?? 0)}%</h1>
          <p className="text-sm text-ink-muted">{t.answered} of {t.questions.length} answered. {t.kind === "coding" ? "Score = share of test cases passed, averaged over questions." : "Score = correct answers out of all questions."}</p>
        </div>
        <div className="flex gap-2"><ButtonLink href="/practice/test/" variant="secondary">New test</ButtonLink><ButtonLink href="/progress/">See progress</ButtonLink></div>
      </div>
      <div className="space-y-4">
        {t.questions.map((q, i) => {
          const a = q.my_answer;
          const ok = !!a?.correct;
          return (
            <Card key={q.id} className="p-6">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs text-ink-faint">Q{i + 1}</span><SourceLabel label={q.label} /><Badge>{q.difficulty}</Badge>
                <Badge tone={!a ? "neutral" : ok ? "green" : "red"}>{!a ? "Not answered" : t.kind === "coding" ? `${a.passed}/${a.total} tests passed` : ok ? "Correct" : "Wrong"}</Badge>
              </div>
              <ProblemStatement q={q} />
              {t.kind === "mcq" && (
                <p className="mt-3 text-sm">{a?.choice && <span className={ok ? "text-accent" : "text-danger"}>{ok ? <Check className="mr-1 inline h-4 w-4" /> : <X className="mr-1 inline h-4 w-4" />}Your answer: {a.choice}. </span>}
                  <span className="text-ink-soft">Correct: <b className="font-medium">{q.correct_option}</b></span></p>
              )}
              {q.explanation && t.kind === "mcq" && <p className="mt-1 text-sm text-ink-muted">{q.explanation}</p>}
              {t.kind === "coding" && (
                <details className="mt-4"><summary className="cursor-pointer text-sm font-medium text-accent">Your code and the model solution</summary>
                  <div className="mt-3 grid gap-4 lg:grid-cols-2">
                    <div><p className="label-sm mb-2">Your code</p><pre className="max-h-[420px] overflow-auto rounded border border-line bg-paper px-3 py-2 font-mono text-[12.5px]">{a?.code || "(no code submitted)"}</pre></div>
                    <div><p className="label-sm mb-2">Model solution</p><SolutionTabs python={q.solution} others={q.solutions_other} /></div>
                  </div>
                  {q.explanation && <p className="mt-3 text-sm text-ink-soft">{q.explanation}</p>}
                </details>
              )}
            </Card>
          );
        })}
      </div>
    </>
  );
}

function Session() {
  const id = useSearchParams().get("id");
  const { data: t, error, loading, setData, reload } = useApi<PracticeTest>(id ? `/api/tests/${id}` : null);
  const { refresh } = useShell();
  const [idx, setIdx] = useState(0);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const finishing = useRef(false);
  const active = t?.status === "active";
  const left = useCountdown(t?.ends_at, !!active);

  const finish = useCallback(async () => {
    if (!t || finishing.current) return;
    finishing.current = true;
    try { setData(await api<PracticeTest>(`/api/tests/${t.id}/finish`, { method: "POST" })); refresh(); window.scrollTo({ top: 0 }); }
    catch (e) { setErr(e instanceof Error ? e.message : String(e)); finishing.current = false; }
  }, [t, setData, refresh]);

  useEffect(() => { if (active && left === 0) finish(); }, [left, active, finish]);

  if (loading && !t) return <PageSkeleton />;
  if (error || !t) return <ErrorNote message={error?.message ?? "Test not found."} />;
  if (t.status === "completed") return <Results t={t} />;

  const q: Question = t.questions[idx];
  const markAnswered = (qid: number, patch: Question["my_answer"]) =>
    setData({ ...t, answered: t.questions.filter((x) => x.my_answer || x.id === qid).length,
      questions: t.questions.map((x) => (x.id === qid ? { ...x, my_answer: { ...x.my_answer, ...patch } } : x)) });
  const choose = async (choice: string) => {
    setSaving(true); setErr(null);
    try { await api(`/api/tests/${t.id}/answer`, { body: { question_id: q.id, choice } }); markAnswered(q.id, { choice }); }
    catch (e) { setErr(e instanceof Error ? e.message : String(e)); reload(); } finally { setSaving(false); }
  };
  const mm = left === null ? "--:--" : `${String(Math.floor(left / 60)).padStart(2, "0")}:${String(left % 60).padStart(2, "0")}`;
  return (
    <div>
      <div className="sticky top-14 z-10 -mx-4 mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-line bg-paper/95 px-4 py-3 backdrop-blur sm:-mx-8 sm:px-8 lg:top-0">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <Link href="/practice/test/" className="text-ink-muted hover:text-ink">Timed tests</Link><span className="text-ink-faint">/</span>
          <span className="font-medium">{t.kind === "coding" ? "Coding" : "MCQ"} test · {t.company_name ?? "Any company"}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className={clsx("inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 font-mono text-sm", left !== null && left < 120 ? "border-danger-line bg-danger-soft text-danger" : "border-line bg-white")} aria-live="polite" data-testid="timer"><Clock className="h-4 w-4" aria-hidden />{mm}</span>
          <Button size="sm" variant="secondary" onClick={finish} data-testid="finish-test">Finish test</Button>
        </div>
      </div>
      {t.note && <Notice tone="amber" className="mb-4">{t.note}</Notice>}
      <nav className="mb-5 flex flex-wrap gap-2" aria-label="Questions">
        {t.questions.map((x, i) => (
          <button key={x.id} onClick={() => setIdx(i)} aria-current={i === idx ? "step" : undefined}
            className={clsx("h-9 min-w-9 rounded-md border px-3 text-sm font-medium", i === idx ? "border-accent bg-accent text-white" : x.my_answer ? "border-accent-line bg-accent-soft text-accent" : "border-line bg-white text-ink-soft hover:bg-paper")}>{i + 1}</button>
        ))}
        <span className="ml-auto self-center text-xs text-ink-muted">{t.answered} of {t.questions.length} answered</span>
      </nav>
      <Card className="p-6">
        <div className="flex flex-wrap items-center gap-2"><span className="font-mono text-xs text-ink-faint">Question {idx + 1}</span><SourceLabel label={q.label} /><Badge>{q.subject}</Badge><Badge>{q.difficulty}</Badge></div>
        <ProblemStatement q={q} />
        {t.kind === "coding" ? (
          <div className="mt-5">
            <CodingWorkbench key={q.id} q={q} initialCode={q.my_answer?.code} runPath={`/api/tests/${t.id}/run?qid=${q.id}`} submitPath={`/api/tests/${t.id}/answer`}
              submitBody={(code) => ({ question_id: q.id, code })} submitLabel="Submit answer (all tests)"
              onSubmitted={(r) => markAnswered(q.id, { passed: r.passed, total: r.total })} />
            {q.my_answer?.total ? <p className="mt-3 text-sm text-ink-muted">Saved answer: {q.my_answer.passed}/{q.my_answer.total} tests passed. You can improve it and submit again until time runs out.</p> : null}
          </div>
        ) : (
          <fieldset className="mt-5 space-y-2" disabled={saving}>
            <legend className="sr-only">Options</legend>
            {(q.options ?? []).map((o, i) => (
              <label key={o} className={clsx("flex cursor-pointer items-center gap-3 rounded-md border px-3 py-2.5 text-sm", q.my_answer?.choice === o ? "border-accent bg-accent-soft" : "border-line hover:bg-paper")}>
                <input type="radio" name={`t${q.id}`} checked={q.my_answer?.choice === o} onChange={() => choose(o)} className="accent-[#1F5C46]" />
                <span className="font-mono text-xs text-ink-muted">{"ABCDEFGH"[i]}</span><span>{o}</span>
              </label>
            ))}
          </fieldset>
        )}
        <div className="mt-4"><ErrorNote message={err} /></div>
        <div className="mt-6 flex justify-between">
          <Button variant="ghost" disabled={idx === 0} onClick={() => setIdx(idx - 1)}>Previous</Button>
          {idx < t.questions.length - 1 ? <Button variant="secondary" onClick={() => setIdx(idx + 1)}>Next question</Button> : <Button onClick={finish}>Finish and see results</Button>}
        </div>
      </Card>
    </div>
  );
}

export default function Page() {
  return <Suspense fallback={<PageSkeleton />}><Session /></Suspense>;
}
