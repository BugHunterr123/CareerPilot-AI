import Link from "next/link";
import { Logo } from "@/components/Logo";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-paper px-4 text-center">
      <Logo />
      <h1 className="h-display text-3xl">This page does not exist.</h1>
      <p className="text-ink-muted">The link may be old. Your dashboard has everything.</p>
      <Link href="/dashboard/" className="link">Go to dashboard</Link>
    </div>
  );
}
