"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { ExerciseTypeComponentProps, RevealContent } from "./types";

/**
 * Carte à révéler (blague). Pas de bonne réponse : révéler la chute émet une
 * réponse (toujours correcte côté serveur) `{ revealed: true }`.
 */
export function Reveal({
  content,
  emoji,
  onAnswer,
  disabled = false,
}: ExerciseTypeComponentProps<RevealContent>) {
  const [revealed, setRevealed] = useState(false);

  const reveal = () => {
    if (disabled) return;
    setRevealed(true);
    onAnswer({ revealed: true });
  };

  return (
    <div className="space-y-6 text-center">
      <div className="flex flex-col items-center gap-3">
        {emoji && <span className="text-5xl">{emoji}</span>}
        <h2 className="text-xl font-bold text-fun-text sm:text-2xl">
          {content.prompt}
        </h2>
      </div>

      {revealed ? (
        <div className="animate-[candy-pop_0.6s_ease-out] rounded-2xl bg-fun-sun-light p-6 text-2xl font-extrabold text-fun-text">
          {content.reveal}
        </div>
      ) : (
        <button
          type="button"
          onClick={reveal}
          disabled={disabled}
          className={cn(
            "min-h-[56px] rounded-2xl bg-fun-violet px-8 py-3 text-lg font-bold text-white transition-all active:scale-95",
            disabled && "cursor-not-allowed opacity-60"
          )}
        >
          Révéler la réponse 🎉
        </button>
      )}
    </div>
  );
}
