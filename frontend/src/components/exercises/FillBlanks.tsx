"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { ExerciseTypeComponentProps, FillBlanksContent } from "./types";

const MARKER = "___";

/**
 * Exercice à trous. Le texte contient des marqueurs `___` ; on rend un champ par
 * trou et on émet `{ blanks: string[] }` dans l'ordre.
 */
export function FillBlanks({
  question,
  content,
  emoji,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
}: ExerciseTypeComponentProps<FillBlanksContent>) {
  const segments = content.text.split(MARKER);
  const blankCount = segments.length - 1;
  const [values, setValues] = useState<string[]>(() =>
    Array(blankCount).fill("")
  );

  const update = (index: number, value: string) => {
    if (disabled) return;
    const next = [...values];
    next[index] = value;
    setValues(next);
    onAnswer(next.every((v) => v.trim().length > 0) ? { blanks: next } : null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        {emoji && <span className="text-4xl">{emoji}</span>}
        <h2 className="text-xl font-bold text-fun-text sm:text-2xl">
          {question}
        </h2>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-1 rounded-2xl bg-fun-sky-light p-6 text-2xl font-bold text-fun-text">
        {segments.map((segment, i) => (
          <span key={i} className="flex items-center gap-1">
            <span>{segment}</span>
            {i < blankCount && (
              <input
                type="text"
                value={values[i]}
                onChange={(e) => update(i, e.target.value)}
                disabled={disabled}
                maxLength={4}
                aria-label={`Trou ${i + 1}`}
                className={cn(
                  "h-12 w-16 rounded-xl border-2 border-fun-border bg-white text-center text-2xl font-bold text-fun-text outline-none focus:border-fun-sky",
                  showResult &&
                    isCorrect &&
                    "border-fun-green bg-fun-green-light",
                  showResult &&
                    isCorrect === false &&
                    "border-fun-red bg-fun-red-light"
                )}
              />
            )}
          </span>
        ))}
      </div>
    </div>
  );
}
