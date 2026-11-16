"use client";

import { useState } from "react";
import { BassClef, CClef, NoteHead, TrebleClef } from "./MusicNote";
import { useMusicPlayback, pitchFrequency } from "./useMusicPlayback";
import type {
  ExerciseTypeComponentProps,
  MusicSequenceContent,
  NoteName,
} from "./types";

const NAMES: NoteName[] = ["do", "ré", "mi", "fa", "sol", "la", "si"];
const LETTERS = "CDEFGAB";
const BOTTOM = { sol: 30, fa: 18, ut3: 24 };

export function MusicSequence({
  question,
  content,
  emoji,
  onAnswer,
  disabled,
  showResult,
  isCorrect,
}: ExerciseTypeComponentProps<MusicSequenceContent>) {
  const [names, setNames] = useState<NoteName[]>([]);
  const { play, playing, audioError } = useMusicPlayback();
  const clef = content.clef ?? "sol";
  const listening = content.mode === "listen";
  const expected = content.pitches.map(
    (pitch) => NAMES[LETTERS.indexOf(pitch[0])]
  );
  const width = 105 + content.pitches.length * 50;
  const choose = (name: NoteName) => {
    if (disabled || names.length >= expected.length) return;
    const next = [...names, name];
    setNames(next);
    onAnswer(next.length === expected.length ? { names: next } : null);
  };

  return (
    <div className="space-y-5">
      <h2 className="text-xl font-bold text-fun-text">
        {emoji} {question}
      </h2>
      {(!listening || showResult) && (
        <div className="overflow-x-auto rounded-2xl bg-white candy-shadow">
          <svg
            viewBox={`0 0 ${width} 220`}
            className="min-w-[360px] w-full"
            role="img"
            aria-label="Suite de notes à lire de gauche à droite"
          >
            {[0, 2, 4, 6, 8].map((step) => (
              <line
                key={step}
                x1={8}
                x2={width - 8}
                y1={150 - step * 10}
                y2={150 - step * 10}
                stroke="#042C60"
                strokeWidth={1.6}
              />
            ))}
            {clef === "fa" ? (
              <BassClef />
            ) : clef === "ut3" ? (
              <CClef step={4} />
            ) : (
              <TrebleClef />
            )}
            {content.pitches.map((pitch, index) => {
              const step =
                Number(pitch[1]) * 7 + LETTERS.indexOf(pitch[0]) - BOTTOM[clef];
              const x = 105 + index * 50;
              const y = 150 - step * 10;
              const stemDirection = step >= 4 ? 1 : -1;
              return (
                <g key={index}>
                  <NoteHead
                    step={step}
                    x={x}
                    color="#042C60"
                    label={showResult ? expected[index] : undefined}
                  />
                  <line
                    x1={x - stemDirection * 9}
                    x2={x - stemDirection * 9}
                    y1={y}
                    y2={y + stemDirection * 35}
                    stroke="#042C60"
                    strokeWidth={2}
                  />
                  <text
                    x={x}
                    y={210}
                    textAnchor="middle"
                    fill="#64748B"
                    fontSize={14}
                  >
                    {index + 1}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      )}
      {listening && !showResult && (
        <p className="rounded-xl bg-fun-sky-light p-4 text-fun-text">
          Écoute la suite, puis choisis les noms dans l&apos;ordre. Chaque note
          dure un temps.
        </p>
      )}
      <button
        type="button"
        disabled={playing}
        onClick={() =>
          void play(
            content.pitches.map((pitch) => ({
              frequency: pitchFrequency(pitch),
              beats: 1,
            })),
            content.bpm ?? 72
          )
        }
        className="min-h-12 rounded-xl bg-fun-sun-light px-5 font-bold text-fun-text disabled:opacity-50"
      >
        {playing ? "Écoute…" : "🔊 Écouter la suite"}
      </button>
      {listening && (
        <button
          type="button"
          disabled={playing}
          onClick={() =>
            void play(
              [
                {
                  frequency: pitchFrequency(clef === "fa" ? "C3" : "C4"),
                  beats: 1,
                },
              ],
              content.bpm ?? 72
            )
          }
          className="min-h-12 rounded-xl bg-fun-sky-light px-5 font-bold text-fun-text disabled:opacity-50"
        >
          🔊 Repère : do
        </button>
      )}
      {audioError && (
        <p role="alert" className="text-fun-red">
          Le son est indisponible. Active le son du navigateur puis réessaie.
        </p>
      )}
      <ol aria-label="Ta réponse" className="flex flex-wrap gap-2">
        {expected.map((_, index) => (
          <li
            key={index}
            className="flex h-12 min-w-12 items-center justify-center rounded-xl border-2 border-fun-border px-3 font-bold text-fun-text"
          >
            {names[index] ?? "…"}
            <span className="sr-only">, note {index + 1}</span>
          </li>
        ))}
      </ol>
      <div className="flex flex-wrap gap-2">
        {NAMES.map((name) => (
          <button
            key={name}
            type="button"
            disabled={disabled || names.length >= expected.length}
            onClick={() => choose(name)}
            className="h-14 min-w-14 rounded-xl border-2 border-fun-border bg-white px-3 text-xl font-bold text-fun-text active:scale-95 disabled:opacity-50"
          >
            {name}
          </button>
        ))}
      </div>
      <button
        type="button"
        disabled={disabled || names.length === 0}
        onClick={() => {
          setNames(names.slice(0, -1));
          onAnswer(null);
        }}
        className="min-h-12 rounded-xl bg-fun-sky-light px-5 font-bold text-fun-text disabled:opacity-50"
      >
        Effacer la dernière note
      </button>
      {showResult && (
        <p
          className={
            isCorrect
              ? "font-bold text-fun-green-dark"
              : "font-bold text-fun-red"
          }
        >
          La suite : {expected.join(" · ")}
        </p>
      )}
    </div>
  );
}
