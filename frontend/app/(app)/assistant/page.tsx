"use client";
import Link from "next/link";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { ArrowUp, ExternalLink } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import { useShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Button, ErrorNote, Notice } from "@/components/ui";
import { SourceLabel } from "@/components/labels";
import { RichText } from "@/components/RichText";

type Citation = { title: string; label: string; url: string | null; href?: string | null; kind?: string };
type Msg = { id: number; role: string; content: string; at: string; meta: { citations?: Citation[]; engine?: string; ai_error?: string | null } };
const STARTERS = ["Explain normalisation with an example", "What does the Infosys online test cover?", "Make me a 7-day plan for SQL", "How do I explain my final-year project?"];

export default function AssistantPage() {
  const { meta } = useShell();
  const hist = useApi<Msg[]>("/api/assistant");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { if (hist.data) setMsgs(hist.data); }, [hist.data]);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [msgs.length, busy]);

  async function send(message: string) {
    if (!message.trim() || busy) return;
    setBusy(true); setErr(null); setText("");
    setMsgs((m) => [...m, { id: -Date.now(), role: "user", content: message, at: new Date().toISOString(), meta: {} }]);
    try { const reply = await api<Msg>("/api/assistant", { body: { message } }); setMsgs((m) => [...m, reply]); }
    catch (e) { setErr(e instanceof Error ? e.message : String(e)); setText(message); } finally { setBusy(false); }
  }
  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(text); } };
  return (
    <>
      <PageHeader eyebrow="Career assistant" title="Ask anything about your preparation"
        actions={msgs.length > 0 && <Button size="sm" variant="ghost" onClick={async () => { await api("/api/assistant", { method: "DELETE" }); setMsgs([]); }}>Clear chat</Button>}>
        Concepts, coding doubts, company rounds, your resume, study plans. Company facts only come from CareerPilot&apos;s sourced guides; if they do not cover something, the assistant says so.
      </PageHeader>
      <div className="mx-auto flex max-w-3xl flex-col">
        {meta && !meta.ai_configured && (
          <Notice tone="blue" className="mb-6">AI answers are not switched on for this site yet. You can still ask in your own words: the assistant searches the company guides, question bank and your profile and shows the best matches with links.</Notice>
        )}
        <div className="min-h-[320px] space-y-5" aria-live="polite" data-testid="chat-log">
          {!msgs.length && !hist.loading && (
            <div className="rounded-lg border border-dashed border-line px-6 py-8 text-center">
              <p className="font-serif text-lg font-semibold">Type any question below</p>
              <p className="mt-1 text-sm text-ink-muted">Not sure where to start? Try one of these:</p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">{STARTERS.map((s) => <button key={s} onClick={() => setText(s)} className="rounded-full border border-line bg-white px-3 py-1.5 text-sm text-ink-soft hover:border-ink-faint">{s}</button>)}</div>
            </div>
          )}
          {msgs.map((m) => (
            <div key={m.id} className={clsx("flex", m.role === "user" ? "justify-end" : "justify-start")}>
              <div className={clsx("max-w-[88%] rounded-xl px-4 py-3 text-[14.5px] leading-relaxed", m.role === "user" ? "bg-ink text-white" : "border border-line bg-white")} data-testid={m.role === "assistant" ? "assistant-msg" : "user-msg"}>
                {m.role === "assistant" ? <RichText text={m.content} /> : <p className="whitespace-pre-line">{m.content}</p>}
                {m.meta.citations && m.meta.citations.length > 0 && (
                  <div className="mt-3 space-y-1.5 border-t border-line pt-2.5">
                    {m.meta.citations.map((c) => (
                      <p key={c.title + (c.url ?? "")} className="flex flex-wrap items-center gap-1.5 text-xs text-ink-muted">
                        {c.label && <SourceLabel label={c.label} />}
                        {c.url ? <a href={c.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:text-accent">{c.title}<ExternalLink className="h-3 w-3" aria-hidden /></a>
                          : c.href ? <Link href={c.href} className="hover:text-accent">{c.title}</Link> : c.title}
                        {c.url && c.href && <Link href={c.href} className="text-accent hover:underline">Open in CareerPilot</Link>}
                      </p>
                    ))}
                  </div>
                )}
                {m.role === "assistant" && <p className="mt-2 text-[11.5px] text-ink-faint">{m.meta.engine === "llm" ? "AI answer, grounded in your data and CareerPilot's sources" : "Answered from CareerPilot's sources and your data (AI not used)"}</p>}
              </div>
            </div>
          ))}
          {busy && <div className="flex justify-start"><div className="rounded-xl border border-line bg-white px-4 py-3 text-sm text-ink-muted" role="status">Thinking…</div></div>}
          <div ref={end} />
        </div>
        <div className="mt-4"><ErrorNote message={err} /></div>
        <form onSubmit={(e) => { e.preventDefault(); send(text); }} className="sticky bottom-4 mt-6 flex items-end gap-2 rounded-xl border border-line bg-white p-2 shadow-pop">
          <textarea rows={1} className="max-h-40 min-h-[40px] flex-1 resize-none bg-transparent px-2 py-2 text-[14.5px] outline-none" value={text} onChange={(e) => setText(e.target.value)} onKeyDown={onKey}
            placeholder="Ask your own question, e.g. 'What is a deadlock?'" aria-label="Message" data-testid="chat-input" />
          <Button type="submit" disabled={!text.trim()} busy={busy} aria-label="Send" data-testid="chat-send"><ArrowUp className="h-4 w-4" /></Button>
        </form>
        <p className="mt-2 text-center text-xs text-ink-faint">Enter to send, Shift+Enter for a new line. Chat history is saved to your account.</p>
      </div>
    </>
  );
}
