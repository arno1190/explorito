"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ChildLayout } from "@/components/layout/ChildLayout";
import {
  actingRoleHome,
  isPathAllowedForRole,
  useActingRole,
} from "@/lib/navigation";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const actingRole = useActingRole();
  const router = useRouter();
  const pathname = usePathname();

  // Redirect unauthenticated users to login.
  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, loading, router]);

  // Keep each persona in its lane: a child can't open the parent dashboard,
  // a parent can't open admin, etc. Redirect to the role's home instead.
  useEffect(() => {
    if (loading || !isAuthenticated || !actingRole) return;
    if (!isPathAllowedForRole(pathname, actingRole)) {
      router.replace(actingRoleHome(actingRole));
    }
  }, [loading, isAuthenticated, actingRole, pathname, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-fun-surface">
        <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-fun-green-light border-t-fun-green"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <ChildLayout>{children}</ChildLayout>;
}
