"use client";
import { useState } from "react";
import { Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Link } from "@/lib/types";
import { Badge, Button, ErrorNote } from "./ui";

const KINDS = [
  { kind: "github", label: "GitHub", placeholder: "https://github.com/your-username", help: "We read public repositories through GitHub's official API." },
  { kind: "linkedin", label: "LinkedIn", placeholder: "https://linkedin.com/in/your-name", help: "We do not scrape LinkedIn. Paste your skills or courses below if you want them used." },
  { kind: "leetcode", label: "LeetCode", placeholder: "https://leetcode.com/u/your-name", help: "Not read automatically. Add your solved counts or topics below." },
  { kind: "portfolio", label: "Portfolio", placeholder: "https://your-site.dev", help: "We read one public page." },
];
const STATUS: Record<string, { tone: "green" | "amber" | "red" | "neutral"; text: string }> = {
  ok: { tone: "green", text: "Read" }, manual: { tone: "neutral", text: "Manual details" },
  unavailable: { tone: "amber", text: "Unavailable" }, invalid: { tone: "red", text: "Invalid" }, not_checked: { tone: "neutral", text: "Saved, not read" },
};

export function LinksEditor({ links, onChange }: { links: Link[]; onChange: () => void }) {
  const [open, setOpen] = useState<string | null>(null);
  const [url, setUrl] = useState("");
  const [details, setDetails] = useState("");
  const [consent, setConsent] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function add(kind: string) {
    setBusy(true);
    setError(null);
    try {
      await api("/api/profile/links", { body: { kind, url, consent, manual_details: details } });
      setOpen(null); setUrl(""); setDetails("");
      onChange();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  async function remove(id: number) {
    await api(`/api/profile/links/${id}`, { method: "DELETE" });
    onChange();
  }

  return (
    <div className="divide-y divide-line rounded-lg border border-line bg-white">
      {KINDS.map((k) => {
        const existing = links.filter((l) => l.kind === k.kind);
        return (
          <div key={k.kind} className="px-4 py-3.5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium">{k.label} <span className="ml-1 text-xs font-normal text-ink-faint">Optional</span></p>
                <p className="text-xs text-ink-muted">{k.help}</p>
              </div>
              {open !== k.kind && (
                <Button variant="secondary" size="sm" onClick={() => { setOpen(k.kind); setError(null); }}>
                  {existing.length ? "Add another" : "Add"}
                </Button>
              )}
            </div>
            {existing.map((l) => (
              <div key={l.id} className="mt-2 flex items-start justify-between gap-3 rounded-md bg-paper px-3 py-2 text-[13px]">
                <div className="min-w-0">
                  <p className="truncate font-mono text-xs">{l.url}</p>
                  <p className="mt-0.5 text-xs text-ink-muted">{l.note}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge tone={STATUS[l.status]?.tone ?? "neutral"}>{STATUS[l.status]?.text ?? l.status}</Badge>
                  <button onClick={() => remove(l.id)} aria-label={`Remove ${k.label} link`} className="text-ink-faint hover:text-danger"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>
            ))}
            {open === k.kind && (
              <div className="mt-3 space-y-2.5">
                <input className="input" placeholder={k.placeholder} value={url} onChange={(e) => setUrl(e.target.value)} aria-label={`${k.label} URL`} />
                {(k.kind === "linkedin" || k.kind === "leetcode") && (
                  <textarea className="input min-h-[72px]" value={details} onChange={(e) => setDetails(e.target.value)}
                    placeholder={k.kind === "leetcode" ? "e.g. 120 solved: arrays, hashing, two pointers, SQL 50" : "e.g. Skills: Python, SQL, Power BI. Course: Google Data Analytics"}
                    aria-label={`${k.label} details`} />
                )}
                <label className="flex items-start gap-2 text-xs text-ink-soft">
                  <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5 accent-[#1F5C46]" />
                  I allow CareerPilot to read the public information at this link. We never ask for your password.
                </label>
                <ErrorNote message={error} />
                <div className="flex gap-2">
                  <Button size="sm" busy={busy} onClick={() => add(k.kind)} disabled={!url.trim()}>Save link</Button>
                  <Button size="sm" variant="ghost" onClick={() => setOpen(null)}>Cancel</Button>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
