"use client";

import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  getListMyPacksApiV1ContributionsGetQueryKey,
  useDeleteMyPackApiV1ContributionsPackIdDelete as useDeletePack,
} from "@/lib/api/generated/contributions/contributions";

import {
  failureCount,
  parseApiFailure,
  type ApiFailure,
} from "../_lib/contrib";

/**
 * Un refus de suppression n'est presque jamais technique : on le raconte donc
 * en entier plutôt que de relayer le message brut du serveur.
 */
function refusalCopy(failure: ApiFailure): { title: string; body: string } {
  switch (failure.code) {
    case "pack_has_progress": {
      const lessons = failureCount(failure, "progress_rows") ?? 0;
      const answers = failureCount(failure, "result_rows") ?? 0;
      const counts =
        lessons === 0 && answers === 0
          ? "Un enfant y a déjà avancé."
          : `Il porte déjà ${lessons} leçon${lessons > 1 ? "s" : ""} commencée${lessons > 1 ? "s" : ""} et ${answers} réponse${answers > 1 ? "s" : ""} enregistrée${answers > 1 ? "s" : ""}.`;
      return {
        title: "Un enfant a déjà travaillé dans ce pack",
        body:
          `${counts} Le supprimer effacerait sa progression et les XP qu'il a gagnés. ` +
          "La suppression est refusée pour protéger ce travail : ce n'est pas une " +
          "limite technique, et il n'existe pas de contournement. Corrigez le pack " +
          "plutôt que de l'effacer.",
      };
    }
    case "pack_not_deletable":
      return {
        title: "Ce pack ne se supprime pas d'ici",
        body:
          "Seuls un brouillon et un pack refusé peuvent être supprimés. Un pack " +
          "publié se retire par la modération, car d'autres familles l'utilisent. " +
          "Un pack en attente de relecture doit d'abord recevoir son verdict.",
      };
    case "pack_locked":
      return {
        title: "Pack verrouillé",
        body:
          "Ce pack est approuvé, donc verrouillé : il ne peut plus être supprimé. " +
          "Clonez-le pour proposer une révision.",
      };
    default:
      return { title: "Suppression impossible", body: failure.message };
  }
}

/**
 * Confirmation d'une suppression définitive : elle nomme le pack pour qu'un
 * parent qui en a plusieurs ne se trompe pas de ligne, et reste ouverte sur un
 * refus pour qu'il en lise la raison.
 */
export function DeletePackDialog({
  open,
  onOpenChange,
  packId,
  packTitle,
  onDeleted,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  packId: string;
  packTitle: string;
  onDeleted: () => void;
}) {
  const queryClient = useQueryClient();
  const [failure, setFailure] = useState<ApiFailure | null>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);

  // La fermeture est le seul moment où l'on oublie un refus : tant que la boîte
  // reste ouverte, le parent doit pouvoir le relire.
  const close = (next: boolean) => {
    if (!next) setFailure(null);
    onOpenChange(next);
  };

  const remove = useDeletePack({
    mutation: {
      onSuccess: () => {
        setFailure(null);
        queryClient.invalidateQueries({
          queryKey: getListMyPacksApiV1ContributionsGetQueryKey(),
        });
        onDeleted();
      },
      onError: (error: unknown) => setFailure(parseApiFailure(error)),
    },
  });

  const refusal = failure ? refusalCopy(failure) : null;

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent
        // Le geste par défaut d'une boîte destructrice est « annuler ».
        onOpenAutoFocus={(event) => {
          event.preventDefault();
          cancelRef.current?.focus();
        }}
      >
        <DialogHeader>
          <DialogTitle className="text-xl font-extrabold text-fun-text">
            Supprimer «&nbsp;{packTitle}&nbsp;»&nbsp;?
          </DialogTitle>
          <DialogDescription className="text-fun-text-muted">
            Cette action est définitive.
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-xl border-2 border-fun-red bg-fun-red-light p-3">
          <p className="flex items-center gap-2 font-bold text-fun-text">
            <AlertTriangle className="h-5 w-5 shrink-0 text-fun-red" />
            Ce qui disparaît
          </p>
          <p className="mt-1 text-sm text-fun-text">
            Le pack «&nbsp;{packTitle}&nbsp;», ses leçons et tous ses exercices
            sont effacés définitivement. Rien n&apos;est mis à la corbeille, et
            nous ne pourrons pas les rétablir.
          </p>
        </div>

        {refusal && (
          <div className="rounded-xl border-2 border-fun-accent bg-fun-accent-light p-3">
            <p className="font-bold text-fun-text">{refusal.title}</p>
            <p className="mt-1 text-sm text-fun-text">{refusal.body}</p>
          </div>
        )}

        <DialogFooter>
          <Button
            ref={cancelRef}
            variant="outline"
            className="min-h-12"
            onClick={() => close(false)}
            disabled={remove.isPending}
          >
            Annuler
          </Button>
          <Button
            variant="destructive"
            className="min-h-12 bg-fun-red text-white"
            onClick={() => {
              setFailure(null);
              remove.mutate({ packId });
            }}
            disabled={remove.isPending}
          >
            <Trash2 className="h-4 w-4" />
            {remove.isPending ? "Suppression…" : "Supprimer définitivement"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
