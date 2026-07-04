import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";

const STORAGE_KEY = "mj_cookie_consent";

function readChoice() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function saveChoice(value) {
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch {
    // Ignore storage failures (private mode / strict browser policy)
  }
}

export default function CookieConsentBanner() {
  const location = useLocation();
  const [choice, setChoice] = useState(null);

  useEffect(() => {
    setChoice(readChoice());
  }, []);

  const hidden = useMemo(() => {
    if (choice) return true;

    const path = location.pathname || "/";

    // Website-only: hide inside authenticated product surfaces.
    if (path.startsWith("/app") || path.startsWith("/admin")) return true;

    // Keep legal pages clean and avoid recursive consent prompts.
    if (path === "/cookies" || path === "/privacy" || path === "/terms" || path === "/disclaimer") return true;

    // Show banner only on public website routes.
    return false;
  }, [choice, location.pathname]);

  if (hidden) return null;

  const acceptAll = () => {
    saveChoice("accepted");
    setChoice("accepted");
  };

  const rejectOptional = () => {
    saveChoice("rejected");
    setChoice("rejected");
  };

  return (
    <div className="fixed inset-x-0 bottom-0 z-[120] p-3 sm:p-4">
      <div className="mx-auto max-w-4xl rounded-2xl border border-border bg-card/95 p-4 shadow-xl backdrop-blur">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-1.5">
            <p className="font-display text-base font-semibold text-foreground">Cookies on MapleJourney</p>
            <p className="text-sm text-muted-foreground">
              We use essential cookies to keep you signed in and keep Maple secure. Optional cookies help us improve quality and reliability.
              Read our {" "}
              <Link to="/cookies" className="font-medium text-primary underline underline-offset-2">Cookie Policy</Link>.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={rejectOptional}
              className="inline-flex items-center rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground hover:bg-muted"
            >
              Reject optional
            </button>
            <button
              type="button"
              onClick={acceptAll}
              className="inline-flex items-center rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground hover:opacity-95"
            >
              Accept all cookies
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
