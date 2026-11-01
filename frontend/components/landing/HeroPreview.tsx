import { Check } from "lucide-react";
import { SourceLabel } from "@/components/labels";

/** A real-looking slice of the product (an example hiring guide), instead of an illustration. */
const ROWS = [
  ["Technical MCQ", "45 questions, 45 min", "Candidate-reported"],
  ["Coding", "3 questions in 60 min: frontend, SQL, DSA", "Candidate-reported"],
  ["Communication", "About 20 to 25 voice tasks", "Third-party"],
  ["Interview", "Projects + HR, 10 to 15 min", "Candidate-reported"],
];

export function HeroPreview() {
  return (
    <div className="relative sm:pb-36" aria-label="Example of a company hiring guide in CareerPilot">
      <div className="card overflow-hidden shadow-pop sm:ml-8">
        <div className="flex items-center justify-between border-b border-line bg-paper/60 px-5 py-3">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-ink-faint">Hiring guide · example</p>
            <p className="font-serif text-lg font-semibold">Accenture, campus drive</p>
          </div>
          <span className="rounded-full bg-accent-soft px-2.5 py-1 text-xs font-medium text-accent">Your target</span>
        </div>
        <ol className="divide-y divide-line">
          {ROWS.map(([name, fmt, label], i) => (
            <li key={name} className="flex items-start gap-3 px-5 py-3">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-line font-mono text-[11px] text-ink-muted">{i + 1}</span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-medium">{name}</p>
                  <SourceLabel label={label} />
                </div>
                <p className="text-[13px] text-ink-muted">{fmt}</p>
              </div>
            </li>
          ))}
        </ol>
        <div className="border-t border-line px-5 py-3 text-xs text-ink-muted">Reddit r/PlacementsPrep · 2026-09-24 · PrepInsta · GeeksforGeeks</div>
      </div>
      <div className="card absolute bottom-0 left-0 hidden w-64 p-4 shadow-pop sm:block">
        <p className="text-[11px] uppercase tracking-wider text-ink-faint">This week</p>
        {["Practise pseudocode: 10 questions", "Revise SQL joins", "2-minute project explanation"].map((t, i) => (
          <div key={t} className="mt-2 flex items-center gap-2 text-[13px]">
            <span className={`flex h-4 w-4 items-center justify-center rounded border ${i === 0 ? "border-accent bg-accent text-white" : "border-line"}`}>
              {i === 0 && <Check className="h-3 w-3" strokeWidth={3} aria-hidden />}
            </span>
            <span className={i === 0 ? "text-ink-muted line-through" : ""}>{t}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
