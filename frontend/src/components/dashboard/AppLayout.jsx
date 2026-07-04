import { useMemo, useState } from "react";
import { NavLink, Outlet, useNavigate, Navigate, useLocation } from "react-router-dom";
import { Menu, X, LogOut, ShieldQuestion, MessageCircle, Sparkles, ArrowLeft, ChevronDown, UserRound, Globe, CalendarDays, MapPin } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { useAuth } from "@/context/AuthContext";
import { FEATURES } from "@/lib/features";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { MapleProvider } from "@/context/MapleContext";
import { MapleDock } from "@/components/dashboard/MapleDock";

// Sidebar nav is driven by feature flags: an item only renders when its
// flag is enabled (or it is an always-on item like Dashboard/Settings).
function useNavItems(features) {
  return FEATURES.filter((f) => f.always || features[f.key]);
}

export default function AppLayout() {
  const { user, features, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const items = useNavItems(features);
  const liveDateLabel = useMemo(() => new Date().toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  }), []);

  if (user === null) return <div className="grid min-h-screen place-items-center text-muted-foreground">Loading…</div>;
  if (user === false) return <Navigate to="/login" replace />;

  // Only gate onboarding on the home page (/app); let users access other routes freely
  const isOnboarding = location.pathname === "/app/onboarding";
  const isAppHome = location.pathname === "/app";
  if (user.role !== "admin" && !user.profile_completed && isAppHome && !isOnboarding) {
    return <Navigate to="/app/onboarding" replace />;
  }

  const isPaid = user.tier === "plus" || user.tier === "family";
  const isChat = location.pathname === "/app/chat";
  const profile = user.profile || {};

  const initials = (user.name || "U").split(" ").map((s) => s[0]).slice(0, 2).join("").toUpperCase();
  const journeyLabel = profile.current_city || profile.province_of_residence || profile.intended_province || "Canada";
  const pathwayLabel = profile.immigration_category
    ? profile.immigration_category.replace(/_/g, " ")
    : (user.newcomer_type || "newcomer").replace(/_/g, " ");

  const SidebarContent = (
    <div className="flex h-full flex-col">
      <div className="px-5 py-5"><Logo size="sm" /></div>
      <nav className="flex-1 space-y-1 overflow-y-auto px-3">
        {items.map((f) => (
          <NavLink
            key={f.key}
            to={f.path}
            end={f.path === "/app"}
            onClick={() => setOpen(false)}
            data-testid={`nav-${f.key}`}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive ? "bg-brand-500 text-white shadow-lg shadow-brand-500/20" : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`
            }
          >
            <f.icon className="h-[18px] w-[18px]" /> {f.label}
          </NavLink>
        ))}
      </nav>
      {user.role === "admin" && (
        <div className="px-3 pb-2">
          <button onClick={() => navigate("/admin")} data-testid="nav-goto-admin" className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-maple hover:bg-maple-50 dark:hover:bg-maple-500/10">
            <ShieldQuestion className="h-[18px] w-[18px]" /> Admin Panel
          </button>
        </div>
      )}
      <div className="border-t border-border p-3">
        <div className="flex items-center gap-3 rounded-xl px-2 py-2">
          <div className="grid h-9 w-9 place-items-center rounded-full bg-brand-500 text-sm font-semibold text-white">{initials}</div>
          <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{user.name}</p><p className="truncate text-xs text-muted-foreground">{user.email}</p></div>
          <button onClick={logout} data-testid="logout-btn" className="grid h-8 w-8 place-items-center rounded-lg text-muted-foreground hover:bg-secondary hover:text-maple"><LogOut className="h-4 w-4" /></button>
        </div>
      </div>
    </div>
  );

  return (
    <MapleProvider>
    <div className="min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-card lg:block">{SidebarContent}</aside>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 bg-card">{SidebarContent}</aside>
        </div>
      )}

      <div className={isChat ? "flex h-[100dvh] flex-col overflow-hidden lg:pl-64" : "lg:pl-64"}>
        {/* Topbar */}
        <header className="sticky top-0 z-30 mj-glass flex shrink-0 items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <button className="grid h-9 w-9 place-items-center rounded-lg lg:hidden" onClick={() => setOpen(true)} data-testid="app-mobile-menu">
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            {location.pathname !== "/app" && (
              <button onClick={() => navigate(-1)} data-testid="app-back"
                className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
                <ArrowLeft className="h-4 w-4" /> <span className="hidden sm:inline">Back</span>
              </button>
            )}
            <div className="hidden sm:block">
              <p className="text-xs text-muted-foreground">Welcome back,</p>
              <p className="font-display text-sm font-semibold">{user.name?.split(" ")[0]} 👋</p>
            </div>
            <div className="hidden xl:flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground">
              <CalendarDays className="h-3.5 w-3.5 text-brand-600" />
              <span>{liveDateLabel}</span>
              <span className="opacity-50">•</span>
              <MapPin className="h-3.5 w-3.5 text-brand-600" />
              <span>{journeyLabel}</span>
              <span className="opacity-50">•</span>
              <span className="capitalize">{pathwayLabel}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {!isPaid && (
              <Button size="sm" className="rounded-full bg-gradient-to-r from-brand-500 to-maple text-white hover:opacity-90" onClick={() => navigate("/app/plans")} data-testid="app-upgrade">
                <Sparkles className="mr-1 h-3.5 w-3.5" /> Upgrade
              </Button>
            )}
            <NavLink to="/app/chat" data-testid="nav-ask-maple" className="grid h-9 w-9 place-items-center rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground"><MessageCircle className="h-4 w-4" /></NavLink>
            <ThemeToggle />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button data-testid="app-account" className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card py-1 pl-1 pr-2 transition-colors hover:bg-secondary">
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-brand-500 text-[11px] font-semibold text-white">{initials}</span>
                  <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52">
                <div className="px-2 py-1.5">
                  <p className="truncate text-sm font-semibold">{user.name}</p>
                  <p className="truncate text-xs text-muted-foreground">{user.email}</p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate("/app/profile")} data-testid="account-profile"><UserRound className="mr-2 h-4 w-4" /> Profile</DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/")} data-testid="account-view-site"><Globe className="mr-2 h-4 w-4" /> View site</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} data-testid="account-logout" className="text-maple focus:text-maple"><LogOut className="mr-2 h-4 w-4" /> Log out</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <main className={isChat ? "min-h-0 flex-1 overflow-hidden" : "mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8"}>
          <Outlet />
        </main>
      </div>
      {!isChat && <MapleDock />}
    </div>
    </MapleProvider>
  );
}
