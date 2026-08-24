"use client";

import { useRef } from "react";
import { Lock, Star } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CatalogGridItem } from "@/lib/api/model";

export type Rarity = "common" | "rare" | "epic" | "legendary";

const RARITY_LABEL: Record<Rarity, string> = {
  common: "Commune",
  rare: "Rare",
  epic: "Épique",
  legendary: "Légendaire",
};

interface CollectibleCardProps {
  item: CatalogGridItem;
  rarity: Rarity;
  currency: "points" | "behavior";
  affordable: boolean;
  pending: boolean;
  /** Joue l'animation de révélation (carte tout juste débloquée). */
  justUnlocked?: boolean;
  onBuy: (item: CatalogGridItem) => void;
  onOpen: (item: CatalogGridItem) => void;
}

/**
 * Carte à collectionner : format 1:1.4, cadre selon la rareté (dérivée du prix),
 * reflet holographique réactif au pointeur (rare+), dos « mystère » tant qu'elle
 * n'est pas débloquée, et révélation en retournement à l'achat.
 */
export function CollectibleCard({
  item,
  rarity,
  currency,
  affordable,
  pending,
  justUnlocked,
  onBuy,
  onOpen,
}: CollectibleCardProps) {
  const cardRef = useRef<HTMLButtonElement>(null);
  const holo = rarity !== "common";

  // Reflet holo : suit le pointeur (variables CSS lues par .art::after).
  const onMove = (e: React.PointerEvent<HTMLButtonElement>) => {
    const el = cardRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty("--mx", String((e.clientX - r.left) / r.width));
    el.style.setProperty("--my", String((e.clientY - r.top) / r.height));
  };

  return (
    <div className="flex flex-col items-center gap-2">
      {item.owned ? (
        <button
          ref={cardRef}
          type="button"
          onPointerMove={holo ? onMove : undefined}
          onClick={() => onOpen(item)}
          aria-label={`Voir ${item.name_fr}`}
          className={cn(
            "tc block w-full transition-transform hover:-translate-y-0.5 active:scale-95",
            rarity,
            holo && "holo",
            justUnlocked && "flip"
          )}
        >
          <div className="tc-inner">
            <div className="face front candy-shadow">
              <div className="art">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={item.image_url} alt={item.name_fr} loading="lazy" />
              </div>
              <div className="cap">
                <b>{item.name_fr}</b>
                <span className="rar-badge">{RARITY_LABEL[rarity]}</span>
              </div>
            </div>
          </div>
        </button>
      ) : (
        <div className={cn("tc", rarity)} aria-hidden="true">
          <div className="tc-inner">
            <div className="face back">
              <span className="q">?</span>
              <small>Explorito</small>
            </div>
          </div>
        </div>
      )}

      <span className="text-[11px] font-bold text-fun-text-muted">
        #{String(item.id).padStart(3, "0")}
      </span>

      {item.owned ? (
        <span className="flex items-center gap-1 rounded-full bg-fun-green-light px-3 py-1 text-xs font-bold text-fun-green-dark">
          <Star className="h-3 w-3 fill-fun-green text-fun-green" />
          Ma carte
        </span>
      ) : (
        <button
          type="button"
          onClick={() => onBuy(item)}
          disabled={!affordable || pending}
          className={cn(
            "flex min-h-[40px] w-full items-center justify-center gap-1 rounded-xl px-3 py-2 text-sm font-bold transition-all active:scale-95",
            affordable
              ? "bg-fun-green text-white shadow-[0_4px_0_var(--fun-green-dark)] active:translate-y-[4px] active:shadow-none"
              : "cursor-not-allowed bg-fun-border text-fun-text-muted"
          )}
        >
          {affordable ? (
            <span aria-hidden>{currency === "behavior" ? "💚" : "⭐"}</span>
          ) : (
            <Lock className="h-4 w-4" />
          )}
          {item.price}
        </button>
      )}
    </div>
  );
}
