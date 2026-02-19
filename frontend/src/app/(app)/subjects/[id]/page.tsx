"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { subjectsApi, lessonsApi, exercisesApi, progressApi } from "@/lib/api";
import type { Subject, Lesson } from "@/types";
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

  const [subject, setSubject] = useState<Subject | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
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
          subjectsApi.getById(subjectId),
          lessonsApi.getBySubject(subjectId),
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
              exercisesApi.getByLesson(lesson.id),
              progressApi.getCompletedExercises(lesson.id),
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
        <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-candy-purple-light border-t-candy-purple"></div>
      </div>
    );
  }

  if (error || !subject) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-candy-red font-semibold">
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-candy-purple-light via-candy-surface to-candy-orange-light p-4">
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
              <h1 className="text-3xl font-bold text-candy-text mb-1">
                {subject.name}
              </h1>
              <p className="text-candy-text-muted">{subject.description}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Lesson Tree - Duolingo Style */}
      <div className="max-w-md mx-auto relative">
        {lessons.map((lesson, index) => {
          const progress = lessonProgress.get(lesson.id);
          const isCompleted = progress?.isCompleted || false;

          // A lesson is unlocked if:
          // 1. It's the first lesson (index === 0), OR
          // 2. The previous lesson is completed
          const previousLesson = index > 0 ? lessons[index - 1] : null;
          const previousProgress = previousLesson
            ? lessonProgress.get(previousLesson.id)
            : null;
          const isLocked = index > 0 && !previousProgress?.isCompleted;

          return (
            <div key={lesson.id} className="mb-12 relative">
              {/* Connecting line to next lesson */}
              {index < lessons.length - 1 && (
                <div
                  className="absolute top-full left-1/2 w-1 h-12 -translate-x-1/2 bg-gradient-to-b from-candy-purple/40 to-transparent"
                  style={{ zIndex: 0 }}
                />
              )}

              {/* Lesson Node */}
              <div
                className="flex flex-col items-center relative"
                style={{ zIndex: 1 }}
              >
                <button
                  onClick={() =>
                    !isLocked && router.push(`/lessons/${lesson.id}`)
                  }
                  disabled={isLocked}
                  className="relative group"
                >
                  {/* Lesson Circle */}
                  <div
                    className={`w-24 h-24 rounded-full flex items-center justify-center text-white font-bold text-2xl shadow-lg transition-all ${
                      isLocked
                        ? "bg-candy-border cursor-not-allowed"
                        : isCompleted
                          ? "bg-gradient-to-br from-candy-green to-emerald-400 hover:scale-110"
                          : "bg-gradient-to-br from-candy-purple to-candy-pink hover:scale-110 animate-[candy-glow_2s_infinite]"
                    }`}
                  >
                    {isLocked ? (
                      <Lock className="h-10 w-10" />
                    ) : isCompleted ? (
                      <CheckCircle className="h-10 w-10" />
                    ) : (
                      <BookOpen className="h-10 w-10" />
                    )}
                  </div>

                  {/* Stars for completed lessons */}
                  {isCompleted && (
                    <div className="absolute -top-2 -right-2 flex gap-1">
                      {[1, 2, 3].map((star) => (
                        <span key={star} className="text-2xl">
                          ⭐
                        </span>
                      ))}
                    </div>
                  )}
                </button>

                {/* Lesson Info */}
                <div className="mt-4 bg-white rounded-2xl candy-shadow p-4 max-w-xs">
                  <h3 className="text-xl font-bold text-center mb-2 text-candy-text">
                    {lesson.name}
                  </h3>
                  <p className="text-sm text-candy-text-muted text-center mb-3">
                    {lesson.description}
                  </p>

                  {!isLocked && progress && progress.totalExercises > 0 && (
                    <div className="mb-3">
                      {/* Progress bar */}
                      <div className="flex items-center justify-between text-xs text-candy-text-muted mb-1">
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
                      <div className="w-full bg-candy-purple-light rounded-full h-2">
                        <div
                          className="bg-candy-green h-2 rounded-full transition-all"
                          style={{
                            width: `${(progress.completedExercises / progress.totalExercises) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {!isLocked && (
                    <div className="flex items-center justify-center gap-4 text-sm text-candy-text-muted">
                      {lesson.xp_reward > 0 && (
                        <span className="flex items-center gap-1">
                          ⚡ +{lesson.xp_reward} XP
                        </span>
                      )}
                      {lesson.estimated_duration && (
                        <span className="flex items-center gap-1">
                          ⏱️ {lesson.estimated_duration} min
                        </span>
                      )}
                    </div>
                  )}

                  {isLocked && (
                    <div className="text-center text-sm text-candy-text-muted mt-2">
                      🔒 Termine la leçon précédente pour débloquer
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {lessons.length === 0 && (
        <div className="max-w-md mx-auto bg-white rounded-3xl candy-shadow p-12 text-center">
          <div className="text-6xl mb-4">📚</div>
          <p className="text-xl text-candy-text-muted">
            Aucune leçon disponible pour le moment
          </p>
          <p className="text-sm text-candy-text-muted mt-2">
            Reviens plus tard!
          </p>
        </div>
      )}
    </div>
  );
}
