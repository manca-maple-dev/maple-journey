import { createContext, useContext, useState, useRef, useCallback, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { API } from "@/lib/api";

/**
 * Maple Wingman Context — One persistent, page-aware companion.
 *
 * A single conversation/session is shared by the floating MapleDock (available
 * on every app screen) and the full /app/chat view. The context is page-aware:
 * it tracks which page the user is on and can seed contextual questions.
 *
 * Implements the 'Sovereign UI Architect' pattern: the companion is omnipresent,
 * never feels like a separate product, and carries conversation across pages.
 */
const MapleContext = createContext(null);

// Page-aware context hints for proactive seeding
const PAGE_CONTEXT = {
  "/app": "The user is on the home dashboard viewing their daily briefing and proactive alerts.",
  "/app/assessment": "The user is checking their PR/CRS assessment and immigration deadlines.",
  "/app/jobs": "The user is browsing job matches (LMIA-exempt, PNP-friendly roles).",
  "/app/legal": "The user is looking for legal help (RCIC, lawyers, legal aid clinics).",
  "/app/communities": "The user is exploring communities and settlement services near them.",
  "/app/accessibilities": "The user is setting up essentials: eSIM, banking, transit.",
  "/app/profile": "The user is viewing/editing their profile and Maple preferences.",
  "/app/plans": "The user is considering upgrading their plan for deeper intelligence.",
  "/app/onboarding": "The user is completing their newcomer profile for personalized guidance.",
};

export function MapleProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const [assistantPhase, setAssistantPhase] = useState("idle"); // idle | reasoning | typing
  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState(() => localStorage.getItem("mj_chat_session") || "");
  const [currentPage, setCurrentPage] = useState("/app");
  const loadedRef = useRef(false);

  // Track current page for context-awareness
  const location = useLocation();
  useEffect(() => {
    setCurrentPage(location.pathname);
  }, [location.pathname]);

  // Load prior history once, if a session already exists.
  useEffect(() => {
    if (!sessionId || loadedRef.current) return;
    loadedRef.current = true;
    const token = localStorage.getItem("mj_token");
    fetch(`${API}/assistant/history?session_id=${sessionId}`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((data) => Array.isArray(data) && setMessages(data.map((m) => ({ role: m.role, content: m.content }))))
      .catch(() => {});
  }, [sessionId]);

  const send = useCallback(async (text) => {
    const msg = (text || "").trim();
    if (!msg || sending) return;
    setMessages((m) => [...m, { role: "user", content: msg }, { role: "assistant", content: "" }]);
    setSending(true);
    setAssistantPhase("reasoning");
    try {
      const token = localStorage.getItem("mj_token");
      const res = await fetch(`${API}/assistant/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ session_id: sessionId || null, message: msg }),
      });
      const sid = res.headers.get("X-Session-Id");
      if (sid && sid !== sessionId) {
        loadedRef.current = true;
        setSessionId(sid);
        localStorage.setItem("mj_chat_session", sid);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let acc = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        if (assistantPhase !== "typing") setAssistantPhase("typing");
        acc += decoder.decode(value, { stream: true });
        setMessages((m) => { const copy = [...m]; copy[copy.length - 1] = { role: "assistant", content: acc }; return copy; });
      }
    } catch {
      setMessages((m) => { const copy = [...m]; copy[copy.length - 1] = { role: "assistant", content: "I apologize for the interruption. Please try again." }; return copy; });
    } finally {
      setSending(false);
      setAssistantPhase("idle");
    }
  }, [sending, sessionId, assistantPhase]);

  // Open the dock, optionally seeded with a page-contextual question.
  const openWith = useCallback((prefill) => {
    setOpen(true);
    const t = (prefill || "").trim();
    if (t) send(t);
  }, [send]);

  // Start a fresh conversation (new session).
  const resetChat = useCallback(() => {
    setMessages([]);
    setSessionId("");
    localStorage.removeItem("mj_chat_session");
    loadedRef.current = false;
  }, []);

  // Get contextual hint for the current page
  const getPageContext = useCallback(() => {
    return PAGE_CONTEXT[currentPage] || "The user is navigating the app.";
  }, [currentPage]);

  return (
    <MapleContext.Provider value={{ messages, sending, assistantPhase, open, setOpen, openWith, send, resetChat, sessionId, currentPage, getPageContext }}>
      {children}
    </MapleContext.Provider>
  );
}

export const useMaple = () => useContext(MapleContext);
