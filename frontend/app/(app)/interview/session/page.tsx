"use client";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense, useState } from "react";
import { api } from "@/lib/api";
import { useAction, useApi } from "@/lib/hooks";
import type { Interview } from "@/lib/types";
import { useShell } from "@/components/AppShell";
import { Badge, Button, ButtonLink, Card, ErrorNote, Meter, Notice, PageSkeleton } from "@/components/ui";
import { ScoreBars } from "@/components/interview/ScoreBars";
import { InterviewReport } from "@/components/interview/InterviewReport";

function Session() {
  const id = useSearchParams().get("id");
  const { data: mi, error, loading, setData } = useApi<Interview>(id ? `/api/interviews/${id}` : null);
  const { refresh } = useShell();
  const [answer, setAnswer] = useState("");
  const act = useAction();
  if (loading && !mi) return <PageSkeleton />;
  if (error || !mi) return <ErrorNote message={error?.message ?? "Interview not found."} />;

  const submit = () => act.run(async () => {
    const next = await api<Interview>(`/api/interviews/${mi.id}/answer`, { body: { answer } });
    setData(next); setAnswer("");
    if (next.status === "completed") refresh();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  const end = () => act.run(async () => { setData(await api<Interview>(`/api/interviews/${mi.id}/finish`, { method: "POST" })); refresh(); });

  if (mi.status === "completed" && mi.report) return <InterviewReport mi={mi} />;
  const last = mi.last_feedback ?? (mi.responses.length ? mi.responses[mi.responses.length - 1] : null);
  const words = answer.trim() ? answer.trim().split(/\s+/).length : 0;
  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-4 flex items-center justify-between text-sm">
        <Link href="/interview/" className="text-ink-muted hover:text-ink">Mock interviews</Link>
        <span className="text-ink-muted">Question {mi.current_index + 1} of {mi.total_questions}</span>
      </div>
      <Meter value={(100 * mi.current_index) / mi.total_questions} className="mb-6" />
      {last && (
        <Card className="mb-6 p-5">
          <div className="flex items-center justify-between"><p className="text-sm font-semibold">Feedback on your last answer</p><Badge tone={last.total >= 3 ? "green" : "amber"}>{last.total}/5</Badge></div>
          <p className="mt-1 text-xs text-ink-muted">{last.question}</p>
          <div className="mt-4 grid gap-5 md:grid-cols-2">
            <ScoreBars scores={last.scores} />
            <div className="space-y-3 text-sm">
              {last.feedback.good.length > 0 && <p className="text-ink-soft"><b className="font-medium text-ink">Good:</b> {last.feedback.good.join("; ")}</p>}
              {last.feedback.missing.length > 0 && <p className="text-ink-soft"><b className="font-medium text-ink">You could also mention:</b> {last.feedback.missing.join(", ")}</p>}
              {last.feedback.quote && <p className="border-l-2 border-line pl-3 italic text-ink-muted">&ldquo;{last.feedback.quote}&rdquo;</p>}
              {last.feedback.better_answer && <p className="text-ink-soft"><b className="font-medium text-ink">A stronger answer:</b> {last.feedback.better_answer}</p>}
              <p className="text-ink-soft"><b className="font-medium text-ink">A good structure:</b> {last.feedback.structure_tip}</p>
              <p className="text-xs text-ink-faint">Scored by {last.feedback.engine === "llm" ? "the AI model" : "the rule-based rubric"} from this answer only.</p>
            </div>
          </div>
        </Card>
      )}
      {mi.current_question && (
        <Card className="p-6">
          <div className="flex flex-wrap items-center gap-2"><Badge>{mi.current_question.topic}</Badge><Badge tone="outline">{mi.current_question.kind}</Badge>
            {mi.current_question.origin && <span className="text-xs text-ink-muted">{mi.current_question.origin}</span>}</div>
          <h1 className="mt-3 font-serif text-[22px] font-semibold leading-snug">{mi.current_question.q}</h1>
          <textarea className="input mt-5 min-h-[180px] text-[15px] leading-relaxed" value={answer} onChange={(e) => setAnswer(e.target.value)}
            placeholder="Answer the way you would speak it. 60 to 150 words is a good length." aria-label="Your answer" />
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <span className="text-xs text-ink-muted">{words} words</span>
            <div className="flex gap-2">
              {mi.responses.length > 0 && <Button variant="ghost" onClick={end} disabled={act.busy}>End and see report</Button>}
              <Button busy={act.busy} disabled={!answer.trim()} onClick={submit}>{mi.current_index + 1 === mi.total_questions ? "Submit and finish" : "Submit answer"}</Button>
            </div>
          </div>
          <div className="mt-3"><ErrorNote message={act.error} /></div>
        </Card>
      )}
      <Notice className="mt-6">Scoring: {mi.scoring_mode === "llm" ? "AI model using the same four-part rubric." : "rule-based rubric (key points covered, examples and reasons, structure, length). It cannot judge correctness the way a person can."}</Notice>
      {!mi.current_question && <ButtonLink href="/interview/" className="mt-4">Back</ButtonLink>}
    </div>
  );
}

export default function Page() {
  return <Suspense fallback={<PageSkeleton />}><Session /></Suspense>;
}
