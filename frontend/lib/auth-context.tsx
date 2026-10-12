"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { api, User } from "./api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEFAULT_USER: User = {
  id: "default-local-user",
  email: "local@lecturedubber.internal",
  role: "admin",
  created_at: new Date().toISOString(),
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(DEFAULT_USER);
  const [loading, setLoading] = useState(false);

  const refreshUser = async () => {
    try {
      const me = await api.getMe();
      if (me && me.id) {
        setUser(me);
        return;
      }
    } catch {
      // Fallback to local default user
    }
    setUser(DEFAULT_USER);
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const res = await api.login(email, password);
      if (res?.user) {
        setUser(res.user);
      }
    } catch {
      setUser(DEFAULT_USER);
    }
  };

  const register = async (email: string, password: string) => {
    try {
      const res = await api.register(email, password);
      if (res?.user) {
        setUser(res.user);
      }
    } catch {
      setUser(DEFAULT_USER);
    }
  };

  const logout = () => {
    // Zero-auth mode: keep local user session active
    setUser(DEFAULT_USER);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
