"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { resolveMediaSrc } from "@/lib/media";
import type {
  ExerciseTypeComponentProps,
  MultipleChoiceContent,
} from "./types";

/**
 * QCM. Émet `{ option_ids: string[] }`.
 * Réponse unique par défaut ; multiple si `content.multiple`.
 */
export function MultipleChoice({
  question,
  content,
  emoji,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
}: ExerciseTypeComponentProps<MultipleChoiceContent>) {
  const multiple = content.multiple ?? false;
  const [selected, setSelected] = useState<string[]>([]);

  const emit = (ids: string[]) => {
    setSelected(ids);
    onAnswer(ids.length > 0 ? { option_ids: ids } : null);
  };

  const toggle = (id: string) => {
    if (disabled) return;
    if (multiple) {
      emit(
        selected.includes(id)
          ? selected.filter((x) => x !== id)
          : [...selected, id]
      );
    } else {
      emit([id]);
    }
  };

  // Layout « image d'abord » pour les non-lecteurs dès qu'une option est illustrée.
  const hasImages = content.options.some((o) => o.image);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        {emoji && <span className="text-4xl">{emoji}</span>}
        <h2 className="text-xl font-bold text-fun-text sm:text-2xl">
          {question}
        </h2>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-2">
        {content.options.map((option) => {
          const isSelected = selected.includes(option.id);
          const img = resolveMediaSrc(option.image);
          const stateClasses = cn(
            "border-fun-border bg-white text-fun-text hover:border-fun-sky",
            isSelected && !showResult && "border-fun-sky bg-fun-sky-light",
            showResult &&
              isSelected &&
              isCorrect &&
              "border-fun-green bg-fun-green-light",
            showResult &&
              isSelected &&
              isCorrect === false &&
              "border-fun-red bg-fun-red-light",
            disabled && "cursor-not-allowed"
          );

          if (hasImages) {
            return (
              <button
                key={option.id}
                type="button"
                onClick={() => toggle(option.id)}
                disabled={disabled}
                className={cn(
                  "flex flex-col items-center gap-2 rounded-2xl border-2 p-3 text-center text-base font-bold transition-all active:scale-95",
                  stateClasses
                )}
              >
                {img ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={img}
                    alt={option.text}
                    className="h-28 w-28 object-contain sm:h-32 sm:w-32"
                  />
                ) : (
                  <span className="flex h-28 w-28 items-center justify-center text-4xl sm:h-32 sm:w-32">
                    {option.text}
                  </span>
                )}
                <span>{option.text}</span>
              </button>
            );
          }

          return (
            <button
              key={option.id}
              type="button"
              onClick={() => toggle(option.id)}
              disabled={disabled}
              className={cn(
                "col-span-2 flex min-h-[56px] items-center gap-3 rounded-2xl border-2 px-4 py-3 text-left text-lg font-semibold transition-all active:scale-95 sm:col-span-1",
                stateClasses
              )}
            >
              <span>{option.text}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
