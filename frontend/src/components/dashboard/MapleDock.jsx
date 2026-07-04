import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Sparkles, Send, X, Maximize2, Bot, User, ShieldCheck } from "lucide-react";
import { useMaple } from "@/context/MapleContext";

/**
 * MapleDock — Persistent floating companion with sovereign presence.
 *
 * Present on every app screen (except /app/chat full view). The dock is
 * page-aware: it knows which section the user is viewing and can provide
 * contextual prompts. Implements the 'Sovereign UI Architect' pattern.
 */

// Page-contextual suggestions for the dock
const PAGE_SUGGESTIONS = {
  "/app": ["What should I focus on today?", "Explain my next deadline"],
  "/app/assessment": ["What's my CRS score outlook?", "How do I boost my score?"],
  "/app/jobs": ["Which jobs are LMIA-exempt?", "What's a PNP-friendly role?"],
  "/app/legal": ["Do I qualify for free legal aid?", "How do I verify an RCIC?"],
  "/app/communities": ["Settlement services near me?", "Find newcomer groups"],
  "/app/accessibilities": ["How do I get a SIN?", "Best newcomer bank account?"],
  "/app/profile": ["What deadlines should I track?", "Review my status"],
};

export function MapleDock() {
  const { messages, sending, open, setOpen, send, currentPage } = useMaple();
  const [input, setInput] = useState("");
  const endRef = useRef(null);
  const { pathname } = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending, open]);

  // The full chat page already renders the conversation — no floating dock there.
  if (pathname === "/app/chat") return null;

  const submit = (e) => {
    e.preventDefault();
    const t = input.trim();
    if (!t) return;
    setInput("");
    send(t);
  };

  const suggestions = PAGE_SUGGESTIONS[pathname] || PAGE_SUGGESTIONS["/app"];

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          data-testid="maple-dock-launcher"
          className="fixed bottom-5 right-5 z-40 flex items-center gap-2 rounded-full bg-brand-600 px-4 py-3 text-white shadow-xl shadow-brand-600/30 transition-transform hover:-translate-y-0.5"
        >
          <Sparkles className="h-5 w-5" />
          <span className="hidden text-sm font-semibold sm:inline">Ask Maple</span>
        </button>
      )}

      {open && (
        <div
          data-testid="maple-dock"
          className="fixed bottom-5 right-5 z-40 flex h-[560px] max-h-[80vh] w-[calc(100vw-2.5rem)] max-w-sm flex-col overflow-hidden rounded-3xl border border-border bg-card shadow-2xl"
        >
          <header className="flex items-center gap-2 bg-brand-600 px-4 py-3 text-white">
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-white/15"><Sparkles className="h-4 w-4" /></div>
            <div className="min-w-0 flex-1">
              <p className="font-display text-sm font-semibold leading-none">Maple</p>
              <p className="mt-0.5 text-[11px] text-white/70">Newcomers in Canada Wingman</p>
            </div>
            <button onClick={() => { setOpen(false); navigate("/app/chat"); }} data-testid="maple-dock-expand" title="Open full chat" className="grid h-8 w-8 place-items-center rounded-lg hover:bg-white/15"><Maximize2 className="h-4 w-4" /></button>
            <button onClick={() => setOpen(false)} data-testid="maple-dock-close" title="Close" className="grid h-8 w-8 place-items-center rounded-lg hover:bg-white/15"><X className="h-4 w-4" /></button>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto p-3">
            {messages.length === 0 && (
              <div className="grid h-full place-items-center px-4 text-center text-sm text-muted-foreground">
                <div>
                  <div className="mx-auto mb-3 grid h-11 w-11 place-items-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/10"><Sparkles className="h-5 w-5" /></div>
                  <p className="font-medium text-foreground mb-2">Sovereign immigration intelligence</p>
                  <p className="text-xs mb-3">Every answer is grounded in IRCC law and cited to source.</p>
                  {/* Page-contextual quick suggestions */}
                  <div className="space-y-1.5">
                    {suggestions.map((s) => (
                      <button key={s} onClick={() => send(s)} className="block w-full rounded-lg border border-border px-3 py-1.5 text-left text-xs hover:border-brand-500 hover:text-brand-600 transition-colors">
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-2 ${m.role === "user" ? "flex-row-reverse" : ""}`} data-testid={`dock-msg-${m.role}`}>
                <div className={`grid h-7 w-7 shrink-0 place-items-center rounded-lg ${m.role === "user" ? "bg-brand-500 text-white" : "bg-maple text-white"}`}>
                  {m.role === "user" ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
                </div>
                <div className={`max-w-[82%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm ${m.role === "user" ? "bg-brand-500 text-white" : "bg-secondary text-foreground"}`}>
                  {m.content || <span className="inline-flex gap-1"><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current" /><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:0.15s]" /><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:0.3s]" /></span>}
                </div>
              </div>
            ))}
            <div ref={endRef} />
          </div>

          {/* Sovereign disclosure */}
          <div className="flex items-center gap-1.5 px-3 py-1 text-[10px] text-muted-foreground border-t border-border/50">
            <ShieldCheck className="h-3 w-3 text-brand-500 shrink-0" />
            <span>Cited information only — not legal advice</span>
          </div>

          <form onSubmit={submit} className="flex items-center gap-2 border-t border-border p-3">
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask Maple…" data-testid="maple-dock-input"
              className="flex-1 rounded-full border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-brand-500/40" />
            <button type="submit" disabled={sending || !input.trim()} data-testid="maple-dock-send"
              className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-brand-500 text-white transition-transform hover:-translate-y-0.5 disabled:opacity-50"><Send className="h-4 w-4" /></button>
          </form>
        </div>
      )}
    </>
  );
}
