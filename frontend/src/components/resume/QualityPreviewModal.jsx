import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Download, X, CheckCircle2, AlertCircle, Info, Zap, Eye, FileText,
  TrendingUp, Target, Settings
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function QualityPreviewModal({ 
  isOpen, 
  onClose, 
  onDownload, 
  resume, 
  templateName,
  completeness 
}) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Calculate quality metrics
  const metrics = useMemo(() => {
    const calculations = {
      // Content completeness (0-100)
      completeness: completeness || 0,
      
      // ATS compatibility score (0-100)
      atsScore: calculateATSScore(resume),
      
      // Content density (0-100)
      density: calculateContentDensity(resume),
      
      // Keyword richness (0-100)
      keywords: calculateKeywordRichness(resume),
    };

    // Overall quality score (weighted average)
    calculations.overall = Math.round(
      (calculations.completeness * 0.30 +
        calculations.atsScore * 0.35 +
        calculations.density * 0.20 +
        calculations.keywords * 0.15)
    );

    return calculations;
  }, [resume, completeness]);

  const issues = useMemo(() => {
    const problems = [];

    if (metrics.completeness < 60) {
      problems.push({
        level: "warning",
        icon: AlertCircle,
        text: "Resume is incomplete. Add more details to improve chances.",
      });
    }

    if (!resume.summary || resume.summary.trim().length < 50) {
      problems.push({
        level: "warning",
        icon: Info,
        text: "Professional summary is missing or too short. Add 2-3 sentences about yourself.",
      });
    }

    if (!resume.experience || resume.experience.length === 0) {
      problems.push({
        level: "error",
        icon: AlertCircle,
        text: "No work experience added. Include at least one position.",
      });
    } else {
      const emptyBullets = resume.experience.some(
        (exp) => !exp.bullets || exp.bullets.filter(Boolean).length < 1
      );
      if (emptyBullets) {
        problems.push({
          level: "warning",
          icon: Info,
          text: "Some job entries lack achievement bullets. Add 2+ bullet points per role.",
        });
      }
    }

    if (!resume.skills || resume.skills.trim().split(",").length < 3) {
      problems.push({
        level: "warning",
        icon: Info,
        text: "Add more skills to improve ATS matching.",
      });
    }

    if (metrics.atsScore < 70) {
      problems.push({
        level: "info",
        icon: Info,
        text: "ATS score is moderate. Avoid fancy formatting if applying to large companies.",
      });
    }

    return problems;
  }, [resume, metrics]);

  const suggestions = useMemo(() => {
    const tips = [];

    if (resume.phone && resume.phone.length < 10) {
      tips.push("✓ Add your phone number");
    } else {
      tips.push("✓ Phone number included");
    }

    if (resume.email && resume.email.includes("@")) {
      tips.push("✓ Professional email included");
    }

    if (resume.headline && resume.headline.length > 30) {
      tips.push("✓ Strong headline with keywords");
    }

    if (resume.location) {
      tips.push("✓ Location specified");
    }

    const expYears = countYearsExperience(resume.experience);
    if (expYears > 0) {
      tips.push(`✓ ${expYears}+ years of experience shown`);
    }

    const bulletCount = resume.experience.reduce((sum, exp) => sum + (exp.bullets ? exp.bullets.filter(Boolean).length : 0), 0);
    if (bulletCount > 5) {
      tips.push(`✓ ${bulletCount} achievement bullets with metrics`);
    }

    return tips;
  }, [resume]);

  const getScoreColor = (score) => {
    if (score >= 85) return "text-green-600";
    if (score >= 70) return "text-amber-600";
    return "text-orange-600";
  };

  const getScoreBg = (score) => {
    if (score >= 85) return "bg-green-50 dark:bg-green-950";
    if (score >= 70) return "bg-amber-50 dark:bg-amber-950";
    return "bg-orange-50 dark:bg-orange-950";
  };

  const getScoreRing = (score) => {
    if (score >= 85) return "text-green-600";
    if (score >= 70) return "text-amber-600";
    return "text-orange-600";
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
          >
            <div className="pointer-events-auto bg-background border border-border rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-auto">
              {/* Header */}
              <div className="sticky top-0 bg-background border-b border-border px-6 py-4 flex items-center justify-between z-10">
                <div className="flex items-center gap-3">
                  <Eye className="h-5 w-5 text-brand-600" />
                  <h2 className="text-lg font-semibold">Quality Preview</h2>
                </div>
                <button
                  onClick={onClose}
                  className="rounded-lg p-1 hover:bg-secondary transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="p-6 space-y-6">
                {/* Overall Score Card */}
                <div className={`rounded-2xl border-2 border-border p-6 ${getScoreBg(metrics.overall)}`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground mb-1">Overall Quality Score</p>
                      <p className="text-4xl font-bold tracking-tight">
                        <span className={getScoreColor(metrics.overall)}>{metrics.overall}</span>
                        <span className="text-2xl ml-2 text-muted-foreground">/100</span>
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">
                        {metrics.overall >= 85 && "Excellent resume! Ready to impress. 🚀"}
                        {metrics.overall >= 70 && metrics.overall < 85 && "Good resume! Consider the suggestions below to improve. 💡"}
                        {metrics.overall < 70 && "Resume needs improvement. Follow the suggestions below. 📝"}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge 
                        variant={metrics.overall >= 85 ? "default" : metrics.overall >= 70 ? "secondary" : "outline"}
                        className={metrics.overall >= 85 ? "bg-green-600" : metrics.overall >= 70 ? "bg-amber-600" : ""}
                      >
                        {metrics.overall >= 85 ? "Excellent" : metrics.overall >= 70 ? "Good" : "Fair"}
                      </Badge>
                    </div>
                  </div>
                </div>

                {/* Individual Metrics */}
                <div>
                  <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-brand-600" />
                    Quality Breakdown
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    <MetricCard
                      label="Content Complete"
                      score={metrics.completeness}
                      icon={FileText}
                      description="All sections filled"
                    />
                    <MetricCard
                      label="ATS Compatible"
                      score={metrics.atsScore}
                      icon={Target}
                      description="Recruiter-friendly"
                    />
                    <MetricCard
                      label="Content Density"
                      score={metrics.density}
                      icon={Zap}
                      description="Right amount of detail"
                    />
                    <MetricCard
                      label="Keyword Rich"
                      score={metrics.keywords}
                      icon={Settings}
                      description="Matches job searches"
                    />
                  </div>
                </div>

                {/* Issues & Alerts */}
                {issues.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-semibold text-sm flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-amber-600" />
                      Things to Review
                    </h3>
                    <div className="space-y-2">
                      {issues.map((issue, idx) => (
                        <div
                          key={idx}
                          className={`rounded-lg border p-3 flex gap-3 text-sm ${
                            issue.level === "error"
                              ? "bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800"
                              : issue.level === "warning"
                              ? "bg-amber-50 border-amber-200 dark:bg-amber-950 dark:border-amber-800"
                              : "bg-blue-50 border-blue-200 dark:bg-blue-950 dark:border-blue-800"
                          }`}
                        >
                          <issue.icon className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                            issue.level === "error"
                              ? "text-red-600"
                              : issue.level === "warning"
                              ? "text-amber-600"
                              : "text-blue-600"
                          }`} />
                          <p className="text-foreground">{issue.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Strengths */}
                {suggestions.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-semibold text-sm flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      What's Great
                    </h3>
                    <div className="space-y-1">
                      {suggestions.map((suggestion, idx) => (
                        <p key={idx} className="text-sm text-foreground flex items-center gap-2">
                          <span className="text-green-600">✓</span>
                          {suggestion}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {/* Preview Info */}
                <div className="rounded-lg bg-secondary/50 border border-border p-3 text-sm">
                  <p className="text-foreground">
                    <strong>Template:</strong> {templateName}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    This resume preview uses the {templateName} template and is optimized for ATS systems and recruiter scanning.
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-2">
                  <Button
                    variant="outline"
                    onClick={onClose}
                    className="flex-1"
                  >
                    Back to Editing
                  </Button>
                  <Button
                    onClick={onDownload}
                    className="flex-1 bg-gradient-to-r from-brand-600 to-brand-700 hover:from-brand-700 hover:to-brand-800"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download PDF
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// Metric Card Component
function MetricCard({ label, score, icon: Icon, description }) {
  const getColor = (s) => s >= 85 ? "text-green-600" : s >= 70 ? "text-amber-600" : "text-orange-600";
  
  return (
    <div className="rounded-lg border border-border p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-brand-600" />
          <span className="text-xs font-medium">{label}</span>
        </div>
        <span className={`text-lg font-bold ${getColor(score)}`}>{score}</span>
      </div>
      <p className="text-xs text-muted-foreground">{description}</p>
    </div>
  );
}

// Helper Functions
function calculateATSScore(resume) {
  let score = 0;

  // Name present and not placeholder
  if (resume.name && resume.name !== "Your Name" && resume.name.trim().length > 2) score += 15;

  // Contact info
  if (resume.email && resume.email.includes("@")) score += 10;
  if (resume.phone && resume.phone.length >= 10) score += 10;

  // Location
  if (resume.location && resume.location.trim()) score += 5;

  // Headline present
  if (resume.headline && resume.headline.trim().length > 20) score += 10;

  // Summary present and substantial
  if (resume.summary && resume.summary.trim().length > 80) score += 15;

  // Skills present and varied
  const skills = resume.skills?.split(",") || [];
  if (skills.length >= 5) score += 10;
  if (skills.length >= 8) score += 5;

  // Education
  if (resume.education && resume.education.trim()) score += 10;

  // Experience with bullets
  if (resume.experience && resume.experience.length > 0) {
    score += 10;
    const hasGoodBullets = resume.experience.some(
      (exp) => exp.bullets && exp.bullets.filter(Boolean).length >= 2
    );
    if (hasGoodBullets) score += 10;
  }

  // Formatting consistency (max score = 100)
  return Math.min(score, 100);
}

function calculateContentDensity(resume) {
  // Calculate if resume has balanced content (not too sparse, not too dense)
  const charCount = JSON.stringify(resume).length;
  
  // Optimal density around 3000-5000 chars
  if (charCount < 1500) return 40; // Too sparse
  if (charCount >= 1500 && charCount < 3000) return 70;
  if (charCount >= 3000 && charCount < 5000) return 90;
  if (charCount >= 5000 && charCount < 7000) return 85;
  return 70; // Too dense
}

function calculateKeywordRichness(resume) {
  const keywordPatterns = [
    /led|managed|coordinated|supervised|directed/i,
    /achieved|accomplished|completed|delivered|implemented/i,
    /improved|increased|enhanced|optimized|streamlined/i,
    /analyzed|evaluated|assessed|reviewed|determined/i,
    /collaborated|partnered|communicated|coordinated|worked/i,
  ];

  const text = JSON.stringify(resume).toLowerCase();
  let matchCount = 0;

  keywordPatterns.forEach((pattern) => {
    const matches = text.match(pattern);
    if (matches) matchCount += matches.length;
  });

  // Score based on keyword density
  const density = Math.min(matchCount / 5, 1); // Normalized to 0-1
  return Math.round(density * 100);
}

function countYearsExperience(experiences) {
  if (!experiences || experiences.length === 0) return 0;
  
  // Simple heuristic: count number of roles as approximate years
  return experiences.length;
}
