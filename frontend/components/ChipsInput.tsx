"use client";
import { X } from "lucide-react";
import { useState } from "react";

/** Editable list of short text items (skills, certifications...). Enter or comma adds an item. */
export function ChipsInput({ value, onChange, placeholder, label }: { value: string[]; onChange: (v: string[]) => void; placeholder?: string; label: string }) {
  const [draft, setDraft] = useState("");
  const add = () => {
    const parts = draft.split(",").map((s) => s.trim()).filter(Boolean);
    if (parts.length) onChange(Array.from(new Set([...value, ...parts])));
    setDraft("");
  };
  return (
    <div className="rounded-md border border-line bg-white p-2 focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/15">
      <ul className="flex flex-wrap gap-1.5" aria-label={label}>
        {value.map((v) => (
          <li key={v} className="inline-flex items-center gap-1 rounded border border-line bg-paper py-0.5 pl-2 pr-1 text-[13px]">
            {v}
            <button type="button" onClick={() => onChange(value.filter((x) => x !== v))} className="rounded p-0.5 text-ink-faint hover:text-danger" aria-label={`Remove ${v}`}>
              <X className="h-3 w-3" />
            </button>
          </li>
        ))}
        <li className="min-w-[160px] flex-1">
          <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={placeholder} aria-label={`Add to ${label}`}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === ",") { e.preventDefault(); add(); } }} onBlur={add}
            className="w-full bg-transparent px-1 py-0.5 text-sm outline-none placeholder:text-ink-faint" />
        </li>
      </ul>
    </div>
  );
}
