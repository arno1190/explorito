"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  getLessonApiV1LessonsLessonIdGet,
  getLessonExercisesApiV1LessonsLessonIdExercisesGet,
} from "@/lib/api/generated/lessons/lessons";
import {
  getSubjectApiV1SubjectsSubjectIdGet,
  getSubjectLessonsApiV1SubjectsSubjectIdLessonsGet,
} from "@/lib/api/generated/subjects/subjects";
import { getCompletedExercisesApiV1ProgressLessonsLessonIdCompletedExercisesGet } from "@/lib/api/generated/progress/progress";
import type {
  ExerciseResponse,
  LessonResponse,
  SubjectResponse,
} from "@/lib/api/model";
import {
  ChevronLeft,
  PlayCircle,
  CheckCircle2,
  Star,
  Clock,
} from "lucide-react";

export default function LessonDetailPage() {
  const router = useRouter();
  const params = useParams();
  const { user, impersonatedChild } = useAuth();
  const lessonId = params.id as string;

  const [lesson, setLesson] = useState<LessonResponse | null>(null);
  const [subject, setSubject] = useState<SubjectResponse | null>(null);
  const [nextLesson, setNextLesson] = useState<LessonResponse | null>(null);
  const [exercises, setExercises] = useState<ExerciseResponse[]>([]);
  const [completedExerciseIds, setCompletedExerciseIds] = useState<Set<string>>(
    new Set()
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get child ID for tracking progress
  const childId =
    impersonatedChild?.id || (user?.role === "child" ? user.id : null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const lessonData = await getLessonApiV1LessonsLessonIdGet(lessonId);
        setLesson(lessonData);

        const exercisesData =
          await getLessonExercisesApiV1LessonsLessonIdExercisesGet(lessonId);
        // Sort by order_index
        const sortedExercises = exercisesData.sort(
          (a, b) => (a.order_index || 0) - (b.order_index || 0)
        );
        setExercises(sortedExercises);

        // Fetch completed exercises from backend
        try {
          const completedIds =
            await getCompletedExercisesApiV1ProgressLessonsLessonIdCompletedExercisesGet(
              lessonId
            );
          setCompletedExerciseIds(new Set(completedIds));
        } catch (err) {
          // If fetch fails, fall back to localStorage
          console.warn(
            "Could not fetch completed exercises from backend:",
            err
          );
          const stored = localStorage.getItem(
            `completed_exercises_${lessonId}`
          );
          if (stored) {
            setCompletedExerciseIds(new Set(JSON.parse(stored)));
          }
        }

        // Charger la vraie matière (nom, icône, couleur) via son id — sinon le
        // bouton « Retour à … » afficherait toujours la même matière.
        const subjectId = lessonData.subject_id || lessonData.path_id;
        try {
          const subjectData =
            await getSubjectApiV1SubjectsSubjectIdGet(subjectId);
          setSubject(subjectData);
        } catch (subjectErr) {
          console.warn("Could not load subject:", subjectErr);
          // Repli neutre (jamais une matière codée en dur).
          setSubject({
            id: subjectId,
            name: "les matières",
            slug: "",
            description: "",
            icon: "📚",
            color: null,
            order_index: 0,
            is_active: true,
            lesson_count: 0,
          });
        }

        // Determine the next lesson in the same subject (for "Niveau suivant").
        if (lessonData.subject_id) {
          try {
            const siblings =
              await getSubjectLessonsApiV1SubjectsSubjectIdLessonsGet(
                lessonData.subject_id
              );
            // Stay within the same learning path (e.g. CP), since CP and CE1
            // lessons share the same order_index values.
            const samePath = siblings
              .filter((l) => l.path_id === lessonData.path_id)
              .sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0));
            const idx = samePath.findIndex((l) => l.id === lessonData.id);
            setNextLesson(
              idx >= 0 && idx < samePath.length - 1 ? samePath[idx + 1] : null
            );
          } catch (siblingErr) {
            console.warn("Could not load sibling lessons:", siblingErr);
            setNextLesson(null);
          }
        }
      } catch (err) {
        setError("Impossible de charger la leçon");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [lessonId]);

  // Calculate progress
  const totalExercises = exercises.length;
  const completedCount = completedExerciseIds.size;
  const progressPercent =
    totalExercises > 0
      ? Math.round((completedCount / totalExercises) * 100)
      : 0;
  const totalPoints = exercises.reduce((sum, ex) => sum + 10, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-fun-green-light border-t-fun-green"></div>
      </div>
    );
  }

  if (error || !lesson || !subject) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-fun-red font-semibold">
            {error || "Leçon introuvable"}
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

  // Get exercise type label in French
  const getExerciseTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      mcq: "Choix multiple",
      multiple_choice: "Choix multiple",
      true_false: "Vrai ou Faux",
      fill_blanks: "Texte à trous",
      image_selection: "Sélection d'image",
      drag_drop: "Glisser-déposer",
      drag_and_drop: "Glisser-déposer",
    };
    return labels[type] || type.replace("_", " ");
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <Button
        variant="ghost"
        onClick={() => router.push(`/subjects/${subject.id}`)}
        className="mb-6"
      >
        <ChevronLeft className="h-4 w-4 mr-2" />
        Retour à {subject.name}
      </Button>

      {/* Lesson Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div
            className="w-14 h-14 rounded-xl flex items-center justify-center text-white font-bold text-2xl"
            style={{ backgroundColor: subject.color ?? undefined }}
          >
            {(lesson.order_index || 0) + 1}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-fun-text">{lesson.name}</h1>
            <p className="text-fun-text-muted">{lesson.description}</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-fun-surface rounded-xl p-4 border border-fun-border candy-shadow">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-fun-text">
              Progression: {completedCount}/{totalExercises} exercices
            </span>
            <span
              className="text-sm font-bold"
              style={{ color: subject.color ?? undefined }}
            >
              {progressPercent}%
            </span>
          </div>
          <Progress value={progressPercent} className="h-3" />
          <div className="flex items-center justify-between mt-3 text-sm text-fun-text-muted">
            <div className="flex items-center gap-1">
              <Star className="h-4 w-4 text-fun-sun fill-fun-sun" />
              <span>{totalPoints} points disponibles</span>
            </div>
            {lesson.estimated_duration && (
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                <span>~{lesson.estimated_duration} min</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Exercises List */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-fun-text">
          Exercices ({exercises.length})
        </h2>

        {exercises.map((exercise, index) => {
          const isCompleted = completedExerciseIds.has(exercise.id);
          const points = 10;

          return (
            <Card
              key={exercise.id}
              className={`p-5 transition-all hover:shadow-lg cursor-pointer border-2 ${
                isCompleted
                  ? "bg-fun-green-light border-fun-green"
                  : "hover:border-primary"
              }`}
              onClick={() => router.push(`/exercises/${exercise.id}`)}
            >
              <div className="flex items-center gap-4">
                {/* Exercise Number / Status */}
                <div
                  className={`flex-shrink-0 w-14 h-14 rounded-full flex items-center justify-center font-bold text-lg ${
                    isCompleted ? "bg-fun-green text-white" : "text-white"
                  }`}
                  style={
                    !isCompleted
                      ? { backgroundColor: subject.color ?? undefined }
                      : {}
                  }
                >
                  {isCompleted ? (
                    <CheckCircle2 className="h-7 w-7" />
                  ) : (
                    index + 1
                  )}
                </div>

                {/* Exercise Info */}
                <div className="flex-grow min-w-0">
                  <h3 className="text-lg font-bold mb-1 truncate">
                    {`Exercice ${index + 1}`}
                  </h3>
                  <p className="text-fun-text-muted text-sm line-clamp-2">
                    {exercise.question}
                  </p>
                </div>

                {/* Exercise Meta */}
                <div className="flex-shrink-0 text-right">
                  <div className="flex items-center gap-1 justify-end mb-1">
                    <Star className="h-4 w-4 text-fun-sun fill-fun-sun" />
                    <span className="font-bold text-fun-sun">{points} pts</span>
                  </div>
                  <span
                    className="text-xs px-2 py-1 rounded-full"
                    style={{
                      backgroundColor: `${subject.color}15`,
                      color: subject.color ?? undefined,
                    }}
                  >
                    {getExerciseTypeLabel(exercise.type)}
                  </span>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {exercises.length === 0 && (
        <div className="text-center py-12">
          <PlayCircle className="h-16 w-16 text-fun-border mx-auto mb-4" />
          <p className="text-fun-text-muted">
            Aucun exercice disponible pour le moment
          </p>
        </div>
      )}

      {/* Start / completion actions */}
      {exercises.length > 0 &&
        (completedCount >= totalExercises ? (
          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button
              size="lg"
              variant="outline"
              className="px-8 py-6 text-lg"
              onClick={() => router.push(`/exercises/${exercises[0].id}`)}
            >
              Refaire les exercices
            </Button>
            {nextLesson ? (
              <Button
                size="lg"
                className="px-8 py-6 text-lg"
                style={{ backgroundColor: subject.color ?? undefined }}
                onClick={() => router.push(`/lessons/${nextLesson.id}`)}
              >
                Niveau suivant →
              </Button>
            ) : (
              <Button
                size="lg"
                className="px-8 py-6 text-lg"
                style={{ backgroundColor: subject.color ?? undefined }}
                onClick={() => router.push("/subjects")}
              >
                Choisir une autre matière →
              </Button>
            )}
          </div>
        ) : (
          <div className="mt-8 text-center">
            <Button
              size="lg"
              className="px-8 py-6 text-lg"
              style={{ backgroundColor: subject.color ?? undefined }}
              onClick={() => router.push(`/exercises/${exercises[0].id}`)}
            >
              {completedCount === 0 ? "Commencer les exercices" : "Continuer"}
            </Button>
          </div>
        ))}
    </div>
  );
}
