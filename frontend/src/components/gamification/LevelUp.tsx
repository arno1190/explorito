"use client";

import { useEffect, useState } from "react";
import { useSound } from "@/hooks/useSound";

interface LevelUpProps {
  newLevel: number;
  onClose?: () => void;
}

export function LevelUp({ newLevel, onClose }: LevelUpProps) {
  const [visible, setVisible] = useState(true);
  const { play } = useSound();

  useEffect(() => {
    play("levelup");
  }, [play]);

  const handleClose = () => {
    setVisible(false);
    onClose?.();
  };

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      {/* Confetti particles */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="animate-confetti-fall absolute"
            style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 1}s`,
              animationDuration: `${1.5 + Math.random() * 1.5}s`,
              backgroundColor: [
                "#f59e0b",
                "#ef4444",
                "#3b82f6",
                "#10b981",
                "#8b5cf6",
                "#ec4899",
              ][i % 6],
              width: `${8 + Math.random() * 8}px`,
              height: `${8 + Math.random() * 8}px`,
              borderRadius: Math.random() > 0.5 ? "50%" : "2px",
            }}
          />
        ))}
      </div>

      {/* Star burst background */}
      <div className="animate-level-starburst absolute h-64 w-64 rounded-full bg-yellow-300/30 blur-3xl" />

      {/* Main card */}
      <div className="animate-level-pop relative rounded-3xl bg-gradient-to-b from-yellow-400 to-amber-500 p-10 text-center shadow-2xl">
        <div className="animate-level-star mb-4 text-7xl">⭐</div>
        <p className="mb-1 text-lg font-bold text-yellow-900/70">
          Nouveau niveau !
        </p>
        <h2 className="mb-2 text-6xl font-extrabold text-white drop-shadow-lg">
          Niveau {newLevel}
        </h2>
        <p className="mb-6 text-lg font-semibold text-yellow-100">
          Bravo, tu progresses super bien !
        </p>
        <button
          onClick={handleClose}
          className="rounded-full bg-white px-8 py-3 text-lg font-bold text-amber-600 shadow-lg transition-transform hover:scale-105 active:scale-95"
        >
          Continuer
        </button>
      </div>

      <style jsx>{`
        @keyframes level-pop {
          0% {
            opacity: 0;
            transform: scale(0.3) rotate(-10deg);
          }
          60% {
            transform: scale(1.1) rotate(2deg);
          }
          100% {
            opacity: 1;
            transform: scale(1) rotate(0deg);
          }
        }
        @keyframes level-star {
          0%,
          100% {
            transform: scale(1) rotate(0deg);
          }
          50% {
            transform: scale(1.2) rotate(15deg);
          }
        }
        @keyframes level-starburst {
          0% {
            opacity: 0;
            transform: scale(0.5);
          }
          50% {
            opacity: 1;
            transform: scale(1.5);
          }
          100% {
            opacity: 0.5;
            transform: scale(1);
          }
        }
        @keyframes confetti-fall {
          0% {
            opacity: 1;
            transform: translateY(-20px) rotate(0deg);
          }
          100% {
            opacity: 0;
            transform: translateY(100vh) rotate(720deg);
          }
        }
        .animate-level-pop {
          animation: level-pop 0.6s ease-out forwards;
        }
        .animate-level-star {
          animation: level-star 1.5s ease-in-out infinite;
        }
        .animate-level-starburst {
          animation: level-starburst 1s ease-out forwards;
        }
        .animate-confetti-fall {
          animation: confetti-fall 2s ease-in forwards;
        }
      `}</style>
    </div>
  );
}
