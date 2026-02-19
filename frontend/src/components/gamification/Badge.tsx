"use client";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Award, Lock } from "lucide-react";
import type { Achievement } from "@/types";

interface BadgeProps {
  achievement: Achievement;
  earned?: boolean;
  earnedAt?: string;
  className?: string;
}

export function Badge({
  achievement,
  earned = false,
  earnedAt,
  className,
}: BadgeProps) {
  return (
    <Card
      className={cn(
        "p-4 transition-all",
        earned ? "border-2 hover:shadow-lg" : "opacity-50 grayscale",
        className
      )}
      style={earned ? { borderColor: achievement.color } : undefined}
    >
      <div className="flex flex-col items-center gap-3">
        {earned ? (
          <div
            className="p-4 rounded-full"
            style={{ backgroundColor: `${achievement.color}20` }}
          >
            <Award className="h-8 w-8" style={{ color: achievement.color }} />
          </div>
        ) : (
          <div className="p-4 rounded-full bg-candy-purple-light">
            <Lock className="h-8 w-8 text-candy-text-muted" />
          </div>
        )}

        <div className="text-center">
          <h3 className="font-bold text-lg">{achievement.name}</h3>
          <p className="text-sm text-candy-text-muted mt-1">
            {achievement.description}
          </p>

          {earned && earnedAt && (
            <p className="text-xs text-candy-text-muted mt-2">
              Obtenu le {new Date(earnedAt).toLocaleDateString("fr-FR")}
            </p>
          )}

          {!earned && (
            <p className="text-xs text-candy-text-muted mt-2">
              {achievement.requirement}
            </p>
          )}
        </div>

        <div
          className={cn(
            "px-3 py-1 rounded-full text-sm font-semibold",
            earned
              ? "bg-candy-yellow-light text-candy-text"
              : "bg-candy-surface text-candy-text-muted"
          )}
        >
          {achievement.points} pts
        </div>
      </div>
    </Card>
  );
}
