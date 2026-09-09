import type { LevelEnum } from "@/lib/api/model";
import { useGetAvailableLevelsApiV1ChildrenLevelsGet as useApiAvailableLevels } from "@/lib/api/generated/children/children";

/**
 * Libellés des niveaux scolaires, dans l'ordre pédagogique.
 *
 * Ceci est une table de **libellés**, pas un catalogue : la question « ce
 * niveau a-t-il du contenu ? » se tranche côté API (`useAvailableLevels`).
 * L'ordre alphabétique des valeurs est faux (« ce1 » < « cp »), donc cet ordre
 * est celui qui fait foi côté affichage.
 */
export const LEVELS: { value: LevelEnum; label: string }[] = [
  { value: "ps", label: "Petite Section" },
  { value: "ms", label: "Moyenne Section" },
  { value: "gs", label: "Grande Section" },
  { value: "cp", label: "CP" },
  { value: "ce1", label: "CE1" },
  { value: "ce2", label: "CE2" },
  { value: "cm1", label: "CM1" },
  { value: "cm2", label: "CM2" },
];

/** Libellé d'un niveau, ou sa valeur brute si elle est inconnue. */
export function levelLabel(value: LevelEnum | null | undefined): string {
  if (!value) return "";
  return LEVELS.find((l) => l.value === value)?.label ?? value;
}

/**
 * Restreint les libellés aux niveaux proposables, dans l'ordre pédagogique.
 *
 * Fonction pure, pour les sélecteurs rendus dans une boucle (un par enfant),
 * où un hook ne peut pas être appelé.
 *
 * @param available Niveaux ayant du contenu, tels que renvoyés par l'API.
 * @param keep Niveau à conserver même s'il n'a plus de contenu — celui de
 *   l'enfant concerné. Le masquer retirerait sa propre valeur du sélecteur, et
 *   l'enregistrement changerait son niveau en silence.
 */
export function levelsFor(
  available: readonly LevelEnum[] | undefined,
  keep?: LevelEnum | null
): { value: LevelEnum; label: string }[] {
  // Tant que la liste n'est pas connue (chargement, ou API en échec), on
  // n'affiche rien plutôt que tout : proposer un niveau vide est précisément
  // le mauvais premier contact que cette issue supprime.
  const offered = new Set<LevelEnum>(available ?? []);
  if (keep) offered.add(keep);
  return LEVELS.filter((l) => offered.has(l.value));
}

/**
 * Niveaux réellement proposables à un enfant, dérivés du contenu publié.
 *
 * Une liste en dur finit par promettre un niveau qu'on a cessé de semer : une
 * famille le choisit et arrive sur une application vide (issue #23). La liste
 * vient donc de l'API et suit le contenu.
 *
 * @param keep Voir {@link levelsFor}.
 */
export function useAvailableLevels(keep?: LevelEnum | null) {
  const { data, isLoading, isError } = useApiAvailableLevels();

  return {
    levels: levelsFor(data, keep),
    /** Liste brute renvoyée par l'API, à passer à {@link levelsFor}. */
    available: data,
    isLoading,
    isError,
  };
}
