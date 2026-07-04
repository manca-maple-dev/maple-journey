import { CheckCircle2, AlertCircle } from "lucide-react";

/**
 * Calculate profile completeness percentage
 * Based on: immigration_category, arrival_status, location, employment, health, languages
 */
export function calculateProfileCompletion(profile) {
  if (!profile) return 0;

  const requiredFields = [
    "preferred_name",
    "immigration_category",
    "arrival_status",
  ];

  const optionalFields = [
    "current_city",
    "intended_province",
    "employment_status",
    "current_occupation",
    "health_coverage_status",
    "languages_spoken",
    "date_of_birth",
    "country_of_citizenship",
  ];

  const requiredFilled = requiredFields.filter((f) => profile[f]).length;
  const requiredScore = (requiredFilled / requiredFields.length) * 60; // 60% from required

  const optionalFilled = optionalFields.filter((f) => profile[f]).length;
  const optionalScore = (optionalFilled / optionalFields.length) * 40; // 40% from optional

  return Math.round(requiredScore + optionalScore);
}

/**
 * Get completion status label
 */
function getCompletionLabel(percentage) {
  if (percentage < 25) return "Just started";
  if (percentage < 50) return "Getting there";
  if (percentage < 75) return "Almost there";
  if (percentage < 100) return "Nearly complete";
  return "Complete";
}

/**
 * Get color based on completion percentage
 */
function getCompletionColor(percentage) {
  if (percentage < 25) return "bg-red-500/20 text-red-700 dark:text-red-300";
  if (percentage < 50) return "bg-amber-500/20 text-amber-700 dark:text-amber-300";
  if (percentage < 75) return "bg-blue-500/20 text-blue-700 dark:text-blue-300";
  if (percentage < 100) return "bg-brand-500/20 text-brand-700 dark:text-brand-300";
  return "bg-green-500/20 text-green-700 dark:text-green-300";
}

/**
 * Profile Completeness Bar
 * Compact version for header or sidebar
 */
export function ProfileCompletionBar({ profile, size = "sm" }) {
  const percentage = calculateProfileCompletion(profile);

  if (size === "sm") {
    return (
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold text-muted-foreground">Profile {percentage}% complete</p>
          <span className="text-xs font-medium text-muted-foreground">{percentage}%</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full bg-gradient-to-r from-brand-500 to-maple transition-all duration-300"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  }

  // size === "lg"
  return (
    <div className={`rounded-lg p-3 ${getCompletionColor(percentage)}`}>
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0">
          {percentage === 100 ? (
            <CheckCircle2 className="h-5 w-5" />
          ) : (
            <AlertCircle className="h-5 w-5" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-semibold">{getCompletionLabel(percentage)}</p>
          <p className="text-sm opacity-90 mt-1">
            {percentage === 100
              ? "Your profile is complete. You're all set!"
              : `Your profile is ${percentage}% complete. More details help Maple give better guidance.`}
          </p>
          {percentage < 100 && (
            <a href="/app/profile" className="mt-2 inline-flex text-sm font-medium underline underline-offset-2 hover:opacity-80">
              Complete your profile →
            </a>
          )}
        </div>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-black/20">
        <div
          className="h-full bg-current transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

/**
 * Profile Completion Mini-Widget
 * For sidebar or dashboard
 */
export function ProfileCompletionWidget({ profile }) {
  const percentage = calculateProfileCompletion(profile);

  return (
    <div className="rounded-lg border border-border bg-card p-4" data-testid="profile-completion-widget">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm">Profile Completion</h3>
        <span className="text-xs font-bold text-brand-600 dark:text-brand-400">{percentage}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-secondary mb-3">
        <div
          className="h-full bg-gradient-to-r from-brand-500 to-maple transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-muted-foreground mb-3">
        {percentage === 100
          ? "✨ Your profile is complete!"
          : `Add ${100 - percentage}% more info for better recommendations`}
      </p>
      {percentage < 100 && (
        <a href="/app/profile" className="inline-flex text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline">
          Complete →
        </a>
      )}
    </div>
  );
}
