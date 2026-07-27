"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { usePlaySessionApiV1PythagoreSessionPost as usePlaySession } from "@/lib/api/generated/pythagore/pythagore";
import { PythagoreDifficulty } from "@/lib/api/model";
import type { PythagoreItem, PythagoreSessionResponse } from "@/lib/api/model";

type Phase = "intro" | "playing" | "done";

interface DifficultyConfig {
  key: PythagoreDifficulty;
  label: string;
  emoji: string;
  tables: number[];
  count: number;
}

const DIFFICULTIES: DifficultyConfig[] = [
  {
    key: PythagoreDifficulty.facile,
    label: "Facile",
    emoji: "🌱",
    tables: [2, 3, 4, 5],
    count: 8,
  },
  {
    key: PythagoreDifficulty.moyen,
    label: "Moyen",
    emoji: "⭐",
    tables: [2, 3, 4, 5, 6, 7, 8, 9],
    count: 10,
  },
  {
    key: PythagoreDifficulty.difficile,
    label: "Difficile",
    emoji: "🔥",
    tables: [6, 7, 8, 9, 10, 11, 12],
    count: 12,
  },
];

function buildQuestions(config: DifficultyConfig): { a: number; b: number }[] {
  const questions: { a: number; b: number }[] = [];
  for (let i = 0; i < config.count; i++) {
    const a = config.tables[Math.floor(Math.random() * config.tables.length)];
    const b = 1 + Math.floor(Math.random() * 10); // 1..10 (dans les bornes 1..12)
    questions.push({ a, b });
  }
  return questions;
}

export default function PythagorePage() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("intro");
  const [config, setConfig] = useState<DifficultyConfig>(DIFFICULTIES[1]);
  const [questions, setQuestions] = useState<{ a: number; b: number }[]>([]);
  const [index, setIndex] = useState(0);
  const [items, setItems] = useState<PythagoreItem[]>([]);
  const [input, setInput] = useState("");
  const [result, setResult] = useState<PythagoreSessionResponse | null>(null);

  const { mutate, isPending } = usePlaySession();

  const current = questions[index];
  const progressPct = useMemo(
    () => (questions.length ? (index / questions.length) * 100 : 0),
    [index, questions.length]
  );

  const start = (c: DifficultyConfig) => {
    setConfig(c);
    setQuestions(buildQuestions(c));
    setItems([]);
    setIndex(0);
    setInput("");
    setResult(null);
    setPhase("playing");
  };

  const submitAnswer = () => {
    if (input.trim() === "" || !current) return;
    const answer = parseInt(input, 10);
    const nextItems = [...items, { a: current.a, b: current.b, answer }];
    setItems(nextItems);
    setInput("");

    if (index + 1 < questions.length) {
      setIndex(index + 1);
      return;
    }
    // Dernière question -> le serveur corrige et attribue l'XP.
    mutate(
      { data: { difficulty: config.key, items: nextItems } },
      {
        onSuccess: (data) => {
          setResult(data);
          setPhase("done");
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light p-4">
      <div className="mx-auto max-w-xl">
        <Button
          variant="ghost"
          onClick={() => router.push("/play")}
          className="mb-4 text-lg"
          size="lg"
        >
          <ChevronLeft className="mr-2 h-5 w-5" />
          Retour
        </Button>

        {phase === "intro" && (
          <div className="rounded-3xl bg-white p-6 candy-shadow">
            <div className="mb-2 text-center text-6xl">✖️</div>
            <h1 className="mb-1 text-center text-3xl font-extrabold text-fun-text">
              Défi des tables
            </h1>
            <p className="mb-6 text-center text-fun-text-muted">
              Réponds vite et enchaîne les bonnes réponses pour gagner des ⚡ XP
              bonus !
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.key}
                  onClick={() => start(d)}
                  className="flex min-h-[96px] flex-col items-center justify-center rounded-2xl border-2 border-fun-border bg-white p-4 candy-shadow transition-all hover:scale-[1.03] hover:border-fun-sky active:scale-95"
                >
                  <span className="text-4xl">{d.emoji}</span>
                  <span className="mt-1 font-bold text-fun-text">
                    {d.label}
                  </span>
                  <span className="text-xs text-fun-text-muted">
                    {d.count} questions
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {phase === "playing" && current && (
          <div className="rounded-3xl bg-white p-6 candy-shadow">
            <div className="mb-4 h-3 w-full rounded-full bg-fun-green-light">
              <div
                className="h-3 rounded-full bg-fun-green transition-all"
                style={{ width: `${progressPct}%` }}
              />
            </div>
            <p className="mb-2 text-center text-sm font-semibold text-fun-text-muted">
              Question {index + 1} / {questions.length}
            </p>
            <div className="my-8 text-center text-6xl font-extrabold text-fun-text">
              {current.a} × {current.b}
            </div>
            <input
              type="number"
              inputMode="numeric"
              autoFocus
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submitAnswer()}
              placeholder="?"
              className="mb-4 h-16 w-full rounded-xl border-2 border-fun-border text-center text-3xl font-bold text-fun-text focus:border-fun-sky focus:outline-none"
            />
            <Button
              onClick={submitAnswer}
              disabled={input.trim() === "" || isPending}
              className="h-14 w-full rounded-xl text-lg font-bold active:scale-95"
              size="lg"
            >
              {index + 1 < questions.length ? "Valider" : "Terminer"}
            </Button>
          </div>
        )}

        {phase === "done" && result && (
          <div className="rounded-3xl bg-white p-6 text-center candy-shadow">
            <div className="mb-2 text-6xl">
              {result.correct === result.total ? "🏆" : "🎉"}
            </div>
            <h2 className="mb-1 text-3xl font-extrabold text-fun-text">
              +{result.xp_earned} XP
            </h2>
            <p className="mb-4 text-fun-text-muted">
              {result.correct} / {result.total} bonnes réponses · meilleure
              série {result.longest_streak} 🔥
            </p>
            {result.capped && (
              <p className="mb-4 rounded-xl bg-fun-sun-light px-3 py-2 text-sm font-semibold text-fun-text-muted">
                Tu as atteint le maximum d&apos;XP des défis pour
                aujourd&apos;hui — reviens demain !
              </p>
            )}
            <div className="mb-6 inline-block rounded-2xl bg-fun-sun-light px-4 py-2 text-lg font-bold text-fun-sun">
              💰 {result.balance} XP à dépenser
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button
                onClick={() => start(config)}
                className="h-14 flex-1 rounded-xl text-lg font-bold active:scale-95"
                size="lg"
              >
                Rejouer
              </Button>
              <Button
                variant="outline"
                onClick={() => setPhase("intro")}
                className="h-14 flex-1 rounded-xl text-lg font-bold active:scale-95"
                size="lg"
              >
                Changer de niveau
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
