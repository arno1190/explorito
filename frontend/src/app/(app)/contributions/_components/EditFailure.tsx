"use client";

import { Copy, Lock } from "lucide-react";

import { Button } from "@/components/ui/button";

import type { ApiFailure } from "../_lib/contrib";
import { IssueList } from "./IssueList";

/**
 * Refus d'un enregistrement. Le 409 « pack_locked » n'est pas une panne mais la
 * règle : un pack approuvé est figé pour son auteur, sinon la communauté
 * recevrait une modification jamais relue. La seule issue est le clone.
 */
export function EditFailure({
  failure,
  onClone,
  cloning,
}: {
  failure: ApiFailure;
  onClone: () => void;
  cloning: boolean;
}) {
  if (failure.code === "pack_locked") {
    return (
      <div className="mt-3 rounded-2xl border-2 border-fun-violet bg-fun-violet-light p-4">
        <p className="flex items-center gap-2 font-extrabold text-fun-text">
          <Lock className="h-5 w-5 text-fun-violet" />
          Ce pack est verrouillé
        </p>
        <p className="mt-1 text-sm text-fun-text">
          D&apos;autres familles l&apos;utilisent déjà : une modification
          partirait sans relecture. Clonez-le pour en proposer une révision, qui
          repassera en revue. L&apos;original garde sa progression.
        </p>
        <Button className="mt-3" onClick={onClone} disabled={cloning}>
          <Copy className="h-4 w-4" />
          {cloning ? "Clonage…" : "Cloner pour réviser"}
        </Button>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-2xl border-2 border-fun-red bg-fun-red-light p-4">
      <p className="font-extrabold text-fun-text">
        {failure.issues.length > 0
          ? "Enregistrement refusé : le pack deviendrait invalide"
          : "Enregistrement refusé"}
      </p>
      <p className="mt-1 text-sm text-fun-text">{failure.message}</p>
      {failure.issues.length > 0 && (
        <>
          <p className="mt-2 text-sm text-fun-text">
            Votre saisie est conservée : corrigez ces points, puis enregistrez à
            nouveau.
          </p>
          <IssueList className="mt-2" issues={failure.issues} />
        </>
      )}
    </div>
  );
}
