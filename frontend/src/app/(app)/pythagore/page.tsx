"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { useQueryClient } from "@tanstack/react-query";
import { usePlaySessionApiV1PythagoreSessionPost as usePlaySession } from "@/lib/api/generated/pythagore/pythagore";
import { getGetWalletApiV1CollectionMeGetQueryKey } from "@/lib/api/generated/collection/collection";
import { PythagoreDifficulty } from "@/lib/api/model";
import type { PythagoreItem, PythagoreSessionResponse } from "@/lib/api/model";

type Phase = "intro" | "playing" | "done";

interface DifficultyConfig {
  key: PythagoreDifficulty;
  label: string;
  emoji: string;
  size: number; // grille size × size (facteurs 1..size)
  blanks: number; // nombre de cases à compléter
}

const DIFFICULTIES: DifficultyConfig[] = [
  {
    key: PythagoreDifficulty.facile,
    label: "Facile",
    emoji: "🌱",
    size: 5,
    blanks: 6,
  },
  {
    key: PythagoreDifficulty.moyen,
    label: "Moyen",
    emoji: "⭐",
    size: 10,
    blanks: 10,
  },
  {
    key: PythagoreDifficulty.difficile,
    label: "Difficile",
    emoji: "🔥",
    size: 10,
    blanks: 18,
  },
];

/** Choisit `blanks` cases distinctes (a,b) dans la grille size×size. */
function pickBlanks(size: number, blanks: number): Set<string> {
  const keys: string[] = [];
  for (let a = 1; a <= size; a++) {
    for (let b = 1; b <= size; b++) keys.push(`${a}-${b}`);
  }
  // Mélange (Fisher-Yates) puis prend les premiers `blanks`.
  for (let i = keys.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [keys[i], keys[j]] = [keys[j], keys[i]];
  }
  return new Set(keys.slice(0, Math.min(blanks, keys.length)));
}

export default function PythagorePage() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("intro");
  const [config, setConfig] = useState<DifficultyConfig>(DIFFICULTIES[1]);
  const [blankKeys, setBlankKeys] = useState<Set<string>>(new Set());
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<PythagoreSessionResponse | null>(null);

  const { mutate, isPending } = usePlaySession();
  const queryClient = useQueryClient();

  const rows = useMemo(
    () => Array.from({ length: config.size }, (_, i) => i + 1),
    [config.size]
  );

  const filledCount = useMemo(
    () =>
      [...blankKeys].filter((k) => (values[k] ?? "").trim().length > 0).length,
    [blankKeys, values]
  );
  const allFilled = filledCount === blankKeys.size && blankKeys.size > 0;

  const start = (c: DifficultyConfig) => {
    setConfig(c);
    setBlankKeys(pickBlanks(c.size, c.blanks));
    setValues({});
    setResult(null);
    setPhase("playing");
  };

  const finish = () => {
    if (!allFilled || isPending) return;
    // Chaque case trouée -> un item {a, b, answer}. Le serveur corrige (a×b).
    const items: PythagoreItem[] = [...blankKeys].map((k) => {
      const [a, b] = k.split("-").map(Number);
      return { a, b, answer: parseInt(values[k], 10) };
    });
    mutate(
      { data: { difficulty: config.key, items } },
      {
        onSuccess: (data) => {
          setResult(data);
          setPhase("done");
          // Met à jour le compteur d'XP de la barre du haut sans recharger.
          queryClient.invalidateQueries({
            queryKey: getGetWalletApiV1CollectionMeGetQueryKey(),
          });
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light p-4">
      <div className="mx-auto max-w-2xl">
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
              La table de Pythagore
            </h1>
            <p className="mb-6 text-center text-fun-text-muted">
              Complète les cases vides de la table de multiplication et gagne
              des ⚡ XP !
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
                    {d.blanks} cases · table de {d.size}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {phase === "playing" && (
          <div className="rounded-3xl bg-white p-4 candy-shadow sm:p-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-xl font-extrabold text-fun-text">
                Complète la table
              </h2>
              <span className="rounded-full bg-fun-sun-light px-3 py-1 text-sm font-bold text-fun-sun">
                {filledCount}/{blankKeys.size}
              </span>
            </div>

            <div className="overflow-x-auto pb-2">
              <table className="border-collapse">
                <thead>
                  <tr>
                    <th className="sticky left-0 z-10 h-10 w-10 rounded-tl-xl bg-fun-sky text-white">
                      ×
                    </th>
                    {rows.map((c) => (
                      <th
                        key={c}
                        className="h-10 min-w-[44px] bg-fun-sky-light text-sm font-bold text-fun-text"
                      >
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r}>
                      <th className="sticky left-0 z-10 h-11 w-10 bg-fun-sky-light text-sm font-bold text-fun-text">
                        {r}
                      </th>
                      {rows.map((c) => {
                        const key = `${r}-${c}`;
                        const isBlank = blankKeys.has(key);
                        return (
                          <td
                            key={c}
                            className="h-11 min-w-[44px] border border-fun-border p-0 text-center"
                          >
                            {isBlank ? (
                              <input
                                type="number"
                                inputMode="numeric"
                                aria-label={`${r} fois ${c}`}
                                value={values[key] ?? ""}
                                onChange={(e) =>
                                  setValues((v) => ({
                                    ...v,
                                    [key]: e.target.value,
                                  }))
                                }
                                className={cn(
                                  "h-full w-full min-w-[44px] bg-fun-sun-light text-center text-sm font-bold text-fun-text outline-none focus:bg-fun-sun/30",
                                  (values[key] ?? "").trim() &&
                                    "bg-fun-sky-light"
                                )}
                              />
                            ) : (
                              <span className="text-sm text-fun-text-muted">
                                {r * c}
                              </span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <Button
              onClick={finish}
              disabled={!allFilled || isPending}
              className="mt-4 h-14 w-full rounded-xl text-lg font-bold active:scale-95"
              size="lg"
            >
              {isPending ? "…" : "Valider la table"}
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
              {result.correct} / {result.total} cases justes · meilleure série{" "}
              {result.longest_streak} 🔥
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
