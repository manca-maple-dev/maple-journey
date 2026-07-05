import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText, Sparkles, Download, Plus, Trash2, Edit2, Check, X, Loader2,
  ChevronDown, ChevronUp, Lock, AlertCircle, Info
} from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";

const DRAFT_KEY = "mj_resume_v1";
const TEMPLATES = [
  {
    id: "classic",
    name: "Classic",
    desc: "Traditional single-column. Most ATS-friendly.",
    icon: "📄",
  },
  {
    id: "modern",
    name: "Modern",
    desc: "Contemporary sidebar layout with skills focus.",
    icon: "✨",
  },
  {
    id: "compact",
    name: "Compact",
    desc: "Dense single-page for experienced pros.",
    icon: "⚡",
  },
];

/* ============ Resume Questionnaire (Step 1) ============ */
function ResumeMakerQuestions({ onGenerate, loading }) {
  const [answers, setAnswers] = useState({
    target_role: "",
    years_experience: "",
    key_achievements: [""],
    key_skills: [""],
    additional_info: "",
  });

  const handleAchievementChange = (idx, val) => {
    setAnswers((s) => ({
      ...s,
      key_achievements: s.key_achievements.map((a, i) => (i === idx ? val : a)),
    }));
  };

  const handleSkillChange = (idx, val) => {
    setAnswers((s) => ({
      ...s,
      key_skills: s.key_skills.map((sk, i) => (i === idx ? val : sk)),
    }));
  };

  const addAchievement = () => {
    setAnswers((s) => ({
      ...s,
      key_achievements: [...s.key_achievements, ""],
    }));
  };

  const addSkill = () => {
    setAnswers((s) => ({
      ...s,
      key_skills: [...s.key_skills, ""],
    }));
  };

  const removeAchievement = (idx) => {
    setAnswers((s) => ({
      ...s,
      key_achievements: s.key_achievements.filter((_, i) => i !== idx),
    }));
  };

  const removeSkill = (idx) => {
    setAnswers((s) => ({
      ...s,
      key_skills: s.key_skills.filter((_, i) => i !== idx),
    }));
  };

  const handleGenerate = async () => {
    if (!answers.target_role || !answers.years_experience) {
      toast.error("Please fill in target role and years of experience");
      return;
    }

    const filtered = {
      ...answers,
      key_achievements: answers.key_achievements.filter((a) => a.trim()),
      key_skills: answers.key_skills.filter((s) => s.trim()),
    };

    onGenerate(filtered);
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="mb-4 flex items-start gap-3">
          <Sparkles className="mt-0.5 h-5 w-5 text-brand-600" />
          <div>
            <h3 className="font-display font-semibold">Build Your Resume</h3>
            <p className="text-xs text-muted-foreground">
              We'll use your profile + these details to create a professional resume.
            </p>
          </div>
        </div>

        {/* Target Role */}
        <div className="mb-4 space-y-1.5">
          <Label>Target role (where do you want to work?)</Label>
          <Input
            value={answers.target_role}
            onChange={(e) => setAnswers((s) => ({ ...s, target_role: e.target.value }))}
            placeholder="e.g., Software Engineer, Nurse, Electrician"
            className="text-sm"
          />
        </div>

        {/* Years Experience */}
        <div className="mb-4 space-y-1.5">
          <Label>Years of professional experience</Label>
          <Input
            type="number"
            value={answers.years_experience}
            onChange={(e) => setAnswers((s) => ({ ...s, years_experience: e.target.value }))}
            placeholder="0"
            min="0"
            className="text-sm"
          />
        </div>

        {/* Key Achievements */}
        <div className="mb-4 space-y-2">
          <div className="flex items-center justify-between">
            <Label>Key achievements (highlight these)</Label>
            <Button
              size="sm"
              variant="ghost"
              onClick={addAchievement}
              className="h-auto p-1 text-brand-600 hover:bg-brand-500/10"
            >
              <Plus className="h-3.5 w-3.5" /> Add
            </Button>
          </div>
          <div className="space-y-2">
            {answers.key_achievements.map((ach, idx) => (
              <div key={idx} className="flex gap-2">
                <Input
                  value={ach}
                  onChange={(e) => handleAchievementChange(idx, e.target.value)}
                  placeholder="e.g., Led team of 5, delivered project on time and under budget"
                  className="text-xs"
                />
                {answers.key_achievements.length > 1 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => removeAchievement(idx)}
                    className="h-auto p-1 text-destructive hover:bg-destructive/10"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Key Skills */}
        <div className="mb-4 space-y-2">
          <div className="flex items-center justify-between">
            <Label>Key skills</Label>
            <Button
              size="sm"
              variant="ghost"
              onClick={addSkill}
              className="h-auto p-1 text-brand-600 hover:bg-brand-500/10"
            >
              <Plus className="h-3.5 w-3.5" /> Add
            </Button>
          </div>
          <div className="space-y-2">
            {answers.key_skills.map((skill, idx) => (
              <div key={idx} className="flex gap-2">
                <Input
                  value={skill}
                  onChange={(e) => handleSkillChange(idx, e.target.value)}
                  placeholder="e.g., Project Management, Python, Nursing"
                  className="text-xs"
                />
                {answers.key_skills.length > 1 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => removeSkill(idx)}
                    className="h-auto p-1 text-destructive hover:bg-destructive/10"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Additional Info */}
        <div className="mb-6 space-y-1.5">
          <Label>Anything else to highlight?</Label>
          <Textarea
            value={answers.additional_info}
            onChange={(e) => setAnswers((s) => ({ ...s, additional_info: e.target.value }))}
            placeholder="e.g., Recently completed Canadian credential assessment, open to relocation"
            className="text-sm"
            rows={3}
          />
        </div>

        <Button
          onClick={handleGenerate}
          disabled={loading || !answers.target_role}
          className="w-full"
        >
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Generate Resume
        </Button>
      </div>
    </div>
  );
}

/* ============ Template Picker ============ */
function TemplatePicker({ selected, onSelect, disabled }) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {TEMPLATES.map((tmpl) => (
        <button
          key={tmpl.id}
          onClick={() => onSelect(tmpl.id)}
          disabled={disabled}
          className={`rounded-xl border-2 p-3 text-left transition-all ${
            selected === tmpl.id
              ? "border-brand-600 bg-brand-50 dark:bg-brand-950"
              : "border-border hover:border-brand-300"
          } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          <div className="text-2xl mb-1">{tmpl.icon}</div>
          <div className="font-semibold text-sm">{tmpl.name}</div>
          <div className="text-xs text-muted-foreground mt-1">{tmpl.desc}</div>
        </button>
      ))}
    </div>
  );
}

/* ============ Experience Editor ============ */
function ExperienceSection({ experience, onChange, onAdd, onRemove }) {
  const [expanded, setExpanded] = useState({});

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-sm">Experience</h4>
        <Button
          size="sm"
          variant="ghost"
          onClick={onAdd}
          className="h-auto p-1 text-brand-600 hover:bg-brand-500/10"
        >
          <Plus className="h-3.5 w-3.5" /> Add
        </Button>
      </div>

      {experience.length === 0 ? (
        <div className="text-xs text-muted-foreground rounded-lg bg-secondary/50 p-3">
          No experience added. Click the + button above to add one.
        </div>
      ) : (
        experience.map((exp, idx) => (
          <div key={idx} className="rounded-lg border border-border bg-card p-3">
            <div
              className="flex items-start justify-between gap-2 cursor-pointer"
              onClick={() =>
                setExpanded((s) => ({ ...s, [idx]: !s[idx] }))
              }
            >
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-sm truncate">{exp.title || "[Job title]"}</div>
                <div className="text-xs text-muted-foreground truncate">
                  {exp.employer || "[Company]"} • {exp.location || "[Location]"}
                </div>
              </div>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemove(idx);
                  }}
                  className="h-auto p-1 text-destructive hover:bg-destructive/10"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
                {expanded[idx] ? (
                  <ChevronUp className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            </div>

            {expanded[idx] && (
              <div className="mt-3 space-y-2 border-t border-border pt-3">
                <div>
                  <Label className="text-xs">Title</Label>
                  <Input
                    value={exp.title}
                    onChange={(e) =>
                      onChange(idx, { ...exp, title: e.target.value })
                    }
                    className="text-xs mt-1"
                  />
                </div>
                <div>
                  <Label className="text-xs">Employer</Label>
                  <Input
                    value={exp.employer}
                    onChange={(e) =>
                      onChange(idx, { ...exp, employer: e.target.value })
                    }
                    className="text-xs mt-1"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs">Start (YYYY-MM)</Label>
                    <Input
                      value={exp.start_date}
                      onChange={(e) =>
                        onChange(idx, { ...exp, start_date: e.target.value })
                      }
                      placeholder="2020-01"
                      className="text-xs mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">End (YYYY-MM)</Label>
                    <Input
                      value={exp.end_date || ""}
                      onChange={(e) =>
                        onChange(idx, { ...exp, end_date: e.target.value || null })
                      }
                      placeholder="Leave blank if current"
                      className="text-xs mt-1"
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-xs">Location</Label>
                  <Input
                    value={exp.location}
                    onChange={(e) =>
                      onChange(idx, { ...exp, location: e.target.value })
                    }
                    className="text-xs mt-1"
                  />
                </div>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}

/* ============ Main Resume Maker Component ============ */
export default function ResumeMaker() {
  const { user } = useAuth();
  const profile = user?.profile || {};
  const [step, setStep] = useState("questions"); // questions | edit | success
  const [draft, setDraft] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [template, setTemplate] = useState("classic");
  const [quota, setQuota] = useState(null);

  useEffect(() => {
    // Fetch quota on mount
    (async () => {
      try {
        const { data } = await api.get("/resume/quota");
        setQuota(data);
      } catch (e) {
        console.error("Failed to fetch quota:", e);
      }
    })();
  }, []);

  const handleGenerate = async (answers) => {
    setLoading(true);
    try {
      const { data } = await api.post("/resume/generate", answers);
      setDraft(data.draft);
      setStep("edit");
      toast.success("Resume generated!");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!draft) return;
    setLoading(true);
    try {
      await api.put("/resume", { data: draft });
      toast.success("Resume saved!");
      setStep("success");
    } catch (e) {
      toast.error("Failed to save resume");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!draft) return;
    setExporting(true);
    try {
      const response = await api.get(`/resume/pdf?template=${template}`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${draft.full_name}_Resume.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      toast.success("Resume downloaded!");
    } catch (e) {
      toast.error("Export failed");
    } finally {
      setExporting(false);
    }
  };

  const canGenerate = quota && quota.remaining > 0;
  const isFree = quota && quota.tier === "free";

  return (
    <div className="space-y-6">
      {/* Quota Info */}
      {quota && (
        <div className={`rounded-2xl border-2 p-4 ${isFree ? "border-maple bg-maple-50 dark:bg-maple-950" : "border-brand-500 bg-brand-50 dark:bg-brand-950"}`}>
          <div className="flex items-start gap-3">
            {isFree ? <Lock className="h-5 w-5 text-maple mt-0.5" /> : <Info className="h-5 w-5 text-brand-600 mt-0.5" />}
            <div>
              <div className="font-semibold text-sm">
                {quota.remaining !== null
                  ? `${quota.remaining} resume${quota.remaining !== 1 ? "s" : ""} remaining this month`
                  : "Unlimited resume generations"}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {isFree
                  ? "Exports include a small watermark. Upgrade to Plus for clean exports."
                  : "All exports are clean. No watermarks."}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Step: Questions */}
      <AnimatePresence mode="wait">
        {step === "questions" && (
          <motion.div
            key="questions"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            <ResumeMakerQuestions
              onGenerate={handleGenerate}
              loading={loading}
            />
          </motion.div>
        )}

        {/* Step: Edit */}
        {step === "edit" && draft && (
          <motion.div
            key="edit"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="space-y-6"
          >
            {/* Resume Preview Section */}
            <div className="rounded-2xl border border-border bg-card p-6">
              <h3 className="font-display font-semibold mb-4 flex items-center gap-2">
                <Edit2 className="h-5 w-5 text-brand-600" />
                Review & Edit
              </h3>

              {/* Name & Contact */}
              <div className="space-y-3 mb-6 pb-6 border-b border-border">
                <div>
                  <Label className="text-xs">Full name</Label>
                  <Input
                    value={draft.full_name}
                    onChange={(e) =>
                      setDraft((s) => ({ ...s, full_name: e.target.value }))
                    }
                    className="text-sm mt-1"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs">Email</Label>
                    <Input
                      value={draft.email}
                      onChange={(e) =>
                        setDraft((s) => ({ ...s, email: e.target.value }))
                      }
                      className="text-sm mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Phone</Label>
                    <Input
                      value={draft.phone}
                      onChange={(e) =>
                        setDraft((s) => ({ ...s, phone: e.target.value }))
                      }
                      className="text-sm mt-1"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs">City</Label>
                    <Input
                      value={draft.city}
                      onChange={(e) =>
                        setDraft((s) => ({ ...s, city: e.target.value }))
                      }
                      className="text-sm mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Province</Label>
                    <Input
                      value={draft.province}
                      onChange={(e) =>
                        setDraft((s) => ({ ...s, province: e.target.value }))
                      }
                      className="text-sm mt-1"
                    />
                  </div>
                </div>
              </div>

              {/* Summary */}
              <div className="mb-6 pb-6 border-b border-border">
                <Label className="text-xs">Professional summary</Label>
                <Textarea
                  value={draft.summary}
                  onChange={(e) =>
                    setDraft((s) => ({ ...s, summary: e.target.value }))
                  }
                  className="text-sm mt-2"
                  rows={3}
                />
              </div>

              {/* Experience */}
              <div className="mb-6 pb-6 border-b border-border">
                <ExperienceSection
                  experience={draft.experience}
                  onChange={(idx, updated) => {
                    setDraft((s) => {
                      const exp = [...s.experience];
                      exp[idx] = updated;
                      return { ...s, experience: exp };
                    });
                  }}
                  onAdd={() => {
                    setDraft((s) => ({
                      ...s,
                      experience: [
                        ...s.experience,
                        {
                          title: "",
                          employer: "",
                          location: "",
                          start_date: "",
                          end_date: null,
                          bullets: [],
                        },
                      ],
                    }));
                  }}
                  onRemove={(idx) => {
                    setDraft((s) => ({
                      ...s,
                      experience: s.experience.filter((_, i) => i !== idx),
                    }));
                  }}
                />
              </div>

              {/* Skills */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <Label className="text-xs">Skills (comma-separated)</Label>
                </div>
                <Textarea
                  value={draft.skills.join(", ")}
                  onChange={(e) =>
                    setDraft((s) => ({
                      ...s,
                      skills: e.target.value
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean),
                    }))
                  }
                  className="text-sm"
                  rows={2}
                  placeholder="Project Management, Python, Nursing, etc."
                />
              </div>
            </div>

            {/* Template Picker */}
            <div className="rounded-2xl border border-border bg-card p-6">
              <h3 className="font-display font-semibold mb-4">Choose template</h3>
              <TemplatePicker
                selected={template}
                onSelect={setTemplate}
                disabled={false}
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setStep("questions")}
                className="flex-1"
              >
                Back
              </Button>
              <Button
                onClick={handleSave}
                disabled={loading}
                className="flex-1"
              >
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Save Resume
              </Button>
              <Button
                onClick={handleExport}
                disabled={exporting}
                className="flex-1 bg-emerald-600 hover:bg-emerald-700"
              >
                {exporting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                <Download className="mr-2 h-4 w-4" />
                Download PDF
              </Button>
            </div>
          </motion.div>
        )}

        {/* Step: Success */}
        {step === "success" && (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            className="rounded-2xl border border-border bg-card p-8 text-center"
          >
            <div className="mb-4 flex justify-center">
              <div className="rounded-full bg-emerald-50 dark:bg-emerald-950 p-4">
                <Check className="h-8 w-8 text-emerald-600" />
              </div>
            </div>
            <h3 className="font-display text-lg font-semibold mb-2">Resume saved!</h3>
            <p className="text-sm text-muted-foreground mb-6">
              Your resume is ready. You can download it now or make more edits anytime.
            </p>
            <div className="flex gap-3 justify-center">
              <Button
                variant="outline"
                onClick={() => setStep("edit")}
              >
                Edit More
              </Button>
              <Button
                onClick={handleExport}
                disabled={exporting}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {exporting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                <Download className="mr-2 h-4 w-4" />
                Download PDF
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
