"use client";

import { useEffect, useState } from "react";
import { Check, Copy, Sparkles, Timer } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useStartPairingApiV1ContributionsPairingPost as useStartPairing } from "@/lib/api/generated/contributions/contributions";

import { parseApiFailure } from "../_lib/contrib";
import {
  formatCountdown,
  formatPairingCode,
  pairingSentence,
} from "../_lib/pairing";

/** Fin de validité calculée à la réception : insensible à l'heure du poste. */
interface PairingSession {
  code: string;
  expiresAt: number;
}

/**
 * Chemin principal pour brancher un assistant : le parent lit un code à voix
 * haute, l'assistant récupère le jeton lui-même. Aucun secret à recopier.
 */
export function PairingCard({ disabled = false }: { disabled?: boolean }) {
  const [session, setSession] = useState<PairingSession | null>(null);
  const [remaining, setRemaining] = useState(0);
  const [copied, setCopied] = useState<"code" | "phrase" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startPairing = useStartPairing({
    mutation: {
      onSuccess: (data) => {
        setError(null);
        setCopied(null);
        // Le compte à rebours est posé dans le même rendu que le code : sans
        // cela, la première image afficherait « expiré » (remaining encore à 0).
        setRemaining(data.expires_in_seconds);
        setSession({
          code: data.code,
          expiresAt: Date.now() + data.expires_in_seconds * 1000,
        });
      },
      onError: (failure: unknown) => setError(parseApiFailure(failure).message),
    },
  });

  useEffect(() => {
    if (!session) return;
    const tick = () =>
      setRemaining(
        Math.max(0, Math.round((session.expiresAt - Date.now()) / 1000))
      );
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [session]);

  const expired = session !== null && remaining <= 0;
  const start = () => {
    if (disabled) return;
    startPairing.mutate();
  };
  const copy = async (what: "code" | "phrase", value: string) => {
    await navigator.clipboard.writeText(value);
    setCopied(what);
  };

  return (
    <section className="rounded-2xl border-2 border-fun-green bg-white p-5 candy-shadow">
      <h2 className="flex items-center gap-2 text-xl font-extrabold text-fun-text">
        <Sparkles className="h-5 w-5 text-fun-green" />
        Connecter mon assistant
      </h2>
      <p className="mt-1 text-sm text-fun-text-muted">
        Affichez un code, lisez-le à voix haute à votre assistant IA&nbsp;: il
        se configure tout seul. Rien à installer, rien à recopier.
      </p>

      {(session === null || expired) && (
        <Button
          type="button"
          size="lg"
          className="mt-4 w-full sm:w-auto"
          onClick={start}
          disabled={disabled || startPairing.isPending}
        >
          {startPairing.isPending
            ? "Génération…"
            : session === null
              ? "Afficher mon code"
              : "Afficher un nouveau code"}
        </Button>
      )}

      {session !== null && expired && (
        <p className="mt-3 text-sm font-semibold text-fun-text">
          Ce code a expiré. Affichez-en un nouveau, il sera valable 15 minutes.
        </p>
      )}

      {session !== null && !expired && (
        <div className="mt-4 rounded-2xl border-2 border-fun-green-light bg-fun-green-light p-4">
          <p className="text-sm font-semibold text-fun-text">
            Dictez ce code à votre assistant&nbsp;:
          </p>
          <p className="mt-2 break-all font-display text-3xl font-extrabold tracking-[0.25em] text-fun-text sm:text-4xl">
            {formatPairingCode(session.code)}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => copy("code", formatPairingCode(session.code))}
              disabled={disabled}
            >
              {copied === "code" ? (
                <Check className="h-4 w-4 text-fun-green" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              {copied === "code" ? "Copié" : "Copier le code"}
            </Button>
            <span className="inline-flex items-center gap-2 text-sm font-bold text-fun-text">
              <Timer className="h-4 w-4 text-fun-accent" />
              Valable encore {formatCountdown(remaining)}
            </span>
          </div>

          <p className="mt-3 text-sm font-semibold text-fun-text">
            À dire à votre assistant&nbsp;:
          </p>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center">
            <p className="min-w-0 flex-1 rounded-xl border-2 border-fun-border bg-white p-3 text-sm text-fun-text">
              «&nbsp;{pairingSentence(session.code)}&nbsp;»
            </p>
            <Button
              type="button"
              variant="outline"
              onClick={() => copy("phrase", pairingSentence(session.code))}
              disabled={disabled}
            >
              {copied === "phrase" ? (
                <Check className="h-4 w-4 text-fun-green" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              {copied === "phrase" ? "Copié" : "Copier la phrase"}
            </Button>
          </div>
        </div>
      )}

      {error && (
        <p className="mt-3 rounded-xl border-2 border-fun-red bg-fun-red-light p-3 text-sm font-semibold text-fun-text">
          {error}
        </p>
      )}

      <p className="mt-3 text-xs text-fun-text-muted">
        Le code ne sert qu&apos;une fois et en afficher un nouveau annule le
        précédent. Votre assistant reçoit alors un jeton qui ne sait que{" "}
        <strong>créer un brouillon</strong>&nbsp;: il ne peut ni publier, ni
        supprimer, ni lire quoi que ce soit d&apos;autre — et vous pouvez le
        révoquer à tout moment dans la liste des jetons ci-dessous.
      </p>
    </section>
  );
}
