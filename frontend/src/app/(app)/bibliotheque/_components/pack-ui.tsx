"use client";

import { useState } from "react";
import {
  AlertTriangle,
  Check,
  ChevronDown,
  ChevronRight,
  Flag,
  Info,
  Sparkles,
} from "lucide-react";
import type {
  PackExercisePreview,
  PackLessonPreview,
  ValidationIssue,
} from "@/lib/api/model";

/**
 * Briques partagées par les deux surfaces adultes qui lisent un pack : le
 * catalogue parent (avant activation) et la file de modération (avant verdict).
 * Le même rendu des deux côtés garantit que l'admin approuve exactement ce que
 * le parent lira.
 */

export const LEVEL_LABELS: Record<string, string> = {
  ps: "Petite section",
  ms: "Moyenne section",
  gs: "Grande section",
  cp: "CP",
  ce1: "CE1",
  ce2: "CE2",
  cm1: "CM1",
  cm2: "CM2",
};

export const LEVEL_SHORT: Record<string, string> = {
  ps: "PS",
  ms: "MS",
  gs: "GS",
  cp: "CP",
  ce1: "CE1",
  ce2: "CE2",
  cm1: "CM1",
  cm2: "CM2",
};

export const LEVEL_VALUES = [
  "ps",
  "ms",
  "gs",
  "cp",
  "ce1",
  "ce2",
  "cm1",
  "cm2",
] as const;

export const EXERCISE_TYPE_LABELS: Record<string, string> = {
  multiple_choice: "Choix multiple",
  fill_blanks: "Compléter les trous",
  reveal: "Carte à révéler",
  pythagore: "Table de multiplication",
  math_problem: "Problème de maths",
  reading: "Lecture",
  soroban: "Soroban",
};

export function levelRange(min?: string | null, max?: string | null): string {
  const a = min ? (LEVEL_SHORT[min] ?? min) : null;
  const b = max ? (LEVEL_SHORT[max] ?? max) : null;
  if (!a && !b) return "Tous niveaux";
  if (!b || a === b) return a ?? b ?? "Tous niveaux";
  return `${a} → ${b}`;
}

export function frDate(iso?: string | null, withTime = false): string {
  if (!iso) return "—";
  // Le backend renvoie des dates UTC naïves : sans marqueur, le navigateur les
  // interpréterait comme locales.
  const hasTz = /[zZ]|[+-]\d{2}:\d{2}$/.test(iso);
  const d = new Date(hasTz ? iso : `${iso}Z`);
  return d.toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  });
}

/** Rend n'importe quelle valeur JSON en texte lisible (contenus libres). */
export function readableValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.map((v) => readableValue(v)).join(" · ");
  }
  const entries = Object.entries(value as Record<string, unknown>);
  if (entries.length === 0) return "—";
  if (entries.length === 1) return readableValue(entries[0][1]);
  return entries.map(([k, v]) => `${k} : ${readableValue(v)}`).join(" · ");
}

type ExerciseOption = { id: string; label: string };

/**
 * Lecture du contenu d'un exercice tel que le backend le stocke : les QCM
 * portent `content.options = [{id, text}]` et `correct_answer.option_ids`,
 * les textes à trous `correct_answer.blanks`, les problèmes de maths
 * `correct_answer.value`. Les identifiants d'options seuls ne veulent rien
 * dire pour un relecteur : il faut les résoudre en libellés.
 */
function readExercise(exercise: PackExercisePreview): {
  options: ExerciseOption[] | null;
  support: string | null;
  correctIds: string[];
  answer: string | null;
} {
  const content = (exercise.content ?? {}) as Record<string, unknown>;
  const rawOptions = content.options;
  const options = Array.isArray(rawOptions)
    ? rawOptions.map((option, i) => {
        if (option && typeof option === "object") {
          const record = option as Record<string, unknown>;
          return {
            id: String(record.id ?? i),
            label: String(record.text ?? readableValue(option)),
          };
        }
        return { id: String(i), label: readableValue(option) };
      })
    : null;

  const support = typeof content.text === "string" ? content.text : null;

  const correct = (exercise.correct_answer ?? {}) as Record<string, unknown>;
  const rawIds = correct.option_ids;
  const correctIds = Array.isArray(rawIds) ? rawIds.map(String) : [];

  let answer: string | null = null;
  if (correctIds.length > 0) {
    answer = correctIds
      .map((id) => options?.find((o) => o.id === id)?.label ?? id)
      .join(" · ");
  } else if (Object.keys(correct).length > 0) {
    answer = readableValue(correct);
  }

  return { options, support, correctIds, answer };
}

/** Pastille violette réutilisée pour les compteurs et les étiquettes. */
export function Pill({
  children,
  tone = "violet",
}: {
  children: React.ReactNode;
  tone?: "violet" | "green" | "sky" | "sun" | "red" | "accent";
}) {
  const tones: Record<string, string> = {
    violet: "bg-fun-violet-light text-fun-violet",
    green: "bg-fun-green-light text-fun-green-dark",
    sky: "bg-fun-sky-light text-fun-sky",
    sun: "bg-fun-sun-light text-fun-accent-dark",
    red: "bg-fun-red-light text-fun-red",
    accent: "bg-fun-accent-light text-fun-accent-dark",
  };
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-bold ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

/** Interrupteur accessible (pas de primitive Switch dans le projet). */
export function Toggle({
  checked,
  onChange,
  disabled = false,
  label,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  disabled?: boolean;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`flex h-8 w-14 shrink-0 items-center rounded-full border-2 p-0.5 transition-colors ${
        checked
          ? "border-fun-green bg-fun-green"
          : "border-fun-border bg-fun-surface"
      } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
    >
      <span
        className={`block h-7 w-7 rounded-full transition-transform ${
          checked ? "translate-x-6 bg-white" : "translate-x-0 bg-fun-border"
        }`}
      />
    </button>
  );
}

export function QualityScore({ score }: { score?: number | null }) {
  if (score === null || score === undefined) {
    return <Pill tone="sky">Qualité non notée</Pill>;
  }
  const tone = score >= 80 ? "green" : score >= 50 ? "sun" : "red";
  return (
    <Pill tone={tone}>
      <Sparkles className="mr-1 inline h-3 w-3" />
      Qualité {score}/100
    </Pill>
  );
}

const SEVERITY_STYLE: Record<
  string,
  { label: string; box: string; icon: React.ReactNode }
> = {
  error: {
    label: "Erreur",
    box: "border-fun-red bg-fun-red-light text-fun-red",
    icon: <AlertTriangle className="h-4 w-4 shrink-0" />,
  },
  warning: {
    label: "Avertissement",
    box: "border-fun-accent bg-fun-accent-light text-fun-accent-dark",
    icon: <AlertTriangle className="h-4 w-4 shrink-0" />,
  },
  flag: {
    label: "À vérifier",
    box: "border-fun-violet bg-fun-violet-light text-fun-violet",
    icon: <Flag className="h-4 w-4 shrink-0" />,
  },
};

/** Constats du validateur, ancrés sur la leçon/l'exercice fautif. */
export function ValidationIssues({ issues }: { issues?: ValidationIssue[] }) {
  if (!issues || issues.length === 0) {
    return (
      <p className="flex items-center gap-2 text-sm text-fun-text-muted">
        <Info className="h-4 w-4" />
        Aucun constat du validateur.
      </p>
    );
  }
  return (
    <ul className="space-y-2">
      {issues.map((issue, i) => {
        const style = SEVERITY_STYLE[issue.severity] ?? SEVERITY_STYLE.flag;
        const anchor = [
          issue.lesson_index !== null && issue.lesson_index !== undefined
            ? `leçon ${issue.lesson_index + 1}`
            : null,
          issue.exercise_index !== null && issue.exercise_index !== undefined
            ? `exercice ${issue.exercise_index + 1}`
            : null,
          issue.field ? `champ « ${issue.field} »` : null,
        ]
          .filter(Boolean)
          .join(" · ");
        return (
          <li
            key={`${issue.code}-${i}`}
            className={`flex items-start gap-2 rounded-2xl border-2 p-3 text-sm ${style.box}`}
          >
            {style.icon}
            <span>
              <strong className="font-bold">{style.label}</strong> —{" "}
              {issue.message}
              <span className="block text-xs opacity-80">
                {issue.code}
                {anchor ? ` · ${anchor}` : ""}
              </span>
            </span>
          </li>
        );
      })}
    </ul>
  );
}

function ExerciseRow({
  exercise,
  showAnswers,
}: {
  exercise: PackExercisePreview;
  showAnswers: boolean;
}) {
  const { options, support, correctIds, answer } = readExercise(exercise);
  return (
    <li className="rounded-2xl border-2 border-fun-border bg-white p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-bold text-fun-text-muted">
          #{exercise.order_index + 1}
        </span>
        <Pill tone="sky">
          {EXERCISE_TYPE_LABELS[exercise.type] ?? exercise.type}
        </Pill>
        {exercise.difficulty_level ? (
          <Pill tone="violet">Difficulté {exercise.difficulty_level}</Pill>
        ) : null}
      </div>
      <p className="mt-2 font-semibold text-fun-text">{exercise.question}</p>
      {support && !exercise.question.includes(support) ? (
        <p className="mt-2 rounded-xl bg-fun-surface p-2 text-sm text-fun-text">
          {support}
        </p>
      ) : null}
      {options ? (
        <ul className="mt-2 flex flex-wrap gap-2">
          {options.map((option) => {
            const isCorrect = showAnswers && correctIds.includes(option.id);
            return (
              <li
                key={option.id}
                className={`flex items-center gap-1 rounded-xl px-2 py-1 text-sm ${
                  isCorrect
                    ? "bg-fun-green-light font-bold text-fun-green-dark"
                    : "bg-fun-surface text-fun-text"
                }`}
              >
                {isCorrect ? <Check className="h-3 w-3 shrink-0" /> : null}
                {option.label}
              </li>
            );
          })}
        </ul>
      ) : null}
      {showAnswers && answer ? (
        <p className="mt-2 rounded-xl bg-fun-green-light px-2 py-1 text-sm font-bold text-fun-green-dark">
          Bonne réponse : {answer}
        </p>
      ) : null}
      {exercise.explanation ? (
        <p className="mt-2 text-sm text-fun-text-muted">
          Explication : {exercise.explanation}
        </p>
      ) : null}
    </li>
  );
}

function LessonBlock({
  lesson,
  index,
  showAnswers,
}: {
  lesson: PackLessonPreview;
  index: number;
  showAnswers: boolean;
}) {
  const [open, setOpen] = useState(true);
  const exercises = lesson.exercises ?? [];
  return (
    <div className="rounded-2xl border-2 border-fun-border bg-fun-card">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 p-4 text-left"
      >
        {open ? (
          <ChevronDown className="h-5 w-5 shrink-0 text-fun-text-muted" />
        ) : (
          <ChevronRight className="h-5 w-5 shrink-0 text-fun-text-muted" />
        )}
        <span className="text-2xl">{lesson.subject_icon ?? "📘"}</span>
        <span className="min-w-0 flex-1">
          <span className="block font-bold text-fun-text">
            {index + 1}. {lesson.name}
          </span>
          <span className="block text-sm text-fun-text-muted">
            {lesson.subject_name ?? lesson.subject_slug} ·{" "}
            {LEVEL_SHORT[lesson.level] ?? lesson.level} · palier {lesson.tier} ·{" "}
            {exercises.length} exercice{exercises.length > 1 ? "s" : ""} ·{" "}
            {lesson.xp_reward ?? 0} XP
          </span>
        </span>
      </button>
      {open ? (
        <div className="space-y-3 px-4 pb-4">
          {lesson.description ? (
            <p className="text-sm text-fun-text-muted">{lesson.description}</p>
          ) : null}
          {exercises.length === 0 ? (
            <p className="text-sm text-fun-text-muted">
              Aucun exercice dans cette leçon.
            </p>
          ) : (
            <ul className="space-y-2">
              {exercises.map((ex, i) => (
                <ExerciseRow
                  key={ex.id ?? `${lesson.name}-${i}`}
                  exercise={ex}
                  showAnswers={showAnswers}
                />
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}

/**
 * Contenu complet d'un pack : toutes les leçons, tous les exercices.
 * ``showAnswers`` expose les bonnes réponses (le parent lit avant d'activer,
 * l'admin doit pouvoir vérifier l'arithmétique).
 */
export function PackContent({
  lessons,
  showAnswers = true,
}: {
  lessons?: PackLessonPreview[];
  showAnswers?: boolean;
}) {
  if (!lessons || lessons.length === 0) {
    return (
      <p className="text-sm text-fun-text-muted">
        Ce pack ne contient aucune leçon.
      </p>
    );
  }
  return (
    <div className="space-y-3">
      {lessons.map((lesson, i) => (
        <LessonBlock
          key={lesson.id ?? `${lesson.name}-${i}`}
          lesson={lesson}
          index={i}
          showAnswers={showAnswers}
        />
      ))}
    </div>
  );
}

export const REPORT_REASON_LABELS: Record<string, string> = {
  inappropriate: "Contenu inapproprié",
  wrong_content: "Contenu faux ou erroné",
  personal_data: "Données personnelles",
  duplicate: "Doublon d'un pack existant",
  other: "Autre",
};
