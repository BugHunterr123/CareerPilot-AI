"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { Logo } from "./Logo";
import { Button, ErrorNote, Field } from "./ui";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [next, setNext] = useState<string | null>(null);

  useEffect(() => {
    const qs = new URLSearchParams(window.location.search);
    const n = qs.get("next");
    if (n && n.startsWith("/") && !n.startsWith("//")) setNext(n);
    if (qs.get("signed_out")) setNotice("You have been logged out. Log in with any account, or create a new one.");
    // Already signed in? Go straight to the app.
    api<{ authenticated: boolean }>("/api/auth/session").then((s) => s.authenticated && router.replace(n && n.startsWith("/") && !n.startsWith("//") ? n : "/dashboard/")).catch(() => {});
  }, [router]);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body = mode === "login" ? { email: form.email, password: form.password } : form;
      await api(`/api/auth/${mode}`, { body }); // the server sets the httpOnly session cookie
      router.push(mode === "register" ? "/onboarding/" : next || "/dashboard/");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-paper px-4 py-10">
      <Link href="/" className="mb-8"><Logo /></Link>
      <div className="card w-full max-w-[400px] p-6 sm:p-8">
        <h1 className="h-display text-2xl">{mode === "login" ? "Welcome back" : "Create your account"}</h1>
        <p className="mt-1 text-sm text-ink-muted">
          {mode === "login" ? "Pick up where you left off." : "Next we will ask for your education and resume. That is all that is required."}
        </p>
        {notice && <p className="mt-4 rounded-md border border-line bg-paper px-3 py-2 text-sm text-ink-soft" role="status">{notice}</p>}
        <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
          {mode === "register" && (
            <Field label="Full name" htmlFor="name">
              <input id="name" className="input" autoComplete="name" value={form.full_name} onChange={set("full_name")} required minLength={2} />
            </Field>
          )}
          <Field label="College email or personal email" htmlFor="email">
            <input id="email" type="email" className="input" autoComplete="email" value={form.email} onChange={set("email")} required />
          </Field>
          <Field label="Password" htmlFor="password" hint={mode === "register" ? "At least 8 characters, with a letter and a number." : undefined}>
            <input id="password" type="password" className="input" autoComplete={mode === "login" ? "current-password" : "new-password"}
              value={form.password} onChange={set("password")} required minLength={mode === "register" ? 8 : 1} />
          </Field>
          <ErrorNote message={error} />
          <Button type="submit" busy={busy} className="w-full">{mode === "login" ? "Log in" : "Create account"}</Button>
        </form>
      </div>
      <p className="mt-5 text-sm text-ink-muted">
        {mode === "login" ? <>New here? <Link className="link" href="/register/">Create an account</Link></>
          : <>Already have an account? <Link className="link" href="/login/">Log in</Link></>}
      </p>
    </div>
  );
}
