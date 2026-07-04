import { motion } from "framer-motion";
import { Smartphone, Globe, Wallet, Bus, ArrowUpRight, Check, CreditCard, ShieldCheck, GraduationCap, FileText, HeartPulse, Baby, CarFront, Globe2 } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";

// Curated launch data (blueprint E.3): eSIM marketplace as a comparison +
// affiliate layer first; live partner APIs (Airalo/Gigs) are a fast-follow.
const ESIMS = [
  { name: "Airalo", type: "International", data: "1–20 GB", validity: "7–30 days", price: "from $4.50 CAD", note: "Best for staying connected the moment you land, before a local number.", tag: "Roaming", url: "https://www.airalo.com" },
  { name: "Gigs", type: "Canadian number", data: "Unlimited plans", validity: "Monthly", price: "from $15 CAD/mo", note: "A real Canadian mobile number on an eSIM — ideal once you've arrived.", tag: "Local", url: "https://gigs.com" },
  { name: "Public Mobile", type: "Canadian number", data: "Various", validity: "Monthly", price: "from $19 CAD/mo", note: "Budget Canadian carrier with newcomer-friendly prepaid plans.", tag: "Budget", url: "https://www.publicmobile.ca" },
];

const SERVICES = [
  { icon: Wallet, title: "Newcomer banking", desc: "No-fee newcomer accounts from TD, RBC, Scotiabank, BMO and CIBC — compare and open before you arrive.", cta: "Compare banks", url: "https://www.canada.ca/en/financial-consumer-agency/services/banking/opening-bank-account.html" },
  { icon: Bus, title: "Transit passes", desc: "Register for Presto (ON), Compass (BC) or OPUS (QC) and check newcomer & low-income discounts.", cta: "Find your transit", url: "https://www.canada.ca/en/immigration-refugees-citizenship/services/new-immigrants/new-life-canada/public-transportation.html" },
];

const MORE_STARTERS = [
  { icon: ShieldCheck, title: "Health coverage", desc: "Find how to apply for provincial health insurance and what to bring.", url: "https://www.canada.ca/en/health-canada/services/health-care-system.html" },
  { icon: CreditCard, title: "Taxes & benefits", desc: "Learn how filing unlocks GST/HST, CCB and other benefits.", url: "https://www.canada.ca/en/services/taxes/income-tax/personal-income-tax.html" },
  { icon: GraduationCap, title: "School & childcare", desc: "Explore school registration, daycare help and newcomer family services.", url: "https://www.canada.ca/en/immigration-refugees-citizenship/services/new-immigrants/new-life-canada/schooling.html" },
  { icon: FileText, title: "Documents & IDs", desc: "Keep your permit, SIN, health card and local IDs organized.", url: "https://www.canada.ca/en/employment-social-development/services/sin/apply.html" },
  { icon: Baby, title: "Family supports", desc: "Benefits, parenting help, and settlement services for households.", url: "https://www.canada.ca/en/services/benefits/family.html" },
  { icon: CarFront, title: "Driver’s licence", desc: "Understand how to exchange or apply for a Canadian licence.", url: "https://www.canada.ca/en/immigration-refugees-citizenship/services/new-immigrants/new-life-canada/driving.html" },
  { icon: HeartPulse, title: "Walk-in clinics", desc: "Find low-barrier care and community health centres near you.", url: "https://www.canada.ca/en/health-canada/services/health-care-system.html" },
  { icon: Globe2, title: "Language support", desc: "ESL, French classes, translation help and settlement language programs.", url: "https://www.canada.ca/en/immigration-refugees-citizenship/services/new-immigrants/new-life-canada/language-training.html" },
];

export default function Accessibilities() {
  return (
    <div data-testid="accessibilities-page">
      <PageHeader
        icon={Smartphone}
        title="Get connected"
        subtitle="Essential services for your first weeks in Canada — mobile data, a phone number, banking and transit."
      />

      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
        <Globe className="h-4 w-4" /> eSIM plans
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {ESIMS.map((e, i) => (
          <motion.a
            key={e.name}
            href={e.url}
            target="_blank"
            rel="noreferrer"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            data-testid={`esim-${e.name.toLowerCase().replace(/\s/g, "-")}`}
            className="group flex flex-col rounded-2xl border border-border bg-card p-5 transition-colors hover:border-brand-500"
          >
            <div className="flex items-center justify-between">
              <span className="rounded-full bg-brand-500/10 px-2.5 py-1 text-[11px] font-semibold text-brand-600 dark:text-brand-400">{e.tag}</span>
              <ArrowUpRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
            </div>
            <h3 className="mt-3 font-display text-lg font-semibold">{e.name}</h3>
            <p className="text-xs text-muted-foreground">{e.type}</p>
            <p className="mt-3 font-display text-xl font-bold">{e.price}</p>
            <ul className="mt-3 space-y-1.5 text-sm text-muted-foreground">
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-brand-500" /> {e.data} data</li>
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-brand-500" /> {e.validity}</li>
            </ul>
            <p className="mt-3 flex-1 text-sm text-muted-foreground">{e.note}</p>
          </motion.a>
        ))}
      </div>

      <div className="mb-3 mt-8 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
        <Wallet className="h-4 w-4" /> Banking & transit
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {SERVICES.map((s) => (
          <a
            key={s.title}
            href={s.url}
            target="_blank"
            rel="noreferrer"
            data-testid={`service-${s.title.split(" ")[0].toLowerCase()}`}
            className="group flex items-start gap-4 rounded-2xl border border-border bg-card p-5 transition-colors hover:border-brand-500"
          >
            <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400"><s.icon className="h-5 w-5" /></div>
            <div className="min-w-0 flex-1">
              <h3 className="font-display font-semibold">{s.title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{s.desc}</p>
              <span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-brand-600 dark:text-brand-400">{s.cta} <ArrowUpRight className="h-3.5 w-3.5" /></span>
            </div>
          </a>
        ))}
      </div>

      <div className="mb-3 mt-8 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
        <FileText className="h-4 w-4" /> More newcomer starters
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {MORE_STARTERS.map((s) => (
          <a
            key={s.title}
            href={s.url}
            target="_blank"
            rel="noreferrer"
            className="group flex items-start gap-4 rounded-2xl border border-border bg-card p-5 transition-colors hover:border-brand-500"
          >
            <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400">
              <s.icon className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="font-display font-semibold">{s.title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{s.desc}</p>
              <span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-brand-600 dark:text-brand-400">
                Open official guide <ArrowUpRight className="h-3.5 w-3.5" />
              </span>
            </div>
          </a>
        ))}
      </div>

      <p className="mt-6 text-xs text-muted-foreground">
        Prices are indicative and set by each provider. MapleJourney links you to authoritative sources — always confirm current rates on the provider's site.
      </p>
    </div>
  );
}
