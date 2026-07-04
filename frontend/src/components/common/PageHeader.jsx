import { motion } from "framer-motion";

/**
 * Consistent page header for app + admin views.
 * One optional primary action, per the design system.
 */
export function PageHeader({ title, subtitle, icon: Icon, action, testId }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22 }}
      className="mb-6 flex flex-wrap items-start justify-between gap-4"
      data-testid={testId || "page-header"}
    >
      <div className="flex items-start gap-3">
        {Icon && (
          <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400">
            <Icon className="h-5 w-5" />
          </div>
        )}
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
        </div>
      </div>
      {action}
    </motion.div>
  );
}

export default PageHeader;
