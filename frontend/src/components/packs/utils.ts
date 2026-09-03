import type { PackPathLesson } from "@/lib/api/model";

const TIER_LABELS: Record<number, string> = {
  1: "Niveau 1 · Découverte",
  2: "Niveau 2 · Entraînement",
  3: "Niveau 3 · Défi",
};

/** Même libellé de palier que `subjects/[id]` : l'enfant voit un seul vocabulaire. */
export function tierLabel(tier: number): string {
  return TIER_LABELS[tier] ?? `Niveau ${tier}`;
}

export interface TierGroup {
  tier: number;
  /** Toutes les leçons du palier, filtrage d'affichage non appliqué. */
  lessons: PackPathLesson[];
}

/** Regroupe des leçons par palier, paliers triés croissants. */
export function groupByTier(lessons: PackPathLesson[]): TierGroup[] {
  const map = new Map<number, PackPathLesson[]>();
  for (const lesson of lessons) {
    const tier = lesson.tier ?? 0;
    const bucket = map.get(tier);
    if (bucket) bucket.push(lesson);
    else map.set(tier, [lesson]);
  }
  return [...map.keys()]
    .sort((a, b) => a - b)
    .map((tier) => ({ tier, lessons: map.get(tier)! }));
}

/**
 * Le verrou d'un palier se lit sur *toutes* ses leçons, jamais sur la liste
 * filtrée : masquer les leçons terminées ne doit pas déverrouiller un palier.
 */
export function isTierLocked(lessons: PackPathLesson[]): boolean {
  return lessons.length > 0 && lessons.every((l) => l.locked);
}

/** Icônes de matière distinctes d'un pack, dans l'ordre d'apparition. */
export function distinctSubjectIcons(lessons: PackPathLesson[]): string[] {
  const seen: string[] = [];
  for (const lesson of lessons) {
    const icon = lesson.subject_icon;
    if (icon && !seen.includes(icon)) seen.push(icon);
  }
  return seen;
}

export function frDate(iso?: string | null): string {
  if (!iso) return "—";
  // Le backend renvoie des dates UTC naïves (sans fuseau) : sans marqueur, le
  // navigateur les interprète comme locales. On force UTC puis on affiche dans
  // le fuseau du navigateur.
  const hasTz = /[zZ]|[+-]\d{2}:\d{2}$/.test(iso);
  return new Date(hasTz ? iso : `${iso}Z`).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}
