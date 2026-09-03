"use client";

import { useQueryClient } from "@tanstack/react-query";
import {
  getGetChildAccessApiV1LibraryChildrenChildIdAccessGetQueryKey as childAccessKey,
  useGetChildAccessApiV1LibraryChildrenChildIdAccessGet as useChildAccess,
  usePutAutoEnableApiV1LibraryChildrenChildIdAutoEnablePut as usePutAutoEnable,
  usePutChildAccessApiV1LibraryChildrenChildIdAccessPackIdPut as usePutChildAccess,
} from "@/lib/api/generated/library/library";
import type { ChildResponse, PackSummary } from "@/lib/api/model";
import { UserAvatar } from "@/components/profile/UserAvatar";
import { LEVEL_SHORT, LEVEL_VALUES, Toggle } from "./pack-ui";

/**
 * Un interrupteur par (enfant, pack). Chaque instance s'abonne à la requête
 * d'accès de SON enfant : react-query dédoublonne par clé, donc N enfants ×
 * M packs ne déclenchent que N requêtes.
 */
export function ChildPackToggle({
  child,
  pack,
}: {
  child: ChildResponse;
  pack: PackSummary;
}) {
  const queryClient = useQueryClient();
  const { data, isPending } = useChildAccess(child.id);
  const putAccess = usePutChildAccess({
    mutation: {
      onSuccess: () =>
        queryClient.invalidateQueries({ queryKey: childAccessKey(child.id) }),
    },
  });

  const entry = data?.entries?.find((e) => e.pack_id === pack.id);

  // L'auto-activation est évaluée à la lecture côté serveur : elle rend actif
  // tout pack communautaire approuvé couvrant le niveau de l'enfant. Une ligne
  // d'accès explicite fait autorité dans les deux sens (une ligne « désactivé »
  // oppose son veto à l'auto-activation).
  const levelIndex = child.level ? LEVEL_VALUES.indexOf(child.level) : -1;
  const coversLevel =
    levelIndex >= 0 &&
    LEVEL_VALUES.indexOf(pack.level_min) <= levelIndex &&
    levelIndex <= LEVEL_VALUES.indexOf(pack.level_max);
  const viaAutoEnable =
    !entry &&
    (data?.auto_enable_approved_packs ?? false) &&
    pack.origin === "community" &&
    pack.community_status === "approved" &&
    coversLevel;

  const enabled = entry ? entry.enabled : viaAutoEnable;
  const busy = isPending || putAccess.isPending;

  return (
    <div className="flex min-h-12 items-center justify-between gap-3 rounded-2xl border-2 border-fun-border bg-white px-3 py-2">
      <span className="flex min-w-0 items-center gap-2">
        <UserAvatar
          avatar={child.avatar_url}
          name={child.name}
          className="h-8 w-8"
          textClassName="text-base"
        />
        <span className="min-w-0">
          <span className="block truncate font-semibold text-fun-text">
            {child.name}
          </span>
          <span className="block text-xs text-fun-text-muted">
            {viaAutoEnable
              ? "Activé automatiquement (packs approuvés de son niveau)"
              : enabled
                ? "Activé par vous"
                : "Non activé"}
            {child.level ? ` · ${LEVEL_SHORT[child.level] ?? child.level}` : ""}
          </span>
        </span>
      </span>
      <Toggle
        checked={enabled}
        disabled={busy}
        label={`${enabled ? "Désactiver" : "Activer"} ce pack pour ${child.name}`}
        onChange={(next) =>
          putAccess.mutate({
            childId: child.id,
            packId: pack.id,
            data: { enabled: next },
          })
        }
      />
    </div>
  );
}

/** Interrupteur « auto-activer les packs approuvés de son niveau », par enfant. */
export function ChildAutoEnableRow({ child }: { child: ChildResponse }) {
  const queryClient = useQueryClient();
  const { data, isPending } = useChildAccess(child.id);
  const putAutoEnable = usePutAutoEnable({
    mutation: {
      onSuccess: () =>
        queryClient.invalidateQueries({ queryKey: childAccessKey(child.id) }),
    },
  });

  const enabled = data?.auto_enable_approved_packs ?? false;
  const activeCount = (data?.entries ?? []).filter((e) => e.enabled).length;

  return (
    <div className="flex min-h-12 items-start justify-between gap-3 rounded-2xl border-2 border-fun-border bg-white p-4">
      <span className="flex min-w-0 items-start gap-3">
        <UserAvatar
          avatar={child.avatar_url}
          name={child.name}
          className="h-10 w-10"
          textClassName="text-xl"
        />
        <span className="min-w-0">
          <span className="block font-bold text-fun-text">{child.name}</span>
          <span className="block text-sm text-fun-text-muted">
            Activer automatiquement les packs approuvés de son niveau
          </span>
          <span className="mt-1 block text-xs text-fun-text-muted">
            {enabled
              ? "Vous faites confiance à la relecture : tout nouveau pack approuvé de son niveau s'active sans votre validation. Vous pouvez toujours en désactiver un individuellement."
              : "Désactivé : chaque pack de la communauté demande votre accord."}{" "}
            {activeCount} pack{activeCount > 1 ? "s" : ""} de la communauté
            activé{activeCount > 1 ? "s" : ""} explicitement pour {child.name}.
          </span>
        </span>
      </span>
      <Toggle
        checked={enabled}
        disabled={isPending || putAutoEnable.isPending}
        label={`Auto-activation des packs approuvés pour ${child.name}`}
        onChange={(next) =>
          putAutoEnable.mutate({ childId: child.id, data: { enabled: next } })
        }
      />
    </div>
  );
}
