"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Check, Copy, KeyRound, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  getGetSignupInvitesApiV1AdminSignupInvitesGetQueryKey,
  useCreateSignupInviteApiV1AdminSignupInvitesPost as useCreateInvite,
  useGetSignupInvitesApiV1AdminSignupInvitesGet as useSignupInvites,
  useRevokeSignupInviteApiV1AdminSignupInvitesTokenDelete as useRevokeInvite,
} from "@/lib/api/generated/admin/admin";
import type { SignupInviteRow } from "@/lib/api/model";

function frDateTime(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** État lisible d'un code : ce que l'admin doit savoir d'un coup d'œil. */
function inviteState(invite: SignupInviteRow): {
  label: string;
  className: string;
} {
  if (invite.accepted_at)
    return {
      label: `Utilisé par ${invite.accepted_by_email ?? "un compte"}`,
      className: "bg-fun-green-light text-fun-green-dark",
    };
  if (invite.revoked_at)
    return {
      label: "Révoqué",
      className: "bg-fun-red-light text-fun-red",
    };
  if (!invite.is_usable)
    return {
      label: "Expiré",
      className: "bg-fun-sun-light text-fun-text-muted",
    };
  return {
    label: `Valable jusqu'au ${frDateTime(invite.expires_at)}`,
    className: "bg-fun-sky-light text-fun-sky",
  };
}

/**
 * Codes d'inscription (issue #22) : en créer un, copier le lien, révoquer.
 *
 * Un code = une famille. La liste garde les codes consommés, pour qu'on sache
 * qui est entré par quelle porte.
 */
export function SignupInvitesCard() {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState<string | null>(null);
  const { data: invites, isLoading } = useSignupInvites();

  const refresh = () =>
    queryClient.invalidateQueries({
      queryKey: getGetSignupInvitesApiV1AdminSignupInvitesGetQueryKey(),
    });

  const create = useCreateInvite({ mutation: { onSuccess: refresh } });
  const revoke = useRevokeInvite({ mutation: { onSuccess: refresh } });

  const copy = async (invite: SignupInviteRow) => {
    await navigator.clipboard.writeText(invite.url);
    setCopied(invite.token);
    window.setTimeout(() => setCopied(null), 2000);
  };

  const usable = (invites ?? []).filter((i) => i.is_usable);

  return (
    <Card className="candy-shadow">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <KeyRound className="h-5 w-5 text-fun-violet" />
          Codes d&apos;inscription
        </CardTitle>
        <CardDescription>
          Un code ouvre la création d&apos;un compte parent, une seule fois.
          Sans effet tant que <code>SIGNUP_INVITE_REQUIRED</code> reste
          désactivé.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm text-fun-text-muted">
            {usable.length} code{usable.length > 1 ? "s" : ""} encore valable
            {usable.length > 1 ? "s" : ""}
          </p>
          <Button
            onClick={() => create.mutate()}
            disabled={create.isPending}
            className="shrink-0"
          >
            {create.isPending ? "Création…" : "Créer un code"}
          </Button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-6">
            <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-8 w-8 border-4 border-fun-green-light border-t-fun-green" />
          </div>
        ) : (invites ?? []).length === 0 ? (
          <p className="text-sm text-fun-text-muted">
            Aucun code pour l&apos;instant.
          </p>
        ) : (
          <ul className="space-y-2">
            {(invites ?? []).map((invite) => {
              const state = inviteState(invite);
              return (
                <li
                  key={invite.token}
                  className="flex flex-col gap-2 rounded-xl border-2 border-fun-border p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p className="truncate font-mono text-sm text-fun-text">
                      {invite.token}
                    </p>
                    <span
                      className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${state.className}`}
                    >
                      {state.label}
                    </span>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copy(invite)}
                      disabled={!invite.is_usable}
                      title="Copier le lien d'invitation"
                    >
                      {copied === invite.token ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                      <span className="ml-1">Lien</span>
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => revoke.mutate({ token: invite.token })}
                      disabled={!invite.is_usable || revoke.isPending}
                      title="Révoquer ce code"
                    >
                      <Trash2 className="h-4 w-4 text-fun-red" />
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
