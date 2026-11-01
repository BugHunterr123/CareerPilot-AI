import type { ReactNode } from "react";

export function PageHeader({ eyebrow, title, children, actions }: { eyebrow?: string; title: string; children?: ReactNode; actions?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-col gap-4 border-b border-line pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="max-w-2xl">
        {eyebrow && <p className="label-sm mb-1.5">{eyebrow}</p>}
        <h1 className="h-display text-[28px] leading-tight sm:text-[32px]">{title}</h1>
        {children && <div className="mt-2 text-[15px] leading-relaxed text-ink-muted">{children}</div>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
    </header>
  );
}
