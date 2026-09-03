"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronUp, Lock } from "lucide-react";

import type { PackPathEntry, PackPathLesson } from "@/lib/api/model";
import { PackLessonRow } from "./PackLessonRow";
import { PackStars } from "./PackStars";
import {
  distinctSubjectIcons,
  frDate,
  groupByTier,
  isTierLocked,
  tierLabel,
} from "./utils";

interface PackCardProps {
  entry: PackPathEntry;
  /** Pack terminé déplié d'entrée (utile pour cibler une révision). */
  defaultExpanded?: boolean;
}

function TierSection({
  tier,
  all,
  visible,
}: {
  tier: number;
  /** Toutes les leçons du palier : c'est elles qui portent le verrou. */
  all: PackPathLesson[];
  visible: PackPathLesson[];
}) {
  if (visible.length === 0) return null;
  return (
    <section>
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <h4 className="text-sm font-extrabold text-fun-text">
          {tierLabel(tier)}
        </h4>
        {isTierLocked(all) && (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-fun-text-muted">
            <Lock className="h-4 w-4" /> Termine le niveau précédent
          </span>
        )}
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {visible.map((lesson) => (
          <PackLessonRow key={lesson.id} lesson={lesson} />
        ))}
      </div>
    </section>
  );
}

export function PackCard({ entry, defaultExpanded = false }: PackCardProps) {
  const lessons = entry.lessons ?? [];
  const rollup = entry.rollup;
  const complete = rollup.complete ?? false;

  const [expanded, setExpanded] = useState(defaultExpanded);
  const [showCompleted, setShowCompleted] = useState(false);

  const tiers = useMemo(() => groupByTier(lessons), [lessons]);
  const icons = useMemo(() => distinctSubjectIcons(lessons), [lessons]);

  const total = rollup.lessons_total ?? lessons.length;
  const done = rollup.lessons_completed ?? 0;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  const remainingCount = lessons.filter((l) => l.status !== "completed").length;
  const completedCount = lessons.length - remainingCount;

  const emoji = entry.pack.emoji ?? "🎒";

  // Pack terminé : une seule ligne trophée. Les étoiles, la date et l'XP y
  // figurent, sinon le repli se lirait comme du contenu retiré à l'enfant.
  if (complete) {
    return (
      <div className="space-y-3">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          className="w-full min-h-[48px] rounded-2xl border-2 border-fun-green bg-fun-green-light p-4 text-left candy-shadow transition-all hover:candy-shadow-lg active:scale-[0.99]"
        >
          <div className="flex items-center gap-3">
            <span className="text-3xl" aria-hidden="true">
              {emoji}
            </span>
            <div className="min-w-0 flex-1">
              <h3 className="font-extrabold text-fun-text">
                {entry.pack.title}
              </h3>
              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm font-semibold text-fun-text-muted">
                <span className="text-fun-green-dark">
                  ✅ {done}/{total}
                </span>
                <PackStars
                  earned={rollup.stars_earned ?? 0}
                  total={rollup.stars_total ?? 0}
                />
                <span>{frDate(rollup.completed_at)}</span>
                <span>⚡ {rollup.xp_banked ?? 0} XP</span>
              </div>
            </div>
            {expanded ? (
              <ChevronUp className="h-5 w-5 shrink-0 text-fun-green" />
            ) : (
              <ChevronDown className="h-5 w-5 shrink-0 text-fun-green" />
            )}
          </div>
        </button>

        {expanded && (
          <div className="space-y-4 rounded-2xl border-2 border-fun-border bg-white p-4 candy-shadow">
            {tiers.map((group) => (
              <TierSection
                key={group.tier}
                tier={group.tier}
                all={group.lessons}
                visible={group.lessons}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-3xl border-2 border-fun-border bg-white p-4 candy-shadow">
      <div className="flex items-start gap-3">
        <span className="text-4xl" aria-hidden="true">
          {emoji}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg leading-tight font-extrabold text-fun-text">
            {entry.pack.title}
          </h3>
          <div className="mt-1 flex flex-wrap items-center gap-1">
            {icons.map((icon) => (
              <span
                key={icon}
                className="rounded-full bg-fun-violet-light px-2 py-0.5 text-xs font-bold text-fun-violet"
              >
                {icon}
              </span>
            ))}
            {entry.pack.origin === "community" && entry.pack.author_handle && (
              <span className="rounded-full bg-fun-sky-light px-2 py-0.5 text-xs font-bold text-fun-sky">
                par {entry.pack.author_handle}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="mt-3">
        <div className="h-3 w-full overflow-hidden rounded-full bg-fun-green-light">
          <div
            className="h-3 rounded-full bg-fun-green transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="mt-2 text-sm font-semibold text-fun-text-muted">
          {done}/{total} leçons · ⚡ {rollup.xp_banked ?? 0} XP
        </p>
      </div>

      {/* La longueur à l'écran suit le travail *restant* : les leçons terminées
          sont repliées derrière un basculement, jamais supprimées. */}
      <div className="mt-4 space-y-4">
        {tiers.map((group) => (
          <TierSection
            key={group.tier}
            tier={group.tier}
            all={group.lessons}
            visible={
              showCompleted
                ? group.lessons
                : group.lessons.filter((l) => l.status !== "completed")
            }
          />
        ))}
      </div>

      {completedCount > 0 && (
        <button
          type="button"
          onClick={() => setShowCompleted((v) => !v)}
          aria-expanded={showCompleted}
          className="mt-3 inline-flex min-h-[48px] items-center gap-2 rounded-xl px-3 text-sm font-bold text-fun-green transition-all hover:bg-fun-green-light active:scale-95"
        >
          {showCompleted ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
          {showCompleted ? "masquer" : "voir"}{" "}
          {completedCount === 1
            ? "la leçon terminée"
            : `les ${completedCount} terminées`}
        </button>
      )}
    </div>
  );
}
