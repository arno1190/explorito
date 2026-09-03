"use client";

import { useState } from "react";
import type { AxiosError } from "axios";
import { useQueryClient } from "@tanstack/react-query";
import { Eye, Inbox } from "lucide-react";
import {
  getGetPendingRequestsApiV1LibraryRequestsGetQueryKey as pendingRequestsKey,
  useDecideRequestApiV1LibraryRequestsRequestIdDecidePost as useDecideRequest,
  useGetPendingRequestsApiV1LibraryRequestsGet as usePendingRequests,
} from "@/lib/api/generated/library/library";
import type { PackRequestResponse } from "@/lib/api/model";
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
import { frDate } from "./pack-ui";

/** Le backend renvoie 403 + ``detail.code`` pour un PIN erroné ou absent. */
type DecideError = AxiosError<{ detail?: { code?: string; message?: string } }>;

type Pending = { request: PackRequestResponse; approve: boolean };

/**
 * Demandes « Je veux ça ! » des enfants. Le PIN voyage dans le corps de la
 * requête : l'écran est atteignable depuis un téléphone que l'enfant a en
 * main, un garde côté client ne suffirait pas.
 */
export function RequestsPanel({
  onPreview,
}: {
  onPreview: (packId: string) => void;
}) {
  const queryClient = useQueryClient();
  const { data: requests, isPending } = usePendingRequests();
  const [target, setTarget] = useState<Pending | null>(null);
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pinMissing, setPinMissing] = useState(false);

  const decide = useDecideRequest<DecideError>({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: pendingRequestsKey() });
        // Une approbation écrit une ligne d'accès : les clés d'accès sont des
        // chaînes complètes (`/api/v1/library/children/<id>/access`), d'où le
        // prédicat plutôt qu'un préfixe de clé.
        queryClient.invalidateQueries({
          predicate: (query) =>
            typeof query.queryKey[0] === "string" &&
            query.queryKey[0].startsWith("/api/v1/library/children/"),
        });
        closeDialog(false);
      },
      onError: (err) => {
        const code = err.response?.data?.detail?.code;
        if (code === "pin_not_set") {
          setPinMissing(true);
          setError(
            "Aucun code parent n'est défini sur votre compte. Définissez-le depuis le menu de votre avatar, en haut à droite, puis revenez ici."
          );
          return;
        }
        if (code === "invalid_pin") {
          setError("Code incorrect. Réessayez.");
          return;
        }
        setError("La demande n'a pas pu être tranchée. Réessayez.");
      },
    },
  });

  const closeDialog = (next: boolean) => {
    if (!next) {
      setTarget(null);
      setPin("");
      setError(null);
      setPinMissing(false);
      decide.reset();
    }
  };

  const openDecision = (request: PackRequestResponse, approve: boolean) => {
    setPin("");
    setError(null);
    setPinMissing(false);
    setTarget({ request, approve });
  };

  if (isPending) {
    return (
      <div className="flex justify-center py-8">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  const rows = requests ?? [];

  return (
    <>
      {rows.length === 0 ? (
        <p className="flex items-center gap-2 rounded-2xl border-2 border-fun-border bg-white p-4 text-sm text-fun-text-muted">
          <Inbox className="h-5 w-5 shrink-0" />
          Aucune demande en attente. Quand un enfant repère un pack dans
          Découvrir, sa demande apparaît ici.
        </p>
      ) : (
        <ul className="space-y-2">
          {rows.map((request) => (
            <li
              key={request.id}
              className="rounded-2xl border-2 border-fun-sky bg-white p-4 text-left candy-shadow transition-all"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span className="text-3xl">{request.pack_emoji ?? "📦"}</span>
                  <div className="min-w-0">
                    <p className="font-bold text-fun-text">
                      {request.child_name ?? "Votre enfant"} demande «{" "}
                      {request.pack_title} »
                    </p>
                    <p className="text-xs text-fun-text-muted">
                      Demandé le {frDate(request.created_at, true)}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="ghost"
                    onClick={() => onPreview(request.pack_id)}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    Lire le pack
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => openDecision(request, false)}
                  >
                    Refuser
                  </Button>
                  <Button onClick={() => openDecision(request, true)}>
                    Accepter
                  </Button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      <Dialog open={target !== null} onOpenChange={closeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {target?.approve ? "Accepter la demande" : "Refuser la demande"}
            </DialogTitle>
            <DialogDescription>
              {target?.approve
                ? `« ${target?.request.pack_title} » sera activé pour ${target?.request.child_name ?? "votre enfant"}.`
                : `« ${target?.request.pack_title} » ne sera pas activé. ${target?.request.child_name ?? "Votre enfant"} pourra le redemander plus tard.`}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2">
            <Label htmlFor="decision-pin">Votre code parent à 4 chiffres</Label>
            <Input
              id="decision-pin"
              inputMode="numeric"
              autoComplete="off"
              maxLength={4}
              value={pin}
              onChange={(e) => {
                setPin(e.target.value.replace(/\D/g, ""));
                setError(null);
              }}
              className="text-center text-2xl tracking-[0.5em]"
            />
            <p className="text-xs text-fun-text-muted">
              Le code est demandé ici parce que l&apos;écran peut être ouvert
              sur un téléphone que l&apos;enfant a en main.
            </p>
            {error ? (
              <p className="rounded-xl bg-fun-red-light p-3 text-sm font-semibold text-fun-red">
                {error}
              </p>
            ) : null}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => closeDialog(false)}>
              Annuler
            </Button>
            <Button
              variant={target?.approve ? "default" : "destructive"}
              disabled={pin.length !== 4 || decide.isPending || pinMissing}
              onClick={() => {
                if (!target) return;
                setError(null);
                decide.mutate({
                  requestId: target.request.id,
                  data: { approve: target.approve, pin },
                });
              }}
            >
              {target?.approve ? "Activer le pack" : "Refuser"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
