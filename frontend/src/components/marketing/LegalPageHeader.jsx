import { Link, useLocation } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { LegalPageNav } from "@/components/marketing/LegalPageNav";

const DEFAULT_RETURN = { pathname: "/" };

function labelForPath(pathname) {
  if (!pathname) return "Back to MapleJourney";
  if (pathname.startsWith("/login")) return "Back to sign in";
  if (pathname.startsWith("/signup")) return "Back to sign up";
  if (pathname.startsWith("/app/onboarding")) return "Back to onboarding";
  if (pathname.startsWith("/app")) return "Back to app";
  if (pathname === "/contact") return "Back to contact";
  return "Back to MapleJourney";
}

export function LegalPageHeader({ eyebrow, title, updatedAt, intro }) {
  const location = useLocation();
  const from = location.state?.from || DEFAULT_RETURN;
  const returnLabel = labelForPath(from.pathname);

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-maple">{eyebrow}</p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">{title}</h1>
          <p className="mt-4 text-sm text-muted-foreground">Last updated: {updatedAt}</p>
        </div>
        <Link
          to={from.pathname || "/"}
          className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-brand-500"
        >
          <ArrowLeft className="h-4 w-4" /> {returnLabel}
        </Link>
      </div>
      <LegalPageNav />
      {intro && <div className="mt-6 rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">{intro}</div>}
    </>
  );
}