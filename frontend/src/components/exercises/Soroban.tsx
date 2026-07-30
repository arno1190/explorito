"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { ExerciseTypeComponentProps, SorobanContent } from "./types";

/**
 * Boulier japonais (soroban) dessiné en SVG, sans dépendance externe.
 *
 * Chaque tige a 1 boule « du ciel » (vaut 5, en haut de la barre) et 4 boules
 * « de terre » (valent 1, sous la barre). Une boule compte quand elle touche la
 * barre. Deux modes :
 * - ``read``  : le boulier affiche `value`, l'enfant lit et écrit le nombre.
 * - ``build`` : l'enfant déplace les boules pour construire `value`.
 */

interface ColState {
  heaven: boolean;
  earth: number; // 0..4
}

// Géométrie (unités SVG).
const COL_W = 60;
const MARGIN_X = 18;
const BEAD_RX = 24;
const BEAD_RY = 14;
const BAR_Y = 74;
const HEAVEN_TOP_Y = 29;
const HEAVEN_BOTTOM_Y = 59;
const EARTH_CENTERS = [97, 127, 157, 187, 217]; // 5 emplacements (4 boules + 1 espace)
const HEIGHT = 246;

function colValue(c: ColState): number {
  return (c.heaven ? 5 : 0) + c.earth;
}

function digitToCol(d: number): ColState {
  return { heaven: d >= 5, earth: d % 5 };
}

function Bead({
  cx,
  cy,
  active,
  color,
  onClick,
  interactive,
}: {
  cx: number;
  cy: number;
  active: boolean;
  color: string;
  onClick?: () => void;
  interactive: boolean;
}) {
  return (
    <ellipse
      cx={cx}
      cy={cy}
      rx={BEAD_RX}
      ry={BEAD_RY}
      fill={color}
      stroke="#042C60"
      strokeWidth={2}
      opacity={active ? 1 : 0.4}
      onClick={onClick}
      style={{ cursor: interactive ? "pointer" : "default" }}
    />
  );
}

function Column({
  x,
  col,
  interactive,
  onHeaven,
  onEarth,
}: {
  x: number;
  col: ColState;
  interactive: boolean;
  onHeaven?: () => void;
  onEarth?: (p: number) => void;
}) {
  // Emplacement d'une boule de terre p (1 = près de la barre) : montée si p<=earth.
  const slotForBead = (p: number) => (p <= col.earth ? p - 1 : p);
  return (
    <g>
      {/* Tige */}
      <line x1={x} y1={20} x2={x} y2={232} stroke="#CBD5E1" strokeWidth={4} />
      {/* Boule du ciel (5) */}
      <Bead
        cx={x}
        cy={col.heaven ? HEAVEN_BOTTOM_Y : HEAVEN_TOP_Y}
        active={col.heaven}
        color="#F3C35B"
        interactive={interactive}
        onClick={interactive ? onHeaven : undefined}
      />
      {/* Boules de terre (1) */}
      {[1, 2, 3, 4].map((p) => (
        <Bead
          key={p}
          cx={x}
          cy={EARTH_CENTERS[slotForBead(p)]}
          active={p <= col.earth}
          color="#1CAFF6"
          interactive={interactive}
          onClick={interactive ? () => onEarth?.(p) : undefined}
        />
      ))}
    </g>
  );
}

export function Soroban({
  question,
  content,
  emoji,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
}: ExerciseTypeComponentProps<SorobanContent>) {
  const build = content.mode === "build";
  const columns = Math.max(
    1,
    (content.columns ?? String(content.value).length) || 1
  );
  const width = MARGIN_X * 2 + columns * COL_W;
  const colX = (c: number) => MARGIN_X + COL_W / 2 + c * COL_W;

  // --- État ---
  // read : colonnes figées dérivées de value. build : colonnes manipulables (à 0).
  const readCols: ColState[] = String(content.value)
    .padStart(columns, "0")
    .split("")
    .map((d) => digitToCol(Number(d)));

  const [cols, setCols] = useState<ColState[]>(() =>
    Array.from({ length: columns }, () => ({ heaven: false, earth: 0 }))
  );
  const [typed, setTyped] = useState("");

  const built = cols.reduce(
    (acc, c, i) => acc + colValue(c) * 10 ** (columns - 1 - i),
    0
  );

  const applyCols = (next: ColState[]) => {
    if (disabled) return;
    setCols(next);
    const value = next.reduce(
      (acc, c, i) => acc + colValue(c) * 10 ** (columns - 1 - i),
      0
    );
    onAnswer({ value });
  };

  const toggleHeaven = (i: number) =>
    applyCols(
      cols.map((c, idx) => (idx === i ? { ...c, heaven: !c.heaven } : c))
    );
  const setEarth = (i: number, p: number) =>
    applyCols(
      cols.map((c, idx) =>
        idx === i ? { ...c, earth: p <= c.earth ? p - 1 : p } : c
      )
    );
  const reset = () =>
    applyCols(
      Array.from({ length: columns }, () => ({ heaven: false, earth: 0 }))
    );

  const onType = (raw: string) => {
    if (disabled) return;
    const clean = raw.replace(/[^0-9]/g, "");
    setTyped(clean);
    onAnswer(clean.length > 0 ? { value: Number(clean) } : null);
  };

  const display = build ? cols : readCols;

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-3">
        {emoji && <span className="text-4xl">{emoji}</span>}
        <h2 className="text-xl font-bold text-fun-text sm:text-2xl">
          {question}
        </h2>
      </div>

      {/* Boulier */}
      <div className="flex justify-center">
        <svg
          viewBox={`0 0 ${width} ${HEIGHT}`}
          className="w-full"
          style={{ maxWidth: Math.min(width * 1.6, 520) }}
          role="img"
          aria-label="Boulier"
        >
          {/* Cadre */}
          <rect
            x={4}
            y={8}
            width={width - 8}
            height={HEIGHT - 16}
            rx={16}
            fill="#FFFFFF"
            stroke="#E2E8F0"
            strokeWidth={4}
          />
          {/* Barre de comptage */}
          <rect
            x={8}
            y={BAR_Y - 3}
            width={width - 16}
            height={6}
            rx={3}
            fill="#042C60"
          />
          {display.map((c, i) => (
            <Column
              key={i}
              x={colX(i)}
              col={c}
              interactive={build && !disabled}
              onHeaven={() => toggleHeaven(i)}
              onEarth={(p) => setEarth(i, p)}
            />
          ))}
          {/* Repères de colonnes (unités / dizaines…) pour plusieurs tiges */}
          {columns > 1 &&
            display.map((_, i) => (
              <text
                key={`lbl-${i}`}
                x={colX(i)}
                y={HEIGHT - 2}
                textAnchor="middle"
                fontSize={12}
                fontWeight={700}
                fill="#64748B"
              >
                {["u", "d", "c", "m"][columns - 1 - i] ?? ""}
              </text>
            ))}
        </svg>
      </div>

      {build ? (
        <div className="flex flex-col items-center gap-3">
          <div
            className={cn(
              "rounded-2xl px-6 py-3 text-2xl font-extrabold",
              showResult && isCorrect
                ? "bg-fun-green-light text-fun-green-dark"
                : showResult && isCorrect === false
                  ? "bg-fun-red-light text-fun-red"
                  : built === content.value
                    ? "bg-fun-green-light text-fun-green-dark"
                    : "bg-fun-sky-light text-fun-text"
            )}
          >
            Ton nombre : {built}
          </div>
          {!disabled && (
            <button
              type="button"
              onClick={reset}
              className="min-h-[44px] rounded-xl bg-fun-border px-4 py-2 text-sm font-bold text-fun-text active:scale-95"
            >
              ↺ Recommencer
            </button>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-center gap-3 rounded-2xl bg-fun-sky-light p-5">
          <span className="text-lg font-bold text-fun-text">
            Quel nombre&nbsp;?
          </span>
          <input
            type="text"
            inputMode="numeric"
            value={typed}
            onChange={(e) => onType(e.target.value)}
            disabled={disabled}
            aria-label="Ta réponse"
            placeholder="?"
            className={cn(
              "h-14 w-28 rounded-xl border-2 border-fun-border bg-white text-center text-3xl font-bold text-fun-text outline-none focus:border-fun-sky",
              showResult && isCorrect && "border-fun-green bg-fun-green-light",
              showResult &&
                isCorrect === false &&
                "border-fun-red bg-fun-red-light"
            )}
          />
        </div>
      )}
    </div>
  );
}
