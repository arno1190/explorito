"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  getCurrentUserInfoApiV1AuthMeGet,
  loginApiV1AuthLoginPost,
  registerApiV1AuthRegisterPost,
} from "@/lib/api/generated/auth/auth";
import type {
  ChildResponse,
  UserLogin,
  UserRegister,
  UserResponse,
} from "@/lib/api/model";

interface AuthContextType {
  user: UserResponse | null;
  loading: boolean;
  login: (data: UserLogin) => Promise<void>;
  register: (data: UserRegister) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
  impersonatedChild: ChildResponse | null;
  impersonateChild: (child: ChildResponse) => void;
  stopImpersonation: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [impersonatedChild, setImpersonatedChild] =
    useState<ChildResponse | null>(null);
  const router = useRouter();

  useEffect(() => {
    const loadUser = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (token) {
          setUser(await getCurrentUserInfoApiV1AuthMeGet());
        }
        const impersonatedChildData =
          localStorage.getItem("impersonated_child");
        if (impersonatedChildData) {
          setImpersonatedChild(JSON.parse(impersonatedChildData));
        }
      } catch (error) {
        console.error("Failed to load user:", error);
        localStorage.removeItem("access_token");
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, []);

  const login = async (data: UserLogin) => {
    const token = await loginApiV1AuthLoginPost(data);
    localStorage.setItem("access_token", token.access_token);
    const currentUser = await getCurrentUserInfoApiV1AuthMeGet();
    setUser(currentUser);

    if (currentUser.role !== "parent") {
      localStorage.removeItem("impersonated_child");
      setImpersonatedChild(null);
    }

    switch (currentUser.role) {
      case "admin":
        router.push("/admin");
        break;
      case "parent":
        router.push("/dashboard");
        break;
      case "child":
        router.push("/play");
        break;
      default:
        router.push("/dashboard");
    }
  };

  const register = async (data: UserRegister) => {
    await registerApiV1AuthRegisterPost(data);
    await login({ email: data.email, password: data.password });
  };

  const refreshUser = async () => {
    if (!localStorage.getItem("access_token")) return;
    try {
      setUser(await getCurrentUserInfoApiV1AuthMeGet());
    } catch (error) {
      console.error("Failed to refresh user:", error);
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("impersonated_child");
    setUser(null);
    setImpersonatedChild(null);
    router.push("/login");
  };

  const impersonateChild = (child: ChildResponse) => {
    localStorage.setItem("impersonated_child", JSON.stringify(child));
    setImpersonatedChild(child);
    router.push("/play");
  };

  const stopImpersonation = () => {
    localStorage.removeItem("impersonated_child");
    setImpersonatedChild(null);
    router.push("/dashboard");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        refreshUser,
        isAuthenticated: !!user,
        impersonatedChild,
        impersonateChild,
        stopImpersonation,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
