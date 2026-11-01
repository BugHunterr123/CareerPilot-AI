/** Wordmark: a simple heading mark (a needle pointing north-east) + serif name. */
export function Logo({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden>
        <rect x="1" y="1" width="22" height="22" rx="6" fill="#1F5C46" />
        <path d="M7 17 L12.5 11.5 L17 7 L14.6 13.4 L12.5 11.5 L10.6 9.4 Z" fill="#F7F6F2" />
      </svg>
      <span className="font-serif text-[19px] font-semibold tracking-tight text-ink">CareerPilot</span>
    </span>
  );
}
