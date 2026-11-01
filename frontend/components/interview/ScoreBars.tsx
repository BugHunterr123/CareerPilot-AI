import type { Score } from "@/lib/types";
import { Meter } from "../ui";

const NAMES: Record<string, string> = { concepts: "Key concepts", depth: "Depth", structure: "Structure", clarity: "Clarity" };

export function ScoreBars({ scores, plain }: { scores: Record<string, Score | number>; plain?: boolean }) {
  return (
    <dl className="space-y-2.5">
      {Object.entries(scores).map(([k, v]) => {
        const n = typeof v === "number" ? v : v.score;
        return (
          <div key={k}>
            <div className="flex justify-between text-[13px]"><dt>{NAMES[k] ?? k}</dt><dd className="tabular-nums text-ink-muted">{n}/5</dd></div>
            <Meter value={(100 * n) / 5} tone={n >= 3 ? "green" : "amber"} className="mt-1" />
            {!plain && typeof v !== "number" && <p className="mt-0.5 text-xs text-ink-muted">{v.reason}</p>}
          </div>
        );
      })}
    </dl>
  );
}
