"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronUp, Lock } from "lucide-react";

import type { PackPathLesson } from "@/lib/api/model";
import { PackLessonRow } from "./PackLessonRow";
import { groupByTier, isTierLocked, tierLabel } from "./utils";

interface SubjectSectionProps {
  name: string;
  icon?: string | null;
  /** Les leçons de cette matière, tous packs confondus. */
  lessons: PackPathLesson[];
}

export function SubjectSection({ name, icon, lessons }: SubjectSectionProps) {
  const [showCompleted, setShowCompleted] = useState(false);
  const tiers = useMemo(() => groupByTier(lessons), [lessons]);

  const done = lessons.filter((l) => l.status === "completed").length;
  const pct =
    lessons.length > 0 ? Math.round((done / lessons.length) * 100) : 0;

  return (
    <div className="rounded-3xl border-2 border-fun-border bg-white p-4 candy-shadow">
      <div className="flex items-start gap-3">
        <span className="text-4xl" aria-hidden="true">
          {icon}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg leading-tight font-extrabold text-fun-text">
            {name}
          </h3>
          <div className="mt-1 h-3 w-full overflow-hidden rounded-full bg-fun-green-light">
            <div
              className="h-3 rounded-full bg-fun-green transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="mt-2 text-sm font-semibold text-fun-text-muted">
            {done}/{lessons.length} leçons
          </p>
        </div>
      </div>

      <div className="mt-4 space-y-4">
        {tiers.map((group) => {
          const visible = showCompleted
            ? group.lessons
            : group.lessons.filter((l) => l.status !== "completed");
          if (visible.length === 0) return null;
          return (
            <section key={group.tier}>
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <h4 className="text-sm font-extrabold text-fun-text">
                  {tierLabel(group.tier)}
                </h4>
                {isTierLocked(group.lessons) && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-fun-text-muted">
                    <Lock className="h-4 w-4" /> Termine le niveau précédent
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {visible.map((lesson) => (
                  <PackLessonRow
                    key={lesson.id}
                    lesson={lesson}
                    showSubject={false}
                  />
                ))}
              </div>
            </section>
          );
        })}
      </div>

      {done > 0 && (
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
          {done === 1 ? "la leçon terminée" : `les ${done} terminées`}
        </button>
      )}
    </div>
  );
}
