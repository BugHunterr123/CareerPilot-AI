"use client";
import { useState } from "react";
import clsx from "clsx";

const NAMES: Record<string, string> = { python: "Python", java: "Java", cpp: "C++" };

/** Model solution in the language the student picks (coding questions are language-agnostic). */
export function SolutionTabs({ python, others, initial = "python" }: { python: string; others: Record<string, string>; initial?: string }) {
  const all: Record<string, string> = { ...(python ? { python } : {}), ...others };
  const langs = Object.keys(all);
  const [lang, setLang] = useState(langs.includes(initial) ? initial : langs[0]);
  if (!langs.length) return null;
  return (
    <div>
      <div className="mb-2 flex gap-1" role="tablist" aria-label="Solution language">
        {langs.map((l) => (
          <button key={l} role="tab" aria-selected={lang === l} onClick={() => setLang(l)}
            className={clsx("rounded px-2.5 py-1 text-xs font-medium", lang === l ? "bg-accent text-white" : "text-ink-muted hover:bg-black/[0.04]")}>{NAMES[l] ?? l}</button>
        ))}
      </div>
      <pre className="max-h-[420px] overflow-auto rounded border border-line bg-white px-3 py-2 font-mono text-[12.5px] leading-relaxed">{all[lang]}</pre>
      {lang !== "python" && <p className="mt-1 text-xs text-ink-muted">The code runner executes Python. Solutions in other languages are shown for reading and were tested offline on the same cases.</p>}
    </div>
  );
}
