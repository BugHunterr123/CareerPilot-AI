"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAction, useApi } from "@/lib/hooks";
import type { Link as LinkT, Profile, User } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { ChipsInput } from "@/components/ChipsInput";
import { LinksEditor } from "@/components/LinksEditor";
import { Button, Card, ErrorNote, Field, PageSkeleton } from "@/components/ui";

type Data = { user: User; profile: Profile; links: LinkT[] };

export default function ProfilePage() {
  const { data, loading, error, reload } = useApi<Data>("/api/profile");
  const [f, setF] = useState<Record<string, any> | null>(null);
  const act = useAction();
  const [ok, setOk] = useState(false);
  useEffect(() => { if (data && !f) setF({ full_name: data.user.full_name, ...data.profile }); }, [data, f]);
  if ((loading && !data) || !f) return error ? <ErrorNote message={error.message} /> : <PageSkeleton />;
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value });
  const save = () => act.run(async () => {
    setOk(false);
    await api("/api/profile", { method: "PUT", body: {
      full_name: f.full_name, college: f.college, degree: f.degree, branch: f.branch, cgpa: f.cgpa || null,
      graduation_year: f.graduation_year ? Number(f.graduation_year) : null, interests: f.interests, preferred_roles: f.preferred_roles,
      preferred_locations: f.preferred_locations, job_type: f.job_type || null, weekly_hours: f.weekly_hours ? Number(f.weekly_hours) : null,
      target_date: f.target_date || null } });
    setOk(true);
  });
  return (
    <>
      <PageHeader eyebrow="My profile" title="Your details">Education is required. Everything under Preferences is optional and only used to personalise suggestions.</PageHeader>
      <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        <div className="space-y-6">
          <Card className="space-y-4 p-5">
            <h2 className="font-serif text-lg font-semibold">Education</h2>
            <Field label="Full name" htmlFor="fn"><input id="fn" className="input" value={f.full_name ?? ""} onChange={set("full_name")} /></Field>
            <Field label="College" htmlFor="col"><input id="col" className="input" value={f.college ?? ""} onChange={set("college")} /></Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Degree" htmlFor="deg"><input id="deg" className="input" value={f.degree ?? ""} onChange={set("degree")} /></Field>
              <Field label="Branch" htmlFor="br"><input id="br" className="input" value={f.branch ?? ""} onChange={set("branch")} /></Field>
              <Field label="Graduation year" htmlFor="gy"><input id="gy" type="number" className="input" value={f.graduation_year ?? ""} onChange={set("graduation_year")} /></Field>
              <Field label="CGPA" htmlFor="cg" optional><input id="cg" className="input" value={f.cgpa ?? ""} onChange={set("cgpa")} /></Field>
            </div>
          </Card>
          <Card className="space-y-4 p-5">
            <h2 className="font-serif text-lg font-semibold">Preferences <span className="text-sm font-normal text-ink-faint">Optional</span></h2>
            <Field label="Career interests" hint="e.g. backend, data, AI"><ChipsInput label="Career interests" value={f.interests ?? []} onChange={(v) => setF({ ...f, interests: v })} placeholder="Add an interest" /></Field>
            <Field label="Preferred locations"><ChipsInput label="Preferred locations" value={f.preferred_locations ?? []} onChange={(v) => setF({ ...f, preferred_locations: v })} placeholder="e.g. Bengaluru" /></Field>
            <div className="grid gap-4 sm:grid-cols-3">
              <Field label="Looking for" htmlFor="jt"><select id="jt" className="input" value={f.job_type ?? ""} onChange={set("job_type")}><option value="">Not set</option><option value="full-time">Full-time</option><option value="internship">Internship</option><option value="both">Both</option><option value="apprenticeship">Apprenticeship</option></select></Field>
              <Field label="Hours per week" htmlFor="wh"><input id="wh" type="number" className="input" value={f.weekly_hours ?? ""} onChange={set("weekly_hours")} /></Field>
              <Field label="Next test date" htmlFor="td"><input id="td" type="date" className="input" value={f.target_date ?? ""} onChange={set("target_date")} /></Field>
            </div>
          </Card>
          <div className="flex items-center gap-3"><Button busy={act.busy} onClick={save}>Save profile</Button>{ok && <span className="text-sm text-accent" role="status">Saved.</span>}</div>
          <ErrorNote message={act.error} />
        </div>
        <div>
          <h2 className="mb-1 font-serif text-lg font-semibold">Optional profiles</h2>
          <p className="mb-3 text-sm text-ink-muted">Add them only if you have them. Your recommendations work without any of these.</p>
          <LinksEditor links={data?.links ?? []} onChange={reload} />
        </div>
      </div>
    </>
  );
}
