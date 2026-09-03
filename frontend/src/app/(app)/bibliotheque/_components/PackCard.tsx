"use client";

import { BookOpen, CheckCircle, Users } from "lucide-react";
import type { ChildResponse, PackSummary } from "@/lib/api/model";
import { Button } from "@/components/ui/button";
import { ChildPackToggle } from "./ChildAccessControls";
import { levelRange, Pill, QualityScore } from "./pack-ui";

/**
 * Carte de catalogue. Un pack officiel n'a **jamais** d'interrupteur : il est
 * actif implicitement au niveau de l'enfant, et afficher un interrupteur
 * laisserait croire le contraire.
 */
export function PackCard({
  pack,
  childProfiles,
  onOpen,
}: {
  pack: PackSummary;
  childProfiles: ChildResponse[];
  onOpen: (packId: string) => void;
}) {
  const official = pack.origin === "official";
  return (
    <div
      className={`rounded-2xl border-2 bg-white p-4 text-left candy-shadow transition-all ${
        official ? "border-fun-green" : "border-fun-sky"
      }`}
    >
      <div className="flex items-start gap-3">
        <span className="text-3xl">{pack.emoji ?? "📦"}</span>
        <div className="min-w-0 flex-1">
          <h3 className="font-bold text-fun-text">{pack.title}</h3>
          <p className="line-clamp-2 text-sm text-fun-text-muted">
            {pack.description ?? "Pas de description."}
          </p>
        </div>
        {official ? (
          <CheckCircle className="h-5 w-5 shrink-0 text-fun-green" />
        ) : (
          <BookOpen className="h-5 w-5 shrink-0 text-fun-sky" />
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Pill tone={official ? "green" : "violet"}>
          {official ? "Officiel" : `@${pack.author_handle ?? "auteur anonyme"}`}
        </Pill>
        <Pill tone="sky">{levelRange(pack.level_min, pack.level_max)}</Pill>
        <Pill tone="accent">
          {pack.lesson_count ?? 0} leçon
          {(pack.lesson_count ?? 0) > 1 ? "s" : ""} · {pack.exercise_count ?? 0}{" "}
          exercice
          {(pack.exercise_count ?? 0) > 1 ? "s" : ""}
        </Pill>
        {official ? null : <QualityScore score={pack.quality_score} />}
        {official ? null : (
          <Pill tone="sun">
            <Users className="mr-1 inline h-3 w-3" />
            {pack.families_count ?? 0} famille
            {(pack.families_count ?? 0) > 1 ? "s" : ""}
          </Pill>
        )}
      </div>

      {official ? (
        <p className="mt-3 flex items-start gap-2 rounded-xl bg-fun-green-light p-3 text-sm font-semibold text-fun-green-dark">
          <CheckCircle className="h-4 w-4 shrink-0" />
          Déjà actif pour tous vos enfants du niveau concerné. Rien à activer.
        </p>
      ) : childProfiles.length > 0 ? (
        <div className="mt-3 space-y-2">
          <p className="text-xs font-bold uppercase tracking-wide text-fun-text-muted">
            Activer pour
          </p>
          {childProfiles.map((child) => (
            <ChildPackToggle key={child.id} child={child} pack={pack} />
          ))}
        </div>
      ) : null}

      <Button
        variant="outline"
        className="mt-3 w-full"
        onClick={() => onOpen(pack.id)}
      >
        <BookOpen className="mr-2 h-4 w-4" />
        Lire tout le contenu
      </Button>
    </div>
  );
}
