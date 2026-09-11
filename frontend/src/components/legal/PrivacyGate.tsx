"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { isAxiosError } from "axios";
import { ShieldCheck } from "lucide-react";

import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  useAcceptPrivacyPolicyApiV1LegalPrivacyAcceptPost as useAcceptPrivacy,
  useGetPrivacyPolicyApiV1LegalPrivacyGet as usePrivacyPolicy,
} from "@/lib/api/generated/legal/legal";

/**
 * Case à cocher de la politique de confidentialité, présentée une fois par
 * version au premier passage de l'adulte responsable.
 *
 * L'authentification passe par Google : il n'existe pas d'écran d'inscription
 * où intercaler une case avant la création du compte. Le consentement est donc
 * recueilli ici, à la première visite qui suit — c'est le premier moment où on
 * peut réellement montrer le texte au parent.
 *
 * Un enfant ne consent à rien : la case ne lui est jamais montrée. Mais le mode
 * enfant est restauré depuis `localStorage` à chaque chargement, donc s'en
 * tenir là laisserait une famille restée en mode enfant enregistrer
 * indéfiniment le travail d'un enfant sans qu'aucun adulte n'ait jamais
 * consenti. Au chargement de l'application, un consentement manquant fait donc
 * sortir du mode enfant (voir l'effet ci-dessous) : le parent reprend l'écran,
 * et c'est lui qu'on interroge. Le choix du chargement — et pas d'un moment
 * quelconque — est ce qui évite de dresser un mur juridique devant un enfant au
 * milieu d'un exercice.
 */
export function PrivacyGate() {
  const { user, impersonatedChild, exitChildMode, refreshUser } = useAuth();
  const [checked, setChecked] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const alreadyAccepted = user?.privacy_accepted ?? true;
  const consentMissing = Boolean(user) && !alreadyAccepted;
  const shouldAsk = consentMissing && !impersonatedChild;

  // Sortie du mode enfant, une seule fois par chargement : sans le garde-fou,
  // un `exitChildMode` sans effet relancerait l'effet en boucle.
  const leftChildMode = useRef(false);
  useEffect(() => {
    if (!consentMissing || !impersonatedChild || leftChildMode.current) return;
    leftChildMode.current = true;
    exitChildMode();
  }, [consentMissing, impersonatedChild, exitChildMode]);

  const { data: policy, refetch: refetchPolicy } = usePrivacyPolicy({
    query: { enabled: shouldAsk },
  });

  const accept = useAcceptPrivacy<unknown>({
    mutation: {
      onSuccess: async () => {
        setError(null);
        await refreshUser();
      },
      onError: async (mutationError) => {
        // 409 : le texte a changé entre l'affichage et le clic. Ce n'est pas
        // une panne de réseau — il faut relire, pas réessayer. On recharge donc
        // le texte affiché et on décoche : la case doit porter sur ce que le
        // parent a effectivement sous les yeux.
        if (
          isAxiosError(mutationError) &&
          mutationError.response?.status === 409
        ) {
          setChecked(false);
          await refetchPolicy();
          setError(
            "La politique a changé pendant que cette fenêtre était ouverte. Rechargez la page pour lire la nouvelle version, puis acceptez-la."
          );
          return;
        }
        setError(
          "L'enregistrement a échoué. Vérifiez votre connexion et réessayez."
        );
      },
    },
  });

  if (!shouldAsk) return null;

  return (
    <Dialog open>
      <DialogContent
        // Ni croix, ni échappement, ni clic extérieur : la case doit être
        // cochée, pas écartée. `DialogContent` rend toujours un bouton de
        // fermeture en dernier enfant ; sans `onOpenChange` il ne ferait rien,
        // et un bouton visible qui n'agit pas est pire que pas de bouton.
        className="rounded-2xl max-w-lg [&>button]:hidden"
        onEscapeKeyDown={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-fun-text">
            <ShieldCheck className="h-5 w-5 text-fun-green" />
            Vos données, en clair
          </DialogTitle>
          <DialogDescription>
            Explorito enregistre le travail scolaire de vos enfants. Avant
            d&apos;aller plus loin, voici ce qui est collecté et comment tout
            effacer.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 text-sm text-fun-text">
          <ul className="space-y-2 list-disc pl-5 text-fun-text-muted">
            <li>
              <strong className="text-fun-text">
                Vos enfants n&apos;ont aucun compte
              </strong>{" "}
              : ni identifiant, ni mot de passe, ni email.
            </li>
            <li>
              Sur eux : un prénom d&apos;affichage, une date de naissance, un
              niveau scolaire, leur progression, et l&apos;avatar que vous leur
              choisissez éventuellement.
            </li>
            <li>
              Hébergement en France, aucune publicité, aucune revente de
              données.
            </li>
            <li>
              Supprimer un enfant efface immédiatement toute sa progression et
              son avatar.
            </li>
          </ul>

          <Link
            href="/confidentialite"
            target="_blank"
            className="inline-block underline text-fun-sky font-semibold"
          >
            Lire la politique complète
            {policy ? ` (version ${policy.version})` : ""}
          </Link>

          <label className="flex items-start gap-3 pt-2 cursor-pointer">
            <input
              type="checkbox"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
              className="mt-1 h-5 w-5 accent-fun-green"
            />
            <span>
              J&apos;ai lu la politique de confidentialité et j&apos;accepte que
              les données de ma famille soient traitées comme elle le décrit.
            </span>
          </label>

          {error && (
            <div className="bg-fun-red-light text-fun-red p-3 rounded-xl text-sm border border-fun-red/20">
              {error}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            className="w-full"
            disabled={!checked || !policy || accept.isPending}
            onClick={() => {
              if (!policy) return;
              accept.mutate({ data: { version: policy.version } });
            }}
          >
            {accept.isPending ? "Enregistrement…" : "J'accepte, continuer"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
