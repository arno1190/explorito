"use client";

import { useState } from "react";
import { CheckCircle, Circle, Pencil } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import type { PackExercisePreview, ValidationIssue } from "@/lib/api/model";

import { exerciseTypeLabel, parseJsonObject } from "../_lib/contrib";
import { useQuickEdit } from "../_lib/useQuickEdit";
import { EditFailure } from "./EditFailure";
import { IssueList } from "./IssueList";

const FIELD_CLASS =
  "w-full rounded-xl border-2 border-fun-border bg-white p-3 text-sm text-fun-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fun-sky";

/**
 * Rendu **lecture seule** de l'exercice, au plus proche de ce que l'enfant
 * verra. Les composants de `components/exercises/` ne conviennent pas ici :
 * ils mélangent les options, exigent un `onAnswer` et cachent volontairement la
 * bonne réponse — or c'est précisément elle que l'auteur doit relire.
 */
function ExerciseBody({ exercise }: { exercise: PackExercisePreview }) {
  const content = (exercise.content ?? {}) as Record<string, unknown>;
  const answer = (exercise.correct_answer ?? {}) as Record<string, unknown>;

  switch (exercise.type) {
    case "multiple_choice": {
      const options = Array.isArray(content.options)
        ? (content.options as Record<string, unknown>[])
        : [];
      const correct = Array.isArray(answer.option_ids)
        ? (answer.option_ids as unknown[]).map(String)
        : [];
      return (
        <ul className="space-y-2">
          {options.map((option, index) => {
            const id = String(option.id ?? index);
            const isCorrect = correct.includes(id);
            return (
              <li
                key={id}
                className={cn(
                  "flex items-center gap-2 rounded-xl border-2 p-2 text-sm",
                  isCorrect
                    ? "border-fun-green bg-fun-green-light font-bold text-fun-text"
                    : "border-fun-border bg-white text-fun-text"
                )}
              >
                {isCorrect ? (
                  <CheckCircle className="h-4 w-4 shrink-0 text-fun-green" />
                ) : (
                  <Circle className="h-4 w-4 shrink-0 text-fun-text-muted" />
                )}
                {typeof option.color === "string" && (
                  <span
                    className="h-4 w-4 shrink-0 rounded-full border border-fun-border"
                    style={{ background: option.color }}
                    aria-hidden
                  />
                )}
                <span className="min-w-0 break-words">
                  {String(option.text ?? "")}
                </span>
              </li>
            );
          })}
          {content.multiple === true && (
            <li className="text-xs text-fun-text-muted">
              Plusieurs réponses attendues.
            </li>
          )}
        </ul>
      );
    }
    case "fill_blanks": {
      const blanks = Array.isArray(answer.blanks)
        ? (answer.blanks as unknown[]).map(String)
        : [];
      return (
        <div className="space-y-2 text-sm text-fun-text">
          <p className="rounded-xl border-2 border-fun-border bg-white p-3">
            {String(content.text ?? "")}
          </p>
          <p>
            <span className="font-bold">Réponses&nbsp;: </span>
            {blanks.length > 0 ? blanks.join(" · ") : "—"}
          </p>
        </div>
      );
    }
    case "reveal": {
      return (
        <div className="space-y-2 text-sm text-fun-text">
          <p className="rounded-xl border-2 border-fun-border bg-white p-3">
            {String(content.prompt ?? "")}
          </p>
          <p className="rounded-xl border-2 border-fun-sun bg-fun-sun-light p-3">
            {String(content.reveal ?? "")}
          </p>
        </div>
      );
    }
    case "reading": {
      return (
        <p className="whitespace-pre-wrap rounded-xl border-2 border-fun-border bg-white p-3 text-sm text-fun-text">
          {String(content.text ?? "")}
        </p>
      );
    }
    case "math_problem": {
      const unit = typeof content.unit === "string" ? ` ${content.unit}` : "";
      return (
        <p className="text-sm text-fun-text">
          <span className="font-bold">Réponse attendue&nbsp;: </span>
          {answer.value == null ? "—" : `${String(answer.value)}${unit}`}
          {typeof answer.tolerance === "number" && answer.tolerance > 0 && (
            <span className="text-fun-text-muted">
              {" "}
              (tolérance ±{answer.tolerance})
            </span>
          )}
        </p>
      );
    }
    case "pythagore": {
      const tables = Array.isArray(content.tables)
        ? (content.tables as unknown[]).map(String)
        : [];
      return (
        <p className="text-sm text-fun-text">
          <span className="font-bold">Tables&nbsp;: </span>
          {tables.join(", ") || "—"}
          {content.blanks != null && (
            <span className="text-fun-text-muted">
              {" "}
              · {String(content.blanks)} calculs
            </span>
          )}
        </p>
      );
    }
    case "soroban": {
      return (
        <p className="text-sm text-fun-text">
          <span className="font-bold">
            {content.mode === "build" ? "À construire" : "À lire"}&nbsp;:{" "}
          </span>
          {String(content.value ?? "—")}
        </p>
      );
    }
    default: {
      return (
        <pre className="overflow-x-auto rounded-xl border-2 border-fun-border bg-white p-3 font-mono text-xs text-fun-text">
          {JSON.stringify({ content, correct_answer: answer }, null, 2)}
        </pre>
      );
    }
  }
}

export function ExerciseCard({
  packId,
  lessonId,
  exercise,
  position,
  issues,
  editable,
  onClone,
  cloning,
}: {
  packId: string;
  lessonId: string;
  exercise: PackExercisePreview;
  /** Rang affiché (1-based), aligné sur les ancres du validateur. */
  position: number;
  issues: ValidationIssue[];
  editable: boolean;
  onClone: () => void;
  cloning: boolean;
}) {
  // Un contrôleur par carte : un refus doit s'afficher sous l'exercice concerné,
  // pas sous tous les éditeurs ouverts.
  const quickEdit = useQuickEdit(packId);
  const [editing, setEditing] = useState(false);
  const [question, setQuestion] = useState(exercise.question);
  const [content, setContent] = useState(() =>
    JSON.stringify(exercise.content ?? {}, null, 2)
  );
  const [answer, setAnswer] = useState(() =>
    JSON.stringify(exercise.correct_answer ?? {}, null, 2)
  );
  const [difficulty, setDifficulty] = useState(
    String(exercise.difficulty_level ?? "")
  );
  const [order, setOrder] = useState(String(exercise.order_index));
  const [jsonError, setJsonError] = useState<string | null>(null);

  const exerciseId = exercise.id;

  const submit = () => {
    const parsedContent = parseJsonObject(content);
    const parsedAnswer = parseJsonObject(answer);
    if (!parsedContent || !parsedAnswer) {
      setJsonError(
        "Le contenu et la réponse doivent être des objets JSON valides (accolades incluses)."
      );
      return;
    }
    setJsonError(null);
    if (!exerciseId) return;
    quickEdit.save(
      {
        lessons: [
          {
            id: lessonId,
            exercises: [
              {
                id: exerciseId,
                question,
                content: parsedContent,
                correct_answer: parsedAnswer,
                difficulty_level: difficulty ? Number(difficulty) : null,
                order_index: order ? Number(order) : null,
              },
            ],
          },
        ],
      },
      () => setEditing(false)
    );
  };

  return (
    <li className="rounded-2xl border-2 border-fun-border bg-fun-card p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-fun-violet-light px-2 py-0.5 text-xs font-bold text-fun-violet">
          Exercice {position}
        </span>
        <span className="rounded-full bg-fun-sky-light px-2 py-0.5 text-xs font-bold text-fun-sky">
          {exerciseTypeLabel(exercise.type)}
        </span>
        <span className="rounded-full bg-fun-sun-light px-2 py-0.5 text-xs font-bold text-fun-text">
          Difficulté {exercise.difficulty_level ?? "—"}/5
        </span>
        {editable && !editing && exerciseId && (
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto"
            onClick={() => setEditing(true)}
          >
            <Pencil className="h-4 w-4" />
            Corriger
          </Button>
        )}
      </div>

      {editing ? (
        <div className="mt-3 space-y-3">
          <div className="space-y-1">
            <Label htmlFor={`q-${exerciseId}`} className="text-fun-text">
              Question
            </Label>
            <textarea
              id={`q-${exerciseId}`}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={2}
              className={FIELD_CLASS}
            />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor={`c-${exerciseId}`} className="text-fun-text">
                Contenu (JSON)
              </Label>
              <textarea
                id={`c-${exerciseId}`}
                value={content}
                onChange={(event) => setContent(event.target.value)}
                rows={6}
                spellCheck={false}
                className={cn(FIELD_CLASS, "font-mono text-xs")}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor={`a-${exerciseId}`} className="text-fun-text">
                Bonne réponse (JSON)
              </Label>
              <textarea
                id={`a-${exerciseId}`}
                value={answer}
                onChange={(event) => setAnswer(event.target.value)}
                rows={6}
                spellCheck={false}
                className={cn(FIELD_CLASS, "font-mono text-xs")}
              />
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor={`d-${exerciseId}`} className="text-fun-text">
                Difficulté (1 à 5)
              </Label>
              <Input
                id={`d-${exerciseId}`}
                type="number"
                min={1}
                max={5}
                inputMode="numeric"
                value={difficulty}
                onChange={(event) => setDifficulty(event.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor={`o-${exerciseId}`} className="text-fun-text">
                Position dans la leçon
              </Label>
              <Input
                id={`o-${exerciseId}`}
                type="number"
                min={0}
                inputMode="numeric"
                value={order}
                onChange={(event) => setOrder(event.target.value)}
              />
            </div>
          </div>

          {jsonError && (
            <p className="rounded-xl border-2 border-fun-red bg-fun-red-light p-3 text-sm font-semibold text-fun-text">
              {jsonError}
            </p>
          )}

          <div className="flex flex-wrap gap-2">
            <Button onClick={submit} disabled={quickEdit.isPending}>
              {quickEdit.isPending ? "Enregistrement…" : "Enregistrer"}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setEditing(false);
                setJsonError(null);
                quickEdit.clearFailure();
              }}
            >
              Annuler
            </Button>
          </div>

          {quickEdit.failure && (
            <EditFailure
              failure={quickEdit.failure}
              onClone={onClone}
              cloning={cloning}
            />
          )}
        </div>
      ) : (
        <div className="mt-3 space-y-3">
          <p className="font-bold text-fun-text">{exercise.question}</p>
          <ExerciseBody exercise={exercise} />
          {exercise.explanation && (
            <p className="text-sm text-fun-text-muted">
              <span className="font-bold">Explication&nbsp;: </span>
              {exercise.explanation}
            </p>
          )}
          <IssueList issues={issues} showAnchor={false} />
        </div>
      )}
    </li>
  );
}
