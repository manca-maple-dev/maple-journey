import { Link, useLocation } from "react-router-dom";

const LEGAL_LINKS = [
  { label: "Privacy", to: "/privacy" },
  { label: "Terms", to: "/terms" },
  { label: "Cookies", to: "/cookies" },
  { label: "AI Disclaimer", to: "/disclaimer" },
];

export function LegalPageNav() {
  const location = useLocation();
  const sourcePath = location.state?.from?.pathname || location.pathname;

  return (
    <div className="mt-6 flex flex-wrap gap-2">
      {LEGAL_LINKS.map((link) => (
        <Link
          key={link.to}
          to={link.to}
          state={{ from: { pathname: sourcePath } }}
          className="rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-brand-500"
        >
          {link.label}
        </Link>
      ))}
    </div>
  );
}