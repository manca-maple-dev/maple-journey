import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  Sun, Cloud, CloudSun, CloudRain, CloudDrizzle, CloudFog, CloudLightning, Snowflake,
  Wind, Droplets, ExternalLink, CalendarDays, MapPin, Send, ArrowRight, Sparkles, ShieldCheck,
  CreditCard, Languages, HeartPulse, Briefcase, Baby, FileText, AlertCircle, CheckCircle2, Clock,
} from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useMaple } from "@/context/MapleContext";
import { useNavigate } from "react-router-dom";
import { ProfileCompletionBar } from "@/components/profile/ProfileCompletion";

const WEATHER_ICON = {
  sun: Sun, cloud: Cloud, "cloud-sun": CloudSun, "cloud-rain": CloudRain,
  "cloud-drizzle": CloudDrizzle, "cloud-fog": CloudFog, "cloud-lightning": CloudLightning, snowflake: Snowflake,
};

const ESSENTIALS = [
  {
    id: "sin",
    title: "Get your SIN",
    desc: "Apply for your Social Insurance Number through Service Canada.",
    href: "https://www.canada.ca/en/employment-social-development/services/sin.html",
  },
  {
    id: "health",
    title: "Start health coverage",
    desc: "Check provincial health card eligibility and wait periods.",
    href: "https://www.canada.ca/en/health-canada/services/health-care-system.html",
  },
  {
    id: "jobbank",
    title: "Build a Canadian resume",
    desc: "Use Job Bank tools and role-specific career guidance.",
    href: "https://www.jobbank.gc.ca/findajob/resources/write-good-resume",
  },
  {
    id: "help211",
    title: "Find local newcomer support (211)",
    desc: "Housing, food, legal and mental-health referrals in your area.",
    href: "https://211.ca/",
  },
];

const QUICK_WINS = [
  { id: "resume", title: "Build your resume", desc: "Choose a clean template and edit with Maple guidance.", icon: FileText, onClick: () => navigate("/app/resume") },
  { id: "bank", title: "Open a bank account", desc: "Compare newcomer-friendly banks and starter offers.", icon: CreditCard, onClick: () => window.open("https://www.canada.ca/en/financial-consumer-agency/services/banking/opening-bank-account.html", "_blank", "noreferrer") },
  { id: "language", title: "Find language classes", desc: "ESL, French and settlement language support.", icon: Languages, onClick: () => window.open("https://www.canada.ca/en/immigration-refugees-citizenship/services/new-immigrants/new-life-canada/language-training.html", "_blank", "noreferrer") },
  { id: "health", title: "Set up health coverage", desc: "Check province rules and waiting periods.", icon: HeartPulse, onClick: () => navigate("/app/accessibilities") },
  { id: "work", title: "Improve your job search", desc: "Resume help and role matching for newcomers.", icon: Briefcase, onClick: () => navigate("/app/jobs") },
  { id: "family", title: "Family & childcare support", desc: "Helpful links for parents and households.", icon: Baby, onClick: () => navigate("/app/benefits") },
  { id: "docs", title: "Organize your documents", desc: "Keep SIN, permits and deadlines in one place.", icon: FileText, onClick: () => navigate("/app/assessment") },
];

function timeAgo(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const days = Math.round((Date.now() - d) / 86400000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/* Flat skeleton — single-colour fill, no shimmer (per briefing spec). */
function Skel({ className = "" }) {
  return <div className={`rounded-2xl bg-[#E8E3DC] dark:bg-[#2A2A2A] ${className}`} />;
}

export default function MapleHome() {
  const { user } = useAuth();
  const { openWith } = useMaple();
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  const [data, setData] = useState(null);
  const [ask, setAsk] = useState("");
  const [newJobsCount, setNewJobsCount] = useState(0);
  const [showJobsToast, setShowJobsToast] = useState(false);
  const profile = user?.profile || {};
  const pathway = (profile.immigration_category || "").toLowerCase();
  const checklistKey = `mj-week1-checklist-${user?.id || "anon"}`;
  const liveDateLabel = useMemo(() => new Date().toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  }), []);
  const journeyStage = profile.arrival_status ? profile.arrival_status.replace(/_/g, " ") : "getting settled";
  const locationLabel = profile.current_city || profile.province_of_residence || profile.intended_province || "Canada";

  const [weekChecklist, setWeekChecklist] = useState(() => {
    try {
      const raw = localStorage.getItem("mj-week1-checklist");
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem("mj-week1-checklist", JSON.stringify(weekChecklist));
    } catch {
      // ignore storage errors
    }
  }, [weekChecklist]);

  const weekTasks = useMemo(() => ([
    { id: "sin", label: "Get your SIN number" },
    { id: "bank", label: "Open a newcomer-friendly bank account" },
    { id: "health", label: "Start health card/coverage process" },
    { id: "docs", label: "Save permit and deadline documents in one folder" },
  ]), []);

  const pathwayAction = useMemo(() => {
    if (pathway === "student") {
      return {
        id: "student-path",
        title: "Plan your study permit deadlines",
        body: "Track expiry, enrollment letters, and renewal windows early.",
        cta: "Get student steps",
        onClick: () => { openWith("I am a student. Give me a simple study permit renewal checklist with deadlines."); navigate("/app/chat"); },
      };
    }
    if (pathway === "temp_foreign_worker" || pathway === "visitor_work_permit") {
      return {
        id: "worker-path",
        title: "Protect your work permit status",
        body: "Review renewal timing, employer conditions, and status-safe next steps.",
        cta: "Get work permit plan",
        onClick: () => { openWith("I have a work permit. What should I do this month to stay compliant and avoid status issues?"); navigate("/app/chat"); },
      };
    }
    if (pathway === "refugee_claimant" || pathway === "protected_person") {
      return {
        id: "refugee-path",
        title: "Find legal aid and settlement support",
        body: "Get immediate, low-cost legal and community support options by province.",
        cta: "Open legal support",
        onClick: () => navigate("/app/legal"),
      };
    }
    if (pathway === "spousal_family") {
      return {
        id: "family-path",
        title: "Check family benefits and services",
        body: "See support programs for dependents, schooling, and newcomer families.",
        cta: "View benefits",
        onClick: () => navigate("/app/benefits"),
      };
    }
    return null;
  }, [navigate, openWith, pathway]);

  const doneCount = weekTasks.filter((t) => !!weekChecklist[`${checklistKey}:${t.id}`]).length;

  const priorityActions = [
    !data?.profile_completed && {
      id: "complete-profile",
      title: "Finish onboarding",
      body: "Unlock personalized guidance, deadlines, and location-aware recommendations.",
      cta: "Complete now",
      onClick: () => navigate("/app/onboarding"),
    },
    pathwayAction,
    {
      id: "ask-maple",
      title: "Ask Maple your top question",
      body: "Get a grounded answer with official source links you can trust.",
      cta: "Open assistant",
      onClick: () => navigate("/app/chat"),
    },
    {
      id: "jobs",
      title: "Check matched jobs",
      body: newJobsCount > 0 
        ? `${newJobsCount} new job${newJobsCount !== 1 ? 's' : ''} posted in your area today.`
        : "Review opportunities aligned with your newcomer pathway.",
      cta: "View jobs",
      onClick: () => navigate("/app/jobs"),
      badge: newJobsCount > 0 ? `${newJobsCount} new` : null,
    },
    {
      id: "legal",
      title: "Review legal help",
      body: "Find regulated help and official resources for complex cases.",
      cta: "Open legal help",
      onClick: () => navigate("/app/legal"),
    },
  ].filter(Boolean);

  useEffect(() => {
    let alive = true;
    api.get("/overview").then((r) => alive && setData(r.data)).catch(() => alive && setData({ greeting: "", news: [], holidays: [] }));
    
    // Fetch new jobs count for notification
    api.get("/jobs/new-count").then((r) => {
      if (alive && r.data.new_jobs > 0) {
        setNewJobsCount(r.data.new_jobs);
        setShowJobsToast(true);
        setTimeout(() => setShowJobsToast(false), 5000); // Auto-dismiss after 5s
      }
    }).catch(() => {});
    
    return () => { alive = false; };
  }, []);

  const startChat = (prefill) => { if (prefill) openWith(prefill); setAsk(""); };
  const words = (data?.greeting || "").split(" ");
  const WeatherIcon = data?.weather ? (WEATHER_ICON[data.weather.icon] || Cloud) : Cloud;

  return (
    <div className="mx-auto max-w-2xl space-y-6" data-testid="maple-home">
      {/* Jobs toast notification on login */}
      <AnimatePresence>
        {showJobsToast && newJobsCount > 0 && (
          <motion.button
            onClick={() => navigate("/app/jobs")}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex w-full items-center gap-3 rounded-xl border border-green-500/30 bg-green-50 p-3 text-left transition-colors hover:bg-green-100 dark:bg-green-500/10"
          >
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-green-100 text-green-700 dark:bg-green-500/20">
              <Briefcase className="h-4 w-4" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-semibold text-green-900 dark:text-green-200">{newJobsCount} new job{newJobsCount !== 1 ? 's' : ''} in your area</span>
              <span className="block text-xs text-green-700/70 dark:text-green-300/70">Tap to view matched opportunities</span>
            </span>
            <ArrowRight className="h-4 w-4 shrink-0 text-green-700" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Greeting — words fade in with a 30ms stagger */}
      <div className="pt-1">
        {data ? (
          <h1 className="font-display text-2xl font-bold leading-snug tracking-tight sm:text-3xl" data-testid="maple-greeting">
            {words.map((w, i) => (
              <motion.span key={i} initial={reduce ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: reduce ? 0 : i * 0.03, duration: 0.18 }} className="inline-block">
                {w}&nbsp;
              </motion.span>
            ))}
          </h1>
        ) : (
          <Skel className="h-8 w-3/4" />
        )}
        <p className="mt-1 text-xs text-muted-foreground">Cited from IRCC and official sources. Nothing here is generated without a source.</p>
      </div>

      <section className="grid gap-3 lg:grid-cols-[1.2fr,0.8fr]" data-testid="home-live-overview">
        <div className="rounded-2xl border border-border bg-card p-5">
          <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-muted-foreground">
            <span className="rounded-full bg-brand-500/10 px-2.5 py-1 text-brand-600">Live today</span>
            <span>{liveDateLabel}</span>
            {data?.generated_at && <span>• Updated {timeAgo(data.generated_at)}</span>}
          </div>
          <h2 className="mt-3 font-display text-xl font-semibold">Your day in {locationLabel}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Maple is prioritizing what matters for your {pathway ? pathway.replace(/_/g, " ") : "journey"} while you are {journeyStage}.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-border bg-background p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Location</p>
              <p className="mt-1 text-sm font-semibold">{locationLabel}</p>
            </div>
            <div className="rounded-xl border border-border bg-background p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Pathway</p>
              <p className="mt-1 text-sm font-semibold capitalize">{pathway ? pathway.replace(/_/g, " ") : "Not set yet"}</p>
            </div>
            <div className="rounded-xl border border-border bg-background p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Focus today</p>
              <p className="mt-1 text-sm font-semibold">{priorityActions[0]?.title || "Review your next best step"}</p>
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-border bg-card p-5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Personalization signals</p>
          <div className="mt-3 space-y-3">
            <div className="rounded-xl border border-border bg-background p-3">
              <ProfileCompletionBar profile={profile} size="sm" />
            </div>
            <div className="flex items-start justify-between gap-3 rounded-xl border border-border bg-background p-3">
              <div>
                <p className="text-sm font-semibold">Arrival progress</p>
                <p className="text-xs text-muted-foreground">Used to tune reminders, deadlines, and service recommendations.</p>
              </div>
              <span className="rounded-full bg-secondary px-2.5 py-1 text-xs font-semibold text-foreground capitalize">{journeyStage}</span>
            </div>
            <button
              type="button"
              onClick={() => navigate(data?.profile_completed ? "/app/profile" : "/app/onboarding")}
              className="w-full rounded-xl border border-brand-500/30 bg-brand-50 px-4 py-3 text-left transition-colors hover:bg-brand-100 dark:bg-brand-500/10"
            >
              <span className="block text-sm font-semibold">Improve my personalization</span>
              <span className="mt-1 block text-xs text-muted-foreground">Add more about your city, status, family, and priorities so Maple can tune every page better.</span>
            </button>
          </div>
        </div>
      </section>

      {/* Complete-profile banner (empty/partial state) */}
      {data && !data.profile_completed && (
        <button onClick={() => navigate("/app/onboarding")} data-testid="complete-profile-banner"
          className="flex w-full items-center gap-3 rounded-2xl border border-brand-500/30 bg-brand-50 p-4 text-left transition-colors hover:bg-brand-100 dark:bg-brand-500/10">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-brand-500 text-white"><Sparkles className="h-4.5 w-4.5" /></span>
          <span className="min-w-0 flex-1">
            <span className="block text-sm font-semibold">Complete your profile to personalize this</span>
            <span className="block text-xs text-muted-foreground">You're seeing general news — finish onboarding for briefings matched to your city and status.</span>
          </span>
          <ArrowRight className="h-4 w-4 shrink-0 text-brand-600" />
        </button>
      )}

      {/* Action rail — only show relevant, incomplete actions */}
      {priorityActions.length > 0 && (
        <section data-testid="priority-actions">
          <h2 className="mb-3 font-display text-lg font-semibold">What to do next</h2>
          <div className="space-y-3">
            {priorityActions.map((a) => (
              <button key={a.id} onClick={a.onClick} className="w-full rounded-2xl border border-border bg-card p-4 text-left transition-colors hover:border-brand-400">
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10">
                    {a.id === "jobs" && a.badge ? (
                      <span className="relative">
                        <Briefcase className="h-4 w-4" />
                        <span className="absolute -right-2 -top-2 h-4 w-4 rounded-full bg-green-500 text-[10px] font-bold text-white flex items-center justify-center">
                          {newJobsCount}
                        </span>
                      </span>
                    ) : (
                      <Sparkles className="h-4 w-4" />
                    )}
                  </span>
                  <span className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="block text-sm font-semibold">{a.title}</span>
                      {a.badge && (
                        <span className="rounded-full bg-green-100 px-2 py-0.5 text-[11px] font-bold text-green-700 dark:bg-green-500/20 whitespace-nowrap">
                          {a.badge}
                        </span>
                      )}
                    </div>
                    <span className="mt-1 block text-xs text-muted-foreground">{a.body}</span>
                    <span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-brand-600">{a.cta} <ArrowRight className="h-3.5 w-3.5" /></span>
                  </span>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Status & Deadlines — Show user's key dates and Resume CTA */}
      {profile && (
        <section className="rounded-2xl border-2 border-maple/30 bg-gradient-to-br from-maple/5 to-maple/10 p-6 dark:from-maple-900/20 dark:to-maple-900/30" data-testid="status-deadlines">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <h2 className="font-display text-lg font-semibold flex items-center gap-2">
                <Clock className="h-5 w-5 text-maple" />
                Status & Deadlines
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                Key dates in your immigration journey. Keep these updated for accurate reminders.
              </p>
            </div>
          </div>

          {/* Display key dates */}
          <div className="grid gap-3 sm:grid-cols-2 mb-4">
            {profile.arrival_date_canada && (
              <div className="rounded-lg border border-maple/20 bg-white/50 dark:bg-black/20 p-3">
                <p className="text-xs font-semibold text-muted-foreground uppercase">Arrived in Canada</p>
                <p className="mt-1 text-sm font-semibold">
                  {new Date(profile.arrival_date_canada).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}
                </p>
              </div>
            )}
            {profile.work_permit_expiry && (
              <div className="rounded-lg border-l-2 border-l-maple bg-white/50 dark:bg-black/20 p-3">
                <p className="text-xs font-semibold text-muted-foreground uppercase">Work Permit Expires</p>
                <p className="mt-1 text-sm font-semibold">
                  {new Date(profile.work_permit_expiry).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}
                </p>
              </div>
            )}
            {profile.study_permit_expiry && (
              <div className="rounded-lg border-l-2 border-l-brand-500 bg-white/50 dark:bg-black/20 p-3">
                <p className="text-xs font-semibold text-muted-foreground uppercase">Study Permit Expires</p>
                <p className="mt-1 text-sm font-semibold">
                  {new Date(profile.study_permit_expiry).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}
                </p>
              </div>
            )}
            {profile.pr_received_date && (
              <div className="rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-950/20 p-3">
                <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-300 uppercase">Became Permanent Resident</p>
                <p className="mt-1 text-sm font-semibold text-emerald-900 dark:text-emerald-100">
                  {new Date(profile.pr_received_date).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}
                </p>
              </div>
            )}
          </div>

          {/* Build Resume CTA */}
          <button
            onClick={() => navigate("/app/resume")}
            className="w-full rounded-xl border-2 border-maple bg-gradient-to-r from-maple to-maple/80 hover:from-maple/90 hover:to-maple/70 text-white px-4 py-3 font-semibold transition-all shadow-sm hover:shadow-md"
          >
            <FileText className="mr-2 inline h-4 w-4" />
            Build Your Resume Now
          </button>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Use your profile info + deadlines to create a professional resume for job applications
          </p>
        </section>
      )}

      {/* Week-one progress — Hide when complete, show celebration instead */}
      {doneCount < weekTasks.length && (
        <section className="rounded-2xl border border-border bg-card p-4" data-testid="week-one-checklist">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-display text-base font-semibold">Your first-week checklist</h2>
            <span className="text-xs font-medium text-muted-foreground">{doneCount}/{weekTasks.length} done</span>
          </div>
          <div className="space-y-2.5">
            {weekTasks.map((task) => {
              const key = `${checklistKey}:${task.id}`;
              const done = !!weekChecklist[key];
              return (
                <button
                  key={task.id}
                  onClick={() => setWeekChecklist((s) => ({ ...s, [key]: !done }))}
                  data-testid={`week-task-${task.id}`}
                  className={`flex w-full items-center gap-2 rounded-xl border px-3 py-2 text-left text-sm transition-colors ${done ? "border-brand-500/40 bg-brand-50/60 text-foreground dark:bg-brand-500/10" : "border-border bg-background"}`}
                >
                  <span className={`grid h-4 w-4 place-items-center rounded border text-[10px] ${done ? "border-brand-500 bg-brand-500 text-white" : "border-muted-foreground/40"}`}>
                    {done ? "✓" : ""}
                  </span>
                  <span>{task.label}</span>
                </button>
              );
            })}
          </div>
        </section>
      )}

      {/* Celebration — when all first-week tasks complete */}
      {doneCount === weekTasks.length && doneCount > 0 && (
        <section className="rounded-2xl border border-brand-500/30 bg-gradient-to-br from-brand-50 to-brand-50/50 p-5 dark:from-brand-500/5 dark:to-brand-500/10" data-testid="checklist-complete">
          <div className="flex items-start gap-3">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-500 text-2xl">🎉</span>
            <div className="min-w-0 flex-1">
              <h2 className="font-display text-base font-bold text-brand-700 dark:text-brand-300">Week one complete!</h2>
              <p className="mt-1 text-sm text-brand-600/90 dark:text-brand-400/90">
                You've tackled the essentials. Now it's time to focus on the next steps in your settlement journey.
              </p>
              <button
                type="button"
                onClick={() => { openWith("I've completed my first week. What should I focus on next in my journey?"); navigate("/app/chat"); }}
                className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-brand-500 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-brand-600"
              >
                <Sparkles className="h-3.5 w-3.5" /> Ask Maple what's next
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Essentials — only show if profile complete (so content is personalized) */}
      {data?.profile_completed && (
        <section data-testid="essentials-hub">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-display text-lg font-semibold">Essentials for this week</h2>
            <span className="rounded-full bg-secondary px-2.5 py-1 text-[11px] font-medium text-muted-foreground">Official links</span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {ESSENTIALS.map((item) => (
              <a
                key={item.id}
                href={item.href}
                target="_blank"
                rel="noopener noreferrer"
                data-testid={`essential-${item.id}`}
                className="rounded-2xl border border-border bg-card p-4 transition-colors hover:border-brand-400"
              >
                <p className="text-sm font-semibold leading-tight">{item.title}</p>
                <p className="mt-1 text-xs text-muted-foreground">{item.desc}</p>
                <span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-brand-600">
                  Open resource <ExternalLink className="h-3.5 w-3.5" />
                </span>
              </a>
            ))}
          </div>
          <div className="mt-3 rounded-xl border border-amber-500/30 bg-amber-500/5 px-3.5 py-2.5 text-xs text-amber-800 dark:text-amber-300">
            <span className="inline-flex items-center gap-1.5 font-medium"><ShieldCheck className="h-3.5 w-3.5" /> In immediate danger? Call 911 now.</span>
          </div>
        </section>
      )}

      {/* Quick wins — only show relevant ones based on profile, hide if profile incomplete */}
      {data?.profile_completed && (
        <section data-testid="quick-wins" className="rounded-2xl border border-border bg-card p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <h2 className="font-display text-lg font-semibold">Quick wins for newcomers</h2>
              <p className="text-xs text-muted-foreground">A few high-value actions to make the app feel immediately useful.</p>
            </div>
            <span className="rounded-full bg-brand-500/10 px-2.5 py-1 text-[11px] font-semibold text-brand-600">One tap</span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {QUICK_WINS.map((item) => (
              <button
                key={item.id}
                onClick={item.onClick}
                data-testid={`quick-win-${item.id}`}
                className="group flex items-start gap-3 rounded-2xl border border-border bg-background p-4 text-left transition-colors hover:border-brand-400"
              >
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-500/10 text-brand-600">
                  <item.icon className="h-4.5 w-4.5" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-semibold">{item.title}</span>
                  <span className="mt-1 block text-xs text-muted-foreground">{item.desc}</span>
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Weather — only show if we have location + weather data */}
      {data && data.weather && locationLabel !== "Canada" && (
        <div className="flex items-center gap-4 rounded-2xl border border-border bg-card p-5" data-testid="weather-card">
          <div className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/10"><WeatherIcon className="h-7 w-7" /></div>
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline gap-2">
              <span className="font-display text-3xl font-bold">{data.weather.temperature != null ? `${data.weather.temperature}°` : "—"}</span>
              <span className="text-sm font-medium text-muted-foreground">{data.weather.condition}</span>
            </div>
            <div className="mt-1 flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{data.weather.city}</span>
              <span className="flex items-center gap-1"><Droplets className="h-3.5 w-3.5" />{data.weather.precipitation ?? 0} mm</span>
              <span className="flex items-center gap-1"><Wind className="h-3.5 w-3.5" />{data.weather.wind ?? "—"} km/h</span>
            </div>
          </div>
        </div>
      )}

      {/* Days since arrival — only show if we have real data */}
      {data?.days_since_arrival != null && data.days_since_arrival > 0 && (
        <p className="-mt-2 text-xs text-muted-foreground" data-testid="days-arrival">
          <span className="font-semibold text-foreground">Day {data.days_since_arrival}</span> in Canada — you're doing great.
        </p>
      )}

      {/* Holiday pills — only show if we have actual holidays coming */}
      {data?.holidays && data.holidays.length > 0 && (
        <div>
          <h2 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground"><CalendarDays className="h-3.5 w-3.5" /> Upcoming days off</h2>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {data.holidays.map((h) => (
              <div key={h.name} data-testid="holiday-pill"
                className="flex shrink-0 items-center gap-2 rounded-full border border-border bg-card px-3.5 py-2">
                <span className={`h-2 w-2 rounded-full ${h.kind === "religious" ? "bg-maple" : "bg-brand-500"}`} />
                <span className="text-sm font-medium">{h.name}</span>
                <span className="text-xs text-muted-foreground">{h.label} · in {h.days}d</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Briefing — only show if profile complete & we have real data */}
      {data?.profile_completed && (
        <div>
          <h2 className="mb-3 font-display text-lg font-semibold">Today's briefing</h2>
          <div className="space-y-3">
            <AnimatePresence>
              {data?.news && data.news.length > 0 ? (
                data.news.map((n, i) => (
                  <motion.a key={n.link || i} href={n.link} target="_blank" rel="noopener noreferrer"
                    initial={reduce ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.18, delay: reduce ? 0 : i * 0.04 }}
                    data-testid="news-item"
                    className="block rounded-2xl border border-border bg-card p-5 transition-colors hover:border-brand-400">
                    <p className="font-display font-semibold leading-snug">{n.title}</p>
                    {n.summary && <p className="mt-1.5 text-sm text-muted-foreground line-clamp-2">{n.summary}</p>}
                    <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                      <span className="rounded-full bg-secondary px-2 py-0.5 font-medium">{n.source?.split("—")[0]?.trim() || "IRCC"}</span>
                      {n.updated && <span>· {timeAgo(n.updated)}</span>}
                      <ExternalLink className="ml-auto h-3.5 w-3.5" />
                    </div>
                  </motion.a>
                ))
              ) : (
                <p className="rounded-2xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground" data-testid="news-empty">
                  No new immigration news at the moment. Updates appear as soon as IRCC publishes them, and accuracy improves as Maple ingests additional verified sources.
                </p>
              )}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Sponsored — only show if we have inventory */}
      {data?.ads && data.ads.length > 0 && data.ads.map((a) => (
        a?.url ? (
          <a key={a.id} href={a.url} target="_blank" rel="noopener noreferrer" data-testid="ad-tile" className="block rounded-2xl border border-border bg-card p-4">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Sponsored · Newcomer Service</span>
            <p className="mt-1 font-medium">{a.title}</p>
            {a.body && <p className="text-sm text-muted-foreground">{a.body}</p>}
          </a>
        ) : (
          <div key={a.id} data-testid="ad-tile" className="rounded-2xl border border-border bg-card p-4">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Sponsored · Newcomer Service</span>
            <p className="mt-1 font-medium">{a.title}</p>
            {a.body && <p className="text-sm text-muted-foreground">{a.body}</p>}
          </div>
        )
      ))}

      {/* Ask Maple — slim, actionable */}
      <form onSubmit={(e) => { e.preventDefault(); startChat(ask.trim()); }} className="sticky bottom-4 flex items-center gap-2 rounded-full border border-border bg-card/95 p-1.5 pl-4 shadow-lg backdrop-blur">
        <input value={ask} onChange={(e) => setAsk(e.target.value)} placeholder="Ask Maple about today's briefing…" data-testid="maple-ask-input"
          className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground" />
        <button type="submit" data-testid="maple-ask-send" className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand-500 text-white transition-transform hover:-translate-y-0.5"><Send className="h-4 w-4" /></button>
      </form>

      <div className="flex gap-2 overflow-x-auto pb-1" data-testid="quick-prompts">
        {["Do I qualify for PGWP?", "How do I renew my permit?", "What should I do this week?"].map((q) => (
          <button key={q} type="button" onClick={() => startChat(q)}
            className="shrink-0 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground">
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
