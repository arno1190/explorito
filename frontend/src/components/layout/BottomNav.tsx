"use client";

import { usePathname, useRouter } from "next/navigation";
import {
  Gamepad2,
  BookOpen,
  LayoutDashboard,
  BookMarked,
  Compass,
  Library,
  Upload,
} from "lucide-react";
import { useActingRole } from "@/lib/navigation";

const CHILD_TABS = [
  { href: "/play", icon: Gamepad2, label: "Jouer" },
  { href: "/subjects", icon: BookOpen, label: "Matières" },
  { href: "/decouvrir", icon: Compass, label: "Découvrir" },
  { href: "/collection", icon: BookMarked, label: "Collections" },
];

const PARENT_TABS = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Tableau" },
  { href: "/bibliotheque", icon: Library, label: "Bibliothèque" },
  { href: "/contributions", icon: Upload, label: "Mes leçons" },
];

export function BottomNav() {
  const pathname = usePathname();
  const router = useRouter();
  const actingRole = useActingRole();

  // Admin works from the admin section; no kid tab bar there.
  if (!actingRole || actingRole === "admin") return null;

  const tabs = actingRole === "parent" ? PARENT_TABS : CHILD_TABS;
  // A single destination doesn't warrant a tab bar.
  if (tabs.length < 2) return null;

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
              <span className="mt-0.5 whitespace-nowrap text-xs font-semibold">
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
