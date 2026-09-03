"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import type { ApiFailure } from "../_lib/contrib";

const FAILURE_TITLES: Record<string, string> = {
  not_a_draft: "Ce pack n'est plus un brouillon",
  too_many_pending: "Trop de packs déjà en attente",
};

export function SubmitDialog({
  open,
  onOpenChange,
  pending,
  failure,
  onConfirm,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  pending: boolean;
  failure: ApiFailure | null;
  onConfirm: () => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="text-xl font-extrabold text-fun-text">
            Soumettre ce pack&nbsp;?
          </DialogTitle>
          <DialogDescription className="text-fun-text-muted">
            Ce que la soumission déclenche, dans cet ordre.
          </DialogDescription>
        </DialogHeader>

        <ul className="space-y-2 text-sm text-fun-text">
          <li className="rounded-xl border-2 border-fun-green bg-fun-green-light p-3">
            <strong>Tout de suite</strong> : vos enfants voient le pack et
            peuvent y jouer.
          </li>
          <li className="rounded-xl border-2 border-fun-sky bg-fun-sky-light p-3">
            <strong>Après relecture</strong> : les autres familles peuvent
            l&apos;ajouter. Personne d&apos;autre n&apos;y a accès avant.
          </li>
          <li className="rounded-xl border-2 border-fun-violet bg-fun-violet-light p-3">
            <strong>Une fois publié</strong> : le pack est verrouillé. Pour le
            corriger, vous le clonerez et le clone repassera en revue.
          </li>
        </ul>

        {failure && (
          <div className="rounded-xl border-2 border-fun-red bg-fun-red-light p-3">
            <p className="font-bold text-fun-text">
              {(failure.code && FAILURE_TITLES[failure.code]) ??
                "Soumission impossible"}
            </p>
            <p className="mt-1 text-sm text-fun-text">{failure.message}</p>
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={pending}
          >
            Pas maintenant
          </Button>
          <Button onClick={onConfirm} disabled={pending}>
            {pending ? "Envoi…" : "Soumettre"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
