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
import QualityPreviewModal from "@/components/resume/QualityPreviewModal";

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

const SMART_THEMES = {
  general: {
    name: "Balanced Professional",
    accent: "#2563eb",
    accentSoft: "#dbeafe",
    accentBorder: "#93c5fd",
    heading: "#0f172a",
    body: "#1f2937",
    muted: "#6b7280",
  },
  tech: {
    name: "Technical Precision",
    accent: "#0f766e",
    accentSoft: "#ccfbf1",
    accentBorder: "#5eead4",
    heading: "#042f2e",
    body: "#134e4a",
    muted: "#0f766e",
  },
  healthcare: {
    name: "Trust & Care",
    accent: "#0369a1",
    accentSoft: "#e0f2fe",
    accentBorder: "#7dd3fc",
    heading: "#082f49",
    body: "#0c4a6e",
    muted: "#0369a1",
  },
  finance: {
    name: "Executive Finance",
    accent: "#14532d",
    accentSoft: "#dcfce7",
    accentBorder: "#86efac",
    heading: "#052e16",
    body: "#166534",
    muted: "#15803d",
  },
  creative: {
    name: "Creative Impact",
    accent: "#9d174d",
    accentSoft: "#fce7f3",
    accentBorder: "#f9a8d4",
    heading: "#500724",
    body: "#831843",
    muted: "#9d174d",
  },
};

const TEMPLATE_VISUALS = {
  "north-star": { titleSize: "text-2xl", sectionTrack: "tracking-[0.12em]", contentGap: "space-y-4", sectionLabelSize: "text-xs" },
  harbour: { titleSize: "text-2xl", sectionTrack: "tracking-[0.14em]", contentGap: "space-y-4", sectionLabelSize: "text-xs" },
  aurora: { titleSize: "text-[1.85rem]", sectionTrack: "tracking-[0.16em]", contentGap: "space-y-5", sectionLabelSize: "text-xs" },
  cedar: { titleSize: "text-2xl", sectionTrack: "tracking-[0.13em]", contentGap: "space-y-4", sectionLabelSize: "text-xs" },
  summit: { titleSize: "text-xl", sectionTrack: "tracking-[0.1em]", contentGap: "space-y-3", sectionLabelSize: "text-[11px]" },
  "maple-pro": { titleSize: "text-2xl", sectionTrack: "tracking-[0.12em]", contentGap: "space-y-4", sectionLabelSize: "text-xs" },
  express: { titleSize: "text-lg", sectionTrack: "tracking-[0.08em]", contentGap: "space-y-2", sectionLabelSize: "text-[10px]" },
  catalyst: { titleSize: "text-lg", sectionTrack: "tracking-[0.09em]", contentGap: "space-y-2", sectionLabelSize: "text-[10px]" },
  prestige: { titleSize: "text-[2rem]", sectionTrack: "tracking-[0.2em]", contentGap: "space-y-5", sectionLabelSize: "text-xs" },
  velocity: { titleSize: "text-[1.9rem]", sectionTrack: "tracking-[0.16em]", contentGap: "space-y-5", sectionLabelSize: "text-xs" },
};

const NEWCOMER_PRESETS = {
  office: {
    id: "office",
    label: "Office / Admin",
    resume: {
      name: "Your Name",
      headline: "Newcomer Professional in Canada | Customer Service & Office Operations",
      email: "you@email.com",
      phone: "+1 647 000 0000",
      location: "Toronto, ON",
      summary:
        "Detail-oriented newcomer professional with customer service and office operations experience. Strong at coordinating schedules, supporting teams, and resolving client concerns with professionalism, empathy, and clear communication.",
      skills: "Customer Service, Office Administration, POS Systems, Scheduling, Conflict Resolution, Team Collaboration, English, French",
      education: "Diploma in Business Administration, 2023 | Toronto, ON",
      experience: [
        {
          title: "Customer Service Specialist",
          company: "Northside Retail",
          period: "2024 - Present",
          bullets: [
            "Improved customer satisfaction by 18% by reducing response times and resolving issues at first contact.",
            "Handled 80+ customer interactions per shift while maintaining service quality, empathy, and accuracy.",
          ],
        },
        {
          title: "Operations Coordinator Assistant",
          company: "Bright Logistics",
          period: "2022 - 2024",
          bullets: [
            "Supported shipment coordination and reduced recurring delays by 22% through stronger daily process checks.",
            "Maintained accurate records across inventory and delivery systems to improve reporting reliability.",
          ],
        },
      ],
    },
  },
  healthcare: {
    id: "healthcare",
    label: "Healthcare Support",
    resume: {
      name: "Your Name",
      headline: "Newcomer Professional in Canada | Healthcare Support & Patient Service",
      email: "you@email.com",
      phone: "+1 647 000 0000",
      location: "Toronto, ON",
      summary:
        "Compassionate healthcare support professional with strong patient service, communication, and care-coordination skills. Committed to safe, respectful care delivery while supporting clinical teams in busy healthcare environments.",
      skills: "Patient Support, Appointment Coordination, Medical Documentation, Communication, Team Collaboration, English, French",
      education: "Healthcare Administration Certificate, 2023 | Toronto, ON",
      experience: [
        {
          title: "Patient Service Assistant",
          company: "Community Health Centre",
          period: "2024 - Present",
          bullets: [
            "Supported patient intake and appointment flow, improving check-in efficiency by 20%.",
            "Responded to 60+ daily patient inquiries with clear communication and culturally sensitive support.",
          ],
        },
        {
          title: "Clinic Operations Assistant",
          company: "WellCare Medical Group",
          period: "2022 - 2024",
          bullets: [
            "Maintained accurate patient records and reduced documentation errors through stronger verification checks.",
            "Coordinated schedules and follow-ups to help the care team improve continuity of service.",
          ],
        },
      ],
    },
  },
};

function detectResumeDomain(headline = "", skills = "") {
  const text = `${headline} ${skills}`.toLowerCase();
  if (/(developer|engineer|software|data|cloud|devops|python|react|javascript|it)/.test(text)) return "tech";
  if (/(nurse|health|medical|clinic|caregiver|healthcare|pharmacy)/.test(text)) return "healthcare";
  if (/(finance|account|bank|analyst|bookkeeper|audit|tax)/.test(text)) return "finance";
  if (/(design|creative|marketing|content|brand|ux|ui|artist)/.test(text)) return "creative";
  return "general";
}

function withTemplateAccent(theme, templateId) {
  const overrides = {
    "north-star": "#2563eb",
    harbour: "#0f766e",
    aurora: "#a21caf",
    cedar: "#166534",
    summit: "#334155",
    "maple-pro": "#9333ea",
    express: "#ea580c",
    catalyst: "#dc2626",
    prestige: "#0f172a",
    velocity: "#0891b2",
  };
  const accent = overrides[templateId] || theme.accent;
  return {
    ...theme,
    accent,
  };
}

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
  const [showQualityPreview, setShowQualityPreview] = useState(false);
  const [printSafe, setPrintSafe] = useState(true);
  const [previewMode, setPreviewMode] = useState("normal"); // normal or fullscreen
  const [showEmptyTemplate, setShowEmptyTemplate] = useState(false); // show template structure without content
  const [activePreset, setActivePreset] = useState("office");

  const [resume, setResume] = useState(NEWCOMER_PRESETS.office.resume);

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

  const smartTheme = useMemo(() => {
    const domain = detectResumeDomain(resume.headline, resume.skills);
    const baseTheme = SMART_THEMES[domain] || SMART_THEMES.general;
    return {
      domain,
      ...withTemplateAccent(baseTheme, templateId),
    };
  }, [resume.headline, resume.skills, templateId]);

  const visualSystem = useMemo(
    () => TEMPLATE_VISUALS[templateId] || TEMPLATE_VISUALS["maple-pro"],
    [templateId]
  );

  const renderTheme = useMemo(() => {
    if (!printSafe) return smartTheme;
    return {
      ...smartTheme,
      accent: smartTheme.accent,
      accentSoft: "#f8fafc",
      accentBorder: "#cbd5e1",
      body: "#111827",
      muted: "#374151",
      heading: "#020617",
    };
  }, [smartTheme, printSafe]);

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
              <div className="border-b-2 pb-3" style={{ borderColor: renderTheme.accent, color: renderTheme.heading }}>
                <h3 className={`font-display ${visualSystem.titleSize} font-bold`} style={{ color: renderTheme.heading }}>{resume.name}</h3>
                <p className="mt-1 text-sm font-medium">{resume.headline}</p>
              </div>

              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Summary</h4>
                <p className="mt-2 text-xs leading-relaxed" style={{ color: renderTheme.body }}>{resume.summary}</p>
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
                          <li key={i} style={{ color: renderTheme.body }}>{b}</li>
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
          <header className="border-b-2 pb-2" style={{ borderColor: renderTheme.accent }}>
            <h3 className={`font-display ${visualSystem.titleSize} font-bold`} style={{ color: renderTheme.heading }}>{resume.name}</h3>
            <p className="text-xs font-medium" style={{ color: renderTheme.body }}>{resume.headline}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">{resume.email} • {resume.phone} • {resume.location}</p>
          </header>

          <div className="mt-2 grid grid-cols-2 gap-3">
            <div>
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Summary</h4>
              <p className="mt-1 text-xs leading-tight line-clamp-2" style={{ color: renderTheme.body }}>{resume.summary}</p>
            </div>
            <div>
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Skills</h4>
              <p className="mt-1 text-xs line-clamp-2" style={{ color: renderTheme.body }}>{resume.skills}</p>
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
        <header className="border-b-2 pb-3" style={{ borderColor: renderTheme.accent }}>
          <h3 className={`font-display ${visualSystem.titleSize} font-bold tracking-tight`} style={{ color: renderTheme.heading }}>{resume.name}</h3>
          <p className="mt-1 text-sm font-medium" style={{ color: renderTheme.body }}>{resume.headline}</p>
          <p className="mt-2 text-xs text-muted-foreground">{resume.email} • {resume.phone} • {resume.location}</p>
        </header>

        <section className={visualSystem.contentGap}>
          <h4 className={`${visualSystem.sectionLabelSize} font-bold uppercase ${visualSystem.sectionTrack} text-muted-foreground opacity-70`}>Professional Summary</h4>
          <p className="mt-2 text-sm leading-relaxed" style={{ color: renderTheme.body }}>{resume.summary}</p>
        </section>

        <section className={visualSystem.contentGap}>
          <h4 className={`${visualSystem.sectionLabelSize} font-bold uppercase ${visualSystem.sectionTrack} text-muted-foreground opacity-70`}>Professional Experience</h4>
          <div className="mt-2 space-y-4">
            {resume.experience.map((exp) => (
              <div key={`${exp.title}-${exp.company}`} className="border-l-2 pl-3" style={{ borderColor: renderTheme.accentBorder }}>
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start">
                  <div>
                    <p className="text-sm font-bold" style={{ color: renderTheme.heading }}>{exp.title}</p>
                    <p className="text-xs font-medium text-muted-foreground">{exp.company}</p>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 sm:mt-0">{exp.period}</p>
                </div>
                <ul className="mt-1.5 space-y-1 list-disc pl-4 marker:text-xs">
                  {exp.bullets.map((b, i) => (
                    <li key={i} className="text-sm" style={{ color: renderTheme.body }}>{b}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <div className="grid grid-cols-2 gap-4">
          <section>
            <h4 className={`${visualSystem.sectionLabelSize} font-bold uppercase ${visualSystem.sectionTrack} text-muted-foreground opacity-70`}>Skills</h4>
            <p className="mt-2 text-sm" style={{ color: renderTheme.body }}>{resume.skills}</p>
          </section>
          <section>
            <h4 className={`${visualSystem.sectionLabelSize} font-bold uppercase ${visualSystem.sectionTrack} text-muted-foreground opacity-70`}>Education</h4>
            <p className="mt-2 text-sm" style={{ color: renderTheme.body }}>{resume.education}</p>
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

  const applyPreset = (presetId) => {
    const preset = NEWCOMER_PRESETS[presetId];
    if (!preset) return;
    setActivePreset(presetId);
    setResume(preset.resume);
  };

  return (
    <div className="mx-auto max-w-6xl space-y-5" data-testid="resume-studio-page">
      <section className="relative overflow-hidden rounded-3xl border border-border bg-card">
        <div className="pointer-events-none absolute -left-12 -top-16 h-44 w-44 rounded-full bg-white/15 blur-2xl" />
        <div className="pointer-events-none absolute right-0 top-10 h-32 w-32 rounded-full bg-cyan-300/20 blur-2xl" />
        <div className="bg-gradient-to-br from-brand-800 via-brand-700 to-maple px-6 py-7 text-white sm:px-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/15 px-3 py-1 text-xs font-semibold backdrop-blur-sm">
                <Sparkles className="h-3.5 w-3.5" /> Maple Resume Studio
              </p>
              <h1 className="mt-3 font-display text-2xl font-bold sm:text-3xl">Professional resume builder for Canada</h1>
              <p className="mt-2 max-w-2xl text-sm text-white/90">
                Choose from 10 beautifully formatted templates, customize every detail in real-time, and use Maple AI to strengthen your impact. Built specifically for Canadian hiring standards and ATS compatibility.
              </p>
            </div>
            <div className="min-w-[220px] rounded-2xl border border-white/25 bg-white/10 p-4 shadow-lg backdrop-blur-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-white/80">ATS Readiness Score</p>
              <p className="mt-2 text-3xl font-bold">{completeness}%</p>
              <p className="text-xs text-white/80">Aim for 85%+ before applying.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.05fr,0.95fr]">
        <div className="space-y-5">
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
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

            <div className="mb-4 rounded-xl border border-border bg-background p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Starter profile</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {Object.values(NEWCOMER_PRESETS).map((preset) => {
                  const active = preset.id === activePreset;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => applyPreset(preset.id)}
                      className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
                        active
                          ? "bg-brand-600 text-white"
                          : "bg-secondary text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {preset.label}
                    </button>
                  );
                })}
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
                                ? "border-brand-500 bg-brand-50 shadow-md ring-2 ring-brand-200/60 dark:bg-brand-500/10"
                                : "border-border bg-background hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-md"
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
                            <div className="mt-2 h-1.5 w-full rounded-full bg-secondary">
                              <div className={`h-full rounded-full ${t.accent}`} style={{ width: active ? "72%" : "42%" }} />
                            </div>
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
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="font-display text-lg font-semibold">{selectedTemplate.name} Preview</h2>
                <p className="mt-0.5 text-xs text-muted-foreground">{selectedTemplate.category}</p>
              </div>
              <span
                className="rounded-full px-2.5 py-1 text-xs font-semibold"
                style={{
                  backgroundColor: renderTheme.accentSoft,
                  border: `1px solid ${renderTheme.accentBorder}`,
                  color: renderTheme.muted,
                }}
              >
                {selectedTemplate.vibe} • {smartTheme.name}
              </span>
            </div>

            <div className="mb-3 flex items-center justify-between rounded-xl border border-border bg-background px-3 py-2">
              <p className="text-xs font-medium text-muted-foreground">PDF color mode</p>
              <button
                type="button"
                onClick={() => setPrintSafe((v) => !v)}
                className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                  printSafe
                    ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300"
                    : "bg-secondary text-muted-foreground"
                }`}
              >
                {printSafe ? "Print-safe ON" : "Print-safe OFF"}
              </button>
            </div>

            <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900/30 dark:to-slate-800/30">
              <div className="max-h-[620px] overflow-y-auto p-6">
                <div className="mx-auto w-full max-w-[790px] rounded-[28px] border border-slate-200 bg-white p-4 shadow-[0_24px_70px_-30px_rgba(2,6,23,0.45)] dark:border-slate-700 dark:bg-slate-950/40">
                  {renderTemplatePreview()}
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <h3 className="font-display text-lg font-semibold mb-1">Maple power tools</h3>
            <p className="text-xs text-muted-foreground mb-4">Enhance and export your resume</p>
            
            {/* Download Button - Prominent */}
            <div className="mb-4 rounded-2xl bg-gradient-to-r from-brand-50 to-brand-100/50 dark:from-brand-500/10 dark:to-brand-600/10 border-2 border-brand-200 dark:border-brand-500/30 p-4">
              <div className="space-y-3">
                <button
                  type="button"
                  onClick={() => setShowEmptyTemplate(true)}
                  className="w-full flex items-center justify-between rounded-xl bg-gradient-to-r from-cyan-600 to-cyan-700 hover:from-cyan-700 hover:to-cyan-800 text-white px-4 py-3.5 text-sm font-semibold transition-all shadow-lg hover:shadow-xl active:scale-95"
                >
                  <span className="inline-flex items-center gap-2">
                    <LayoutTemplate className="h-5 w-5" />
                    <span>Preview Empty Template</span>
                  </span>
                  <ArrowRight className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewMode("fullscreen")}
                  className="w-full flex items-center justify-between rounded-xl bg-gradient-to-r from-brand-600 to-brand-700 hover:from-brand-700 hover:to-brand-800 text-white px-4 py-3.5 text-sm font-semibold transition-all shadow-lg hover:shadow-xl active:scale-95"
                >
                  <span className="inline-flex items-center gap-2">
                    <LayoutTemplate className="h-5 w-5" />
                    <span>Open Full Preview</span>
                  </span>
                  <ArrowRight className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setShowQualityPreview(true)}
                  className="w-full flex items-center justify-between rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 text-white px-4 py-3.5 text-sm font-semibold transition-all shadow-lg hover:shadow-xl active:scale-95"
                >
                  <span className="inline-flex items-center gap-2">
                    <Download className="h-5 w-5" />
                    <span>Download as PDF</span>
                  </span>
                  <span className="text-xs bg-white/20 rounded-full px-2.5 py-1">Ctrl+P</span>
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-3 text-center">Review spacing, alignment, and hierarchy before export</p>
            </div>

            {/* Other Tools */}
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => askMapleToEnhance("resume", toMarkdown(resume))}
                className="flex w-full items-center justify-between rounded-xl border border-border bg-background px-3 py-2.5 text-left text-sm hover:bg-secondary/50 transition-colors"
              >
                <span className="inline-flex items-center gap-2"><Sparkles className="h-4 w-4 text-brand-600" /> Rewrite for Canadian Recruiters</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </button>
              <button
                type="button"
                onClick={() => askMapleToEnhance("experience bullets", resume.experience.flatMap((e) => e.bullets).join(" | "))}
                className="flex w-full items-center justify-between rounded-xl border border-border bg-background px-3 py-2.5 text-left text-sm hover:bg-secondary/50 transition-colors"
              >
                <span className="inline-flex items-center gap-2"><BadgeCheck className="h-4 w-4 text-brand-600" /> Strengthen Impact Metrics</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </button>
              <button
                type="button"
                onClick={copyMarkdown}
                className="flex w-full items-center justify-between rounded-xl border border-border bg-background px-3 py-2.5 text-left text-sm hover:bg-secondary/50 transition-colors"
              >
                <span className="inline-flex items-center gap-2">
                  {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4 text-brand-600" />} 
                  {copied ? "Markdown Copied" : "Copy as Markdown"}
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
              onClick={() => setPreviewMode("fullscreen")}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background hover:bg-secondary px-3 py-2 text-xs font-medium transition-colors"
            >
              <LayoutTemplate className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Preview</span>
            </button>
            <button
              type="button"
              onClick={() => setShowQualityPreview(true)}
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

      {/* Fullscreen Preview Modal */}
      {previewMode === "fullscreen" && (
        <div className="fixed inset-0 z-50 flex flex-col bg-background">
          {/* Header */}
          <div className="border-b border-border bg-card px-4 sm:px-6 py-4 flex items-center justify-between">
            <div className="flex-1">
              <h2 className="text-lg font-semibold">Full Page Preview</h2>
              <p className="text-xs text-muted-foreground mt-1">This is exactly how your resume will print to PDF</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setShowQualityPreview(true)}
                className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-brand-600 to-brand-700 hover:from-brand-700 hover:to-brand-800 text-white px-4 py-2 text-sm font-semibold transition-all"
              >
                <Download className="h-4 w-4" />
                Download PDF
              </button>
              <button
                type="button"
                onClick={() => setPreviewMode("normal")}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-background hover:bg-secondary px-4 py-2 text-sm font-medium transition-colors"
              >
                <span>Close</span>
              </button>
            </div>
          </div>

          {/* Content - A4/Letter Size Preview */}
          <div className="flex-1 overflow-auto bg-muted/20 p-4 sm:p-8 flex items-center justify-center">
            <div 
              className="bg-white text-black shadow-2xl"
              style={{
                width: "8.5in",
                height: "11in",
                overflow: "hidden",
              }}

              {/* Quality Check Modal */}
              {showQualityPreview && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                  <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl">
                    <h3 className="font-display text-xl font-semibold">Ready to Download</h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Quick check before export: your template and spacing look polished. Continue to print/download PDF.
                    </p>
                    <div className="mt-4 rounded-xl border border-border bg-background p-3 text-xs text-muted-foreground">
                      Template: <span className="font-semibold text-foreground">{selectedTemplate.name}</span> • Theme: <span className="font-semibold text-foreground">{smartTheme.name}</span>
                    </div>
                    <div className="mt-5 flex items-center justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => setShowQualityPreview(false)}
                        className="rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium hover:bg-secondary"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setShowQualityPreview(false);
                          window.print();
                        }}
                        className="rounded-lg bg-gradient-to-r from-brand-600 to-brand-700 px-4 py-2 text-sm font-semibold text-white hover:from-brand-700 hover:to-brand-800"
                      >
                        Continue to Download
                      </button>
                    </div>
                  </div>
                </div>
              )}
            >
              {/* A4/Letter page with print styles */}
              <div className="p-6" style={{ fontSize: "11pt", lineHeight: "1.4" }}>
                {renderTemplatePreview()}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-border bg-card px-4 sm:px-6 py-3 text-center text-xs text-muted-foreground">
            <p>Tip: Use Cmd+P (Mac) or Ctrl+P (Windows) in the preview to save directly as PDF</p>
          </div>
        </div>
      )}

      {/* Quality Preview Modal */}
      <QualityPreviewModal
        isOpen={showQualityPreview}
        onClose={() => setShowQualityPreview(false)}
        onDownload={() => {
          setShowQualityPreview(false);
          window.print();
        }}
        resume={resume}
        templateName={selectedTemplate.name}
        completeness={completeness}
      />

      {/* Empty Template Preview Modal */}
      {showEmptyTemplate && (
        <div className="fixed inset-0 z-50 flex flex-col bg-background">
          {/* Header */}
          <div className="border-b border-border bg-card px-4 sm:px-6 py-4 flex items-center justify-between">
            <div className="flex-1">
              <h2 className="text-lg font-semibold">{selectedTemplate.name} Template Structure</h2>
              <p className="text-xs text-muted-foreground mt-1">See how this template is organized before adding your content</p>
            </div>
            <button
              type="button"
              onClick={() => setShowEmptyTemplate(false)}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-background hover:bg-secondary px-4 py-2 text-sm font-medium transition-colors"
            >
              <span>Close</span>
            </button>
          </div>

          {/* Content - A4/Letter Size Preview */}
          <div className="flex-1 overflow-auto bg-muted/20 p-4 sm:p-8 flex items-center justify-center">
            <div 
              className="bg-white text-black shadow-2xl"
              style={{
                width: "8.5in",
                height: "11in",
                overflow: "hidden",
              }}
            >
              {/* A4/Letter page - Empty template structure */}
              <div className="p-6 space-y-4" style={{ fontSize: "11pt", lineHeight: "1.5", color: "#666" }}>
                {/* Header Section */}
                <div className="border-b-2" style={{ borderColor: renderTheme.accent, paddingBottom: "12px" }}>
                  <div style={{ fontSize: "18pt", fontWeight: "bold", color: renderTheme.heading }}>Your Name Here</div>
                  <div style={{ fontSize: "10pt", marginTop: "4px", color: renderTheme.body }}>Professional headline or target role</div>
                  <div style={{ fontSize: "9pt", marginTop: "4px", color: renderTheme.muted }}>Email • Phone • Location</div>
                </div>

                {/* Summary Section */}
                {selectedTemplate.layout !== "compact" && (
                  <div>
                    <div style={{ fontSize: "9pt", fontWeight: "bold", letterSpacing: "0.08em", color: "#888", marginBottom: "6px" }}>PROFESSIONAL SUMMARY</div>
                    <div style={{ fontSize: "10pt", color: renderTheme.body, lineHeight: "1.4" }}>
                      Your professional summary or objective goes here. Highlight key strengths, years of experience, and career goals relevant to the role.
                    </div>
                  </div>
                )}

                {/* Experience Section */}
                <div>
                  <div style={{ fontSize: "9pt", fontWeight: "bold", letterSpacing: "0.08em", color: "#888", marginBottom: "6px" }}>PROFESSIONAL EXPERIENCE</div>
                  <div style={{ marginBottom: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
                      <div style={{ fontWeight: "bold", color: renderTheme.heading }}>Job Title</div>
                      <div style={{ fontSize: "9pt", color: "#999" }}>2024 - Present</div>
                    </div>
                    <div style={{ fontSize: "9pt", color: "#999", marginBottom: "4px" }}>Company Name</div>
                    <ul style={{ fontSize: "10pt", color: renderTheme.body, marginLeft: "16px", listStyleType: "disc" }}>
                      <li>Achievement or responsibility with impact metrics</li>
                      <li>Key contribution to team or project success</li>
                    </ul>
                  </div>
                </div>

                {/* Footer Sections */}
                <div style={{ display: "grid", gridTemplateColumns: selectedTemplate.layout === "two-column" ? "1fr" : "1fr 1fr", gap: "16px", marginTop: "12px" }}>
                  <div>
                    <div style={{ fontSize: "9pt", fontWeight: "bold", letterSpacing: "0.08em", color: "#888", marginBottom: "6px" }}>SKILLS</div>
                    <div style={{ fontSize: "10pt", color: renderTheme.body }}>Skill 1 • Skill 2 • Skill 3 • Skill 4</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "9pt", fontWeight: "bold", letterSpacing: "0.08em", color: "#888", marginBottom: "6px" }}>EDUCATION</div>
                    <div style={{ fontSize: "10pt", color: renderTheme.body }}>Degree, Institution, Year</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-border bg-card px-4 sm:px-6 py-3 text-center text-xs text-muted-foreground">
            <p>This is the structural layout. Your content will fill these sections.</p>
          </div>
        </div>
      )}
    </div>
  );
}
