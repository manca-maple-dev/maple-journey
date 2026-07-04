import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Plus, Trash2, Megaphone, CheckCircle2, AlertTriangle } from "lucide-react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const TONE = {
  info: { icon: Megaphone, cls: "bg-brand-50 text-brand-600 dark:bg-brand-500/10" },
  success: { icon: CheckCircle2, cls: "bg-green-500/10 text-green-600" },
  warning: { icon: AlertTriangle, cls: "bg-amber-500/10 text-amber-600" },
};

export default function Announcements() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ title: "", body: "", tone: "info" });
  const [confirmPublish, setConfirmPublish] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);

  const load = () => api.get("/announcements").then(({ data }) => setItems(data));
  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!form.title || !form.body) return;
    try {
      await api.post("/admin/announcements", form);
      setForm({ title: "", body: "", tone: "info" });
      toast.success("Announcement published");
      load();
    } catch {
      toast.error("Publish failed");
    }
  };
  const remove = async (id) => {
    try {
      await api.delete(`/admin/announcements/${id}`);
      toast.success("Announcement deleted");
      load();
    } catch {
      toast.error("Delete failed");
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-announcements-page">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">Announcements</h1>
        <p className="mt-1 text-sm text-muted-foreground">Broadcast updates to every user's dashboard.</p>
      </div>

      <div className="grid gap-3 rounded-2xl border border-border bg-card p-6">
        <div className="grid gap-3 sm:grid-cols-[1fr_180px]">
          <div className="space-y-1.5"><Label>Title</Label><Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} data-testid="ann-title" /></div>
          <div className="space-y-1.5"><Label>Tone</Label>
            <Select value={form.tone} onValueChange={(v) => setForm({ ...form, tone: v })}><SelectTrigger data-testid="ann-tone"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="info">Info</SelectItem><SelectItem value="success">Success</SelectItem><SelectItem value="warning">Warning</SelectItem></SelectContent></Select>
          </div>
        </div>
        <div className="space-y-1.5"><Label>Message</Label><Textarea value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} data-testid="ann-body" /></div>
        <Button onClick={() => setConfirmPublish(true)} className="rounded-full justify-self-start" data-testid="ann-publish"><Plus className="mr-1 h-4 w-4" /> Publish</Button>
      </div>

      <div className="space-y-3">
        {items.map((a) => {
          const t = TONE[a.tone] || TONE.info; const Icon = t.icon;
          return (
            <div key={a.id} className="flex items-start gap-3 rounded-2xl border border-border bg-card p-4" data-testid={`ann-item-${a.id}`}>
              <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg ${t.cls}`}><Icon className="h-4 w-4" /></span>
              <div className="flex-1"><p className="text-sm font-semibold">{a.title}</p><p className="mt-1 text-xs text-muted-foreground">{a.body}</p></div>
              <button onClick={() => setConfirmDelete(a)} className="grid h-8 w-8 place-items-center rounded-lg text-muted-foreground hover:text-maple" data-testid={`ann-del-${a.id}`}><Trash2 className="h-4 w-4" /></button>
            </div>
          );
        })}
      </div>

      <Dialog open={confirmPublish} onOpenChange={setConfirmPublish}>
        <DialogContent>
          <DialogHeader><DialogTitle>Publish this announcement?</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div className="rounded-xl border border-border bg-secondary/40 p-3">
              <p className="text-sm font-semibold">{form.title || "Untitled announcement"}</p>
              <p className="mt-1 text-xs text-muted-foreground">{form.body || "No message body"}</p>
              <p className="mt-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Tone: {form.tone}</p>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setConfirmPublish(false)}>Cancel</Button>
              <Button onClick={async () => { setConfirmPublish(false); await add(); }} disabled={!form.title || !form.body}>
                Confirm publish
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={!!confirmDelete} onOpenChange={(o) => !o && setConfirmDelete(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete announcement?</DialogTitle></DialogHeader>
          {confirmDelete && (
            <div className="space-y-3">
              <div className="rounded-xl border border-maple/30 bg-maple-50/60 p-3 text-sm dark:bg-maple-500/10">
                <p className="font-semibold">{confirmDelete.title}</p>
                <p className="mt-1 text-xs text-muted-foreground">This announcement will be removed for all users.</p>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setConfirmDelete(null)}>Cancel</Button>
                <Button className="bg-maple text-white hover:bg-maple-600" onClick={async () => {
                  const target = confirmDelete;
                  setConfirmDelete(null);
                  await remove(target.id);
                }}>
                  Delete
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
