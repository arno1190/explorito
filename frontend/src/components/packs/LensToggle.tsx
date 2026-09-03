"use client";

import type { PackLensUpdateLens } from "@/lib/api/model";

export type PackLens = PackLensUpdateLens;

interface LensToggleProps {
  value: PackLens;
  onChange: (lens: PackLens) => void;
  /** Vrai pendant l'enregistrement : la bascule reste lisible, juste inerte. */
  disabled?: boolean;
}

const OPTIONS: { lens: PackLens; label: string; emoji: string }[] = [
  { lens: "themes", label: "Thèmes", emoji: "🎒" },
  { lens: "matieres", label: "Matières", emoji: "📚" },
];

export function LensToggle({ value, onChange, disabled }: LensToggleProps) {
  return (
    <div
      role="tablist"
      aria-label="Affichage du chemin"
      className="inline-flex w-full max-w-xs rounded-2xl border-2 border-fun-border bg-white p-1 candy-shadow"
    >
      {OPTIONS.map((option) => {
        const active = option.lens === value;
        return (
          <button
            key={option.lens}
            type="button"
            role="tab"
            aria-selected={active}
            disabled={disabled}
            onClick={() => {
              if (!active) onChange(option.lens);
            }}
            className={`min-h-[48px] flex-1 rounded-xl px-3 text-base font-extrabold transition-all active:scale-95 ${
              active
                ? "bg-fun-green text-white candy-shadow"
                : "text-fun-text-muted hover:bg-fun-green-light"
            } ${disabled ? "cursor-wait" : ""}`}
          >
            <span aria-hidden="true">{option.emoji}</span> {option.label}
          </button>
        );
      })}
    </div>
  );
}
