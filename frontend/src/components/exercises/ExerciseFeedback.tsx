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
        "animate-feedback-in rounded-3xl p-6 text-center shadow-lg",
        isCorrect
          ? "bg-green-100 border-4 border-green-400"
          : "bg-orange-50 border-4 border-orange-300"
      )}
    >
      <div
        className={cn(
          "mb-3 text-6xl",
          isCorrect ? "animate-feedback-bounce" : "animate-feedback-shake"
        )}
      >
        {isCorrect ? "✅" : "💪"}
      </div>
      <h3
        className={cn(
          "text-2xl font-extrabold mb-2",
          isCorrect ? "text-green-800" : "text-orange-800"
        )}
      >
        {isCorrect ? "Bravo !" : "Oups !"}
      </h3>
      <p
        className={cn(
          "text-lg font-semibold mb-4",
          isCorrect ? "text-green-700" : "text-orange-700"
        )}
      >
        {displayMessage}
      </p>
      <button
        onClick={onNext}
        className={cn(
          "rounded-full px-8 py-3 text-lg font-bold text-white transition-transform hover:scale-105 active:scale-95 shadow-md",
          isCorrect
            ? "bg-green-500 hover:bg-green-600"
            : "bg-orange-400 hover:bg-orange-500"
        )}
      >
        {isCorrect ? "Continuer" : "Reessayer"}
      </button>

      <style jsx>{`
        @keyframes feedback-in {
          0% {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
          }
          100% {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        @keyframes feedback-bounce {
          0%,
          100% {
            transform: scale(1);
          }
          30% {
            transform: scale(1.3);
          }
          60% {
            transform: scale(0.9);
          }
          80% {
            transform: scale(1.1);
          }
        }
        @keyframes feedback-shake {
          0%,
          100% {
            transform: translateX(0);
          }
          15% {
            transform: translateX(-8px);
          }
          30% {
            transform: translateX(8px);
          }
          45% {
            transform: translateX(-6px);
          }
          60% {
            transform: translateX(6px);
          }
          75% {
            transform: translateX(-3px);
          }
        }
        .animate-feedback-in {
          animation: feedback-in 0.4s ease-out forwards;
        }
        .animate-feedback-bounce {
          animation: feedback-bounce 0.6s ease-out;
        }
        .animate-feedback-shake {
          animation: feedback-shake 0.5s ease-out;
        }
      `}</style>
    </div>
  );
}
