/** Trust labels used everywhere: where a fact came from and how strong a skill's evidence is. */
import { ExternalLink } from "lucide-react";
import { Badge, type Tone } from "./ui";

const SOURCE_TONE: Record<string, Tone> = {
  Official: "green", "Candidate-reported": "blue", "Third-party": "neutral", "AI practice": "amber", Unverified: "red",
};
const SOURCE_HELP: Record<string, string> = {
  Official: "Published by the company itself.",
  "Candidate-reported": "Written by students who went through the process. Can vary by year and college.",
  "Third-party": "From a prep or education website, not the company.",
  "AI practice": "A practice question written for CareerPilot on a reported topic. Not a previously asked question.",
  Unverified: "We could not confirm this.",
};

export function SourceLabel({ label }: { label: string }) {
  return <Badge tone={SOURCE_TONE[label] ?? "neutral"} title={SOURCE_HELP[label]}>{label}</Badge>;
}

export type SourceRef = { url: string | null; title?: string; publisher?: string; date?: string | null; label: string };

export function SourceLink({ src, compact }: { src?: SourceRef | null; compact?: boolean }) {
  if (!src) return null;
  const when = src.date ? ` · ${src.date}` : " · page undated";
  return (
    <span className="inline-flex flex-wrap items-center gap-1.5 text-xs text-ink-muted">
      {!compact && <SourceLabel label={src.label} />}
      {src.url ? (
        <a href={src.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:text-accent">
          {src.publisher || "Source"}{when}
          <ExternalLink className="h-3 w-3" aria-hidden />
          <span className="sr-only">(opens in a new tab)</span>
        </a>
      ) : (
        <span>{src.publisher}{when}</span>
      )}
    </span>
  );
}

const LEVEL: Record<string, { tone: Tone; text: string; help: string }> = {
  validated: { tone: "green", text: "Validated", help: "You answered practice questions on it correctly." },
  project: { tone: "blue", text: "Project evidence", help: "A project, internship or repository shows you used it." },
  claimed: { tone: "amber", text: "Claimed", help: "Listed on your resume, not yet shown anywhere else." },
  inferred: { tone: "outline", text: "AI-inferred", help: "Not written on your resume. Guessed from a related skill." },
};

export function LevelBadge({ level }: { level: string }) {
  const l = LEVEL[level] ?? LEVEL.claimed;
  return <Badge tone={l.tone} title={l.help}>{l.text}</Badge>;
}
export const LEVEL_INFO = LEVEL;

export function PriorityBadge({ p }: { p: string }) {
  // A quiet dot + word: a list full of red boxes reads as alarm, not as an order of work.
  const dot = p === "high" ? "bg-danger" : p === "medium" ? "bg-amber" : p === "low" ? "bg-ink-faint" : "bg-accent";
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap text-xs text-ink-muted">
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} aria-hidden />
      {p === "done" ? "Already shown" : `${p[0].toUpperCase()}${p.slice(1)} priority`}
    </span>
  );
}
