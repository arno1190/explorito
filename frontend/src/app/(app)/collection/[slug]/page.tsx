"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ChevronLeft, Sparkles } from "lucide-react";

import { Confetti } from "@/components/gamification/Confetti";
import { PokemonCardModal } from "@/components/pokedex/PokemonCardModal";
import { CollectibleModal } from "@/components/pokedex/CollectibleModal";
import {
  CollectibleCard,
  type Rarity,
} from "@/components/pokedex/CollectibleCard";
import { cn } from "@/lib/utils";
import {
  useGetCatalogApiV1CollectionCatalogsSlugGet as useCatalog,
  useGetWalletApiV1CollectionMeGet as useWallet,
  usePurchaseApiV1CollectionPurchasePost as usePurchase,
} from "@/lib/api/generated/collection/collection";
import type { CatalogGridItem } from "@/lib/api/model";

export default function CatalogPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;

  const catalogQuery = useCatalog(slug);
  const walletQuery = useWallet();
  const purchase = usePurchase();

  const [celebrating, setCelebrating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<CatalogGridItem | null>(null);
  const [filter, setFilter] = useState<"all" | "owned" | "locked">("all");
  const [rarityFilter, setRarityFilter] = useState<"all" | Rarity>("all");
  const [sort, setSort] = useState<
    "number" | "name" | "rarity" | "price-asc" | "price-desc"
  >("number");
  const [currency, setCurrency] = useState<"points" | "behavior">("points");
  const [justUnlockedId, setJustUnlockedId] = useState<number | null>(null);

  const wallet = walletQuery.data;
  const pointsBalance = wallet?.balance ?? 0;
  const behaviorBalance = wallet?.behavior_balance ?? 0;
  const balance = currency === "behavior" ? behaviorBalance : pointsBalance;
  const info = walletQuery.data?.catalogs?.find((c) => c.slug === slug);
  const items = catalogQuery.data ?? [];
  // Rareté dérivée du prix (percentiles au sein du catalogue) : les objets les
  // plus chers sont les plus rares.
  const prices = items.map((i) => i.price).sort((a, b) => a - b);
  const q = (f: number) =>
    prices.length
      ? prices[Math.min(prices.length - 1, Math.floor(prices.length * f))]
      : 0;
  const cut = { rare: q(0.55), epic: q(0.8), legend: q(0.95) };
  const rarityFor = (price: number): Rarity =>
    price >= cut.legend
      ? "legendary"
      : price >= cut.epic
        ? "epic"
        : price >= cut.rare
          ? "rare"
          : "common";
  const ownedCount = items.filter((p) => p.owned).length;
  const total = items.length;
  // Filtre par statut → puis par rareté → puis tri.
  const statusFiltered = items.filter((p) =>
    filter === "owned" ? p.owned : filter === "locked" ? !p.owned : true
  );
  const RARITY_ORDER: Record<Rarity, number> = {
    legendary: 3,
    epic: 2,
    rare: 1,
    common: 0,
  };
  const rarityCounts: Record<Rarity, number> = {
    common: 0,
    rare: 0,
    epic: 0,
    legendary: 0,
  };
  statusFiltered.forEach((p) => (rarityCounts[rarityFor(p.price)] += 1));
  const rarityFiltered =
    rarityFilter === "all"
      ? statusFiltered
      : statusFiltered.filter((p) => rarityFor(p.price) === rarityFilter);
  const sorted = [...rarityFiltered].sort((a, b) => {
    switch (sort) {
      case "name":
        return a.name_fr.localeCompare(b.name_fr, "fr");
      case "rarity":
        return (
          RARITY_ORDER[rarityFor(b.price)] - RARITY_ORDER[rarityFor(a.price)] ||
          a.id - b.id
        );
      case "price-asc":
        return a.price - b.price || a.id - b.id;
      case "price-desc":
        return b.price - a.price || a.id - b.id;
      default:
        return a.id - b.id;
    }
  });

  const FILTERS: { key: typeof filter; label: string }[] = [
    { key: "all", label: `Tous (${total})` },
    { key: "owned", label: `Ma collection (${ownedCount})` },
    { key: "locked", label: `À débloquer (${total - ownedCount})` },
  ];

  const buy = async (entry: CatalogGridItem) => {
    setError(null);
    try {
      const res = await purchase.mutateAsync({
        data: { catalog: slug, item_id: entry.id, currency },
      });
      await Promise.all([catalogQuery.refetch(), walletQuery.refetch()]);
      setCelebrating(res.item.name_fr);
      setJustUnlockedId(res.item.id);
      window.setTimeout(() => setCelebrating(null), 1800);
      window.setTimeout(() => setJustUnlockedId(null), 1200);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Achat impossible pour le moment";
      setError(detail);
    }
  };

  if (catalogQuery.isLoading || walletQuery.isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-6xl p-4 pb-24 sm:p-6">
      <Confetti show={!!celebrating} onComplete={() => setCelebrating(null)} />

      <button
        onClick={() => router.push("/collection")}
        className="mb-4 inline-flex items-center gap-1 font-semibold text-fun-text-muted hover:text-fun-green"
      >
        <ChevronLeft className="h-5 w-5" /> Mes collections
      </button>

      {/* Wallet header */}
      <div className="mb-6 rounded-3xl bg-white p-6 candy-shadow">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-fun-text sm:text-3xl">
              {info?.icon} {info?.name ?? "Collection"}
            </h1>
            <p className="mt-1 text-fun-text-muted">
              Choisis ta cagnotte et débloque&nbsp;!
            </p>
          </div>
          {/* Sélecteur de porte-monnaie : le solde actif pilote les achats. */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setCurrency("points")}
              className={cn(
                "flex items-center gap-2 rounded-2xl px-5 py-3 transition-all active:scale-95",
                currency === "points"
                  ? "bg-fun-sun-light ring-2 ring-fun-sun"
                  : "bg-fun-surface candy-shadow opacity-70 hover:opacity-100"
              )}
              aria-pressed={currency === "points"}
            >
              <span className="text-2xl">⭐</span>
              <div className="text-left">
                <div className="text-2xl font-extrabold text-fun-text">
                  {pointsBalance}
                </div>
                <div className="text-xs font-semibold text-fun-text-muted">
                  Points
                </div>
              </div>
            </button>
            <button
              type="button"
              onClick={() => setCurrency("behavior")}
              className={cn(
                "flex items-center gap-2 rounded-2xl px-5 py-3 transition-all active:scale-95",
                currency === "behavior"
                  ? "bg-fun-green-light ring-2 ring-fun-green"
                  : "bg-fun-surface candy-shadow opacity-70 hover:opacity-100"
              )}
              aria-pressed={currency === "behavior"}
            >
              <span className="text-2xl">💚</span>
              <div className="text-left">
                <div className="text-2xl font-extrabold text-fun-text">
                  {behaviorBalance}
                </div>
                <div className="text-xs font-semibold text-fun-text-muted">
                  Comportement
                </div>
              </div>
            </button>
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

      {/* Filter */}
      <div className="mb-4 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            type="button"
            onClick={() => setFilter(f.key)}
            className={cn(
              "min-h-[40px] rounded-full px-4 py-2 text-sm font-bold transition-all active:scale-95",
              filter === f.key
                ? "bg-fun-green text-white"
                : "bg-white text-fun-text candy-shadow hover:bg-fun-green-light"
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Rareté + tri */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {(
          [
            { key: "all", label: "Toutes", dot: "" },
            {
              key: "common",
              label: `Communes (${rarityCounts.common})`,
              dot: "#94a3b8",
            },
            {
              key: "rare",
              label: `Rares (${rarityCounts.rare})`,
              dot: "var(--fun-sky)",
            },
            {
              key: "epic",
              label: `Épiques (${rarityCounts.epic})`,
              dot: "var(--fun-violet)",
            },
            {
              key: "legendary",
              label: `Légendaires (${rarityCounts.legendary})`,
              dot: "var(--fun-sun)",
            },
          ] as const
        ).map((r) => (
          <button
            key={r.key}
            type="button"
            onClick={() => setRarityFilter(r.key)}
            className={cn(
              "flex min-h-[36px] items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-bold transition-all active:scale-95",
              rarityFilter === r.key
                ? "bg-fun-text text-white"
                : "bg-white text-fun-text candy-shadow hover:bg-fun-green-light"
            )}
          >
            {r.dot && (
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ background: r.dot }}
              />
            )}
            {r.label}
          </button>
        ))}

        <label className="ml-auto flex items-center gap-2 text-sm font-semibold text-fun-text-muted">
          Trier&nbsp;:
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as typeof sort)}
            className="h-9 rounded-xl border-2 border-fun-border bg-white px-2 text-sm font-semibold text-fun-text outline-none focus:border-fun-green"
          >
            <option value="number">Numéro</option>
            <option value="name">Nom (A–Z)</option>
            <option value="rarity">Rareté</option>
            <option value="price-asc">Prix ↑</option>
            <option value="price-desc">Prix ↓</option>
          </select>
        </label>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {sorted.map((p) => (
          <CollectibleCard
            key={p.id}
            item={p}
            rarity={rarityFor(p.price)}
            currency={currency}
            affordable={balance >= p.price}
            pending={purchase.isPending}
            justUnlocked={justUnlockedId === p.id}
            onBuy={buy}
            onOpen={setSelected}
          />
        ))}
      </div>

      {sorted.length === 0 && (
        <div className="mt-8 text-center text-fun-text-muted">
          {filter === "owned"
            ? "Rien ici pour l'instant. Gagne de l'XP pour débloquer !"
            : "Aucun objet dans cette catégorie."}
        </div>
      )}

      {/* Detail modal: rich PokéAPI card for Pokémon, simple card otherwise */}
      {slug === "pokemon" ? (
        <PokemonCardModal
          id={selected?.id ?? null}
          nameFr={selected?.name_fr ?? ""}
          imageUrl={selected?.image_url ?? ""}
          open={selected !== null}
          onClose={() => setSelected(null)}
        />
      ) : (
        <CollectibleModal
          open={selected !== null}
          onClose={() => setSelected(null)}
          name={selected?.name_fr ?? ""}
          imageUrl={selected?.image_url ?? ""}
          fact={selected?.fact}
        />
      )}
    </div>
  );
}
