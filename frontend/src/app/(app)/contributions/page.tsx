"use client";

import { useState } from "react";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { GraduationCap, Library, Lock } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  getGetTermsApiV1ContributionsTermsGetQueryKey,
  useGetTermsApiV1ContributionsTermsGet as useContributorTerms,
} from "@/lib/api/generated/contributions/contributions";

import { MyPackList } from "./_components/MyPackList";
import { PairingCard } from "./_components/PairingCard";
import { TermsGateDialog } from "./_components/TermsGateDialog";
import { TokenPanel } from "./_components/TokenPanel";
import { UploadPanel } from "./_components/UploadPanel";

/**
 * Espace de contribution du parent : ses packs, le dépôt d'un nouveau pack et
 * la connexion de son assistant IA. Rien ici n'est visible d'un enfant.
 *
 * Tant que les conditions ne sont pas acceptées, la page reste inerte : le
 * parent doit les découvrir en arrivant, pas au moment où son envoi échoue.
 */
export default function ContributionsPage() {
  const queryClient = useQueryClient();
  const termsQuery = useContributorTerms();

  // `forced` couvre le 428 résiduel : il rouvre le dialogue même si l'état
  // local croyait encore les conditions acceptées (version remplacée).
  const [dismissed, setDismissed] = useState(false);
  const [forced, setForced] = useState(false);

  if (termsQuery.isPending) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  const terms = termsQuery.data;
  const locked = terms?.accepted !== true;
  const modalOpen = forced || (locked && !dismissed);

  const openTerms = () => {
    setDismissed(false);
    setForced(true);
    // Un 428 alors que l'état local croit les conditions acceptées signale une
    // version remplacée : on resynchronise pour reverrouiller la page derrière
    // le dialogue.
    queryClient.invalidateQueries({
      queryKey: getGetTermsApiV1ContributionsTermsGetQueryKey(),
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light p-4 pb-20 md:pb-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <header className="rounded-2xl bg-white p-5 candy-shadow">
          <h1 className="text-2xl font-extrabold text-fun-text">
            Mes contributions
          </h1>
          <p className="mt-1 text-sm text-fun-text-muted">
            Écrivez des leçons avec votre assistant IA, relisez-les, puis
            partagez-les avec les autres familles si vous le souhaitez.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              href="/tutoriel/lecons-communautaires"
              className="inline-flex min-h-12 items-center gap-2 rounded-xl border-2 border-fun-sky bg-fun-sky-light px-4 font-semibold text-fun-text transition-transform active:scale-95"
            >
              <GraduationCap className="h-5 w-5 text-fun-sky" />
              Comment ça marche&nbsp;?
            </Link>
            <Link
              href="/bibliotheque"
              className="inline-flex min-h-12 items-center gap-2 rounded-xl border-2 border-fun-border bg-white px-4 font-semibold text-fun-text transition-transform active:scale-95"
            >
              <Library className="h-5 w-5 text-fun-violet" />
              Bibliothèque
            </Link>
          </div>
        </header>

        {termsQuery.isError && (
          <div className="rounded-2xl border-2 border-fun-red bg-fun-red-light p-5">
            <p className="font-extrabold text-fun-text">
              Impossible de lire les conditions de contribution.
            </p>
            <p className="mt-1 text-sm text-fun-text">
              La page reste inactive tant qu&apos;elles n&apos;ont pas été
              chargées et acceptées.
            </p>
            <Button
              type="button"
              className="mt-3"
              onClick={() => termsQuery.refetch()}
            >
              Réessayer
            </Button>
          </div>
        )}

        {locked && !termsQuery.isError && (
          <div className="rounded-2xl border-2 border-fun-accent bg-fun-accent-light p-5">
            <p className="flex items-center gap-2 font-extrabold text-fun-text">
              <Lock className="h-5 w-5 shrink-0 text-fun-accent-dark" />
              Cette page est inactive
            </p>
            <p className="mt-1 text-sm text-fun-text">
              Vous devez d&apos;abord accepter les conditions de contribution :
              tant que ce n&apos;est pas fait, vous ne pouvez ni envoyer un
              pack, ni connecter un assistant.
            </p>
            <Button type="button" className="mt-3" onClick={openTerms}>
              Lire et accepter les conditions
            </Button>
          </div>
        )}

        {/* `fieldset disabled` neutralise réellement boutons, champs et envois ;
            l'opacité et `pointer-events-none` ne sont que le signal visuel. */}
        <fieldset
          disabled={locked}
          className={cn(
            "m-0 min-w-0 space-y-6 border-0 p-0",
            locked && "select-none opacity-50 pointer-events-none"
          )}
        >
          <section className="rounded-2xl bg-white p-5 candy-shadow">
            <h2 className="mb-4 text-xl font-extrabold text-fun-text">
              Mes packs
            </h2>
            <MyPackList />
          </section>

          <PairingCard disabled={locked} />
          <UploadPanel disabled={locked} onTermsRequired={openTerms} />

          <details className="rounded-2xl border-2 border-fun-border bg-fun-card p-2">
            <summary className="flex min-h-12 cursor-pointer items-center px-3 font-semibold text-fun-text">
              Je préfère gérer un jeton moi-même
            </summary>
            <div className="mt-2">
              <TokenPanel disabled={locked} />
            </div>
          </details>
        </fieldset>

        {!locked && terms && (
          <p className="px-1 text-xs text-fun-text-muted">
            Conditions de contribution version {terms.version} acceptées
            {terms.handle ? ` sous le pseudonyme « ${terms.handle} »` : ""}.
          </p>
        )}
      </div>

      <TermsGateDialog
        open={modalOpen}
        onOpenChange={(open) => {
          setForced(open);
          setDismissed(!open);
        }}
        terms={terms}
        loading={termsQuery.isFetching}
      />
    </div>
  );
}
