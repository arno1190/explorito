"use client";

import { useState } from "react";
import { Sparkles, Star, Lock } from "lucide-react";

import { Confetti } from "@/components/gamification/Confetti";
import { PokemonCardModal } from "@/components/pokedex/PokemonCardModal";
import { cn } from "@/lib/utils";
import {
  useGetPokedexApiV1CollectionPokedexGet as usePokedex,
  useGetUserCollectionApiV1CollectionMeGet as useMyCollection,
  usePurchaseApiV1CollectionPurchasePost as usePurchase,
} from "@/lib/api/generated/collection/collection";
import type { PokedexGridEntry } from "@/lib/api/model";

export default function PokedexPage() {
  const pokedexQuery = usePokedex();
  const meQuery = useMyCollection();
  const purchase = usePurchase();

  const [celebrating, setCelebrating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<PokedexGridEntry | null>(null);

  const balance = meQuery.data?.balance ?? 0;
  const ownedCount = meQuery.data?.unlocked_count ?? 0;
  const total = meQuery.data?.total_count ?? pokedexQuery.data?.length ?? 0;
  const pokedex = pokedexQuery.data ?? [];

  const buy = async (entry: PokedexGridEntry) => {
    setError(null);
    try {
      const res = await purchase.mutateAsync({
        data: { pokemon_id: entry.id },
      });
      await Promise.all([pokedexQuery.refetch(), meQuery.refetch()]);
      setCelebrating(res.pokemon.name_fr);
      window.setTimeout(() => setCelebrating(null), 1800);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Achat impossible pour le moment";
      setError(detail);
    }
  };

  if (pokedexQuery.isLoading || meQuery.isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-6xl p-4 pb-24 sm:p-6">
      <Confetti show={!!celebrating} onComplete={() => setCelebrating(null)} />

      {/* Wallet header */}
      <div className="mb-6 rounded-3xl bg-white p-6 candy-shadow">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-fun-text sm:text-3xl">
              📕 Mon Pokédex
            </h1>
            <p className="mt-1 text-fun-text-muted">
              Dépense ton XP pour débloquer des Pokémon&nbsp;!
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-2xl bg-fun-sun-light px-5 py-3">
            <Star className="h-6 w-6 fill-fun-sun text-fun-sun" />
            <div>
              <div className="text-2xl font-extrabold text-fun-text">
                {balance}
              </div>
              <div className="text-xs font-semibold text-fun-text-muted">
                XP à dépenser
              </div>
            </div>
          </div>
        </div>

        <div className="mt-4">
          <div className="mb-1 flex justify-between text-sm font-semibold text-fun-text-muted">
            <span>Collection</span>
            <span>
              {ownedCount} / {total}
            </span>
          </div>
          <div className="h-3 w-full overflow-hidden rounded-full bg-fun-green-light">
            <div
              className="h-3 rounded-full bg-fun-green transition-all"
              style={{ width: `${total ? (ownedCount / total) * 100 : 0}%` }}
            />
          </div>
        </div>
      </div>

      {celebrating && (
        <div className="mb-4 flex animate-[candy-pop_0.6s_ease-out] items-center justify-center gap-2 rounded-2xl bg-fun-green-light px-4 py-3 text-lg font-bold text-fun-text">
          <Sparkles className="h-5 w-5 text-fun-green" />
          {celebrating} rejoint ta collection&nbsp;!
        </div>
      )}
      {error && (
        <div className="mb-4 rounded-2xl bg-fun-red-light px-4 py-3 text-center font-semibold text-fun-red">
          {error}
        </div>
      )}

      {/* Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {pokedex.map((p) => {
          const affordable = balance >= p.price;
          return (
            <div
              key={p.id}
              className={cn(
                "flex flex-col items-center rounded-2xl border-2 bg-white p-3 candy-shadow transition-all",
                p.owned ? "border-fun-green" : "border-fun-border"
              )}
            >
              <span className="self-start text-xs font-bold text-fun-text-muted">
                #{String(p.id).padStart(3, "0")}
              </span>
              {p.owned ? (
                <button
                  type="button"
                  onClick={() => setSelected(p)}
                  className="flex flex-col items-center transition-transform active:scale-95"
                  aria-label={`Voir la carte de ${p.name_fr}`}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={p.image_url}
                    alt={p.name_fr}
                    loading="lazy"
                    className="h-24 w-24 object-contain transition-all hover:scale-105"
                  />
                  <div className="mt-1 h-6 text-center text-sm font-bold text-fun-text">
                    {p.name_fr}
                  </div>
                </button>
              ) : (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={p.image_url}
                    alt="Pokémon mystère"
                    loading="lazy"
                    className="h-24 w-24 object-contain opacity-40 [filter:grayscale(1)_brightness(0.6)]"
                  />
                  <div className="mt-1 h-6 text-center text-sm font-bold text-fun-text">
                    ???
                  </div>
                </>
              )}

              {p.owned ? (
                <div className="mt-2 flex items-center gap-1 rounded-full bg-fun-green-light px-3 py-1 text-xs font-bold text-fun-green-dark">
                  <Star className="h-3 w-3 fill-fun-green text-fun-green" />
                  Voir la carte
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => buy(p)}
                  disabled={!affordable || purchase.isPending}
                  className={cn(
                    "mt-2 flex min-h-[40px] items-center gap-1 rounded-xl px-3 py-2 text-sm font-bold transition-all active:scale-95",
                    affordable
                      ? "bg-fun-green text-white hover:bg-fun-green-dark"
                      : "cursor-not-allowed bg-fun-border text-fun-text-muted"
                  )}
                >
                  {affordable ? (
                    <>
                      <Star className="h-4 w-4 fill-fun-sun text-fun-sun" />
                      {p.price} XP
                    </>
                  ) : (
                    <>
                      <Lock className="h-4 w-4" />
                      {p.price} XP
                    </>
                  )}
                </button>
              )}
            </div>
          );
        })}
      </div>

      <PokemonCardModal
        id={selected?.id ?? null}
        nameFr={selected?.name_fr ?? ""}
        imageUrl={selected?.image_url ?? ""}
        open={selected !== null}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}
