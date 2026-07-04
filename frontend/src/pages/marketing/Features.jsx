import { motion } from "framer-motion";
import {
  CalendarClock, MessageSquareText, TrendingUp, Briefcase, Smartphone,
  Scale, MapPin, UserRound, ShieldCheck, FileCheck2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ASSETS } from "@/lib/assets";
import { useAuth } from "@/context/AuthContext";
import { resolveSmartLink } from "@/lib/smartLinks";

// Accurate to the shipping app + blueprint core sections. No feature listed here
// that the product doesn't actually do.
const GROUPS = [
  { icon: CalendarClock, img: ASSETS.iconAi, title: "Daily Briefing", desc: "Your Today page: local weather, cited IRCC news, government alerts and upcoming holidays — specific to your city and status." },
  { icon: MessageSquareText, title: "Ask Maple", desc: "A grounded companion that answers with cited sources — on the web and on WhatsApp. When it doesn't have a source, it says so." },
  { icon: TrendingUp, title: "PR Readiness", desc: "A live CRS-style readiness score for permanent-residence pathways, with clear tips to close the gaps." },
  { icon: Briefcase, img: ASSETS.iconJobs, title: "Job Matching", desc: "Canadian roles ranked to your profile and flagged LMIA-exempt or PNP-friendly." },
  { icon: Smartphone, title: "Get Connected", desc: "eSIM plans to land online from day one, plus curated links to newcomer banking and transit." },
  { icon: Scale, title: "Legal & Government", desc: "Cited guidance on immigration, tax and health services — with the required IRPA s.91 disclosure." },
  { icon: MapPin, title: "Communities", desc: "Find places of worship, ethnic groceries, food banks and newcomer organizations near you on an open map." },
  { icon: UserRound, img: ASSETS.iconTimeline, title: "Profile & Timeline", desc: "Manage your details, track permit / PR / citizenship countdowns, and control your data — export or delete anytime." },
];

export default function Features() {
  const { user, features } = useAuth();
  const isSignedIn = !!user && user !== false;
  const cta = resolveSmartLink("start-journey", { isSignedIn, features });

  return (
    <div>
      <section className="relative mx-auto max-w-6xl px-4 py-16 text-center">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-64 mj-grid-bg opacity-60" />
        <p className="relative text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Features</p>
        <h1 className="relative mt-3 text-4xl font-bold tracking-tight sm:text-5xl">Everything you need to settle in Canada</h1>
        <p className="relative mx-auto mt-5 max-w-2xl text-muted-foreground">Connected tools built on official sources — from IRCC, the CRA and Service Canada. Every answer is cited, so you always know where it came from.</p>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-8">
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {GROUPS.map((g, i) => (
            <motion.div key={g.title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: (i % 3) * 0.06 }}
              className="group rounded-2xl border border-border bg-card p-6 transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-black/[0.04]">
              {g.img ? (
                <img src={g.img} alt="" className="h-16 w-16 rounded-2xl object-cover shadow-sm transition-transform group-hover:scale-105" />
              ) : (
                <div className="grid h-16 w-16 place-items-center rounded-2xl bg-brand-50 text-brand-600 transition-transform group-hover:scale-105 dark:bg-brand-500/10">
                  <g.icon className="h-7 w-7" />
                </div>
              )}
              <h3 className="mt-5 font-display text-lg font-semibold">{g.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{g.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Signature capability — cited & grounded */}
      <section className="mx-auto max-w-6xl px-4 pb-20">
        <div className="grid gap-5 rounded-3xl border border-border bg-secondary/40 p-8 sm:grid-cols-2">
          <div className="flex items-start gap-4">
            <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-500 text-white"><FileCheck2 className="h-5 w-5" /></span>
            <div>
              <h3 className="font-display text-lg font-semibold">Cited, every time</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">Every piece of information links back to its official source, exposed inline — nothing is surfaced without one.</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-500 text-white"><ShieldCheck className="h-5 w-5" /></span>
            <div>
              <h3 className="font-display text-lg font-semibold">Grounded, not guessed</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">Maple retrieves real documents and cites them. When it doesn't know, it tells you — and points you to a regulated representative.</p>
            </div>
          </div>
        </div>

        <div className="mt-14 text-center">
          <Link to={cta.to}><Button size="lg" className="h-12 rounded-full px-8" data-testid="features-cta">Try it free</Button></Link>
        </div>
      </section>
    </div>
  );
}
