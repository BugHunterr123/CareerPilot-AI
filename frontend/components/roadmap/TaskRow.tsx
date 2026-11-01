"use client";
import clsx from "clsx";
import Link from "next/link";
import { useState } from "react";
import { Check, ChevronDown } from "lucide-react";
import { api } from "@/lib/api";
import type { Task } from "@/lib/types";
import { PriorityBadge } from "../labels";

function practiceHref(p: Task["practice"]): string | null {
  if (p.mock) return "/interview/";
  const q = new URLSearchParams();
  if (p.subject) q.set("subject", String(p.subject));
  if (p.company_id) q.set("company_id", String(p.company_id));
  return q.toString() ? `/practice/?${q}` : null;
}

export function TaskRow({ t, onChange }: { t: Task; onChange: (t: Task) => void }) {
  const [open, setOpen] = useState(false);
  const done = t.status === "done";
  const patch = async (body: Record<string, string>) => onChange(await api<Task>(`/api/roadmap/tasks/${t.id}`, { method: "PATCH", body }));
  const href = practiceHref(t.practice);
  return (
    <li className="border-b border-line last:border-0">
      <div className="flex items-start gap-3 px-4 py-3">
        <button onClick={() => patch({ status: done ? "todo" : "done" })} role="checkbox" aria-checked={done} aria-label={`Mark "${t.topic}" as ${done ? "not done" : "done"}`}
          className={clsx("mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-colors", done ? "border-accent bg-accent text-white" : "border-ink-faint bg-white hover:border-accent")}>
          {done && <Check className="h-3.5 w-3.5" strokeWidth={3} />}
        </button>
        <button onClick={() => setOpen(!open)} aria-expanded={open} className="flex min-w-0 flex-1 items-start justify-between gap-3 text-left">
          <span className="min-w-0">
            <span className={clsx("block text-sm font-medium", done && "text-ink-muted line-through")}>{t.topic}</span>
            <span className="text-xs text-ink-muted">{new Date(t.due_date).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })} · {t.est_minutes} min{t.skill ? ` · ${t.skill}` : ""}</span>
          </span>
          <span className="flex shrink-0 items-center gap-2"><PriorityBadge p={t.priority} /><ChevronDown className={clsx("h-4 w-4 text-ink-faint transition-transform", open && "rotate-180")} /></span>
        </button>
      </div>
      {open && (
        <div className="space-y-3 px-4 pb-4 pl-12 text-sm">
          <p className="text-ink-soft">{t.explanation}</p>
          <p className="text-ink-soft"><b className="font-medium text-ink">Why:</b> {t.why}</p>
          {t.resources.length > 0 && (
            <div>{t.resources.map((r) => <a key={r.url} href={r.url} target="_blank" rel="noreferrer" className="block text-accent hover:underline">{r.title} <span className="text-ink-faint">· {r.provider}</span></a>)}</div>
          )}
          <div className="flex flex-wrap items-center gap-3">
            {href && <Link href={href} className="text-accent hover:underline">{t.practice.mock ? "Start mock interview" : "Practise now"}</Link>}
            <label className="flex items-center gap-2 text-xs text-ink-muted">Move to
              <input type="date" className="input h-8 w-auto py-0 text-xs" value={t.due_date} onChange={(e) => e.target.value && patch({ due_date: e.target.value })} />
            </label>
            {t.status !== "skipped" && !done && <button className="text-xs text-ink-muted hover:text-ink" onClick={() => patch({ status: "skipped" })}>Skip</button>}
          </div>
        </div>
      )}
    </li>
  );
}
