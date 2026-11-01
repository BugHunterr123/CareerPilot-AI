import { BarChart3, Briefcase, Building2, CalendarCheck, FileText, LayoutDashboard, ListChecks, MessageSquare,
  Mic, Settings, Sparkles, Target, Timer, User } from "lucide-react";

// Sidebar navigation, grouped the way a student moves through the app (spec section 25).
export const NAV = [
  { title: "Overview", items: [{ href: "/dashboard/", label: "Dashboard", icon: LayoutDashboard }] },
  { title: "You", items: [
    { href: "/profile/", label: "My Profile", icon: User },
    { href: "/resume/", label: "Resume Analysis", icon: FileText },
    { href: "/skills/", label: "Skill Intelligence", icon: Sparkles },
    { href: "/careers/", label: "Career Recommendations", icon: Briefcase },
  ] },
  { title: "Prepare", items: [
    { href: "/companies/", label: "Company Explorer", icon: Building2 },
    { href: "/gaps/", label: "Skill Gap Analysis", icon: Target },
    { href: "/roadmap/", label: "Preparation Roadmap", icon: CalendarCheck },
    { href: "/practice/", label: "Practice Questions", icon: ListChecks, exact: true },
    { href: "/practice/test/", label: "Timed Tests", icon: Timer },
    { href: "/interview/", label: "Mock Interviews", icon: Mic },
  ] },
  { title: "Track", items: [
    { href: "/progress/", label: "Progress Tracking", icon: BarChart3 },
    { href: "/assistant/", label: "Career Assistant", icon: MessageSquare },
    { href: "/settings/", label: "Settings", icon: Settings },
  ] },
];
