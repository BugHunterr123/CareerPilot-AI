"use client";
/**
 * The frame around every logged-in page: sidebar, the 8-step journey tracker,
 * the account menu (log out), and the login guard (no session -> /login).
 */
import clsx from "clsx";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { ChevronUp, KeyRound, LogOut, Menu, X } from "lucide-react";
import { api, logout } from "@/lib/api";
import type { JourneyStep, Meta, User } from "@/lib/types";
import { Logo } from "./Logo";
import { NAV } from "./nav";
import { StepTracker } from "./StepTracker";

type Shell = { user: User | null; meta: Meta | null; journey: JourneyStep[]; refresh: () => void };
const ShellContext = createContext<Shell>({ user: null, meta: null, journey: [], refresh: () => {} });
export const useShell = () => useContext(ShellContext);

export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [journey, setJourney] = useState<JourneyStep[]>([]);
  const [open, setOpen] = useState(false);
  const [menu, setMenu] = useState(false);
  const [checked, setChecked] = useState(false);

  const refresh = useCallback(() => {
    api<JourneyStep[]>("/api/journey").then(setJourney).catch(() => {});
  }, []);

  // Check the session first (always a 200), and only then load anything that needs a login.
  useEffect(() => {
    api<{ authenticated: boolean; user: User | null }>("/api/auth/session")
      .then((s) => {
        if (s.authenticated && s.user) { setUser(s.user); setChecked(true); }
        else router.replace(`/login/?next=${encodeURIComponent(pathname || "/dashboard/")}`);
      })
      .catch(() => setChecked(true));
    api<Meta>("/api/meta").then(setMeta).catch(() => {});
  }, [router, pathname]);

  useEffect(() => {
    if (user) refresh();
    setOpen(false);
    setMenu(false);
  }, [pathname, refresh, user]);

  if (!checked) {
    return <div className="flex min-h-screen items-center justify-center bg-paper text-sm text-ink-muted" role="status">Loading your workspace…</div>;
  }

  return (
    <ShellContext.Provider value={{ user, meta, journey, refresh }}>
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2">Skip to content</a>
      <div className="min-h-screen lg:grid lg:grid-cols-[248px_1fr]">
        {/* Sidebar (the wrapper is the grid cell, so its background runs the full page height) */}
        <div className="lg:border-r lg:border-line lg:bg-surface">
        <aside className={clsx("fixed inset-y-0 left-0 z-40 w-[248px] border-r border-line bg-surface transition-transform lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 lg:border-r-0",
          open ? "translate-x-0" : "-translate-x-full")} aria-label="Main navigation">
          <div className="flex h-full flex-col">
            <div className="flex h-14 items-center justify-between px-5">
              <Link href="/dashboard/" aria-label="CareerPilot dashboard"><Logo /></Link>
              <button className="rounded p-1 text-ink-muted lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu"><X className="h-5 w-5" /></button>
            </div>
            <nav className="flex-1 overflow-y-auto px-3 pb-4">
              {NAV.map((group) => (
                <div key={group.title} className="mt-4">
                  <p className="px-2 pb-1 text-[11px] font-medium uppercase tracking-wider text-ink-faint">{group.title}</p>
                  {group.items.map((item) => {
                    const base = item.href.replace(/\/$/, "");
                    const active = "exact" in item && item.exact
                      ? pathname === item.href || pathname === base
                      : !!pathname?.startsWith(base);
                    const Icon = item.icon;
                    return (
                      <Link key={item.href} href={item.href} aria-current={active ? "page" : undefined}
                        className={clsx("flex items-center gap-2.5 rounded-md px-2 py-[7px] text-[13.5px] transition-colors",
                          active ? "bg-accent-soft font-medium text-accent" : "text-ink-soft hover:bg-black/[0.035] hover:text-ink")}>
                        <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} aria-hidden />
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              ))}
            </nav>
            <div className="relative border-t border-line p-3">
              {menu && (
                <div className="absolute bottom-[calc(100%-4px)] left-3 right-3 z-10 overflow-hidden rounded-lg border border-line bg-surface shadow-lg" role="menu">
                  <Link href="/settings/" role="menuitem" className="flex items-center gap-2 px-3 py-2.5 text-sm text-ink-soft hover:bg-paper"><KeyRound className="h-4 w-4" aria-hidden />Account and password</Link>
                  <button role="menuitem" onClick={() => logout()} className="flex w-full items-center gap-2 border-t border-line px-3 py-2.5 text-left text-sm text-danger hover:bg-paper"><LogOut className="h-4 w-4" aria-hidden />Log out</button>
                </div>
              )}
              <button onClick={() => setMenu(!menu)} aria-expanded={menu} aria-haspopup="menu" data-testid="user-menu"
                className="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left hover:bg-black/[0.035]">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent-soft text-[13px] font-semibold text-accent" aria-hidden>
                  {(user?.full_name || "?").trim().split(/\s+/).map((p) => p[0]).slice(0, 2).join("").toUpperCase()}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-ink">{user?.full_name}</span>
                  <span className="block truncate text-xs text-ink-muted">{user?.email}</span>
                </span>
                <ChevronUp className={clsx("h-4 w-4 shrink-0 text-ink-faint transition-transform", !menu && "rotate-180")} aria-hidden />
              </button>
            </div>
          </div>
        </aside>
        </div>
        {open && <div className="fixed inset-0 z-30 bg-black/20 lg:hidden" onClick={() => setOpen(false)} aria-hidden />}

        <div className="min-w-0">
          <div className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-line bg-paper/95 px-4 backdrop-blur lg:hidden">
            <button onClick={() => setOpen(true)} className="rounded p-1.5 text-ink-soft" aria-label="Open menu"><Menu className="h-5 w-5" /></button>
            <Logo />
            <button onClick={() => logout()} className="ml-auto rounded-md px-2 py-1 text-sm text-ink-muted hover:text-ink" aria-label="Log out">Log out</button>
          </div>
          <StepTracker steps={journey} />
          <main id="main" className="mx-auto w-full max-w-content px-4 pb-16 pt-6 sm:px-8">{children}</main>
        </div>
      </div>
    </ShellContext.Provider>
  );
}
