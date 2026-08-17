"use client";

import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createApiV1InvitationsPost as createInvitation } from "@/lib/api/generated/invitations/invitations";

interface ShareDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** ID de l'enfant à partager ; null/undefined = inviter un co-parent (tous les enfants). */
  childId?: string | null;
  childName?: string;
}

/**
 * Génère un lien d'invitation (partage d'un enfant, ou co-parent) et propose de
 * le copier / l'envoyer par email. Le lien est à usage unique et expire sous 7 jours.
 */
export function ShareDialog({
  open,
  onOpenChange,
  childId,
  childName,
}: ShareDialogProps) {
  const [link, setLink] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const isCoParent = !childId;

  useEffect(() => {
    if (!open) {
      setLink("");
      setError("");
      setCopied(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    createInvitation(
      isCoParent
        ? { kind: "all" }
        : { kind: "child", child_id: childId as string }
    )
      .then((inv) => {
        if (!cancelled) {
          setLink(`${window.location.origin}/invite/${inv.token}`);
        }
      })
      .catch(() => {
        if (!cancelled) setError("Impossible de créer le lien. Réessaie.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, childId, isCoParent]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard indisponible : l'utilisateur peut copier manuellement */
    }
  };

  const subject = isCoParent
    ? "Explorito — je t'invite comme parent"
    : `Explorito — accès à ${childName ?? "un enfant"}`;
  const body = isCoParent
    ? `Rejoins-moi sur Explorito pour suivre nos enfants. Ouvre ce lien puis connecte-toi avec Google :\n\n${link}\n\n(Le lien expire dans 7 jours.)`
    : `Je te partage l'accès à ${childName ?? "un enfant"} sur Explorito. Ouvre ce lien puis connecte-toi avec Google :\n\n${link}\n\n(Le lien expire dans 7 jours.)`;
  const mailto = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-2xl">
        <DialogHeader>
          <DialogTitle>
            {isCoParent
              ? "Inviter un parent"
              : `Partager ${childName ?? "l'enfant"}`}
          </DialogTitle>
          <DialogDescription>
            {isCoParent
              ? "La personne invitée aura accès à tous vos enfants (actuels et futurs), avec les mêmes droits que vous."
              : "La personne invitée pourra suivre cet enfant, lui attribuer des points et jouer avec lui."}
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <p className="py-4 text-center text-fun-text-muted">
            Création du lien…
          </p>
        ) : error ? (
          <p className="rounded-xl bg-fun-red-light px-3 py-2 text-sm text-fun-red">
            {error}
          </p>
        ) : (
          <div className="space-y-3">
            <Input value={link} readOnly onFocus={(e) => e.target.select()} />
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button className="flex-1" onClick={copy}>
                {copied ? "✓ Copié !" : "📋 Copier le lien"}
              </Button>
              <a href={mailto} className="flex-1">
                <Button variant="outline" className="w-full">
                  ✉️ Envoyer par email
                </Button>
              </a>
            </div>
            <p className="text-xs text-fun-text-muted">
              Ce lien est à usage unique et expire dans 7 jours. Vous pouvez le
              révoquer à tout moment depuis « Gérer les accès ».
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
