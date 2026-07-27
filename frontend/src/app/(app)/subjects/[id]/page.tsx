"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  getSubjectApiV1SubjectsSubjectIdGet,
  getSubjectLessonsApiV1SubjectsSubjectIdLessonsGet,
} from "@/lib/api/generated/subjects/subjects";
import { getLessonExercisesApiV1LessonsLessonIdExercisesGet } from "@/lib/api/generated/lessons/lessons";
import { getCompletedExercisesApiV1ProgressLessonsLessonIdCompletedExercisesGet } from "@/lib/api/generated/progress/progress";
import type { LessonResponse, SubjectResponse } from "@/lib/api/model";
import { ChevronLeft, BookOpen, CheckCircle, Lock } from "lucide-react";

interface LessonProgress {
  lessonId: string;
  totalExercises: number;
  completedExercises: number;
  isCompleted: boolean;
}

export default function SubjectDetailPage() {
  const router = useRouter();
  const params = useParams();
  const subjectId = params.id as string;

  const [subject, setSubject] = useState<SubjectResponse | null>(null);
  const [lessons, setLessons] = useState<LessonResponse[]>([]);
  const [lessonProgress, setLessonProgress] = useState<
    Map<string, LessonProgress>
  >(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [subjectData, lessonsData] = await Promise.all([
          getSubjectApiV1SubjectsSubjectIdGet(subjectId),
          getSubjectLessonsApiV1SubjectsSubjectIdLessonsGet(subjectId),
        ]);
        setSubject(subjectData);

        // Sort lessons by order_index
        const sortedLessons = lessonsData.sort(
          (a, b) => (a.order_index || 0) - (b.order_index || 0)
        );
        setLessons(sortedLessons);

        // Fetch progress for each lesson
        const progressMap = new Map<string, LessonProgress>();
        for (const lesson of sortedLessons) {
          try {
            const [exercises, completedIds] = await Promise.all([
              getLessonExercisesApiV1LessonsLessonIdExercisesGet(lesson.id),
              getCompletedExercisesApiV1ProgressLessonsLessonIdCompletedExercisesGet(
                lesson.id
              ),
            ]);
            progressMap.set(lesson.id, {
              lessonId: lesson.id,
              totalExercises: exercises.length,
              completedExercises: completedIds.length,
              isCompleted:
                exercises.length > 0 && completedIds.length >= exercises.length,
            });
          } catch {
            // If we can't fetch progress, assume not started
            progressMap.set(lesson.id, {
              lessonId: lesson.id,
              totalExercises: 0,
              completedExercises: 0,
              isCompleted: false,
            });
          }
        }
        setLessonProgress(progressMap);
      } catch (err) {
        setError("Impossible de charger les leçons");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [subjectId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-fun-green-light border-t-fun-green"></div>
      </div>
    );
  }

  if (error || !subject) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-fun-red font-semibold">
            {error || "Matière introuvable"}
          </p>
          <button
            onClick={() => router.push("/subjects")}
            className="mt-4 text-primary hover:underline"
          >
            Retour aux matières
          </button>
        </div>
      </div>
    );
  }

  // Group lessons into tiers by order_index. Within a tier, lessons are freely
  // pickable (any order). A tier unlocks only once every lesson of all lower
  // tiers is completed.
  const tierMap = new Map<number, LessonResponse[]>();
  for (const l of lessons) {
    const t = l.order_index ?? 0;
    if (!tierMap.has(t)) tierMap.set(t, []);
    tierMap.get(t)!.push(l);
  }
  const tierKeys = [...tierMap.keys()].sort((a, b) => a - b);
  const isTierComplete = (t: number) =>
    (tierMap.get(t) ?? []).every((l) => lessonProgress.get(l.id)?.isCompleted);
  const isTierUnlocked = (idx: number) =>
    idx === 0 || tierKeys.slice(0, idx).every(isTierComplete);
  const tierLabel = (t: number) =>
    ({
      1: "Niveau 1 · Découverte",
      2: "Niveau 2 · Entraînement",
      3: "Niveau 3 · Défi",
    })[t] ?? `Niveau ${t}`;

  return (
    <div className="min-h-screen bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light p-4">
      {/* Header */}
      <div className="max-w-3xl mx-auto mb-6">
        <Button
          variant="ghost"
          onClick={() => router.push("/play")}
          className="mb-4 text-lg"
          size="lg"
        >
          <ChevronLeft className="h-5 w-5 mr-2" />
          Retour
        </Button>

        <div className="bg-white rounded-3xl candy-shadow p-6 mb-8">
          <div className="flex items-center gap-4">
            <div className="text-6xl">{subject.icon}</div>
            <div>
              <h1 className="text-3xl font-bold text-fun-text mb-1">
                {subject.name}
              </h1>
              <p className="text-fun-text-muted">{subject.description}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Lessons grouped by tier — free order within a tier, tiers gate */}
      <div className="max-w-3xl mx-auto space-y-8">
        {tierKeys.map((tier, tierIdx) => {
          const unlocked = isTierUnlocked(tierIdx);
          const tierLessons = tierMap.get(tier) ?? [];
          return (
            <section key={tier}>
              <div className="mb-3 flex items-center gap-2">
                <h2 className="text-xl font-extrabold text-fun-text">
                  {tierLabel(tier)}
                </h2>
                {!unlocked && (
                  <span className="inline-flex items-center gap-1 text-sm font-semibold text-fun-text-muted">
                    <Lock className="h-4 w-4" /> Termine le niveau précédent
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {tierLessons.map((lesson) => {
                  const progress = lessonProgress.get(lesson.id);
                  const isCompleted = progress?.isCompleted || false;
                  const isLocked = !unlocked;
                  return (
                    <button
                      key={lesson.id}
                      onClick={() =>
                        !isLocked && router.push(`/lessons/${lesson.id}`)
                      }
                      disabled={isLocked}
                      className={`rounded-2xl border-2 bg-white p-4 text-left candy-shadow transition-all ${
                        isLocked
                          ? "cursor-not-allowed border-fun-border opacity-60"
                          : isCompleted
                            ? "border-fun-green hover:candy-shadow-lg"
                            : "border-fun-sky hover:scale-[1.02] hover:candy-shadow-lg"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-bold text-fun-text">
                          {lesson.name}
                        </h3>
                        {isLocked ? (
                          <Lock className="h-5 w-5 shrink-0 text-fun-text-muted" />
                        ) : isCompleted ? (
                          <CheckCircle className="h-5 w-5 shrink-0 text-fun-green" />
                        ) : (
                          <BookOpen className="h-5 w-5 shrink-0 text-fun-sky" />
                        )}
                      </div>

                      {lesson.description && (
                        <p className="mt-1 text-sm text-fun-text-muted">
                          {lesson.description}
                        </p>
                      )}

                      {!isLocked && progress && progress.totalExercises > 0 && (
                        <div className="mt-3">
                          <div className="mb-1 flex justify-between text-xs text-fun-text-muted">
                            <span>
                              {progress.completedExercises}/
                              {progress.totalExercises} exercices
                            </span>
                            <span>
                              {Math.round(
                                (progress.completedExercises /
                                  progress.totalExercises) *
                                  100
                              )}
                              %
                            </span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-fun-green-light">
                            <div
                              className="h-2 rounded-full bg-fun-green transition-all"
                              style={{
                                width: `${(progress.completedExercises / progress.totalExercises) * 100}%`,
                              }}
                            />
                          </div>
                        </div>
                      )}

                      {!isLocked && (lesson.xp_reward ?? 0) > 0 && (
                        <div className="mt-2 text-sm text-fun-text-muted">
                          ⚡ +{lesson.xp_reward} XP {isCompleted && "· ⭐⭐⭐"}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>

      {lessons.length === 0 && (
        <div className="max-w-md mx-auto bg-white rounded-3xl candy-shadow p-12 text-center">
          <div className="text-6xl mb-4">📚</div>
          <p className="text-xl text-fun-text-muted">
            Aucune leçon disponible pour le moment
          </p>
          <p className="text-sm text-fun-text-muted mt-2">Reviens plus tard!</p>
        </div>
      )}
    </div>
  );
}
