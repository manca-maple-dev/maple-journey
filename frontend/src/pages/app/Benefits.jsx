import { useEffect, useState } from "react";
import { Gift, Search, Filter, Zap, MapPin, Check } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

export default function BenefitsMarketplace() {
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [province, setProvince] = useState(user?.profile?.province || "ON");

  const { data: benefits = [], isLoading } = useQuery({
    queryKey: ["benefits", province],
    queryFn: () => api.get(`/domain/benefits?province=${province}`).then((r) => r.data || []),
  });

  let filtered = benefits;
  if (filter !== "all") filtered = filtered.filter((b) => b.category === filter);
  if (search) filtered = filtered.filter((b) => 
    b.title.toLowerCase().includes(search.toLowerCase()) ||
    b.description.toLowerCase().includes(search.toLowerCase())
  );

  const handleOpen = (benefit) => {
    if (benefit.url) {
      window.open(benefit.url, "_blank");
      toast.success(`Opened ${benefit.title}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-bold flex items-center gap-2">
          <Gift className="h-8 w-8 text-maple-red" />
          Government Benefits & Services
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Discover programs and benefits available to you. Filtering by <span className="font-semibold">{province}</span>.
        </p>
      </div>

      {/* Search & Filters */}
      <div className="rounded-2xl border border-border bg-card p-4 space-y-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search benefits (e.g., healthcare, housing, jobs)..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 rounded-lg"
              />
            </div>
          </div>

          <Select value={province} onValueChange={setProvince}>
            <SelectTrigger className="w-40">
              <MapPin className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ON">Ontario</SelectItem>
              <SelectItem value="BC">British Columbia</SelectItem>
              <SelectItem value="QC">Quebec</SelectItem>
              <SelectItem value="AB">Alberta</SelectItem>
              <SelectItem value="MB">Manitoba</SelectItem>
              <SelectItem value="SK">Saskatchewan</SelectItem>
              <SelectItem value="NS">Nova Scotia</SelectItem>
              <SelectItem value="NB">New Brunswick</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-40">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All benefits</SelectItem>
              <SelectItem value="healthcare">Healthcare</SelectItem>
              <SelectItem value="housing">Housing</SelectItem>
              <SelectItem value="employment">Employment</SelectItem>
              <SelectItem value="education">Education</SelectItem>
              <SelectItem value="childcare">Childcare</SelectItem>
              <SelectItem value="financial">Financial Aid</SelectItem>
              <SelectItem value="social">Social Services</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Benefits Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          [...Array(6)].map((_, i) => (
            <div key={i} className="h-48 rounded-2xl bg-card border border-border mj-shimmer" />
          ))
        ) : filtered.length === 0 ? (
          <div className="sm:col-span-2 lg:col-span-3 rounded-2xl border border-border bg-card p-8 text-center">
            <Gift className="h-12 w-12 mx-auto opacity-20 mb-3" />
            <p className="text-muted-foreground">No benefits match your search yet. We are continuously adding more accurate benefit data for each province.</p>
          </div>
        ) : (
          filtered.map((benefit) => (
            <div key={benefit.id} className="rounded-2xl border border-border bg-card p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between gap-3 mb-3">
                <h3 className="font-semibold text-lg flex-1">{benefit.title}</h3>
                {benefit.is_new && (
                  <div className="text-xs font-bold px-2 py-1 rounded-full bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-200 flex-shrink-0">
                    NEW
                  </div>
                )}
              </div>

              <p className="text-sm text-muted-foreground mb-4">{benefit.description}</p>

              {/* Key details */}
              <div className="space-y-2 mb-4 text-sm">
                {benefit.eligibility && (
                  <div className="flex gap-2">
                    <Check className="h-4 w-4 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-muted-foreground">Eligibility: {benefit.eligibility}</span>
                  </div>
                )}
                {benefit.coverage && (
                  <div className="flex gap-2">
                    <Zap className="h-4 w-4 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <span className="text-muted-foreground">{benefit.coverage}</span>
                  </div>
                )}
              </div>

              <Button
                onClick={() => handleOpen(benefit)}
                className="w-full"
                disabled={!benefit.url}
              >
                {benefit.cta_text || "Learn More"}
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
