/**
 * Very small, safe renderer for chat answers: ``` code blocks, `inline code`, **bold** and "- " lists.
 * Everything else is plain text (React escapes it), so model output can never inject HTML.
 */
import type { ReactNode } from "react";

function inline(text: string, key: string): ReactNode[] {
  return text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).map((part, i) => {
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2)
      return <code key={`${key}-${i}`} className="rounded bg-paper px-1 py-0.5 font-mono text-[0.88em]">{part.slice(1, -1)}</code>;
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) return <strong key={`${key}-${i}`} className="font-semibold">{part.slice(2, -2)}</strong>;
    return part;
  });
}

export function RichText({ text }: { text: string }) {
  const blocks = text.split(/```[a-zA-Z0-9+#-]*\n?/);
  return (
    <div className="space-y-2">
      {blocks.map((b, bi) => {
        if (bi % 2 === 1) return <pre key={bi} className="overflow-x-auto rounded-md border border-line bg-paper px-3 py-2 font-mono text-[12.5px] leading-relaxed">{b.replace(/\n$/, "")}</pre>;
        const paras = b.split(/\n{2,}/).filter((p) => p.trim());
        return paras.map((p, pi) => {
          const lines = p.split("\n");
          if (lines.every((l) => /^\s*([-*•]|\d+[.)])\s+/.test(l) || !l.trim()))
          {
            const items = lines.filter((l) => l.trim()).map((l, li) => <li key={li}>{inline(l.replace(/^\s*([-*•]|\d+[.)])\s+/, ""), `${bi}-${pi}-${li}`)}</li>);
            return /^\s*\d/.test(lines[0])
              ? <ol key={`${bi}-${pi}`} className="list-decimal space-y-1 pl-5">{items}</ol>
              : <ul key={`${bi}-${pi}`} className="list-disc space-y-1 pl-5">{items}</ul>;
          }
          return <p key={`${bi}-${pi}`} className="whitespace-pre-line">{inline(p, `${bi}-${pi}`)}</p>;
        });
      })}
    </div>
  );
}
