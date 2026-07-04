import { Navigate } from "react-router-dom";
import { Lock } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

/**
 * Guards a route behind a feature flag. If an admin has disabled the feature
 * (globally or for this user), we show a friendly "unavailable" state instead
 * of the page — keeping admin ↔ user wiring instant and safe.
 */
export function FeatureGate({ feature, children }) {
  const { user, features } = useAuth();
  if (user === null) return null;
  if (user === false) return <Navigate to="/login" replace />;
  if (feature && features[feature] === false) {
    return (
      <div className="grid min-h-[60vh] place-items-center text-center" data-testid="feature-disabled">
        <div className="max-w-sm">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-secondary text-muted-foreground"><Lock className="h-6 w-6" /></div>
          <h2 className="mt-5 font-display text-xl font-semibold">This feature isn't available</h2>
          <p className="mt-2 text-sm text-muted-foreground">Your MapleJourney plan doesn't include this module right now. Reach out to an advisor to enable it.</p>
        </div>
      </div>
    );
  }
  return children;
}
