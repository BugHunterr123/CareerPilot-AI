"use client";
import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import type { Project, Resume } from "@/lib/types";
import { ChipsInput } from "../ChipsInput";
import { Button, Card, ErrorNote, Field, Notice } from "../ui";

/** Lets the student correct what the parser extracted. Their version is what the rest of the app uses. */
export function ReviewForm({ resume, onSaved }: { resume: Resume; onSaved: (r: Resume) => void }) {
  const p = resume.parsed;
  const [skills, setSkills] = useState<string[]>(p.skills);
  const [projects, setProjects] = useState<Project[]>(p.projects.map((x) => ({ ...x })));
  const [certs, setCerts] = useState<string[]>(p.certifications);
  const [ach, setAch] = useState<string[]>(p.achievements);
  const [edu, setEdu] = useState(p.education.map((e) => ({ degree: e.degree, institution: e.institution, year: e.year, score: e.score })));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const setProject = (i: number, patch: Partial<Project>) => setProjects(projects.map((x, j) => (j === i ? { ...x, ...patch } : x)));

  async function save() {
    setBusy(true); setError(null); setSaved(false);
    try {
      const r = await api<Resume>("/api/resume/review", { method: "PUT", body: { skills, projects, education: edu, certifications: certs, achievements: ach } });
      setSaved(true);
      onSaved(r);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(false); }
  }

  return (
    <Card className="p-5 sm:p-6">
      <h2 className="font-serif text-xl font-semibold">Check what we read</h2>
      <p className="mt-1 text-sm text-ink-muted">Fix anything wrong or missing. Saving updates your skills, role matches and plan inputs.</p>
      <div className="mt-5 space-y-6">
        <Field label="Skills" hint="Press Enter after each one. Remove anything you would not want to be asked about.">
          <ChipsInput label="Skills" value={skills} onChange={setSkills} placeholder="Add a skill" />
        </Field>
        <div>
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Projects</p>
            <Button size="sm" variant="ghost" onClick={() => setProjects([...projects, { name: "", description: "", technologies: [] }])}><Plus className="h-4 w-4" /> Add project</Button>
          </div>
          <div className="mt-2 space-y-3">
            {projects.map((pr, i) => (
              <div key={i} className="rounded-md border border-line p-3">
                <div className="flex gap-2">
                  <input className="input font-medium" value={pr.name} onChange={(e) => setProject(i, { name: e.target.value })} aria-label={`Project ${i + 1} name`} placeholder="Project name" />
                  <button onClick={() => setProjects(projects.filter((_, j) => j !== i))} className="px-2 text-ink-faint hover:text-danger" aria-label={`Remove project ${pr.name}`}><Trash2 className="h-4 w-4" /></button>
                </div>
                <textarea className="input mt-2 min-h-[72px]" value={pr.description} onChange={(e) => setProject(i, { description: e.target.value })} aria-label={`Project ${i + 1} description`} placeholder="What you built and what you did" />
                <div className="mt-2"><ChipsInput label={`Project ${i + 1} technologies`} value={pr.technologies} onChange={(t) => setProject(i, { technologies: t })} placeholder="Technologies" /></div>
              </div>
            ))}
            {!projects.length && <Notice tone="amber">No projects found. Projects are the strongest evidence of your skills, so add at least one if you have it.</Notice>}
          </div>
        </div>
        <div>
          <p className="text-sm font-medium">Education</p>
          {edu.map((e, i) => (
            <div key={i} className="mt-2 grid gap-2 sm:grid-cols-[1.2fr_1.5fr_0.6fr_0.8fr]">
              {(["degree", "institution", "year", "score"] as const).map((k) => (
                <input key={k} className="input" value={e[k]} placeholder={k} aria-label={`Education ${i + 1} ${k}`}
                  onChange={(ev) => setEdu(edu.map((x, j) => (j === i ? { ...x, [k]: ev.target.value } : x)))} />
              ))}
            </div>
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Certifications"><ChipsInput label="Certifications" value={certs} onChange={setCerts} placeholder="Add a certification" /></Field>
          <Field label="Achievements"><ChipsInput label="Achievements" value={ach} onChange={setAch} placeholder="Add an achievement" /></Field>
        </div>
        <ErrorNote message={error} />
        <div className="flex items-center gap-3">
          <Button busy={busy} onClick={save}>Save and update my analysis</Button>
          {saved && <span className="text-sm text-accent" role="status">Saved. Skills and role matches are updated.</span>}
        </div>
      </div>
    </Card>
  );
}
