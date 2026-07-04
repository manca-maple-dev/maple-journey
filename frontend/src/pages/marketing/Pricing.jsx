import { useState } from "react";
import { Link } from "react-router-dom";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { resolveSmartLink } from "@/lib/smartLinks";

const PLANS = [
  { name: "Newcomer", monthly: 0, yearly: 0, tag: "Get started", feats: ["Maple companion (8 chats/day)", "Daily briefing — weather & cited IRCC news", "PR readiness assessment", "Jobs, Legal help & Communities"], cta: "Start free", highlight: false },
  { name: "Plus", monthly: 2.99, yearly: 29, tag: "Most popular", feats: ["Everything in Newcomer", "Unlimited Maple chats", "Deeper, profile-aware guidance", "Priority responses"], cta: "Go Plus", highlight: true },
  { name: "Family", monthly: 4.99, yearly: 49, tag: "For households", feats: ["Everything in Plus", "Guidance tuned for your whole household", "Priority responses", "Early access to new features"], cta: "Choose Family", highlight: false },
];

const FAQ = [
  ["Can I cancel anytime?", "Yes — plans are month-to-month and you can cancel or downgrade whenever you like."],
  ["Is MapleJourney affiliated with the government?", "No. We're an independent tool that helps you understand and organize your journey. For legal advice, consult a licensed RCIC."],
  ["Do you offer newcomer discounts?", "The Newcomer plan is free forever, and we offer discounted yearly billing on paid plans."],
];

export default function Pricing() {
  const [yearly, setYearly] = useState(false);
  const { user, features } = useAuth();
  const isSignedIn = !!user && user !== false;

  const startJourney = resolveSmartLink("start-journey", { isSignedIn, features });
  const plusPlan = resolveSmartLink("plan-plus", { isSignedIn, features });
  const familyPlan = resolveSmartLink("plan-family", { isSignedIn, features });

  return (
    <div className="mx-auto max-w-6xl px-4 py-16">
      <div className="text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Pricing</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">Choose your journey plan</h1>
        <p className="mx-auto mt-5 max-w-xl text-muted-foreground">Start free. Upgrade when you're ready for the full experience.</p>
        <div className="mt-7 inline-flex items-center gap-1 rounded-full border border-border bg-card p-1">
          <button onClick={() => setYearly(false)} data-testid="billing-monthly" className={`rounded-full px-4 py-1.5 text-sm font-medium ${!yearly ? "bg-brand-500 text-white" : "text-muted-foreground"}`}>Monthly</button>
          <button onClick={() => setYearly(true)} data-testid="billing-yearly" className={`rounded-full px-4 py-1.5 text-sm font-medium ${yearly ? "bg-brand-500 text-white" : "text-muted-foreground"}`}>Yearly <span className="text-xs opacity-80">-17%</span></button>
        </div>
      </div>

      <div className="mt-12 grid gap-5 lg:grid-cols-3">
        {PLANS.map((p) => {
          const price = yearly ? p.yearly : p.monthly;
          return (
            <div key={p.name} className={`relative flex flex-col rounded-3xl border p-7 ${p.highlight ? "border-brand-500 bg-card shadow-2xl shadow-brand-500/10 lg:-translate-y-3" : "border-border bg-card"}`}>
              {p.highlight && <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-brand-500 px-3 py-1 text-xs font-semibold text-white">{p.tag}</span>}
              <p className="text-sm font-semibold text-muted-foreground">{p.name}</p>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="font-display text-4xl font-bold">{price === 0 ? "Free" : `$${price}`}</span>
                {price !== 0 && <span className="text-muted-foreground">/{yearly ? "yr" : "mo"}</span>}
              </div>
              <ul className="mt-6 flex-1 space-y-3">
                {p.feats.map((f) => <li key={f} className="flex items-start gap-2.5 text-sm"><Check className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" />{f}</li>)}
              </ul>
              <Link
                to={p.name === "Plus" ? plusPlan.to : p.name === "Family" ? familyPlan.to : startJourney.to}
                className="mt-7"
              >
                <Button className="w-full rounded-full" variant={p.highlight ? "default" : "outline"} data-testid={`pricing-${p.name.toLowerCase()}`}>
                  {p.cta}
                </Button>
              </Link>
            </div>
          );
        })}
      </div>

      <div className="mx-auto mt-16 max-w-2xl">
        <h2 className="text-center text-2xl font-bold tracking-tight">Frequently asked questions</h2>
        <div className="mt-6 space-y-3">
          {FAQ.map(([q, a]) => (
            <div key={q} className="rounded-2xl border border-border bg-card p-5">
              <p className="font-display font-semibold">{q}</p>
              <p className="mt-2 text-sm text-muted-foreground">{a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
