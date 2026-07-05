import { useEffect, useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Check, Loader2, Sparkles, ArrowRight, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import api, { apiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function PlanSelection() {
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const [params, setParams] = useSearchParams();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [verifying, setVerifying] = useState(false);

  const sessionId = params.get("session_id");

  useEffect(() => {
    api.get("/plans").then(({ data }) => setPlans(data)).catch(() => setPlans([])).finally(() => setLoading(false));
  }, []);

  // If we came back from Stripe, poll the payment status before continuing.
  const pollStatus = useCallback(async (sid, attempt = 0) => {
    if (attempt >= 6) { setVerifying(false); toast.error("Still processing — check back in a moment."); return; }
    try {
      const { data } = await api.get(`/checkout/status/${sid}`);
      if (data.payment_status === "paid") {
        await refreshUser();
        setVerifying(false);
        toast.success("You're upgraded — welcome to unlimited Maple! 🍁");
        navigate("/app/billing?upgraded=1", { replace: true });
        return;
      }
      if (data.status === "expired") { setVerifying(false); toast.error("That checkout expired. Please try again."); return; }
      setTimeout(() => pollStatus(sid, attempt + 1), 2000);
    } catch {
      setVerifying(false);
      toast.error("Couldn't verify payment. Please try again.");
    }
  }, [navigate, refreshUser]);

  useEffect(() => {
    if (sessionId) {
      setVerifying(true);
      pollStatus(sessionId);
      setParams({}, { replace: true }); // clean the URL
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const choose = async (plan) => {
    if (plan.id === "free") { navigate("/app"); return; }
    setBusyId(plan.id);
    try {
      const { data } = await api.post("/checkout/session", { plan_id: plan.id, origin_url: window.location.origin });
      if (data.url) window.location.href = data.url;
      else throw new Error("No checkout URL");
    } catch (e) {
      setBusyId(null);
      toast.error(apiError(e));
    }
  };

  if (verifying) {
    return (
      <div className="grid min-h-[60vh] place-items-center text-center" data-testid="plans-verifying">
        <div>
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-brand-500" />
          <p className="mt-4 font-display text-lg font-semibold">Confirming your payment…</p>
          <p className="mt-1 text-sm text-muted-foreground">This only takes a moment.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl" data-testid="plans-page">
      <div className="text-center">
        <p className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">
          <Sparkles className="h-3.5 w-3.5" /> Choose your plan
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight sm:text-4xl">Pick the guidance that fits you</h1>
        <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
          Start free — upgrade any time for unlimited Maple and deeper, profile-aware guidance. Cancel whenever.
        </p>
      </div>

      {loading ? (
        <div className="mt-12 grid gap-5 lg:grid-cols-3">
          {[0, 1, 2].map((i) => <div key={i} className="h-80 rounded-3xl border border-border bg-card mj-shimmer" />)}
        </div>
      ) : (
        <div className="mt-12 grid gap-5 lg:grid-cols-3">
          {plans.map((p, i) => {
            const current = (user?.tier || "free") === p.id;
            return (
              <motion.div key={p.id}
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: i * 0.06 }}
                data-testid={`plan-card-${p.id}`}
                className={cn("relative flex flex-col rounded-3xl border p-7", p.highlight ? "border-brand-500 bg-card shadow-2xl shadow-brand-500/10 lg:-translate-y-2" : "border-border bg-card")}>
                {p.highlight && <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-brand-500 px-3 py-1 text-xs font-semibold text-white">{p.tagline}</span>}
                <p className="text-sm font-semibold text-muted-foreground">{p.name}</p>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="font-display text-4xl font-bold">{p.price === 0 ? "Free" : `$${p.price}`}</span>
                  {p.price !== 0 && <span className="text-muted-foreground">/{p.period === "month" ? "mo" : p.period}</span>}
                </div>
                <ul className="mt-6 flex-1 space-y-3">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm"><Check className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" />{f}</li>
                  ))}
                </ul>
                <Button
                  onClick={() => choose(p)}
                  disabled={busyId === p.id || current}
                  variant={p.highlight ? "default" : "outline"}
                  className="mt-7 h-11 w-full rounded-full"
                  data-testid={`plan-select-${p.id}`}>
                  {busyId === p.id ? <Loader2 className="h-4 w-4 animate-spin" />
                    : current ? "Current plan"
                    : p.id === "free" ? <>Continue free <ArrowRight className="ml-1.5 h-4 w-4" /></>
                    : <>Choose {p.name}</>}
                </Button>
              </motion.div>
            );
          })}
        </div>
      )}

      <div className="mt-8 flex flex-col items-center gap-2 text-center">
        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5" /> Secure checkout by Stripe · cancel anytime
        </p>
        <button onClick={() => navigate("/app")} className="text-sm font-medium text-muted-foreground underline underline-offset-2 hover:text-foreground" data-testid="plans-skip">
          Maybe later — take me to the app
        </button>
      </div>
    </div>
  );
}
