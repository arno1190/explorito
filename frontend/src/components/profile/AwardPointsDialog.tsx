"use client";

import { useState } from "react";
import { useCreateAwardApiV1ChildrenChildIdAwardsPost as useCreateAward } from "@/lib/api/generated/children/children";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Wallet = "points" | "behavior";

const PRESETS: Record<Wallet, { label: string; amount: number }[]> = {
  points: [
    { label: "Dictée", amount: 10 },
    { label: "Écriture", amount: 10 },
    { label: "Lecture", amount: 10 },
  ],
  behavior: [
    { label: "Bonne action", amount: 5 },
    { label: "Aide", amount: 5 },
    { label: "Bêtise", amount: -3 },
  ],
};

interface AwardPointsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  childId: string;
  childName: string;
  onAwarded?: () => void;
}

/** Dialogue parent : attribuer (ou retirer) des points à un enfant. */
export function AwardPointsDialog({
  open,
  onOpenChange,
  childId,
  childName,
  onAwarded,
}: AwardPointsDialogProps) {
  const [wallet, setWallet] = useState<Wallet>("points");
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const create = useCreateAward();

  const reset = () => {
    setAmount("");
    setReason("");
    setError("");
  };

  const applyPreset = (p: { label: string; amount: number }) => {
    setAmount(String(p.amount));
    setReason(p.label);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const amt = parseInt(amount, 10);
    if (!amt || Number.isNaN(amt)) {
      setError("Entre un montant non nul.");
      return;
    }
    if (wallet === "points" && amt < 0) {
      setError("Les points de compétence ne peuvent pas être retirés.");
      return;
    }
    try {
      await create.mutateAsync({
        childId,
        data: { wallet, amount: amt, reason: reason || undefined },
      });
      reset();
      onOpenChange(false);
      onAwarded?.();
    } catch {
      setError("L'attribution a échoué. Réessaie.");
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) reset();
        onOpenChange(o);
      }}
    >
      <DialogContent className="rounded-2xl sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Attribuer des points — {childName}</DialogTitle>
          <DialogDescription>
            Récompense une activité hors-ligne. Choisis la cagnotte, un
            raccourci ou saisis un montant.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Choix de la cagnotte */}
          <div className="grid grid-cols-2 gap-2">
            {(["points", "behavior"] as Wallet[]).map((w) => (
              <button
                key={w}
                type="button"
                onClick={() => setWallet(w)}
                className={cn(
                  "rounded-xl px-3 py-2 text-sm font-bold transition-all active:scale-95",
                  wallet === w
                    ? w === "points"
                      ? "bg-fun-sun-light ring-2 ring-fun-sun"
                      : "bg-fun-green-light ring-2 ring-fun-green"
                    : "bg-fun-surface candy-shadow text-fun-text-muted"
                )}
                aria-pressed={wallet === w}
              >
                {w === "points" ? "⭐ Points" : "💚 Comportement"}
              </button>
            ))}
          </div>

          {/* Raccourcis */}
          <div className="flex flex-wrap gap-2">
            {PRESETS[wallet].map((p) => (
              <button
                key={p.label}
                type="button"
                onClick={() => applyPreset(p)}
                className="rounded-full bg-fun-sky-light px-3 py-1.5 text-sm font-semibold text-fun-text transition-all hover:bg-fun-sky/20 active:scale-95"
              >
                {p.label} {p.amount > 0 ? `+${p.amount}` : p.amount}
              </button>
            ))}
          </div>

          {/* Saisie personnalisée */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="flex gap-2">
              <Input
                type="number"
                inputMode="numeric"
                placeholder="Montant"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-28"
              />
              <Input
                placeholder="Motif (ex. dictée)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="flex-1"
              />
            </div>
            {error && (
              <p className="text-sm font-semibold text-fun-red">{error}</p>
            )}
            <Button
              type="submit"
              className="w-full"
              disabled={create.isPending}
            >
              {create.isPending ? "..." : "Attribuer"}
            </Button>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
