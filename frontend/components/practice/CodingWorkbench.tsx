"use client";
/**
 * Write code, run it against the visible test cases (or your own input), then submit
 * against all test cases including hidden ones. Used by the question bank and timed tests.
 */
import clsx from "clsx";
import { useState } from "react";
import { Check, Play, RotateCcw, Send, X } from "lucide-react";
import { api } from "@/lib/api";
import type { Question, RunResult, TestRun } from "@/lib/types";
import { Badge, Button, ErrorNote } from "../ui";
import { CodeEditor } from "./CodeEditor";

export function TestResults({ run }: { run: TestRun }) {
  return (
    <div className="space-y-2" data-testid="test-results">
      <p className={clsx("flex items-center gap-2 text-sm font-semibold", run.all_passed ? "text-accent" : "text-danger")}>
        {run.all_passed ? <Check className="h-4 w-4" aria-hidden /> : <X className="h-4 w-4" aria-hidden />}
        {run.passed} of {run.total} test cases passed
      </p>
      <ul className="space-y-2">
        {run.results.map((r) => (
          <li key={r.index} className={clsx("rounded-md border px-3 py-2 text-[13px]", r.passed ? "border-accent-line bg-accent-soft/40" : "border-danger-line bg-danger-soft/50")}>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">Test {r.index}{r.hidden ? " (hidden)" : ""}</span>
              <Badge tone={r.passed ? "green" : "red"}>{r.passed ? "Passed" : r.status === "timeout" ? "Time limit" : r.status === "error" ? "Error" : r.status === "blocked" ? "Blocked" : "Wrong answer"}</Badge>
              <span className="text-xs text-ink-faint">{r.time_ms} ms</span>
            </div>
            {!r.hidden && (
              <div className="mt-2 grid gap-2 font-mono text-[12px] sm:grid-cols-3">
                <div><p className="label-sm mb-0.5">Input</p><pre className="max-h-28 overflow-auto whitespace-pre-wrap rounded bg-white px-2 py-1">{r.input}</pre></div>
                <div><p className="label-sm mb-0.5">Expected</p><pre className="max-h-28 overflow-auto whitespace-pre-wrap rounded bg-white px-2 py-1">{r.expected}</pre></div>
                <div><p className="label-sm mb-0.5">Your output</p><pre className="max-h-28 overflow-auto whitespace-pre-wrap rounded bg-white px-2 py-1">{r.output || " "}</pre></div>
              </div>
            )}
            {r.error && <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap rounded bg-white px-2 py-1 font-mono text-[12px] text-danger">{r.error}</pre>}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function CodingWorkbench({ q, runPath, submitPath, submitBody, submitLabel = "Submit", initialCode, onCode, onSubmitted }: {
  q: Question; runPath: string; submitPath: string; submitBody?: (code: string) => Record<string, unknown>;
  submitLabel?: string; initialCode?: string; onCode?: (code: string) => void; onSubmitted?: (r: TestRun & Record<string, unknown>) => void;
}) {
  const [code, setCode] = useState(initialCode ?? q.starter_code);
  const [custom, setCustom] = useState<string | null>(null);
  const [run, setRun] = useState<TestRun | null>(null);
  const [customOut, setCustomOut] = useState<RunResult | null>(null);
  const [busy, setBusy] = useState<"run" | "submit" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const change = (c: string) => { setCode(c); onCode?.(c); };

  const go = async (kind: "run" | "submit") => {
    setBusy(kind); setError(null);
    try {
      if (kind === "run" && custom !== null) {
        setCustomOut(await api<RunResult>(runPath, { body: { code, stdin: custom } })); setRun(null);
      } else if (kind === "run") {
        setRun(await api<TestRun>(runPath, { body: { code } })); setCustomOut(null);
      } else {
        const r = await api<TestRun & Record<string, unknown>>(submitPath, { body: submitBody ? submitBody(code) : { code } });
        setRun(r); setCustomOut(null); onSubmitted?.(r);
      }
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(null); }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-ink-muted">Python 3 · read input from stdin, print the answer · {q.visible_tests.length} visible + {q.hidden_test_count} hidden tests</p>
        <button className="inline-flex items-center gap-1 text-xs text-ink-muted hover:text-ink" onClick={() => change(q.starter_code)}><RotateCcw className="h-3.5 w-3.5" aria-hidden />Reset to starter code</button>
      </div>
      <CodeEditor value={code} onChange={change} />
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" variant="secondary" busy={busy === "run"} disabled={!!busy} onClick={() => go("run")} data-testid="run-code"><Play className="h-3.5 w-3.5" aria-hidden />{custom !== null ? "Run with my input" : "Run sample tests"}</Button>
        <Button size="sm" busy={busy === "submit"} disabled={!!busy} onClick={() => go("submit")} data-testid="submit-code"><Send className="h-3.5 w-3.5" aria-hidden />{submitLabel}</Button>
        <label className="ml-auto flex items-center gap-2 text-xs text-ink-muted"><input type="checkbox" className="accent-[#1F5C46]" checked={custom !== null} onChange={(e) => setCustom(e.target.checked ? (q.visible_tests[0]?.input ?? "") : null)} />Use custom input</label>
      </div>
      {custom !== null && <textarea className="input min-h-[80px] font-mono text-[12.5px]" value={custom} onChange={(e) => setCustom(e.target.value)} aria-label="Custom input" />}
      <ErrorNote message={error} />
      {customOut && (
        <div className="rounded-md border border-line bg-paper/60 p-3 text-[13px]">
          <p className="mb-1 font-medium">Output <span className="text-xs font-normal text-ink-faint">({customOut.status}, {customOut.time_ms} ms)</span></p>
          <pre className="whitespace-pre-wrap font-mono text-[12px]">{customOut.stdout || " "}</pre>
          {customOut.stderr && <pre className="mt-2 whitespace-pre-wrap font-mono text-[12px] text-danger">{customOut.stderr}</pre>}
        </div>
      )}
      {run && <TestResults run={run} />}
    </div>
  );
}
