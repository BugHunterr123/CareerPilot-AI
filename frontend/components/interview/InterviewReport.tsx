import type { Interview } from "@/lib/types";
import { PageHeader } from "../PageHeader";
import { Badge, ButtonLink, Card, Notice } from "../ui";
import { ScoreBars } from "./ScoreBars";

function Block({ title, items }: { title: string; items: string[] }) {
  return (
    <Card className="p-5">
      <h2 className="text-sm font-semibold">{title}</h2>
      {items.length ? <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-ink-soft">{items.map((i) => <li key={i}>{i}</li>)}</ul> : <p className="mt-2 text-sm text-ink-muted">Nothing to add.</p>}
    </Card>
  );
}

export function InterviewReport({ mi }: { mi: Interview }) {
  const r = mi.report as Record<string, any>;
  return (
    <>
      <PageHeader eyebrow="Mock interview report" title={`${r.overall}/5 overall`}
        actions={<><ButtonLink href="/interview/" variant="secondary">New interview</ButtonLink><ButtonLink href="/practice/">Practise weak topics</ButtonLink></>}>
        Session #{mi.id} · <span className="capitalize">{mi.itype}</span> · {mi.difficulty} · {r.questions.length} answered{mi.company_name ? ` · ${mi.company_name}` : ""} · {new Date(mi.created_at).toLocaleString()}
        <span className="mt-2 block text-xs">This report is built only from the answers in this session. Scored by {r.engine === "llm" ? "the AI model with the four-part rubric" : r.engine === "mixed" ? "the AI model (some answers by the rule-based rubric after an AI error)" : "the rule-based rubric (no AI key configured)"}.</span>
      </PageHeader>
      <div className="grid gap-5 lg:grid-cols-[1fr_1.4fr]">
        <Card className="p-5"><h2 className="mb-4 text-sm font-semibold">By rubric area</h2><ScoreBars scores={r.criteria} plain /></Card>
        <div className="grid gap-5 sm:grid-cols-2">
          <Block title="Strengths" items={r.strengths} />
          <Block title="Areas to improve" items={r.improvements} />
          <Card className="p-5">
            <h2 className="text-sm font-semibold">Key terms you could have used</h2>
            {r.missing_concepts.length ? <div className="mt-2 flex flex-wrap gap-1.5">{(r.missing_concepts as string[]).map((c) => <Badge key={c}>{c}</Badge>)}</div>
              : <p className="mt-2 text-sm text-ink-muted">You covered the expected points.</p>}
          </Card>
          <Block title="Revise next" items={[...r.revision_topics, ...r.next_steps]} />
        </div>
      </div>
      <Card className="mt-5 p-5">
        <h2 className="text-sm font-semibold">Suggested answer structures</h2>
        <dl className="mt-2 grid gap-3 text-sm md:grid-cols-3">
          {Object.entries(r.suggested_structures as Record<string, string>).map(([k, v]) => <div key={k}><dt className="label-sm">{k}</dt><dd className="mt-1 text-ink-soft">{v}</dd></div>)}
        </dl>
      </Card>
      <h2 className="mb-3 mt-8 font-serif text-xl font-semibold">Your answers</h2>
      <div className="space-y-3">
        {mi.responses.map((x) => (
          <Card key={x.index} className="p-5">
            <div className="flex items-start justify-between gap-3"><p className="text-sm font-medium">{x.question}</p><span className="shrink-0 font-serif text-lg font-semibold">{x.total}</span></div>
            <p className="mt-2 whitespace-pre-line text-sm text-ink-soft">{x.answer}</p>
            <div className="mt-3 grid gap-4 md:grid-cols-[220px_1fr]">
              <ScoreBars scores={x.scores} />
              <div className="space-y-2 text-sm">
                {x.feedback.good.length > 0 && <p className="text-ink-soft"><b className="font-medium text-ink">Good:</b> {x.feedback.good.join("; ")}</p>}
                {x.feedback.missing.length > 0 && <p className="text-ink-soft"><b className="font-medium text-ink">Could also mention:</b> {x.feedback.missing.join(", ")}</p>}
                {x.feedback.quote && <p className="border-l-2 border-line pl-3 italic text-ink-muted">&ldquo;{x.feedback.quote}&rdquo;</p>}
                {x.feedback.better_answer && <p className="text-ink-soft"><b className="font-medium text-ink">A stronger answer:</b> {x.feedback.better_answer}</p>}
              </div>
            </div>
          </Card>
        ))}
      </div>
      <Notice className="mt-6">{r.disclaimer}</Notice>
    </>
  );
}
