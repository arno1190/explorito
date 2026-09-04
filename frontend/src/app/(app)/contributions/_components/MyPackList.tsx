"use client";

import { useState } from "react";
import Link from "next/link";
import { BookOpen, ChevronRight, Sparkles, Trash2 } from "lucide-react";

import { useListMyPacksApiV1ContributionsGet as useMyPacks } from "@/lib/api/generated/contributions/contributions";

import { DeletePackDialog } from "./DeletePackDialog";
import { StatusBadge } from "./StatusBadge";
import { isDeletable, statusStyle } from "../_lib/contrib";

export function MyPackList() {
  const { data, isLoading, isError } = useMyPacks();
  const packs = data ?? [];
  /** Pack visé par la confirmation : son titre doit survivre à la disparition de la ligne. */
  const [target, setTarget] = useState<{ id: string; title: string } | null>(
    null
  );

  if (isLoading) {
    return (
      <div className="flex justify-center py-10">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  if (isError) {
    return (
      <p className="rounded-xl border-2 border-fun-red bg-fun-red-light p-3 text-sm font-semibold text-fun-text">
        Impossible de charger vos packs. Rechargez la page.
      </p>
    );
  }

  if (packs.length === 0) {
    return (
      <div className="rounded-2xl border-2 border-dashed border-fun-border bg-fun-card p-6 text-center">
        <Sparkles className="mx-auto h-8 w-8 text-fun-violet" />
        <p className="mt-2 font-bold text-fun-text">
          Aucun pack pour l&apos;instant.
        </p>
        <p className="mt-1 text-sm text-fun-text-muted">
          Demandez un pack à votre assistant IA, puis déposez son fichier
          ci-dessous.
        </p>
      </div>
    );
  }

  return (
    <>
      <ul className="space-y-3">
        {packs.map((pack) => (
          <li
            key={pack.id}
            className="flex items-center gap-1 rounded-2xl border-2 border-fun-border bg-white p-2 candy-shadow transition-all hover:scale-[1.02] hover:candy-shadow-lg"
          >
            <Link
              href={`/contributions/${pack.id}`}
              className="flex min-w-0 flex-1 items-center gap-4 rounded-xl p-2 text-left"
            >
              <span className="text-3xl" aria-hidden>
                {pack.emoji || "📦"}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-extrabold text-fun-text">
                    {pack.title}
                  </span>
                  <StatusBadge status={pack.community_status} />
                </div>
                <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-fun-text-muted">
                  <span className="flex items-center gap-1">
                    <BookOpen className="h-4 w-4 text-fun-sky" />
                    {pack.lesson_count ?? 0} leçon
                    {(pack.lesson_count ?? 0) > 1 ? "s" : ""}
                  </span>
                  <span>
                    Qualité&nbsp;:{" "}
                    {pack.quality_score == null
                      ? "—"
                      : `${Math.round(pack.quality_score)}/100`}
                  </span>
                </p>
                <p className="mt-1 text-xs text-fun-text-muted">
                  {statusStyle(pack.community_status).hint}
                </p>
              </div>
              <ChevronRight className="h-5 w-5 shrink-0 text-fun-text-muted" />
            </Link>
            {isDeletable(pack.community_status) && (
              <button
                type="button"
                aria-label="Supprimer le pack"
                title="Supprimer le pack"
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-fun-text-muted transition-all hover:bg-fun-red-light hover:text-fun-red active:scale-95"
                onClick={(event) => {
                  // La ligne entière mène à l'aperçu : ce geste-ci ne doit pas y aller.
                  event.preventDefault();
                  event.stopPropagation();
                  setTarget({ id: pack.id, title: pack.title });
                }}
              >
                <Trash2 className="h-5 w-5" />
              </button>
            )}
          </li>
        ))}
      </ul>

      {target && (
        <DeletePackDialog
          open
          onOpenChange={(open) => {
            if (!open) setTarget(null);
          }}
          packId={target.id}
          packTitle={target.title}
          onDeleted={() => setTarget(null)}
        />
      )}
    </>
  );
}
