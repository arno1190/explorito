"use client";

import { useAuth } from "@/lib/auth";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminUsersPage() {
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
        <h1 className="text-3xl font-bold">User Management</h1>
        <p className="text-muted-foreground">
          Create, edit, and delete users of all types
        </p>
      </div>

      <div className="rounded-lg border p-6">
        <p className="text-muted-foreground">
          User management interface coming soon...
        </p>
        <p className="text-sm text-muted-foreground mt-2">
          This will include functionality to:
        </p>
        <ul className="list-disc list-inside text-sm text-muted-foreground mt-2 space-y-1">
          <li>View all users (admins, parents, children)</li>
          <li>Create new users of any type</li>
          <li>Edit user details</li>
          <li>Delete users</li>
          <li>Manage user permissions</li>
        </ul>
      </div>
    </div>
  );
}
