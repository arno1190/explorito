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
    const animationDelay = Math.random() * 3;
    const colors = [
      "bg-red-500",
      "bg-blue-500",
      "bg-green-500",
      "bg-yellow-500",
      "bg-purple-500",
      "bg-pink-500",
      "bg-orange-500",
    ];
    const color = colors[Math.floor(Math.random() * colors.length)];

    return (
      <div
        key={i}
        className={cn("absolute w-2 h-2 rounded-full animate-confetti", color)}
        style={{
          left: `${left}%`,
          animationDelay: `${animationDelay}s`,
          top: "-10px",
        }}
      />
    );
  });

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {confettiPieces}
      <style jsx>{`
        @keyframes confetti {
          0% {
            transform: translateY(0) rotate(0deg);
            opacity: 1;
          }
          100% {
            transform: translateY(100vh) rotate(720deg);
            opacity: 0;
          }
        }
        .animate-confetti {
          animation: confetti 3s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
