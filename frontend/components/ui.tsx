/** Small shared UI building blocks (our own shadcn-style components). */
import clsx from "clsx";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
const variants: Record<Variant, string> = {
  primary: "bg-accent text-white hover:bg-accent-hover border border-accent",
  secondary: "bg-white text-ink border border-line hover:border-ink-faint hover:bg-paper",
  ghost: "text-ink-soft hover:bg-black/[0.04] border border-transparent",
  danger: "bg-white text-danger border border-danger-line hover:bg-danger-soft",
};
const sizes = { sm: "h-8 px-3 text-[13px]", md: "h-10 px-4 text-sm", lg: "h-11 px-5 text-[15px]" };

export function Button({ variant = "primary", size = "md", busy, className, children, ...rest }:
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: keyof typeof sizes; busy?: boolean }) {
  return (
    <button {...rest} disabled={rest.disabled || busy}
      className={clsx("inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors",
        "disabled:cursor-not-allowed disabled:opacity-60", variants[variant], sizes[size], className)}>
      {busy && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function ButtonLink({ href, variant = "primary", size = "md", className, children }:
  { href: string; variant?: Variant; size?: keyof typeof sizes; className?: string; children: ReactNode }) {
  return (
    <Link href={href} className={clsx("inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors",
      variants[variant], sizes[size], className)}>{children}</Link>
  );
}

export function Card({ className, children, as: Tag = "div", ...rest }: { className?: string; children: ReactNode; as?: "div" | "section" | "article" } & Omit<HTMLAttributes<HTMLElement>, "className" | "children">) {
  return <Tag {...rest} className={clsx("card", className)}>{children}</Tag>;
}

const tones = {
  neutral: "bg-paper text-ink-soft border-line",
  green: "bg-accent-soft text-accent border-accent-line",
  amber: "bg-amber-soft text-amber border-amber-line",
  red: "bg-danger-soft text-danger border-danger-line",
  blue: "bg-info-soft text-info border-info-line",
  outline: "bg-transparent text-ink-muted border-dashed border-ink-faint",
};
export type Tone = keyof typeof tones;
export function Badge({ tone = "neutral", children, className, title }: { tone?: Tone; children: ReactNode; className?: string; title?: string }) {
  return (
    <span title={title} className={clsx("inline-flex items-center gap-1 whitespace-nowrap rounded border px-1.5 py-0.5 text-[11.5px] font-medium leading-4", tones[tone], className)}>
      {children}
    </span>
  );
}

export function Field({ label, hint, error, children, htmlFor, optional }:
  { label: string; hint?: string; error?: string; children: ReactNode; htmlFor?: string; optional?: boolean }) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="flex items-baseline gap-2 text-sm font-medium text-ink">
        {label} {optional && <span className="text-xs font-normal text-ink-faint">Optional</span>}
      </label>
      {children}
      {hint && !error && <p className="text-xs text-ink-muted">{hint}</p>}
      {error && <p className="text-xs text-danger" role="alert">{error}</p>}
    </div>
  );
}

export function ErrorNote({ message, onRetry }: { message?: string | null; onRetry?: () => void }) {
  if (!message) return null;
  return (
    <div role="alert" className="flex items-start justify-between gap-4 rounded-md border border-danger-line bg-danger-soft px-3 py-2.5 text-sm text-danger">
      <span>{message}</span>
      {onRetry && <button onClick={onRetry} className="shrink-0 font-medium underline underline-offset-2">Try again</button>}
    </div>
  );
}

export function Notice({ tone = "neutral", children, className }: { tone?: "neutral" | "amber" | "blue" | "green"; children: ReactNode; className?: string }) {
  const t = { neutral: "border-line bg-paper text-ink-soft", amber: "border-amber-line bg-amber-soft text-[#6E4A10]",
    blue: "border-info-line bg-info-soft text-[#24496D]", green: "border-accent-line bg-accent-soft text-accent" }[tone];
  return <div className={clsx("rounded-md border px-3 py-2.5 text-sm leading-relaxed", t, className)}>{children}</div>;
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("skeleton rounded-md", className)} aria-hidden />;
}

export function PageSkeleton() {
  return (
    <div className="space-y-4" aria-busy="true" aria-label="Loading">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-96 max-w-full" />
      <div className="grid gap-4 md:grid-cols-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-32" />)}</div>
      <Skeleton className="h-56" />
    </div>
  );
}

export function Empty({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-white/60 px-6 py-10 text-center">
      <p className="font-serif text-lg font-semibold text-ink">{title}</p>
      {children && <div className="mx-auto mt-1.5 max-w-md text-sm text-ink-muted">{children}</div>}
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}

export function Meter({ value, className, tone = "green" }: { value: number; className?: string; tone?: "green" | "amber" }) {
  return (
    <div className={clsx("h-1.5 w-full overflow-hidden rounded-full bg-[#ECEAE3]", className)} role="progressbar" aria-valuenow={Math.round(value)} aria-valuemin={0} aria-valuemax={100}>
      <div className={clsx("h-full rounded-full", tone === "green" ? "bg-accent" : "bg-amber")} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}
