"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ExerciseRenderer } from "@/components/exercises/ExerciseRenderer";
import { Confetti } from "@/components/gamification/Confetti";
import { XPGain } from "@/components/gamification/XPGain";
import { ExerciseFeedback } from "@/components/exercises/ExerciseFeedback";
import { useSound } from "@/hooks/useSound";
import { exercisesApi, lessonsApi } from "@/lib/api";
import type {
  Exercise,
  Lesson,
  ExerciseSubmission,
  ExerciseResult,
} from "@/types";
import { ChevronLeft, Trophy, Star } from "lucide-react";

export default function ExercisePage() {
  const router = useRouter();
  const params = useParams();
  const { user, impersonatedChild } = useAuth();
  const exerciseId = params.id as string;

  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [allExercises, setAllExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [answer, setAnswer] = useState<unknown>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ExerciseResult | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [showXPGain, setShowXPGain] = useState(false);
  const [startTime] = useState(Date.now());
  const { play } = useSound();

  // Determine the child ID - either from impersonation or the logged-in child user
  const childId =
    impersonatedChild?.id || (user?.role === "child" ? user.id : null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const exerciseData = await exercisesApi.getById(exerciseId);
        setExercise(exerciseData);

        const lessonData = await lessonsApi.getById(exerciseData.lesson_id);
        setLesson(lessonData);

        // Fetch all exercises for this lesson to enable "Next exercise" navigation
        const exercisesData = await exercisesApi.getByLesson(
          exerciseData.lesson_id
        );
        setAllExercises(
          exercisesData.sort(
            (a, b) => (a.order_index || 0) - (b.order_index || 0)
          )
        );
      } catch (err) {
        setError("Impossible de charger l'exercice");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [exerciseId]);

  // Format answer based on exercise type for backend compatibility
  const formatAnswer = (
    rawAnswer: unknown,
    exerciseType: string
  ): Record<string, unknown> => {
    // Map frontend type to backend type
    const backendType =
      exerciseType === "multiple_choice"
        ? "mcq"
        : exerciseType === "drag_and_drop"
          ? "drag_drop"
          : exerciseType;

    switch (backendType) {
      case "mcq":
        // Backend expects {"answer": "option_text"} for single or {"answers": [...]} for multiple
        // Frontend sends string (single) or string[] (multiple)
        if (Array.isArray(rawAnswer)) {
          return { answers: rawAnswer };
        }
        return { answer: rawAnswer };

      case "true_false":
        // Backend expects {"answer": true/false}
        // Frontend sends boolean
        return { answer: rawAnswer };

      case "fill_blanks":
        // Backend expects {"blanks": ["answer1", "answer2"]}
        // Frontend sends string[]
        return { blanks: rawAnswer };

      case "image_selection":
        // Backend expects {"selected": "img_id"}
        // Frontend sends the image ID
        return { selected: rawAnswer };

      case "drag_drop":
        // Backend expects {"positions": {...}}
        return { positions: rawAnswer };

      default:
        // Wrap in object if not already
        if (typeof rawAnswer === "object" && rawAnswer !== null) {
          return rawAnswer as Record<string, unknown>;
        }
        return { answer: rawAnswer };
    }
  };

  const handleSubmit = async () => {
    if (!answer || !exercise) return;

    // Verify we have a child ID (from impersonation or logged-in child)
    if (!childId) {
      setError(
        "Aucun enfant sélectionné. Veuillez vous connecter en tant qu'enfant."
      );
      return;
    }

    try {
      setSubmitting(true);

      const timeSpent = Math.floor((Date.now() - startTime) / 1000);

      // Format answer for backend based on exercise type
      const formattedAnswer = formatAnswer(answer, exercise.type);

      const submission: ExerciseSubmission = {
        exercise_id: exerciseId,
        child_id: childId,
        answer: formattedAnswer,
        is_correct: false, // Will be determined by backend
        points_earned: 0, // Will be determined by backend
        time_spent_seconds: timeSpent,
      };

      const submissionResult = await exercisesApi.submit(submission);
      setResult(submissionResult);

      if (submissionResult.is_correct) {
        setShowConfetti(true);
        setShowXPGain(true);
      }
    } catch (err) {
      setError("Impossible de soumettre la réponse");
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  // Find current exercise index and next exercise
  const currentIndex = allExercises.findIndex((e) => e.id === exerciseId);
  const nextExercise =
    currentIndex >= 0 && currentIndex < allExercises.length - 1
      ? allExercises[currentIndex + 1]
      : null;
  const isLastExercise = currentIndex === allExercises.length - 1;

  const handleNextExercise = () => {
    if (nextExercise) {
      router.push(`/exercises/${nextExercise.id}`);
    } else if (lesson) {
      // Last exercise - go back to lesson
      router.push(`/lessons/${lesson.id}`);
    }
  };

  const handleBackToExercises = () => {
    if (lesson) {
      router.push(`/lessons/${lesson.id}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-candy-purple-light border-t-candy-purple"></div>
      </div>
    );
  }

  if (error || !exercise || !lesson) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-candy-red font-semibold">
            {error || "Exercice introuvable"}
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
    <div className="container mx-auto p-6 max-w-4xl">
      <Confetti show={showConfetti} onComplete={() => setShowConfetti(false)} />

      <Button
        variant="ghost"
        onClick={() => router.push(`/lessons/${lesson.id}`)}
        className="mb-6"
      >
        <ChevronLeft className="h-4 w-4 mr-2" />
        Retour à la leçon
      </Button>

      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold text-candy-text">
            {exercise.title || `Exercice ${(exercise.order_index || 0) + 1}`}
          </h1>
          <div className="flex items-center gap-2 bg-candy-yellow-light px-4 py-2 rounded-full">
            <Star className="h-5 w-5 text-candy-yellow fill-candy-yellow" />
            <span className="font-bold text-candy-text">
              {exercise.points || 10} pts
            </span>
          </div>
        </div>
      </div>

      <Card className="p-8 mb-6">
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
            disabled={!answer || submitting}
            className="px-8 py-6 text-lg"
          >
            {submitting ? "Vérification..." : "Vérifier ma réponse"}
          </Button>
        </div>
      )}

      {result && (
        <div className="mb-6">
          <ExerciseFeedback
            isCorrect={result.is_correct}
            onNext={
              result.is_correct
                ? handleNextExercise
                : () => {
                    setResult(null);
                    setAnswer(null);
                  }
            }
          />
        </div>
      )}

      {showXPGain && (
        <XPGain
          xp={exercise?.points || 10}
          onComplete={() => setShowXPGain(false)}
        />
      )}

      {result && result.is_correct && (
        <div className="flex justify-center gap-4">
          <Button variant="outline" onClick={handleBackToExercises}>
            Retour aux exercices
          </Button>
          <Button onClick={handleNextExercise}>
            {isLastExercise ? "Terminer la leçon 🎉" : "Exercice suivant →"}
          </Button>
        </div>
      )}
    </div>
  );
}
