"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Check, Copy, KeyRound, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { frDate } from "@/components/packs/utils";
import {
  getListTokensApiV1ContributionsTokensGetQueryKey,
  useCreateTokenApiV1ContributionsTokensPost as useCreateToken,
  useListTokensApiV1ContributionsTokensGet as useTokens,
  useRevokeAllTokensApiV1ContributionsTokensDelete as useRevokeAll,
  useRevokeTokenApiV1ContributionsTokensTokenIdDelete as useRevokeToken,
} from "@/lib/api/generated/contributions/contributions";

import { parseApiFailure } from "../_lib/contrib";

/**
 * Jetons d'envoi : un identifiant long terme qui ne sait que **déposer un
 * brouillon**. Le secret n'existe côté serveur que haché, il n'est donc lisible
 * qu'à l'émission — d'où l'encadré unique.
 */
export function TokenPanel({ disabled = false }: { disabled?: boolean }) {
  const queryClient = useQueryClient();
  const tokensQuery = useTokens();
  const [label, setLabel] = useState("");
  const [secret, setSecret] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const invalidate = () =>
    queryClient.invalidateQueries({
      queryKey: getListTokensApiV1ContributionsTokensGetQueryKey(),
    });

  const createToken = useCreateToken({
    mutation: {
      onSuccess: (created) => {
        setSecret(created.token);
        setCopied(false);
        setLabel("");
        setError(null);
        invalidate();
      },
      onError: (err: unknown) => setError(parseApiFailure(err).message),
    },
  });

  const revokeToken = useRevokeToken({
    mutation: {
      onSuccess: () => invalidate(),
      onError: (err: unknown) => setError(parseApiFailure(err).message),
    },
  });

  const revokeAll = useRevokeAll({
    mutation: {
      onSuccess: () => {
        setSecret(null);
        invalidate();
      },
      onError: (err: unknown) => setError(parseApiFailure(err).message),
    },
  });

  const tokens = tokensQuery.data ?? [];
  const activeCount = tokens.filter((token) => token.active).length;

  return (
    <section className="rounded-2xl bg-white p-5 candy-shadow">
      <h2 className="flex items-center gap-2 text-xl font-extrabold text-fun-text">
        <KeyRound className="h-5 w-5 text-fun-sun" />
        Jeton d&apos;envoi
      </h2>
      <p className="mt-1 text-sm text-fun-text-muted">
        Donnez ce jeton à votre assistant IA pour qu&apos;il dépose ses packs
        sans vous. Il ne sait faire qu&apos;<strong>une</strong> chose : créer
        un brouillon. Il ne peut ni soumettre, ni publier, ni modifier, ni lire
        quoi que ce soit de votre compte. En cas de doute, révoquez-le :
        c&apos;est immédiat.
      </p>

      {secret && (
        <div className="mt-4 rounded-2xl border-2 border-fun-sun bg-fun-sun-light p-4">
          <p className="font-extrabold text-fun-text">
            Copiez-le maintenant : vous ne le reverrez plus.
          </p>
          <p className="mt-1 text-sm text-fun-text">
            Nous n&apos;en gardons qu&apos;une empreinte, impossible de le
            réafficher. Si vous le perdez, révoquez-le et créez-en un autre.
          </p>
          <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
            <code className="min-w-0 flex-1 break-all rounded-xl border-2 border-fun-border bg-white p-3 font-mono text-sm text-fun-text">
              {secret}
            </code>
            <Button
              type="button"
              variant="outline"
              onClick={async () => {
                await navigator.clipboard.writeText(secret);
                setCopied(true);
              }}
            >
              {copied ? (
                <Check className="h-4 w-4 text-fun-green" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              {copied ? "Copié" : "Copier"}
            </Button>
          </div>
        </div>
      )}

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="flex-1 space-y-2">
          <Label htmlFor="token-label" className="text-fun-text">
            Nom du jeton (facultatif)
          </Label>
          <Input
            id="token-label"
            value={label}
            onChange={(event) => setLabel(event.target.value)}
            placeholder="Mon assistant sur le portable"
            maxLength={60}
          />
        </div>
        <Button
          type="button"
          onClick={() => {
            if (disabled) return;
            createToken.mutate({ data: { label: label.trim() || null } });
          }}
          disabled={disabled || createToken.isPending}
        >
          {createToken.isPending ? "Création…" : "Créer un jeton"}
        </Button>
      </div>

      {error && (
        <p className="mt-3 rounded-xl border-2 border-fun-red bg-fun-red-light p-3 text-sm font-semibold text-fun-text">
          {error}
        </p>
      )}

      <div className="mt-4 space-y-2">
        {tokensQuery.isLoading && (
          <p className="text-sm text-fun-text-muted">Chargement des jetons…</p>
        )}
        {!tokensQuery.isLoading && tokens.length === 0 && (
          <p className="text-sm text-fun-text-muted">
            Aucun jeton pour le moment.
          </p>
        )}
        {tokens.map((token) => (
          <div
            key={token.id}
            className={cn(
              "flex flex-wrap items-center gap-3 rounded-2xl border-2 bg-white p-4 candy-shadow",
              token.active
                ? "border-fun-border"
                : "border-fun-border opacity-60"
            )}
          >
            <div className="min-w-0 flex-1">
              <p className="font-bold text-fun-text">
                <span className="font-mono">{token.prefix}…</span>
                {token.label && (
                  <span className="ml-2 font-normal text-fun-text-muted">
                    {token.label}
                  </span>
                )}
              </p>
              <p className="text-xs text-fun-text-muted">
                Créé le {frDate(token.created_at)} · Dernier envoi&nbsp;:{" "}
                {token.last_used_at ? frDate(token.last_used_at) : "jamais"}
                {!token.active && " · Révoqué"}
              </p>
            </div>
            {token.active && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  if (disabled) return;
                  revokeToken.mutate({ tokenId: token.id });
                }}
                disabled={disabled || revokeToken.isPending}
              >
                <Trash2 className="h-4 w-4" />
                Révoquer
              </Button>
            )}
          </div>
        ))}
      </div>

      {activeCount > 1 && (
        <Button
          type="button"
          variant="destructive"
          className="mt-3"
          onClick={() => {
            if (disabled) return;
            if (
              confirm(
                "Révoquer tous les jetons actifs ? Votre assistant ne pourra plus rien déposer avant que vous en créiez un nouveau."
              )
            ) {
              revokeAll.mutate();
            }
          }}
          disabled={disabled || revokeAll.isPending}
        >
          <Trash2 className="h-4 w-4" />
          Tout révoquer
        </Button>
      )}
    </section>
  );
}
