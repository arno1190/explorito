"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { useQueryClient } from "@tanstack/react-query";
import {
  useCreatePuzzleApiV1SudokuNewPost as useCreatePuzzle,
  useSolvePuzzleApiV1SudokuSessionIdSolvePost as useSolvePuzzle,
} from "@/lib/api/generated/sudoku/sudoku";
import { getGetWalletApiV1CollectionMeGetQueryKey } from "@/lib/api/generated/collection/collection";
import { SudokuDifficulty } from "@/lib/api/model";
import type { PuzzleResponse, SolveResponse } from "@/lib/api/model";

type Phase = "intro" | "playing" | "done";

interface DifficultyConfig {
  key: SudokuDifficulty;
  label: string;
  emoji: string;
  grid: string;
  xp: number;
}

const DIFFICULTIES: DifficultyConfig[] = [
  {
    key: SudokuDifficulty.easy,
    label: "Facile",
    emoji: "🌱",
    grid: "4 × 4",
    xp: 10,
  },
  {
    key: SudokuDifficulty.medium,
    label: "Moyen",
    emoji: "⭐",
    grid: "6 × 6",
    xp: 20,
  },
  {
    key: SudokuDifficulty.hard,
    label: "Difficile",
    emoji: "🔥",
    grid: "8 × 8",
    xp: 30,
  },
];

export default function SudokuPage() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("intro");
  const [config, setConfig] = useState<DifficultyConfig>(DIFFICULTIES[0]);
  const [puzzle, setPuzzle] = useState<PuzzleResponse | null>(null);
  // Valeurs saisies par l'enfant, indexées "r-c" (les cases indices restent fixes).
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<SolveResponse | null>(null);
  const [tryAgain, setTryAgain] = useState(false);

  const createPuzzle = useCreatePuzzle();
  const solvePuzzle = useSolvePuzzle();
  const queryClient = useQueryClient();

  const size = puzzle?.size ?? 0;
  const rows = useMemo(() => Array.from({ length: size }, (_, i) => i), [size]);

  // Nombre de cases à remplir et cases remplies (avec une valeur valide 1..size).
  const blanks = useMemo(() => {
    if (!puzzle) return [] as string[];
    const out: string[] = [];
    puzzle.puzzle.forEach((row, r) =>
      row.forEach((v, c) => {
        if (v === 0) out.push(`${r}-${c}`);
      })
    );
    return out;
  }, [puzzle]);

  const filledCount = blanks.filter((k) => {
    const n = parseInt(values[k] ?? "", 10);
    return n >= 1 && n <= size;
  }).length;
  const allFilled = blanks.length > 0 && filledCount === blanks.length;

  const start = (c: DifficultyConfig) => {
    setConfig(c);
    setResult(null);
    setTryAgain(false);
    createPuzzle.mutate(
      { data: { difficulty: c.key } },
      {
        onSuccess: (data) => {
          setPuzzle(data);
          setValues({});
          setPhase("playing");
        },
      }
    );
  };

  const submit = () => {
    if (!puzzle || !allFilled || solvePuzzle.isPending) return;
    // Reconstruit la grille complète : indices donnés + saisies de l'enfant.
    const grid = puzzle.puzzle.map((row, r) =>
      row.map((v, c) => (v !== 0 ? v : parseInt(values[`${r}-${c}`], 10)))
    );
    solvePuzzle.mutate(
      { sessionId: puzzle.session_id, data: { grid } },
      {
        onSuccess: (data) => {
          if (data.correct) {
            setResult(data);
            setPhase("done");
            queryClient.invalidateQueries({
              queryKey: getGetWalletApiV1CollectionMeGetQueryKey(),
            });
          } else {
            setTryAgain(true);
          }
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
            <div className="mb-2 text-center text-6xl">🔢</div>
            <h1 className="mb-1 text-center text-3xl font-extrabold text-fun-text">
              Le Sudoku
            </h1>
            <p className="mb-6 text-center text-fun-text-muted">
              Remplis la grille : chaque ligne, chaque colonne et chaque bloc
              contient tous les chiffres. Résous-la et gagne des ⚡ XP !
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.key}
                  onClick={() => start(d)}
                  disabled={createPuzzle.isPending}
                  className="flex min-h-[96px] flex-col items-center justify-center rounded-2xl border-2 border-fun-border bg-white p-4 candy-shadow transition-all hover:scale-[1.03] hover:border-fun-sky active:scale-95 disabled:opacity-60"
                >
                  <span className="text-4xl">{d.emoji}</span>
                  <span className="mt-1 font-bold text-fun-text">
                    {d.label}
                  </span>
                  <span className="text-xs text-fun-text-muted">
                    Grille {d.grid} · +{d.xp} XP
                  </span>
                </button>
              ))}
            </div>
            {createPuzzle.isPending && (
              <p className="mt-4 text-center text-fun-text-muted">
                Préparation de la grille…
              </p>
            )}
          </div>
        )}

        {phase === "playing" && puzzle && (
          <div className="rounded-3xl bg-white p-4 candy-shadow sm:p-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-xl font-extrabold text-fun-text">
                {config.emoji} Sudoku {config.grid}
              </h2>
              <span className="rounded-full bg-fun-sun-light px-3 py-1 text-sm font-bold text-fun-sun">
                {filledCount}/{blanks.length}
              </span>
            </div>

            <div className="flex justify-center overflow-x-auto pb-2">
              <div
                className="grid gap-0 border-2 border-fun-text"
                style={{
                  gridTemplateColumns: `repeat(${size}, minmax(0, 1fr))`,
                }}
              >
                {rows.map((r) =>
                  rows.map((c) => {
                    const given = puzzle.puzzle[r][c];
                    const key = `${r}-${c}`;
                    // Bordures épaisses aux frontières de blocs.
                    const thickTop = r % puzzle.box_rows === 0 && r !== 0;
                    const thickLeft = c % puzzle.box_cols === 0 && c !== 0;
                    return (
                      <div
                        key={key}
                        className={cn(
                          "flex h-10 w-10 items-center justify-center border border-fun-border sm:h-11 sm:w-11",
                          thickTop && "border-t-2 border-t-fun-text",
                          thickLeft && "border-l-2 border-l-fun-text"
                        )}
                      >
                        {given !== 0 ? (
                          <span className="text-lg font-extrabold text-fun-text">
                            {given}
                          </span>
                        ) : (
                          <input
                            type="text"
                            inputMode="numeric"
                            aria-label={`Ligne ${r + 1} colonne ${c + 1}`}
                            value={values[key] ?? ""}
                            onChange={(e) => {
                              // N'accepte qu'un chiffre 1..size.
                              const raw = e.target.value
                                .replace(/[^0-9]/g, "")
                                .slice(-1);
                              const n = parseInt(raw, 10);
                              const ok = raw === "" || (n >= 1 && n <= size);
                              if (ok) {
                                setValues((v) => ({ ...v, [key]: raw }));
                                setTryAgain(false);
                              }
                            }}
                            className="h-full w-full bg-fun-sun-light text-center text-lg font-bold text-fun-sky outline-none focus:bg-fun-sky-light"
                          />
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {tryAgain && (
              <p className="mt-3 rounded-xl bg-fun-red-light px-3 py-2 text-center text-sm font-semibold text-fun-red">
                Ce n&apos;est pas encore ça — vérifie tes lignes, colonnes et
                blocs&nbsp;! 🧐
              </p>
            )}

            <Button
              onClick={submit}
              disabled={!allFilled || solvePuzzle.isPending}
              className="mt-4 h-14 w-full rounded-xl text-lg font-bold active:scale-95"
              size="lg"
            >
              {solvePuzzle.isPending ? "…" : "Valider la grille"}
            </Button>
          </div>
        )}

        {phase === "done" && result && (
          <div className="rounded-3xl bg-white p-6 text-center candy-shadow">
            <div className="mb-2 text-6xl">🏆</div>
            <h2 className="mb-1 text-3xl font-extrabold text-fun-text">
              +{result.xp_earned} XP
            </h2>
            <p className="mb-4 text-fun-text-muted">
              Grille résolue, bravo&nbsp;! 🎉
            </p>
            <div className="mb-6 inline-block rounded-2xl bg-fun-sun-light px-4 py-2 text-lg font-bold text-fun-sun">
              💰 {result.balance} XP à dépenser
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button
                onClick={() => start(config)}
                disabled={createPuzzle.isPending}
                className="h-14 flex-1 rounded-xl text-lg font-bold active:scale-95"
                size="lg"
              >
                Nouvelle grille
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
