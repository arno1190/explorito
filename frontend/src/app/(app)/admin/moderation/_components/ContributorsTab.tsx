"use client";

import { useQueryClient } from "@tanstack/react-query";
import { ShieldCheck, Users } from "lucide-react";
import {
  useGetContributorsApiV1ModerationContributorsGet as useContributors,
  useSetTrustApiV1ModerationContributorsUserIdTrustPost as useSetTrust,
} from "@/lib/api/generated/moderation/moderation";
import {
  frDate,
  Pill,
  Toggle,
} from "@/app/(app)/bibliotheque/_components/pack-ui";

/**
 * Palier de confiance : un auteur « de confiance » publie sans revue préalable,
 * donc le palier doit être explicite, justifié par des nombres, et révocable.
 */
export function ContributorsTab() {
  const queryClient = useQueryClient();
  const { data: contributors, isPending } = useContributors({ limit: 200 });
  const setTrust = useSetTrust({
    mutation: {
      onSuccess: () =>
        queryClient.invalidateQueries({
          predicate: (query) =>
            typeof query.queryKey[0] === "string" &&
            query.queryKey[0].startsWith("/api/v1/moderation"),
        }),
    },
  });

  if (isPending) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  const rows = contributors ?? [];

  return (
    <div className="space-y-4">
      <p className="rounded-2xl border-2 border-fun-sky bg-fun-sky-light p-4 text-sm text-fun-text">
        Un auteur de confiance voit ses packs publiés sans relecture préalable ;
        les signalements des parents deviennent alors le filet de sécurité. Le
        palier est accordé à la main, et retirable à tout moment.
      </p>

      {rows.length === 0 ? (
        <p className="rounded-2xl border-2 border-fun-border bg-white p-4 text-sm text-fun-text-muted">
          Aucun contributeur pour le moment.
        </p>
      ) : (
        <ul className="space-y-2">
          {rows.map((row) => (
            <li
              key={row.user_id}
              className={`rounded-2xl border-2 bg-white p-4 text-left candy-shadow transition-all ${
                row.trusted ? "border-fun-green" : "border-fun-border"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="flex items-center gap-2 font-bold text-fun-text">
                    @{row.handle}
                    {row.trusted ? (
                      <ShieldCheck className="h-4 w-4 shrink-0 text-fun-green" />
                    ) : null}
                  </p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <Pill tone="green">
                      {row.approved_packs ?? 0} approuvé
                      {(row.approved_packs ?? 0) > 1 ? "s" : ""}
                    </Pill>
                    <Pill tone="sun">{row.pending_packs ?? 0} en attente</Pill>
                    <Pill tone="sky">
                      <Users className="mr-1 inline h-3 w-3" />
                      {row.families_reached ?? 0} famille
                      {(row.families_reached ?? 0) > 1 ? "s" : ""} touchée
                      {(row.families_reached ?? 0) > 1 ? "s" : ""}
                    </Pill>
                    {row.trusted ? (
                      <Pill tone="green">
                        De confiance depuis le {frDate(row.trusted_at)}
                      </Pill>
                    ) : row.trust_eligible ? (
                      <Pill tone="accent">
                        Éligible : {row.approved_packs ?? 0} /{" "}
                        {row.trust_threshold} packs approuvés
                      </Pill>
                    ) : (
                      <Pill tone="violet">
                        Pas encore éligible : {row.approved_packs ?? 0} /{" "}
                        {row.trust_threshold} packs approuvés
                      </Pill>
                    )}
                  </div>
                  <p className="mt-2 text-xs text-fun-text-muted">
                    Conditions acceptées :{" "}
                    {row.terms_version
                      ? `${row.terms_version} le ${frDate(row.terms_accepted_at)}`
                      : "non acceptées"}
                  </p>
                </div>
                <div className="flex min-h-12 items-center gap-3">
                  <span className="text-sm font-semibold text-fun-text">
                    {row.trusted
                      ? "Retirer la confiance"
                      : "Accorder la confiance"}
                  </span>
                  <Toggle
                    checked={row.trusted ?? false}
                    disabled={setTrust.isPending}
                    label={`${row.trusted ? "Retirer" : "Accorder"} le palier de confiance à ${row.handle}`}
                    onChange={(next) =>
                      setTrust.mutate({
                        userId: row.user_id,
                        data: { trusted: next },
                      })
                    }
                  />
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
