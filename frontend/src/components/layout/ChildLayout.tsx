"use client";

import { useAuth } from "@/lib/auth";
import { Header } from "./Header";
import { BottomNav } from "./BottomNav";

export function ChildLayout({ children }: { children: React.ReactNode }) {
  const { loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-candy-surface">
        <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-candy-purple-light border-t-candy-purple"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-candy-surface">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-6 pb-20 md:pb-6">
        {children}
      </main>
      <BottomNav />
    </div>
  );
}
