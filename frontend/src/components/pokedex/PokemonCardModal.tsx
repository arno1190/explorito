"use client";

import { useQuery } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

/** Noms FR + couleurs des 18 types (statique — évite des appels PokéAPI en plus). */
const TYPE_FR: Record<string, string> = {
  normal: "Normal",
  fire: "Feu",
  water: "Eau",
  grass: "Plante",
  electric: "Électrik",
  ice: "Glace",
  fighting: "Combat",
  poison: "Poison",
  ground: "Sol",
  flying: "Vol",
  psychic: "Psy",
  bug: "Insecte",
  rock: "Roche",
  ghost: "Spectre",
  dragon: "Dragon",
  dark: "Ténèbres",
  steel: "Acier",
  fairy: "Fée",
};

const TYPE_COLOR: Record<string, string> = {
  normal: "#A8A77A",
  fire: "#EE8130",
  water: "#6390F0",
  grass: "#7AC74C",
  electric: "#F7D02C",
  ice: "#96D9D6",
  fighting: "#C22E28",
  poison: "#A33EA1",
  ground: "#E2BF65",
  flying: "#A98FF3",
  psychic: "#F95587",
  bug: "#A6B91A",
  rock: "#B6A136",
  ghost: "#735797",
  dragon: "#6F35FC",
  dark: "#705746",
  steel: "#B7B7CE",
  fairy: "#D685AD",
};

const STAT_FR: Record<string, string> = {
  hp: "PV",
  attack: "Attaque",
  defense: "Défense",
  "special-attack": "Atq. Spé",
  "special-defense": "Déf. Spé",
  speed: "Vitesse",
};

interface PokemonCard {
  types: string[];
  hp: number;
  stats: { key: string; value: number }[];
  height: number;
  weight: number;
  genus: string | null;
  flavor: string | null;
}

async function fetchCard(id: number): Promise<PokemonCard> {
  const [pokeRes, speciesRes] = await Promise.all([
    fetch(`https://pokeapi.co/api/v2/pokemon/${id}`),
    fetch(`https://pokeapi.co/api/v2/pokemon-species/${id}`).catch(() => null),
  ]);
  if (!pokeRes.ok) throw new Error("PokéAPI indisponible");
  const poke = await pokeRes.json();

  const types: string[] = poke.types.map(
    (t: { type: { name: string } }) => t.type.name
  );
  const stats = poke.stats.map(
    (s: { stat: { name: string }; base_stat: number }) => ({
      key: s.stat.name,
      value: s.base_stat,
    })
  );
  const hp = stats.find((s: { key: string }) => s.key === "hp")?.value ?? 0;

  let genus: string | null = null;
  let flavor: string | null = null;
  if (speciesRes && speciesRes.ok) {
    const species = await speciesRes.json();
    genus =
      species.genera?.find(
        (g: { language: { name: string } }) => g.language.name === "fr"
      )?.genus ?? null;
    const fe = species.flavor_text_entries?.find(
      (e: { language: { name: string } }) => e.language.name === "fr"
    );
    flavor = fe ? fe.flavor_text.replace(/[\f\n\r]/g, " ") : null;
  }

  return {
    types,
    hp,
    stats,
    height: poke.height / 10, // dm -> m
    weight: poke.weight / 10, // hg -> kg
    genus,
    flavor,
  };
}

interface PokemonCardModalProps {
  id: number | null;
  nameFr: string;
  imageUrl: string;
  open: boolean;
  onClose: () => void;
}

export function PokemonCardModal({
  id,
  nameFr,
  imageUrl,
  open,
  onClose,
}: PokemonCardModalProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["pokeapi-card", id],
    queryFn: () => fetchCard(id as number),
    enabled: open && id != null,
    staleTime: Infinity, // données immuables
    gcTime: 1000 * 60 * 60,
  });

  const primary = data?.types[0] ?? "normal";
  const primaryColor = TYPE_COLOR[primary] ?? "#A8A77A";

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent
        className="max-h-[92vh] max-w-[360px] overflow-y-auto rounded-3xl border-0 p-0"
        style={{
          background: `linear-gradient(160deg, ${primaryColor} 0%, #ffffff 55%)`,
        }}
      >
        <DialogTitle className="sr-only">{nameFr}</DialogTitle>

        <div className="p-4">
          {/* Card frame */}
          <div className="rounded-2xl border-4 border-white/70 bg-white/85 p-3 shadow-inner backdrop-blur-sm">
            {/* Header: name + HP */}
            <div className="mb-2 flex items-baseline justify-between gap-2">
              <h2 className="text-xl font-extrabold text-fun-text">{nameFr}</h2>
              {data && (
                <span className="whitespace-nowrap text-sm font-extrabold text-fun-red">
                  <span className="text-xs align-top">PV</span> {data.hp}
                </span>
              )}
            </div>

            {/* Artwork window */}
            <div
              className="flex items-center justify-center rounded-xl border-2 border-white/80 p-2"
              style={{
                background: `radial-gradient(circle, ${primaryColor}33 0%, #ffffff 70%)`,
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={imageUrl}
                alt={nameFr}
                className="h-40 w-40 object-contain drop-shadow-lg"
              />
            </div>

            {/* Types */}
            {data && (
              <div className="mt-3 flex flex-wrap justify-center gap-2">
                {data.types.map((t) => (
                  <span
                    key={t}
                    className="rounded-full px-3 py-1 text-xs font-bold text-white shadow"
                    style={{ backgroundColor: TYPE_COLOR[t] ?? "#A8A77A" }}
                  >
                    {TYPE_FR[t] ?? t}
                  </span>
                ))}
              </div>
            )}

            {/* Genus + height/weight */}
            {data && (
              <div className="mt-3 flex items-center justify-between rounded-xl bg-fun-sky-light px-3 py-2 text-xs font-semibold text-fun-text">
                <span>{data.genus ?? "Pokémon"}</span>
                <span>
                  {data.height.toFixed(1)} m · {data.weight.toFixed(1)} kg
                </span>
              </div>
            )}

            {/* Stats */}
            {data && (
              <div className="mt-3 space-y-1.5">
                {data.stats.map((s) => (
                  <div key={s.key} className="flex items-center gap-2">
                    <span className="w-16 text-[11px] font-bold text-fun-text-muted">
                      {STAT_FR[s.key] ?? s.key}
                    </span>
                    <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-fun-border">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${Math.min(100, (s.value / 200) * 100)}%`,
                          backgroundColor: primaryColor,
                        }}
                      />
                    </div>
                    <span className="w-7 text-right text-[11px] font-bold text-fun-text">
                      {s.value}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Flavor text */}
            {data?.flavor && (
              <p className="mt-3 rounded-xl bg-fun-sun-light px-3 py-2 text-xs italic text-fun-text">
                {data.flavor}
              </p>
            )}

            {isLoading && (
              <div className="flex justify-center py-8">
                <div className="h-8 w-8 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
              </div>
            )}
            {isError && (
              <p className="mt-3 rounded-xl bg-fun-red-light px-3 py-2 text-center text-xs font-semibold text-fun-red">
                Détails indisponibles (connexion requise).
              </p>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
