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

export interface TracingContent {
  /** Lettre ou chiffre à tracer (un caractère). */
  glyph: string;
  /** "capitale", "script" (minuscules d'imprimerie), "cursive" ou "chiffre". */
  style?: "capitale" | "script" | "cursive" | "chiffre";
  /** "guided" : pointillés ; "model" : modèle à côté ; "free" : sans modèle. */
  mode?: "guided" | "model" | "free";
}

export type NoteName = "do" | "ré" | "mi" | "fa" | "sol" | "la" | "si";

export interface MusicNoteContent {
  /** "sol" : clé de sol 2e ligne ; "ut3" : clé d'ut 3e ligne (alto). */
  clef: "sol" | "fa" | "ut3";
  /** "name" : nommer la note affichée ; "place" : poser la note nommée. */
  mode: "name" | "place";
  /** Hauteur en notation anglo-saxonne, ex. "C4" (do du milieu). */
  pitch: string;
  /** Noms proposés (par défaut, les 7 notes). */
  choices?: NoteName[] | null;
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

export type RhythmSymbol =
  | "ronde"
  | "blanche"
  | "noire"
  | "croche"
  | "demi_pause"
  | "soupir"
  | "demi_soupir";

export interface MusicRhythmContent {
  mode?: "count" | "listen" | "tap";
  events: RhythmSymbol[];
  beats_per_bar?: 2 | 3 | 4;
  bpm?: number;
  choices?: { id: string; events: RhythmSymbol[] }[] | null;
}

export interface MusicSequenceContent {
  clef?: "sol" | "fa" | "ut3";
  mode?: "read" | "listen";
  pitches: string[];
  bpm?: number;
}
