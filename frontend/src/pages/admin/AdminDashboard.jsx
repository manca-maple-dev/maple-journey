import { useEffect, useState } from "react";
import { Users, FolderLock, ClipboardCheck, Bot } from "lucide-react";
import { BarChart, Bar, XAxis, ResponsiveContainer, Cell, Tooltip } from "recharts";
import api from "@/lib/api";
import { TOGGLEABLE_FEATURES } from "@/lib/features";

const STAT_META = [
  { key: "total_users", label: "Users", icon: Users, color: "#0066FF" },
  { key: "total_assessments", label: "Assessments", icon: ClipboardCheck, color: "#16A34A" },
  { key: "total_chats", label: "Maple chats", icon: Bot, color: "#F59E0B" },
];

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => { api.get("/admin/stats").then(({ data }) => setStats(data)); }, []);

  if (!stats) return <div className="h-64 rounded-2xl border border-border bg-card mj-shimmer" />;

  const usageData = TOGGLEABLE_FEATURES.map((f) => ({ name: f.label, value: stats.feature_usage?.[f.key] || 0 }));

  return (
    <div className="space-y-6" data-testid="admin-dashboard">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">Overview</h1>
        <p className="mt-1 text-sm text-muted-foreground">Platform activity at a glance.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {STAT_META.map((s) => (
          <div key={s.key} className="rounded-2xl border border-border bg-card p-5" data-testid={`stat-${s.key}`}>
            <div className="grid h-10 w-10 place-items-center rounded-xl" style={{ background: `${s.color}14`, color: s.color }}><s.icon className="h-5 w-5" /></div>
            <p className="mt-3 font-display text-3xl font-bold">{stats[s.key] ?? 0}</p>
            <p className="text-xs text-muted-foreground">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-border bg-card p-6">
          <h2 className="font-display text-lg font-semibold">Feature usage</h2>
          <p className="text-xs text-muted-foreground">Users with each module enabled.</p>
          <div className="mt-6 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={usageData}>
                <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-30} textAnchor="end" height={60} stroke="hsl(var(--muted-foreground))" />
                <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))", background: "hsl(var(--card))" }} cursor={{ fill: "hsl(var(--secondary))" }} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {usageData.map((_, i) => <Cell key={i} fill={i % 2 ? "#E31837" : "#0066FF"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6">
          <h2 className="font-display text-lg font-semibold">Global feature status</h2>
          <p className="text-xs text-muted-foreground">Modules enabled platform-wide.</p>
          <div className="mt-4 grid gap-2">
            {TOGGLEABLE_FEATURES.map((f) => {
              const on = stats.global_features?.[f.key] !== false;
              return (
                <div key={f.key} className="flex items-center gap-3 rounded-xl border border-border bg-background px-3 py-2.5 text-sm">
                  <f.icon className="h-4 w-4 text-muted-foreground" /> {f.label}
                  <span className={`ml-auto rounded-full px-2.5 py-1 text-[11px] font-semibold ${on ? "bg-green-500/10 text-green-600" : "bg-secondary text-muted-foreground"}`}>{on ? "Enabled" : "Disabled"}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
