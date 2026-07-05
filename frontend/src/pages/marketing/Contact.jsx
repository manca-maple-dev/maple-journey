import { Mail, MapPin, ShieldCheck, Scale, LifeBuoy } from "lucide-react";
import { LegalPageHeader } from "@/components/marketing/LegalPageHeader";

const CONTACTS = [
  {
    icon: LifeBuoy,
    title: "General support",
    value: "support@maplejourney.ca",
    href: "mailto:support@maplejourney.ca",
    description: "Questions about your account, access, features, or onboarding.",
  },
  {
    icon: ShieldCheck,
    title: "Privacy",
    value: "privacy@maplejourney.ca",
    href: "mailto:privacy@maplejourney.ca",
    description: "Requests related to privacy, data handling, export, or deletion.",
  },
  {
    icon: Scale,
    title: "Legal",
    value: "legal@maplejourney.ca",
    href: "mailto:legal@maplejourney.ca",
    description: "Questions about terms, disclaimers, compliance, or official notices.",
  },
  {
    icon: Mail,
    title: "Billing",
    value: "billing@maplejourney.ca",
    href: "mailto:billing@maplejourney.ca",
    description: "Subscription, payment, cancellation, or invoice questions.",
  },
];

export default function Contact() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-16">
      <LegalPageHeader
        eyebrow="Contact"
        title="Reach MapleJourney"
        updatedAt="July 4, 2026"
        intro="MapleJourney helps newcomers in Canada organize information, understand next steps, and find trustworthy resources. For account, privacy, billing, or legal questions, use the contact channels below."
      />

      <div className="mt-8 rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">
        <div className="flex items-center gap-3">
          <MapPin className="h-4 w-4 text-brand-500" />
          <span>Operating location: Calgary, Alberta, Canada. No public street address is published.</span>
        </div>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {CONTACTS.map((item) => (
          <div key={item.title} className="rounded-2xl border border-border bg-card p-6">
            <div className="grid h-11 w-11 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10">
              <item.icon className="h-5 w-5" />
            </div>
            <h2 className="mt-4 text-lg font-semibold tracking-tight">{item.title}</h2>
            <p className="mt-2 text-sm text-muted-foreground">{item.description}</p>
            <a href={item.href} className="mt-4 inline-block text-sm font-semibold text-brand-500 hover:underline underline-offset-2">
              {item.value}
            </a>
          </div>
        ))}
      </div>

      <div className="mt-10 rounded-2xl border border-border bg-secondary/40 p-5 text-sm leading-7 text-muted-foreground">
        MapleJourney is not a law firm, government office, or emergency service. If you need urgent legal help, emergency housing, crisis support, or medical assistance,
        contact the appropriate qualified provider directly.
      </div>
    </div>
  );
}