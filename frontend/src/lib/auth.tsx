"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  devLoginApiV1AuthDevLoginPost,
  getCurrentUserInfoApiV1AuthMeGet,
  googleLoginApiV1AuthGooglePost,
  setPinApiV1AuthPinPost,
  verifyPinApiV1AuthVerifyPinPost,
} from "@/lib/api/generated/auth/auth";
import type { ChildResponse, UserResponse } from "@/lib/api/model";
import { actingRoleHome, resolveActingRole } from "@/lib/navigation";

interface AuthContextType {
  user: UserResponse | null;
  loading: boolean;
  isAuthenticated: boolean;
  /** Connexion via Google (id_token renvoyé par Google Identity Services). */
  googleLogin: (credential: string) => Promise<void>;
  /** Connexion de développement (email), active uniquement hors production. */
  devLogin: (email: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  /** Définit ou remplace le code PIN parent (4 chiffres). */
  setPin: (pin: string) => Promise<void>;
  /** Vérifie le code PIN parent ; renvoie true si correct. */
  verifyPin: (pin: string) => Promise<boolean>;
  impersonatedChild: ChildResponse | null;
  impersonateChild: (child: ChildResponse) => void;
  /** Quitte le mode enfant et revient à la vue parent. */
  exitChildMode: () => void;
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

  const finishLogin = async (accessToken: string) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.removeItem("impersonated_child");
    setImpersonatedChild(null);
    const currentUser = await getCurrentUserInfoApiV1AuthMeGet();
    setUser(currentUser);
    const role = resolveActingRole(currentUser.role, false);
    router.push(role ? actingRoleHome(role) : "/dashboard");
  };

  const googleLogin = async (credential: string) => {
    const token = await googleLoginApiV1AuthGooglePost({ credential });
    await finishLogin(token.access_token);
  };

  const devLogin = async (email: string) => {
    const token = await devLoginApiV1AuthDevLoginPost({ email });
    await finishLogin(token.access_token);
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

  const setPin = async (pin: string) => {
    const updated = await setPinApiV1AuthPinPost({ pin });
    setUser(updated);
  };

  const verifyPin = async (pin: string): Promise<boolean> => {
    try {
      await verifyPinApiV1AuthVerifyPinPost({ pin });
      return true;
    } catch {
      return false;
    }
  };

  const impersonateChild = (child: ChildResponse) => {
    localStorage.setItem("impersonated_child", JSON.stringify(child));
    setImpersonatedChild(child);
    router.push("/play");
  };

  const exitChildMode = () => {
    localStorage.removeItem("impersonated_child");
    setImpersonatedChild(null);
    router.push("/dashboard");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        googleLogin,
        devLogin,
        logout,
        refreshUser,
        setPin,
        verifyPin,
        impersonatedChild,
        impersonateChild,
        exitChildMode,
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
