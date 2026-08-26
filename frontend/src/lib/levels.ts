import type { LevelEnum } from "@/lib/api/model";

/** Niveaux scolaires (maternelle → CM2), source unique partagée. */
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
