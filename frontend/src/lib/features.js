import {
  Home, Briefcase, User, ClipboardCheck, Sparkles, Scale, Smartphone, MapPin,
  Bell, Gift, CreditCard, Settings,
} from "lucide-react";

/**
 * Central registry mapping each feature flag to its UI metadata.
 * Admin toggles map 1:1 to the gated keys. Always-on items (Home, Maple
 * companion, Settings) are not gated. Scope follows the blueprint:
 * Home briefing, Maple companion, PR Assessment, Jobs, Accessibilities (eSIM),
 * Legal & Government, Communities & Help, and Settings (Profile).
 */
export const FEATURES = [
  { key: "home", label: "Home", icon: Home, path: "/app", always: true, desc: "Your daily briefing" },
  { key: "companion", label: "Ask Maple", icon: Sparkles, path: "/app/chat", always: true, desc: "Chat with your companion" },
  { key: "questionnaire", label: "Get My Resumes", icon: ClipboardCheck, path: "/app/assessment", desc: "Build and edit your resumes" },
  { key: "jobs", label: "Jobs", icon: Briefcase, path: "/app/jobs", desc: "AI job matching" },
  { key: "accessibilities", label: "Get Connected", icon: Smartphone, path: "/app/accessibilities", desc: "eSIM, banking & transit" },
  { key: "legal", label: "Legal & Government", icon: Scale, path: "/app/legal", desc: "Free & low-cost legal aid" },
  { key: "communities", label: "Communities", icon: MapPin, path: "/app/communities", desc: "Places & help near you" },
  { key: "announcements", label: "Updates", icon: Bell, path: "/app/announcements", always: true, desc: "Latest announcements" },
  { key: "benefits", label: "Benefits", icon: Gift, path: "/app/benefits", always: true, desc: "Government benefits & services" },
  { key: "billing", label: "Billing", icon: CreditCard, path: "/app/billing", always: true, desc: "Subscriptions & invoices" },
  { key: "settings", label: "Account Settings", icon: Settings, path: "/app/settings", always: true, desc: "Security, data & preferences" },
  { key: "profile", label: "Profile", icon: User, path: "/app/profile", always: true, desc: "Details, timeline & status" },
];

// Flags that admins can toggle (excludes always-on Maple Wingman/Settings).
export const TOGGLEABLE_FEATURES = FEATURES.filter((f) => !f.always);
