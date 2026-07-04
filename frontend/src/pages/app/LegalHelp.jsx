import { useEffect, useState } from "react";
import { Scale, Phone, ExternalLink, ShieldCheck, Bot, Heart } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useMaple } from "@/context/MapleContext";

const RIGHTS_LINKS = [
  {
    id: "find-rep",
    label: "Find an authorized representative",
    href: "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigration-citizenship-representative/choose/authorized.html",
  },
  {
    id: "legal-aid",
    label: "Find legal aid by province",
    href: "https://www.justice.gc.ca/eng/fund-fina/gov-gouv/aid-aide.html",
  },
  {
    id: "abuse-help",
    label: "Help if you face abuse or exploitation",
    href: "https://www.canada.ca/en/employment-social-development/services/foreign-workers/report-abuse.html",
  },
];

export default function LegalHelp() {
  const { user } = useAuth();
  const { openWith } = useMaple();
  const [items, setItems] = useState([]);
  const [type, setType] = useState("All");
  const [province, setProvince] = useState("All");

  useEffect(() => { api.get("/legal-resources").then(({ data }) => setItems(data)).catch(() => {}); }, []);

  const isRefugee = (user?.newcomer_type || "").toLowerCase() === "refugee";
  const types = ["All", ...Array.from(new Set(items.map((i) => i.type)))];
  const provinces = ["All", ...Array.from(new Set(items.map((i) => i.province)))];
  const filtered = items.filter((i) => (type === "All" || i.type === type) && (province === "All" || i.province === province));

  return (
    <div className="space-y-6" data-testid="legal-page">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">Find legal help</h1>
        <p className="mt-1 text-sm text-muted-foreground">Free and low-cost immigration lawyers, refugee legal aid, and community clinics.</p>
      </div>

      {/* Reassurance banner (refugee-aware) */}
      <div className="relative overflow-hidden rounded-2xl border border-border bg-brand-600 p-6 text-white">
        <div className="pointer-events-none absolute inset-0 mj-dot-bg opacity-20" />
        <div className="relative flex items-start gap-3">
          <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white/15"><Heart className="h-5 w-5" /></div>
          <div>
            <h2 className="font-display text-lg font-semibold">
              {isRefugee ? "You likely qualify for FREE legal aid" : "Good legal help doesn't have to be expensive"}
            </h2>
            <p className="mt-1 text-sm text-white/85">
              {isRefugee
                ? "Refugee claimants across Canada can access free, government-funded legal representation. Start with the legal-aid office in your province below."
                : "Many newcomers qualify for free or low-cost legal support. Explore the options below, or ask Maple which fits your situation."}
            </p>
            <button onClick={() => openWith("What free or low-cost legal help can I get for my immigration situation?")} data-testid="legal-ask-maple" className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-white px-3.5 py-1.5 text-xs font-semibold text-brand-600 transition-transform hover:-translate-y-0.5">
              <Bot className="h-3.5 w-3.5" /> Ask Maple about my options
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {types.map((t) => (
          <button key={t} onClick={() => setType(t)} data-testid={`legal-type-${t}`}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${type === t ? "bg-brand-500 text-white" : "border border-border bg-card text-muted-foreground hover:text-foreground"}`}>{t}</button>
        ))}
        <span className="mx-1 self-center text-border">|</span>
        {provinces.map((p) => (
          <button key={p} onClick={() => setProvince(p)} data-testid={`legal-prov-${p}`}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${province === p ? "bg-maple text-white" : "border border-border bg-card text-muted-foreground hover:text-foreground"}`}>{p}</button>
        ))}
      </div>

      {/* Prepare for legal call */}
      <div className="rounded-2xl border border-border bg-card p-4" data-testid="legal-prepare">
        <p className="text-sm font-semibold">Prepare before you call</p>
        <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
          <li>1. Keep your permit/visa dates and UCI number nearby.</li>
          <li>2. Bring refusal letters, notices, and deadlines in one folder.</li>
          <li>3. Write your top 3 questions so the call stays focused.</li>
        </ul>
        <div className="mt-3 flex flex-wrap gap-2">
          {RIGHTS_LINKS.map((r) => (
            <a key={r.id} href={r.href} target="_blank" rel="noreferrer" className="rounded-full border border-border bg-secondary/40 px-3 py-1.5 text-[11px] font-medium text-brand-600 hover:border-brand-400" data-testid={`legal-rights-${r.id}`}>
              {r.label} <ExternalLink className="ml-1 inline h-3 w-3" />
            </a>
          ))}
        </div>
      </div>

      {/* Resource cards */}
      <div className="grid gap-4 sm:grid-cols-2">
        {filtered.length === 0 && <p className="col-span-full rounded-2xl border border-dashed border-border p-8 text-center text-sm text-muted-foreground">No legal resources match these filters at the moment. Try clearing filters. We continue adding verified legal data over time.</p>}
        {filtered.map((r) => (
          <div key={r.id} className="flex flex-col rounded-2xl border border-border bg-card p-5" data-testid={`legal-${r.id}`}>
            <div className="flex items-start justify-between">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10"><Scale className="h-5 w-5" /></div>
              <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${r.cost === "Free" ? "bg-green-500/10 text-green-600" : "bg-amber-500/10 text-amber-600"}`}>{r.cost}</span>
            </div>
            <h3 className="mt-4 font-display font-semibold">{r.name}</h3>
            <div className="mt-1 flex flex-wrap gap-1.5">
              <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">{r.type}</span>
              <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">{r.province}</span>
              {r.freshness_label && <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-600">{r.freshness_label}</span>}
            </div>
            {r.relevance_reasons?.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {r.relevance_reasons.map((reason) => (
                  <span key={reason} className="rounded-full bg-maple/10 px-2 py-0.5 text-[11px] font-medium text-maple">
                    {reason}
                  </span>
                ))}
              </div>
            )}
            <p className="mt-2 flex-1 text-sm text-muted-foreground">{r.description}</p>
            <div className="mt-4 flex items-center gap-3 border-t border-border pt-3 text-sm">
              {r.contact && <a href={`tel:${r.contact.replace(/[^0-9+]/g, "")}`} className="inline-flex items-center gap-1 font-semibold text-brand-500"><Phone className="h-3.5 w-3.5" /> {r.contact}</a>}
              {r.url && <a href={r.url} target="_blank" rel="noreferrer" className="ml-auto inline-flex items-center gap-1 text-muted-foreground hover:text-brand-500" data-testid={`legal-link-${r.id}`}>Visit <ExternalLink className="h-3.5 w-3.5" /></a>}
            </div>
          </div>
        ))}
      </div>

      <p className="flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
        <ShieldCheck className="h-3.5 w-3.5" /> MapleJourney is not a law firm. These are independent organizations — always verify eligibility directly.
      </p>
    </div>
  );
}
