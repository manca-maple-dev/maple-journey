import { useEffect, useState, useCallback, useRef } from "react";
import { MapPin, Bookmark, BookmarkCheck, ExternalLink, Info, Search, FileCheck2, Loader, RotateCw, Zap } from "lucide-react";
import api from "@/lib/api";

export default function Jobs() {
  const hasLoadedRef = useRef(false);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState("");
  const [location, setLocation] = useState("Toronto");
  const [jobType, setJobType] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("");
  const [daysPosted, setDaysPosted] = useState(7);
  const [salaryMin, setSalaryMin] = useState(null);
  const [salaryMax, setSalaryMax] = useState(null);
  const [savedJobs, setSavedJobs] = useState(new Set());
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Intelligent search - live scraping with cache bypass
  const searchJobs = useCallback(async (forceRefresh = false) => {
    setLoading(true);
    try {
      const response = await api.get("/jobs/search", {
        params: {
          location,
          keywords: q || undefined,
          job_type: jobType || undefined,
          experience_level: experienceLevel || undefined,
          salary_min: salaryMin || undefined,
          salary_max: salaryMax || undefined,
          days_posted: daysPosted,
          refresh: forceRefresh,
          limit: 50,
        },
      });
      
      setJobs(response.data.jobs || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Job search failed:", error);
    } finally {
      setLoading(false);
    }
  }, [q, location, jobType, experienceLevel, daysPosted, salaryMin, salaryMax]);

  // Initial load
  useEffect(() => {
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true;
      searchJobs();
    }
  }, [searchJobs]);

  // Debounced search on filter changes
  useEffect(() => {
    const timer = setTimeout(() => searchJobs(), 500);
    return () => clearTimeout(timer);
  }, [q, location, jobType, experienceLevel, daysPosted, searchJobs]);

  const handleForceRefresh = async () => {
    setIsRefreshing(true);
    await searchJobs(true);
    setIsRefreshing(false);
  };

  const toggle = (jobId) => {
    setSavedJobs((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(jobId)) {
        newSet.delete(jobId);
      } else {
        newSet.add(jobId);
      }
      return newSet;
    });
  };

  const formatSalary = (min, max) => {
    if (!min && !max) return null;
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    if (min) return `$${min.toLocaleString()}+`;
    return `$${max.toLocaleString()}`;
  };

  const getRelevanceColor = (score) => {
    if (score >= 80) return "bg-green-50 text-green-700 dark:bg-green-500/10";
    if (score >= 60) return "bg-blue-50 text-blue-700 dark:bg-blue-500/10";
    if (score >= 40) return "bg-amber-50 text-amber-700 dark:bg-amber-500/10";
    return "bg-gray-50 text-gray-700 dark:bg-gray-500/10";
  };

  return (
    <div className="space-y-5" data-testid="jobs-page">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">Jobs in Canada</h1>
        <p className="mt-1 text-sm text-muted-foreground">Live job listings matched to your profile. Updated in real time within a 25 km radius.</p>
      </div>

      {/* Smart matching badge */}
      <div className="inline-flex items-center gap-2 rounded-full bg-green-50 px-3.5 py-1.5 text-xs font-medium text-green-700 dark:bg-green-500/10">
        <Zap className="h-3.5 w-3.5" />
        Intelligent matching active - refreshed on each search
      </div>

      {/* Discovery layer disclaimer */}
      <div className="flex items-start gap-2 rounded-xl border border-border bg-secondary/50 px-3.5 py-2.5 text-xs text-muted-foreground">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand-500" />
        <span>Maple aggregates live job listings from Government Job Bank and top Canadian boards. We're a discovery layer — all applications go directly to employers.</span>
      </div>

      {/* Application readiness */}
      <div className="rounded-2xl border border-brand-500/25 bg-brand-50/60 p-4 dark:bg-brand-500/10">
        <div className="flex items-start gap-2">
          <FileCheck2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" />
          <div>
            <p className="text-sm font-semibold">Increase your success rate</p>
            <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
              <li>✓ Tailor your resume to each role using Canadian keywords.</li>
              <li>✓ Confirm your work authorization fits the position.</li>
              <li>✓ Apply to 3-5 roles weekly for best results.</li>
            </ul>
            <div className="mt-3 flex flex-wrap gap-2">
              <a href="https://www.jobbank.gc.ca/findajob/resources/write-good-resume" target="_blank" rel="noopener noreferrer" className="rounded-full border border-border bg-card px-3 py-1.5 text-[11px] font-medium text-brand-600 hover:border-brand-400">
                Resume guide <ExternalLink className="ml-1 inline h-3 w-3" />
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Smart filters */}
      <div className="rounded-2xl border border-border bg-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">Smart Filters</h3>
          <button
            onClick={handleForceRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 text-xs font-medium text-brand-600 hover:text-brand-700 disabled:opacity-50"
          >
            <RotateCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Refreshing...' : 'Live Refresh'}
          </button>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {/* Location */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Location</label>
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
            >
              <option>Toronto</option>
              <option>Vancouver</option>
              <option>Montreal</option>
              <option>Calgary</option>
              <option>Edmonton</option>
              <option>Ottawa</option>
              <option>Winnipeg</option>
            </select>
          </div>

          {/* Job Type */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Job Type</label>
            <select
              value={jobType}
              onChange={(e) => setJobType(e.target.value)}
              className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
            >
              <option value="">All types</option>
              <option>Full-time</option>
              <option>Part-time</option>
              <option>Contract</option>
            </select>
          </div>

          {/* Experience Level */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Experience</label>
            <select
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value)}
              className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
            >
              <option value="">All levels</option>
              <option>entry</option>
              <option>mid</option>
              <option>senior</option>
            </select>
          </div>

          {/* Days Posted */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Posted</label>
            <select
              value={daysPosted}
              onChange={(e) => setDaysPosted(parseInt(e.target.value))}
              className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
            >
              <option value={1}>Today</option>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Search box */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search job titles, companies, skills…"
          className="w-full rounded-xl border border-border bg-card py-2.5 pl-10 pr-4 text-sm outline-none focus:ring-2 focus:ring-brand-500/40"
        />
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-2">
            <Loader className="h-6 w-6 animate-spin text-brand-600" />
            <p className="text-sm text-muted-foreground">Scraping live jobs...</p>
          </div>
        </div>
      )}

      {/* Results */}
      {!loading && (
        <>
          <p className="text-xs text-muted-foreground">
            Found {jobs.length} jobs in {location}
            {lastUpdated && ` · Updated ${lastUpdated.toLocaleTimeString()}`}
          </p>

          <div className="grid gap-4 sm:grid-cols-2">
            {jobs.length > 0 ? (
              jobs.map((job) => (
                <div
                  key={job._id}
                  className="group flex flex-col rounded-2xl border border-border bg-card p-5 transition-all hover:-translate-y-1 hover:shadow-lg"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-display font-semibold leading-snug text-foreground truncate">
                        {job.title}
                      </h3>
                      <p className="text-xs text-muted-foreground truncate">{job.company}</p>
                    </div>
                    <button
                      onClick={() => toggle(job._id)}
                      className="ml-2 grid h-9 w-9 shrink-0 place-items-center rounded-lg text-muted-foreground hover:bg-secondary"
                    >
                      {savedJobs.has(job._id) ? (
                        <BookmarkCheck className="h-5 w-5 text-brand-500" />
                      ) : (
                        <Bookmark className="h-5 w-5" />
                      )}
                    </button>
                  </div>

                  {/* Details */}
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5" /> {job.location}
                    </span>
                    {job.salary_max && (
                      <>
                        <span>·</span>
                        <span>{formatSalary(job.salary_min, job.salary_max)}</span>
                      </>
                    )}
                    {job.job_type && (
                      <>
                        <span>·</span>
                        <span>{job.job_type}</span>
                      </>
                    )}
                  </div>

                  {/* Tags */}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {job.industry && (
                      <span className="rounded-full bg-secondary px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                        {job.industry}
                      </span>
                    )}
                    {job.experience_level && (
                      <span className="rounded-full bg-secondary px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                        {job.experience_level}
                      </span>
                    )}
                  </div>

                  {/* Relevance Score */}
                  {job.relevance_score && (
                    <div className={`mt-3 inline-flex w-fit items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${getRelevanceColor(job.relevance_score)}`}>
                      ⭐ {job.relevance_score}/100 match
                    </div>
                  )}

                  {/* Apply button */}
                  <a
                    href={job.external_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 flex items-center justify-center gap-1.5 rounded-full border border-border py-2 text-sm font-semibold text-brand-600 transition-colors hover:bg-brand-50 dark:hover:bg-brand-500/10"
                  >
                    View job <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </div>
              ))
            ) : (
              <div className="col-span-full py-12 text-center">
                <p className="text-muted-foreground">No jobs match these filters at the moment. Try adjusting your search criteria. We continuously ingest more accurate job data to improve results.</p>
              </div>
            )}
          </div>
        </>
      )}

      <p className="pt-4 text-center text-[11px] text-muted-foreground">
        Powered by Government Job Bank and Canadian job platforms. Maple is a discovery layer — all job applications and communications go directly to employers.
      </p>
    </div>
  );
}
