"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import type { Link as LinkT, Profile, Resume } from "@/lib/types";
import { Logo } from "@/components/Logo";
import { Button, ErrorNote, Field, Notice } from "@/components/ui";
import { ResumeDrop } from "@/components/ResumeDrop";
import { LinksEditor } from "@/components/LinksEditor";

const STEPS = ["Education", "Resume", "Optional links"];

export default function Onboarding() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [edu, setEdu] = useState({ college: "", degree: "B.E.", branch: "", graduation_year: "", cgpa: "" });
  const [links, setLinks] = useState<LinkT[]>([]);
  const [resume, setResume] = useState<Resume | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadProfile = () => api<{ profile: Profile; links: LinkT[] }>("/api/profile").then((d) => {
    setLinks(d.links);
    setEdu((e) => ({ ...e, college: d.profile.college || e.college, branch: d.profile.branch || e.branch,
      degree: d.profile.degree || e.degree, graduation_year: d.profile.graduation_year ? String(d.profile.graduation_year) : e.graduation_year }));
  });
  useEffect(() => {
    loadProfile().catch(() => {}); // a missing session redirects to /login inside api()
  }, [router]);

  async function saveEducation() {
    if (!edu.college.trim() || !edu.branch.trim() || !edu.graduation_year) return setError("Please fill in college, branch and graduation year.");
    setBusy(true); setError(null);
    try {
      await api("/api/profile", { method: "PUT", body: { ...edu, graduation_year: Number(edu.graduation_year), cgpa: edu.cgpa || null } });
      setStep(1);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(false); }
  }
  async function finish() {
    await api("/api/profile/optional-done", { method: "POST" });
    router.push("/resume/?fresh=1");
  }

  return (
    <div className="min-h-screen bg-paper px-4 py-8">
      <div className="mx-auto max-w-[640px]">
        <Logo />
        <ol className="mt-8 flex items-center gap-2" aria-label="Setup steps">
          {STEPS.map((s, i) => (
            <li key={s} className="flex items-center gap-2 text-sm">
              <span className={clsx("flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold",
                i < step ? "bg-accent text-white" : i === step ? "border border-accent text-accent" : "border border-line text-ink-faint")}>
                {i < step ? <Check className="h-3.5 w-3.5" strokeWidth={3} /> : i + 1}
              </span>
              <span className={i === step ? "font-medium" : "text-ink-muted"}>{s}</span>
              {i < STEPS.length - 1 && <span className="h-px w-6 bg-line" aria-hidden />}
            </li>
          ))}
        </ol>
        <div className="card mt-6 p-6 sm:p-8">
          {step === 0 && (
            <div className="space-y-4">
              <h1 className="h-display text-2xl">Where are you studying?</h1>
              <p className="text-sm text-ink-muted">Companies filter by degree, branch and year, so we need these to match you correctly.</p>
              <Field label="College or university" htmlFor="college"><input id="college" className="input" value={edu.college} onChange={(e) => setEdu({ ...edu, college: e.target.value })} /></Field>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Degree" htmlFor="degree"><input id="degree" className="input" value={edu.degree} onChange={(e) => setEdu({ ...edu, degree: e.target.value })} /></Field>
                <Field label="Branch" htmlFor="branch"><input id="branch" className="input" placeholder="e.g. Computer Science" value={edu.branch} onChange={(e) => setEdu({ ...edu, branch: e.target.value })} /></Field>
                <Field label="Graduation year" htmlFor="year"><input id="year" type="number" className="input" placeholder="2027" value={edu.graduation_year} onChange={(e) => setEdu({ ...edu, graduation_year: e.target.value })} /></Field>
                <Field label="CGPA" htmlFor="cgpa" optional><input id="cgpa" className="input" placeholder="e.g. 8.2" value={edu.cgpa} onChange={(e) => setEdu({ ...edu, cgpa: e.target.value })} /></Field>
              </div>
              <ErrorNote message={error} />
              <div className="flex justify-end"><Button busy={busy} onClick={saveEducation}>Continue</Button></div>
            </div>
          )}
          {step === 1 && (
            <div className="space-y-4">
              <h1 className="h-display text-2xl">Upload your resume</h1>
              <p className="text-sm text-ink-muted">This is the only document we need. You will be able to check and correct everything we read from it.</p>
              {resume ? (
                <Notice tone="green">Read <b>{resume.filename}</b>: {resume.parsed.skills.length} skills and {resume.projects.length} projects found.</Notice>
              ) : <ResumeDrop onDone={setResume} />}
              <div className="flex justify-between">
                <Button variant="ghost" onClick={() => setStep(0)}>Back</Button>
                <Button disabled={!resume} onClick={() => setStep(2)}>Continue</Button>
              </div>
            </div>
          )}
          {step === 2 && (
            <div className="space-y-4">
              <h1 className="h-display text-2xl">Anything else? (optional)</h1>
              <p className="text-sm text-ink-muted">Extra profiles can make your skill report more accurate. If you do not have them, skip this. Everything works with just your resume.</p>
              <LinksEditor links={links} onChange={loadProfile} />
              <div className="flex justify-between">
                <Button variant="ghost" onClick={() => setStep(1)}>Back</Button>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={finish}>Skip for now</Button>
                  <Button onClick={finish}>Review my resume</Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
