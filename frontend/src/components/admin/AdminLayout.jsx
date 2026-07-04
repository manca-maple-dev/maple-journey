import { useState } from "react";
import { NavLink, Outlet, Navigate, useNavigate } from "react-router-dom";
import { LayoutDashboard, Users, ToggleRight, FileEdit, Megaphone, Menu, X, LogOut, ArrowLeft } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";

const NAV = [
  { label: "Overview", path: "/admin", icon: LayoutDashboard, end: true },
  { label: "Users", path: "/admin/users", icon: Users },
  { label: "Feature Toggles", path: "/admin/features", icon: ToggleRight },
  { label: "Content", path: "/admin/content", icon: FileEdit },
  { label: "Announcements", path: "/admin/announcements", icon: Megaphone },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  if (user === null) return <div className="grid min-h-screen place-items-center text-muted-foreground">Loading…</div>;
  if (user === false) return <Navigate to="/login" replace />;
  if (user.role !== "admin") return <Navigate to="/app" replace />;

  const Sidebar = (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-5 py-5">
        <Logo size="sm" showText={false} />
        <div><p className="font-display text-sm font-bold leading-none">MapleJourney</p><p className="text-[11px] font-semibold text-maple">ADMIN</p></div>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {NAV.map((n) => (
          <NavLink key={n.path} to={n.path} end={n.end} onClick={() => setOpen(false)} data-testid={`admin-nav-${n.label.toLowerCase().replace(" ", "-")}`}
            className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${isActive ? "bg-maple text-white shadow-lg shadow-maple/20" : "text-muted-foreground hover:bg-secondary hover:text-foreground"}`}>
            <n.icon className="h-[18px] w-[18px]" /> {n.label}
          </NavLink>
        ))}
      </nav>
      <div className="space-y-1 border-t border-border p-3">
        <button onClick={() => navigate("/app")} data-testid="admin-back-app" className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-secondary"><ArrowLeft className="h-[18px] w-[18px]" /> User app</button>
        <button onClick={logout} data-testid="admin-logout" className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-secondary hover:text-maple"><LogOut className="h-[18px] w-[18px]" /> Sign out</button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-card lg:block">{Sidebar}</aside>
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 bg-card">{Sidebar}</aside>
        </div>
      )}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 mj-glass flex items-center justify-between px-4 py-3">
          <button className="grid h-9 w-9 place-items-center rounded-lg lg:hidden" onClick={() => setOpen(true)} data-testid="admin-mobile-menu">{open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}</button>
          <p className="font-display text-sm font-semibold">Admin Panel</p>
          <div className="flex items-center gap-2"><ThemeToggle /><Button size="sm" variant="outline" className="hidden rounded-full sm:inline-flex" onClick={() => navigate("/")}>View site</Button></div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8"><Outlet /></main>
      </div>
    </div>
  );
}
