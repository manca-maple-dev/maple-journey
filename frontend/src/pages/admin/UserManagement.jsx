import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Search, Trash2, ShieldCheck } from "lucide-react";
import api from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { TOGGLEABLE_FEATURES } from "@/lib/features";

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);

  const load = () => api.get("/admin/users").then(({ data }) => setUsers(data));
  useEffect(() => { load(); }, []);

  const toggleFeature = async (u, key, value) => {
    const features = { ...u.features, [key]: value };
    // Optimistic update
    setUsers((prev) => prev.map((x) => (x.id === u.id ? { ...x, features } : x)));
    setEditing((e) => (e && e.id === u.id ? { ...e, features } : e));
    try {
      const { data } = await api.put(`/admin/users/${u.id}/features`, { features });
      setUsers((prev) => prev.map((x) => (x.id === u.id ? data : x)));
      toast.success(`${TOGGLEABLE_FEATURES.find((f) => f.key === key)?.label} ${value ? "enabled" : "disabled"} for ${u.name}`);
    } catch { toast.error("Update failed"); load(); }
  };

  const remove = async (u) => {
    try {
      await api.delete(`/admin/users/${u.id}`);
      toast.success("User removed");
      load();
    } catch {
      toast.error("Delete failed");
    }
  };

  const filtered = users.filter((u) => `${u.name} ${u.email}`.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="space-y-6" data-testid="admin-users-page">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">User management</h1>
        <p className="mt-1 text-sm text-muted-foreground">Toggle features per user — changes reflect instantly on their dashboard.</p>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search users…" className="pl-9" data-testid="user-search" />
      </div>

      <div className="overflow-x-auto rounded-2xl border border-border bg-card">
        <table className="w-full min-w-[560px] text-sm">
          <thead className="border-b border-border bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
            <tr><th className="px-4 py-3">User</th><th className="hidden px-4 py-3 sm:table-cell">Pathway</th><th className="hidden px-4 py-3 md:table-cell">Enabled</th><th className="px-4 py-3 text-right">Actions</th></tr>
          </thead>
          <tbody>
            {filtered.map((u) => {
              const enabledCount = TOGGLEABLE_FEATURES.filter((f) => u.features?.[f.key] !== false).length;
              return (
                <tr key={u.id} className="border-b border-border last:border-0" data-testid={`user-row-${u.id}`}>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="grid h-9 w-9 place-items-center rounded-full bg-brand-500 text-xs font-semibold text-white">{(u.name || "U")[0]}</div>
                      <div>
                        <p className="flex items-center gap-1.5 font-semibold">{u.name}{u.role === "admin" && <ShieldCheck className="h-3.5 w-3.5 text-maple" />}</p>
                        <p className="text-xs text-muted-foreground">{u.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">{u.visa_type}</td>
                  <td className="hidden px-4 py-3 md:table-cell"><span className="rounded-full bg-secondary px-2.5 py-1 text-xs font-semibold">{enabledCount}/{TOGGLEABLE_FEATURES.length}</span></td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <Button size="sm" variant="outline" className="rounded-full" onClick={() => setEditing(u)} data-testid={`user-manage-${u.id}`}>Manage</Button>
                      {u.role !== "admin" && <button onClick={() => setConfirmDelete(u)} data-testid={`user-delete-${u.id}`} className="grid h-8 w-8 place-items-center rounded-lg text-muted-foreground hover:bg-secondary hover:text-maple"><Trash2 className="h-4 w-4" /></button>}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Manage features — {editing?.name}</DialogTitle></DialogHeader>
          {editing && (
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">Flip a switch to enable or disable a module on this user's dashboard in real time.</p>
              {TOGGLEABLE_FEATURES.map((f) => (
                <div key={f.key} className="flex items-center gap-3 rounded-xl border border-border bg-background px-3 py-2.5">
                  <f.icon className="h-4 w-4 text-muted-foreground" />
                  <div className="flex-1"><Label className="text-sm">{f.label}</Label><p className="text-xs text-muted-foreground">{f.desc}</p></div>
                  <Switch checked={editing.features?.[f.key] !== false} onCheckedChange={(v) => toggleFeature(editing, f.key, v)} data-testid={`toggle-${editing.id}-${f.key}`} />
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={!!confirmDelete} onOpenChange={(o) => !o && setConfirmDelete(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete user account?</DialogTitle></DialogHeader>
          {confirmDelete && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                This permanently removes <span className="font-semibold text-foreground">{confirmDelete.name}</span> and related user data.
              </p>
              <div className="rounded-xl border border-maple/30 bg-maple-50/60 px-3 py-2 text-xs text-maple dark:bg-maple-500/10">
                This action cannot be undone.
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setConfirmDelete(null)}>Cancel</Button>
                <Button className="bg-maple text-white hover:bg-maple-600" onClick={async () => {
                  const target = confirmDelete;
                  setConfirmDelete(null);
                  await remove(target);
                }}>
                  Delete user
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
