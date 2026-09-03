"use client";

import { useState } from "react";
import { Flag } from "lucide-react";
import { useReportPackApiV1LibraryPacksPackIdReportPost as useReportPack } from "@/lib/api/generated/library/library";
import { ReportReason } from "@/lib/api/model";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { REPORT_REASON_LABELS } from "./pack-ui";

const REASONS = [
  ReportReason.inappropriate,
  ReportReason.wrong_content,
  ReportReason.personal_data,
  ReportReason.duplicate,
  ReportReason.other,
] as const;

/** Signalement d'un pack par un parent (filet de sécurité des auteurs de confiance). */
export function ReportDialog({
  packId,
  packTitle,
  open,
  onOpenChange,
}: {
  packId: string;
  packTitle: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [reason, setReason] = useState<string>(ReportReason.inappropriate);
  const [details, setDetails] = useState("");
  const [sent, setSent] = useState(false);
  const report = useReportPack({
    mutation: { onSuccess: () => setSent(true) },
  });

  const close = (next: boolean) => {
    if (!next) {
      setReason(ReportReason.inappropriate);
      setDetails("");
      setSent(false);
      report.reset();
    }
    onOpenChange(next);
  };

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Flag className="h-5 w-5 text-fun-red" />
            Signaler « {packTitle} »
          </DialogTitle>
          <DialogDescription>
            Un modérateur relira ce pack. Le signalement n&apos;est pas partagé
            avec l&apos;auteur.
          </DialogDescription>
        </DialogHeader>

        {sent ? (
          <p className="rounded-2xl border-2 border-fun-green bg-fun-green-light p-4 text-sm font-semibold text-fun-green-dark">
            Signalement enregistré. Merci : c&apos;est ce qui protège les autres
            familles.
          </p>
        ) : (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Motif</Label>
              <div className="space-y-2">
                {REASONS.map((value) => (
                  <label
                    key={value}
                    className={`flex min-h-12 cursor-pointer items-center gap-3 rounded-2xl border-2 bg-white p-3 text-left candy-shadow transition-all ${
                      reason === value
                        ? "border-fun-sky bg-fun-sky-light"
                        : "border-fun-border"
                    }`}
                  >
                    <input
                      type="radio"
                      name="report-reason"
                      value={value}
                      checked={reason === value}
                      onChange={() => setReason(value)}
                      className="h-4 w-4 accent-[var(--fun-sky)]"
                    />
                    <span className="font-semibold text-fun-text">
                      {REPORT_REASON_LABELS[value]}
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="report-details">Précisions (optionnel)</Label>
              <textarea
                id="report-details"
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                rows={4}
                placeholder="Quelle leçon, quel exercice ?"
                className="w-full rounded-xl border-2 border-fun-border bg-white p-3 text-fun-text outline-none focus:border-fun-sky"
              />
            </div>
            {report.isError ? (
              <p className="rounded-xl bg-fun-red-light p-3 text-sm font-semibold text-fun-red">
                Le signalement n&apos;a pas pu être envoyé. Réessayez.
              </p>
            ) : null}
          </div>
        )}

        <DialogFooter>
          {sent ? (
            <Button onClick={() => close(false)}>Fermer</Button>
          ) : (
            <>
              <Button variant="outline" onClick={() => close(false)}>
                Annuler
              </Button>
              <Button
                variant="destructive"
                disabled={report.isPending}
                onClick={() =>
                  report.mutate({
                    packId,
                    data: {
                      reason: reason as ReportReason,
                      details: details.trim() || null,
                    },
                  })
                }
              >
                Envoyer le signalement
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
