"use client";

import { useEffect } from "react";
import { useSound } from "@/hooks/useSound";
import { cn } from "@/lib/utils";

interface ExerciseFeedbackProps {
  isCorrect: boolean;
  message?: string;
  onNext: () => void;
}

const correctMessages = [
  "Bravo, c'est la bonne reponse !",
  "Super, bien joue !",
  "Excellent travail !",
  "Genial, tu as tout bon !",
  "Fantastique !",
];

const wrongMessages = [
  "Pas tout a fait, essaie encore !",
  "Presque ! Reflechis bien.",
  "Ce n'est pas ca, mais tu peux y arriver !",
  "Continue, tu vas trouver !",
];

function pickRandom(arr: string[]): string {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function ExerciseFeedback({
  isCorrect,
  message,
  onNext,
}: ExerciseFeedbackProps) {
  const { play } = useSound();

  useEffect(() => {
    play(isCorrect ? "correct" : "wrong");
  }, [isCorrect, play]);

  const displayMessage =
    message ||
    (isCorrect ? pickRandom(correctMessages) : pickRandom(wrongMessages));

  return (
    <div
      className={cn(
        "animate-[feedback-slide-up_0.4s_ease-out] rounded-2xl p-6 text-center shadow-lg",
        isCorrect
          ? "bg-candy-green-light border-4 border-candy-green"
          : "bg-candy-orange-light border-4 border-candy-orange"
      )}
    >
      <div
        className={cn(
          "mb-3 text-6xl",
          isCorrect
            ? "animate-[candy-pop_0.6s_ease-out]"
            : "animate-[candy-shake_0.5s_ease-in-out]"
        )}
      >
        {isCorrect ? "✅" : "💪"}
      </div>
      <h3
        className={cn(
          "text-2xl font-extrabold mb-2",
          isCorrect ? "text-candy-green" : "text-candy-orange"
        )}
      >
        {isCorrect ? "Bravo !" : "Oups !"}
      </h3>
      <p
        className={cn(
          "text-lg font-semibold mb-4",
          isCorrect ? "text-candy-green" : "text-candy-orange"
        )}
      >
        {displayMessage}
      </p>
      <button
        onClick={onNext}
        className={cn(
          "rounded-xl px-8 py-3 text-lg font-bold text-white transition-transform hover:scale-105 active:scale-95 shadow-md",
          isCorrect
            ? "bg-candy-green hover:bg-emerald-600"
            : "bg-candy-orange hover:bg-orange-600"
        )}
      >
        {isCorrect ? "Continuer" : "Reessayer"}
      </button>
    </div>
  );
}
