import { LegalPageHeader } from "@/components/marketing/LegalPageHeader";

function Section({ title, children }) {
  return (
    <section className="mt-10">
      <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-7 text-muted-foreground">{children}</div>
    </section>
  );
}

export default function CookiePolicy() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-16">
      <LegalPageHeader
        eyebrow="Legal"
        title="Cookie Policy"
        updatedAt="July 4, 2026"
      />

      <Section title="What Cookies Are">
        <p>Cookies and similar technologies are small files or identifiers used to remember sessions, preferences, and service activity across visits.</p>
      </Section>

      <Section title="How MapleJourney Uses Them">
        <p>MapleJourney may use cookies, local storage, and similar tools to keep users signed in, remember preferences, preserve onboarding state, improve performance, support analytics, and protect accounts against abuse.</p>
      </Section>

      <Section title="Categories">
        <p>These technologies may include strictly necessary session tools, functional preference storage, analytics tools, and performance or reliability monitoring.</p>
      </Section>

      <Section title="Your Controls">
        <p>Most browsers allow you to control or delete cookies through browser settings. Blocking some cookies may affect sign-in, preferences, onboarding continuity, or other core product features.</p>
      </Section>

      <Section title="Contact">
        <p>Questions about cookie or tracking practices may be directed to MapleJourney through <a className="text-brand-500 underline underline-offset-2" href="mailto:privacy@maplejourney.ca">privacy@maplejourney.ca</a> once that mailbox is activated for the maplejourney.ca domain.</p>
      </Section>
    </div>
  );
}