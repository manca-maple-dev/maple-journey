import { LegalPageHeader } from "@/components/marketing/LegalPageHeader";

function Section({ title, children }) {
  return (
    <section className="mt-10">
      <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-7 text-muted-foreground">{children}</div>
    </section>
  );
}

export default function TermsOfService() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-16">
      <LegalPageHeader
        eyebrow="Legal"
        title="Terms of Service"
        updatedAt="July 4, 2026"
      />

      <Section title="Use of MapleJourney">
        <p>By using MapleJourney, you agree to use the service only for lawful purposes and in accordance with these Terms. You are responsible for the accuracy of the information you provide and for maintaining the confidentiality of your account credentials.</p>
      </Section>

      <Section title="Service Scope">
        <p>MapleJourney provides digital tools for guidance, organization, information discovery, planning, resource discovery, and AI-assisted support for newcomers in Canada. Features may include onboarding, profile tools, AI chat, legal resource listings, jobs, benefits, reminders, community discovery, and subscription management.</p>
      </Section>

      <Section title="No Legal Advice or Representation">
        <p>MapleJourney is not a law firm, legal clinic, immigration representative, or government authority unless explicitly stated in a separate written agreement. Nothing on the platform creates a lawyer-client, consultant-client, or representative relationship.</p>
        <p>Information and AI-generated responses are provided for general informational and organizational purposes only and should not be relied on as legal advice or a guarantee of outcome.</p>
      </Section>

      <Section title="Acceptable Use">
        <p>You may not use MapleJourney to break the law, abuse other users, submit fraudulent information, interfere with security controls, attempt prompt injection or extraction attacks, scrape the service without authorization, or misuse the platform as a substitute for emergency or professional services.</p>
      </Section>

      <Section title="AI Features">
        <p>AI outputs may be inaccurate, incomplete, delayed, or unsuitable for your circumstances. You are responsible for reviewing, validating, and deciding whether to act on any generated output.</p>
      </Section>

      <Section title="Billing and Paid Features">
        <p>If MapleJourney offers paid plans, prices, billing cycles, renewals, cancellations, and refund rules will be disclosed at the point of purchase. Payment processing may be handled by third-party providers.</p>
      </Section>

      <Section title="Termination and Availability">
        <p>MapleJourney may modify, suspend, or discontinue features at any time. Access may be limited or terminated where necessary to protect the service, comply with law, or prevent abuse.</p>
      </Section>

      <Section title="Disclaimers and Liability">
        <p>The service is provided on an "as is" and "as available" basis to the extent permitted by law. MapleJourney does not guarantee uninterrupted availability, complete accuracy, or suitability for every purpose.</p>
      </Section>

      <Section title="Governing Law">
        <p>Unless applicable law requires otherwise, these Terms are intended to be governed by the laws of Alberta and the federal laws of Canada applicable in Alberta.</p>
      </Section>

      <Section title="Contact">
        <p>MapleJourney operates from Calgary, Alberta, Canada. Planned public legal and support contacts include <a className="text-brand-500 underline underline-offset-2" href="mailto:legal@maplejourney.ca">legal@maplejourney.ca</a> and <a className="text-brand-500 underline underline-offset-2" href="mailto:support@maplejourney.ca">support@maplejourney.ca</a>.</p>
      </Section>
    </div>
  );
}