import "@/App.css";
import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { PageLoader } from "@/components/common/PageLoader";
import CookieConsentBanner from "@/components/common/CookieConsentBanner";

// Layouts + auth are eager (they gate everything else).
import MarketingLayout from "@/components/marketing/MarketingLayout";
import AppLayout from "@/components/dashboard/AppLayout";
import AdminLayout from "@/components/admin/AdminLayout";
import { FeatureGate } from "@/components/dashboard/FeatureGate";
import { Login, Signup } from "@/pages/auth/Auth";

// Pages are code-split for faster initial load.
const Landing = lazy(() => import("@/pages/marketing/Landing"));
const Features = lazy(() => import("@/pages/marketing/Features"));
const Resources = lazy(() => import("@/pages/marketing/Resources"));
const Pricing = lazy(() => import("@/pages/marketing/Pricing"));
const About = lazy(() => import("@/pages/marketing/About"));
const Contact = lazy(() => import("@/pages/marketing/Contact"));
const AutoSignup = lazy(() => import("@/pages/marketing/AutoSignup"));
const Dashboard = lazy(() => import("@/pages/marketing/Dashboard"));
const Admin = lazy(() => import("@/pages/marketing/Admin"));
const PrivacyPolicy = lazy(() => import("@/pages/marketing/PrivacyPolicy"));
const TermsOfService = lazy(() => import("@/pages/marketing/TermsOfService"));
const CookiePolicy = lazy(() => import("@/pages/marketing/CookiePolicy"));
const LegalDisclaimer = lazy(() => import("@/pages/marketing/LegalDisclaimer"));

const MapleHome = lazy(() => import("@/pages/app/MapleHome"));
const Questionnaire = lazy(() => import("@/pages/app/Questionnaire"));
const Jobs = lazy(() => import("@/pages/app/Jobs"));
const ResumePage = lazy(() => import("@/pages/app/ResumePage"));
const Accessibilities = lazy(() => import("@/pages/app/Accessibilities"));
const LegalHelp = lazy(() => import("@/pages/app/LegalHelp"));
const Communities = lazy(() => import("@/pages/app/Communities"));
const MapleChat = lazy(() => import("@/pages/app/Assistant"));
const Onboarding = lazy(() => import("@/pages/app/Onboarding"));
const PlanSelection = lazy(() => import("@/pages/app/PlanSelection"));
const PlanSuccess = lazy(() => import("@/pages/app/PlanSuccess"));
const Profile = lazy(() => import("@/pages/app/Profile"));
const AppAnnouncements = lazy(() => import("@/pages/app/Announcements"));
const Benefits = lazy(() => import("@/pages/app/Benefits"));
const BillingHistory = lazy(() => import("@/pages/app/BillingHistory"));
const Settings = lazy(() => import("@/pages/app/Settings"));

const AdminDashboard = lazy(() => import("@/pages/admin/AdminDashboard"));
const UserManagement = lazy(() => import("@/pages/admin/UserManagement"));
const FeatureToggles = lazy(() => import("@/pages/admin/FeatureToggles"));
const ContentManagement = lazy(() => import("@/pages/admin/ContentManagement"));
const AdminAnnouncements = lazy(() => import("@/pages/admin/Announcements"));

// Redirect authed users away from auth pages.
function AuthGate({ children }) {
  const { user } = useAuth();
  if (user) return <Navigate to={user.role === "admin" ? "/admin" : "/app"} replace />;
  return children;
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                {/* Marketing */}
                <Route element={<MarketingLayout />}>
                  <Route path="/" element={<Landing />} />
                  <Route path="/features" element={<Features />} />
                  <Route path="/resources" element={<Resources />} />
                  <Route path="/pricing" element={<Pricing />} />
                  <Route path="/about" element={<About />} />
                  <Route path="/contact" element={<Contact />} />
                  <Route path="/form" element={<AutoSignup />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/admin" element={<Admin />} />
                  <Route path="/privacy" element={<PrivacyPolicy />} />
                  <Route path="/terms" element={<TermsOfService />} />
                  <Route path="/cookies" element={<CookiePolicy />} />
                  <Route path="/disclaimer" element={<LegalDisclaimer />} />
                </Route>

                {/* Auth */}
                <Route path="/login" element={<AuthGate><Login /></AuthGate>} />
                <Route path="/signup" element={<AuthGate><Signup /></AuthGate>} />

                {/* User app */}
                <Route path="/app" element={<AppLayout />}>
                  <Route index element={<MapleHome />} />
                  <Route path="onboarding" element={<Onboarding />} />
                  <Route path="plans" element={<PlanSelection />} />
                  <Route path="plans/success" element={<PlanSuccess />} />
                  <Route path="chat" element={<MapleChat />} />
                  <Route path="assessment" element={<FeatureGate feature="questionnaire"><Questionnaire /></FeatureGate>} />
                  <Route path="jobs" element={<FeatureGate feature="jobs"><Jobs /></FeatureGate>} />
                  <Route path="resume" element={<ResumePage />} />
                  <Route path="accessibilities" element={<FeatureGate feature="accessibilities"><Accessibilities /></FeatureGate>} />
                  <Route path="legal" element={<FeatureGate feature="legal"><LegalHelp /></FeatureGate>} />
                  <Route path="communities" element={<FeatureGate feature="communities"><Communities /></FeatureGate>} />
                  <Route path="announcements" element={<AppAnnouncements />} />
                  <Route path="benefits" element={<Benefits />} />
                  <Route path="billing" element={<BillingHistory />} />
                  <Route path="profile" element={<Profile />} />
                  <Route path="settings" element={<Settings />} />
                </Route>

                {/* Admin */}
                <Route path="/admin" element={<AdminLayout />}>
                  <Route index element={<AdminDashboard />} />
                  <Route path="users" element={<UserManagement />} />
                  <Route path="features" element={<FeatureToggles />} />
                  <Route path="content" element={<ContentManagement />} />
                  <Route path="announcements" element={<AdminAnnouncements />} />
                </Route>

                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
            <Toaster position="top-right" richColors />
            <CookieConsentBanner />
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
