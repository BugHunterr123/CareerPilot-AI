import { AppShell } from "@/components/AppShell";

// Every page inside the (app) folder gets the sidebar, step tracker and login guard.
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
