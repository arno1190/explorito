"use client";

import { useState } from "react";
import { useSound } from "@/hooks/useSound";
import { cn } from "@/lib/utils";
import type {
  ExerciseTypeComponentProps,
  MusicNoteContent,
  NoteName,
} from "./types";

/**
 * Lecture de notes sur une portée dessinée en SVG, avec le son de chaque note
 * (synthèse Web Audio, aucun fichier). Deux clés : sol (2e ligne) et ut 3e
 * ligne (celle de l'alto). Deux modes :
 * - ``name``  : la note est affichée, l'enfant choisit son nom.
 * - ``place`` : l'enfant pose la note nommée (tap sur la portée ou flèches).
 *
 * Les positions sont en « marches » : 0 = 1re ligne du bas, 1 = 1er interligne,
 * 2 = 2e ligne… comme `staff_step` côté backend.
 */

const NAMES: NoteName[] = ["do", "ré", "mi", "fa", "sol", "la", "si"];
const LETTERS = "CDEFGAB";
const SEMITONES = [0, 2, 4, 5, 7, 9, 11];
// Note de la 1re ligne de chaque clé, en degrés diatoniques (octave*7 + lettre).
const BOTTOM_LINE = { sol: 4 * 7 + 2, ut3: 3 * 7 + 3 }; // mi4, fa3
// Couleur de chaque note (façon cloches de classe), du do au si.
const NOTE_COLORS = [
  "#EF4444",
  "#F97316",
  "#F3C35B",
  "#58CC02",
  "#1CAFF6",
  "#A855F7",
  "#F28DEE",
];

const W = 260;
const H = 220;
const STEP = 10;
const BOTTOM_Y = 150;
const MIN_STEP = -4;
const MAX_STEP = 12;
const NOTE_X = 165;
const NAVY = "#042C60";

const yOf = (step: number) => BOTTOM_Y - step * STEP;

function parsePitch(pitch: string): number {
  return Number(pitch[1]) * 7 + LETTERS.indexOf(pitch[0]);
}

function frequencyOf(diatonic: number): number {
  const octave = Math.floor(diatonic / 7);
  const midi = 12 * (octave + 1) + SEMITONES[diatonic % 7];
  return 440 * 2 ** ((midi - 69) / 12);
}

function TrebleClef() {
  return (
    <g>
      <path
        d="M 46 133 C 39 133, 37 123, 45 120 C 55 117, 62 128, 57 138 C 50 150, 28 147, 27 129 C 26 112, 45 100, 54 87 C 63 74, 62 52, 55 47 C 48 44, 43 58, 45 78 L 53 170 C 55 184, 42 189, 37 180"
        fill="none"
        stroke={NAVY}
        strokeWidth={3.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={39} cy={178} r={4.5} fill={NAVY} />
    </g>
  );
}

const C_LOBE =
  "M 3 0 L 8 -9 C 12 -16, 17 -20, 20 -18 C 30 -24, 28 -38, 18 -38 C 12 -38, 10 -34, 12 -31";

/** Clé d'ut : son milieu (pointe) est posé sur la ligne `step`. */
function CClef({ step }: { step: number }) {
  const lobe = (
    <>
      <path
        d={C_LOBE}
        fill="none"
        stroke={NAVY}
        strokeWidth={3.5}
        strokeLinecap="round"
      />
      <circle cx={14} cy={-30} r={4.5} fill={NAVY} />
    </>
  );
  return (
    <g transform={`translate(42, ${yOf(step)})`}>
      <rect x={-12} y={-40} width={7} height={80} fill={NAVY} />
      <rect x={-2} y={-40} width={2.5} height={80} fill={NAVY} />
      {lobe}
      <g transform="scale(1,-1)">{lobe}</g>
    </g>
  );
}

function LedgerLines({ step, x }: { step: number; x: number }) {
  const steps: number[] = [];
  for (let s = -2; s >= step; s -= 2) steps.push(s);
  for (let s = 10; s <= step; s += 2) steps.push(s);
  return (
    <>
      {steps.map((s) => (
        <line
          key={s}
          x1={x - 17}
          x2={x + 17}
          y1={yOf(s)}
          y2={yOf(s)}
          stroke={NAVY}
          strokeWidth={1.6}
        />
      ))}
    </>
  );
}

function NoteHead({
  step,
  x,
  color,
  label,
  labelColor,
  onClick,
}: {
  step: number;
  x: number;
  color: string;
  label?: string;
  labelColor?: string;
  onClick?: () => void;
}) {
  const y = yOf(step);
  return (
    <g onClick={onClick} style={{ cursor: onClick ? "pointer" : undefined }}>
      <LedgerLines step={step} x={x} />
      {/* `key` sur le step : l'animation rejoue à chaque déplacement. */}
      <g
        key={step}
        className="animate-[candy-pop_0.3s_ease-out]"
        style={{ transformBox: "fill-box", transformOrigin: "center" }}
      >
        <ellipse
          cx={x}
          cy={y}
          rx={10}
          ry={7.5}
          transform={`rotate(-20 ${x} ${y})`}
          fill={color}
          stroke={NAVY}
          strokeWidth={1.5}
        />
      </g>
      {label && (
        <text
          x={x}
          y={step < 2 ? y - 16 : y + 26}
          textAnchor="middle"
          fontSize={16}
          fontWeight={800}
          fill={labelColor ?? color}
          stroke="#FFFFFF"
          strokeWidth={3}
          paintOrder="stroke"
        >
          {label}
        </text>
      )}
    </g>
  );
}

export function MusicNote({
  question,
  content,
  emoji,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
}: ExerciseTypeComponentProps<MusicNoteContent>) {
  const { playFrequency } = useSound();
  const bottom = BOTTOM_LINE[content.clef] ?? BOTTOM_LINE.sol;
  const target = parsePitch(content.pitch);
  const targetStep = target - bottom;
  const targetName = NAMES[target % 7];
  const placing = content.mode === "place";
  const choices = content.choices?.length ? content.choices : NAMES;

  const [picked, setPicked] = useState<NoteName | null>(null);
  const [placed, setPlaced] = useState<number | null>(null);

  const playStep = (step: number) => playFrequency(frequencyOf(bottom + step));

  const pick = (name: NoteName) => {
    if (disabled) return;
    setPicked(name);
    // Le bouton chante sa note dans l'octave du do du milieu.
    playFrequency(frequencyOf(4 * 7 + NAMES.indexOf(name)));
    onAnswer({ name });
  };

  const place = (step: number) => {
    if (disabled) return;
    const clamped = Math.max(MIN_STEP, Math.min(MAX_STEP, step));
    setPlaced(clamped);
    playStep(clamped);
    onAnswer({ name: NAMES[(bottom + clamped) % 7] });
  };

  // Après correction en mode « place » : la bonne note apparaît en vert si l'enfant s'est trompé.
  const showSolution = placing && showResult && isCorrect === false;
  const placedName = placed === null ? null : NAMES[(bottom + placed) % 7];

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-3">
        {emoji && <span className="text-4xl">{emoji}</span>}
        <h2 className="text-xl font-bold text-fun-text sm:text-2xl">
          {question}
        </h2>
      </div>

      <div className="flex flex-col items-center gap-3">
        <span className="rounded-full bg-fun-violet-light px-4 py-1 text-sm font-bold text-fun-text">
          {content.clef === "ut3" ? "🎻 Clé d'ut 3e ligne" : "🎼 Clé de sol"}
        </span>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full max-w-[520px] rounded-2xl bg-white candy-shadow"
          role="img"
          aria-label={
            placing
              ? "Portée : touche une ligne ou un interligne pour poser la note"
              : "Portée avec une note à lire"
          }
        >
          {[0, 2, 4, 6, 8].map((s) => (
            <line
              key={s}
              x1={8}
              x2={W - 8}
              y1={yOf(s)}
              y2={yOf(s)}
              stroke={NAVY}
              strokeWidth={1.6}
            />
          ))}
          {content.clef === "ut3" ? <CClef step={4} /> : <TrebleClef />}

          {placing ? (
            <>
              {/* Zones de tap : une par ligne / interligne, sur toute la largeur utile. */}
              {!disabled &&
                Array.from(
                  { length: MAX_STEP - MIN_STEP + 1 },
                  (_, i) => MIN_STEP + i
                ).map((s) => (
                  <rect
                    key={s}
                    x={80}
                    y={yOf(s) - STEP / 2}
                    width={W - 88}
                    height={STEP}
                    fill="transparent"
                    style={{ cursor: "pointer" }}
                    onClick={() => place(s)}
                  />
                ))}
              {placed !== null && (
                <NoteHead
                  step={placed}
                  x={showSolution ? NOTE_X - 40 : NOTE_X}
                  color={
                    showResult
                      ? isCorrect
                        ? NOTE_COLORS[NAMES.indexOf(placedName!)]
                        : "#FEE2E2"
                      : NAVY
                  }
                  label={showResult ? placedName! : undefined}
                  labelColor={isCorrect ? undefined : "#EF4444"}
                />
              )}
              {showSolution && (
                <NoteHead
                  step={targetStep}
                  x={NOTE_X + 40}
                  color={NOTE_COLORS[NAMES.indexOf(targetName)]}
                  label={targetName}
                  onClick={() => playStep(targetStep)}
                />
              )}
            </>
          ) : (
            <NoteHead
              step={targetStep}
              x={NOTE_X}
              color={showResult ? NOTE_COLORS[NAMES.indexOf(targetName)] : NAVY}
              label={showResult ? targetName : undefined}
              onClick={() => playStep(targetStep)}
            />
          )}
        </svg>

        {placing ? (
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => place((placed ?? 3) - 1)}
              disabled={disabled}
              aria-label="Descendre la note"
              className="h-14 w-14 rounded-xl bg-fun-sky-light text-2xl font-bold text-fun-text active:scale-95 disabled:opacity-50"
            >
              ⬇️
            </button>
            <button
              type="button"
              onClick={() => placed !== null && playStep(placed)}
              disabled={placed === null}
              className="h-14 whitespace-nowrap rounded-xl bg-fun-sun-light px-5 text-lg font-bold text-fun-text active:scale-95 disabled:opacity-50"
            >
              🔊 Écouter
            </button>
            <button
              type="button"
              onClick={() => place((placed ?? 3) + 1)}
              disabled={disabled}
              aria-label="Monter la note"
              className="h-14 w-14 rounded-xl bg-fun-sky-light text-2xl font-bold text-fun-text active:scale-95 disabled:opacity-50"
            >
              ⬆️
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => playStep(targetStep)}
            className="h-12 rounded-xl bg-fun-sun-light px-5 text-lg font-bold text-fun-text active:scale-95"
          >
            🔊 Écouter la note
          </button>
        )}
      </div>

      {!placing && (
        <div
          className={cn(
            "grid gap-3",
            choices.length <= 3 ? "grid-cols-3" : "grid-cols-4 sm:grid-cols-7"
          )}
        >
          {choices.map((name) => {
            const selected = picked === name;
            const right = showResult && name === targetName;
            const wrong = showResult && selected && !isCorrect;
            return (
              <button
                key={name}
                type="button"
                onClick={() => pick(name)}
                disabled={disabled}
                className={cn(
                  "flex h-14 items-center justify-center gap-2 rounded-xl border-2 bg-white text-xl font-extrabold text-fun-text candy-shadow active:scale-95",
                  selected && !showResult && "border-fun-sky bg-fun-sky-light",
                  !selected && !right && "border-fun-border",
                  right && "border-fun-green bg-fun-green-light",
                  wrong && "border-fun-red bg-fun-red-light"
                )}
              >
                <span
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: NOTE_COLORS[NAMES.indexOf(name)] }}
                />
                {name}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
