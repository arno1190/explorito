"use client";

import { useRouter } from "next/navigation";
import { BookOpen, CheckCircle, Lock, PlayCircle } from "lucide-react";

import type { PackPathLesson } from "@/lib/api/model";
import { PackStars } from "./PackStars";

interface PackLessonRowProps {
  lesson: PackPathLesson;
  /** Badge de matière : indispensable dans la lentille Thèmes (pack multi-matières),
   * redondant dans la lentille Matières où la section porte déjà la matière. */
  showSubject?: boolean;
}

const STARS_PER_LESSON = 3;

export function PackLessonRow({
  lesson,
  showSubject = true,
}: PackLessonRowProps) {
  const router = useRouter();
  // Le verrou vient toujours de la charge utile : aucun calcul de gating client.
  const locked = lesson.locked ?? false;
  const completed = lesson.status === "completed";
  const started = lesson.status === "started";

  return (
    <button
      type="button"
      onClick={() => {
        if (!locked) router.push(`/lessons/${lesson.id}`);
      }}
      disabled={locked}
      className={`w-full min-h-[48px] rounded-2xl border-2 p-4 text-left candy-shadow transition-all ${
        locked
          ? "cursor-not-allowed border-fun-border bg-white opacity-60"
          : completed
            ? "border-fun-green bg-fun-green-light hover:candy-shadow-lg"
            : "border-fun-sky bg-white hover:scale-[1.02] hover:candy-shadow-lg"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <h4 className="font-bold text-fun-text">{lesson.name}</h4>
        {locked ? (
          <Lock className="h-5 w-5 shrink-0 text-fun-text-muted" />
        ) : completed ? (
          <CheckCircle className="h-5 w-5 shrink-0 text-fun-green" />
        ) : started ? (
          <PlayCircle className="h-5 w-5 shrink-0 text-fun-accent" />
        ) : (
          <BookOpen className="h-5 w-5 shrink-0 text-fun-sky" />
        )}
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-2">
        {showSubject && (
          <span className="rounded-full bg-fun-violet-light px-2 py-0.5 text-xs font-bold text-fun-violet">
            {lesson.subject_icon} {lesson.subject_name ?? lesson.subject_slug}
          </span>
        )}
        {started && (
          <span className="rounded-full bg-fun-accent-light px-2 py-0.5 text-xs font-bold text-fun-accent-dark">
            En cours
          </span>
        )}
        {locked && (
          <span className="rounded-full bg-fun-border px-2 py-0.5 text-xs font-bold text-fun-text-muted">
            À débloquer
          </span>
        )}
      </div>

      {lesson.description && !locked && (
        <p className="mt-2 text-sm text-fun-text-muted">{lesson.description}</p>
      )}

      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm font-semibold text-fun-text-muted">
        {completed ? (
          <>
            <PackStars
              earned={lesson.stars ?? 0}
              total={STARS_PER_LESSON}
              max={STARS_PER_LESSON}
            />
            <span>⚡ {lesson.xp_earned ?? 0} XP</span>
          </>
        ) : (
          !locked &&
          (lesson.xp_reward ?? 0) > 0 && <span>⚡ +{lesson.xp_reward} XP</span>
        )}
        {(lesson.exercise_count ?? 0) > 0 && (
          <span>{lesson.exercise_count} exercices</span>
        )}
      </div>
    </button>
  );
}
