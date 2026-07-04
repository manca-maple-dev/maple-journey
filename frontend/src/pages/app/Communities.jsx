import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MapPin, Loader2, X, Search, Filter, AlertTriangle, Bookmark, BookmarkCheck
} from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { PageHeader } from "@/components/common/PageHeader";
import api from "@/lib/api";

const PROVINCES = ["ON", "BC", "AB", "QC", "MB", "NS", "NB", "SK", "PE", "NL"];
const ICON_MAP = {
  Church: "⛪",
  ShoppingBasket: "🛒",
  Utensils: "🍽️",
  Home: "🏠",
  HeartPulse: "❤️",
  Baby: "👶",
  Languages: "🗣️",
  BriefcaseBusiness: "💼",
  GraduationCap: "🎓",
  Shield: "🛡️",
  Users: "👥",
  AlertTriangle: "🚨",
  Phone: "📞",
};

export default function Communities() {
  const [city, setCity] = useState("");
  const [selectedProvince, setSelectedProvince] = useState("ON");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilters, setSelectedFilters] = useState([]);
  const [bookmarkedResources, setBookmarkedResources] = useState([]);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [expandedResource, setExpandedResource] = useState(null);

  // Fetch all resources for province
  const { data: resourcesData, isLoading: resourcesLoading } = useQuery({
    queryKey: ["community-resources", selectedProvince, city],
    queryFn: async () => {
      try {
        const params = new URLSearchParams();
        params.append("province", selectedProvince || "ON");
        params.append("city", city);
        const res = await api.get(`/community/resources?${params.toString()}`);
        return res.data;
      } catch (error) {
        console.error("Error fetching resources:", error);
        return { resources: {}, province: selectedProvince };
      }
    },
    enabled: !!selectedProvince,
  });

  // Track interest mutation
  const trackInterestMutation = useMutation({
    mutationFn: async (resourceId) => {
      return api.post("/community/track-interest", {
        category: resourceId,
        action: "viewed",
      });
    },
  });

  const filters = [
    { id: "all", label: "All Resources" },
    { id: "settlement", label: "Settlement" },
    { id: "health", label: "Health" },
    { id: "language", label: "Language" },
    { id: "jobsupport", label: "Employment" },
    { id: "mentalhealth", label: "Crisis Support" },
  ];

  // Flatten and filter resources
  const allResources = useMemo(() => {
    if (!resourcesData?.resources) return [];
    
    const flat = [];
    Object.entries(resourcesData.resources).forEach(([category, items]) => {
      if (Array.isArray(items)) {
        items.forEach(item => {
          flat.push({
            ...item,
            category,
            categoryId: category,
          });
        });
      }
    });
    return flat;
  }, [resourcesData]);

  // Smart filtering and searching
  const filteredResources = useMemo(() => {
    let filtered = allResources;

    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (r) =>
          r.name?.toLowerCase().includes(q) ||
          r.description?.toLowerCase().includes(q) ||
          r.type?.toLowerCase().includes(q) ||
          r.focus_areas?.some(f => f.toLowerCase().includes(q))
      );
    }

    // Category filter
    if (selectedFilters.length > 0 && !selectedFilters.includes("all")) {
      filtered = filtered.filter((r) =>
        selectedFilters.includes(r.categoryId)
      );
    }

    // Sort: bookmarked first
    filtered.sort((a, b) => {
      const aBookmarked = bookmarkedResources.includes(a.id) ? 0 : 1;
      const bBookmarked = bookmarkedResources.includes(b.id) ? 0 : 1;
      return aBookmarked - bBookmarked;
    });

    return filtered;
  }, [allResources, searchQuery, selectedFilters, bookmarkedResources]);

  const toggleBookmark = (id, e) => {
    e?.stopPropagation();
    setBookmarkedResources((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const toggleFilter = (filterId) => {
    setSelectedFilters((prev) =>
      prev.includes(filterId)
        ? prev.filter((f) => f !== filterId)
        : [...prev, filterId]
    );
  };

  return (
    <div data-testid="communities-page" className="space-y-6">
      <PageHeader
        icon={MapPin}
        title="Communities & resources"
        subtitle="Verified providers in your area with direct contact information. Coverage expands continuously as Maple ingests more accurate local data over time."
      />

      {/* LOCATION CONTROLS */}
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex items-center gap-2 rounded-2xl border border-border bg-card p-2">
          <MapPin className="ml-2 h-4 w-4 shrink-0 text-muted-foreground" />
          <input
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Your city (e.g. Toronto, Vancouver)"
            className="flex-1 bg-transparent px-1 py-2 text-sm outline-none"
          />
        </div>
        <select
          value={selectedProvince}
          onChange={(e) => setSelectedProvince(e.target.value)}
          className="rounded-2xl border border-border bg-card px-3 py-2 text-sm outline-none"
        >
          {PROVINCES.map((prov) => (
            <option key={prov} value={prov}>
              {prov}
            </option>
          ))}
        </select>
      </div>

      {/* EMERGENCY RESOURCES - ALWAYS VISIBLE */}
      {filteredResources.some(r => r.categoryId === "mentalhealth") && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-2xl border-2 border-red-500/50 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950"
        >
          <p className="flex items-center gap-2 text-sm font-bold text-red-900 dark:text-red-100">
            <AlertTriangle className="h-4 w-4" />
            Emergency Support (24/7)
          </p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {filteredResources
              .filter(r => r.categoryId === "mentalhealth")
              .slice(0, 2)
              .map((resource) => (
                <div
                  key={resource.id}
                  className="rounded-lg border border-red-200 bg-white p-3 dark:border-red-800 dark:bg-red-900/20"
                >
                  <p className="font-semibold text-red-900 dark:text-red-100">
                    {resource.name}
                  </p>
                  <p className="mt-1 text-xs text-red-700 dark:text-red-200">
                    {resource.description}
                  </p>
                  {resource.action && (
                    <p className="mt-2 text-xs font-semibold text-red-600 dark:text-red-400">
                      {resource.action}
                    </p>
                  )}
                </div>
              ))}
          </div>
        </motion.div>
      )}

      {/* SEARCH & FILTERS */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 rounded-2xl border border-border bg-card p-2">
          <Search className="ml-2 h-4 w-4 text-muted-foreground" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search providers (e.g. YMCA, ESL, childcare)"
            className="flex-1 bg-transparent px-1 py-2 text-sm outline-none"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="mr-2 rounded-full p-1 hover:bg-secondary"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <button
          onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          className="flex items-center gap-2 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <Filter className="h-4 w-4" />
          {selectedFilters.length > 0 ? `Filtered (${selectedFilters.length})` : "Show filters"}
        </button>

        {showAdvancedFilters && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-wrap gap-2 rounded-lg border border-border bg-secondary/20 p-3"
          >
            {filters.map((filter) => (
              <button
                key={filter.id}
                onClick={() => toggleFilter(filter.id)}
                className={`rounded-full px-3 py-1.5 text-xs font-medium transition-all ${
                  selectedFilters.includes(filter.id)
                    ? "border-2 border-brand-500 bg-brand-500/20"
                    : "border border-border bg-card hover:border-brand-400"
                }`}
              >
                {filter.label}
              </button>
            ))}
          </motion.div>
        )}
      </div>

      {/* RESOURCES LIST */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <p className="text-sm font-semibold">
            👥 Real Providers in {selectedProvince}
          </p>
          {filteredResources.length > 0 && (
            <span className="text-xs text-muted-foreground">
              {filteredResources.length} found {bookmarkedResources.length > 0 && `• ${bookmarkedResources.length} saved`}
            </span>
          )}
        </div>

        {resourcesLoading ? (
          <div className="flex items-center justify-center gap-2 rounded-lg border border-border bg-card p-8">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm text-muted-foreground">Loading providers...</span>
          </div>
        ) : filteredResources.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <AnimatePresence mode="popLayout">
              {filteredResources.map((resource, i) => {
                const isBookmarked = bookmarkedResources.includes(resource.id);
                const isExpanded = expandedResource === resource.id;

                return (
                  <motion.div
                    key={resource.id}
                    layoutId={resource.id}
                    onClick={() => {
                      setExpandedResource(isExpanded ? null : resource.id);
                      trackInterestMutation.mutate(resource.id);
                    }}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -12 }}
                    transition={{ delay: i * 0.03 }}
                    className="group relative cursor-pointer rounded-2xl border border-border bg-card p-5 transition-all hover:border-brand-500 hover:shadow-md"
                  >
                    {/* BOOKMARK BUTTON */}
                    <button
                      onClick={(e) => toggleBookmark(resource.id, e)}
                      className="absolute top-3 right-3 rounded-full p-1.5 transition-colors hover:bg-secondary"
                    >
                      {isBookmarked ? (
                        <BookmarkCheck className="h-4 w-4 text-brand-600 dark:text-brand-400" />
                      ) : (
                        <Bookmark className="h-4 w-4 text-muted-foreground" />
                      )}
                    </button>

                    {/* CONTENT */}
                    <div className="pr-8">
                      <div className="flex items-start gap-3">
                        <div className="text-2xl">{ICON_MAP[resource.icon] || "📍"}</div>
                        <div className="flex-1">
                          <h3 className="font-display font-semibold">{resource.name}</h3>
                          <p className="mt-1 text-xs text-muted-foreground">{resource.type}</p>
                        </div>
                      </div>

                      <p className="mt-3 text-sm text-muted-foreground">{resource.description}</p>

                      {/* LANGUAGES */}
                      {resource.languages && resource.languages.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {resource.languages.map((lang) => (
                            <span
                              key={lang}
                              className="rounded-full bg-secondary px-2 py-0.5 text-xs text-muted-foreground"
                            >
                              {lang}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* FOCUS AREAS */}
                      {resource.focus_areas && resource.focus_areas.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {resource.focus_areas.slice(0, 3).map((focus) => (
                            <span
                              key={focus}
                              className="rounded-full bg-brand-500/10 px-2 py-0.5 text-xs text-brand-600 dark:text-brand-400"
                            >
                              {focus}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* EXPANDED DETAILS */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-4 border-t border-border pt-4"
                          >
                            <div className="space-y-2 text-xs">
                              {resource.cost && (
                                <div>
                                  <p className="font-semibold text-muted-foreground">Cost:</p>
                                  <p className="text-foreground">{resource.cost}</p>
                                </div>
                              )}
                              {resource.hours && (
                                <div>
                                  <p className="font-semibold text-muted-foreground">Hours:</p>
                                  <p className="text-foreground">{resource.hours}</p>
                                </div>
                              )}
                              {resource.action && (
                                <div className="rounded-lg bg-brand-500/10 p-2">
                                  <p className="font-semibold text-brand-600 dark:text-brand-400">
                                    {resource.action}
                                  </p>
                                </div>
                              )}
                              {resource.source && (
                                <p className="text-muted-foreground">
                                  Verified from: {resource.source}
                                </p>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        ) : (
          <div className="rounded-lg border border-border bg-card p-8 text-center">
            <p className="text-sm text-muted-foreground">
              {resourcesLoading ? "Loading..." : "No providers match your search at the moment. We are continuously adding more accurate community data."}
            </p>
          </div>
        )}
      </div>

      {/* INFO FOOTER */}
      <div className="rounded-2xl border border-border bg-secondary/20 p-4">
        <p className="text-xs text-muted-foreground">
          <strong>✨ Smart discovery:</strong> Providers are verified from official government directories, provincial health services, and employment programs. Data is location-aware and accuracy improves as new sources are added.
        </p>
      </div>
    </div>
  );
}
