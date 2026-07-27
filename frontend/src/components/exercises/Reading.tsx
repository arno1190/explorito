"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { ExerciseTypeComponentProps, ReadingContent } from "./types";

/**
 * Bloc de lecture (compréhension / leçon). Pas de bonne réponse : lire le texte
 * puis "J'ai lu" émet `{ read: true }` (toujours validé). Les questions de
 * compréhension sont des exercices suivants dans la même leçon.
 */
export function Reading({
  question,
  content,
  emoji,
  onAnswer,
  disabled = false,
}: ExerciseTypeComponentProps<ReadingContent>) {
  const [read, setRead] = useState(false);

  const markRead = () => {
    if (disabled) return;
    setRead(true);
    onAnswer({ read: true });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        {emoji && <span className="text-4xl">{emoji}</span>}
        <h2 className="text-xl font-bold text-fun-text sm:text-2xl">
          {question}
        </h2>
      </div>

      {content.image && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={content.image}
          alt=""
          className="mx-auto max-h-56 rounded-2xl object-contain"
        />
      )}

      <div className="whitespace-pre-line rounded-2xl bg-fun-sun-light p-5 text-lg leading-relaxed text-fun-text">
        {content.text}
      </div>

      <div className="flex justify-center">
        <button
          type="button"
          onClick={markRead}
          disabled={disabled}
          className={cn(
            "min-h-[48px] rounded-2xl px-6 py-3 text-lg font-bold transition-all active:scale-95",
            read
              ? "bg-fun-green-light text-fun-green-dark"
              : "bg-fun-green text-white hover:bg-fun-green-dark",
            disabled && "cursor-not-allowed opacity-60"
          )}
        >
          {read ? "Bien lu ✓" : "J'ai lu →"}
        </button>
      </div>
    </div>
  );
}
