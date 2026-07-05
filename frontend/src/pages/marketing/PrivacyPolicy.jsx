import { LegalPageHeader } from "@/components/marketing/LegalPageHeader";

function Section({ title, children }) {
  return (
    <section className="mt-10">
      <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-7 text-muted-foreground">{children}</div>
    </section>
  );
}

export default function PrivacyPolicy() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-16">
      <LegalPageHeader
        eyebrow="Legal"
        title="Privacy Policy"
        updatedAt="July 4, 2026"
        intro="MapleJourney is an AI-powered digital platform based in Calgary, Alberta, Canada for informational, organizational, and assistive support for newcomers. This policy explains what information MapleJourney may collect, how it may use that information, and the choices available to users."
      />

      <Section title="What We Collect">
        <p>MapleJourney may collect account information such as name, email address, password-related authentication data, phone number, subscription details, and service preferences.</p>
        <p>MapleJourney may also collect onboarding, profile, questionnaire, and feature usage information you choose to provide, including immigration pathway details, location inputs, job preferences, legal topics, community preferences, reminders, and chat interactions.</p>
        <p>Technical information such as IP address, browser type, device information, session data, logs, and security-related activity may also be collected to operate and protect the service.</p>
      </Section>

      <Section title="How We Use Information">
        <p>Information may be used to create and secure accounts, personalize recommendations, support AI-assisted chat and planning tools, show legal or community resources, process billing, send notifications, improve service quality, and prevent abuse or unauthorized access.</p>
        <p>MapleJourney may use automated systems and AI to generate summaries, recommendations, and reminders. These features are assistive only and should be verified against official sources before important decisions are made.</p>
      </Section>

      <Section title="How Information May Be Shared">
        <p>MapleJourney may share information with service providers that support hosting, databases, authentication, payments, communications, analytics, logging, and infrastructure operations. Information may also be disclosed where required by law or to protect users, rights, or system integrity.</p>
        <p>MapleJourney does not present this page as a promise to sell personal information. If third-party analytics, advertising, or additional sharing practices are introduced, this policy should be updated before those features go live.</p>
      </Section>

      <Section title="Retention and Security">
        <p>Information is retained for as long as reasonably necessary to operate the service, maintain security, comply with legal obligations, resolve disputes, and enforce platform rules.</p>
        <p>MapleJourney uses reasonable administrative, technical, and organizational safeguards to protect information, but no system can guarantee absolute security.</p>
      </Section>

      <Section title="Your Choices">
        <p>Depending on applicable law, users may have the right to request access, correction, deletion, export, or withdrawal of consent for certain optional processing activities.</p>
        <p>If account deletion or data export features are available in the product, those controls can be used directly. Additional privacy requests should be handled through the contact method MapleJourney publishes for support or privacy matters.</p>
      </Section>

      <Section title="Important Notice">
        <p>MapleJourney is not a law firm, government agency, or legal representative. AI-generated content may be inaccurate, incomplete, or outdated. Users should verify important information with official government sources or qualified professionals.</p>
      </Section>

      <Section title="Contact">
        <p>For privacy or support questions, use the professional domain-based contact channels published for MapleJourney, including <a className="text-brand-500 underline underline-offset-2" href="mailto:privacy@maplejourney.ca">privacy@maplejourney.ca</a> and <a className="text-brand-500 underline underline-offset-2" href="mailto:support@maplejourney.ca">support@maplejourney.ca</a>.</p>
        <p>Operational location: Calgary, Alberta, Canada.</p>
      </Section>
    </div>
  );
}