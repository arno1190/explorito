"use client";

import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { resolveMediaSrc } from "@/lib/media";
import type {
  ExerciseTypeComponentProps,
  McqOption,
  MultipleChoiceContent,
} from "./types";

/** Mélange (Fisher-Yates) une copie du tableau. */
function shuffled<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

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

  // Ordre d'affichage mélangé une fois par question : la bonne réponse n'est plus
  // à une position prévisible (sinon un enfant « clique toujours la 1re/2e »).
  // La correction se fait par `id`, donc réordonner l'affichage est sans risque.
  const options: McqOption[] = useMemo(
    () => shuffled(content.options),
    [content]
  );

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

  // Une option est « visuelle » (pas de lecture requise) si elle porte une image,
  // une pastille de couleur, ou un texte fait uniquement d'emojis/de symboles.
  const isGlyph = (t: string) => t.length > 0 && !/\p{L}\p{L}/u.test(t);
  const useTiles = options.some((o) => o.image || o.color || isGlyph(o.text));

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        {emoji && <span className="text-4xl">{emoji}</span>}
        <h2 className="text-xl font-bold text-fun-text sm:text-2xl">
          {question}
        </h2>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-2">
        {options.map((option) => {
          const isSelected = selected.includes(option.id);
          const img = resolveMediaSrc(option.image);
          const glyph = !option.image && !option.color && isGlyph(option.text);
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

          if (useTiles) {
            return (
              <button
                key={option.id}
                type="button"
                onClick={() => toggle(option.id)}
                disabled={disabled}
                aria-label={option.text}
                className={cn(
                  "flex min-h-[8rem] flex-col items-center justify-center gap-2 rounded-2xl border-2 p-3 text-center text-base font-bold transition-all active:scale-95",
                  stateClasses
                )}
              >
                {img ? (
                  <>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={img}
                      alt={option.text}
                      className="h-28 w-28 object-contain sm:h-32 sm:w-32"
                    />
                    <span>{option.text}</span>
                  </>
                ) : option.color ? (
                  <span
                    className="h-24 w-24 rounded-2xl border-2 border-black/10 sm:h-28 sm:w-28"
                    style={{ backgroundColor: option.color }}
                  />
                ) : (
                  // Options emoji (ex. quantités « 🐱🐱 ») : grand rendu, pas de texte.
                  <span className="flex max-w-full flex-wrap items-center justify-center gap-0.5 text-4xl leading-tight sm:text-5xl">
                    {option.text}
                  </span>
                )}
                {!img && !glyph && !option.color && <span>{option.text}</span>}
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
