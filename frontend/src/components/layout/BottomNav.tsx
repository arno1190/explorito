"use client";

import { usePathname, useRouter } from "next/navigation";
import { Gamepad2, BookOpen, LayoutDashboard } from "lucide-react";

const tabs = [
  { href: "/play", icon: Gamepad2, label: "Jouer" },
  { href: "/subjects", icon: BookOpen, label: "Matières" },
  { href: "/dashboard", icon: LayoutDashboard, label: "Tableau" },
];

export function BottomNav() {
  const pathname = usePathname();
  const router = useRouter();

  if (pathname.startsWith("/admin")) return null;

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-sm border-t-2 border-fun-border md:hidden">
      <div className="flex items-center justify-around py-2 px-4 pb-[env(safe-area-inset-bottom,8px)]">
        {tabs.map((tab) => {
          const isActive =
            pathname === tab.href || pathname.startsWith(tab.href + "/");
          return (
            <button
              key={tab.href}
              onClick={() => router.push(tab.href)}
              className={`flex flex-col items-center justify-center min-w-[64px] min-h-[48px] rounded-xl transition-all duration-200 ${
                isActive
                  ? "text-fun-green bg-fun-green-light scale-105"
                  : "text-fun-text-muted hover:text-fun-green"
              }`}
            >
              <tab.icon className="h-6 w-6" />
              <span className="text-xs font-semibold mt-0.5">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
