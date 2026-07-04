import { Link } from "react-router-dom";
import { Logo } from "@/components/brand/Logo";
import { useAuth } from "@/context/AuthContext";
import { resolveSmartLink } from "@/lib/smartLinks";

const COLS = [
  { title: "In the app", links: ["ask-maple", "jobs", "benefits"] },
  { title: "Support", links: ["legal", "connected", "communities"] },
  { title: "Journey", links: ["work-permit", "study-permit", "account"] },
];

const LEGAL_LINKS = [
  { label: "Privacy Policy", to: "/privacy" },
  { label: "Terms of Service", to: "/terms" },
  { label: "Cookie Policy", to: "/cookies" },
  { label: "AI Disclaimer", to: "/disclaimer" },
  { label: "Contact", to: "/contact" },
];

export function Footer() {
  const { user, features } = useAuth();
  const isSignedIn = !!user && user !== false;

  return (
    <footer className="border-t border-border bg-card">
      <div className="mx-auto max-w-6xl px-4 py-14">
        <div className="grid gap-10 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
          <div>
            <Logo />
            <p className="mt-4 max-w-xs text-sm text-muted-foreground">
              The companion for your journey to Canada — visas, PR, jobs, benefits and settlement in one place.
            </p>
          </div>
          {COLS.map((col) => (
            <div key={col.title}>
              <h4 className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">{col.title}</h4>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((key) => {
                  const link = resolveSmartLink(key, { isSignedIn, features });
                  return (
                  <li key={key}>
                    <Link
                      to={link.to}
                      className="text-sm text-muted-foreground transition-colors hover:text-brand-500"
                      data-testid={`footer-link-${key}`}
                    >
                      {link.label}
                    </Link>
                  </li>
                )})}
              </ul>
            </div>
          ))}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">Legal</h4>
            <ul className="mt-4 space-y-2.5">
              {LEGAL_LINKS.map((link) => (
                <li key={link.to}>
                  <Link to={link.to} className="text-sm text-muted-foreground transition-colors hover:text-brand-500">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-border pt-6 text-sm text-muted-foreground sm:flex-row">
          <p>© {new Date().getFullYear()} MapleJourney. Not affiliated with the Government of Canada.</p>
          <p>MapleJourney provides information and organizational tools, not legal representation.</p>
        </div>
      </div>
    </footer>
  );
}
