import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Send, User, ShieldCheck, MessageSquareText, Clock, Sparkles, Infinity as InfinityIcon, RotateCcw, Copy, Check } from "lucide-react";
import { useMaple } from "@/context/MapleContext";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { extractCitations, removeCitationTags, CitationCards } from "@/components/chat/CitationCard";

const SUGGESTIONS = [
  "How do I apply for a SIN?",
  "What's the difference between a work permit and a PGWP?",
  "How do I get provincial health coverage?",
  "What are the steps to renew my study or work permit?",
];

const URL_RE = /(https?:\/\/[^\s)]+|(?:www\.)?canada\.ca[^\s)]*)/g;

function Linkified({ text }) {
  const out = [];
  let last = 0;
  let m;
  const re = new RegExp(URL_RE);
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const url = m[0];
    const href = url.startsWith("http") ? url : `https://${url}`;
    out.push(<a key={m.index} href={href} target="_blank" rel="noopener noreferrer" className="font-medium text-brand-600 underline underline-offset-2 hover:text-brand-500">{url}</a>);
    last = m.index + url.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return <>{out}</>;
}

function TypingDots() {
  return (
    <span className="inline-flex gap-1 py-1" data-testid="assistant-typing">
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:0.15s]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:0.3s]" />
    </span>
  );
}

export default function Assistant() {
  const { messages, sending, assistantPhase, send, resetChat, getPageContext, currentPage } = useMaple();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [input, setInput] = useState("");
  const [usage, setUsage] = useState(null);
  const [copied, setCopied] = useState(-1);
  const endRef = useRef(null);
  const taRef = useRef(null);
  const seededTopicRef = useRef("");

  const isPaid = usage ? usage.unlimited : (user?.tier === "plus" || user?.tier === "family");
  const limitReached = usage && !usage.unlimited && usage.remaining <= 0;

  const loadUsage = useCallback(() => {
    api.get("/assistant/usage").then(({ data }) => setUsage(data)).catch(() => {});
  }, []);

  useEffect(() => { if (!sending) loadUsage(); }, [sending, loadUsage]);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, sending]);

  const autosize = () => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  };

  const submit = useCallback((text) => {
    const msg = (text ?? input).trim();
    if (!msg || sending || limitReached) return;
    setInput("");
    if (taRef.current) taRef.current.style.height = "auto";
    send(msg);
  }, [input, sending, limitReached, send]);

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  const copyMsg = async (text, idx) => {
    try { await navigator.clipboard.writeText(text); setCopied(idx); setTimeout(() => setCopied(-1), 1500); } catch { /* ignore */ }
  };

  const retentionLabel = () => {
    if (!usage) return "";
    if (usage.retention_days === null) return "Your chat history is saved forever.";
    if (isPaid) return `Your chat history is saved for ${usage.retention_days} days.`;
    return `Free chat history is kept for ${usage.retention_days} days.`;
  };

  const askFromPageContext = () => {
    submit(`Based on my current app context (${currentPage}), tell me the top 3 next steps I should take this week.`);
  };

  useEffect(() => {
    const topic = (params.get("topic") || "").trim().toLowerCase();
    if (!topic || sending || messages.length > 0 || seededTopicRef.current === topic) return;

    const promptByTopic = {
      "work-permit": "I need help with my work permit. Give me the top steps, required documents, and common mistakes to avoid.",
      "study-permit": "I need help with my study permit. Give me the top steps, required documents, and deadlines I should track.",
      resources: "Point me to the most important official resources I should read first as a newcomer in Canada.",
    };

    const prompt = promptByTopic[topic] || `Help me with ${topic.replace(/-/g, " ")} in Canada. Give me practical next steps and official sources.`;
    seededTopicRef.current = topic;
    submit(prompt);

    const next = new URLSearchParams(params);
    next.delete("topic");
    setParams(next, { replace: true });
  }, [messages.length, params, sending, setParams, submit]);

  return (
    <div className="flex h-full flex-col bg-background" data-testid="assistant-page">
      {/* ── Pinned top ── */}
      <div className="shrink-0 border-b border-border/70 bg-background/90 backdrop-blur supports-[backdrop-filter]:bg-background/75">
        <div className="mx-auto w-full max-w-3xl px-3 pt-2.5 sm:px-6 sm:pt-3">
          <div className="flex items-center gap-2.5 sm:gap-3">
            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-maple text-base text-white sm:h-9 sm:w-9 sm:text-lg">🍁</div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h1 className="font-display text-[15px] font-bold tracking-tight sm:text-lg">Ask Maple</h1>
                {usage && (
                  <span data-testid="assistant-tier-badge" className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${isPaid ? "bg-brand-50 text-brand-600 dark:bg-brand-500/10" : "bg-secondary text-muted-foreground"}`}>
                    {isPaid ? <InfinityIcon className="h-3 w-3" /> : null}
                    {usage.tier === "free" ? "Free" : usage.tier === "plus" ? "Plus" : "Family"}
                  </span>
                )}
              </div>
              <p className="truncate text-[11px] text-muted-foreground">Cited answers from IRCC, the CRA &amp; Service Canada.</p>
              <p className="mt-1 hidden text-[11px] text-muted-foreground sm:block" data-testid="assistant-page-context">{getPageContext()}</p>
            </div>
            {messages.length > 0 && (
              <div className="flex items-center gap-1">
                <button onClick={askFromPageContext} data-testid="assistant-context-ask" className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1.5 text-[11px] font-medium text-muted-foreground transition-colors hover:text-foreground">
                  <Sparkles className="h-3.5 w-3.5" /> <span className="hidden sm:inline">Use my page context</span>
                </button>
                <button onClick={resetChat} data-testid="assistant-new-chat" className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1.5 text-[11px] font-medium text-muted-foreground transition-colors hover:text-foreground">
                  <RotateCcw className="h-3.5 w-3.5" /> <span className="hidden sm:inline">New chat</span>
                </button>
              </div>
            )}
          </div>

          {usage && (
            <div data-testid="assistant-retention" className={`mb-1.5 mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-lg px-2.5 py-1.5 text-[11px] ${isPaid ? "text-brand-700 dark:text-brand-300" : "bg-amber-50 text-amber-800 dark:bg-amber-500/10 dark:text-amber-300"}`}>
              <Clock className="h-3 w-3 shrink-0" />
              {isPaid ? (
                <span className="font-medium">{retentionLabel()}</span>
              ) : limitReached ? (
                <>
                  <span className="font-medium">Credits used up for today. Your chat history is kept for {usage.retention_days} days.</span>
                  <button onClick={() => navigate("/app/plans")} className="font-semibold underline underline-offset-2 hover:opacity-80">Upgrade to keep history</button>
                </>
              ) : (
                <>
                  <span className="font-medium">Chat history is kept for {usage.retention_days} days.</span>
                  <button onClick={() => navigate("/app/plans")} className="font-semibold underline underline-offset-2 hover:opacity-80">Upgrade to keep history</button>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Scrollable messages (only this moves) ── */}
      <div className="min-h-0 flex-1 overflow-y-auto" data-testid="assistant-scroll">
        <div className="mx-auto w-full max-w-3xl px-3 sm:px-6">
          {messages.length === 0 ? (
            <div className="flex min-h-[38vh] items-center justify-center py-6 text-center sm:min-h-[55vh] sm:py-8">
              <div className="max-w-md">
                <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 sm:h-14 sm:w-14"><MessageSquareText className="h-6 w-6 sm:h-7 sm:w-7" /></div>
                <h2 className="mt-4 font-display text-[17px] font-semibold sm:mt-5 sm:text-lg">What would you like to know?</h2>
                <p className="mt-2 text-[13px] text-muted-foreground sm:text-sm">Ask about permits, your SIN, health coverage, taxes, benefits or legal help. Every answer is cited.</p>
                <div className="mt-4 grid gap-2 sm:mt-6 sm:grid-cols-2">
                  {SUGGESTIONS.map((s) => (
                    <button key={s} onClick={() => submit(s)} data-testid="assistant-suggestion" className="rounded-xl border border-border bg-card px-3 py-2 text-left text-[13px] transition-colors hover:border-brand-500 hover:text-brand-500 sm:py-2.5 sm:text-sm">{s}</button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4 py-4 sm:space-y-5 sm:py-6">
              {messages.map((m, i) => {
                const isLast = i === messages.length - 1;
                const streaming = m.role === "assistant" && isLast && sending && !!m.content;
                const isReasoning = m.role === "assistant" && isLast && sending && !m.content && assistantPhase === "reasoning";
                const citations = m.role === "assistant" ? extractCitations(m.content) : [];
                const cleanContent = m.role === "assistant" ? removeCitationTags(m.content) : m.content;
                return (
                  <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`} data-testid={`chat-msg-${m.role}`}>
                    <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${m.role === "user" ? "bg-brand-500 text-white" : "bg-maple text-white"}`}>
                      {m.role === "user" ? <User className="h-4 w-4" /> : <span className="text-sm">🍁</span>}
                    </div>
                    <div className={`max-w-[88%] ${m.role === "user" ? "" : "w-full sm:max-w-2xl"}`}>
                      <div className={`whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${m.role === "user" ? "rounded-tr-sm bg-brand-500 text-white" : "rounded-tl-sm bg-secondary text-foreground"}`}>
                        {cleanContent
                          ? (m.role === "assistant"
                              ? <><Linkified text={cleanContent} />{streaming && <span className="ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 animate-pulse bg-current align-middle" />}
                                  {!streaming && (
                                    <button onClick={() => copyMsg(cleanContent, i)} data-testid="assistant-copy" className="mt-2 flex items-center gap-1 text-[11px] font-medium text-muted-foreground transition-colors hover:text-brand-500">
                                      {copied === i ? <><Check className="h-3 w-3" /> Copied</> : <><Copy className="h-3 w-3" /> Copy</>}
                                    </button>
                                  )}
                                </>
                              : cleanContent)
                          : (
                            <div className="space-y-1">
                              <div className="text-[11px] font-medium text-muted-foreground">
                                {isReasoning ? "Maple is reasoning..." : "Maple is typing..."}
                              </div>
                              <TypingDots />
                            </div>
                          )}
                      </div>
                      {m.role === "assistant" && citations.length > 0 && !streaming && (
                        <div className="mt-3">
                          <CitationCards citations={citations} />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
              <div ref={endRef} />
            </div>
          )}
        </div>
      </div>

      {/* ── Pinned composer (safe-area aware) ── */}
      <div className="shrink-0 border-t border-border bg-background/90 backdrop-blur" style={{ paddingBottom: "max(0.5rem, env(safe-area-inset-bottom))" }}>
        <div className="mx-auto w-full max-w-3xl px-3 pt-2.5 sm:px-6 sm:pt-3">
          {limitReached ? (
            <div className="flex flex-col items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3.5 text-center dark:border-amber-500/20 dark:bg-amber-500/10" data-testid="assistant-limit-banner">
              <p className="text-sm font-medium text-amber-800 dark:text-amber-300">You've used all {usage.limit} free credits today.</p>
              <p className="text-xs text-amber-700/80 dark:text-amber-200/80">Your chat history is still kept for {usage.retention_days} days, but new messages need a plan upgrade.</p>
              <button onClick={() => navigate("/app/plans")} data-testid="assistant-limit-upgrade" className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-brand-500 to-maple px-5 py-2.5 text-sm font-semibold text-white transition-transform hover:-translate-y-0.5">
                <Sparkles className="h-4 w-4" /> Upgrade for unlimited chat
              </button>
            </div>
          ) : (
            <form onSubmit={(e) => { e.preventDefault(); submit(); }} className="flex items-end gap-2">
              <textarea
                ref={taRef}
                value={input}
                rows={1}
                onChange={(e) => { setInput(e.target.value); autosize(); }}
                onKeyDown={onKeyDown}
                placeholder="Ask Maple anything about settling in Canada…"
                data-testid="assistant-input"
                className="max-h-40 min-h-[44px] flex-1 resize-none rounded-2xl border border-border bg-card px-3.5 py-2.5 text-[13px] outline-none focus:ring-2 focus:ring-brand-500/40 sm:px-4 sm:py-3 sm:text-sm"
              />
              <button type="submit" disabled={sending || !input.trim()} data-testid="assistant-send" className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-brand-500 text-white transition-transform hover:-translate-y-0.5 disabled:opacity-50 sm:h-12 sm:w-12"><Send className="h-4.5 w-4.5 sm:h-5 sm:w-5" /></button>
            </form>
          )}
          <p className="flex items-center justify-center gap-1.5 py-2 text-center text-[11px] text-muted-foreground">
            <ShieldCheck className="h-3 w-3" /> Cited information only — not legal advice. Consult a regulated representative (RCIC or lawyer).
          </p>
        </div>
      </div>
    </div>
  );
}
