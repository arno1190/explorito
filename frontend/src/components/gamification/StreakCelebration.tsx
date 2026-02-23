"use client";

import { useEffect, useState } from "react";

interface StreakCelebrationProps {
  streakDays: number;
  onClose?: () => void;
}

const milestones = [3, 7, 14, 30];

export function StreakCelebration({
  streakDays,
  onClose,
}: StreakCelebrationProps) {
  const [visible, setVisible] = useState(true);

  const isMilestone = milestones.includes(streakDays);

  useEffect(() => {
    if (!isMilestone) {
      setVisible(false);
      onClose?.();
      return;
    }
    const timer = setTimeout(() => {
      setVisible(false);
      onClose?.();
    }, 3000);
    return () => clearTimeout(timer);
  }, [isMilestone, onClose]);

  if (!visible || !isMilestone) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="rounded-3xl bg-gradient-to-b from-fun-sun to-fun-red p-8 text-center candy-shadow-lg animate-[candy-pop_0.5s_ease-out_forwards]">
        <div className="mb-2 text-7xl animate-[candy-wiggle_0.8s_ease-in-out_infinite]">
          🔥
        </div>
        <h2 className="mb-2 text-4xl font-extrabold text-white drop-shadow-lg">
          {streakDays} jours !
        </h2>
        <p className="text-lg font-semibold text-fun-sun-light">
          Super série ! Continue comme ça !
        </p>
        <button
          onClick={() => {
            setVisible(false);
            onClose?.();
          }}
          className="mt-4 rounded-xl bg-white/20 px-6 py-2 text-sm font-bold text-white hover:bg-white/30"
        >
          Merci !
        </button>
      </div>
    </div>
  );
}
