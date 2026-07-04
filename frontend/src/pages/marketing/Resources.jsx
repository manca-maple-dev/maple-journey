import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { BookOpen, ExternalLink } from "lucide-react";
import api from "@/lib/api";

const TOPIC_META = {
  "work-permit": { label: "Work Permit", keywords: ["work permit", "lmia", "pgwp", "employment authorization"] },
  "study-permit": { label: "Study Permit", keywords: ["study permit", "student", "school", "college", "university"] },
  benefits: { label: "Benefits", keywords: ["benefit", "tax", "credit", "child", "support"] },
  "newcomer-checklist": { label: "Newcomer Checklist", keywords: ["checklist", "first steps", "newcomer", "settlement"] },
};

export default function Resources() {
  const [items, setItems] = useState([]);
  const [active, setActive] = useState("All");
  const [params, setParams] = useSearchParams();

  const topicKey = (params.get("topic") || "").trim().toLowerCase();
  const topic = TOPIC_META[topicKey] || null;

  useEffect(() => {
    api.get("/resources").then(({ data }) => setItems(data)).catch(() => {});
  }, []);

  const cats = ["All", ...Array.from(new Set(items.map((i) => i.category)))];
  const categoryFiltered = active === "All" ? items : items.filter((i) => i.category === active);
  const filtered = useMemo(() => {
    if (!topic || active !== "All") return categoryFiltered;
    const byTopic = categoryFiltered.filter((i) => {
      const haystack = `${i.title || ""} ${i.description || ""} ${i.category || ""}`.toLowerCase();
      return topic.keywords.some((k) => haystack.includes(k));
    });
    return byTopic.length > 0 ? byTopic : categoryFiltered;
  }, [categoryFiltered, topic, active]);

  const clearTopic = () => {
    const next = new URLSearchParams(params);
    next.delete("topic");
    setParams(next, { replace: true });
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-16">
      <div className="max-w-2xl">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Immigration Resources</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">Guides for your Canadian journey</h1>
        <p className="mt-5 text-muted-foreground">Plain-language explainers on the pathways, paperwork and first steps that matter most.</p>
        {topic && (
          <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-700">
            Focused on: {topic.label}
            <button onClick={clearTopic} className="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-brand-700 hover:bg-brand-100" data-testid="resources-clear-topic">
              Clear
            </button>
          </div>
        )}
      </div>

      <div className="mt-8 flex flex-wrap gap-2">
        {cats.map((c) => (
          <button key={c} onClick={() => setActive(c)} data-testid={`resource-filter-${c}`}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${active === c ? "bg-brand-500 text-white" : "border border-border bg-card text-muted-foreground hover:text-foreground"}`}>
            {c}
          </button>
        ))}
      </div>

      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((r) => (
          <a key={r.id} href={r.url || "#"} className="group rounded-2xl border border-border bg-card p-6 transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-black/[0.04]" data-testid={`resource-${r.id}`}>
            <div className="flex items-center justify-between">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-maple-50 text-maple dark:bg-maple-500/10"><BookOpen className="h-5 w-5" /></div>
              <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
            <span className="mt-4 inline-block rounded-full bg-secondary px-2.5 py-1 text-[11px] font-semibold text-muted-foreground">{r.category}</span>
            <h3 className="mt-3 font-display text-lg font-semibold">{r.title}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{r.description}</p>
          </a>
        ))}
      </div>
    </div>
  );
}
