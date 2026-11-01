import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Logo } from "@/components/Logo";
import { ButtonLink } from "@/components/ui";
import { SourceLabel } from "@/components/labels";
import { HeroPreview } from "@/components/landing/HeroPreview";

const START = "/register/";

const STEPS = [
  ["Upload your resume", "PDF or DOCX. We pull out skills, projects and education, and you correct anything we got wrong."],
  ["See your real skill evidence", "Each skill is marked claimed, shown in a project, or validated by practice. No inflated levels."],
  ["Compare roles", "Match percentages with the exact formula shown, plus what each role still needs from you."],
  ["Pick a company", "Hiring stages, formats and tips, each line linked to where it came from."],
  ["Get a plan", "Your gaps become dated tasks that fit the hours you actually have each week."],
  ["Practise", "Company-tagged questions with answers. Wrong answers are tracked so you can revisit them."],
  ["Mock interview", "One question at a time, scored on a visible rubric, with a report at the end."],
  ["Track progress", "Completion, accuracy and interview scores from what you actually did."],
];

const PROBLEMS = [
  ["Portals announce, they do not prepare", "Your placement portal tells you a company is coming and who is eligible. It does not tell you what to study for it."],
  ["Prep material is scattered", "Round patterns live in Reddit threads, GfG posts and seniors' WhatsApp messages, with no dates and no way to tell what is current."],
  ["Generic plans waste weeks", "A 90-day DSA sheet does not help when the drive is in three weeks and the test is mostly aptitude and pseudocode."],
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-paper">
      <header className="mx-auto flex h-16 max-w-content items-center justify-between px-4 sm:px-8">
        <Logo />
        <nav className="flex items-center gap-2">
          <ButtonLink href="/login/" variant="ghost" size="sm">Log in</ButtonLink>
          <ButtonLink href={START} size="sm">Sign up</ButtonLink>
        </nav>
      </header>

      <section className="mx-auto grid max-w-content items-center gap-10 px-4 pb-16 pt-8 sm:px-8 lg:grid-cols-[1.05fr_1fr] lg:pt-14">
        <div>
          <p className="label-sm mb-4">For students preparing for campus placements</p>
          <h1 className="h-display text-[36px] leading-[1.12] sm:text-[48px]">
            Your resume, a target company, and a plan you can actually follow.
          </h1>
          <p className="mt-5 max-w-xl text-[17px] leading-relaxed text-ink-soft">
            CareerPilot reads your resume, shows which roles fit and why, explains each company&apos;s hiring rounds with
            sources, and turns your gaps into a day-by-day plan with practice questions and mock interviews.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <ButtonLink href={START} size="lg">Create a free account <ArrowRight className="h-4 w-4" aria-hidden /></ButtonLink>
            <ButtonLink href="#how" variant="secondary" size="lg">See how it works</ButtonLink>
          </div>
          <p className="mt-4 text-sm text-ink-muted">Only your resume is required. GitHub, LinkedIn and LeetCode are optional.</p>
        </div>
        <HeroPreview />
      </section>

      <section className="border-y border-line bg-surface">
        <div className="mx-auto grid max-w-content gap-8 px-4 py-14 sm:px-8 md:grid-cols-3">
          {PROBLEMS.map(([t, d]) => (
            <div key={t}>
              <h2 className="font-serif text-xl font-semibold">{t}</h2>
              <p className="mt-2 text-[15px] leading-relaxed text-ink-muted">{d}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="how" className="mx-auto max-w-content scroll-mt-8 px-4 py-16 sm:px-8">
        <h2 className="h-display text-3xl">How it works</h2>
        <p className="mt-2 max-w-2xl text-ink-muted">Eight steps. The tracker at the top of the app shows where you are.</p>
        <ol className="mt-8 grid gap-x-8 gap-y-7 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map(([t, d], i) => (
            <li key={t} className="border-t border-ink pt-3">
              <span className="font-mono text-xs text-ink-muted">{String(i + 1).padStart(2, "0")}</span>
              <h3 className="mt-1 font-semibold">{t}</h3>
              <p className="mt-1 text-sm leading-relaxed text-ink-muted">{d}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="border-t border-line bg-surface">
        <div className="mx-auto grid max-w-content gap-10 px-4 py-16 sm:px-8 lg:grid-cols-2">
          <div>
            <h2 className="h-display text-3xl">Honest by design</h2>
            <p className="mt-3 text-[15px] leading-relaxed text-ink-soft">
              Hiring processes change by year, role and college. So every company fact in CareerPilot carries a link,
              a date when the page shows one, and a label that tells you how much to trust it. Practice questions we wrote
              ourselves are never passed off as previously asked ones.
            </p>
            <p className="mt-3 text-[15px] leading-relaxed text-ink-soft">
              CareerPilot works alongside your college placement portal. The portal handles applications; we help you get
              ready for them.
            </p>
          </div>
          <dl className="divide-y divide-line rounded-lg border border-line">
            {[["Official", "Published by the company itself."], ["Candidate-reported", "Shared by students who went through it."],
              ["Third-party", "From a prep or education site."], ["AI practice", "Written for practice on a reported topic."]].map(([l, d]) => (
              <div key={l} className="flex items-center justify-between gap-4 px-4 py-3">
                <dt><SourceLabel label={l} /></dt>
                <dd className="text-right text-sm text-ink-muted">{d}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section className="mx-auto max-w-content px-4 py-16 text-center sm:px-8">
        <h2 className="h-display text-3xl">Start with the resume you already have.</h2>
        <p className="mt-2 text-ink-muted">It takes about five minutes to get your first plan.</p>
        <div className="mt-6 flex justify-center gap-3">
          <ButtonLink href={START} size="lg">Create a free account</ButtonLink>
          <ButtonLink href="/login/" variant="secondary" size="lg">Log in</ButtonLink>
        </div>
      </section>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-content flex-col gap-2 px-4 py-6 text-xs text-ink-muted sm:flex-row sm:justify-between sm:px-8">
          <span>CareerPilot AI, built for the IBM Bobathon 2026.</span>
          <span>Mock scores and match percentages are practice indicators, not hiring predictions. <Link className="link" href="/login/">Sign in</Link></span>
        </div>
      </footer>
    </div>
  );
}
