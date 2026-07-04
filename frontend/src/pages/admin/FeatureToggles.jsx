import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { TOGGLEABLE_FEATURES } from "@/lib/features";

export default function FeatureToggles() {
  const [features, setFeatures] = useState(null);

  useEffect(() => { api.get("/admin/features").then(({ data }) => setFeatures(data)); }, []);

  const toggle = async (key, value) => {
    const next = { ...features, [key]: value };
    setFeatures(next);
    try {
      const { data } = await api.put("/admin/features", { features: { [key]: value } });
      setFeatures(data);
      toast.success(`${TOGGLEABLE_FEATURES.find((f) => f.key === key)?.label} ${value ? "enabled" : "disabled"} globally`);
    } catch { toast.error("Update failed"); }
  };

  if (!features) return <div className="h-64 rounded-2xl border border-border bg-card mj-shimmer" />;

  return (
    <div className="mx-auto max-w-2xl space-y-6" data-testid="admin-features-page">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">Global feature toggles</h1>
        <p className="mt-1 text-sm text-muted-foreground">Disable a module here to hide it for every user, regardless of their individual settings.</p>
      </div>

      <div className="space-y-3">
        {TOGGLEABLE_FEATURES.map((f) => {
          const on = features[f.key] !== false;
          return (
            <div key={f.key} className="flex items-center gap-4 rounded-2xl border border-border bg-card p-4" data-testid={`global-toggle-${f.key}`}>
              <div className={`grid h-11 w-11 place-items-center rounded-xl ${on ? "bg-brand-50 text-brand-600 dark:bg-brand-500/10" : "bg-secondary text-muted-foreground"}`}><f.icon className="h-5 w-5" /></div>
              <div className="flex-1"><Label className="font-display text-base">{f.label}</Label><p className="text-xs text-muted-foreground">{f.desc}</p></div>
              <Switch checked={on} onCheckedChange={(v) => toggle(f.key, v)} data-testid={`global-switch-${f.key}`} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
