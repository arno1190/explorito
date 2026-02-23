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
        className="text-4xl font-extrabold drop-shadow-lg animate-[candy-float_1.2s_ease-out_forwards]"
        style={{
          color: "var(--fun-sun)",
          textShadow: "0 2px 8px rgba(243, 195, 91, 0.5)",
        }}
      >
        +{xp} XP
      </span>
    </div>
  );
}
