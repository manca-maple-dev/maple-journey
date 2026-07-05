import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Sparkles,
  LayoutTemplate,
  Wand2,
  Copy,
  Check,
  ArrowRight,
  Download,
  BadgeCheck,
} from "lucide-react";
import { useMaple } from "@/context/MapleContext";

const TEMPLATES = [
  {
    id: "north-star",
    name: "North Star",
    vibe: "Clean executive",
    accent: "bg-blue-600",
    preview: "A strong top summary with structured experience blocks.",
  },
  {
    id: "harbour",
    name: "Harbour",
    vibe: "Modern newcomer",
    accent: "bg-teal-600",
    preview: "Balanced design for both service and office roles.",
  },
  {
    id: "summit",
    name: "Summit",
    vibe: "ATS-first",
    accent: "bg-zinc-700",
    preview: "Minimal layout optimized for applicant tracking systems.",
  },
  {
    id: "maple-pro",
    name: "Maple Pro",
    vibe: "Bold premium",
    accent: "bg-brand-600",
    preview: "Confident profile presentation with measurable impact focus.",
  },
  {
    id: "cedar",
    name: "Cedar",
    vibe: "Classic professional",
    accent: "bg-emerald-700",
    preview: "Traditional recruiter-friendly style for broad industries.",
  },
  {
    id: "aurora",
    name: "Aurora",
    vibe: "Creative clean",
    accent: "bg-fuchsia-700",
    preview: "Subtle color accents for design, media, and product roles.",
  },
];

function toMarkdown(resume) {
  const lines = [
    `# ${resume.name}`,
    `${resume.headline}`,
    "",
    `- Email: ${resume.email}`,
    `- Phone: ${resume.phone}`,
    `- Location: ${resume.location}`,
    "",
    "## Summary",
    resume.summary,
    "",
    "## Experience",
    ...resume.experience.flatMap((exp) => [
      `### ${exp.title} - ${exp.company}`,
      `${exp.period}`,
      ...exp.bullets.map((b) => `- ${b}`),
      "",
    ]),
    "## Skills",
    resume.skills,
    "",
    "## Education",
    resume.education,
  ];
  return lines.join("\n").trim();
}

export default function ResumeStudio() {
  const navigate = useNavigate();
  const { openWith } = useMaple();
  const [templateId, setTemplateId] = useState("maple-pro");
  const [copied, setCopied] = useState(false);
  const [resume, setResume] = useState({
    name: "Your Name",
    headline: "Newcomer professional in Canada | Customer Service | Operations",
    email: "you@email.com",
    phone: "+1 647 000 0000",
    location: "Toronto, ON",
    summary:
      "Results-driven professional with newcomer resilience, strong communication, and a proven ability to improve service quality and team efficiency in fast-paced environments.",
    skills: "Customer Support, POS Systems, Scheduling, Team Collaboration, English, French",
    education: "Diploma in Business Administration, 2023",
    experience: [
      {
        title: "Customer Service Associate",
        company: "Northside Retail",
        period: "2024 - Present",
        bullets: [
          "Improved customer satisfaction by 18% by reducing response times and resolving issues on first contact.",
          "Handled 80+ customer interactions per shift while maintaining high quality and empathy.",
        ],
      },
      {
        title: "Operations Assistant",
        company: "Bright Logistics",
        period: "2022 - 2024",
        bullets: [
          "Supported shipment coordination and cut recurring delays by 22% through better daily checklists.",
          "Maintained accurate records across inventory and delivery systems.",
        ],
      },
    ],
  });

  const selectedTemplate = useMemo(
    () => TEMPLATES.find((t) => t.id === templateId) || TEMPLATES[0],
    [templateId]
  );

  const completeness = useMemo(() => {
    let score = 0;
    if (resume.name.trim()) score += 10;
    if (resume.headline.trim()) score += 10;
    if (resume.summary.trim().length > 80) score += 20;
    if (resume.skills.trim()) score += 15;
    if (resume.education.trim()) score += 15;
    if (resume.experience.every((e) => e.bullets.filter(Boolean).length >= 2)) score += 30;
    return score;
  }, [resume]);

  const updateExpBullet = (index, bulletIndex, value) => {
    setResume((prev) => {
      const copy = { ...prev, experience: [...prev.experience] };
      const expCopy = { ...copy.experience[index], bullets: [...copy.experience[index].bullets] };
      expCopy.bullets[bulletIndex] = value;
      copy.experience[index] = expCopy;
      return copy;
    });
  };

  const askMapleToEnhance = (section, text) => {
    openWith(
      `Enhance my resume ${section}. Keep it ATS-friendly for Canada, action-oriented, and concise. Current text: ${text}`
    );
    navigate("/app/chat");
  };

  const copyMarkdown = async () => {
    const md = toMarkdown(resume);
    try {
      await navigator.clipboard.writeText(md);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-5" data-testid="resume-studio-page">
      <section className="overflow-hidden rounded-3xl border border-border bg-card">
        <div className="bg-gradient-to-r from-brand-700 via-brand-600 to-maple px-6 py-6 text-white sm:px-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold">
                <Sparkles className="h-3.5 w-3.5" /> Maple Resume Studio
              </p>
              <h1 className="mt-3 font-display text-2xl font-bold sm:text-3xl">Build resume templates people remember</h1>
              <p className="mt-2 max-w-2xl text-sm text-white/90">
                Pick a clean template, edit every section in real time, and use Maple to rewrite your profile for stronger recruiter impact.
              </p>
            </div>
            <div className="min-w-[220px] rounded-2xl border border-white/20 bg-white/10 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-white/80">ATS readiness</p>
              <p className="mt-2 text-3xl font-bold">{completeness}%</p>
              <p className="text-xs text-white/80">Aim for 85%+ before applying.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.05fr,0.95fr]">
        <div className="space-y-5">
          <div className="rounded-2xl border border-border bg-card p-5">
            <div className="mb-3 flex items-center gap-2">
              <LayoutTemplate className="h-4 w-4 text-brand-600" />
              <h2 className="font-display text-lg font-semibold">Choose a template</h2>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {TEMPLATES.map((t) => {
                const active = t.id === templateId;
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setTemplateId(t.id)}
                    className={`rounded-2xl border p-3 text-left transition-all ${
                      active
                        ? "border-brand-500 bg-brand-50 shadow-sm dark:bg-brand-500/10"
                        : "border-border bg-background hover:border-brand-300"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold">{t.name}</p>
                        <p className="text-xs text-muted-foreground">{t.vibe}</p>
                      </div>
                      <span className={`h-3 w-3 rounded-full ${t.accent}`} />
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">{t.preview}</p>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="font-display text-lg font-semibold">Edit your content</h2>
              <button
                type="button"
                onClick={() => askMapleToEnhance("summary", resume.summary)}
                className="inline-flex items-center gap-1.5 rounded-full border border-brand-500/30 bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700 hover:bg-brand-100 dark:bg-brand-500/10"
              >
                <Wand2 className="h-3.5 w-3.5" /> Enhance with Maple
              </button>
            </div>

            <div className="space-y-3">
              <input
                value={resume.name}
                onChange={(e) => setResume((p) => ({ ...p, name: e.target.value }))}
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm"
                placeholder="Full name"
              />
              <input
                value={resume.headline}
                onChange={(e) => setResume((p) => ({ ...p, headline: e.target.value }))}
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm"
                placeholder="Headline"
              />
              <textarea
                value={resume.summary}
                onChange={(e) => setResume((p) => ({ ...p, summary: e.target.value }))}
                className="min-h-[110px] w-full rounded-xl border border-border bg-background px-3 py-2 text-sm"
                placeholder="Professional summary"
              />
              <input
                value={resume.skills}
                onChange={(e) => setResume((p) => ({ ...p, skills: e.target.value }))}
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm"
                placeholder="Skills"
              />
              <input
                value={resume.education}
                onChange={(e) => setResume((p) => ({ ...p, education: e.target.value }))}
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm"
                placeholder="Education"
              />

              <div className="space-y-3 rounded-xl border border-border bg-background p-3">
                <p className="text-sm font-semibold">Experience bullets</p>
                {resume.experience.map((exp, i) => (
                  <div key={`${exp.company}-${i}`} className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">{exp.title} at {exp.company}</p>
                    {exp.bullets.map((b, bi) => (
                      <textarea
                        key={`${exp.company}-${bi}`}
                        value={b}
                        onChange={(e) => updateExpBullet(i, bi, e.target.value)}
                        className="min-h-[72px] w-full rounded-xl border border-border bg-card px-3 py-2 text-sm"
                      />
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="rounded-2xl border border-border bg-card p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold">Live preview - {selectedTemplate.name}</h2>
              <span className="rounded-full bg-secondary px-2.5 py-1 text-xs font-semibold text-muted-foreground">{selectedTemplate.vibe}</span>
            </div>

            <article className="rounded-2xl border border-border bg-background p-5">
              <header className="border-b border-border pb-3">
                <h3 className="font-display text-xl font-bold tracking-tight">{resume.name}</h3>
                <p className="mt-1 text-sm font-medium text-brand-700 dark:text-brand-300">{resume.headline}</p>
                <p className="mt-2 text-xs text-muted-foreground">{resume.email} • {resume.phone} • {resume.location}</p>
              </header>

              <section className="pt-3">
                <h4 className="text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground">Summary</h4>
                <p className="mt-1 text-sm leading-relaxed">{resume.summary}</p>
              </section>

              <section className="pt-3">
                <h4 className="text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground">Experience</h4>
                <div className="mt-2 space-y-3">
                  {resume.experience.map((exp) => (
                    <div key={`${exp.title}-${exp.company}`}>
                      <p className="text-sm font-semibold">{exp.title} - {exp.company}</p>
                      <p className="text-xs text-muted-foreground">{exp.period}</p>
                      <ul className="mt-1 list-disc space-y-1 pl-4 text-sm">
                        {exp.bullets.map((b, bi) => (
                          <li key={`${exp.company}-preview-${bi}`}>{b}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </section>

              <section className="pt-3">
                <h4 className="text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground">Skills</h4>
                <p className="mt-1 text-sm">{resume.skills}</p>
              </section>

              <section className="pt-3">
                <h4 className="text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground">Education</h4>
                <p className="mt-1 text-sm">{resume.education}</p>
              </section>
            </article>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5">
            <h3 className="font-display text-lg font-semibold">Maple power tools</h3>
            <div className="mt-3 space-y-2">
              <button
                type="button"
                onClick={() => askMapleToEnhance("resume", toMarkdown(resume))}
                className="flex w-full items-center justify-between rounded-xl border border-border bg-background px-3 py-2.5 text-left text-sm hover:border-brand-300"
              >
                <span className="inline-flex items-center gap-2"><Sparkles className="h-4 w-4 text-brand-600" /> Rewrite full resume for Canadian recruiters</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </button>
              <button
                type="button"
                onClick={() => askMapleToEnhance("experience bullets", resume.experience.flatMap((e) => e.bullets).join(" | "))}
                className="flex w-full items-center justify-between rounded-xl border border-border bg-background px-3 py-2.5 text-left text-sm hover:border-brand-300"
              >
                <span className="inline-flex items-center gap-2"><BadgeCheck className="h-4 w-4 text-brand-600" /> Improve impact metrics in bullets</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </button>
              <button
                type="button"
                onClick={copyMarkdown}
                className="flex w-full items-center justify-between rounded-xl border border-border bg-background px-3 py-2.5 text-left text-sm hover:border-brand-300"
              >
                <span className="inline-flex items-center gap-2">
                  {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4 text-brand-600" />} 
                  {copied ? "Copied markdown resume" : "Copy resume as markdown"}
                </span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </button>
              <button
                type="button"
                onClick={() => window.print()}
                className="flex w-full items-center justify-between rounded-xl border border-border bg-background px-3 py-2.5 text-left text-sm hover:border-brand-300"
              >
                <span className="inline-flex items-center gap-2"><Download className="h-4 w-4 text-brand-600" /> Print / Save as PDF</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
