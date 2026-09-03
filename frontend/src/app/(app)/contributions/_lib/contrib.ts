import axios from "axios";

import { axiosInstance } from "@/lib/api/axios-instance";
import type {
  CommunityStatus,
  UploadResult,
  ValidationIssue,
} from "@/lib/api/model";

/* -------------------------------------------------------------------------- */
/* Erreurs de l'API                                                           */
/* -------------------------------------------------------------------------- */

/** Erreur d'API normalisée : le backend renvoie un `detail` objet **ou** texte. */
export interface ApiFailure {
  status: number;
  code: string | null;
  message: string;
  /** Constats du validateur (422 « pack_invalid »). */
  issues: ValidationIssue[];
  /** Conditions renvoyées par le 428, pour les afficher sans second appel. */
  terms: { version: string; text: string } | null;
}

const GENERIC = "Une erreur est survenue. Réessayez dans un instant.";

export function parseApiFailure(error: unknown): ApiFailure {
  const empty: ApiFailure = {
    status: 0,
    code: null,
    message: GENERIC,
    issues: [],
    terms: null,
  };
  if (!axios.isAxiosError(error)) return empty;

  const status = error.response?.status ?? 0;
  const detail = (error.response?.data as { detail?: unknown } | undefined)
    ?.detail;

  // Un `detail` texte : refus de pseudonyme, JSON illisible…
  if (typeof detail === "string") return { ...empty, status, message: detail };

  // Un `detail` tableau : 422 de Pydantic sur un corps mal formé. Les `loc`
  // techniques n'aident pas un parent, on reste sur le message générique.
  if (Array.isArray(detail)) return { ...empty, status };

  if (detail && typeof detail === "object") {
    const body = detail as Record<string, unknown>;
    return {
      status,
      code: typeof body.code === "string" ? body.code : null,
      message: typeof body.message === "string" ? body.message : GENERIC,
      issues: Array.isArray(body.issues)
        ? (body.issues as ValidationIssue[])
        : [],
      terms:
        typeof body.terms === "string"
          ? {
              version:
                typeof body.terms_version === "string"
                  ? body.terms_version
                  : "",
              text: body.terms,
            }
          : null,
    };
  }
  return { ...empty, status };
}

/* -------------------------------------------------------------------------- */
/* Envoi d'un pack                                                            */
/* -------------------------------------------------------------------------- */

export type UploadSource =
  | { kind: "file"; file: File }
  | { kind: "text"; text: string };

export interface UploadArgs {
  source: UploadSource;
  acceptTerms?: boolean;
  handle?: string | null;
}

/**
 * Le client généré n'expose aucun corps pour cet envoi : l'endpoint lit la
 * requête brute (JSON collé **ou** multipart), ce que l'OpenAPI ne décrit pas.
 * On passe donc par l'instance axios partagée, qui porte déjà la session.
 */
export function uploadPack({
  source,
  acceptTerms,
  handle,
}: UploadArgs): Promise<UploadResult> {
  const params = new URLSearchParams();
  if (acceptTerms) params.set("accept_terms", "true");
  if (handle) params.set("handle", handle);
  const query = params.toString();
  const url = `/api/v1/contributions${query ? `?${query}` : ""}`;

  if (source.kind === "file") {
    const form = new FormData();
    form.append("file", source.file);
    return axiosInstance<UploadResult>({ url, method: "POST", data: form });
  }
  return axiosInstance<UploadResult>({
    url,
    method: "POST",
    data: source.text,
    headers: { "Content-Type": "application/json" },
  });
}

/** Titre du bandeau d'erreur d'envoi, un par cause documentée. */
export function uploadFailureTitle(failure: ApiFailure): string {
  switch (failure.status) {
    case 413:
      return "Fichier trop volumineux";
    case 429:
      return "Limite d'envois atteinte pour aujourd'hui";
    case 422:
      return failure.code === "pack_invalid"
        ? `${failure.issues.length} point(s) à corriger avant l'envoi`
        : "Pseudonyme refusé";
    case 409:
      return "Pseudonyme déjà pris";
    case 400:
      return "Fichier illisible";
    default:
      return "Envoi impossible";
  }
}

/* -------------------------------------------------------------------------- */
/* Libellés                                                                   */
/* -------------------------------------------------------------------------- */

interface StatusStyle {
  label: string;
  className: string;
  /** Ce que le statut change *concrètement* pour le parent. */
  hint: string;
}

/**
 * La visibilité familiale est indépendante du statut communautaire (sauf
 * `blocked`) : c'est la nuance qui évite de croire qu'un refus efface le pack.
 */
export const STATUS_STYLES: Record<CommunityStatus, StatusStyle> = {
  draft: {
    label: "Brouillon",
    className: "bg-fun-sun-light text-fun-text",
    hint: "Visible de vous seul. Soumettez-le pour que vos enfants y jouent.",
  },
  pending: {
    label: "En attente de relecture",
    className: "bg-fun-sky-light text-fun-sky",
    hint: "Déjà jouable par vos enfants ; les autres familles attendent la revue.",
  },
  approved: {
    label: "Publié",
    className: "bg-fun-green-light text-fun-green",
    hint: "Visible au catalogue des autres familles. Verrouillé : clonez-le pour le réviser.",
  },
  rejected: {
    label: "Refusé pour la communauté",
    className: "bg-fun-accent-light text-fun-accent-dark",
    hint: "Vos enfants gardent le pack : seule la publication aux autres familles est refusée.",
  },
  blocked: {
    label: "Bloqué",
    className: "bg-fun-red-light text-fun-red",
    hint: "Masqué pour tout le monde, vous compris. Écrivez-nous si c'est une erreur.",
  },
};

export function statusStyle(status: CommunityStatus): StatusStyle {
  return (
    STATUS_STYLES[status] ?? {
      label: status,
      className: "bg-fun-border text-fun-text",
      hint: "",
    }
  );
}

const SEVERITY_STYLES = {
  error: {
    label: "À corriger",
    box: "border-fun-red bg-fun-red-light",
    chip: "bg-fun-red text-white",
  },
  warning: {
    label: "Conseil",
    box: "border-fun-sun bg-fun-sun-light",
    chip: "bg-fun-sun text-fun-text",
  },
  flag: {
    label: "À vérifier",
    box: "border-fun-violet bg-fun-violet-light",
    chip: "bg-fun-violet text-white",
  },
} as const;

export function severityStyle(severity: string) {
  return (
    SEVERITY_STYLES[severity as keyof typeof SEVERITY_STYLES] ??
    SEVERITY_STYLES.warning
  );
}

/**
 * Le validateur préfixe déjà ses messages par « leçon 2, exercice 3 : ». On
 * détache ce repère pour l'afficher comme étiquette au lieu de le répéter.
 */
const ANCHOR_PREFIX = /^le[çc]on\s+\d+(\s*,\s*exercice\s+\d+)?\s*:?\s*/i;

export function issueRow(issue: ValidationIssue): {
  anchor: string;
  message: string;
} {
  const parts: string[] = [];
  if (issue.lesson_index != null) parts.push(`Leçon ${issue.lesson_index + 1}`);
  if (issue.exercise_index != null)
    parts.push(`exercice ${issue.exercise_index + 1}`);
  const anchor = parts.join(", ");
  const message = anchor
    ? issue.message.replace(ANCHOR_PREFIX, "").trim()
    : issue.message.trim();
  return { anchor, message: message || issue.message };
}

/** Constats portant exactement sur cette leçon (et non sur un de ses exercices). */
export function lessonIssues(
  issues: ValidationIssue[],
  lessonIndex: number
): ValidationIssue[] {
  return issues.filter(
    (issue) =>
      issue.lesson_index === lessonIndex && issue.exercise_index == null
  );
}

/** Constats portant sur un exercice précis. */
export function exerciseIssues(
  issues: ValidationIssue[],
  lessonIndex: number,
  exerciseIndex: number
): ValidationIssue[] {
  return issues.filter(
    (issue) =>
      issue.lesson_index === lessonIndex &&
      issue.exercise_index === exerciseIndex
  );
}

/** Constats sans ancre : ils concernent le pack entier. */
export function packIssues(issues: ValidationIssue[]): ValidationIssue[] {
  return issues.filter((issue) => issue.lesson_index == null);
}

const EXERCISE_TYPE_LABELS: Record<string, string> = {
  multiple_choice: "QCM",
  fill_blanks: "Texte à trous",
  reveal: "Carte à révéler",
  pythagore: "Tables de multiplication",
  math_problem: "Problème",
  reading: "Lecture",
  soroban: "Boulier",
};

/** Nom français d'un type d'exercice (le type brut sinon : un pack peut en porter un inconnu). */
export function exerciseTypeLabel(type: string): string {
  return EXERCISE_TYPE_LABELS[type] ?? type;
}

/** Lit un champ JSON saisi à la main ; `null` si la saisie est inexploitable. */
export function parseJsonObject(
  raw: string
): { [key: string]: unknown } | null {
  const trimmed = raw.trim();
  if (!trimmed) return {};
  try {
    const parsed: unknown = JSON.parse(trimmed);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as { [key: string]: unknown };
    }
    return null;
  } catch {
    return null;
  }
}
