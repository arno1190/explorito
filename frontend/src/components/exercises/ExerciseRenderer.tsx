"use client";

import { MultipleChoice } from "./MultipleChoice";
import { DragAndDrop } from "./DragAndDrop";
import { FillBlanks } from "./FillBlanks";
import { TrueFalse } from "./TrueFalse";
import { ImageSelection } from "./ImageSelection";
import type { Exercise, ExerciseContent } from "@/types";

// API URL for static files (images, etc.)
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Normalize image URLs to point to the backend
function normalizeImageUrl(url: string | null | undefined): string {
  if (!url) return "/placeholder-image.png";
  // If URL is relative and starts with /uploads, prepend API_URL
  if (url.startsWith("/uploads")) {
    return `${API_URL}${url}`;
  }
  // If URL is already absolute, return as-is
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  // Default: prepend API_URL
  return `${API_URL}${url}`;
}

interface ExerciseRendererProps {
  exercise: Exercise;
  onAnswer: (answer: unknown) => void;
  disabled?: boolean;
  showResult?: boolean;
  isCorrect?: boolean;
}

// Normalize exercise content from backend format to frontend expected format
function normalizeContent(exercise: Exercise): ExerciseContent {
  const content = { ...exercise.content };

  // Handle fill_blanks format differences
  // Backend uses: { sentence: "r{blank}tus", blanks: [{ id, correctAnswer, ... }] }
  // Frontend expects: { text: "r___tus", blanks: [{ position, answer }] }
  if (exercise.type === "fill_blanks") {
    const sentence = content.sentence || content.text || "";
    const blanks = content.blanks || [];

    // Find positions of {blank} markers in the sentence
    const blankMarker = "{blank}";
    const normalizedBlanks: Array<{ position: number; answer: string }> = [];
    let searchIndex = 0;
    let normalizedText = sentence;

    blanks.forEach(
      (
        blank: { id?: string; correctAnswer?: string; answer?: string },
        idx: number
      ) => {
        const markerPos = sentence.indexOf(blankMarker, searchIndex);
        if (markerPos !== -1) {
          normalizedBlanks.push({
            position: markerPos,
            answer: blank.correctAnswer || blank.answer || "",
          });
          searchIndex = markerPos + blankMarker.length;
        } else {
          // Fallback: if no marker found, use index position
          normalizedBlanks.push({
            position: idx * 10,
            answer: blank.correctAnswer || blank.answer || "",
          });
        }
      }
    );

    // Replace {blank} markers with ___ for display
    normalizedText = sentence.replace(/{blank}/g, "___");

    return {
      ...content,
      text: normalizedText,
      blanks: normalizedBlanks,
    };
  }

  // Handle MCQ options format differences
  // Backend uses: { options: [{ id, text, image }] }
  // Frontend expects: { options: string[] } or { options: [{ id, text }] }
  if (
    (exercise.type === "mcq" || exercise.type === "multiple_choice") &&
    content.options
  ) {
    const options = content.options as Array<
      string | { id: string; text: string; image?: string | null }
    >;
    // If options are objects with text property, extract text for simple display
    if (
      options.length > 0 &&
      typeof options[0] === "object" &&
      (options[0] as { text: string }).text
    ) {
      const objectOptions = options as Array<{
        id: string;
        text: string;
        image?: string | null;
      }>;
      return {
        ...content,
        options: objectOptions.map((opt) => opt.text),
        // Keep original for correct_answer matching
        _originalOptions: objectOptions,
      };
    }
  }

  // Handle image_selection - normalize image URLs
  if (exercise.type === "image_selection" && content.images) {
    return {
      ...content,
      images: content.images.map(
        (img: { id: string; url: string; alt: string }) => ({
          ...img,
          url: normalizeImageUrl(img.url),
        })
      ),
    };
  }

  return content;
}

export function ExerciseRenderer({
  exercise,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
}: ExerciseRendererProps) {
  // Normalize content to expected format
  const normalizedContent = normalizeContent(exercise);
  const normalizedExercise = { ...exercise, content: normalizedContent };

  // Map backend type to frontend type
  // Backend uses: "mcq", "drag_drop", etc.
  // Frontend uses: "multiple_choice", "drag_and_drop", etc.
  const exerciseType =
    exercise.type === "mcq"
      ? "multiple_choice"
      : exercise.type === "drag_drop"
        ? "drag_and_drop"
        : exercise.type;

  // Use normalized content for rendering
  const content = normalizedContent;

  switch (exerciseType) {
    case "multiple_choice":
      if (!content.options) {
        return (
          <div className="text-red-500 p-4 bg-red-50 rounded">
            Configuration exercice invalide: options manquantes (type:{" "}
            {exercise.type})
          </div>
        );
      }
      // Ensure options are strings (normalized content should handle this)
      const stringOptions = Array.isArray(content.options)
        ? content.options.map((opt) =>
            typeof opt === "string" ? opt : (opt as { text: string }).text
          )
        : [];

      // Detect if multiple answers are allowed:
      // 1. Explicit flag in content: content.allowMultiple or content.multiple
      // 2. Multiple correct answers: correct_answer is array or contains "answers" (plural)
      // 3. Multiple correct option IDs in the answer
      // Note: correct_answer is at exercise level, not inside content
      const correctAnswer = exercise.correct_answer || content.correct_answer;
      let allowMultiple = false;
      let correctAnswerValue: string | string[] = "";

      if (content.allowMultiple || content.multiple) {
        allowMultiple = true;
      }

      if (correctAnswer) {
        if (Array.isArray(correctAnswer)) {
          // Direct array of answers
          allowMultiple = true;
          correctAnswerValue = correctAnswer;
        } else if (typeof correctAnswer === "object") {
          // Check for "answers" (plural) key indicating multiple
          const ans = (correctAnswer as Record<string, unknown>).answers;
          const singleAns = (correctAnswer as Record<string, unknown>).answer;

          if (Array.isArray(ans)) {
            allowMultiple = true;
            // Map answer IDs to option texts
            correctAnswerValue = ans.map((id: string) => {
              const opt = content._originalOptions?.find(
                (o: { id: string }) => o.id === id
              );
              return opt ? opt.text : id;
            });
          } else if (singleAns !== undefined) {
            // Single answer - map ID to text
            const opt = content._originalOptions?.find(
              (o: { id: string }) => o.id === singleAns
            );
            correctAnswerValue = opt ? opt.text : String(singleAns);
          }
        } else {
          correctAnswerValue = String(correctAnswer);
        }
      }

      // Wrap onAnswer to convert text back to IDs for backend
      const handleMcqAnswer = (answer: string | string[]) => {
        if (!content._originalOptions) {
          // No original options, send as-is
          onAnswer(answer);
          return;
        }

        // Convert text(s) to ID(s)
        const originalOptions = content._originalOptions || [];
        if (Array.isArray(answer)) {
          const ids = answer.map((text) => {
            const opt = originalOptions.find(
              (o: { id: string; text: string }) => o.text === text
            );
            return opt ? opt.id : text;
          });
          onAnswer(ids);
        } else {
          const opt = originalOptions.find(
            (o: { id: string; text: string }) => o.text === answer
          );
          onAnswer(opt ? opt.id : answer);
        }
      };

      return (
        <MultipleChoice
          question={exercise.question}
          options={stringOptions}
          onAnswer={handleMcqAnswer}
          disabled={disabled}
          showResult={showResult}
          isCorrect={isCorrect}
          correctAnswer={correctAnswerValue}
          allowMultiple={allowMultiple}
        />
      );

    case "drag_and_drop":
      if (!content.items || !content.targets) {
        return (
          <div className="text-red-500 p-4 bg-red-50 rounded">
            Configuration exercice invalide: items ou targets manquants (type:{" "}
            {exercise.type})
          </div>
        );
      }
      return (
        <DragAndDrop
          question={exercise.question}
          items={content.items}
          targets={content.targets}
          onAnswer={onAnswer}
          disabled={disabled}
          showResult={showResult}
          isCorrect={isCorrect}
          correctMatches={content.correct_matches}
        />
      );

    case "fill_blanks":
      if (!content.text || !content.blanks) {
        return (
          <div className="text-red-500 p-4 bg-red-50 rounded">
            Configuration exercice invalide: text ou blanks manquants (type:{" "}
            {exercise.type}, content: {JSON.stringify(content).slice(0, 100)}
            ...)
          </div>
        );
      }
      return (
        <FillBlanks
          question={exercise.question}
          text={content.text}
          blanks={content.blanks}
          onAnswer={onAnswer}
          disabled={disabled}
          showResult={showResult}
          isCorrect={isCorrect}
        />
      );

    case "true_false":
      // Get correct answer from exercise level (backend format: {answer: true/false})
      const trueFalseAnswer = exercise.correct_answer || content.correct_answer;
      let trueFalseCorrect: boolean | undefined = undefined;
      if (trueFalseAnswer) {
        if (typeof trueFalseAnswer === "boolean") {
          trueFalseCorrect = trueFalseAnswer;
        } else if (
          typeof trueFalseAnswer === "object" &&
          "answer" in trueFalseAnswer
        ) {
          trueFalseCorrect = Boolean(trueFalseAnswer.answer);
        }
      }
      return (
        <TrueFalse
          question={exercise.question}
          statement={content.statement}
          image={content.image ? normalizeImageUrl(content.image) : undefined}
          onAnswer={onAnswer}
          disabled={disabled}
          showResult={showResult}
          isCorrect={isCorrect}
          correctAnswer={trueFalseCorrect}
        />
      );

    case "image_selection":
      if (!content.images) {
        return (
          <div className="text-red-500 p-4 bg-red-50 rounded">
            Configuration exercice invalide: images manquantes (type:{" "}
            {exercise.type})
          </div>
        );
      }
      // Get correct image ID from exercise level (backend format: {selected: "img1"})
      const imageAnswer = exercise.correct_answer || {};
      const correctImageId =
        content.correct_image_id ||
        (imageAnswer as { selected?: string }).selected;
      return (
        <ImageSelection
          question={exercise.question}
          images={content.images}
          onAnswer={onAnswer}
          disabled={disabled}
          showResult={showResult}
          isCorrect={isCorrect}
          correctImageId={correctImageId}
        />
      );

    default:
      return (
        <div className="text-orange-500 p-4 bg-orange-50 rounded">
          Type d&apos;exercice non reconnu: &quot;{exercise.type}&quot;
        </div>
      );
  }
}
