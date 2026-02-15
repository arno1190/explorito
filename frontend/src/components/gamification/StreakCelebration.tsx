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
      <div className="animate-streak-pop rounded-3xl bg-gradient-to-b from-orange-400 to-red-500 p-8 text-center shadow-2xl">
        <div className="animate-streak-fire mb-2 text-7xl">🔥</div>
        <h2 className="mb-2 text-4xl font-extrabold text-white drop-shadow-lg">
          {streakDays} jours !
        </h2>
        <p className="text-lg font-semibold text-orange-100">
          Super série ! Continue comme ça !
        </p>
        <button
          onClick={() => {
            setVisible(false);
            onClose?.();
          }}
          className="mt-4 rounded-full bg-white/20 px-6 py-2 text-sm font-bold text-white hover:bg-white/30"
        >
          Merci !
        </button>
      </div>
      <style jsx>{`
        @keyframes streak-pop {
          0% {
            opacity: 0;
            transform: scale(0.5);
          }
          60% {
            transform: scale(1.1);
          }
          100% {
            opacity: 1;
            transform: scale(1);
          }
        }
        @keyframes streak-fire {
          0%,
          100% {
            transform: scale(1) rotate(0deg);
          }
          25% {
            transform: scale(1.15) rotate(-5deg);
          }
          50% {
            transform: scale(1.05) rotate(5deg);
          }
          75% {
            transform: scale(1.15) rotate(-3deg);
          }
        }
        .animate-streak-pop {
          animation: streak-pop 0.5s ease-out forwards;
        }
        .animate-streak-fire {
          animation: streak-fire 0.8s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
