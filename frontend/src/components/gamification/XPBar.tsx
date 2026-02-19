"use client";

import { Progress } from "@/components/ui/progress";
import { Star } from "lucide-react";

interface XPBarProps {
  currentXP: number;
  nextLevelXP: number;
  level: number;
  className?: string;
}

export function XPBar({
  currentXP,
  nextLevelXP,
  level,
  className,
}: XPBarProps) {
  const percentage = (currentXP / nextLevelXP) * 100;

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="bg-candy-yellow rounded-full p-2">
            <Star className="h-5 w-5 text-candy-text fill-candy-yellow" />
          </div>
          <span className="font-bold text-lg">Niveau {level}</span>
        </div>
        <span className="text-sm text-candy-text-muted">
          {currentXP} / {nextLevelXP} XP
        </span>
      </div>
      <Progress value={percentage} className="h-3" />
    </div>
  );
}
