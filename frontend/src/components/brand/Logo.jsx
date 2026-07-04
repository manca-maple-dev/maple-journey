import { Link } from "react-router-dom";
import { ASSETS } from "@/lib/assets";

// MapleJourney brand mark (generated logo) + wordmark.
export function Logo({ to = "/", size = "md", showText = true, className = "" }) {
  const dims = { sm: 26, md: 32, lg: 40 }[size] || 32;
  const text = { sm: "text-lg", md: "text-xl", lg: "text-2xl" }[size] || "text-xl";
  return (
    <Link to={to} className={`flex items-center gap-2.5 group ${className}`} data-testid="brand-logo">
      <span
        className="relative overflow-hidden rounded-xl shadow-lg shadow-brand-500/25 transition-transform duration-300 group-hover:-translate-y-0.5"
        style={{ width: dims, height: dims }}
      >
        <img src={ASSETS.logo} alt="MapleJourney logo" className="h-full w-full scale-[1.2] object-cover" />
      </span>
      {showText && (
        <span className={`font-display font-bold tracking-tight ${text}`}>
          Maple<span className="text-brand-500">Journey</span>
        </span>
      )}
    </Link>
  );
}
