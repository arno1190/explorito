"use client";

import { useState } from "react";
import { BookOpen, CheckCircle, Flag, Users } from "lucide-react";
import { useGetPackPreviewApiV1LibraryPacksPackIdGet as usePackPreview } from "@/lib/api/generated/library/library";
import type { ChildResponse } from "@/lib/api/model";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ChildPackToggle } from "./ChildAccessControls";
import { ReportDialog } from "./ReportDialog";
import { levelRange, PackContent, Pill, QualityScore } from "./pack-ui";

/**
 * Aperçu complet d'un pack **avant** activation : un parent ne peut pas
 * consentir à ce qu'il n'a pas pu lire. Les bonnes réponses sont affichées :
 * la lecture est destinée à l'adulte.
 */
export function PackPreviewDialog({
  packId,
  childProfiles,
  open,
  onOpenChange,
}: {
  packId: string | null;
  childProfiles: ChildResponse[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [reporting, setReporting] = useState(false);
  const { data: pack, isPending } = usePackPreview(packId ?? "", {
    query: { enabled: open && !!packId },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] max-w-3xl overflow-y-auto">
        {isPending || !pack ? (
          <>
            <DialogHeader>
              <DialogTitle>Aperçu du pack</DialogTitle>
              <DialogDescription>Chargement du contenu…</DialogDescription>
            </DialogHeader>
            <div className="flex justify-center py-12">
              <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
            </div>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-left">
                <span className="text-3xl">{pack.emoji ?? "📦"}</span>
                {pack.title}
              </DialogTitle>
              <DialogDescription className="text-left">
                {pack.description ?? "Pas de description."}
              </DialogDescription>
            </DialogHeader>

            <div className="flex flex-wrap items-center gap-2">
              <Pill tone={pack.origin === "official" ? "green" : "violet"}>
                {pack.origin === "official"
                  ? "Contenu officiel Explorito"
                  : `Communauté · ${pack.author_handle ?? "auteur anonyme"}`}
              </Pill>
              <Pill tone="sky">
                {levelRange(pack.level_min, pack.level_max)}
              </Pill>
              <Pill tone="accent">
                {pack.lesson_count ?? 0} leçon
                {(pack.lesson_count ?? 0) > 1 ? "s" : ""} ·{" "}
                {pack.exercise_count ?? 0} exercice
                {(pack.exercise_count ?? 0) > 1 ? "s" : ""}
              </Pill>
              <QualityScore score={pack.quality_score} />
              <Pill tone="sun">
                <Users className="mr-1 inline h-3 w-3" />
                {pack.families_count ?? 0} famille
                {(pack.families_count ?? 0) > 1 ? "s" : ""} utilise
                {(pack.families_count ?? 0) > 1 ? "nt" : ""} ce pack
              </Pill>
              {pack.tags?.map((tag) => (
                <Pill key={tag} tone="violet">
                  #{tag}
                </Pill>
              ))}
            </div>

            {/* Activation : officiel = déjà actif, communauté = accord explicite. */}
            {pack.origin === "official" ? (
              <div className="flex items-start gap-2 rounded-2xl border-2 border-fun-green bg-fun-green-light p-4">
                <CheckCircle className="h-5 w-5 shrink-0 text-fun-green" />
                <p className="text-sm font-semibold text-fun-green-dark">
                  Contenu officiel : déjà actif pour tous vos enfants du niveau
                  concerné. Rien à activer.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <h3 className="text-base font-bold text-fun-text">
                  Activer pour…
                </h3>
                <p className="text-sm text-fun-text-muted">
                  Désactiver un pack le masque simplement : la progression de
                  l&apos;enfant est conservée et réapparaît si vous le
                  réactivez.
                </p>
                {childProfiles.length === 0 ? (
                  <p className="text-sm text-fun-text-muted">
                    Ajoutez d&apos;abord un enfant depuis votre tableau de bord.
                  </p>
                ) : (
                  <div className="grid gap-2 sm:grid-cols-2">
                    {childProfiles.map((child) => (
                      <ChildPackToggle
                        key={child.id}
                        child={child}
                        pack={pack}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="space-y-2">
              <h3 className="flex items-center gap-2 text-base font-bold text-fun-text">
                <BookOpen className="h-5 w-5 text-fun-sky" />
                Tout le contenu ({pack.lessons?.length ?? 0} leçon
                {(pack.lessons?.length ?? 0) > 1 ? "s" : ""})
              </h3>
              <PackContent lessons={pack.lessons} />
            </div>

            <div className="flex flex-col gap-2 sm:flex-row sm:justify-between">
              <Button
                variant="outline"
                onClick={() => setReporting(true)}
                className="text-fun-red"
              >
                <Flag className="mr-2 h-4 w-4" />
                Signaler ce pack
              </Button>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Fermer
              </Button>
            </div>

            <ReportDialog
              packId={pack.id}
              packTitle={pack.title}
              open={reporting}
              onOpenChange={setReporting}
            />
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
