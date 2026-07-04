/**
 * Route-level loading fallback for lazy-loaded pages.
 * Flat skeleton fills only — no shimmer (respects the motion budget).
 */
export function PageLoader() {
  return (
    <div className="mx-auto max-w-3xl space-y-4 p-2" data-testid="page-loader" aria-busy="true">
      <div className="h-28 rounded-3xl bg-secondary" />
      <div className="grid grid-cols-3 gap-3">
        <div className="h-20 rounded-2xl bg-secondary" />
        <div className="h-20 rounded-2xl bg-secondary" />
        <div className="h-20 rounded-2xl bg-secondary" />
      </div>
      <div className="h-24 rounded-2xl bg-secondary" />
      <div className="h-24 rounded-2xl bg-secondary" />
    </div>
  );
}

export default PageLoader;
