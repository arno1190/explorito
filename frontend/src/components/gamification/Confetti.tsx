"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface ConfettiProps {
  show: boolean;
  duration?: number;
  onComplete?: () => void;
}

export function Confetti({ show, duration = 3000, onComplete }: ConfettiProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (show) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        onComplete?.();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [show, duration, onComplete]);

  if (!visible) return null;

  const confettiPieces = Array.from({ length: 50 }, (_, i) => {
    const left = Math.random() * 100;
    const animationDuration = 2 + Math.random() * 2;
    const animationDelay = Math.random() * 3;
    const colors = [
      "bg-fun-green",
      "bg-fun-violet",
      "bg-fun-sun",
      "bg-fun-sky",
      "bg-fun-green-dark",
    ];
    const color = colors[Math.floor(Math.random() * colors.length)];

    return (
      <div
        key={i}
        className={cn("absolute w-2 h-2 rounded-full", color)}
        style={{
          left: `${left}%`,
          top: "-10px",
          animation: `confetti-fall ${animationDuration}s ease-in ${animationDelay}s forwards`,
        }}
      />
    );
  });

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {confettiPieces}
    </div>
  );
}
