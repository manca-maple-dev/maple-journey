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
  Grid,
  List,
} from "lucide-react";
import { useMaple } from "@/context/MapleContext";

const TEMPLATES = [
  // Modern Category
  {
    id: "north-star",
    name: "North Star",
    category: "Modern",
    vibe: "Clean executive",
    accent: "bg-blue-600",
    preview: "Strong header with structured sections and clean spacing.",
    layout: "single",
    colors: "blue",
  },
  {
    id: "harbour",
    name: "Harbour",
    category: "Modern",
    vibe: "Two-column sidebar",
    accent: "bg-teal-600",
    preview: "Skills sidebar + full-width experience. Perfect for showcasing depth.",
    layout: "two-column",
    colors: "teal",
  },
  {
    id: "aurora",
    name: "Aurora",
    category: "Modern",
    vibe: "Creative professional",
    accent: "bg-fuchsia-700",
    preview: "Elegant color accents with modern spacing for tech & design roles.",
    layout: "single",
    colors: "fuchsia",
  },
  
  // Classic Category
  {
    id: "cedar",
    name: "Cedar",
    category: "Classic",
    vibe: "Traditional recruiter-friendly",
    accent: "bg-emerald-700",
    preview: "Time-tested format trusted by hiring managers across industries.",
    layout: "single",
    colors: "emerald",
  },
  {
    id: "summit",
    name: "Summit",
    category: "Classic",
    vibe: "ATS-optimized",
    accent: "bg-zinc-700",
    preview: "Zero formatting—maximum compatibility with application systems.",
    layout: "single",
    colors: "zinc",
  },
  {
    id: "maple-pro",
    name: "Maple Pro",
    category: "Classic",
    vibe: "Bold professional",
    accent: "bg-brand-600",
    preview: "Confident design emphasizing achievements and measurable impact.",
    layout: "single",
    colors: "brand",
  },
  
  // Compact Category
  {
    id: "express",
    name: "Express",
    category: "Compact",
    vibe: "Single-page density",
    accent: "bg-orange-600",
    preview: "Dense but scannable—fits everything meaningful on one page.",
    layout: "compact",
    colors: "orange",
  },
  {
    id: "catalyst",
    name: "Catalyst",
    category: "Compact",
    vibe: "Impact-first bullets",
    accent: "bg-red-600",
    preview: "Abbreviated experience with bold metrics upfront. Fast hiring manager scan.",
    layout: "compact",
    colors: "red",
  },
  
  // Premium Category
  {
    id: "prestige",
    name: "Prestige",
    category: "Premium",
    vibe: "Executive showcase",
    accent: "bg-slate-900",
    preview: "Sophisticated with subtle accents. Perfect for senior/leadership roles.",
    layout: "two-column",
    colors: "slate",
  },
  {
    id: "velocity",
    name: "Velocity",
    category: "Premium",
    vibe: "Tech-forward",
    accent: "bg-cyan-600",
    preview: "Modern tech aesthetic with clear information hierarchy.",
    layout: "two-column",
    colors: "cyan",
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
  const [viewMode, setViewMode] = useState("grid"); // grid or list

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

  // Group templates by category
  const templatesByCategory = useMemo(() => {
    const grouped = {};
    TEMPLATES.forEach((t) => {
      if (!grouped[t.category]) grouped[t.category] = [];
      grouped[t.category].push(t);
    });
    return grouped;
  }, []);

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

  // Render preview based on template layout
  const renderTemplatePreview = () => {
    const layout = selectedTemplate.layout;
    const headerClasses = {
      blue: "border-blue-600 text-blue-600",
      teal: "border-teal-600 text-teal-600",
      fuchsia: "border-fuchsia-600 text-fuchsia-600",
      emerald: "border-emerald-600 text-emerald-600",
      zinc: "border-zinc-600 text-zinc-600",
      brand: "border-brand-600 text-brand-600",
      orange: "border-orange-600 text-orange-600",
      red: "border-red-600 text-red-600",
      slate: "border-slate-900 text-slate-900",
      cyan: "border-cyan-600 text-cyan-600",
    }[selectedTemplate.colors];

    // Two-column layout (sidebar)
    if (layout === "two-column") {
      return (
        <article className="rounded-2xl border border-border bg-background p-6">
          <div className="grid grid-cols-[160px_1fr] gap-6">
            {/* Left Sidebar */}
            <div className="space-y-5 border-r border-border pr-4">
              <div>
                <h5 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground opacity-60">Skills</h5>
                <div className="mt-2 space-y-1">
                  {resume.skills.split(",").slice(0, 3).map((skill, i) => (
                    <p key={i} className="text-xs text-foreground">{skill.trim()}</p>
                  ))}
                </div>
              </div>
              <div>
                <h5 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground opacity-60">Contact</h5>
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-foreground break-all">{resume.email}</p>
                  <p className="text-xs text-foreground">{resume.phone}</p>
                  <p className="text-xs text-foreground">{resume.location}</p>
                </div>
              </div>
            </div>

            {/* Right Content */}
            <div className="space-y-4">
              <div className={`border-b-2 ${headerClasses} pb-3`}>
                <h3 className="font-display text-2xl font-bold">{resume.name}</h3>
                <p className="mt-1 text-sm font-medium">{resume.headline}</p>
              </div>

              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Summary</h4>
                <p className="mt-2 text-xs leading-relaxed text-foreground">{resume.summary}</p>
              </div>

              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Experience</h4>
                <div className="mt-3 space-y-3">
                  {resume.experience.slice(0, 2).map((exp) => (
                    <div key={`${exp.title}-${exp.company}`}>
                      <div className="flex justify-between">
                        <p className="text-xs font-semibold">{exp.title}</p>
                        <p className="text-xs text-muted-foreground">{exp.period}</p>
                      </div>
                      <p className="text-xs text-muted-foreground">{exp.company}</p>
                      <ul className="mt-1 list-disc space-y-0.5 pl-3 text-xs">
                        {exp.bullets.slice(0, 1).map((b, i) => (
                          <li key={i} className="text-foreground">{b}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold">{resume.education}</p>
              </div>
            </div>
          </div>
        </article>
      );
    }

    // Compact layout (dense single-page)
    if (layout === "compact") {
      return (
        <article className="rounded-2xl border border-border bg-background p-5">
          <header className={`border-b-2 ${headerClasses} pb-2`}>
            <h3 className="font-display text-lg font-bold">{resume.name}</h3>
            <p className="text-xs font-medium text-foreground/80">{resume.headline}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">{resume.email} • {resume.phone} • {resume.location}</p>
          </header>

          <div className="mt-2 grid grid-cols-2 gap-3">
            <div>
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Summary</h4>
              <p className="mt-1 text-xs leading-tight text-foreground line-clamp-2">{resume.summary}</p>
            </div>
            <div>
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Skills</h4>
              <p className="mt-1 text-xs text-foreground line-clamp-2">{resume.skills}</p>
            </div>
          </div>

          <div className="mt-2">
            <h4 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Experience</h4>
            <div className="mt-1 space-y-1">
              {resume.experience.slice(0, 2).map((exp) => (
                <div key={`${exp.title}-${exp.company}`} className="text-xs">
                  <p className="font-semibold">{exp.title} @ {exp.company} ({exp.period})</p>
                  <p className="text-muted-foreground line-clamp-1">{exp.bullets[0]}</p>
                </div>
              ))}
            </div>
          </div>
        </article>
      );
    }

    // Default single-column layout
    return (
      <article className="rounded-2xl border border-border bg-background p-6 space-y-4">
        <header className={`border-b-2 ${headerClasses} pb-3`}>
          <h3 className="font-display text-2xl font-bold tracking-tight">{resume.name}</h3>
          <p className="mt-1 text-sm font-medium">{resume.headline}</p>
          <p className="mt-2 text-xs text-muted-foreground">{resume.email} • {resume.phone} • {resume.location}</p>
        </header>

        <section>
          <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground opacity-70">Professional Summary</h4>
          <p className="mt-2 text-sm leading-relaxed">{resume.summary}</p>
        </section>

        <section>
          <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground opacity-70">Professional Experience</h4>
          <div className="mt-2 space-y-4">
            {resume.experience.map((exp) => (
              <div key={`${exp.title}-${exp.company}`} className="border-l-2 border-border pl-3">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start">
                  <div>
                    <p className="text-sm font-bold">{exp.title}</p>
                    <p className="text-xs font-medium text-muted-foreground">{exp.company}</p>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 sm:mt-0">{exp.period}</p>
                </div>
                <ul className="mt-1.5 space-y-1 list-disc pl-4 marker:text-xs">
                  {exp.bullets.map((b, i) => (
                    <li key={i} className="text-sm">{b}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <div className="grid grid-cols-2 gap-4">
          <section>
            <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground opacity-70">Skills</h4>
            <p className="mt-2 text-sm">{resume.skills}</p>
          </section>
          <section>
            <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground opacity-70">Education</h4>
            <p className="mt-2 text-sm">{resume.education}</p>
          </section>
        </div>
      </article>
    );
  };

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
              <h1 className="mt-3 font-display text-2xl font-bold sm:text-3xl">Professional resume builder for Canada</h1>
              <p className="mt-2 max-w-2xl text-sm text-white/90">
                Choose from 10 beautifully formatted templates, customize every detail in real-time, and use Maple AI to strengthen your impact. Built specifically for Canadian hiring standards and ATS compatibility.
              </p>
            </div>
            <div className="min-w-[220px] rounded-2xl border border-white/20 bg-white/10 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-white/80">ATS Readiness Score</p>
              <p className="mt-2 text-3xl font-bold">{completeness}%</p>
              <p className="text-xs text-white/80">Aim for 85%+ before applying.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.05fr,0.95fr]">
        <div className="space-y-5">
          <div className="rounded-2xl border border-border bg-card p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <LayoutTemplate className="h-4 w-4 text-brand-600" />
                <h2 className="font-display text-lg font-semibold">Choose your template</h2>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setViewMode("grid")}
                  className={`p-1.5 rounded-lg transition-colors ${viewMode === "grid" ? "bg-brand-100 text-brand-600 dark:bg-brand-500/20" : "text-muted-foreground hover:text-foreground"}`}
                >
                  <Grid className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode("list")}
                  className={`p-1.5 rounded-lg transition-colors ${viewMode === "list" ? "bg-brand-100 text-brand-600 dark:bg-brand-500/20" : "text-muted-foreground hover:text-foreground"}`}
                >
                  <List className="h-4 w-4" />
                </button>
              </div>
            </div>

            {viewMode === "grid" ? (
              <div className="space-y-6">
                {Object.entries(templatesByCategory).map(([category, templates]) => (
                  <div key={category}>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">{category}</h3>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {templates.map((t) => {
                        const active = t.id === templateId;
                        return (
                          <button
                            key={t.id}
                            type="button"
                            onClick={() => setTemplateId(t.id)}
                            className={`rounded-2xl border p-3 text-left transition-all group ${
                              active
                                ? "border-brand-500 bg-brand-50 shadow-md dark:bg-brand-500/10"
                                : "border-border bg-background hover:border-brand-300 hover:shadow-sm"
                            }`}
                          >
                            <div className="flex items-center justify-between gap-2">
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <p className="text-sm font-semibold">{t.name}</p>
                                  <span className={`h-2.5 w-2.5 rounded-full ${t.accent}`} />
                                </div>
                                <p className="text-xs text-muted-foreground mt-0.5">{t.vibe}</p>
                              </div>
                              {active && <Check className="h-4 w-4 text-brand-600 flex-shrink-0" />}
                            </div>
                            <p className="mt-2 text-xs text-muted-foreground line-clamp-2">{t.preview}</p>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {Object.entries(templatesByCategory).map(([category, templates]) => (
                  <div key={category} className="space-y-1">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground px-2">{category}</h3>
                    {templates.map((t) => {
                      const active = t.id === templateId;
                      return (
                        <button
                          key={t.id}
                          type="button"
                          onClick={() => setTemplateId(t.id)}
                          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg border transition-all text-left ${
                            active
                              ? "border-brand-500 bg-brand-50 dark:bg-brand-500/10"
                              : "border-transparent bg-background hover:border-border"
                          }`}
                        >
                          <span className={`h-3 w-3 rounded-full flex-shrink-0 ${t.accent}`} />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold">{t.name}</p>
                            <p className="text-xs text-muted-foreground">{t.vibe}</p>
                          </div>
                          {active && <Check className="h-4 w-4 text-brand-600 flex-shrink-0" />}
                        </button>
                      );
                    })}
                  </div>
                ))}
              </div>
            )}
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
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="font-display text-lg font-semibold">{selectedTemplate.name} Preview</h2>
                <p className="mt-0.5 text-xs text-muted-foreground">{selectedTemplate.category}</p>
              </div>
              <span className="rounded-full bg-secondary px-2.5 py-1 text-xs font-semibold text-muted-foreground">{selectedTemplate.vibe}</span>
            </div>

            <div className="overflow-hidden rounded-2xl border border-border">
              <div className="bg-foreground/5 p-6 max-h-[600px] overflow-y-auto">
                {renderTemplatePreview()}
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5">
            <h3 className="font-display text-lg font-semibold mb-1">Maple power tools</h3>
            <p className="text-xs text-muted-foreground mb-4">Enhance and export your resume</p>
            
            {/* Download Button - Prominent */}
            <div className="mb-4 rounded-2xl bg-gradient-to-r from-brand-50 to-brand-100/50 dark:from-brand-500/10 dark:to-brand-600/10 border-2 border-brand-200 dark:border-brand-500/30 p-4">
              <button
                type="button"
                onClick={() => window.print()}
                className="w-full flex items-center justify-between rounded-xl bg-gradient-to-r from-brand-600 to-brand-700 hover:from-brand-700 hover:to-brand-800 text-white px-4 py-3.5 text-sm font-semibold transition-all shadow-lg hover:shadow-xl active:scale-95"
              >
                <span className="inline-flex items-center gap-2">
                  <Download className="h-5 w-5" />
                  <span>Download as PDF</span>
                </span>
                <span className="text-xs bg-white/20 rounded-full px-2.5 py-1">Ctrl+P</span>
              </button>
              <p className="text-xs text-muted-foreground mt-2 text-center">Save professionally formatted resume to your computer</p>
            </div>

            {/* Other Tools */}
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => askMapleToEnhance("resume", toMarkdown(resume))}
                className="flex w-full items-center justify-between rounded-xl border border-border bg-background px-3 py-2.5 text-left text-sm hover:bg-secondary/50 transition-colors"
              >
                <span className="inline-flex items-center gap-2"><Sparkles className="h-4 w-4 text-brand-600" /> Rewrite full resume for Canadian recruiters</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </button>
              <button
                type="button"
                onClick={() => askMapleToEnhance("experience bullets", resume.experience.flatMap((e) => e.bullets).join(" | "))}
                className="flex w-full items-center justify-between rounded-xl border border-border bg-background px-3 py-2.5 text-left text-sm hover:bg-secondary/50 transition-colors"
              >
                <span className="inline-flex items-center gap-2"><BadgeCheck className="h-4 w-4 text-brand-600" /> Improve impact metrics in bullets</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </button>
              <button
                type="button"
                onClick={copyMarkdown}
                className="flex w-full items-center justify-between rounded-xl border border-border bg-background px-3 py-2.5 text-left text-sm hover:bg-secondary/50 transition-colors"
              >
                <span className="inline-flex items-center gap-2">
                  {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4 text-brand-600" />} 
                  {copied ? "Copied markdown resume" : "Copy resume as markdown"}
                </span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Floating Download Bar - Sticky Bottom */}
      <div className="fixed bottom-0 left-0 right-0 border-t border-border bg-card/95 backdrop-blur-sm p-4 sm:p-6 z-40">
        <div className="mx-auto max-w-7xl flex items-center justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-foreground">Ready to download?</p>
            <p className="text-xs text-muted-foreground">Your {selectedTemplate.name} resume is ready</p>
          </div>
          <div className="flex gap-2 flex-shrink-0">
            <button
              type="button"
              onClick={copyMarkdown}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background hover:bg-secondary px-3 py-2 text-xs font-medium transition-colors"
            >
              <Copy className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Copy</span>
            </button>
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-brand-600 to-brand-700 hover:from-brand-700 hover:to-brand-800 text-white px-4 py-2 text-xs font-semibold transition-all shadow-md hover:shadow-lg active:scale-95"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Download PDF</span>
            </button>
          </div>
        </div>
      </div>

      {/* Padding for sticky bar */}
      <div className="h-24" />
    </div>
  );
}
