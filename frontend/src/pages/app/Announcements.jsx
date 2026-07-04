import { useEffect, useState } from "react";
import { Bell, Filter, Clock, Zap, Tag } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";

const CATEGORIES = [
  { value: "all", label: "All categories" },
  { value: "policy", label: "Policy changes" },
  { value: "deadline", label: "Deadline alerts" },
  { value: "feature", label: "New features" },
  { value: "maintenance", label: "Maintenance" },
  { value: "general", label: "General" },
  { value: "jobs", label: "Jobs" },
  { value: "benefits", label: "Benefits" },
  { value: "legal", label: "Legal help" },
  { value: "community", label: "Community" },
  { value: "language", label: "Language support" },
  { value: "health", label: "Health" },
  { value: "housing", label: "Housing" },
  { value: "documents", label: "Documents & IDs" },
];

export default function Announcements() {
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("recent");

  const { data: announcements = [], isLoading } = useQuery({
    queryKey: ["announcements"],
    queryFn: () => api.get("/domain/announcements").then((r) => r.data || []),
  });

  let filtered = announcements;
  if (category !== "all") filtered = filtered.filter((a) => a.category === category);
  if (search) filtered = filtered.filter((a) => 
    a.title.toLowerCase().includes(search.toLowerCase()) || 
    a.content.toLowerCase().includes(search.toLowerCase())
  );

  if (sortBy === "recent") filtered = [...filtered].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  if (sortBy === "priority") filtered = [...filtered].sort((a, b) => (b.priority || 0) - (a.priority || 0));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-bold flex items-center gap-2">
          <Bell className="h-8 w-8 text-maple-red" />
          Announcements & Updates
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Stay informed about policy changes, new features, and important dates.
        </p>
      </div>

      {/* Filters */}
      <div className="rounded-2xl border border-border bg-card p-4 space-y-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="flex-1">
            <Input
              placeholder="Search announcements..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="rounded-lg"
            />
          </div>

          <div className="flex gap-3">
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger className="w-40">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((item) => (
                  <SelectItem key={item.value} value={item.value}>{item.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-40">
                <Clock className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="recent">Most Recent</SelectItem>
                <SelectItem value="priority">High Priority</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Announcements List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 rounded-2xl bg-card border border-border mj-shimmer" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-2xl border border-border bg-card p-8 text-center">
            <Bell className="h-12 w-12 mx-auto opacity-20 mb-3" />
            <p className="text-muted-foreground">No announcements match your filters at the moment. Additional verified updates will appear as new data is ingested.</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {CATEGORIES.filter((item) => item.value !== "all").slice(0, 6).map((item) => (
                <button
                  key={item.value}
                  onClick={() => setCategory(item.value)}
                  className="rounded-full border border-border bg-secondary/40 px-3 py-1.5 text-xs font-medium text-foreground hover:border-brand-400"
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          filtered.map((ann) => (
            <div key={ann.id} className="rounded-2xl border border-border bg-card p-5 hover:shadow-md transition-shadow">
              <div className="flex gap-4">
                {/* Category Badge */}
                <div className="flex-shrink-0">
                  <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                    ann.category === "policy" ? "bg-blue-100 dark:bg-blue-900" :
                    ann.category === "deadline" ? "bg-red-100 dark:bg-red-900" :
                    ann.category === "feature" ? "bg-green-100 dark:bg-green-900" :
                    "bg-gray-100 dark:bg-gray-800"
                  }`}>
                    {ann.category === "policy" && <Tag className="h-5 w-5 text-blue-600 dark:text-blue-300" />}
                    {ann.category === "deadline" && <Zap className="h-5 w-5 text-red-600 dark:text-red-300" />}
                    {ann.category === "feature" && <Zap className="h-5 w-5 text-green-600 dark:text-green-300" />}
                    {!["policy", "deadline", "feature"].includes(ann.category) && <Bell className="h-5 w-5 text-gray-600 dark:text-gray-300" />}
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <h3 className="font-semibold text-base">{ann.title}</h3>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{ann.content}</p>
                    </div>
                    {ann.priority && (
                      <div className="text-xs font-semibold px-2 py-1 rounded-lg bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200 flex-shrink-0">
                        URGENT
                      </div>
                    )}
                  </div>
                  
                  {/* Metadata */}
                  <div className="mt-3 flex gap-4 text-xs text-muted-foreground">
                    <span>{new Date(ann.created_at).toLocaleDateString()}</span>
                    {ann.valid_until && (
                      <span>Valid until: {new Date(ann.valid_until).toLocaleDateString()}</span>
                    )}
                  </div>

                  {/* CTA if present */}
                  {ann.cta_link && (
                    <div className="mt-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(ann.cta_link, "_blank")}
                      >
                        {ann.cta_text || "Learn more"}
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
