// Shared, framework-agnostic validation helpers for the onboarding flow.
// Keep messages specific and actionable (no generic "invalid input").

// Pragmatic RFC 5322 subset — good UX without rejecting valid addresses.
export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function validateName(v) {
  const s = (v || "").trim();
  if (!s) return "Please enter your name";
  if (s.length < 2) return "That name looks a little short";
  return "";
}

export function validateEmail(v) {
  const s = (v || "").trim();
  if (!s) return "Please enter your email";
  if (!EMAIL_RE.test(s)) return "Enter a valid email, e.g. you@example.com";
  return "";
}

// Individual password requirements, surfaced as a live checklist.
export function passwordChecks(pw = "") {
  return [
    { id: "len", label: "At least 8 characters", ok: pw.length >= 8 },
    { id: "case", label: "Upper & lowercase letters", ok: /[a-z]/.test(pw) && /[A-Z]/.test(pw) },
    { id: "num", label: "A number", ok: /\d/.test(pw) },
    { id: "sym", label: "A symbol (!?@#…)", ok: /[^A-Za-z0-9]/.test(pw) },
  ];
}

// 0–4 strength score with a human label.
export function passwordStrength(pw = "") {
  if (!pw) return { score: 0, label: "" };
  const passed = passwordChecks(pw).filter((c) => c.ok).length;
  const score = Math.min(4, passed);
  const label = ["", "Weak", "Fair", "Good", "Strong"][score];
  return { score, label };
}

// Submit is allowed once the minimum bar is met (length + reasonable mix).
export function validatePassword(pw = "") {
  if (!pw) return "Please create a password";
  if (pw.length < 8) return "Use at least 8 characters";
  const { score } = passwordStrength(pw);
  if (score < 2) return "Add a mix of letters and numbers to strengthen it";
  return "";
}

// --- Onboarding field validators ---
export function validateDOB(v) {
  if (!v) return "";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return "Enter a valid date";
  const now = new Date();
  if (d > now) return "Date can't be in the future";
  const age = (now - d) / (365.25 * 24 * 3600 * 1000);
  if (age < 16) return "You must be at least 16";
  if (age > 120) return "Please check this date";
  return "";
}

export function validatePostalPrefix(v) {
  if (!v) return "";
  return /^[A-Za-z]\d[A-Za-z]$/.test(v.trim()) ? "" : "Use the first 3 characters, e.g. M5V";
}

export function validateNonNegative(v) {
  if (v === "" || v == null) return "";
  return Number(v) >= 0 ? "" : "Can't be negative";
}
