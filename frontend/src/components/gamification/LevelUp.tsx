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
            className="absolute"
            style={{
              left: `${Math.random() * 100}%`,
              animation: `confetti-fall ${1.5 + Math.random() * 1.5}s ease-in ${Math.random() * 1}s forwards`,
              backgroundColor: [
                "#58CC02",
                "#1CAFF6",
                "#F28DEE",
                "#F3C35B",
                "#45A302",
              ][i % 5],
              width: `${8 + Math.random() * 8}px`,
              height: `${8 + Math.random() * 8}px`,
              borderRadius: Math.random() > 0.5 ? "50%" : "2px",
            }}
          />
        ))}
      </div>

      {/* Star burst background */}
      <div className="absolute h-64 w-64 rounded-full bg-fun-sun/30 blur-3xl animate-[candy-glow_1s_ease-out_forwards]" />

      {/* Main card */}
      <div className="relative rounded-3xl bg-gradient-to-b from-fun-sun to-fun-violet p-10 text-center candy-shadow-lg animate-[candy-pop_0.6s_ease-out_forwards]">
        <div className="mb-4 text-7xl animate-[candy-wiggle_1.5s_ease-in-out_infinite]">
          ⭐
        </div>
        <p className="mb-1 text-lg font-bold text-white/70">Nouveau niveau !</p>
        <h2 className="mb-2 text-6xl font-extrabold text-white drop-shadow-lg">
          Niveau {newLevel}
        </h2>
        <p className="mb-6 text-lg font-semibold text-white/90">
          Bravo, tu progresses super bien !
        </p>
        <button
          onClick={handleClose}
          className="rounded-xl bg-white px-8 py-3 text-lg font-bold text-fun-green shadow-lg transition-transform hover:scale-105 active:scale-95"
        >
          Continuer
        </button>
      </div>
    </div>
  );
}
