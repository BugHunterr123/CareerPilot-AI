"use client";
import clsx from "clsx";
import Link from "next/link";
import { Check } from "lucide-react";
import { useEffect, useRef } from "react";
import type { JourneyStep } from "@/lib/types";

/** Resume -> Skills -> Roles -> Company -> Plan -> Practice -> Interview -> Progress */
export function StepTracker({ steps }: { steps: JourneyStep[] }) {
  const list = useRef<HTMLOListElement>(null);
  useEffect(() => {  // on narrow screens, scroll the next step into view
    const el = list.current?.querySelector<HTMLElement>("[aria-current=step]");
    if (el && list.current) list.current.scrollLeft = el.offsetLeft - 16;
  }, [steps]);
  if (!steps.length) return <div className="h-[49px] border-b border-line bg-surface" aria-hidden />;
  const current = steps.findIndex((s) => !s.done);
  return (
    <nav aria-label="Your preparation journey" className="border-b border-line bg-surface">
      <ol ref={list} className="mx-auto flex max-w-content items-center gap-1 overflow-x-auto px-4 py-2.5 sm:px-8">
        {steps.map((s, i) => {
          const isCurrent = i === current;
          return (
            <li key={s.key} className="flex shrink-0 items-center">
              <Link href={s.href + "/"} aria-current={isCurrent ? "step" : undefined}
                className={clsx("flex items-center gap-1.5 rounded-full py-1 pl-1 pr-2.5 text-[12.5px] transition-colors",
                  isCurrent ? "bg-accent-soft font-medium text-accent" : s.done ? "text-ink-soft hover:bg-black/[0.04]" : "text-ink-faint hover:bg-black/[0.04]")}>
                <span className={clsx("flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-semibold",
                  s.done ? "bg-accent text-white" : isCurrent ? "border border-accent bg-white text-accent" : "border border-line bg-white text-ink-faint")}>
                  {s.done ? <Check className="h-3 w-3" strokeWidth={3} aria-hidden /> : i + 1}
                </span>
                {s.label}
                <span className="sr-only">{s.done ? "(done)" : isCurrent ? "(next step)" : ""}</span>
              </Link>
              {i < steps.length - 1 && <span className={clsx("mx-0.5 h-px w-3 sm:w-5", s.done ? "bg-accent-line" : "bg-line")} aria-hidden />}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
