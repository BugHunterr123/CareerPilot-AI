"use client";
import clsx from "clsx";
import { FileUp } from "lucide-react";
import { useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Resume } from "@/lib/types";
import { Button, ErrorNote } from "./ui";

/** Drag-and-drop (or click) resume upload with client-side checks mirroring the server's. */
export function ResumeDrop({ onDone, maxMb = 5 }: { onDone: (r: Resume) => void; maxMb?: number }) {
  const input = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState<string | null>(null);

  async function upload(file: File) {
    setError(null);
    if (!/\.(pdf|docx)$/i.test(file.name)) return setError("Please choose a PDF or DOCX file.");
    if (file.size > maxMb * 1024 * 1024) return setError(`That file is larger than ${maxMb} MB.`);
    setName(file.name);
    setBusy(true);
    const form = new FormData();
    form.append("file", file);
    try {
      onDone(await api<Resume>("/api/resume", { form }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <div onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) upload(f); }}
        className={clsx("flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors",
          drag ? "border-accent bg-accent-soft" : "border-line bg-paper/50")}>
        <FileUp className="h-7 w-7 text-ink-muted" strokeWidth={1.5} aria-hidden />
        <p className="mt-3 text-sm font-medium">{busy ? `Reading ${name}...` : "Drop your resume here"}</p>
        <p className="mt-1 text-xs text-ink-muted">PDF or DOCX, up to {maxMb} MB. Text-based files work best.</p>
        <Button type="button" variant="secondary" size="sm" className="mt-4" busy={busy} onClick={() => input.current?.click()}>
          {busy ? "Analysing" : "Choose file"}
        </Button>
        <input ref={input} type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="sr-only" aria-label="Upload resume" onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = ""; }} />
      </div>
      <ErrorNote message={error} />
      <p className="text-xs text-ink-muted">No resume handy? <a href="/api/resume/sample" className="link" download>Download a synthetic sample resume</a> (a made-up student, for trying the app) and upload it here.</p>
    </div>
  );
}
