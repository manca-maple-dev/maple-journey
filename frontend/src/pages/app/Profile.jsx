import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  User, CalendarClock, Sparkles, CreditCard, ShieldCheck, SlidersHorizontal,
  Check, Download, Trash2, ArrowUpRight, MessageCircle, Loader2, FileText,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import api, { apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import ResumeMaker from "@/components/resume/ResumeMaker";

const TIER_LABEL = { free: "Newcomer (Free)", plus: "Plus", family: "Family" };

const CATEGORY = [
  ["express_entry", "Express Entry"], ["provincial_nominee", "Provincial Nominee"], ["student", "Study permit"],
  ["temp_foreign_worker", "Work permit"], ["spousal_family", "Family / spousal"], ["refugee_claimant", "Refugee claimant"],
  ["protected_person", "Protected person"], ["visitor_work_permit", "Visitor / other"], ["other", "Not sure yet"],
];
const GENDER = [["woman", "Woman"], ["man", "Man"], ["non_binary", "Non-binary"], ["self_describe", "Self-describe"], ["prefer_not", "Prefer not to say"]];
const MARITAL = [["single", "Single"], ["married", "Married"], ["common_law", "Common-law"], ["separated", "Separated"], ["divorced", "Divorced"], ["widowed", "Widowed"]];
const EMPLOYMENT = [["employed", "Employed"], ["seeking", "Looking for work"], ["student", "Studying"], ["not_seeking", "Not working"]];
const PROVINCES = [["ON", "Ontario"], ["BC", "British Columbia"], ["QC", "Quebec"], ["AB", "Alberta"], ["MB", "Manitoba"], ["SK", "Saskatchewan"], ["NS", "Nova Scotia"], ["NB", "New Brunswick"], ["NL", "Newfoundland & Labrador"], ["PE", "Prince Edward Island"], ["NT", "Northwest Territories"], ["YT", "Yukon"], ["NU", "Nunavut"]];
const UPDATE_FREQUENCY = [["daily", "Daily"], ["weekly", "Weekly"], ["biweekly", "Every 2 weeks"], ["monthly", "Monthly"]];
const RESPONSE_LANGUAGE = [["auto", "Auto-detect"], ["english", "English"], ["french", "French"]];
const LEGAL_TOPICS = ["Refugee claim", "Work permit", "Study permit", "PR pathway", "Hearing prep", "Detention and removal", "Family sponsorship", "Citizenship", "Appeals", "Housing rights", "Employment rights", "Benefits access"];

function Section({ title, desc, children, testid }) {
  return (
    <div className="rounded-2xl border border-border bg-card p-6" data-testid={testid}>
      <h2 className="font-display text-lg font-semibold">{title}</h2>
      {desc && <p className="mt-1 text-xs text-muted-foreground">{desc}</p>}
      <div className="mt-4">{children}</div>
    </div>
  );
}

function daysUntil(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return null;
  return Math.round((d - new Date()) / (24 * 3600 * 1000));
}

/* Stable, module-level field components (avoid remount / focus loss on typing). */
function TextField({ label, value, onChange, type = "text", placeholder, testid }) {
  return (
    <div className="space-y-1.5"><Label>{label}</Label>
      <Input type={type} value={value} onChange={onChange} placeholder={placeholder} data-testid={testid} /></div>
  );
}
function PickField({ label, value, onValueChange, opts, testid }) {
  return (
    <div className="space-y-1.5"><Label>{label}</Label>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger data-testid={testid}><SelectValue placeholder="Select" /></SelectTrigger>
        <SelectContent>{opts.map(([v, l]) => <SelectItem key={v} value={v}>{l}</SelectItem>)}</SelectContent>
      </Select></div>
  );
}

/* ---------------- My Details ---------------- */
function MyDetails() {
  const { user, refreshUser } = useAuth();
  const p = user?.profile || {};
  const [f, setF] = useState({
    preferred_name: p.preferred_name || "", date_of_birth: p.date_of_birth || "", gender_identity: p.gender_identity || "",
    pronouns: p.pronouns || "", immigration_category: p.immigration_category || "", visa_subtype: p.visa_subtype || "",
    country_of_birth: p.country_of_birth || "", country_of_citizenship: p.country_of_citizenship || "",
    languages_spoken: Array.isArray(p.languages_spoken) ? p.languages_spoken.join(", ") : (p.languages_spoken || ""),
    current_city: p.current_city || "", province_of_residence: p.province_of_residence || p.intended_province || "",
    marital_status: p.marital_status || "", dependents: p.dependents ?? "", employment_status: p.employment_status || "",
    current_occupation: p.current_occupation || "", years_experience: p.years_experience ?? "",
    work_permit_expiry: p.work_permit_expiry || "", study_permit_expiry: p.study_permit_expiry || "",
    pr_received_date: p.pr_received_date || "", arrival_date_canada: p.arrival_date_canada || "",
    update_frequency: p.update_frequency || "",
    preferred_response_language: p.preferred_response_language || "auto",
    province_focus: p.province_focus || "national",
    legal_topics: Array.isArray(p.legal_topics) ? p.legal_topics.join(", ") : (p.legal_topics || ""),
  });
  const [secure, setSecure] = useState({ ircc_file_number: "", ucis_or_foreign_id: "" });
  const [saving, setSaving] = useState(false);
  const onText = (k) => (e) => setF((s) => ({ ...s, [k]: e.target.value }));
  const onPick = (k) => (v) => setF((s) => ({ ...s, [k]: v }));

  useEffect(() => { api.get("/auth/secure-ids").then(({ data }) => setSecure(data)).catch(() => {}); }, []);

  const save = async () => {
    setSaving(true);
    try {
      const merged = { ...p };
      Object.entries(f).forEach(([k, v]) => {
        if (k === "languages_spoken" || k === "legal_topics") merged[k] = v ? v.split(",").map((x) => x.trim()).filter(Boolean) : [];
        else if (v !== "") merged[k] = v; else delete merged[k];
      });
      await api.put("/profile", merged);
      await api.put("/auth/secure-ids", secure);
      await refreshUser();
      toast.success("Your details were saved");
    } catch (e) { toast.error(apiError(e)); }
    setSaving(false);
  };

  return (
    <div className="space-y-6">
      <Section title="Identity" testid="details-identity">
        <div className="grid gap-4 sm:grid-cols-2">
          <TextField label="Preferred name" value={f.preferred_name} onChange={onText("preferred_name")} testid="det-preferred_name" />
          <TextField label="Date of birth" type="date" value={f.date_of_birth} onChange={onText("date_of_birth")} testid="det-date_of_birth" />
          <PickField label="Gender" value={f.gender_identity} onValueChange={onPick("gender_identity")} opts={GENDER} testid="det-gender_identity" />
          <TextField label="Pronouns" value={f.pronouns} onChange={onText("pronouns")} testid="det-pronouns" />
        </div>
      </Section>

      <Section title="Immigration" desc="Sensitive IDs are encrypted at rest and only ever shown to you." testid="details-immigration">
        <div className="grid gap-4 sm:grid-cols-2">
          <PickField label="Immigration category" value={f.immigration_category} onValueChange={onPick("immigration_category")} opts={CATEGORY} testid="det-immigration_category" />
          <TextField label="Visa subtype" value={f.visa_subtype} onChange={onText("visa_subtype")} testid="det-visa_subtype" />
          <div className="space-y-1.5"><Label>IRCC file number 🔒</Label>
            <Input value={secure.ircc_file_number} onChange={(e) => setSecure((s) => ({ ...s, ircc_file_number: e.target.value }))} placeholder="Optional" data-testid="det-ircc" /></div>
          <div className="space-y-1.5"><Label>UCIS / foreign ID 🔒</Label>
            <Input value={secure.ucis_or_foreign_id} onChange={(e) => setSecure((s) => ({ ...s, ucis_or_foreign_id: e.target.value }))} placeholder="Optional" data-testid="det-foreign-id" /></div>
          <TextField label="Arrival date in Canada" type="date" value={f.arrival_date_canada} onChange={onText("arrival_date_canada")} testid="det-arrival_date_canada" />
          <TextField label="PR received date" type="date" value={f.pr_received_date} onChange={onText("pr_received_date")} testid="det-pr_received_date" />
          <TextField label="Work permit expiry" type="date" value={f.work_permit_expiry} onChange={onText("work_permit_expiry")} testid="det-work_permit_expiry" />
          <TextField label="Study permit expiry" type="date" value={f.study_permit_expiry} onChange={onText("study_permit_expiry")} testid="det-study_permit_expiry" />
        </div>
      </Section>

      <Section title="Origin, location & household" testid="details-origin">
        <div className="grid gap-4 sm:grid-cols-2">
          <TextField label="Country of birth" value={f.country_of_birth} onChange={onText("country_of_birth")} testid="det-country_of_birth" />
          <TextField label="Country of citizenship" value={f.country_of_citizenship} onChange={onText("country_of_citizenship")} testid="det-country_of_citizenship" />
          <TextField label="Languages (comma separated)" value={f.languages_spoken} onChange={onText("languages_spoken")} testid="det-languages_spoken" />
          <TextField label="Current city" value={f.current_city} onChange={onText("current_city")} testid="det-current_city" />
          <PickField label="Province" value={f.province_of_residence} onValueChange={onPick("province_of_residence")} opts={PROVINCES} testid="det-province_of_residence" />
          <PickField label="Marital status" value={f.marital_status} onValueChange={onPick("marital_status")} opts={MARITAL} testid="det-marital_status" />
          <TextField label="Number of dependents" type="number" value={f.dependents} onChange={onText("dependents")} testid="det-dependents" />
        </div>
      </Section>

      <Section title="Work" testid="details-work">
        <div className="grid gap-4 sm:grid-cols-2">
          <PickField label="Employment status" value={f.employment_status} onValueChange={onPick("employment_status")} opts={EMPLOYMENT} testid="det-employment_status" />
          <TextField label="Occupation / field" value={f.current_occupation} onChange={onText("current_occupation")} testid="det-current_occupation" />
          <TextField label="Years of experience" type="number" value={f.years_experience} onChange={onText("years_experience")} testid="det-years_experience" />
        </div>
      </Section>

      <Section title="Legal preferences" desc="Control how often Maple refreshes legal updates and what topics to prioritize." testid="details-legal-preferences">
        <div className="grid gap-4 sm:grid-cols-2">
          <PickField label="Update frequency" value={f.update_frequency} onValueChange={onPick("update_frequency")} opts={UPDATE_FREQUENCY} testid="det-update_frequency" />
          <PickField label="Response language" value={f.preferred_response_language} onValueChange={onPick("preferred_response_language")} opts={RESPONSE_LANGUAGE} testid="det-preferred_response_language" />
          <PickField label="Province focus" value={f.province_focus} onValueChange={onPick("province_focus")} opts={[["national", "National"], ...PROVINCES]} testid="det-province_focus" />
          <div className="space-y-1.5 sm:col-span-2">
            <Label>Legal topics (comma separated)</Label>
            <Input
              value={f.legal_topics}
              onChange={onText("legal_topics")}
              placeholder={LEGAL_TOPICS.join(", ")}
              data-testid="det-legal_topics"
            />
          </div>
        </div>
      </Section>

      <div className="flex justify-end">
        <Button onClick={save} disabled={saving} className="rounded-full" data-testid="details-save">
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save details"}
        </Button>
      </div>
    </div>
  );
}

/* ---------------- Immigration Timeline ---------------- */
function Timeline() {
  const { user } = useAuth();
  const items = useMemo(() => {
    const p = user?.profile || {};
    const rows = [];
    if (p.arrival_date_canada) rows.push({ label: "Arrived in Canada", date: p.arrival_date_canada, kind: "past" });
    const wpe = p.work_permit_expiry || user?.work_permit_expiry;
    if (wpe) rows.push({ label: "Work permit expires", date: wpe, kind: "deadline" });
    if (p.study_permit_expiry) rows.push({ label: "Study permit expires", date: p.study_permit_expiry, kind: "deadline" });
    if (p.pr_received_date) {
      rows.push({ label: "Became a permanent resident", date: p.pr_received_date, kind: "past" });
      const cit = new Date(p.pr_received_date); cit.setDate(cit.getDate() + 1095);
      rows.push({ label: "Citizenship eligibility (≈3 yrs)", date: cit.toISOString().split("T")[0], kind: "goal" });
    }
    return rows.sort((a, b) => new Date(a.date) - new Date(b.date));
  }, [user]);

  return (
    <Section title="Immigration timeline" desc="Key dates and countdowns from your profile. Add dates in My Details to fill this in." testid="timeline-section">
      {items.length === 0 ? (
        <p className="rounded-xl bg-secondary/60 p-4 text-sm text-muted-foreground">No dates are available at the moment. Add your arrival, permit expiry, or PR date in <span className="font-medium text-foreground">My Details</span>.</p>
      ) : (
        <ol className="relative space-y-4 border-l-2 border-border pl-5">
          {items.map((it, i) => {
            const d = daysUntil(it.date);
            const color = it.kind === "deadline" ? "bg-maple" : it.kind === "goal" ? "bg-brand-500" : "bg-green-500";
            return (
              <li key={i} className="relative" data-testid={`timeline-item-${i}`}>
                <span className={`absolute -left-[27px] top-1 h-3 w-3 rounded-full ${color} ring-4 ring-card`} />
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border bg-background px-4 py-3">
                  <div>
                    <p className="text-sm font-semibold">{it.label}</p>
                    <p className="text-xs text-muted-foreground">{new Date(it.date).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}</p>
                  </div>
                  {d != null && (
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${d < 0 ? "bg-secondary text-muted-foreground" : d < 60 ? "bg-maple-50 text-maple dark:bg-maple-500/10" : "bg-brand-50 text-brand-600 dark:bg-brand-500/10"}`}>
                      {d < 0 ? `${Math.abs(d)} days ago` : `in ${d} days`}
                    </span>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </Section>
  );
}

/* ---------------- Maple Companion ---------------- */
function Companion() {
  const { user, refreshUser } = useAuth();
  const [wings, setWings] = useState(user?.wings || { tone: "friendly", autonomy: "ask" });
  const [phone, setPhone] = useState(user?.phone || "");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState(user?.phone_verified ? "verified" : "idle");
  const [busy, setBusy] = useState(false);
  const [messagingConfig, setMessagingConfig] = useState(null);
  const [opsBusy, setOpsBusy] = useState(false);
  const [credits, setCredits] = useState(null);
  const [creditHistory, setCreditHistory] = useState([]);
  const [actions, setActions] = useState([]);
  const [actionType, setActionType] = useState("document_check");
  const [actionTitle, setActionTitle] = useState("");
  const [actionPayload, setActionPayload] = useState("{}");
  const [followupMessage, setFollowupMessage] = useState("");
  const [followupMinutes, setFollowupMinutes] = useState("60");
  const [followupChannel, setFollowupChannel] = useState("whatsapp");
  const [scheduledFollowups, setScheduledFollowups] = useState([]);

  const loadCompanionOps = async () => {
    try {
      const [c, h, a] = await Promise.all([
        api.get("/companion/credits"),
        api.get("/companion/credits/history?limit=8"),
        api.get("/companion/actions?limit=20"),
      ]);
      setCredits(c.data);
      setCreditHistory(Array.isArray(h.data) ? h.data : []);
      setActions(Array.isArray(a.data) ? a.data : []);
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  useEffect(() => { loadCompanionOps(); }, []);
  useEffect(() => {
    api.get("/messaging/config").then(({ data }) => setMessagingConfig(data)).catch(() => setMessagingConfig(null));
  }, []);

  const saveWings = async (patch) => {
    setWings((w) => ({ ...w, ...patch }));
    try { await api.put("/wings/settings", patch); await refreshUser(); toast.success("Maple updated"); }
    catch { toast.error("Could not update Maple"); }
  };
  const sendOtp = async () => {
    setBusy(true);
    try { await api.post("/phone/send-otp", { phone }); setStep("sent"); toast.success("Code sent via SMS"); }
    catch (e) { toast.error(apiError(e)); } setBusy(false);
  };
  const verifyOtp = async () => {
    setBusy(true);
    try { await api.post("/phone/verify-otp", { phone, code: otp }); setStep("verified"); await refreshUser(); toast.success("Phone verified!"); }
    catch (e) { toast.error(apiError(e)); } setBusy(false);
  };

  const submitActionProposal = async () => {
    const title = actionTitle.trim();
    if (!title) {
      toast.error("Action title is required");
      return;
    }

    let parsedPayload = {};
    try {
      parsedPayload = actionPayload.trim() ? JSON.parse(actionPayload) : {};
    } catch {
      toast.error("Payload must be valid JSON");
      return;
    }

    setOpsBusy(true);
    try {
      await api.post("/companion/actions/propose", {
        action_type: actionType,
        title,
        payload: parsedPayload,
        channel: "web",
      });
      setActionTitle("");
      setActionPayload("{}");
      await loadCompanionOps();
      toast.success("Action submitted for approval");
    } catch (e) {
      toast.error(apiError(e));
    }
    setOpsBusy(false);
  };

  const decideAction = async (actionId, decision) => {
    setOpsBusy(true);
    try {
      await api.post(`/companion/actions/${actionId}/decision`, { decision, note: "" });
      await loadCompanionOps();
      toast.success(decision === "approve" ? "Action approved" : "Action rejected");
    } catch (e) {
      toast.error(apiError(e));
    }
    setOpsBusy(false);
  };

  const scheduleFollowup = async () => {
    const message = followupMessage.trim();
    const minutes = Math.max(1, Number(followupMinutes) || 60);
    if (!message) {
      toast.error("Follow-up message is required");
      return;
    }
    setOpsBusy(true);
    try {
      const { data } = await api.post("/companion/followups/schedule", {
        message,
        minutes_from_now: minutes,
        channel: followupChannel,
        metadata: { source: "profile-companion" },
      });
      setScheduledFollowups((s) => [data, ...s].slice(0, 8));
      setFollowupMessage("");
      await loadCompanionOps();
      toast.success("Follow-up scheduled");
    } catch (e) {
      toast.error(apiError(e));
    }
    setOpsBusy(false);
  };

  const badgeClass = (status) => {
    if (status === "pending") return "bg-amber-500/10 text-amber-700";
    if (status === "executed" || status === "approved") return "bg-green-500/10 text-green-700";
    if (status === "rejected" || status === "failed") return "bg-maple/10 text-maple";
    return "bg-secondary text-muted-foreground";
  };

  return (
    <div className="space-y-6">
      <Section title="How Maple talks" desc="Tune your companion's voice and how much it does on its own." testid="companion-settings">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5"><Label>Tone</Label>
            <Select value={wings.tone} onValueChange={(v) => saveWings({ tone: v })}>
              <SelectTrigger data-testid="maple-tone"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="friendly">Friendly & encouraging</SelectItem>
                <SelectItem value="concise">Concise & direct</SelectItem>
                <SelectItem value="professional">Professional</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5"><Label>Autonomy</Label>
            <Select value={wings.autonomy} onValueChange={(v) => saveWings({ autonomy: v })}>
              <SelectTrigger data-testid="maple-autonomy"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ask">Ask before consequential actions</SelectItem>
                <SelectItem value="auto">Handle low-stakes tasks automatically</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </Section>

      <Section title="WhatsApp & alerts" desc="Verify your phone to chat with Maple on WhatsApp and get reminders." testid="whatsapp-settings">
        <div className="mb-2 flex items-center gap-2 text-sm"><MessageCircle className="h-4 w-4 text-green-600" /> Maple on the go</div>
        {messagingConfig && (
          <div className={`mb-3 flex flex-wrap items-center gap-2 rounded-xl border px-3 py-2 text-xs ${messagingConfig.configured ? "border-green-500/30 bg-green-500/5 text-green-700 dark:text-green-300" : "border-amber-500/30 bg-amber-500/5 text-amber-800 dark:text-amber-200"}`}>
            <span className="font-semibold uppercase tracking-wide">Backend wiring</span>
            <span>{messagingConfig.configured ? "Twilio is connected" : "Twilio is not fully configured yet"}</span>
            {Array.isArray(messagingConfig.missing) && messagingConfig.missing.length > 0 && (
              <span className="text-muted-foreground">Missing: {messagingConfig.missing.join(", ")}</span>
            )}
          </div>
        )}
        {step === "verified" ? (
          <div className="flex items-center gap-2 rounded-xl border border-green-500/30 bg-green-500/5 px-3 py-2.5 text-sm">
            <span className="grid h-6 w-6 place-items-center rounded-lg bg-green-500/10 text-green-600"><Check className="h-3.5 w-3.5" /></span>
            <span className="font-medium">{user?.phone || phone}</span>
            <span className="ml-auto text-xs font-semibold text-green-600">Verified</span>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex flex-col gap-2 sm:flex-row">
              <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1 415 555 1234" type="tel" data-testid="phone-input" className="flex-1" />
              <Button onClick={sendOtp} disabled={busy || !phone} className="rounded-full" data-testid="send-otp-btn">{step === "sent" ? "Resend" : "Send code"}</Button>
            </div>
            {step === "sent" && (
              <div className="flex flex-col gap-2 sm:flex-row">
                <Input value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="6-digit code" inputMode="numeric" data-testid="otp-input" className="flex-1" />
                <Button onClick={verifyOtp} disabled={busy || !otp} className="rounded-full" data-testid="verify-otp-btn">Verify</Button>
              </div>
            )}
            <p className="text-xs text-muted-foreground">Requires Twilio to be configured. Include your country code.</p>
          </div>
        )}
      </Section>

      <Section title="Companion credits" desc="Free tier is metered. Paid tiers run companion operations without credit caps." testid="companion-credits">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">Tier: {String(user?.tier || "free").toUpperCase()}</Badge>
            <Badge className={credits?.metering_active ? "bg-amber-500/10 text-amber-700" : "bg-green-500/10 text-green-700"}>
              {credits?.metering_active ? "Metering active" : "Unlimited companion ops"}
            </Badge>
            <Badge variant="outline">Balance: {credits?.balance ?? 0}</Badge>
          </div>
          <p className="text-xs text-muted-foreground">{credits?.policy || "subscription-first policy enabled"}</p>

          {creditHistory.length > 0 ? (
            <div className="divide-y divide-border rounded-xl border border-border">
              {creditHistory.map((row, i) => (
                <div key={`${row.created_at || "now"}-${i}`} className="flex items-center justify-between gap-3 px-3 py-2 text-xs">
                  <span className="font-medium">{row.reason || row.kind || "ledger"}</span>
                  <span className="text-muted-foreground">
                    {typeof row.delta === "number"
                      ? (row.delta > 0 ? `+${row.delta}` : row.delta)
                      : (row.kind === "grant" ? `+${row.amount ?? 0}` : `-${row.amount ?? 0}`)}
                  </span>
                  <span className="text-muted-foreground">{row.balance_after ?? row.balance ?? "-"}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">No recent credit activity at the moment.</p>
          )}
        </div>
      </Section>

      <Section title="Action approvals" desc="Propose an action, then approve or reject it for safe execution." testid="companion-actions">
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Action type</Label>
              <Select value={actionType} onValueChange={setActionType}>
                <SelectTrigger data-testid="companion-action-type"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="document_check">Document check</SelectItem>
                  <SelectItem value="deadline_reminder">Deadline reminder</SelectItem>
                  <SelectItem value="status_followup">Status follow-up</SelectItem>
                  <SelectItem value="resource_shortlist">Resource shortlist</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Title</Label>
              <Input value={actionTitle} onChange={(e) => setActionTitle(e.target.value)} placeholder="Prepare a permit-renewal checklist" data-testid="companion-action-title" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>Payload (JSON)</Label>
            <Textarea value={actionPayload} onChange={(e) => setActionPayload(e.target.value)} className="min-h-[96px]" data-testid="companion-action-payload" />
          </div>
          <div className="flex justify-end">
            <Button onClick={submitActionProposal} disabled={opsBusy} className="rounded-full" data-testid="companion-action-submit">
              {opsBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Propose action"}
            </Button>
          </div>

          {actions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No actions have been submitted yet.</p>
          ) : (
            <div className="space-y-2">
              {actions.map((a) => (
                <div key={a.id} className="rounded-xl border border-border p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold">{a.title}</p>
                    <Badge className={badgeClass(a.status)}>{a.status}</Badge>
                    <span className="text-xs text-muted-foreground">{a.action_type}</span>
                  </div>
                  {a.payload && Object.keys(a.payload).length > 0 && (
                    <pre className="mt-2 overflow-auto rounded-lg bg-secondary/70 p-2 text-[11px]">{JSON.stringify(a.payload, null, 2)}</pre>
                  )}
                  {a.status === "pending" && (
                    <div className="mt-2 flex gap-2">
                      <Button size="sm" className="rounded-full" disabled={opsBusy} onClick={() => decideAction(a.id, "approve")}>Approve</Button>
                      <Button size="sm" variant="outline" className="rounded-full" disabled={opsBusy} onClick={() => decideAction(a.id, "reject")}>Reject</Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </Section>

      <Section title="Proactive follow-ups" desc="Schedule future reminders Maple should send on your chosen channel." testid="companion-followups">
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>Follow-up message</Label>
            <Textarea value={followupMessage} onChange={(e) => setFollowupMessage(e.target.value)} placeholder="Remind me to upload my updated enrollment letter." data-testid="companion-followup-message" />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Minutes from now</Label>
              <Input type="number" min="1" value={followupMinutes} onChange={(e) => setFollowupMinutes(e.target.value)} data-testid="companion-followup-minutes" />
            </div>
            <div className="space-y-1.5">
              <Label>Channel</Label>
              <Select value={followupChannel} onValueChange={setFollowupChannel}>
                <SelectTrigger data-testid="companion-followup-channel"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="whatsapp">WhatsApp</SelectItem>
                  <SelectItem value="web">Web</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex justify-end">
            <Button onClick={scheduleFollowup} disabled={opsBusy} className="rounded-full" data-testid="companion-followup-submit">
              {opsBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Schedule follow-up"}
            </Button>
          </div>

          {scheduledFollowups.length > 0 && (
            <div className="space-y-2 rounded-xl border border-border p-3">
              <p className="text-xs font-semibold text-muted-foreground">Recently scheduled in this session</p>
              {scheduledFollowups.map((f) => (
                <div key={f.id} className="rounded-lg bg-secondary/60 px-3 py-2 text-xs">
                  <p className="font-medium">{f.message}</p>
                  <p className="text-muted-foreground">Channel: {f.channel} · Due: {f.due_at ? new Date(f.due_at).toLocaleString() : "-"}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </Section>
    </div>
  );
}

/* ---------------- Subscription ---------------- */
function Subscription() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const isPaid = user?.tier === "plus" || user?.tier === "family";
  useEffect(() => { api.get("/billing/history").then(({ data }) => setHistory(data)).catch(() => {}); }, []);

  return (
    <div className="space-y-6">
      <Section title="Your plan" testid="subscription-plan">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-sm font-semibold text-brand-600 dark:bg-brand-500/10" data-testid="current-tier">
              <Sparkles className="h-3.5 w-3.5" /> {TIER_LABEL[user?.tier || "free"]}
            </span>
            {user?.tier_expires_at && isPaid && <p className="mt-2 text-xs text-muted-foreground">Renews/expires {new Date(user.tier_expires_at).toLocaleDateString()}</p>}
          </div>
          <Button onClick={() => navigate("/app/plans")} className="rounded-full" data-testid="manage-plan">
            {isPaid ? "Change plan" : "Upgrade"} <ArrowUpRight className="ml-1.5 h-4 w-4" />
          </Button>
        </div>
      </Section>
      <Section title="Billing history" testid="billing-history">
        {history.length === 0 ? (
          <p className="text-sm text-muted-foreground">No payment history is available at the moment.</p>
        ) : (
          <div className="divide-y divide-border">
            {history.map((h, i) => (
              <div key={i} className="flex items-center justify-between py-2.5 text-sm">
                <span className="font-medium capitalize">{h.plan_id}</span>
                <span className="text-muted-foreground">${h.amount} {h.currency?.toUpperCase()}</span>
                <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${h.status === "paid" ? "bg-green-500/10 text-green-600" : "bg-secondary text-muted-foreground"}`}>{h.status}</span>
                <span className="text-xs text-muted-foreground">{h.created_at ? new Date(h.created_at).toLocaleDateString() : ""}</span>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}

/* ---------------- Data & Privacy ---------------- */
function DataPrivacy() {
  const { user, refreshUser, logout } = useAuth();
  const p = user?.profile || {};
  const [consents, setConsents] = useState({
    consent_data_personalization: p.consent_data_personalization !== false,
    consent_maple_companion: !!p.consent_maple_companion,
    consent_marketing_emails: !!p.consent_marketing_emails,
    consent_aggregated_analytics: p.consent_aggregated_analytics !== false,
  });
  const [confirmDelete, setConfirmDelete] = useState(false);

  const toggle = async (k) => {
    const next = { ...consents, [k]: !consents[k] };
    setConsents(next);
    try { await api.put("/profile", { ...p, ...next }); await refreshUser(); toast.success("Preferences saved"); }
    catch { toast.error("Could not save"); }
  };
  const exportData = async () => {
    try {
      const { data } = await api.get("/auth/export");
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = "maplejourney-data.json"; a.click();
      URL.revokeObjectURL(url);
    } catch { toast.error("Could not export"); }
  };
  const deleteAccount = async () => {
    try { await api.delete("/auth/account"); toast.success("Account deleted"); logout(); }
    catch (e) { toast.error(apiError(e)); }
  };

  const rows = [
    ["consent_data_personalization", "Personalize my guidance using my answers"],
    ["consent_maple_companion", "Let Maple proactively check in & remind me"],
    ["consent_marketing_emails", "Occasional product update emails"],
    ["consent_aggregated_analytics", "Anonymized analytics to improve Maple"],
  ];

  return (
    <div className="space-y-6">
      <Section title="Consent & communication" testid="privacy-consents">
        <div className="space-y-3">
          {rows.map(([k, label]) => (
            <div key={k} className="flex items-center justify-between gap-3">
              <span className="text-sm">{label}</span>
              <Switch checked={consents[k]} onCheckedChange={() => toggle(k)} data-testid={`consent-${k}`} />
            </div>
          ))}
        </div>
      </Section>
      <Section title="Your data" desc="Download everything we hold about you, or delete your account." testid="privacy-data">
        <div className="flex flex-wrap gap-3">
          <Button variant="outline" className="rounded-full" onClick={exportData} data-testid="export-data">
            <Download className="mr-1.5 h-4 w-4" /> Export my data
          </Button>
          {!confirmDelete ? (
            <Button variant="outline" className="rounded-full border-maple/40 text-maple hover:bg-maple-50" onClick={() => setConfirmDelete(true)} data-testid="delete-account">
              <Trash2 className="mr-1.5 h-4 w-4" /> Delete account
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-maple">Sure? This can't be undone.</span>
              <Button className="rounded-full bg-maple text-white hover:bg-maple-600" onClick={deleteAccount} data-testid="confirm-delete">Yes, delete</Button>
              <Button variant="ghost" className="rounded-full" onClick={() => setConfirmDelete(false)}>Cancel</Button>
            </div>
          )}
        </div>
      </Section>
    </div>
  );
}

/* ---------------- App Settings ---------------- */
function AppSettings() {
  const { theme, toggle } = useTheme();
  return (
    <Section title="Appearance" testid="app-settings">
      <div className="flex items-center justify-between">
        <div><p className="text-sm font-medium">Dark mode</p><p className="text-xs text-muted-foreground">Switch between light and dark themes.</p></div>
        <Switch checked={theme === "dark"} onCheckedChange={toggle} data-testid="settings-dark-toggle" />
      </div>
    </Section>
  );
}

/* ---------------- Hub ---------------- */
const TABS = [
  { v: "details", label: "My Details", icon: User, el: <MyDetails /> },
  { v: "timeline", label: "Timeline", icon: CalendarClock, el: <Timeline /> },
  { v: "resume", label: "Resume Maker", icon: FileText, el: <ResumeMaker /> },
  { v: "companion", label: "Companion", icon: Sparkles, el: <Companion /> },
  { v: "subscription", label: "Subscription", icon: CreditCard, el: <Subscription /> },
  { v: "privacy", label: "Data & Privacy", icon: ShieldCheck, el: <DataPrivacy /> },
  { v: "app", label: "App Settings", icon: SlidersHorizontal, el: <AppSettings /> },
];

export default function Profile() {
  const { user } = useAuth();
  const profile = user?.profile || {};
  const completionKeys = [
    "preferred_name",
    "immigration_category",
    "current_city",
    "province_of_residence",
    "employment_status",
    "arrival_date_canada",
  ];
  const filled = completionKeys.filter((k) => {
    const v = profile[k];
    return Array.isArray(v) ? v.length > 0 : !!v;
  }).length;
  const completionPct = Math.round((filled / completionKeys.length) * 100);

  return (
    <div className="mx-auto max-w-4xl space-y-6" data-testid="profile-page">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">Profile</h1>
        <p className="mt-1 text-sm text-muted-foreground">{user?.name} · {user?.email}</p>
      </div>

      <div className="rounded-2xl border border-border bg-card p-5" data-testid="profile-completion-card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">Profile completeness</p>
            <p className="text-xs text-muted-foreground">
              {user?.profile_completed ? "Onboarding completed" : "Complete key fields to unlock better recommendations"}
            </p>
          </div>
          <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-600 dark:bg-brand-500/10">
            {completionPct}%
          </span>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-secondary">
          <div className="h-full rounded-full bg-brand-500" style={{ width: `${completionPct}%` }} />
        </div>
      </div>

      <Tabs defaultValue="details" className="w-full">
        <TabsList className="flex h-auto w-full flex-wrap justify-start gap-1 rounded-2xl bg-secondary/60 p-1.5">
          {TABS.map((t) => (
            <TabsTrigger key={t.v} value={t.v} data-testid={`profile-tab-${t.v}`} className="gap-1.5 rounded-xl px-3 py-2 text-sm data-[state=active]:bg-card data-[state=active]:shadow-sm">
              <t.icon className="h-4 w-4" /> {t.label}
            </TabsTrigger>
          ))}
        </TabsList>
        {TABS.map((t) => (
          <TabsContent key={t.v} value={t.v} className="mt-5">{t.el}</TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
