"use client";
import { useApi } from "@/lib/hooks";
import { PageHeader } from "@/components/PageHeader";
import { Card, Empty, ErrorNote, Meter, Notice, PageSkeleton } from "@/components/ui";
import { ActivityChart, InterviewChart } from "@/components/progress/Charts";
import { Applications, type App } from "@/components/progress/Applications";

type P = {
  indicators: { name: string; value: number; unit: string; explain: string }[];
  subjects: { subject: string; attempts: number; correct: number; accuracy: number }[];
  weak: { subject: string; accuracy: number }[]; interviews: { id: number; date: string; overall: number | null; type: string }[];
  next: string[]; note: string; daily: { date: string; tasks: number; attempts: number; correct: number }[];
  recent: { kind: string; detail: Record<string, unknown>; at: string }[]; applications: App[];
};

export default function ProgressPage() {
  const { data: d, error, loading, reload } = useApi<P>("/api/progress");
  if (loading && !d) return <PageSkeleton />;
  if (error) return <ErrorNote message={error.message} onRetry={reload} />;
  if (!d) return null;
  return (
    <>
      <PageHeader eyebrow="Progress tracking" title="What you have actually done">{d.note}</PageHeader>
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        {d.indicators.map((i) => (
          <Card key={i.name} className="p-4">
            <p className="text-[13px] text-ink-muted">{i.name}</p>
            <p className="mt-1 font-serif text-[28px] font-semibold leading-none">{i.value}<span className="ml-0.5 text-base font-normal text-ink-muted">{i.unit}</span></p>
            <p className="mt-2 text-xs text-ink-muted">{i.explain}</p>
          </Card>
        ))}
      </div>
      {d.next.length > 0 && <Notice tone="green" className="mt-5"><b className="font-medium">Study next:</b> {d.next.join(" ")}</Notice>}
      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <Card className="p-5"><h2 className="mb-3 text-sm font-semibold">Daily activity</h2>{d.daily.length ? <ActivityChart data={d.daily} /> : <Empty title="No activity yet">Finish a roadmap task or answer a question.</Empty>}</Card>
        <Card className="p-5"><h2 className="mb-3 text-sm font-semibold">Mock interview scores</h2>{d.interviews.length ? <InterviewChart data={d.interviews} /> : <Empty title="No interviews yet">Scores appear here after each mock interview.</Empty>}</Card>
      </div>
      <Card className="mt-5 p-5">
        <h2 className="text-sm font-semibold">Accuracy by subject</h2>
        {d.subjects.length ? (
          <ul className="mt-3 grid gap-x-8 gap-y-3 md:grid-cols-2">
            {d.subjects.map((s) => (
              <li key={s.subject}>
                <div className="flex justify-between text-[13px]"><span>{s.subject}</span><span className="tabular-nums text-ink-muted">{s.correct}/{s.attempts} · {s.accuracy}%</span></div>
                <Meter value={s.accuracy} tone={s.accuracy >= 60 ? "green" : "amber"} className="mt-1" />
              </li>
            ))}
          </ul>
        ) : <p className="mt-2 text-sm text-ink-muted">Answer practice questions to see this.</p>}
      </Card>
      <div className="mt-5"><Applications apps={d.applications} onChange={reload} /></div>
    </>
  );
}
