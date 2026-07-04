import { ExternalLink, Globe, Shield, FileText, BookOpen } from "lucide-react";

/**
 * Parse citations from text and extract structured data
 * Format: [Source: https://example.com, published 2026-07-01]
 */
export function extractCitations(text) {
  const citations = [];
  const citationRegex = /\[Source:\s*(.*?)\]/g;
  let match;

  while ((match = citationRegex.exec(text)) !== null) {
    const citationText = match[1];
    const urlMatch = citationText.match(/(https?:\/\/[^\s,]+)/);
    const dateMatch = citationText.match(/published\s+(\d{4}-\d{2}-\d{2})/);

    if (urlMatch) {
      citations.push({
        url: urlMatch[1],
        date: dateMatch ? dateMatch[1] : null,
        fullText: match[0], // Include full match for removal
      });
    }
  }

  return citations;
}

/**
 * Remove citation tags from text for cleaner display
 */
export function removeCitationTags(text) {
  return text.replace(/\[Source:\s*.*?\]/g, "").trim();
}

/**
 * Get authority label and icon based on domain
 */
function getAuthorityInfo(url) {
  const domain = new URL(url).hostname.toLowerCase();

  if (domain.includes("canada.ca") || domain.includes("service.gc.ca")) {
    return { label: "Government of Canada", icon: Shield, color: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300" };
  }
  if (domain.includes("ontario.ca") || domain.includes("gov.on.ca")) {
    return { label: "Province of Ontario", icon: Shield, color: "bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300" };
  }
  if (domain.includes("laws-lois.justice.gc.ca")) {
    return { label: "Canadian Law Database", icon: BookOpen, color: "bg-purple-50 text-purple-700 dark:bg-purple-500/10 dark:text-purple-300" };
  }
  if (domain.includes("ircc.canada.ca")) {
    return { label: "IRCC (Immigration)", icon: Globe, color: "bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300" };
  }
  if (domain.includes("college-ic.ca")) {
    return { label: "College of Immigration Consultants", icon: FileText, color: "bg-green-50 text-green-700 dark:bg-green-500/10 dark:text-green-300" };
  }
  if (domain.includes(".gc.ca")) {
    return { label: "Government of Canada", icon: Shield, color: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300" };
  }
  if (domain.includes("legalaid")) {
    return { label: "Legal Aid", icon: FileText, color: "bg-green-50 text-green-700 dark:bg-green-500/10 dark:text-green-300" };
  }
  return { label: "Official Source", icon: Globe, color: "bg-secondary text-muted-foreground dark:bg-secondary dark:text-secondary-foreground" };
}

/**
 * Format date for display (e.g., "Jul 1, 2026")
 */
function formatDate(dateStr) {
  if (!dateStr) return null;
  const date = new Date(dateStr + "T00:00:00Z");
  return date.toLocaleDateString("en-CA", { year: "numeric", month: "short", day: "numeric" });
}

/**
 * Citation Card Component
 * Displays a single citation with authority label, date, and clickable link
 */
export function CitationCard({ url, date, compact = false }) {
  const { label, icon: Icon, color } = getAuthorityInfo(url);
  const displayUrl = new URL(url).hostname;
  const formattedDate = formatDate(date);

  if (compact) {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-1.5 text-xs transition-colors hover:border-brand-500 hover:bg-brand-50 dark:hover:bg-brand-500/10"
        data-testid="citation-link-compact"
      >
        <Globe className="h-3 w-3" />
        <span className="truncate font-medium text-muted-foreground">{displayUrl}</span>
        <ExternalLink className="h-3 w-3 shrink-0 text-muted-foreground" />
      </a>
    );
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={`flex items-start gap-3 rounded-lg border border-border p-3 transition-all hover:border-brand-500 hover:shadow-sm ${color}`}
      data-testid="citation-card"
    >
      <div className="mt-0.5 shrink-0">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-xs font-semibold opacity-75">{label}</p>
            <p className="truncate text-sm font-medium">{displayUrl}</p>
          </div>
          <ExternalLink className="h-3.5 w-3.5 shrink-0 opacity-50" />
        </div>
        {formattedDate && (
          <p className="mt-1 text-xs opacity-60">Published: {formattedDate}</p>
        )}
      </div>
    </a>
  );
}

/**
 * Citation Cards Container
 * Renders multiple citations in a grid
 */
export function CitationCards({ citations, compact = false }) {
  if (!citations || citations.length === 0) {
    return null;
  }

  if (compact) {
    return (
      <div className="flex flex-wrap gap-2" data-testid="citation-cards-compact">
        {citations.map((citation, i) => (
          <CitationCard key={i} url={citation.url} date={citation.date} compact={true} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-2" data-testid="citation-cards">
      <p className="text-xs font-semibold uppercase text-muted-foreground">Sources</p>
      <div className="grid gap-2 sm:grid-cols-2">
        {citations.map((citation, i) => (
          <CitationCard key={i} url={citation.url} date={citation.date} />
        ))}
      </div>
    </div>
  );
}
