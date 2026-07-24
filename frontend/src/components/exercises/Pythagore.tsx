"use client";

import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import type { ExerciseTypeComponentProps, PythagoreContent } from "./types";

interface Cell {
  a: number;
  b: number;
  key: string;
}

/**
 * Mini-jeu des tables de multiplication. On tire `content.blanks` cases parmi
 * les tables demandées et on émet `{ cells: { "AxB": number } }`.
 */
export function Pythagore({
  question,
  content,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
}: ExerciseTypeComponentProps<PythagoreContent>) {
  const cells = useMemo<Cell[]>(() => {
    const all: Cell[] = [];
    for (const a of content.tables) {
      for (let b = 1; b <= 10; b++) {
        all.push({ a, b, key: `${a}x${b}` });
      }
    }
    // Mélange déterministe léger puis découpe au nombre de trous demandé.
    const shuffled = [...all].sort((x, y) => x.a * 7 + x.b - (y.a * 7 + y.b));
    const count = Math.min(content.blanks ?? 5, shuffled.length);
    return shuffled.slice(0, count);
  }, [content.tables, content.blanks]);

  const [values, setValues] = useState<Record<string, string>>({});

  const update = (key: string, value: string) => {
    if (disabled) return;
    const next = { ...values, [key]: value };
    setValues(next);
    const allFilled = cells.every((c) => (next[c.key] ?? "").trim().length > 0);
    if (!allFilled) {
      onAnswer(null);
      return;
    }
    const parsed: Record<string, number> = {};
    for (const c of cells) parsed[c.key] = Number.parseInt(next[c.key], 10);
    onAnswer({ cells: parsed });
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-fun-text sm:text-2xl">
        {question}
      </h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {cells.map((c) => (
          <div
            key={c.key}
            className="flex items-center gap-2 rounded-2xl bg-fun-sun-light px-4 py-3 text-2xl font-bold text-fun-text"
          >
            <span>
              {c.a} × {c.b} =
            </span>
            <input
              type="number"
              inputMode="numeric"
              value={values[c.key] ?? ""}
              onChange={(e) => update(c.key, e.target.value)}
              disabled={disabled}
              aria-label={`${c.a} fois ${c.b}`}
              className={cn(
                "h-12 w-20 rounded-xl border-2 border-fun-border bg-white text-center text-2xl font-bold outline-none focus:border-fun-sun",
                showResult &&
                  isCorrect &&
                  "border-fun-green bg-fun-green-light",
                showResult &&
                  isCorrect === false &&
                  "border-fun-red bg-fun-red-light"
              )}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
