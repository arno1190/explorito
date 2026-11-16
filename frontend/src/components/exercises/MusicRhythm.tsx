"use client";

import { useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { useMusicPlayback } from "./useMusicPlayback";
import type {
  ExerciseTypeComponentProps,
  MusicRhythmContent,
  RhythmSymbol,
} from "./types";

export const RHYTHM_BEATS: Record<RhythmSymbol, number> = {
  ronde: 4,
  blanche: 2,
  noire: 1,
  croche: 0.5,
  demi_pause: 2,
  soupir: 1,
  demi_soupir: 0.5,
};
const LABELS: Record<RhythmSymbol, string> = {
  ronde: "ronde",
  blanche: "blanche",
  noire: "noire",
  croche: "croche",
  demi_pause: "demi-pause",
  soupir: "soupir",
  demi_soupir: "demi-soupir",
};
const isNote = (event: RhythmSymbol) =>
  ["ronde", "blanche", "noire", "croche"].includes(event);

export function RhythmNotation({
  events,
  beatsPerBar = 4,
}: {
  events: RhythmSymbol[];
  beatsPerBar?: number;
}) {
  const width = 55 + events.length * 48;
  return (
    <div className="overflow-x-auto rounded-xl bg-white p-2">
      <svg
        viewBox={`0 0 ${width} 115`}
        style={{ minWidth: Math.min(width, 640) }}
        className="w-full"
        role="img"
        aria-label={events.map((event) => LABELS[event]).join(", ")}
      >
        <line x1={8} x2={width - 5} y1={65} y2={65} stroke="#64748B" />
        <text x={15} y={49} fontSize={20} fontWeight={800} fill="#042C60">
          {beatsPerBar}
        </text>
        <text x={15} y={76} fontSize={20} fontWeight={800} fill="#042C60">
          4
        </text>
        {events.map((event, index) => {
          const x = 52 + index * 48;
          const beats = events
            .slice(0, index + 1)
            .reduce((sum, figure) => sum + RHYTHM_BEATS[figure], 0);
          return (
            <g key={index} fill="#042C60" stroke="#042C60">
              {isNote(event) ? (
                <>
                  <ellipse
                    cx={x}
                    cy={65}
                    rx={9}
                    ry={6}
                    transform={`rotate(-20 ${x} 65)`}
                    fill={
                      event === "blanche" || event === "ronde"
                        ? "white"
                        : "#042C60"
                    }
                    strokeWidth={2}
                  />
                  {event !== "ronde" && (
                    <line
                      x1={x + 8}
                      x2={x + 8}
                      y1={63}
                      y2={26}
                      strokeWidth={2}
                    />
                  )}
                  {event === "croche" && (
                    <path
                      d={`M ${x + 8} 26 Q ${x + 29} 39 ${x + 15} 53 Q ${x + 24} 40 ${x + 8} 37 Z`}
                    />
                  )}
                </>
              ) : event === "demi_pause" ? (
                <rect x={x - 8} y={59} width={16} height={6} />
              ) : event === "soupir" ? (
                <path
                  d={`M ${x - 4} 35 L ${x + 5} 47 L ${x - 3} 56 L ${x + 5} 67 Q ${x - 10} 63 ${x - 2} 81 Q ${x - 16} 68 ${x - 6} 61 L ${x - 10} 54 L ${x - 2} 45 Z`}
                />
              ) : (
                <>
                  <circle cx={x - 5} cy={51} r={4} />
                  <path
                    d={`M ${x - 5} 51 Q ${x + 2} 58 ${x + 9} 44 L ${x - 1} 79`}
                    fill="none"
                    strokeWidth={2}
                  />
                </>
              )}
              {beats % beatsPerBar === 0 && (
                <line
                  x1={x + 24}
                  x2={x + 24}
                  y1={25}
                  y2={90}
                  strokeWidth={1.5}
                />
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export function MusicRhythm({
  question,
  content,
  emoji,
  onAnswer,
  disabled,
  showResult,
  isCorrect,
}: ExerciseTypeComponentProps<MusicRhythmContent>) {
  const mode = content.mode ?? "count";
  const bpm = content.bpm ?? 72;
  const [picked, setPicked] = useState<string | number | null>(null);
  const [taps, setTaps] = useState<number[]>([]);
  const times = useRef<number[]>([]);
  const { play, stop, playing, audioError } = useMusicPlayback();
  const total = content.events.reduce(
    (sum, event) => sum + RHYTHM_BEATS[event],
    0
  );
  const expectedChoice = content.choices?.find(
    (choice) => JSON.stringify(choice.events) === JSON.stringify(content.events)
  );
  const clear = () => {
    times.current = [];
    setTaps([]);
    setPicked(null);
    onAnswer(null);
  };
  const tap = () => {
    if (disabled || playing || times.current.length >= 16) return;
    const next = [...times.current, performance.now() / 1000];
    times.current = next;
    setTaps(next);
    onAnswer(next.length >= 2 ? { taps: next } : null);
  };
  const listen = () => {
    if (mode === "tap" && !disabled) clear();
    void play(
      content.events.map((event) => ({
        frequency: isNote(event) ? 660 : null,
        beats: RHYTHM_BEATS[event],
      })),
      bpm
    );
  };
  const selectedClass = (selected: boolean) =>
    cn(
      "min-h-14 rounded-xl border-2 px-4 text-lg font-bold text-fun-text active:scale-95 disabled:opacity-50",
      selected
        ? "border-fun-sky bg-fun-sky-light"
        : "border-fun-border bg-white"
    );
  return (
    <div className="space-y-5">
      <h2 className="text-xl font-bold text-fun-text">
        {emoji} {question}
      </h2>
      <p className="text-sm font-bold text-fun-text-muted">
        Noire = un temps · {bpm} pulsations par minute
      </p>
      {(mode !== "listen" || showResult) && (
        <RhythmNotation
          events={content.events}
          beatsPerBar={content.beats_per_bar}
        />
      )}
      <button
        type="button"
        onClick={playing ? stop : listen}
        className="min-h-12 rounded-xl bg-fun-sun-light px-5 font-bold text-fun-text"
      >
        {playing ? "Arrêter l'écoute" : "🔊 Écouter le rythme"}
      </button>
      {audioError && (
        <p role="alert" className="text-fun-red">
          Le son est indisponible. Active le son du navigateur puis réessaie.
        </p>
      )}
      {mode === "count" && (
        <div className="flex flex-wrap gap-2">
          {Array.from(
            { length: Math.min(16, Math.max(4, Math.ceil(total) + 2)) * 2 },
            (_, index) => (index + 1) / 2
          ).map((value) => (
            <button
              key={value}
              type="button"
              disabled={disabled}
              className={selectedClass(picked === value)}
              onClick={() => {
                setPicked(value);
                onAnswer({ beats: value });
              }}
            >
              {value.toLocaleString("fr-FR")} temps
            </button>
          ))}
        </div>
      )}
      {mode === "listen" && (
        <div className="space-y-3">
          <p className="text-fun-text">
            Écoute le modèle, puis choisis la partition qui correspond.
          </p>
          {content.choices?.map((choice, index) => (
            <button
              key={choice.id}
              type="button"
              disabled={disabled}
              aria-pressed={picked === choice.id}
              className={cn(
                selectedClass(picked === choice.id),
                "block w-full text-left"
              )}
              onClick={() => {
                setPicked(choice.id);
                onAnswer({ option_id: choice.id });
              }}
            >
              <span>Rythme {index + 1}</span>
              <RhythmNotation
                events={choice.events}
                beatsPerBar={content.beats_per_bar}
              />
            </button>
          ))}
        </div>
      )}
      {mode === "tap" && (
        <div className="space-y-3">
          <p className="text-fun-text">
            Écoute, puis frappe une fois au début de chaque note. Pendant un
            silence, attends. Ta première frappe lance le rythme ; respecte
            ensuite le tempo de {bpm} pulsations par minute.
          </p>
          <button
            type="button"
            disabled={disabled || playing || taps.length >= 16}
            onClick={tap}
            onKeyDown={(event) => {
              if (event.repeat) event.preventDefault();
            }}
            className="min-h-24 w-full touch-manipulation rounded-2xl bg-fun-sky-light text-2xl font-extrabold text-fun-text active:scale-95 disabled:opacity-50"
          >
            👏 Frapper
          </button>
          <p aria-live="polite" className="text-fun-text">
            {taps.length} frappe{taps.length > 1 ? "s" : ""} enregistrée
            {taps.length > 1 ? "s" : ""}
          </p>
          <button
            type="button"
            disabled={disabled || playing}
            onClick={clear}
            className="min-h-12 rounded-xl border-2 border-fun-border px-4 font-bold text-fun-text disabled:opacity-50"
          >
            Recommencer
          </button>
        </div>
      )}
      {showResult && (
        <p
          className={
            isCorrect
              ? "font-bold text-fun-green-dark"
              : "font-bold text-fun-red"
          }
        >
          {mode === "count"
            ? `Durée totale : ${total.toLocaleString("fr-FR")} temps, silences compris.`
            : mode === "listen"
              ? `Bonne réponse : rythme ${(content.choices?.findIndex((choice) => choice.id === expectedChoice?.id) ?? 0) + 1}.`
              : "Une frappe par note ; les silences comptent dans le temps entre les frappes."}
        </p>
      )}
    </div>
  );
}
