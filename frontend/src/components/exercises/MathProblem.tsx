"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { ExerciseTypeComponentProps, MathProblemContent } from "./types";

/**
 * Problème de maths : énoncé (question) + saisie numérique.
 * Émet `{ value: number }` (le backend compare avec une tolérance).
 */
export function MathProblem({
  question,
  content,
  emoji,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
}: ExerciseTypeComponentProps<MathProblemContent>) {
  const [value, setValue] = useState("");

  const update = (raw: string) => {
    if (disabled) return;
    setValue(raw);
    const trimmed = raw.trim();
    onAnswer(trimmed.length > 0 ? { value: trimmed.replace(",", ".") } : null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3">
        {emoji && <span className="text-4xl">{emoji}</span>}
        <h2 className="text-xl font-bold text-fun-text sm:text-2xl">
          {question}
        </h2>
      </div>

      <div className="flex items-center justify-center gap-3 rounded-2xl bg-fun-sky-light p-6">
        <input
          type="text"
          inputMode="decimal"
          value={value}
          onChange={(e) => update(e.target.value)}
          disabled={disabled}
          aria-label="Ta réponse"
          placeholder="?"
          className={cn(
            "h-14 w-32 rounded-xl border-2 border-fun-border bg-white text-center text-3xl font-bold text-fun-text outline-none focus:border-fun-sky",
            showResult && isCorrect && "border-fun-green bg-fun-green-light",
            showResult &&
              isCorrect === false &&
              "border-fun-red bg-fun-red-light"
          )}
        />
        {content.unit && (
          <span className="text-2xl font-bold text-fun-text">
            {content.unit}
          </span>
        )}
      </div>
    </div>
  );
}
