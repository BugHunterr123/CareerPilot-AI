"use client";
import clsx from "clsx";
import { useState } from "react";
import { Bookmark, BookmarkCheck, Check, Code2, X } from "lucide-react";
import { api } from "@/lib/api";
import type { Question } from "@/lib/types";
import { Badge, Button } from "../ui";
import { SourceLabel, SourceLink } from "../labels";
import { CodingWorkbench } from "./CodingWorkbench";
import { SolutionTabs } from "./SolutionTabs";

type Result = { correct: boolean; answer: string; explanation: string; stats: Question["stats"]; correct_option?: string | null };

export function ProblemStatement({ q }: { q: Question }) {
  const io = q.io_format || {};
  return (
    <>
      {q.title && <p className="mt-3 font-serif text-lg font-semibold">{q.title}</p>}
      <h3 id={`q-${q.id}`} className={clsx("whitespace-pre-line text-[15px] leading-relaxed", q.title ? "mt-1 text-ink-soft" : "mt-3 font-medium")}>{q.question}</h3>
      {(io.input_format || io.output_format || io.constraints) && (
        <dl className="mt-3 grid gap-3 text-[13px] sm:grid-cols-3">
          {io.input_format && <div><dt className="label-sm">Input</dt><dd className="mt-0.5 whitespace-pre-line text-ink-soft">{io.input_format}</dd></div>}
          {io.output_format && <div><dt className="label-sm">Output</dt><dd className="mt-0.5 whitespace-pre-line text-ink-soft">{io.output_format}</dd></div>}
          {io.constraints && <div><dt className="label-sm">Constraints</dt><dd className="mt-0.5 whitespace-pre-line text-ink-soft">{io.constraints}</dd></div>}
        </dl>
      )}
      {q.code && <pre className="mt-3 overflow-x-auto rounded-md border border-line bg-paper px-3 py-2 font-mono text-[12.5px] leading-relaxed">{q.code}</pre>}
      {q.sample_io && <pre className="mt-3 overflow-x-auto whitespace-pre-wrap rounded-md border border-line bg-paper px-3 py-2 font-mono text-[12px] text-ink-soft">{q.sample_io}</pre>}
    </>
  );
}

export function QuestionCard({ q, n, lang = "python" }: { q: Question; n: number; lang?: string }) {
  const [choice, setChoice] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [reveal, setReveal] = useState(false);
  const [coding, setCoding] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [saved, setSaved] = useState(q.saved);
  const [stats, setStats] = useState(q.stats);
  const isMcq = q.qtype === "mcq" && !!q.options;

  const attempt = async (body: Record<string, unknown>) => {
    const r = await api<Result>(`/api/questions/${q.id}/attempt`, { body });
    setResult(r); setStats(r.stats); setReveal(true);
  };
  const toggleSave = async () => { await api(`/api/questions/${q.id}/save`, { method: saved ? "DELETE" : "POST" }); setSaved(!saved); };

  return (
    <article className="card p-6" aria-labelledby={`q-${q.id}`} data-testid="question-card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="font-mono text-xs text-ink-faint">#{n}</span>
          <SourceLabel label={q.label} />
          {q.company_name && <Badge tone="outline">{q.company_name}</Badge>}
          <Badge>{q.subject}</Badge><Badge>{q.qtype.toUpperCase()}</Badge><Badge>{q.difficulty}</Badge>
          {q.runnable && <Badge tone="green"><Code2 className="h-3 w-3" aria-hidden />Runnable</Badge>}
          {stats.attempts > 0 && <Badge tone={stats.last_correct ? "green" : "red"}>{stats.correct}/{stats.attempts} correct</Badge>}
        </div>
        <button onClick={toggleSave} className="rounded p-1 text-ink-muted hover:text-accent" aria-pressed={saved} aria-label={saved ? "Remove from saved" : "Save question"}>
          {saved ? <BookmarkCheck className="h-5 w-5 text-accent" /> : <Bookmark className="h-5 w-5" />}
        </button>
      </div>
      <ProblemStatement q={q} />

      {isMcq ? (
        <fieldset className="mt-4 space-y-1.5" disabled={!!result}>
          <legend className="sr-only">Options</legend>
          {q.options!.map((o, i) => {
            const isAnswer = !!result && result.correct_option === o;
            return (
              <label key={o} className={clsx("flex cursor-pointer items-center gap-3 rounded-md border px-3 py-2 text-sm transition-colors",
                isAnswer ? "border-accent bg-accent-soft" : result && choice === o ? "border-danger-line bg-danger-soft" : choice === o ? "border-accent" : "border-line hover:bg-paper")}>
                <input type="radio" name={`q${q.id}`} value={o} checked={choice === o} onChange={() => setChoice(o)} className="accent-[#1F5C46]" />
                <span className="font-mono text-xs text-ink-muted">{"ABCDEFGH"[i]}</span><span>{o}</span>
              </label>
            );
          })}
          {!result && <Button size="sm" className="mt-2" disabled={!choice} onClick={() => attempt({ response: choice })}>Check answer</Button>}
        </fieldset>
      ) : q.runnable ? (
        <div className="mt-4">
          {!coding ? (
            <div className="flex flex-wrap gap-2">
              <Button size="sm" onClick={() => setCoding(true)} data-testid="open-editor"><Code2 className="h-4 w-4" aria-hidden />Solve in the editor</Button>
              <Button size="sm" variant="secondary" onClick={() => setReveal(!reveal)}>{reveal ? "Hide solution" : "Show solution"}</Button>
              {q.hints.length > 0 && <details className="text-sm text-ink-muted"><summary className="cursor-pointer py-1.5">Hint</summary>{q.hints.join(" · ")}</details>}
            </div>
          ) : (
            <CodingWorkbench q={q} runPath={`/api/questions/${q.id}/run`} submitPath={`/api/questions/${q.id}/submit`}
              submitLabel="Submit (all tests)" onSubmitted={(r) => { setStats((r.stats as Question["stats"]) ?? stats); setReveal(true); }} />
          )}
        </div>
      ) : !reveal ? (
        <div className="mt-4 space-y-2">
          <textarea className="input min-h-[80px] font-mono text-[13px]" placeholder="Write your answer first (optional)" value={text} onChange={(e) => setText(e.target.value)} aria-label="Your answer" />
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="secondary" onClick={() => setReveal(true)}>Show model answer</Button>
            {q.hints.length > 0 && <details className="text-sm text-ink-muted"><summary className="cursor-pointer py-1.5">Hint</summary>{q.hints.join(" · ")}</details>}
          </div>
        </div>
      ) : null}

      {reveal && (
        <div className="mt-4 space-y-3 rounded-md border border-line bg-paper/60 p-4 text-sm">
          {result && <p className={clsx("flex items-center gap-1.5 font-medium", result.correct ? "text-accent" : "text-danger")}>{result.correct ? <Check className="h-4 w-4" /> : <X className="h-4 w-4" />}{result.correct ? "Correct" : "Not quite"}</p>}
          {q.answer && q.answer !== "See the solution." && <p><b className="font-medium">Answer:</b> <span className="whitespace-pre-line">{q.answer}</span></p>}
          {(q.solution || Object.keys(q.solutions_other || {}).length > 0) && <SolutionTabs python={q.solution} others={q.solutions_other || {}} initial={lang} />}
          {q.explanation && <p className="text-ink-soft">{q.explanation}</p>}
          {!isMcq && !q.runnable && !result && (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-ink-muted">How did you do?</span>
              <Button size="sm" variant="secondary" onClick={() => attempt({ response: text, self_correct: true })}>I got it right</Button>
              <Button size="sm" variant="secondary" onClick={() => attempt({ response: text, self_correct: false })}>I got it wrong</Button>
            </div>
          )}
        </div>
      )}
      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-ink-muted">
        {q.source ? <SourceLink src={q.source} compact /> : null}
        {q.source_note && <span>{q.source_note}</span>}
      </div>
    </article>
  );
}
