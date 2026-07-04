import { useState, useMemo, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { Loader2, Check, X, AlertCircle, ShieldCheck, FileCheck2, Clock } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/common/PasswordInput";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import {
  validateName, validateEmail, validatePassword,
  passwordChecks, passwordStrength,
} from "@/lib/validation";

/* Kept for backwards-compat with any importer; onboarding now captures situation. */
export const NEWCOMER_TYPES = [
  { value: "worker", label: "Worker (work permit)" },
  { value: "student", label: "International student" },
  { value: "visitor", label: "Visitor" },
  { value: "refugee", label: "Refugee / asylum seeker" },
  { value: "family", label: "Family / sponsorship" },
  { value: "other", label: "Not sure yet" },
];

const TRUST = [
  { icon: FileCheck2, text: "Cited from IRCC, CRA & Service Canada" },
  { icon: ShieldCheck, text: "Your data stays private — you're in control" },
  { icon: Clock, text: "Set up in under two minutes" },
];

/* ---------------- Shared shell ---------------- */
function AuthShell({ children }) {
  const reduce = useReducedMotion();
  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      {/* Brand panel */}
      <aside className="relative hidden overflow-hidden bg-brand-600 p-12 text-white lg:flex lg:flex-col lg:justify-between" aria-hidden="true">
        <div className="pointer-events-none absolute inset-0 mj-dot-bg opacity-20" />
        <div className="pointer-events-none absolute -bottom-24 -right-24 h-96 w-96 rounded-full bg-maple/30 blur-3xl" />
        <div className="pointer-events-none absolute -left-16 -top-16 h-72 w-72 rounded-full bg-brand-400/30 blur-3xl" />
        <Logo className="relative [&_span]:text-white" />
        <div className="relative max-w-md">
          <motion.h2
            initial={reduce ? false : { opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
            className="font-display text-4xl font-bold leading-[1.1]">
            Your new life in Canada starts with one clear step.
          </motion.h2>
          <motion.p
            initial={reduce ? false : { opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.08 }}
            className="mt-5 text-lg text-white/80">
            Join 12,000+ newcomers navigating visas, PR, jobs and benefits — guided every step.
          </motion.p>
          <ul className="mt-8 space-y-3">
            {TRUST.map((t, idx) => {
              const Icon = t.icon;
              return (
                <motion.li key={t.text}
                  initial={reduce ? false : { opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.35, delay: 0.15 + idx * 0.08 }}
                  className="flex items-center gap-3 text-white/90">
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-white/15 backdrop-blur">
                    <Icon className="h-4.5 w-4.5" />
                  </span>
                  <span className="text-sm">{t.text}</span>
                </motion.li>
              );
            })}
          </ul>
        </div>
        <p className="relative text-sm text-white/60">🍁 MapleJourney — your newcomer companion</p>
      </aside>

      {/* Form panel */}
      <main className="relative flex flex-col items-center justify-center px-5 py-10 sm:px-6">
        <div className="absolute right-4 top-4"><ThemeToggle /></div>
        <motion.div
          initial={reduce ? false : { opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
          className="w-full max-w-sm">
          <div className="mb-8 lg:hidden"><Logo /></div>
          {children}
        </motion.div>
      </main>
    </div>
  );
}

/* ---------------- Reusable field ---------------- */
function FieldError({ id, message }) {
  if (!message) return null;
  return (
    <p id={id} role="alert" className="flex items-center gap-1.5 pt-1 text-xs font-medium text-maple">
      <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" /> {message}
    </p>
  );
}

/* ---------------- Login ---------------- */
export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [touched, setTouched] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const emailErr = touched.email ? validateEmail(email) : "";

  const submit = async (e) => {
    e.preventDefault();
    setTouched({ email: true, password: true });
    const ve = validateEmail(email);
    if (ve || !password) { setError(""); return; }
    setError(""); setLoading(true);
    const res = await login(email, password);
    setLoading(false);
    if (res.ok) {
      if (res.user.role === "admin") navigate("/admin");
      else if (!res.user.profile_completed) navigate("/app/onboarding");
      else navigate("/app");
    } else setError(res.error);
  };

  return (
    <AuthShell>
      <h1 className="font-display text-3xl font-bold tracking-tight">Welcome back</h1>
      <p className="mt-1.5 text-sm text-muted-foreground">Sign in to continue your journey.</p>
      <form onSubmit={submit} className="mt-8 space-y-4" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" inputMode="email" autoComplete="email" required
            value={email} onChange={(e) => setEmail(e.target.value)} onBlur={() => setTouched((t) => ({ ...t, email: true }))}
            aria-invalid={!!emailErr} aria-describedby={emailErr ? "login-email-err" : undefined}
            className={cn("h-11", emailErr && "border-maple focus-visible:ring-maple/40")}
            placeholder="you@example.com" data-testid="login-email" />
          <FieldError id="login-email-err" message={emailErr} />
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
          </div>
          <PasswordInput id="password" autoComplete="current-password" required value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="h-11" placeholder="••••••••" data-testid="login-password" toggleTestId="login-password-toggle" />
        </div>
        {error && (
          <p className="flex items-center gap-2 rounded-lg bg-maple-50 px-3 py-2.5 text-sm text-maple dark:bg-maple-500/10" role="alert" data-testid="login-error">
            <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />{error}
          </p>
        )}
        <Button type="submit" className="h-11 w-full rounded-full text-[15px]" disabled={loading} data-testid="login-submit">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : "Sign in"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        New to MapleJourney? <Link to="/signup" className="font-semibold text-brand-500 hover:underline" data-testid="login-to-signup">Create an account</Link>
      </p>
      <div className="mt-5 rounded-2xl border border-border bg-card/70 p-4 text-xs leading-6 text-muted-foreground">
        By using MapleJourney, you agree to our <Link to="/terms" state={{ from: location }} className="font-medium text-brand-500 hover:underline">Terms of Service</Link> and <Link to="/privacy" state={{ from: location }} className="font-medium text-brand-500 hover:underline">Privacy Policy</Link>.
        MapleJourney is an AI-powered information and organization platform, not a law firm or government office.
      </div>
    </AuthShell>
  );
}

/* ---------------- Signup ---------------- */
export function Signup() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const reduce = useReducedMotion();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [touched, setTouched] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const pwFocused = useRef(false);
  const [showChecks, setShowChecks] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const blur = (k) => () => setTouched((t) => ({ ...t, [k]: true }));

  const errs = {
    name: touched.name ? validateName(form.name) : "",
    email: touched.email ? validateEmail(form.email) : "",
    password: touched.password ? validatePassword(form.password) : "",
  };
  const { score, label } = passwordStrength(form.password);
  const checks = useMemo(() => passwordChecks(form.password), [form.password]);
  const formValid = !validateName(form.name) && !validateEmail(form.email) && !validatePassword(form.password);

  const submit = async (e) => {
    e.preventDefault();
    setTouched({ name: true, email: true, password: true });
    if (!formValid) { setError(""); return; }
    setError(""); setLoading(true);
    const res = await register({ name: form.name.trim(), email: form.email.trim(), password: form.password });
    setLoading(false);
    if (res.ok) navigate("/app/onboarding");
    else setError(res.error);
  };

  const barColor = ["bg-secondary", "bg-maple", "bg-amber-500", "bg-brand-500", "bg-green-500"][score];

  return (
    <AuthShell>
      <h1 className="font-display text-3xl font-bold tracking-tight">Create your account</h1>
      <p className="mt-1.5 text-sm text-muted-foreground">Free to start · no credit card · about 2 minutes.</p>
      <form onSubmit={submit} className="mt-8 space-y-4" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="name">Full name</Label>
          <Input id="name" autoComplete="name" required value={form.name} onChange={set("name")} onBlur={blur("name")}
            aria-invalid={!!errs.name} aria-describedby={errs.name ? "signup-name-err" : undefined}
            className={cn("h-11", errs.name && "border-maple focus-visible:ring-maple/40")}
            placeholder="Alex Newcomer" data-testid="signup-name" />
          <FieldError id="signup-name-err" message={errs.name} />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <div className="relative">
            <Input id="email" type="email" inputMode="email" autoComplete="email" required
              value={form.email} onChange={set("email")} onBlur={blur("email")}
              aria-invalid={!!errs.email} aria-describedby={errs.email ? "signup-email-err" : undefined}
              className={cn("h-11 pr-9", errs.email && "border-maple focus-visible:ring-maple/40")}
              placeholder="you@example.com" data-testid="signup-email" />
            {touched.email && !errs.email && form.email && (
              <Check className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-green-500" aria-hidden="true" />
            )}
          </div>
          <FieldError id="signup-email-err" message={errs.email} />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <PasswordInput id="password" autoComplete="new-password" required value={form.password}
            onChange={set("password")} onFocus={() => setShowChecks(true)} onBlur={blur("password")}
            aria-describedby="password-reqs"
            className="h-11" placeholder="Create a strong password" data-testid="signup-password" toggleTestId="signup-password-toggle" />

          {form.password && (
            <div className="flex items-center gap-2 pt-1" data-testid="password-strength">
              <div className="flex flex-1 gap-1" aria-hidden="true">
                {[0, 1, 2, 3].map((i) => (
                  <span key={i} className={cn("h-1.5 flex-1 rounded-full transition-colors", i < score ? barColor : "bg-secondary")} />
                ))}
              </div>
              <span className="w-12 text-right text-xs font-medium text-muted-foreground">{label}</span>
            </div>
          )}

          {(showChecks || errs.password) && (
            <motion.ul id="password-reqs" aria-live="polite"
              initial={reduce ? false : { opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
              className="grid grid-cols-2 gap-x-3 gap-y-1.5 pt-2">
              {checks.map((c) => (
                <li key={c.id} className={cn("flex items-center gap-1.5 text-xs", c.ok ? "text-green-600 dark:text-green-500" : "text-muted-foreground")}>
                  {c.ok ? <Check className="h-3.5 w-3.5 shrink-0" aria-hidden="true" /> : <X className="h-3.5 w-3.5 shrink-0 opacity-50" aria-hidden="true" />}
                  {c.label}
                </li>
              ))}
            </motion.ul>
          )}
        </div>

        {error && (
          <p className="flex items-center gap-2 rounded-lg bg-maple-50 px-3 py-2.5 text-sm text-maple dark:bg-maple-500/10" role="alert" data-testid="signup-error">
            <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />{error}
          </p>
        )}
        <Button type="submit" className="h-11 w-full rounded-full text-[15px]" disabled={loading} data-testid="signup-submit">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : "Create account"}
        </Button>
        <p className="text-center text-xs text-muted-foreground">
          By continuing you agree to our <Link to="/terms" state={{ from: location }} className="font-medium text-brand-500 hover:underline">Terms of Service</Link> and <Link to="/privacy" state={{ from: location }} className="font-medium text-brand-500 hover:underline">Privacy Policy</Link>.
        </p>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account? <Link to="/login" className="font-semibold text-brand-500 hover:underline" data-testid="signup-to-login">Sign in</Link>
      </p>
      <div className="mt-5 rounded-2xl border border-border bg-card/70 p-4 text-xs leading-6 text-muted-foreground">
        MapleJourney uses AI to help newcomers organize information, discover resources, and understand next steps. AI responses may be incomplete or wrong, so important decisions should be verified with official sources or qualified professionals. See our <Link to="/disclaimer" state={{ from: location }} className="font-medium text-brand-500 hover:underline">AI Disclaimer</Link> and <Link to="/cookies" state={{ from: location }} className="font-medium text-brand-500 hover:underline">Cookie Policy</Link>.
      </div>
    </AuthShell>
  );
}
