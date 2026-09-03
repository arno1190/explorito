"use client";

import { useState } from "react";
import { Pencil } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { tierLabel } from "@/components/packs/utils";
import type { PackLessonPreview, ValidationIssue } from "@/lib/api/model";

import { exerciseIssues, lessonIssues } from "../_lib/contrib";
import { useQuickEdit } from "../_lib/useQuickEdit";
import { EditFailure } from "./EditFailure";
import { ExerciseCard } from "./ExerciseCard";
import { IssueList } from "./IssueList";

export function LessonCard({
  packId,
  lesson,
  index,
  issues,
  editable,
  onClone,
  cloning,
}: {
  packId: string;
  lesson: PackLessonPreview;
  /** Rang 0-based : c'est l'ancre utilisée par les constats du validateur. */
  index: number;
  issues: ValidationIssue[];
  editable: boolean;
  onClone: () => void;
  cloning: boolean;
}) {
  const quickEdit = useQuickEdit(packId);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(lesson.name);
  const [description, setDescription] = useState(lesson.description ?? "");
  const [tier, setTier] = useState(String(lesson.tier));

  const lessonId = lesson.id;
  const exercises = lesson.exercises ?? [];

  const submit = () => {
    if (!lessonId) return;
    quickEdit.save(
      {
        lessons: [
          {
            id: lessonId,
            name,
            description,
            tier: tier ? Number(tier) : null,
          },
        ],
      },
      () => setEditing(false)
    );
  };

  return (
    <section className="rounded-2xl bg-white p-4 candy-shadow">
      <div className="flex flex-wrap items-start gap-3">
        <span className="text-2xl" aria-hidden>
          {lesson.subject_icon || "📘"}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold text-fun-text-muted">
            Leçon {index + 1}
          </p>
          <h3 className="text-lg font-extrabold text-fun-text">
            {lesson.name}
          </h3>
          <p className="mt-1 flex flex-wrap gap-2">
            <span className="rounded-full bg-fun-sky-light px-2 py-0.5 text-xs font-bold text-fun-sky">
              {lesson.subject_name ?? lesson.subject_slug}
            </span>
            <span className="rounded-full bg-fun-green-light px-2 py-0.5 text-xs font-bold text-fun-green">
              {lesson.level.toUpperCase()}
            </span>
            <span className="rounded-full bg-fun-violet-light px-2 py-0.5 text-xs font-bold text-fun-violet">
              {tierLabel(lesson.tier)}
            </span>
            <span className="rounded-full bg-fun-sun-light px-2 py-0.5 text-xs font-bold text-fun-text">
              {lesson.xp_reward ?? 0} XP
            </span>
          </p>
          {lesson.description && (
            <p className="mt-2 text-sm text-fun-text-muted">
              {lesson.description}
            </p>
          )}
        </div>
        {editable && !editing && lessonId && (
          <Button variant="ghost" size="sm" onClick={() => setEditing(true)}>
            <Pencil className="h-4 w-4" />
            Corriger
          </Button>
        )}
      </div>

      {editing && (
        <div className="mt-4 space-y-3">
          <div className="space-y-1">
            <Label htmlFor={`ln-${lessonId}`} className="text-fun-text">
              Titre de la leçon
            </Label>
            <Input
              id={`ln-${lessonId}`}
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor={`ld-${lessonId}`} className="text-fun-text">
              Description
            </Label>
            <textarea
              id={`ld-${lessonId}`}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={2}
              className="w-full rounded-xl border-2 border-fun-border bg-white p-3 text-sm text-fun-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fun-sky"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor={`lt-${lessonId}`} className="text-fun-text">
              Palier
            </Label>
            <select
              id={`lt-${lessonId}`}
              value={tier}
              onChange={(event) => setTier(event.target.value)}
              className="h-12 w-full rounded-xl border-2 border-fun-border bg-white px-3 text-sm font-semibold text-fun-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fun-sky"
            >
              <option value="1">Niveau 1 · Découverte</option>
              <option value="2">Niveau 2 · Entraînement</option>
              <option value="3">Niveau 3 · Défi</option>
            </select>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={submit} disabled={quickEdit.isPending}>
              {quickEdit.isPending ? "Enregistrement…" : "Enregistrer"}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setEditing(false);
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
      )}

      <IssueList
        className="mt-3"
        issues={lessonIssues(issues, index)}
        showAnchor={false}
      />

      <ul className="mt-4 space-y-3">
        {exercises.map((exercise, exerciseIndex) => (
          <ExerciseCard
            key={exercise.id ?? exerciseIndex}
            packId={packId}
            lessonId={lessonId ?? ""}
            exercise={exercise}
            position={exerciseIndex + 1}
            issues={exerciseIssues(issues, index, exerciseIndex)}
            editable={editable}
            onClone={onClone}
            cloning={cloning}
          />
        ))}
      </ul>
    </section>
  );
}
