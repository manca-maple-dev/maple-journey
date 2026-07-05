import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  Loader2,
  Sparkles,
  ArrowRight,
  Receipt,
  MessageCircle,
  ShieldCheck,
  Rocket,
  CalendarClock,
} from "lucide-react";
import { toast } from "sonner";
import api, { apiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";

const VALUE_STEPS = [
  {
    title: "Maple chat unlocked",
    description: "Use unlimited AI guidance for immigration, jobs, legal navigation, and settlement steps.",
    icon: MessageCircle,
  },
  {
    title: "Billing receipt ready",
    description: "Your payment record is saved in Billing with plan status and history.",
    icon: Receipt,
  },
  {
    title: "Priority support active",
    description: "Your upgraded plan includes faster support and richer, profile-aware recommendations.",
    icon: ShieldCheck,
  },
];

export default function PlanSuccess() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const { refreshUser } = useAuth();

  const [phase, setPhase] = useState("verifying"); // verifying | success | failed
  const [planId, setPlanId] = useState(null);

  const sessionId = params.get("session_id");

  useEffect(() => {
    let cancelled = false;

    const verifyPayment = async () => {
      if (!sessionId) {
        setPhase("failed");
        return;
      }

      for (let attempt = 0; attempt < 8; attempt += 1) {
        try {
          const { data } = await api.get(`/checkout/status/${sessionId}`);

          if (cancelled) return;

          if (data.payment_status === "paid") {
            await refreshUser();
            setPlanId(data.plan_id || null);
            setPhase("success");
            setParams({}, { replace: true });
            toast.success("Payment confirmed. Your upgrade is now active.");
            return;
          }

          if (data.status === "expired") {
            setPhase("failed");
            toast.error("This checkout session expired. Please try again.");
            return;
          }
        } catch (error) {
          if (attempt >= 2) {
            setPhase("failed");
            toast.error(apiError(error));
            return;
          }
        }

        await new Promise((resolve) => setTimeout(resolve, 1800));
      }

      if (!cancelled) {
        setPhase("failed");
        toast.error("We could not confirm your payment yet. Please check Billing.");
      }
    };

    verifyPayment();

    return () => {
      cancelled = true;
    };
  }, [refreshUser, sessionId, setParams]);

  const planLabel = useMemo(() => {
    if (!planId) return "your upgraded";
    if (planId === "plus") return "Maple Plus";
    if (planId === "family") return "Maple Family";
    return planId;
  }, [planId]);

  if (phase === "verifying") {
    return (
      <div className="grid min-h-[70vh] place-items-center text-center" data-testid="plan-success-verifying">
        <div className="max-w-md rounded-3xl border border-border bg-card p-8 shadow-sm">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-brand-500" />
          <h1 className="mt-4 font-display text-2xl font-bold tracking-tight">Confirming your payment</h1>
          <p className="mt-2 text-sm text-muted-foreground">Please wait while we activate your plan and unlock your new features.</p>
        </div>
      </div>
    );
  }

  if (phase === "failed") {
    return (
      <div className="grid min-h-[70vh] place-items-center text-center" data-testid="plan-success-failed">
        <div className="max-w-lg rounded-3xl border border-border bg-card p-8 shadow-sm">
          <h1 className="font-display text-2xl font-bold tracking-tight">We could not confirm this payment yet</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            This can happen if the provider is still processing. You can check your billing page, retry upgrade, or continue using the app.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Button onClick={() => navigate("/app/billing")}>
              Open Billing
            </Button>
            <Button variant="outline" onClick={() => navigate("/app/plans")}>
              Try Again
            </Button>
            <Button variant="ghost" onClick={() => navigate("/app")}>Go to App</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl py-4" data-testid="plan-success-page">
      <motion.section
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="overflow-hidden rounded-3xl border border-green-200 bg-gradient-to-br from-green-50 via-white to-brand-50 p-8 shadow-sm dark:border-green-900 dark:bg-green-950/30"
      >
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-2xl">
            <p className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-green-700 dark:text-green-300">
              <Sparkles className="h-4 w-4" /> Payment complete
            </p>
            <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">
              Welcome to {planLabel}
            </h1>
            <p className="mt-3 text-sm text-green-900/80 dark:text-green-100/85">
              Your subscription is active now. Everything below is ready immediately so the upgrade feels useful from minute one.
            </p>
          </div>
          <div className="flex items-center gap-3 rounded-2xl border border-green-200 bg-white/80 px-4 py-3 text-sm dark:border-green-900 dark:bg-black/15">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            <span className="font-medium">Plan activated successfully</span>
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {VALUE_STEPS.map((step, idx) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.1 + idx * 0.07 }}
              className="rounded-2xl border border-green-200/70 bg-white/85 p-4 dark:border-green-900 dark:bg-black/15"
            >
              <step.icon className="h-4 w-4 text-brand-600" />
              <p className="mt-2 text-sm font-semibold text-foreground">{step.title}</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{step.description}</p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      <section className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-3xl border border-border bg-card p-6">
          <p className="flex items-center gap-2 text-sm font-semibold"><Rocket className="h-4 w-4 text-brand-500" /> Start with high-impact actions</p>
          <div className="mt-4 grid gap-2">
            <Button className="justify-between" onClick={() => navigate("/app/chat")}>Ask Maple your top question <ArrowRight className="h-4 w-4" /></Button>
            <Button variant="outline" className="justify-between" onClick={() => navigate("/app/legal")}>Open Legal Guidance <ArrowRight className="h-4 w-4" /></Button>
            <Button variant="outline" className="justify-between" onClick={() => navigate("/app/jobs")}>See Personalized Jobs <ArrowRight className="h-4 w-4" /></Button>
          </div>
        </div>

        <div className="rounded-3xl border border-border bg-card p-6">
          <p className="flex items-center gap-2 text-sm font-semibold"><CalendarClock className="h-4 w-4 text-brand-500" /> Keep your account organized</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Review your payment record, confirm plan details, and keep profile preferences updated for better recommendations.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => navigate("/app/billing?upgraded=1")}>View Billing</Button>
            <Button variant="ghost" onClick={() => navigate("/app/profile")}>Update Profile</Button>
          </div>
        </div>
      </section>
    </div>
  );
}
