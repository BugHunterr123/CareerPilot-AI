"use client";
/**
 * A lightweight code editor (CodeMirror 6) with Python highlighting.
 * Loaded only in the browser; falls back to a plain textarea while it loads.
 */
import { useEffect, useRef } from "react";

export function CodeEditor({ value, onChange, label = "Code editor", minHeight = 260 }:
  { value: string; onChange: (v: string) => void; label?: string; minHeight?: number }) {
  const host = useRef<HTMLDivElement>(null);
  const view = useRef<import("@codemirror/view").EditorView | null>(null);
  const latest = useRef(onChange);
  latest.current = onChange;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [{ EditorView, keymap }, { basicSetup }, { python }, { indentWithTab }] = await Promise.all([
        import("@codemirror/view"), import("codemirror"), import("@codemirror/lang-python"), import("@codemirror/commands"),
      ]);
      if (cancelled || !host.current) return;
      const theme = EditorView.theme({
        "&": { fontSize: "13.5px", backgroundColor: "#FFFFFF", minHeight: `${minHeight}px` },
        ".cm-scroller": { fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace", lineHeight: "1.6" },
        ".cm-content": { padding: "10px 0", minHeight: `${minHeight}px` },
        ".cm-gutters": { backgroundColor: "#FAF9F6", color: "#9A978E", borderRight: "1px solid #E6E3DA" },
        ".cm-activeLine": { backgroundColor: "#F6F8F5" }, ".cm-activeLineGutter": { backgroundColor: "#EEF3EF" },
        "&.cm-focused": { outline: "none" },
      });
      view.current = new EditorView({
        parent: host.current,
        doc: value,
        extensions: [basicSetup, python(), keymap.of([indentWithTab]), theme,
          EditorView.contentAttributes.of({ "aria-label": label }),
          EditorView.updateListener.of((u) => { if (u.docChanged) latest.current(u.state.doc.toString()); })],
      });
    })();
    return () => { cancelled = true; view.current?.destroy(); view.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Replace the document when the parent swaps the code (e.g. "Reset to starter").
  useEffect(() => {
    const v = view.current;
    if (v && v.state.doc.toString() !== value) v.dispatch({ changes: { from: 0, to: v.state.doc.length, insert: value } });
  }, [value]);

  return <div ref={host} className="overflow-hidden rounded-md border border-line focus-within:border-accent" data-testid="code-editor" />;
}
