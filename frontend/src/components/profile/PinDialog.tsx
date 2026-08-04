"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

type PinMode = "verify" | "set";

interface PinDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: PinMode;
  /** Appelé après un PIN vérifié (verify) ou défini (set) avec succès. */
  onSuccess: () => void;
}

/**
 * Boîte de dialogue du code PIN parent (4 chiffres).
 * - ``verify`` : contrôle le PIN (retour à la vue parent depuis le mode enfant).
 * - ``set`` : définit ou remplace le PIN (double saisie de confirmation).
 */
export function PinDialog({
  open,
  onOpenChange,
  mode,
  onSuccess,
}: PinDialogProps) {
  const { verifyPin, setPin } = useAuth();
  const [pin, setPinValue] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const reset = () => {
    setPinValue("");
    setConfirm("");
    setError("");
  };

  const close = (next: boolean) => {
    if (!next) reset();
    onOpenChange(next);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!/^\d{4}$/.test(pin)) {
      setError("Le code doit contenir exactement 4 chiffres.");
      return;
    }
    if (mode === "set" && pin !== confirm) {
      setError("Les deux codes ne correspondent pas.");
      return;
    }
    setBusy(true);
    try {
      if (mode === "verify") {
        const ok = await verifyPin(pin);
        if (!ok) {
          setError("Code PIN incorrect.");
          return;
        }
      } else {
        await setPin(pin);
      }
      reset();
      onOpenChange(false);
      onSuccess();
    } catch {
      setError("Une erreur est survenue. Réessaie.");
    } finally {
      setBusy(false);
    }
  };

  const title = mode === "verify" ? "Code parent" : "Définir un code parent";
  const description =
    mode === "verify"
      ? "Saisis ton code à 4 chiffres pour revenir à la vue parent."
      : "Choisis un code à 4 chiffres. Il protège l'accès à la vue parent.";

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="rounded-2xl sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3">
          <Input
            autoFocus
            inputMode="numeric"
            pattern="\d*"
            maxLength={4}
            placeholder="••••"
            value={pin}
            onChange={(e) =>
              setPinValue(e.target.value.replace(/\D/g, "").slice(0, 4))
            }
            className="text-center text-2xl tracking-[0.5em]"
          />
          {mode === "set" && (
            <Input
              inputMode="numeric"
              pattern="\d*"
              maxLength={4}
              placeholder="Confirme le code"
              value={confirm}
              onChange={(e) =>
                setConfirm(e.target.value.replace(/\D/g, "").slice(0, 4))
              }
              className="text-center text-2xl tracking-[0.5em]"
            />
          )}
          {error && (
            <p className="text-sm font-semibold text-fun-red">{error}</p>
          )}
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? "..." : mode === "verify" ? "Valider" : "Enregistrer"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
