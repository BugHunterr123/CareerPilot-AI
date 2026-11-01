"use client";
import { useState } from "react";
import { Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { Badge, Button, Card, ErrorNote } from "../ui";

export type App = { id: number; company_name: string; role: string; status: string; applied_on: string | null; interview_date: string | null; outcome: string; notes: string };
const STATUSES = ["planning", "applied", "test", "interview", "offer", "rejected", "withdrawn"];

/** Applications the student records by hand (CareerPilot does not apply on their behalf). */
export function Applications({ apps, onChange }: { apps: App[]; onChange: () => void }) {
  const [f, setF] = useState({ company_name: "", role: "", status: "applied", interview_date: "" });
  const [err, setErr] = useState<string | null>(null);
  const add = async () => {
    try { await api("/api/applications", { body: { ...f, interview_date: f.interview_date || null } }); setF({ company_name: "", role: "", status: "applied", interview_date: "" }); onChange(); }
    catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  };
  const update = async (a: App, status: string) => { await api(`/api/applications/${a.id}`, { method: "PUT", body: { ...a, status } }); onChange(); };
  const remove = async (id: number) => { await api(`/api/applications/${id}`, { method: "DELETE" }); onChange(); };
  return (
    <Card className="p-5">
      <h2 className="font-serif text-lg font-semibold">Applications and interview dates</h2>
      <p className="mt-0.5 text-sm text-ink-muted">Record drives you have applied to from your placement portal.</p>
      <div className="mt-4 grid gap-2 sm:grid-cols-[1.2fr_1fr_0.8fr_0.9fr_auto]">
        <input className="input" placeholder="Company" value={f.company_name} onChange={(e) => setF({ ...f, company_name: e.target.value })} aria-label="Company" />
        <input className="input" placeholder="Role" value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })} aria-label="Role" />
        <select className="input" value={f.status} onChange={(e) => setF({ ...f, status: e.target.value })} aria-label="Status">{STATUSES.map((s) => <option key={s}>{s}</option>)}</select>
        <input type="date" className="input" value={f.interview_date} onChange={(e) => setF({ ...f, interview_date: e.target.value })} aria-label="Interview date" />
        <Button variant="secondary" onClick={add} disabled={!f.company_name.trim()}>Add</Button>
      </div>
      <div className="mt-2"><ErrorNote message={err} /></div>
      {apps.length > 0 && (
        <ul className="mt-3 divide-y divide-line">
          {apps.map((a) => (
            <li key={a.id} className="flex flex-wrap items-center justify-between gap-3 py-2.5 text-sm">
              <span><b className="font-medium">{a.company_name}</b>{a.role && <span className="text-ink-muted"> · {a.role}</span>}{a.interview_date && <span className="text-ink-muted"> · interview {new Date(a.interview_date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</span>}</span>
              <span className="flex items-center gap-2">
                <Badge tone={a.status === "offer" ? "green" : a.status === "rejected" ? "red" : "neutral"}>{a.status}</Badge>
                <select className="input h-8 w-auto py-0 text-xs" value={a.status} onChange={(e) => update(a, e.target.value)} aria-label={`Update ${a.company_name} status`}>{STATUSES.map((s) => <option key={s}>{s}</option>)}</select>
                <button onClick={() => remove(a.id)} aria-label={`Delete ${a.company_name}`} className="text-ink-faint hover:text-danger"><Trash2 className="h-4 w-4" /></button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
