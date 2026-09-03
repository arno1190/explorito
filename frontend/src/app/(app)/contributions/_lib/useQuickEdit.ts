"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import {
  getGetMyPackApiV1ContributionsPackIdGetQueryKey,
  useQuickEditPackApiV1ContributionsPackIdPatch as useQuickEditPack,
} from "@/lib/api/generated/contributions/contributions";
import type { PackQuickEdit } from "@/lib/api/model";

import { parseApiFailure, type ApiFailure } from "./contrib";

/** Contrat d'édition partagé par les éditeurs en ligne de l'aperçu. */
export interface QuickEditController {
  /** Enregistre une correction ; `onSaved` n'est appelé qu'au succès. */
  save: (data: PackQuickEdit, onSaved: () => void) => void;
  /** Dernier refus du serveur, à afficher sans effacer la saisie. */
  failure: ApiFailure | null;
  clearFailure: () => void;
  isPending: boolean;
}

/**
 * Édition rapide d'un élément du pack.
 *
 * Le serveur revalide **tout** le pack et refuse l'enregistrement en bloc : on
 * ne sort donc du mode édition qu'au succès, pour ne jamais perdre la saisie du
 * parent sur un refus.
 */
export function useQuickEdit(packId: string): QuickEditController {
  const queryClient = useQueryClient();
  const [failure, setFailure] = useState<ApiFailure | null>(null);

  const mutation = useQuickEditPack({
    mutation: {
      onSuccess: (detail) => {
        setFailure(null);
        queryClient.setQueryData(
          getGetMyPackApiV1ContributionsPackIdGetQueryKey(packId),
          detail
        );
      },
      onError: (error: unknown) => setFailure(parseApiFailure(error)),
    },
  });

  const save = (data: PackQuickEdit, onSaved: () => void) => {
    setFailure(null);
    mutation.mutate({ packId, data }, { onSuccess: onSaved });
  };

  return {
    save,
    failure,
    clearFailure: () => setFailure(null),
    isPending: mutation.isPending,
  };
}
