"use client";

import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { UserAvatar } from "@/components/profile/UserAvatar";
import {
  getGuardiansApiV1ChildrenChildIdGuardiansGet as getGuardians,
  removeChildGuardianApiV1ChildrenChildIdGuardiansGuardianIdDelete as removeGuardian,
} from "@/lib/api/generated/children/children";
import type { GuardianResponse } from "@/lib/api/model";

interface ManageAccessDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  childId: string;
  childName: string;
}

const ROLE_LABEL: Record<string, string> = {
  owner: "Propriétaire",
  parent: "Co-parent",
  grandparent: "Grand-parent",
  guardian: "Responsable",
};

/** Écran de gestion des accès d'un enfant : liste des responsables + révocation. */
export function ManageAccessDialog({
  open,
  onOpenChange,
  childId,
  childName,
}: ManageAccessDialogProps) {
  const [guardians, setGuardians] = useState<GuardianResponse[]>([]);
  const [loading, setLoading] = useState(false);

  const load = () => {
    setLoading(true);
    getGuardians(childId)
      .then(setGuardians)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (open) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, childId]);

  const revoke = async (guardianId: string) => {
    await removeGuardian(childId, guardianId);
    load();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-2xl">
        <DialogHeader>
          <DialogTitle>Accès de {childName}</DialogTitle>
          <DialogDescription>
            Les personnes qui peuvent suivre cet enfant.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <p className="py-4 text-center text-fun-text-muted">Chargement…</p>
        ) : (
          <ul className="divide-y divide-fun-border">
            {guardians.map((g) => (
              <li key={g.guardian_id} className="flex items-center gap-3 py-3">
                <UserAvatar
                  avatar={g.avatar_url}
                  name={g.name}
                  className="h-9 w-9"
                />
                <div className="min-w-0 flex-1">
                  <div className="truncate font-semibold text-fun-text">
                    {g.name}
                    {g.is_self && (
                      <span className="ml-1 text-xs text-fun-text-muted">
                        (vous)
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-fun-text-muted">
                    {ROLE_LABEL[g.role] ?? g.role}
                  </div>
                </div>
                {g.role !== "owner" && !g.is_self && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-fun-red"
                    onClick={() => revoke(g.guardian_id)}
                  >
                    Retirer
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  );
}
