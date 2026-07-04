import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api, { apiError } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null = loading, false = logged out, object = logged in
  const [features, setFeatures] = useState({});

  const loadFeatures = useCallback(async () => {
    try {
      const { data } = await api.get("/features");
      setFeatures(data);
    } catch {
      setFeatures({});
    }
  }, []);

  const bootstrap = useCallback(async () => {
    const token = localStorage.getItem("mj_token");
    if (!token) {
      setUser(false);
      return;
    }
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
      await loadFeatures();
    } catch {
      localStorage.removeItem("mj_token");
      setUser(false);
    }
  }, [loadFeatures]);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const login = async (email, password) => {
    try {
      const { data } = await api.post("/auth/login", { email, password });
      localStorage.setItem("mj_token", data.token);
      setUser(data.user);
      await loadFeatures();
      return { ok: true, user: data.user };
    } catch (e) {
      return { ok: false, error: apiError(e) };
    }
  };

  const register = async (payload) => {
    try {
      const { data } = await api.post("/auth/register", payload);
      localStorage.setItem("mj_token", data.token);
      setUser(data.user);
      await loadFeatures();
      return { ok: true, user: data.user };
    } catch (e) {
      return { ok: false, error: apiError(e) };
    }
  };

  const logout = () => {
    localStorage.removeItem("mj_token");
    setUser(false);
    setFeatures({});
  };

  const refreshUser = useCallback(async () => {
    const { data } = await api.get("/auth/me");
    setUser(data);
  }, []);

  return (
    <AuthContext.Provider value={{ user, features, login, register, logout, refreshUser, loadFeatures, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
