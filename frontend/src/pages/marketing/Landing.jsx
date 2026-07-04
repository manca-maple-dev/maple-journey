import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight, Sparkles, ShieldCheck, Route, Briefcase, CalendarClock,
  Bot, Smartphone, Star, Check, TrendingUp, Clock, MapPin, Newspaper,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProgressRing } from "@/components/dashboard/ProgressRing";
import { ASSETS } from "@/lib/assets";
import { useAuth } from "@/context/AuthContext";
import { resolveSmartLink } from "@/lib/smartLinks";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.5, delay: i * 0.08 } }),
};

const FEATURES = [
  { icon: Bot, img: ASSETS.iconAi, title: "Ask Maple", desc: "Ask anything about visas, PR, work permits, taxes or healthcare — every answer cites an official source.", color: "#E31837" },
  { icon: CalendarClock, title: "Daily Briefing", desc: "Local weather, cited IRCC news, alerts and holidays for your city — the moment you open the app.", color: "#0066FF" },
  { icon: Briefcase, img: ASSETS.iconJobs, title: "Job Matching", desc: "Canadian roles ranked to your profile and flagged LMIA-exempt or PNP-friendly.", color: "#0066FF" },
  { icon: Route, img: ASSETS.iconTimeline, title: "Immigration Timeline", desc: "Permit, PR and citizenship dates tracked with clear countdowns in your profile.", color: "#16A34A" },
  { icon: Smartphone, title: "Get Connected", desc: "eSIM plans to land online from day one, plus curated newcomer banking and transit links.", color: "#0066FF" },
  { icon: MapPin, title: "Communities", desc: "Find places of worship, ethnic groceries, food banks and newcomer organizations near you.", color: "#E31837" },
];

const TESTIMONIALS = [
  { name: "Aisha K.", from: "🇳🇬 Nigeria → Toronto", quote: "MapleJourney turned an overwhelming process into simple weekly steps. I got my PR faster than I imagined.", role: "PR Approved" },
  { name: "Diego M.", from: "🇧🇷 Brazil → Vancouver", quote: "The AI assistant answered every 2am question I had about my work permit. Genuinely felt like a friend who knew the system.", role: "Work Permit Holder" },
  { name: "Priya S.", from: "🇮🇳 India → Calgary", quote: "Every answer came with a source I could check myself. I finally understood what my family qualified for.", role: "New Resident" },
];

const PLANS = [
  { name: "Newcomer", price: "Free", tag: "Get started", feats: ["Maple companion (8 chats/day)", "PR readiness assessment", "Jobs, Legal & Communities", "Benefits explorer"], cta: "Start free", highlight: false },
  { name: "Plus", price: "$2.99", period: "/mo", tag: "Most popular", feats: ["Everything in Newcomer", "Unlimited Maple chats", "Deeper, profile-aware guidance", "Priority responses"], cta: "Go Plus", highlight: true },
  { name: "Family", price: "$4.99", period: "/mo", tag: "For households", feats: ["Everything in Plus", "Tuned for the whole household", "Family benefits planner", "Shared timeline"], cta: "Choose Family", highlight: false },
];

export default function Landing() {
  const { user, features } = useAuth();
  const isSignedIn = !!user && user !== false;
  const startJourney = resolveSmartLink("start-journey", { isSignedIn, features });
  const exploreFeatures = resolveSmartLink("ask-maple", { isSignedIn, features });
  const plusPlan = resolveSmartLink("plan-plus", { isSignedIn, features });
  const familyPlan = resolveSmartLink("plan-family", { isSignedIn, features });

  return (
    <div className="overflow-hidden">
      {/* HERO */}
      <section className="relative">
        <div className="pointer-events-none absolute inset-0 mj-grid-bg opacity-70" />
        <div className="pointer-events-none absolute -left-40 top-0 h-96 w-96 mj-glow-blue" />
        <div className="pointer-events-none absolute -right-32 top-40 h-96 w-96 mj-glow-red" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-4 pb-8 pt-10 md:pt-16 lg:grid-cols-[1.05fr_0.95fr]">
          {/* Left: copy */}
          <motion.div initial="hidden" animate="show" className="text-center lg:text-left">
            <motion.div variants={fadeUp} className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3.5 py-1.5 text-xs font-medium text-muted-foreground shadow-sm">
              <Sparkles className="h-3.5 w-3.5 text-brand-500" /> Cited guidance from IRCC, CRA & Service Canada
            </motion.div>
            <motion.h1 variants={fadeUp} custom={1} className="mt-6 text-4xl font-bold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
              Your journey to Canada,
              <br className="hidden sm:block" />{" "}
              <span className="mj-gradient-text">guided every step</span>
            </motion.h1>
            <motion.p variants={fadeUp} custom={2} className="mx-auto mt-6 max-w-xl text-base text-muted-foreground sm:text-lg lg:mx-0">
              MapleJourney turns the maze of visas, PR, jobs and benefits into one clear, personalized path — so you can focus on building your new life.
            </motion.p>
            <motion.div variants={fadeUp} custom={3} className="mt-8 flex flex-col items-center gap-3 sm:flex-row lg:justify-start sm:justify-center">
              <Link to={startJourney.to} className="w-full sm:w-auto">
                <Button size="lg" className="group h-12 w-full rounded-full px-7 text-base sm:w-auto" data-testid="hero-get-started">
                  Start your journey <ArrowRight className="ml-1.5 h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Button>
              </Link>
              <Link to={exploreFeatures.to} className="w-full sm:w-auto">
                <Button size="lg" variant="outline" className="h-12 w-full rounded-full px-7 text-base sm:w-auto" data-testid="hero-explore">
                  Ask Maple now
                </Button>
              </Link>
            </motion.div>
            <motion.div variants={fadeUp} custom={4} className="mt-8 flex items-center justify-center gap-6 text-sm text-muted-foreground lg:justify-start">
              <span className="flex items-center gap-1.5"><ShieldCheck className="h-4 w-4 text-brand-500" /> Free to start</span>
              <span className="flex items-center gap-1.5"><Star className="h-4 w-4 fill-amber-400 text-amber-400" /> 4.9/5 rating</span>
            </motion.div>
          </motion.div>

          {/* Right: 3D visual + floating card */}
          <motion.div initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.7, delay: 0.2 }} className="relative mx-auto w-full max-w-md">
            <div className="pointer-events-none absolute -inset-6 rounded-full bg-brand-500/10 blur-3xl" />
            <div className="relative overflow-hidden rounded-3xl border border-border shadow-2xl shadow-brand-500/20">
              <img src={ASSETS.hero} alt="MapleJourney AI immigration assistant" className="w-full" />
            </div>
            <div className="mj-float absolute -bottom-4 -left-4 flex items-center gap-2 rounded-2xl border border-border bg-card px-3.5 py-2.5 shadow-xl">
              <div className="grid h-9 w-9 place-items-center rounded-lg bg-maple text-white"><Bot className="h-4 w-4" /></div>
              <div><p className="text-xs font-semibold">Maple</p><p className="text-[11px] text-muted-foreground">You qualify for CCB 🎉</p></div>
            </div>
            <div className="absolute -right-4 top-6 flex items-center gap-2 rounded-2xl border border-border bg-card px-3.5 py-2.5 shadow-xl">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <div><p className="text-xs font-semibold">On track</p><p className="text-[11px] text-muted-foreground">3 steps done today</p></div>
            </div>
          </motion.div>
        </div>

        {/* Dashboard preview showcase */}
        <div className="relative mx-auto max-w-4xl px-4 pb-4">
          <motion.div initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.7 }} className="relative">
            <div className="mj-glass rounded-3xl p-3 shadow-2xl shadow-brand-500/10">
              <div className="rounded-2xl border border-border bg-background p-5">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Your daily briefing</p>
                    <h3 className="mt-0.5 truncate font-display text-lg font-semibold">Welcome back, Alex</h3>
                  </div>
                  <span className="inline-flex shrink-0 items-center gap-1 whitespace-nowrap rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-600 dark:bg-brand-500/10">
                    <MapPin className="h-3.5 w-3.5" /> Toronto
                  </span>
                </div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="flex flex-col items-center justify-center rounded-2xl border border-border bg-card p-4">
                    <ProgressRing value={78} size={92} label="Profile" sub="78% ready" />
                  </div>
                  <div className="rounded-2xl border border-border bg-card p-4">
                    <div className="flex items-center gap-2 text-muted-foreground"><Clock className="h-4 w-4 shrink-0" /><span className="text-xs font-semibold uppercase tracking-wider">Work permit</span></div>
                    <p className="mt-3 font-display text-3xl font-bold leading-none">312</p>
                    <p className="mt-1.5 text-xs text-muted-foreground">days remaining</p>
                    <div className="mt-3 h-1.5 rounded-full bg-secondary"><div className="h-full w-3/4 rounded-full bg-brand-500" /></div>
                  </div>
                  <div className="rounded-2xl border border-border bg-card p-4">
                    <div className="flex items-center gap-2 text-muted-foreground"><Newspaper className="h-4 w-4 shrink-0" /><span className="text-xs font-semibold uppercase tracking-wider">Today</span></div>
                    <p className="mt-3 font-display text-3xl font-bold leading-none">3</p>
                    <p className="mt-1.5 text-xs text-muted-foreground">cited updates</p>
                    <div className="mt-3 flex flex-wrap gap-1">
                      {["IRCC", "Weather", "Holiday"].map((t) => (<span key={t} className="rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium text-muted-foreground">{t}</span>))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* TRUST BAR */}
      <section className="border-y border-border bg-card/50">
        <div className="mx-auto max-w-6xl px-4 py-8">
          <p className="text-center text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">Trusted by newcomers from 60+ countries</p>
          <div className="mt-6 grid grid-cols-2 gap-6 text-center sm:grid-cols-4">
            {[["12k+","Journeys started"],["94%","Feel more confident"],["$4.2M","Benefits unlocked"],["60+","Countries"]].map(([n,l])=>(
              <div key={l}><p className="font-display text-2xl font-bold sm:text-3xl">{n}</p><p className="mt-1 text-xs text-muted-foreground">{l}</p></div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Everything you need</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">One platform for your whole journey</h2>
          <p className="mt-4 text-muted-foreground">From your first visa question to your citizenship ceremony — MapleJourney is with you at every step.</p>
        </div>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial="hidden" whileInView="show" viewport={{ once: true }} variants={fadeUp} custom={i}
              className="group rounded-2xl border border-border bg-card p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-black/[0.04]"
            >
              {f.img ? (
                <img src={f.img} alt="" className="h-16 w-16 rounded-2xl object-cover shadow-sm transition-transform group-hover:scale-105" />
              ) : (
                <div className="grid h-16 w-16 place-items-center rounded-2xl transition-transform group-hover:scale-105" style={{ background: `${f.color}14`, color: f.color }}>
                  <f.icon className="h-7 w-7" />
                </div>
              )}
              <div className="mt-5 flex items-center gap-2">
                <h3 className="font-display text-lg font-semibold">{f.title}</h3>
                {f.soon && <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Coming soon</span>}
              </div>
              <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="border-y border-border bg-card/50">
        <div className="mx-auto max-w-6xl px-4 py-20">
          <div className="text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-maple">Real stories</p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Newcomers who found their footing</h2>
          </div>
          <div className="mt-12 grid gap-5 md:grid-cols-3">
            {TESTIMONIALS.map((t, i) => (
              <motion.div key={t.name} initial="hidden" whileInView="show" viewport={{ once: true }} variants={fadeUp} custom={i}
                className="flex flex-col rounded-2xl border border-border bg-card p-6">
                <div className="flex gap-0.5 text-amber-400">{[...Array(5)].map((_, k) => <Star key={k} className="h-4 w-4 fill-current" />)}</div>
                <p className="mt-4 flex-1 text-sm leading-relaxed">“{t.quote}”</p>
                <div className="mt-5 flex items-center gap-3 border-t border-border pt-4">
                  <div className="grid h-10 w-10 place-items-center rounded-full bg-brand-500 font-display font-bold text-white">{t.name[0]}</div>
                  <div><p className="text-sm font-semibold">{t.name}</p><p className="text-xs text-muted-foreground">{t.from}</p></div>
                  <span className="ml-auto rounded-full bg-green-500/10 px-2.5 py-1 text-[11px] font-semibold text-green-600">{t.role}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING TEASER */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <div className="text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Simple pricing</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Plans that grow with your journey</h2>
        </div>
        <div className="mt-12 grid gap-5 lg:grid-cols-3">
          {PLANS.map((p) => (
            <div key={p.name} className={`relative flex flex-col rounded-3xl border p-7 ${p.highlight ? "border-brand-500 bg-card shadow-2xl shadow-brand-500/10 lg:-translate-y-3" : "border-border bg-card"}`}>
              {p.highlight && <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-brand-500 px-3 py-1 text-xs font-semibold text-white">{p.tag}</span>}
              <p className="text-sm font-semibold text-muted-foreground">{p.name}</p>
              <div className="mt-2 flex items-baseline gap-1"><span className="font-display text-4xl font-bold">{p.price}</span>{p.period && <span className="text-muted-foreground">{p.period}</span>}</div>
              <ul className="mt-6 flex-1 space-y-3">
                {p.feats.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm"><Check className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" />{f}</li>
                ))}
              </ul>
              <Link
                to={p.name === "Plus" ? plusPlan.to : p.name === "Family" ? familyPlan.to : startJourney.to}
                className="mt-7"
              >
                <Button className="w-full rounded-full" variant={p.highlight ? "default" : "outline"} data-testid={`plan-${p.name.toLowerCase()}`}>
                  {p.cta}
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-4 pb-24">
        <div className="relative overflow-hidden rounded-3xl border border-border bg-brand-600 p-10 text-center text-white sm:p-16">
          <div className="pointer-events-none absolute inset-0 mj-dot-bg opacity-20" />
          <div className="relative">
            <ShieldCheck className="mx-auto h-10 w-10" />
            <h2 className="mt-5 text-3xl font-bold tracking-tight sm:text-4xl">Ready to start your MapleJourney?</h2>
            <p className="mx-auto mt-3 max-w-xl text-white/80">Join thousands of newcomers building their future in Canada — with cited guidance every step of the way.</p>
            <Link to={startJourney.to}><Button size="lg" className="mt-7 h-12 rounded-full bg-white px-8 text-base text-brand-600 hover:bg-white/90" data-testid="cta-signup">Create your free account</Button></Link>
          </div>
        </div>
      </section>
    </div>
  );
}
