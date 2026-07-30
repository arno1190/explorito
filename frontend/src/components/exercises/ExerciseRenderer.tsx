"use client";

import type { ExerciseResponse } from "@/lib/api/model";
import { FillBlanks } from "./FillBlanks";
import { MathProblem } from "./MathProblem";
import { MultipleChoice } from "./MultipleChoice";
import { Pythagore } from "./Pythagore";
import { Reading } from "./Reading";
import { Reveal } from "./Reveal";
import { Soroban } from "./Soroban";
import type {
  AnswerPayload,
  FillBlanksContent,
  MathProblemContent,
  MultipleChoiceContent,
  PythagoreContent,
  ReadingContent,
  RevealContent,
  SorobanContent,
} from "./types";

interface ExerciseRendererProps {
  exercise: ExerciseResponse;
  onAnswer: (answer: AnswerPayload) => void;
  disabled?: boolean;
  showResult?: boolean;
  isCorrect?: boolean;
}

/**
 * Dispatcher d'exercices. Le contrat backend étant typé, il n'y a plus de couche
 * d'adaptation : on aiguille sur `exercise.type` et on passe `content` tel quel.
 */
export function ExerciseRenderer({
  exercise,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
}: ExerciseRendererProps) {
  const emoji = (exercise.media_urls as { emoji?: string } | undefined)?.emoji;
  const shared = {
    question: exercise.question,
    emoji,
    onAnswer,
    disabled,
    showResult,
    isCorrect,
  };

  // `content` est un objet générique côté API (JSON) ; on le restreint par type.
  const content = exercise.content as unknown;

  switch (exercise.type) {
    case "multiple_choice":
      return (
        <MultipleChoice
          {...shared}
          content={content as MultipleChoiceContent}
        />
      );
    case "fill_blanks":
      return <FillBlanks {...shared} content={content as FillBlanksContent} />;
    case "reveal":
      return <Reveal {...shared} content={content as RevealContent} />;
    case "pythagore":
      return <Pythagore {...shared} content={content as PythagoreContent} />;
    case "math_problem":
      return (
        <MathProblem {...shared} content={content as MathProblemContent} />
      );
    case "reading":
      return <Reading {...shared} content={content as ReadingContent} />;
    case "soroban":
      return <Soroban {...shared} content={content as SorobanContent} />;
    default:
      return (
        <div className="rounded-xl bg-fun-sun-light p-4 text-fun-text">
          Type d&apos;exercice non reconnu&nbsp;: &quot;{exercise.type}&quot;
        </div>
      );
  }
}
