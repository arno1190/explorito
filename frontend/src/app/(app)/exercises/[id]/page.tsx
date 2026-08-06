"use client";

import { useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, Flame, Star } from "lucide-react";

import { ExerciseFeedback } from "@/components/exercises/ExerciseFeedback";
import { ExerciseRenderer } from "@/components/exercises/ExerciseRenderer";
import type { AnswerPayload } from "@/components/exercises/types";
import { Confetti } from "@/components/gamification/Confetti";
import { XPGain } from "@/components/gamification/XPGain";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  useGetExerciseApiV1ExercisesExerciseIdGet as useExercise,
  useSubmitExerciseApiV1ExercisesExerciseIdSubmitPost as useSubmitExercise,
} from "@/lib/api/generated/exercises/exercises";
import {
  useGetLessonApiV1LessonsLessonIdGet as useLesson,
  useGetLessonExercisesApiV1LessonsLessonIdExercisesGet as useLessonExercises,
} from "@/lib/api/generated/lessons/lessons";
import { getGetWalletApiV1CollectionMeGetQueryKey } from "@/lib/api/generated/collection/collection";
import type { ExerciseSubmitResponse } from "@/lib/api/model";

export default function ExercisePage() {
  const router = useRouter();
  const params = useParams();
  const exerciseId = params.id as string;

  const [answer, setAnswer] = useState<AnswerPayload>(null);
  const [result, setResult] = useState<ExerciseSubmitResponse | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [showXPGain, setShowXPGain] = useState(false);
  const [startTime, setStartTime] = useState(() => Date.now());

  const exerciseQuery = useExercise(exerciseId);
  const exercise = exerciseQuery.data;
  const lessonId = exercise?.lesson_id;

  const lessonQuery = useLesson(lessonId ?? "", {
    query: { enabled: !!lessonId },
  });
  const lesson = lessonQuery.data;

  const exercisesQuery = useLessonExercises(lessonId ?? "", {
    query: { enabled: !!lessonId },
  });
  const allExercises = useMemo(
    () =>
      [...(exercisesQuery.data ?? [])].sort(
        (a, b) => (a.order_index ?? 0) - (b.order_index ?? 0)
      ),
    [exercisesQuery.data]
  );

  const submitMutation = useSubmitExercise();
  const queryClient = useQueryClient();

  const currentIndex = allExercises.findIndex((e) => e.id === exerciseId);
  const nextExercise =
    currentIndex >= 0 && currentIndex < allExercises.length - 1
      ? allExercises[currentIndex + 1]
      : null;
  const isLastExercise = currentIndex === allExercises.length - 1;

  const handleSubmit = async () => {
    if (!answer || !exercise) return;
    const timeTaken = Math.floor((Date.now() - startTime) / 1000);
    const res = await submitMutation.mutateAsync({
      exerciseId,
      data: { answer, time_taken: timeTaken, hints_used: 0 },
    });
    setResult(res);
    if (res.is_correct) {
      setShowConfetti(true);
      setShowXPGain(true);
    }
    // Rafraîchir le porte-monnaie XP (compteur de la barre du haut) dès qu'un
    // gain a lieu, sans recharger la page.
    if (res.xp_awarded) {
      queryClient.invalidateQueries({
        queryKey: getGetWalletApiV1CollectionMeGetQueryKey(),
      });
    }
  };

  const goNext = () => {
    if (nextExercise) {
      router.push(`/exercises/${nextExercise.id}`);
    } else if (lessonId) {
      router.push(`/lessons/${lessonId}`);
    }
  };

  const retry = () => {
    setResult(null);
    setAnswer(null);
    setStartTime(Date.now());
  };

  if (exerciseQuery.isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  if (exerciseQuery.isError || !exercise) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <p className="font-semibold text-fun-red">Exercice introuvable</p>
          <button
            onClick={() => router.push("/subjects")}
            className="mt-4 text-fun-sky hover:underline"
          >
            Retour aux matières
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl p-6 pb-24">
      <Confetti show={showConfetti} onComplete={() => setShowConfetti(false)} />

      <Button
        variant="ghost"
        onClick={() => lessonId && router.push(`/lessons/${lessonId}`)}
        className="mb-6"
      >
        <ChevronLeft className="mr-2 h-4 w-4" />
        Retour à la leçon
      </Button>

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-extrabold text-fun-text">
          {lesson?.name ?? "Exercice"}
          {allExercises.length > 0 && currentIndex >= 0 && (
            <span className="ml-2 text-base font-semibold text-fun-text-muted">
              {currentIndex + 1}/{allExercises.length}
            </span>
          )}
        </h1>
        <div className="flex items-center gap-2 rounded-full bg-fun-sun-light px-4 py-2">
          <Star className="h-5 w-5 fill-fun-sun text-fun-sun" />
          <span className="font-bold text-fun-text">
            {exercise.xp_value ?? 10} pts
          </span>
        </div>
      </div>

      <Card className="mb-6 p-8">
        <ExerciseRenderer
          exercise={exercise}
          onAnswer={setAnswer}
          disabled={!!result}
          showResult={!!result}
          isCorrect={result?.is_correct}
        />
      </Card>

      {!result && (
        <div className="flex justify-center">
          <Button
            size="lg"
            onClick={handleSubmit}
            disabled={!answer || submitMutation.isPending}
            className="px-8 py-6 text-lg"
          >
            {submitMutation.isPending
              ? "Vérification..."
              : "Vérifier ma réponse"}
          </Button>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <ExerciseFeedback
            isCorrect={result.is_correct}
            onNext={result.is_correct ? goNext : retry}
          />

          {result.is_correct && (
            <div className="flex flex-wrap items-center justify-center gap-4 text-fun-text">
              <span className="inline-flex items-center gap-1 rounded-full bg-fun-sun-light px-3 py-1 font-bold">
                <Star className="h-4 w-4 fill-fun-sun text-fun-sun" />+
                {result.xp_awarded ?? 0} XP
              </span>
              {(result.current_streak ?? 0) > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full bg-fun-red-light px-3 py-1 font-bold">
                  <Flame className="h-4 w-4 text-fun-red" />
                  {result.current_streak}
                </span>
              )}
            </div>
          )}

          {result.lesson_completed && (
            <div className="animate-[candy-pop_0.6s_ease-out] rounded-2xl bg-fun-green-light p-6 text-center">
              <p className="text-xl font-extrabold text-fun-text">
                Leçon terminée ! 🎉
              </p>
              <p className="mt-1 font-semibold text-fun-text-muted">
                {"⭐".repeat(result.lesson_stars ?? 0)} · Score{" "}
                {result.lesson_score ?? 0}%
              </p>
            </div>
          )}

          {result.is_correct && (
            <div className="flex justify-center gap-4">
              <Button
                variant="outline"
                onClick={() => lessonId && router.push(`/lessons/${lessonId}`)}
              >
                Retour aux exercices
              </Button>
              <Button onClick={goNext}>
                {isLastExercise ? "Terminer la leçon 🎉" : "Exercice suivant →"}
              </Button>
            </div>
          )}
        </div>
      )}

      {showXPGain && (
        <XPGain
          xp={result?.xp_awarded ?? exercise.xp_value ?? 10}
          onComplete={() => setShowXPGain(false)}
        />
      )}
    </div>
  );
}
