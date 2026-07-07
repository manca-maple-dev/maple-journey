import axios from "axios";

const RAW_BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function resolveBackendUrl() {
  const raw = (RAW_BACKEND_URL || "").trim();

  // Temporary production safety valve: api.maplejourney.ca is currently failing CORS.
  // Route web traffic to the known healthy Railway API host until DNS/CORS is fixed.
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    // On production domains, if no backend URL or pointing to failed api.maplejourney.ca, use Railway
    if (hostname === "www.maplejourney.ca" || hostname === "maplejourney.ca" || hostname.includes("vercel.app")) {
      if (!raw || /api\.maplejourney\.ca/i.test(raw) || raw.includes("127.0.0.1")) {
        return "https://web-production-1acc6.up.railway.app";
      }
    }
  }

  return raw;
}

const BACKEND_URL = resolveBackendUrl();
export const API = BACKEND_URL ? `${BACKEND_URL}/api` : "/api";

export function getStoredToken() {
  // Backward compatibility: older builds stored auth under "token".
  return localStorage.getItem("mj_token") || localStorage.getItem("token") || "";
}

// Axios instance with bearer-token auth (token stored in localStorage).
const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Normalize FastAPI error payloads (string | array | object) into a string.
export function apiError(e) {
  if (!BACKEND_URL) {
    return "Backend URL is missing. Set REACT_APP_BACKEND_URL in frontend/.env and restart the app.";
  }
  const detail = e?.response?.data?.detail;
  if (detail == null) return e?.message || "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d?.msg || JSON.stringify(d)).join(" ");
  if (typeof detail?.msg === "string") return detail.msg;
  return String(detail);
}

export default api;
