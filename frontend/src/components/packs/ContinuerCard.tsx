"use client";

import Link from "next/link";
import { Compass } from "lucide-react";

import type { ContinuerCard as ContinuerCardPayload } from "@/lib/api/model";

interface ContinuerCardProps {
  /** `null` n'est pas une erreur : c'est l'état vide honnête (tout est terminé). */
  continuer?: ContinuerCardPayload | null;
}

const REASON_SUBTITLE: Record<string, string> = {
  resume: "Reprends là où tu t'es arrêté",
  start: "Commence quelque chose de nouveau",
};

export function ContinuerCard({ continuer }: ContinuerCardProps) {
  if (!continuer) {
    return (
      <div className="rounded-3xl bg-white p-6 text-center candy-shadow">
        <div className="mb-2 text-5xl">🎉</div>
        <p className="text-xl font-extrabold text-fun-text">
          Tout est terminé pour l&apos;instant !
        </p>
        <p className="mt-1 text-sm font-semibold text-fun-text-muted">
          Bravo. Va chercher de nouveaux thèmes pour continuer.
        </p>
        <Link
          href="/decouvrir"
          className="mt-4 inline-flex min-h-[48px] items-center justify-center gap-2 rounded-xl bg-fun-sky px-6 text-base font-extrabold text-white candy-shadow transition-all hover:candy-shadow-lg active:scale-95"
        >
          <Compass className="h-5 w-5" />
          Découvrir des thèmes
        </Link>
      </div>
    );
  }

  const { lesson } = continuer;
  const cta = continuer.reason === "resume" ? "Continuer" : "Commencer";

  return (
    <div className="rounded-3xl bg-gradient-to-r from-fun-green to-fun-sky p-6 candy-shadow">
      <div className="flex items-start gap-4">
        <div className="text-5xl" aria-hidden="true">
          {continuer.pack_emoji ?? "🎒"}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-white/90">
            {REASON_SUBTITLE[continuer.reason] ?? "À toi de jouer"}
          </p>
          <p className="mt-1 truncate text-sm font-extrabold text-white/90">
            {continuer.pack_title}
          </p>
          <h2 className="text-2xl leading-tight font-extrabold text-white">
            {lesson.name}
          </h2>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm font-semibold text-white/90">
            <span>
              {lesson.subject_icon} {lesson.subject_name ?? lesson.subject_slug}
            </span>
            {(lesson.xp_reward ?? 0) > 0 && (
              <span>⚡ +{lesson.xp_reward} XP</span>
            )}
          </div>
        </div>
      </div>

      <Link
        href={`/lessons/${lesson.id}`}
        className="mt-4 flex min-h-[56px] w-full items-center justify-center gap-2 rounded-2xl bg-white px-6 text-xl font-extrabold text-fun-green candy-shadow transition-all hover:candy-shadow-lg active:scale-95"
      >
        {cta} <span aria-hidden="true">→</span>
      </Link>
    </div>
  );
}
