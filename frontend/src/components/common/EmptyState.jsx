import { Button } from "@/components/ui/button";

/**
 * Empty state — always a guide forward, never a dead end.
 * Provide an actionable CTA where possible.
 */
export function EmptyState({ icon: Icon, title, description, actionLabel, onAction, testId }) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card px-6 py-14 text-center"
      data-testid={testId || "empty-state"}
    >
      {Icon && (
        <div className="grid h-14 w-14 place-items-center rounded-2xl bg-brand-500/10 text-brand-600 dark:text-brand-400">
          <Icon className="h-7 w-7" />
        </div>
      )}
      <h3 className="mt-5 font-display text-lg font-semibold">{title}</h3>
      {description && <p className="mt-2 max-w-sm text-sm text-muted-foreground">{description}</p>}
      {actionLabel && onAction && (
        <Button onClick={onAction} className="mt-6 rounded-full" data-testid="empty-state-action">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

export default EmptyState;
