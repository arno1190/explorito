/**
 * Formes de contenu typées par type d'exercice, alignées sur le contrat backend
 * (`app/schemas/exercise.py`). Le champ `content` de l'API est un objet générique ;
 * on le restreint ici par type d'exercice.
 */

export interface McqOption {
  id: string;
  text: string;
  image?: string | null;
  /** Aplat de couleur (CSS) pour les non-lecteurs : option affichée en pastille. */
  color?: string | null;
}

export interface MultipleChoiceContent {
  options: McqOption[];
  multiple?: boolean;
}

export interface FillBlanksContent {
  text: string;
}

export interface RevealContent {
  prompt: string;
  reveal: string;
}

export interface PythagoreContent {
  tables: number[];
  blanks?: number;
}

export interface MathProblemContent {
  unit?: string | null;
}

export interface ReadingContent {
  text: string;
  image?: string | null;
}

export interface SorobanContent {
  /** "read" : lire le nombre affiché ; "build" : construire le nombre cible. */
  mode: "read" | "build";
  value: number;
  /** Nombre de tiges affichées (par défaut, dérivé de `value`). */
  columns?: number | null;
}

/** Réponse prête pour l'API `POST /exercises/{id}/submit` (champ `answer`). */
export type AnswerPayload = Record<string, unknown> | null;

export interface ExerciseTypeComponentProps<TContent> {
  question: string;
  content: TContent;
  emoji?: string;
  onAnswer: (answer: AnswerPayload) => void;
  disabled?: boolean;
  showResult?: boolean;
  isCorrect?: boolean;
}
