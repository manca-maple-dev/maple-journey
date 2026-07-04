import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  Sparkles, ArrowRight, ArrowLeft, Check, Plane, Home, GraduationCap,
  Briefcase, Users, Shield, Globe, HeartHandshake, MapPin, Loader2, AlertCircle,
} from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { CountrySelect } from "@/components/common/CountrySelect";
import { validateDOB, validatePostalPrefix, validateNonNegative } from "@/lib/validation";

const DRAFT_KEY = "mj_onboarding_v2";

/* ---------- option catalogues (blueprint questionnaire) ---------- */
const ARRIVAL = [
  { value: "planning", label: "Still planning my move", icon: Plane },
  { value: "just_arrived", label: "Just arrived", desc: "Less than 3 months", icon: MapPin },
  { value: "recent", label: "Here a few months", desc: "3–12 months", icon: Home },
  { value: "settled", label: "Settled in", desc: "Over a year", icon: HeartHandshake },
];
const CATEGORY = [
  { value: "express_entry", label: "Express Entry", desc: "Federal skilled worker / trades / CEC", icon: Globe },
  { value: "provincial_nominee", label: "Provincial Nominee (PNP)", icon: MapPin },
  { value: "student", label: "Study permit", desc: "College or university", icon: GraduationCap },
  { value: "temp_foreign_worker", label: "Work permit", desc: "Employed or job-seeking", icon: Briefcase },
  { value: "spousal_family", label: "Family / spousal", desc: "Sponsored by a relative", icon: Users },
  { value: "refugee_claimant", label: "Refugee claimant", icon: Shield },
  { value: "protected_person", label: "Protected person", icon: Shield },
  { value: "visitor_work_permit", label: "Visitor / other permit", icon: Plane },
  { value: "other", label: "Not sure yet", desc: "Help me figure it out", icon: Sparkles },
];
const SUBTYPE = {
  express_entry: ["Federal Skilled Worker", "Federal Skilled Trades", "Canadian Experience Class"],
  provincial_nominee: ["Skilled Worker stream", "Tech / in-demand stream", "Entrepreneur", "Other"],
  student: ["University", "College", "Language school", "Other"],
  temp_foreign_worker: ["LMIA-based", "LMIA-exempt", "Open work permit", "Post-Graduation (PGWP)"],
};
const GENDER = [
  { value: "woman", label: "Woman" }, { value: "man", label: "Man" },
  { value: "non_binary", label: "Non-binary" }, { value: "self_describe", label: "Prefer to self-describe" },
  { value: "prefer_not", label: "Prefer not to say" },
];
const LANGUAGES = ["English", "French", "Mandarin", "Cantonese", "Hindi", "Punjabi", "Tagalog", "Arabic", "Spanish", "Portuguese", "Urdu", "Tamil", "Korean", "Vietnamese", "Farsi", "Russian"];
const PROVINCES = [
  { value: "ON", label: "Ontario" }, { value: "BC", label: "British Columbia" }, { value: "QC", label: "Quebec" },
  { value: "AB", label: "Alberta" }, { value: "MB", label: "Manitoba" }, { value: "SK", label: "Saskatchewan" },
  { value: "NS", label: "Nova Scotia" }, { value: "NB", label: "New Brunswick" }, { value: "NL", label: "Newfoundland & Labrador" },
  { value: "PE", label: "Prince Edward Island" }, { value: "NT", label: "Northwest Territories" }, { value: "YT", label: "Yukon" },
  { value: "NU", label: "Nunavut" }, { value: "undecided", label: "Not decided yet" },
];
const MARITAL = [
  { value: "single", label: "Single" }, { value: "married", label: "Married" }, { value: "common_law", label: "Common-law" },
  { value: "separated", label: "Separated" }, { value: "divorced", label: "Divorced" }, { value: "widowed", label: "Widowed" },
];
const EMPLOYMENT = [
  { value: "employed", label: "Employed" }, { value: "seeking", label: "Looking for work" },
  { value: "student", label: "Studying" }, { value: "not_seeking", label: "Not working right now" },
];
const BANKING = [
  { value: "none", label: "No account yet" }, { value: "basic", label: "A basic account" }, { value: "full", label: "Fully set up" },
];
const HEALTH = [
  { value: "provincial", label: "Provincial plan (e.g. OHIP)" }, { value: "employer", label: "Through my employer" },
  { value: "waiting", label: "In the waiting period" }, { value: "none", label: "No coverage yet" },
];
const RELIGION = ["No affiliation", "Christianity", "Islam", "Hinduism", "Sikhism", "Buddhism", "Judaism", "Other", "Prefer not to say"];
const CUISINE = ["Halal", "Vegetarian", "Kosher", "South Asian", "East Asian", "Middle Eastern", "African", "Caribbean", "Latin American", "Mediterranean"];
const HOBBIES = ["Sports", "Cooking", "Faith community", "Music", "Reading", "Tech", "Volunteering", "Outdoors", "Arts", "Gaming", "Fitness", "Family time"];
const UPDATE_FREQUENCY = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "biweekly", label: "Every 2 weeks" },
  { value: "monthly", label: "Monthly" },
];
const RESPONSE_LANGUAGES = [
  { value: "english", label: "English" },
  { value: "french", label: "French" },
  { value: "auto", label: "Auto-detect from profile" },
];
const LEGAL_TOPICS = [
  "Refugee claim",
  "Work permit",
  "Study permit",
  "PR pathway",
  "Hearing prep",
  "Detention and removal",
  "Family sponsorship",
  "Citizenship",
  "Appeals",
  "Housing rights",
  "Employment rights",
  "Benefits access",
];

/* ---------- scene definitions ---------- */
const SCENES = [
  { id: "intro", kind: "intro", section: null },
  { id: "name", kind: "fields", section: "About you", eyebrow: "First, the basics", title: "What should Maple call you?", optional: false,
    requiredKeys: ["preferred_name"],
    fields: [
      { key: "preferred_name", label: "Preferred name", type: "text", placeholder: "e.g. Alex", required: true },
      { key: "date_of_birth", label: "Date of birth (optional)", type: "date", validate: validateDOB },
      { key: "gender_identity", label: "Gender (optional)", type: "select", options: GENDER },
      { key: "pronouns", label: "Pronouns (optional)", type: "text", placeholder: "e.g. she/her" },
    ] },
  { id: "arrival", kind: "options", key: "arrival_status", section: "About you", eyebrow: "Your journey", title: "Where are you in your move to Canada?", options: ARRIVAL },
  { id: "category", kind: "options", key: "immigration_category", section: "Your pathway", eyebrow: "Your pathway", title: "Which path best describes you?", subtitle: "This shapes everything I show you. There's no wrong answer.", options: CATEGORY },
  { id: "subtype", kind: "chips-single", key: "visa_subtype", section: "Your pathway", eyebrow: "Your pathway", title: "Any more detail on that?", optional: true,
    optionsFor: (a) => SUBTYPE[a.immigration_category] || [], showIf: (a) => !!SUBTYPE[a.immigration_category] },
  { id: "origin", kind: "country", section: "Where you're from", eyebrow: "Where you're from", title: "Tell me about your roots", optional: true,
    fields: [{ key: "country_of_birth", label: "Country of birth" }, { key: "country_of_citizenship", label: "Country of citizenship" }] },
  { id: "languages", kind: "chips", key: "languages_spoken", section: "Where you're from", eyebrow: "Where you're from", title: "Which languages do you speak?", subtitle: "Pick all that apply.", options: LANGUAGES, optional: true },
  { id: "location", kind: "fields", section: "Where you'll live", eyebrow: "Where you'll live", title: "Where in Canada are you headed?", optional: true,
    fields: [{ key: "current_city", label: "City", type: "text", placeholder: "e.g. Toronto" }, { key: "intended_province", label: "Province", type: "select", options: PROVINCES }, { key: "current_postal_prefix", label: "Postal prefix (optional)", type: "text", placeholder: "e.g. M5V", validate: validatePostalPrefix }] },
  { id: "dates", kind: "fields", section: "Key dates", eyebrow: "Key dates", title: "A couple of important dates", subtitle: "Leave blank if they don't apply.", optional: true,
    fields: [{ key: "arrival_date_canada", label: "Arrival date in Canada", type: "date" }, { key: "work_permit_expiry", label: "Work permit expiry", type: "date", showIf: (a) => ["temp_foreign_worker", "visitor_work_permit", "tn_visa"].includes(a.immigration_category) }, { key: "study_permit_expiry", label: "Study permit expiry", type: "date", showIf: (a) => a.immigration_category === "student" }] },
  { id: "household", kind: "fields", section: "Your household", eyebrow: "Your household", title: "Who's making the move with you?", optional: true,
    fields: [{ key: "marital_status", label: "Marital status", type: "select", options: MARITAL }, { key: "dependents", label: "Number of dependents", type: "number", placeholder: "0", validate: validateNonNegative }, { key: "housing_status", label: "Housing", type: "select", options: [{ value: "planning", label: "Still arranging" }, { value: "renting", label: "Renting" }, { value: "hosted", label: "Staying with family/friends" }, { value: "shelter", label: "Temporary shelter" }, { value: "own", label: "I own a home" }] }] },
  { id: "work", kind: "fields", section: "Your work", eyebrow: "Your work", title: "What do you do?", optional: true,
    fields: [{ key: "employment_status", label: "Right now I am…", type: "select", options: EMPLOYMENT }, { key: "current_occupation", label: "Occupation / field", type: "text", placeholder: "e.g. Software developer" }, { key: "years_experience", label: "Years of experience", type: "number", placeholder: "0", validate: validateNonNegative }] },
  { id: "money", kind: "fields", section: "Getting set up", eyebrow: "Getting set up", title: "The essentials for daily life", subtitle: "This helps me flag what to set up first.", optional: true,
    fields: [{ key: "has_sin", label: "Do you have a SIN?", type: "select", options: [{ value: "yes", label: "Yes" }, { value: "no", label: "Not yet" }] }, { key: "banking_status", label: "Canadian bank account", type: "select", options: BANKING }, { key: "estimated_monthly_income_cad", label: "Approx. monthly income (CAD, optional)", type: "select", options: [{ value: "0-1000", label: "Under $1,000" }, { value: "1000-3000", label: "$1,000–$3,000" }, { value: "3000-6000", label: "$3,000–$6,000" }, { value: "6000+", label: "$6,000+" }, { value: "prefer_not", label: "Prefer not to say" }] }] },
  { id: "health", kind: "fields", section: "Health", eyebrow: "Health", title: "Your health coverage", optional: true,
    fields: [{ key: "province_of_residence", label: "Province of residence", type: "select", options: PROVINCES }, { key: "health_coverage_status", label: "Coverage", type: "select", options: HEALTH }, { key: "has_family_doctor", label: "Do you have a family doctor?", type: "select", options: [{ value: "yes", label: "Yes" }, { value: "no", label: "Not yet" }] }] },
  { id: "legal-preferences", kind: "fields", section: "Legal preferences", eyebrow: "Legal preferences", title: "How should Maple personalize legal updates?", optional: true,
    fields: [
      { key: "update_frequency", label: "Update frequency", type: "select", options: UPDATE_FREQUENCY },
      { key: "preferred_response_language", label: "Preferred response language", type: "select", options: RESPONSE_LANGUAGES },
      { key: "province_focus", label: "Province focus", type: "select", options: [{ value: "national", label: "National" }, ...PROVINCES] },
    ] },
  { id: "legal-topics", kind: "chips", key: "legal_topics", section: "Legal preferences", eyebrow: "Legal preferences", title: "Which legal topics matter most to you?", subtitle: "Pick all that apply.", options: LEGAL_TOPICS, optional: true },
  { id: "faith", kind: "options", key: "religion", section: "You & your community", eyebrow: "You & your community", title: "Do you have a faith or community you'd like reflected?", subtitle: "Optional — it helps me suggest places of worship, groceries and community groups.", options: RELIGION.map((r) => ({ value: r, label: r })), optional: true },
  { id: "cuisine", kind: "chips", key: "cuisine_preferences", section: "You & your community", eyebrow: "You & your community", title: "Any food preferences?", subtitle: "So I can point you to the right grocers and restaurants.", options: CUISINE, optional: true },
  { id: "hobbies", kind: "chips", key: "hobbies", section: "You & your community", eyebrow: "You & your community", title: "What do you love doing?", options: HOBBIES, optional: true },
  { id: "consent", kind: "consent", section: "Consent", eyebrow: "One last thing", title: "How Maple uses your answers", subtitle: "You're in control. You can change any of this later in Settings." },
  { id: "outro", kind: "outro", section: null },
];

const CONSENTS = [
  { key: "consent_data_personalization", label: "Use my answers to personalize my guidance", required: true },
  { key: "consent_maple_companion", label: "Let Maple proactively check in and remind me of deadlines" },
  { key: "consent_marketing_emails", label: "Send me occasional product updates (optional)" },
];

/* ---------- small building blocks ---------- */
function Chip({ active, onClick, children, testId }) {
  return (
    <button type="button" role="checkbox" aria-checked={active} onClick={onClick} data-testid={testId}
      className={`min-h-[44px] rounded-full border px-4 py-2 text-sm font-medium transition-colors ${active ? "border-brand-500 bg-brand-500 text-white shadow-md shadow-brand-500/25" : "border-border bg-card text-foreground hover:border-brand-400"}`}>
      {children}
    </button>
  );
}

function Field({ f, answers, set, error }) {
  if (f.showIf && !f.showIf(answers)) return null;
  const val = answers[f.key] ?? "";
  const errId = `onb-${f.key}-err`;
  const base = `w-full min-h-[44px] rounded-xl border bg-card px-4 py-3 text-sm outline-none transition-colors focus:ring-2 focus:ring-brand-500/40 ${error ? "border-maple focus:ring-maple/30" : "border-border"}`;
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-muted-foreground">{f.label}</span>
      {f.type === "select" ? (
        <select value={val} onChange={(e) => set(f.key, e.target.value)} data-testid={`onb-${f.key}`}
          aria-invalid={!!error} aria-describedby={error ? errId : undefined} className={base}>
          <option value="">Select…</option>
          {f.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      ) : (
        <input type={f.type} value={val} onChange={(e) => set(f.key, e.target.value)} placeholder={f.placeholder}
          data-testid={`onb-${f.key}`} aria-invalid={!!error} aria-describedby={error ? errId : undefined}
          max={f.type === "date" ? new Date().toISOString().split("T")[0] : undefined}
          min={f.type === "number" ? 0 : undefined} className={base} />
      )}
      {error && (
        <span id={errId} role="alert" className="mt-1 flex items-center gap-1 text-xs font-medium text-maple">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />{error}
        </span>
      )}
    </label>
  );
}

/* ---------- main ---------- */
export default function Onboarding() {
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  const { user, refreshUser } = useAuth();
  const headingRef = useRef(null);
  const resumedRef = useRef(false);

  // Load any saved draft so a refresh / accidental exit never loses progress.
  const draft = useMemo(() => {
    try { return JSON.parse(localStorage.getItem(DRAFT_KEY) || "null"); } catch { return null; }
  }, []);

  const [answers, setAnswers] = useState(() => ({
    preferred_name: user?.name?.split(" ")[0] || "",
    ...(user?.profile || {}),
    ...(draft?.answers || {}),
  }));
  const [i, setI] = useState(() => (Number.isInteger(draft?.i) && draft.i > 0 && draft.i < SCENES.length - 1 ? draft.i : 0));
  const [dir, setDir] = useState(1);
  const [saving, setSaving] = useState(false);
  const [showErrors, setShowErrors] = useState(false);

  const initialAnswers = useMemo(() => ({
    preferred_name: user?.name?.split(" ")[0] || "",
    ...(user?.profile || {}),
  }), [user]);

  // Persist draft on every change (skip once fully finished).
  useEffect(() => {
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify({ answers, i })); } catch { /* ignore quota */ }
  }, [answers, i]);

  // Announce resume once, and move keyboard focus to the new scene heading.
  useEffect(() => {
    if (!resumedRef.current && i > 0 && draft?.i) {
      toast.success("Welcome back — I picked up where you left off.");
      resumedRef.current = true;
    }
    const t = setTimeout(() => headingRef.current?.focus?.(), 60);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [i]);

  const set = (k, v) => setAnswers((a) => ({ ...a, [k]: v }));
  const toggleArr = (k, v) => setAnswers((a) => {
    const cur = Array.isArray(a[k]) ? a[k] : [];
    return { ...a, [k]: cur.includes(v) ? cur.filter((x) => x !== v) : [...cur, v] };
  });

  const startOver = () => {
    setAnswers(initialAnswers);
    setShowErrors(false);
    setDir(-1);
    setI(0);
    try { localStorage.removeItem(DRAFT_KEY); } catch { /* ignore */ }
    toast.success("Started fresh onboarding.");
  };

  const scene = SCENES[i];
  const visible = (idx) => { const s = SCENES[idx]; return s && (!s.showIf || s.showIf(answers)); };
  const total = useMemo(() => SCENES.filter((s) => s.kind !== "intro" && s.kind !== "outro" && (!s.showIf || s.showIf(answers))).length, [answers]);
  const stepNo = useMemo(() => SCENES.slice(0, i + 1).filter((s) => s.kind !== "intro" && s.kind !== "outro" && (!s.showIf || s.showIf(answers))).length, [i, answers]);

  // Validation errors surface in real-time as soon as a value is invalid.
  const validateErrors = useMemo(() => {
    if (scene.kind !== "fields") return {};
    const out = {};
    for (const f of scene.fields || []) {
      if (f.showIf && !f.showIf(answers)) continue;
      if (f.validate) { const msg = f.validate(answers[f.key]); if (msg) out[f.key] = msg; }
    }
    return out;
  }, [scene, answers]);
  const hasValidateErrors = Object.keys(validateErrors).length > 0;

  const requiredMet = scene.kind === "fields"
    ? (scene.requiredKeys || []).every((k) => !!answers[k])
    : scene.optional ? true : !!answers[scene.key];
  const consentOk = !!answers.consent_data_personalization;
  // Continue is enabled once required fields are filled; validation errors are
  // surfaced (real-time + on-attempt) rather than silently blocking.
  const canContinue = scene.kind === "consent" ? consentOk : requiredMet;

  const fieldErrorFor = (f) =>
    validateErrors[f.key] || (showErrors && f.required && !answers[f.key] ? "This one's needed to continue" : undefined);

  const next = () => {
    if (scene.kind === "fields" && (hasValidateErrors || !requiredMet)) { setShowErrors(true); return; }
    setShowErrors(false);
    let n = i + 1; while (n < SCENES.length && !visible(n)) n++;
    setDir(1); setI(Math.min(n, SCENES.length - 1));
  };
  const prev = () => {
    setShowErrors(false);
    let n = i - 1; while (n > 0 && !visible(n)) n--;
    setDir(-1); setI(Math.max(n, 0));
  };

  const doLater = () => { navigate("/app"); };

  const finish = async (destination = "/app/plans") => {
    setSaving(true);
    try {
      const payload = { ...answers };
      if (payload.has_sin) payload.has_sin = payload.has_sin === "yes";
      if (payload.has_family_doctor) payload.has_family_doctor = payload.has_family_doctor === "yes";
      await api.put("/profile", payload);
      await refreshUser();
      try { localStorage.removeItem(DRAFT_KEY); } catch { /* ignore */ }
      toast.success("All set — Maple now knows your story.");
      navigate(destination);
    } catch {
      toast.error("Couldn't save just now. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  // Enter advances on text/field scenes for keyboard users.
  const onKeyDown = (e) => {
    if (e.key !== "Enter" || e.shiftKey) return;
    if (["fields", "country", "chips", "chips-single"].includes(scene.kind) && canContinue) {
      e.preventDefault(); next();
    }
  };

  const slide = reduce ? { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } }
    : { initial: { opacity: 0, x: dir * 40 }, animate: { opacity: 1, x: 0 }, exit: { opacity: 0, x: dir * -40 } };

  return (
    <div className="fixed inset-0 z-50 flex flex-col overflow-hidden" data-testid="onboarding">
      {/* cinematic backdrop */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-brand-600 via-brand-700 to-brand-900" aria-hidden="true" />
      <div className="pointer-events-none absolute -left-24 top-10 h-72 w-72 rounded-full bg-maple/40 blur-3xl" aria-hidden="true" />
      <div className="pointer-events-none absolute -right-16 bottom-0 h-80 w-80 rounded-full bg-brand-400/30 blur-3xl" aria-hidden="true" />
      <div className="pointer-events-none absolute inset-0 mj-dot-bg opacity-10" aria-hidden="true" />

      {/* progress */}
      {scene.kind !== "intro" && scene.kind !== "outro" && (
        <div className="relative z-10 px-5 pt-6 sm:px-10">
          <div className="mx-auto flex max-w-xl items-center gap-3">
            <button onClick={doLater} data-testid="onb-do-later"
              className="hidden shrink-0 rounded-full px-3 py-2 text-xs font-medium text-white/70 transition-colors hover:text-white sm:block">
              Do this later
            </button>
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/20" role="progressbar" aria-valuenow={stepNo} aria-valuemin={1} aria-valuemax={total} aria-label="Setup progress">
              <motion.div className="h-full rounded-full bg-white" animate={{ width: `${(stepNo / total) * 100}%` }} transition={{ duration: reduce ? 0 : 0.3 }} />
            </div>
            <span className="text-xs font-semibold text-white/80" aria-live="polite">
              {scene.section ? `${scene.section} · ` : ""}{stepNo}/{total}
            </span>
          </div>
          <p className="mx-auto mt-2 max-w-xl text-center text-[11px] text-white/50 sm:text-left">Every answer sharpens Maple's guidance — the more you share, the more personal your advice.</p>
        </div>
      )}

      <div className="relative z-10 flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto px-5 py-8 sm:px-10">
        <div className="mx-auto grid min-h-full max-w-xl place-items-center">
        <AnimatePresence mode="wait" custom={dir}>
          <motion.div key={scene.id} custom={dir} {...slide}
            transition={{ duration: reduce ? 0 : 0.32, ease: "easeOut" }}
            onKeyDown={onKeyDown}
            className="w-full max-w-xl text-white">

            {/* INTRO */}
            {scene.kind === "intro" && (
              <div className="text-center">
                <motion.div initial={reduce ? false : { scale: 0.85, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.1 }}
                  className="mx-auto grid h-20 w-20 place-items-center rounded-3xl bg-white/15 backdrop-blur">
                  <Sparkles className="h-10 w-10" aria-hidden="true" />
                </motion.div>
                <h1 ref={headingRef} tabIndex={-1} className="mt-8 font-display text-3xl font-bold outline-none sm:text-4xl">Hi, I'm Maple.</h1>
                <p className="mx-auto mt-4 max-w-md text-white/80">A few quick questions so I can guide you with advice that actually fits your life in Canada. Most are optional — skip anything you like.</p>
                <button onClick={next} data-testid="onb-begin"
                  className="mt-8 inline-flex min-h-[44px] items-center gap-2 rounded-full bg-white px-7 py-3.5 font-semibold text-brand-700 transition-transform hover:-translate-y-0.5">
                  Let's begin <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </button>
                <div className="mt-4 flex items-center justify-center gap-3 text-xs text-white/60">
                  <span>Takes about 2 minutes</span>
                  <span aria-hidden="true">·</span>
                  <button onClick={doLater} data-testid="onb-intro-later" className="underline underline-offset-2 hover:text-white">I'll do this later</button>
                </div>
              </div>
            )}

            {/* OUTRO */}
            {scene.kind === "outro" && (
              <div className="text-center">
                <motion.div initial={reduce ? false : { scale: 0.85 }} animate={{ scale: 1 }} className="mx-auto grid h-20 w-20 place-items-center rounded-3xl bg-white/15 backdrop-blur">
                  <Check className="h-10 w-10" aria-hidden="true" />
                </motion.div>
                <h1 ref={headingRef} tabIndex={-1} className="mt-8 font-display text-3xl font-bold outline-none sm:text-4xl">Thanks, {answers.preferred_name || "friend"}.</h1>
                <p className="mx-auto mt-4 max-w-md text-white/80">I've got a clear picture now. From here, everything — your briefing, jobs, benefits and deadlines — is tailored to you.</p>
                <div className="mx-auto mt-6 max-w-md rounded-2xl bg-white/10 p-4 text-left text-sm text-white/85">
                  <p className="font-semibold text-white">What happens next</p>
                  <p className="mt-1">1. We generate your personalized plan.</p>
                  <p>2. Your dashboard gets tailored tasks and deadlines.</p>
                  <p>3. Maple can now answer using your profile context.</p>
                </div>
                <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
                  <button onClick={() => finish("/app/plans")} disabled={saving} data-testid="onb-finish"
                    className="inline-flex min-h-[44px] items-center gap-2 rounded-full bg-white px-7 py-3.5 font-semibold text-brand-700 transition-transform hover:-translate-y-0.5 disabled:opacity-60">
                    {saving ? <><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Saving…</> : <>See my personalized plan <ArrowRight className="h-4 w-4" aria-hidden="true" /></>}
                  </button>
                  <button onClick={() => finish("/app")} disabled={saving} data-testid="onb-finish-dashboard"
                    className="inline-flex min-h-[44px] items-center gap-2 rounded-full border border-white/50 px-7 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-white/10 disabled:opacity-60">
                    Save and go to dashboard
                  </button>
                </div>
              </div>
            )}

            {/* content scenes share a header */}
            {!["intro", "outro"].includes(scene.kind) && (
              <>
                {scene.eyebrow && <p className="text-xs font-semibold uppercase tracking-[0.25em] text-white/60">{scene.eyebrow}</p>}
                <h1 ref={headingRef} tabIndex={-1} className="mt-2 font-display text-2xl font-bold leading-tight outline-none sm:text-3xl">{scene.title}</h1>
                {scene.subtitle && <p className="mt-3 text-white/75">{scene.subtitle}</p>}

                <div className="mt-7 rounded-3xl bg-white/95 p-5 text-foreground shadow-2xl backdrop-blur sm:p-6 dark:bg-card/95">
                  {/* OPTIONS (single-select cards, auto-advance) */}
                  {scene.kind === "options" && (
                    <div role="radiogroup" aria-label={scene.title} className="grid gap-2.5 sm:grid-cols-2">
                      {scene.options.map((o) => {
                        const Icon = o.icon;
                        const active = answers[scene.key] === o.value;
                        return (
                          <button key={o.value} data-testid={`onb-opt-${o.value}`} role="radio" aria-checked={active}
                            onClick={() => { set(scene.key, o.value); setTimeout(next, reduce ? 0 : 180); }}
                            className={`flex min-h-[44px] items-center gap-3 rounded-2xl border p-3.5 text-left transition-colors ${active ? "border-brand-500 bg-brand-50 dark:bg-brand-500/10" : "border-border hover:border-brand-400 hover:bg-secondary/50"}`}>
                            {Icon && <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${active ? "bg-brand-500 text-white" : "bg-secondary text-brand-600"}`}><Icon className="h-5 w-5" aria-hidden="true" /></span>}
                            <span className="min-w-0">
                              <span className="block text-sm font-semibold">{o.label}</span>
                              {o.desc && <span className="block text-xs text-muted-foreground">{o.desc}</span>}
                            </span>
                            {active && <Check className="ml-auto h-4 w-4 text-brand-500" aria-hidden="true" />}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {/* CHIPS multi-select */}
                  {scene.kind === "chips" && (
                    <div role="group" aria-label={scene.title} className="flex flex-wrap gap-2">
                      {scene.options.map((o) => (
                        <Chip key={o} testId={`onb-chip-${o}`} active={(answers[scene.key] || []).includes(o)} onClick={() => toggleArr(scene.key, o)}>{o}</Chip>
                      ))}
                    </div>
                  )}

                  {/* CHIPS single-select */}
                  {scene.kind === "chips-single" && (
                    <div role="radiogroup" aria-label={scene.title} className="flex flex-wrap gap-2">
                      {scene.optionsFor(answers).map((o) => (
                        <Chip key={o} testId={`onb-chip-${o}`} active={answers[scene.key] === o} onClick={() => set(scene.key, o)}>{o}</Chip>
                      ))}
                    </div>
                  )}

                  {/* FIELDS */}
                  {scene.kind === "fields" && (
                    <div className="space-y-4">
                      {scene.fields.map((f) => <Field key={f.key} f={f} answers={answers} set={set} error={fieldErrorFor(f)} />)}
                    </div>
                  )}

                  {/* COUNTRY */}
                  {scene.kind === "country" && (
                    <div className="space-y-4">
                      {scene.fields.map((f) => (
                        <label key={f.key} className="block">
                          <span className="mb-1.5 block text-sm font-medium text-muted-foreground">{f.label}</span>
                          <CountrySelect value={answers[f.key]} onChange={(v) => set(f.key, v)} testId={`onb-${f.key}`} />
                        </label>
                      ))}
                    </div>
                  )}

                  {/* CONSENT */}
                  {scene.kind === "consent" && (
                    <div className="space-y-2.5">
                      <div className="mb-4 rounded-2xl border border-white/15 bg-white/5 p-4 text-sm leading-6 text-white/80">
                        MapleJourney is an AI-powered information and organization tool for newcomers. It is not a law firm, not a government service, and not a substitute for professional advice.
                        <div className="mt-3 flex flex-wrap gap-3 text-xs">
                          <Link to="/privacy" state={{ from: { pathname: "/app/onboarding" } }} className="font-semibold text-white underline underline-offset-2">Privacy Policy</Link>
                          <Link to="/terms" state={{ from: { pathname: "/app/onboarding" } }} className="font-semibold text-white underline underline-offset-2">Terms of Service</Link>
                          <Link to="/cookies" state={{ from: { pathname: "/app/onboarding" } }} className="font-semibold text-white underline underline-offset-2">Cookie Policy</Link>
                          <Link to="/disclaimer" state={{ from: { pathname: "/app/onboarding" } }} className="font-semibold text-white underline underline-offset-2">AI Disclaimer</Link>
                        </div>
                      </div>
                      {CONSENTS.map((c) => {
                        const on = !!answers[c.key];
                        return (
                          <button key={c.key} type="button" role="checkbox" aria-checked={on} onClick={() => set(c.key, !on)} data-testid={`onb-${c.key}`}
                            className={`flex min-h-[44px] w-full items-center gap-3 rounded-2xl border p-3.5 text-left transition-colors ${on ? "border-brand-500 bg-brand-50 dark:bg-brand-500/10" : "border-border hover:border-brand-400"}`}>
                            <span className={`grid h-6 w-6 shrink-0 place-items-center rounded-md border ${on ? "border-brand-500 bg-brand-500 text-white" : "border-border"}`}>{on && <Check className="h-4 w-4" aria-hidden="true" />}</span>
                            <span className="text-sm">{c.label}{c.required && <span className="ml-1 text-xs font-semibold text-brand-600">(required)</span>}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </>
            )}
          </motion.div>
        </AnimatePresence>
        </div>
        </div>

        {/* Persistent bottom nav — always visible so Continue is never hidden */}
        {scene.kind !== "intro" && scene.kind !== "outro" && (
          <div className="relative z-10 shrink-0 border-t border-white/10 bg-brand-900/70 px-5 py-4 backdrop-blur sm:px-10">
            <div className="mx-auto flex max-w-xl items-center justify-between">
                <div className="flex items-center gap-2">
                  <button onClick={prev} data-testid="onb-back" className="inline-flex min-h-[44px] items-center gap-1.5 rounded-full px-4 py-2.5 text-sm font-medium text-white/80 transition-colors hover:text-white">
                    <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Back
                  </button>
                  <button onClick={doLater} data-testid="onb-save-exit" className="inline-flex min-h-[44px] items-center rounded-full px-3 py-2.5 text-xs font-medium text-white/70 transition-colors hover:text-white sm:hidden">
                    Save & exit
                  </button>
                </div>
              <div className="flex items-center gap-3">
                {scene.optional && scene.kind !== "consent" && (
                  <button onClick={next} data-testid="onb-skip" className="min-h-[44px] rounded-full px-4 py-2.5 text-sm font-medium text-white/70 hover:text-white">Skip</button>
                )}
                {scene.kind !== "options" && (
                  <button onClick={next} disabled={!canContinue} data-testid="onb-continue"
                    className="inline-flex min-h-[44px] items-center gap-2 rounded-full bg-white px-6 py-2.5 text-sm font-semibold text-brand-700 transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50">
                    Continue <ArrowRight className="h-4 w-4" aria-hidden="true" />
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {draft?.i > 0 && scene.kind !== "intro" && scene.kind !== "outro" && (
          <div className="pointer-events-none absolute left-0 right-0 top-2 z-20 px-5 sm:px-10">
            <div className="pointer-events-auto mx-auto flex w-full max-w-xl items-center justify-between rounded-full border border-white/25 bg-brand-950/45 px-4 py-2 text-xs text-white/90 backdrop-blur">
              <span>Resumed from your saved draft.</span>
              <button onClick={startOver} data-testid="onb-start-over" className="font-semibold text-white underline underline-offset-2 hover:text-white/80">
                Start over
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
