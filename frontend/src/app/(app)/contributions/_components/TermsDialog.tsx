"use client";

import { useState } from "react";

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

/**
 * Conditions de contribution, exigées au premier envoi (réponse 428). Le texte
 * vient du 428 lui-même quand il est disponible, sinon de `GET /terms`.
 */
export function TermsDialog({
  open,
  onOpenChange,
  terms,
  pending,
  error,
  onAccept,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  terms: { version: string; text: string } | null;
  pending: boolean;
  error: string | null;
  onAccept: (handle: string) => void;
}) {
  const [accepted, setAccepted] = useState(false);
  const [handle, setHandle] = useState("");
  const handleOk = handle.trim().length >= 3 && handle.trim().length <= 24;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-extrabold text-fun-text">
            Conditions de contribution
          </DialogTitle>
          <DialogDescription className="text-fun-text-muted">
            À accepter une seule fois, avant votre premier envoi.
            {terms?.version && ` Version ${terms.version}.`}
          </DialogDescription>
        </DialogHeader>

        <div className="max-h-56 overflow-y-auto whitespace-pre-wrap rounded-2xl border-2 border-fun-border bg-fun-card p-4 text-sm text-fun-text">
          {terms?.text ?? "Chargement des conditions…"}
        </div>

        <label className="flex min-h-12 cursor-pointer items-start gap-3 rounded-2xl border-2 border-fun-border bg-white p-3">
          <input
            type="checkbox"
            checked={accepted}
            onChange={(event) => setAccepted(event.target.checked)}
            className="mt-1 h-5 w-5 shrink-0 accent-fun-green"
          />
          <span className="text-sm font-semibold text-fun-text">
            J&apos;accepte ces conditions et je confirme être l&apos;auteur du
            contenu que j&apos;envoie.
          </span>
        </label>

        <div className="space-y-2">
          <Label htmlFor="contrib-handle" className="text-fun-text">
            Pseudonyme public
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
            De 3 à 24 caractères. C&apos;est la seule identité affichée aux
            autres familles : n&apos;y mettez ni votre vrai nom, ni votre email.
          </p>
        </div>

        {error && (
          <p className="rounded-xl border-2 border-fun-red bg-fun-red-light p-3 text-sm font-semibold text-fun-text">
            {error}
          </p>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={pending}
          >
            Annuler
          </Button>
          <Button
            onClick={() => onAccept(handle.trim())}
            disabled={!accepted || !handleOk || pending}
          >
            {pending ? "Envoi…" : "Accepter et envoyer"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
