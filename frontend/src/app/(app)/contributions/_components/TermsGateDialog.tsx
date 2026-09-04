"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ScrollText } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  getGetTermsApiV1ContributionsTermsGetQueryKey,
  useAcceptTermsApiV1ContributionsTermsAcceptPost as useAcceptTerms,
} from "@/lib/api/generated/contributions/contributions";
import type { ContributorTerms } from "@/lib/api/model";

import { parseApiFailure } from "../_lib/contrib";

/**
 * Seul composant qui affiche le texte des conditions : il sert aussi bien à
 * l'ouverture automatique en arrivant sur la page qu'au repli du 428 d'envoi.
 */
export function TermsGateDialog({
  open,
  onOpenChange,
  terms,
  loading,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  terms: ContributorTerms | undefined;
  loading: boolean;
}) {
  const queryClient = useQueryClient();
  const [checked, setChecked] = useState(false);
  const [handle, setHandle] = useState("");
  const [error, setError] = useState<string | null>(null);

  const accept = useAcceptTerms({
    mutation: {
      onSuccess: (updated) => {
        setError(null);
        // La réponse porte déjà l'état accepté : on la pose dans le cache pour
        // déverrouiller la page immédiatement, l'invalidation ne fait que
        // resynchroniser derrière, sans rechargement.
        const key = getGetTermsApiV1ContributionsTermsGetQueryKey();
        queryClient.setQueryData(key, updated);
        queryClient.invalidateQueries({ queryKey: key });
        onOpenChange(false);
      },
      onError: (failure: unknown) => {
        const parsed = parseApiFailure(failure);
        setError(
          parsed.status === 409
            ? "Ce pseudonyme est déjà pris. Choisissez-en un autre."
            : parsed.message
        );
      },
    },
  });

  const trimmed = handle.trim();
  const handleOk = trimmed.length >= 3 && trimmed.length <= 24;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl font-extrabold text-fun-text">
            <ScrollText className="h-5 w-5 shrink-0 text-fun-green" />
            Conditions de contribution
          </DialogTitle>
          <DialogDescription className="text-fun-text-muted">
            À accepter une seule fois pour utiliser cet espace.
            {terms?.version ? ` Version ${terms.version}.` : ""}
          </DialogDescription>
        </DialogHeader>

        <p className="text-sm text-fun-text">
          En partageant un pack, vous autorisez Explorito et les autres familles
          à le diffuser <strong>et à le modifier</strong> (corriger une faute,
          adapter un niveau). Vous confirmez que ce contenu est bien le vôtre,
          vous acceptez qu&apos;il soit publié pour d&apos;autres familles, et
          vous êtes informé que vos packs restent en ligne si vous supprimez
          votre compte&nbsp;: ils sont alors rendus anonymes.
        </p>

        <div className="max-h-[40vh] overflow-y-auto whitespace-pre-wrap rounded-2xl border-2 border-fun-border bg-fun-card p-4 text-sm text-fun-text">
          {terms?.text ?? (loading ? "Chargement des conditions…" : "")}
        </div>

        <label className="flex min-h-12 cursor-pointer items-start gap-3 rounded-2xl border-2 border-fun-border bg-white p-3">
          <input
            type="checkbox"
            checked={checked}
            onChange={(event) => setChecked(event.target.checked)}
            className="mt-1 h-5 w-5 shrink-0 accent-fun-green"
          />
          <span className="text-sm font-semibold text-fun-text">
            J&apos;ai lu et j&apos;accepte les conditions de contribution.
          </span>
        </label>

        <div className="space-y-2">
          <Label htmlFor="contrib-handle" className="text-fun-text">
            Votre pseudonyme public
          </Label>
          <Input
            id="contrib-handle"
            value={handle}
            onChange={(event) => setHandle(event.target.value)}
            placeholder="Le Parent Curieux"
            maxLength={24}
            autoComplete="off"
          />
          <p className="text-xs text-fun-text-muted">
            De 3 à 24 caractères. C&apos;est la seule chose publiée à votre
            sujet&nbsp;: jamais votre vrai nom, ni votre email.
          </p>
        </div>

        {error && (
          <p className="rounded-xl border-2 border-fun-red bg-fun-red-light p-3 text-sm font-semibold text-fun-text">
            {error}
          </p>
        )}

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={accept.isPending}
          >
            Plus tard
          </Button>
          <Button
            type="button"
            onClick={() => accept.mutate({ data: { handle: trimmed } })}
            disabled={!checked || !handleOk || accept.isPending}
          >
            {accept.isPending ? "Envoi…" : "Accepter et activer la page"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
