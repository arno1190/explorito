"use client";

import { Flame } from "lucide-react";
import { cn } from "@/lib/utils";

interface StreakProps {
  currentStreak: number;
  longestStreak?: number;
  className?: string;
}

export function Streak({
  currentStreak,
  longestStreak,
  className,
}: StreakProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 p-4 bg-gradient-to-r from-orange-100 to-red-100 rounded-lg",
        className
      )}
    >
      <div className="bg-orange-500 rounded-full p-3">
        <Flame className="h-6 w-6 text-white fill-white" />
      </div>
      <div>
        <div className="font-bold text-2xl text-orange-900">
          {currentStreak} jour{currentStreak !== 1 ? "s" : ""}
        </div>
        <div className="text-sm text-orange-700">
          {longestStreak && (
            <span>
              Record: {longestStreak} jour{longestStreak !== 1 ? "s" : ""}
            </span>
          )}
          {!longestStreak && <span>Continue comme ça!</span>}
        </div>
      </div>
    </div>
  );
}
