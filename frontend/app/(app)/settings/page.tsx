"use client";
import { useState, type FormEvent } from "react";
import { api, logout } from "@/lib/api";
import { useAction } from "@/lib/hooks";
import { useShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Button, Card, ErrorNote, Field } from "@/components/ui";

function PasswordCard() {
  const [f, setF] = useState({ current_password: "", new_password: "", confirm: "" });
  const [done, setDone] = useState<string | null>(null);
  const act = useAction();
  const submit = (e: FormEvent) => {
    e.preventDefault();
    setDone(null);
    if (f.new_password !== f.confirm) { act.setError("The two new passwords do not match."); return; }
    act.run(async () => {
      const r = await api<{ message: string }>("/api/auth/password", { body: { current_password: f.current_password, new_password: f.new_password } });
      setDone(r.message);
      setF({ current_password: "", new_password: "", confirm: "" });
    });
  };
  return (
    <Card className="p-6">
      <h2 className="font-serif text-lg font-semibold">Change password</h2>
      <form onSubmit={submit} className="mt-4 grid gap-4 sm:grid-cols-3">
        <Field label="Current password" htmlFor="cur"><input id="cur" type="password" autoComplete="current-password" className="input" value={f.current_password} onChange={(e) => setF({ ...f, current_password: e.target.value })} /></Field>
        <Field label="New password" htmlFor="new" hint="8+ characters, a letter and a number"><input id="new" type="password" autoComplete="new-password" className="input" value={f.new_password} onChange={(e) => setF({ ...f, new_password: e.target.value })} /></Field>
        <Field label="Repeat new password" htmlFor="rep"><input id="rep" type="password" autoComplete="new-password" className="input" value={f.confirm} onChange={(e) => setF({ ...f, confirm: e.target.value })} /></Field>
        <div className="sm:col-span-3 flex flex-wrap items-center gap-3">
          <Button type="submit" busy={act.busy} disabled={!f.current_password || !f.new_password}>Update password</Button>
          {done && <span className="text-sm text-accent" role="status">{done}</span>}
        </div>
      </form>
      <div className="mt-3"><ErrorNote message={act.error} /></div>
    </Card>
  );
}

export default function SettingsPage() {
  const { meta, user } = useShell();
  const [pw, setPw] = useState("");
  const act = useAction();
  const exportData = () => act.run(async () => {
    const data = await api("/api/privacy/export");
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = "careerpilot-my-data.json"; a.click();
  });
  const del = () => act.run(async () => {
    await api("/api/privacy/account", { method: "DELETE", body: { password: pw } });
    window.location.href = "/?deleted=1";
  });
  return (
    <>
      <PageHeader eyebrow="Settings" title="Account and privacy" />
      <div className="max-w-3xl space-y-6">
        <Card className="flex flex-wrap items-center justify-between gap-4 p-6">
          <div>
            <h2 className="font-serif text-lg font-semibold">Signed in</h2>
            <p className="mt-1 text-sm text-ink-muted">{user?.full_name} · {user?.email}</p>
          </div>
          <Button variant="secondary" onClick={() => logout()} data-testid="settings-logout">Log out</Button>
        </Card>
        <PasswordCard />
        <Card className="p-6">
          <h2 className="font-serif text-lg font-semibold">How analysis runs</h2>
          <div className="mt-3 space-y-2 text-sm">
            <p className="flex flex-wrap items-center gap-2">AI provider: {meta?.ai_configured
              ? <Badge tone="green">{meta.ai_provider === "gemini" ? "Google Gemini" : "OpenAI-compatible"} · {meta.ai_model}</Badge>
              : <Badge tone="amber">Not configured</Badge>}</p>
            {meta?.ai_configured
              ? <p className="text-ink-muted">Assistant answers, interview questions and interview feedback come from the AI model. Company facts are still limited to CareerPilot&apos;s sourced guides.</p>
              : <p className="text-ink-muted">This server has no AI key yet, so the assistant answers from CareerPilot&apos;s sourced content and your data, and interviews use the rule-based rubric. Every result says which engine produced it. The site admin turns AI on by setting <code className="rounded bg-paper px-1">GEMINI_API_KEY</code> in the server environment.</p>}
            <p className="text-ink-muted">Code runner: Python, {meta?.code_runner?.timeout_seconds ?? 4} s per test. Resume upload limit: {meta?.max_upload_mb ?? 5} MB, PDF or DOCX.</p>
          </div>
        </Card>
        <Card className="p-6">
          <h2 className="font-serif text-lg font-semibold">Your data</h2>
          <p className="mt-1 text-sm text-ink-muted">We store your profile, resume, extracted skills, plans, practice attempts and interview answers so the app can work. We never store passwords for GitHub, LinkedIn or LeetCode, and we do not use personal characteristics in recommendations.</p>
          <Button variant="secondary" className="mt-4" onClick={exportData} busy={act.busy}>Download my data (JSON)</Button>
        </Card>
        <Card className="border-danger-line p-6">
          <h2 className="font-serif text-lg font-semibold text-danger">Delete account</h2>
          <p className="mt-1 text-sm text-ink-muted">This removes your account, resume file and every record linked to you. It cannot be undone.</p>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex-1"><Field label="Confirm with your password" htmlFor="pw"><input id="pw" type="password" className="input" value={pw} onChange={(e) => setPw(e.target.value)} /></Field></div>
            <Button variant="danger" disabled={!pw} onClick={del}>Delete everything</Button>
          </div>
        </Card>
        <ErrorNote message={act.error} />
      </div>
    </>
  );
}
