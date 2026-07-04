import { LegalPageHeader } from "@/components/marketing/LegalPageHeader";

function Section({ title, children }) {
  return (
    <section className="mt-10">
      <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-7 text-muted-foreground">{children}</div>
    </section>
  );
}

export default function LegalDisclaimer() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-16">
      <LegalPageHeader
        eyebrow="Legal"
        title="AI and Legal Disclaimer"
        updatedAt="July 4, 2026"
      />

      <div className="mt-6 rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">
        MapleJourney is an AI-powered platform that provides informational, educational, organizational, and assistive tools for newcomers in Canada. MapleJourney is not a law firm, legal clinic, government office, or legal representative.
      </div>

      <Section title="No Legal Advice">
        <p>Nothing on MapleJourney constitutes legal advice, legal strategy, legal representation, or a guarantee of immigration, refugee, employment, housing, benefits, or citizenship outcomes.</p>
      </Section>

      <Section title="AI Output Warning">
        <p>AI-generated responses, summaries, rankings, reminders, and recommendations may be inaccurate, incomplete, delayed, or outdated. Users must verify important information with official government sources, legal aid providers, or qualified licensed professionals before relying on it.</p>
      </Section>

      <Section title="Third-Party Sources">
        <p>MapleJourney may reference official sources, legal aid providers, OpenStreetMap data, settlement resources, job information, or other third-party content. Those references do not mean MapleJourney is affiliated with, endorsed by, or authorized to act for those organizations.</p>
      </Section>

      <Section title="Emergency and Professional Support">
        <p>MapleJourney is not an emergency service. If you need urgent legal help, crisis support, emergency housing, urgent medical care, or immediate protection, contact the appropriate qualified service provider or emergency authority directly.</p>
      </Section>

      <Section title="Location and Contact">
        <p>MapleJourney is operated from Calgary, Alberta, Canada. Planned public contact channels for the maplejourney.ca domain include <a className="text-brand-500 underline underline-offset-2" href="mailto:support@maplejourney.ca">support@maplejourney.ca</a> and <a className="text-brand-500 underline underline-offset-2" href="mailto:legal@maplejourney.ca">legal@maplejourney.ca</a>.</p>
      </Section>
    </div>
  );
}