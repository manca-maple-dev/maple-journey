import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

export default function ContentManagement() {
  const [content, setContent] = useState({ hero_title: "", hero_subtitle: "", cta_label: "" });
  const [resources, setResources] = useState([]);
  const [benefits, setBenefits] = useState([]);
  const [newRes, setNewRes] = useState({ title: "", category: "First Steps", description: "", url: "" });
  const [newBen, setNewBen] = useState({ title: "", category: "Family", description: "", eligibility: "", amount: "" });

  const load = () => {
    api.get("/admin/content").then(({ data }) => setContent({ hero_title: "", hero_subtitle: "", cta_label: "", ...data }));
    api.get("/resources").then(({ data }) => setResources(data));
    api.get("/benefits").then(({ data }) => setBenefits(data));
  };
  useEffect(() => { load(); }, []);

  const saveContent = async () => { await api.put("/admin/content", content); toast.success("Landing copy updated"); };
  const addRes = async () => { if (!newRes.title) return; await api.post("/admin/resources", newRes); setNewRes({ title: "", category: "First Steps", description: "", url: "" }); toast.success("Resource added"); load(); };
  const delRes = async (id) => { await api.delete(`/admin/resources/${id}`); load(); };
  const addBen = async () => { if (!newBen.title) return; await api.post("/admin/benefits", newBen); setNewBen({ title: "", category: "Family", description: "", eligibility: "", amount: "" }); toast.success("Benefit added"); load(); };
  const delBen = async (id) => { await api.delete(`/admin/benefits/${id}`); load(); };

  return (
    <div className="space-y-6" data-testid="admin-content-page">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">Content management</h1>
        <p className="mt-1 text-sm text-muted-foreground">Edit landing copy, resources and benefits data.</p>
      </div>

      <Tabs defaultValue="landing">
        <TabsList data-testid="content-tabs">
          <TabsTrigger value="landing" data-testid="tab-landing">Landing copy</TabsTrigger>
          <TabsTrigger value="resources" data-testid="tab-resources">Resources</TabsTrigger>
          <TabsTrigger value="benefits" data-testid="tab-benefits">Benefits</TabsTrigger>
        </TabsList>

        <TabsContent value="landing" className="mt-4">
          <div className="space-y-4 rounded-2xl border border-border bg-card p-6">
            <div className="space-y-1.5"><Label>Hero title</Label><Input value={content.hero_title} onChange={(e) => setContent({ ...content, hero_title: e.target.value })} data-testid="content-hero-title" /></div>
            <div className="space-y-1.5"><Label>Hero subtitle</Label><Textarea value={content.hero_subtitle} onChange={(e) => setContent({ ...content, hero_subtitle: e.target.value })} data-testid="content-hero-subtitle" /></div>
            <div className="space-y-1.5"><Label>CTA label</Label><Input value={content.cta_label} onChange={(e) => setContent({ ...content, cta_label: e.target.value })} data-testid="content-cta" /></div>
            <Button onClick={saveContent} className="rounded-full" data-testid="content-save">Save copy</Button>
          </div>
        </TabsContent>

        <TabsContent value="resources" className="mt-4 space-y-4">
          <div className="grid gap-3 rounded-2xl border border-border bg-card p-6 sm:grid-cols-2">
            <Input placeholder="Title" value={newRes.title} onChange={(e) => setNewRes({ ...newRes, title: e.target.value })} data-testid="res-title" />
            <Input placeholder="Category" value={newRes.category} onChange={(e) => setNewRes({ ...newRes, category: e.target.value })} data-testid="res-category" />
            <Input placeholder="Description" value={newRes.description} onChange={(e) => setNewRes({ ...newRes, description: e.target.value })} className="sm:col-span-2" data-testid="res-desc" />
            <Button onClick={addRes} className="rounded-full sm:col-span-2" data-testid="res-add"><Plus className="mr-1 h-4 w-4" /> Add resource</Button>
          </div>
          <div className="space-y-2">
            {resources.map((r) => (
              <div key={r.id} className="flex items-center gap-3 rounded-xl border border-border bg-card p-3" data-testid={`res-item-${r.id}`}>
                <div className="flex-1"><p className="text-sm font-semibold">{r.title}</p><p className="text-xs text-muted-foreground">{r.category}</p></div>
                <button onClick={() => delRes(r.id)} className="grid h-8 w-8 place-items-center rounded-lg text-muted-foreground hover:text-maple" data-testid={`res-del-${r.id}`}><Trash2 className="h-4 w-4" /></button>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="benefits" className="mt-4 space-y-4">
          <div className="grid gap-3 rounded-2xl border border-border bg-card p-6 sm:grid-cols-2">
            <Input placeholder="Title" value={newBen.title} onChange={(e) => setNewBen({ ...newBen, title: e.target.value })} data-testid="ben-title" />
            <Input placeholder="Category" value={newBen.category} onChange={(e) => setNewBen({ ...newBen, category: e.target.value })} data-testid="ben-category" />
            <Input placeholder="Description" value={newBen.description} onChange={(e) => setNewBen({ ...newBen, description: e.target.value })} className="sm:col-span-2" data-testid="ben-desc" />
            <Input placeholder="Eligibility" value={newBen.eligibility} onChange={(e) => setNewBen({ ...newBen, eligibility: e.target.value })} data-testid="ben-elig" />
            <Input placeholder="Amount" value={newBen.amount} onChange={(e) => setNewBen({ ...newBen, amount: e.target.value })} data-testid="ben-amount" />
            <Button onClick={addBen} className="rounded-full sm:col-span-2" data-testid="ben-add"><Plus className="mr-1 h-4 w-4" /> Add benefit</Button>
          </div>
          <div className="space-y-2">
            {benefits.map((b) => (
              <div key={b.id} className="flex items-center gap-3 rounded-xl border border-border bg-card p-3" data-testid={`ben-item-${b.id}`}>
                <div className="flex-1"><p className="text-sm font-semibold">{b.title}</p><p className="text-xs text-muted-foreground">{b.category} · {b.amount}</p></div>
                <button onClick={() => delBen(b.id)} className="grid h-8 w-8 place-items-center rounded-lg text-muted-foreground hover:text-maple" data-testid={`ben-del-${b.id}`}><Trash2 className="h-4 w-4" /></button>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
