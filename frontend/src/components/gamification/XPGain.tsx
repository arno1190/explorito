"use client";

import { useEffect, useState } from "react";

interface XPGainProps {
  xp: number;
  onComplete?: () => void;
}

export function XPGain({ xp, onComplete }: XPGainProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      onComplete?.();
    }, 1200);
    return () => clearTimeout(timer);
  }, [onComplete]);

  if (!visible) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center">
      <span
        className="animate-xp-float text-4xl font-extrabold drop-shadow-lg"
        style={{
          color: "#f59e0b",
          textShadow: "0 2px 8px rgba(245, 158, 11, 0.5)",
        }}
      >
        +{xp} XP
      </span>
      <style jsx>{`
        @keyframes xp-float {
          0% {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
          60% {
            opacity: 1;
            transform: translateY(-60px) scale(1.2);
          }
          100% {
            opacity: 0;
            transform: translateY(-120px) scale(0.9);
          }
        }
        .animate-xp-float {
          animation: xp-float 1.2s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
