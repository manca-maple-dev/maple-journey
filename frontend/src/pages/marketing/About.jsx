import { Link } from "react-router-dom";
import { Heart, Globe, ShieldCheck, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { resolveSmartLink } from "@/lib/smartLinks";

const VALUES = [
  { icon: Heart, title: "Human first", desc: "Immigration is deeply personal. We pair fast, clear answers with genuine empathy." },
  { icon: Globe, title: "For everyone", desc: "Built for newcomers from every country, background and pathway." },
  { icon: ShieldCheck, title: "Trustworthy", desc: "Clear, accurate guidance grounded in official sources like IRCC and CRA." },
  { icon: Sparkles, title: "Always improving", desc: "Maple keeps pace as immigration rules evolve." },
];

export default function About() {
  const { user, features } = useAuth();
  const isSignedIn = !!user && user !== false;
  const communities = resolveSmartLink("communities", { isSignedIn, features });

  return (
    <div>
      <section className="relative mx-auto max-w-4xl px-4 py-16 text-center">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-64 mj-grid-bg opacity-60" />
        <p className="relative text-xs font-semibold uppercase tracking-[0.2em] text-maple">About & Community</p>
        <h1 className="relative mt-3 text-4xl font-bold tracking-tight sm:text-5xl">We're building the friend every newcomer deserves</h1>
        <p className="relative mx-auto mt-5 max-w-2xl text-muted-foreground">
          MapleJourney started because settling in a new country shouldn't feel like decoding a legal maze alone.
          We combine trustworthy, cited information with a companion that meets you where you are.
        </p>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-8">
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {VALUES.map((v) => (
            <div key={v.title} className="rounded-2xl border border-border bg-card p-6">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10"><v.icon className="h-5 w-5" /></div>
              <h3 className="mt-4 font-display text-lg font-semibold">{v.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{v.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="grid items-center gap-8 rounded-3xl border border-border bg-card p-8 sm:p-12 lg:grid-cols-2">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Find your community in Canada</h2>
            <p className="mt-4 text-muted-foreground">Our Communities map helps you find places of worship, ethnic groceries, food banks and newcomer organizations near you — drawn from open, public data. Real places, close to home.</p>
            <Link to={communities.to}><Button size="lg" className="mt-6 rounded-full px-7" data-testid="about-join">Explore communities</Button></Link>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {["🇳🇬","🇮🇳","🇧🇷","🇵🇭","🇨🇳","🇺🇦","🇰🇪","🇲🇽","🇵🇰"].map((f, i) => (
              <div key={i} className="grid aspect-square place-items-center rounded-2xl border border-border bg-background text-3xl">{f}</div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
