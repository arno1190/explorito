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
        "flex items-center gap-3 p-4 bg-gradient-to-r from-fun-sun-light to-fun-red-light rounded-2xl",
        className
      )}
    >
      <div className="bg-fun-sun rounded-full p-3">
        <Flame className="h-6 w-6 text-white fill-white" />
      </div>
      <div>
        <div className="font-bold text-2xl text-fun-text">
          {currentStreak} jour{currentStreak !== 1 ? "s" : ""}
        </div>
        <div className="text-sm text-fun-text-muted">
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
