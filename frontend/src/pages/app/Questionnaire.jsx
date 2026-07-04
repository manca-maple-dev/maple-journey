import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ShieldCheck, ExternalLink, CalendarClock, CheckCircle2, Flag, Info, ArrowRight, Loader2,
} from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const KIND = {
  deadline: { icon: CalendarClock, tone: "text-maple", chip: "bg-maple-50 text-maple dark:bg-maple-500/10", label: "Deadline" },
  todo: { icon: CheckCircle2, tone: "text-brand-600", chip: "bg-brand-50 text-brand-600 dark:bg-brand-500/10", label: "To do" },
  milestone: { icon: Flag, tone: "text-green-600", chip: "bg-green-500/10 text-green-600", label: "Milestone" },
  info: { icon: Info, tone: "text-muted-foreground", chip: "bg-secondary text-muted-foreground", label: "Good to know" },
};

const CATEGORY_LABEL = {
  express_entry: "Permanent-residence applicant", provincial_nominee: "Provincial Nominee", student: "International student",
  temp_foreign_worker: "Worker", visitor_work_permit: "Visitor / permit holder", spousal_family: "Family / spousal",
  refugee_claimant: "Refugee claimant", protected_person: "Protected person", other: "Newcomer",
};

function CountBadge({ days }) {
  if (days == null) return null;
  const cls = days < 0 ? "bg-secondary text-muted-foreground" : days < 60 ? "bg-maple-50 text-maple dark:bg-maple-500/10" : "bg-brand-50 text-brand-600 dark:bg-brand-500/10";
  return <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${cls}`}>{days < 0 ? `${Math.abs(days)}d ago` : `in ${days}d`}</span>;
}

export default function Questionnaire() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/status-check").then((r) => setData(r.data)).catch(() => setData({ cards: [] }));
  }, []);

  return (
    <div className="mx-auto max-w-2xl" data-testid="assessment-page">
      <div className="flex items-start gap-3">
        <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-500 text-white"><ShieldCheck className="h-6 w-6" /></div>
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">Status & deadlines</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {data?.status ? CATEGORY_LABEL[data.status] || "Newcomer" : "Your status at a glance"} · a factual self-check from official sources.
          </p>
        </div>
      </div>

      {/* IRPA s.91 disclosure */}
      <div className="mt-4 flex items-start gap-2 rounded-xl border border-border bg-secondary/50 px-3.5 py-2.5 text-xs text-muted-foreground" data-testid="assessment-disclosure">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand-500" />
        <span>This is cited information — <span className="font-medium text-foreground">not a score, ranking, or legal advice</span>. Dates are estimates; always confirm with the official source. For advice on your application, consult a regulated representative (RCIC or immigration lawyer).</span>
      </div>

      {!data && (
        <div className="mt-6 grid place-items-center py-16"><Loader2 className="h-6 w-6 animate-spin text-brand-500" /></div>
      )}

      {data && data.cards?.length === 0 && (
        <button onClick={() => navigate("/app/profile")} data-testid="assessment-empty"
          className="mt-6 flex w-full items-center gap-3 rounded-2xl border border-brand-500/30 bg-brand-50 p-5 text-left transition-colors hover:bg-brand-100 dark:bg-brand-500/10">
          <span className="min-w-0 flex-1">
            <span className="block font-semibold">Add your key dates to see your deadlines</span>
            <span className="mt-0.5 block text-sm text-muted-foreground">Enter your arrival, permit expiry or PR date in My Details and this page fills in with cited reminders.</span>
          </span>
          <ArrowRight className="h-4 w-4 shrink-0 text-brand-600" />
        </button>
      )}

      <div className="mt-5 space-y-3">
        {data?.cards?.map((c, i) => {
          const k = KIND[c.kind] || KIND.info;
          const Icon = k.icon;
          return (
            <motion.div key={c.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
              data-testid={`status-card-${c.id}`} className="rounded-2xl border border-border bg-card p-5">
              <div className="flex items-start gap-3">
                <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-secondary ${k.tone}`}><Icon className="h-4.5 w-4.5" /></span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-display font-semibold">{c.title}</h3>
                    <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${k.chip}`}>{k.label}</span>
                    <span className="ml-auto"><CountBadge days={c.days} /></span>
                  </div>
                  {c.date && <p className="mt-0.5 text-xs text-muted-foreground">{new Date(c.date).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}</p>}
                  <p className="mt-2 text-sm text-muted-foreground">{c.detail}</p>
                  {c.source && (
                    <a href={c.source} target="_blank" rel="noopener noreferrer" data-testid={`status-source-${c.id}`}
                      className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:text-brand-500">
                      {c.action || "Official source"} <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <p className="mt-6 text-center text-[11px] text-muted-foreground">Sources: IRCC, the CRA and Service Canada. Maple does not rank profiles or optimize applications.</p>
    </div>
  );
}
