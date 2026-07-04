import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";

const LINKS = [
  { label: "Features", to: "/features" },
  { label: "Resources", to: "/resources" },
  { label: "Pricing", to: "/pricing" },
  { label: "About", to: "/about" },
  { label: "Contact", to: "/contact" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="mx-auto mt-3 max-w-6xl px-4">
        <nav className="mj-glass flex items-center justify-between rounded-2xl px-4 py-2.5 shadow-lg shadow-black/[0.03]">
          <Logo />
          <div className="hidden items-center gap-1 md:flex">
            {LINKS.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                data-testid={`nav-${l.label.toLowerCase()}`}
                className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
                  pathname === l.to ? "text-brand-500" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {l.label}
              </Link>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            {user ? (
              <Button size="sm" onClick={() => navigate("/app")} data-testid="nav-open-app" className="rounded-full">
                Open app
              </Button>
            ) : (
              <>
                <Button variant="ghost" size="sm" className="hidden rounded-full sm:inline-flex" onClick={() => navigate("/login")} data-testid="nav-login">
                  Sign in
                </Button>
                <Button size="sm" className="rounded-full" onClick={() => navigate("/signup")} data-testid="nav-signup">
                  Get started
                </Button>
              </>
            )}
            <button className="grid h-9 w-9 place-items-center rounded-lg md:hidden" onClick={() => setOpen(!open)} data-testid="nav-mobile-toggle">
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </nav>
        {open && (
          <div className="mj-glass mt-2 flex flex-col gap-1 rounded-2xl p-3 md:hidden" data-testid="nav-mobile-menu">
            {LINKS.map((l) => (
              <Link key={l.to} to={l.to} onClick={() => setOpen(false)} className="rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-secondary">
                {l.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </header>
  );
}
