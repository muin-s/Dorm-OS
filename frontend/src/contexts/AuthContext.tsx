import React, { createContext, useContext, useState, useEffect } from "react";

/**
 * IMPORTANT:
 * - Use relative /api so it works with Nginx + EC2
 * - DO NOT use localhost in production
 */

interface User {
  id: number;
  name: string;
  email: string;
  role: "student" | "admin" | "worker";
  roomNo?: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (userData: any) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      refreshProfile();
    }
  }, []);

  const refreshProfile = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
      const res = await fetch(`/api/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) throw new Error("Profile fetch failed");

      const data = await res.json();
      const profile: User = {
        id: data.id,
        name: data.name,
        email: data.email,
        role: data.role,
        roomNo: data.roomNo,
      };

      setUser(profile);
      localStorage.setItem("user", JSON.stringify(profile));
    } catch {
      logout();
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const res = await fetch(`/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) return false;

      const data = await res.json();
      localStorage.setItem("access_token", data.access);

      await refreshProfile();
      return true;
    } catch {
      return false;
    }
  };

  const signup = async (form: any): Promise<boolean> => {
    try {
      const res = await fetch(`/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: form.name,
          email: form.email,
          password: form.password,
          role: "student",
          roomNo: form.roomNo,
        }),
      });

      return res.ok;
    } catch {
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        signup,
        logout,
        isAuthenticated: !!user,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
