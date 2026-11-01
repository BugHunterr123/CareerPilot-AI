import Link from "next/link";
import type { Source, Stage } from "@/lib/types";
import { SourceLabel, SourceLink } from "../labels";

function List({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <p className="label-sm mb-1.5">{title}</p>
      <ul className="space-y-1 text-sm text-ink-soft">{items.map((i) => <li key={i} className="flex gap-2"><span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-ink-faint" />{i}</li>)}</ul>
    </div>
  );
}

export function StageCard({ stage, sources, slug, last }: { stage: Stage; sources: Record<string, Source>; slug: string; last: boolean }) {
  // "Also described in" lines only add corroborating sources; "Original source notes" are raw research notes.
  const facts = stage.format.filter((f) => !f.text.startsWith("Also described in") && !f.text.startsWith("Original source notes"));
  const also = Array.from(new Set(stage.format.filter((f) => f.text.startsWith("Also described in")).map((f) => f.source)));
  const notes = stage.format.find((f) => f.text.startsWith("Original source notes"));
  const study = stage.study.filter((x) => !stage.evaluates.includes(x));
  return (
    <li className="relative pl-10">
      {!last && <span className="absolute left-[13px] top-8 h-[calc(100%-8px)] w-px bg-line" aria-hidden />}
      <span className="absolute left-0 top-1 flex h-7 w-7 items-center justify-center rounded-full border border-ink bg-white font-mono text-xs">{stage.order}</span>
      <div className="card mb-5 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="font-serif text-lg font-semibold">{stage.name}</h3>
          <SourceLabel label={stage.label} />
        </div>
        <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{stage.what}</p>
        {facts.length > 0 && (
          <ul className="mt-3 divide-y divide-line rounded-md border border-line bg-paper/50">
            {facts.map((f, i) => (
              <li key={i} className="flex flex-col gap-1 px-3 py-2 text-[13px] sm:flex-row sm:items-start sm:justify-between sm:gap-4">
                <span className="text-ink">{f.text}</span>
                <span className="shrink-0"><SourceLink src={sources[f.source]} /></span>
              </li>
            ))}
          </ul>
        )}
        {also.length > 0 && (
          <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-muted">
            <span>Also reported in:</span>{also.map((k) => <SourceLink key={k} src={sources[k]} compact />)}
          </p>
        )}
        {notes && (
          <details className="mt-2 text-xs text-ink-muted">
            <summary className="cursor-pointer">Dates and details from each report</summary>
            <p className="mt-1 leading-relaxed">{notes.text.replace(/^Original source notes:\s*/, "")}</p>
          </details>
        )}
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <List title="What they check" items={stage.evaluates} />
          <List title="Also study" items={study} />
          <List title="Tips" items={stage.tips} />
        </div>
        <div className="mt-4 flex flex-col gap-2 border-t border-line pt-3 text-sm sm:flex-row sm:items-center sm:justify-between">
          {stage.before_next && <p className="text-ink-soft"><b className="font-medium text-ink">Before the next stage:</b> {stage.before_next}</p>}
          <Link href={`/practice/?company=${slug}`} className="shrink-0 text-accent hover:underline">Practice questions</Link>
        </div>
      </div>
    </li>
  );
}
