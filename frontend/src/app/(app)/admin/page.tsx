"use client";

import { useAuth } from "@/lib/auth";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminDashboard() {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user && user.role !== "admin") {
      router.push("/dashboard");
    }
  }, [user, router]);

  if (!user || user.role !== "admin") {
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <p className="text-muted-foreground">
          Manage users, content, and view statistics
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border p-6">
          <h3 className="text-lg font-semibold mb-2">Users</h3>
          <p className="text-3xl font-bold text-primary">0</p>
          <p className="text-sm text-muted-foreground">Total users</p>
        </div>

        <div className="rounded-lg border p-6">
          <h3 className="text-lg font-semibold mb-2">Subjects</h3>
          <p className="text-3xl font-bold text-primary">0</p>
          <p className="text-sm text-muted-foreground">Total subjects</p>
        </div>

        <div className="rounded-lg border p-6">
          <h3 className="text-lg font-semibold mb-2">Lessons</h3>
          <p className="text-3xl font-bold text-primary">0</p>
          <p className="text-sm text-muted-foreground">Total lessons</p>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-2xl font-semibold">Quick Actions</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <button
            onClick={() => router.push("/admin/users")}
            className="rounded-lg border p-6 text-left hover:bg-accent transition-colors"
          >
            <h3 className="text-lg font-semibold mb-2">Manage Users</h3>
            <p className="text-sm text-muted-foreground">
              Create, edit, and delete users of all types
            </p>
          </button>

          <button
            onClick={() => router.push("/subjects")}
            className="rounded-lg border p-6 text-left hover:bg-accent transition-colors"
          >
            <h3 className="text-lg font-semibold mb-2">Manage Content</h3>
            <p className="text-sm text-muted-foreground">
              Edit subjects, lessons, and exercises
            </p>
          </button>
        </div>
      </div>
    </div>
  );
}
