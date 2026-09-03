"use client";

import Link from "next/link";
import { PenLine, ShieldCheck, Sparkles, Users } from "lucide-react";
import { useGetContributorStatsApiV1LibraryMeContributorStatsGet as useContributorStats } from "@/lib/api/generated/library/library";
import { Button } from "@/components/ui/button";
import { Pill } from "./pack-ui";

/**
 * Mes contributions. La reconnaissance est la seule récompense offerte aux
 * auteurs : ces nombres doivent être visibles, et réels.
 */
export function ContributorCard() {
  const { data: stats, isPending } = useContributorStats();

  return (
    <div className="rounded-2xl border-2 border-fun-violet bg-white p-4 candy-shadow">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-lg font-bold text-fun-text">
          <Sparkles className="h-5 w-5 text-fun-violet" />
          Mes contributions
        </h2>
        {stats?.handle ? <Pill tone="violet">@{stats.handle}</Pill> : null}
        {stats?.trusted ? (
          <Pill tone="green">
            <ShieldCheck className="mr-1 inline h-3 w-3" />
            Auteur de confiance
          </Pill>
        ) : null}
      </div>

      {isPending ? (
        <p className="mt-3 text-sm text-fun-text-muted">Chargement…</p>
      ) : !stats?.handle ? (
        <p className="mt-3 text-sm text-fun-text-muted">
          Vous n&apos;avez encore rien publié. Une leçon que vous écrivez pour
          votre enfant peut servir à d&apos;autres familles.
        </p>
      ) : (
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-xl bg-fun-green-light p-3 text-center">
            <p className="text-2xl font-extrabold text-fun-green-dark">
              {stats.packs_approved ?? 0}
            </p>
            <p className="text-xs font-semibold text-fun-text-muted">
              packs approuvés
            </p>
          </div>
          <div className="rounded-xl bg-fun-sun-light p-3 text-center">
            <p className="text-2xl font-extrabold text-fun-accent-dark">
              {stats.packs_pending ?? 0}
            </p>
            <p className="text-xs font-semibold text-fun-text-muted">
              en attente de relecture
            </p>
          </div>
          <div className="rounded-xl bg-fun-sky-light p-3 text-center">
            <p className="text-2xl font-extrabold text-fun-sky">
              {stats.families_reached ?? 0}
            </p>
            <p className="text-xs font-semibold text-fun-text-muted">
              <Users className="mr-1 inline h-3 w-3" />
              familles touchées
            </p>
          </div>
          <div className="rounded-xl bg-fun-violet-light p-3 text-center">
            <p className="text-2xl font-extrabold text-fun-violet">
              {stats.times_enabled ?? 0}
            </p>
            <p className="text-xs font-semibold text-fun-text-muted">
              activations
            </p>
          </div>
        </div>
      )}

      <Button asChild variant="outline" className="mt-3 w-full sm:w-auto">
        <Link href="/contributions">
          <PenLine className="mr-2 h-4 w-4" />
          Créer ou envoyer des leçons
        </Link>
      </Button>
    </div>
  );
}
