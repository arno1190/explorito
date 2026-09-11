"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { useGetPrivacyPolicyApiV1LegalPrivacyGet as usePrivacyPolicy } from "@/lib/api/generated/legal/legal";

type PolicyBlock =
  | { kind: "heading"; text: string }
  | { kind: "paragraph"; lines: string[] };

/**
 * Découpe le texte servi par l'API en blocs affichables.
 *
 * Le texte est habillé à 80 colonnes côté serveur : juste pour un terminal,
 * faux pour un téléphone. Dans la colonne d'environ 343 px d'un écran de
 * 375 px, 70 des 90 lignes se replient une seconde fois, en plein milieu des
 * phrases. On recoud donc les retours à la ligne internes d'un paragraphe et on
 * laisse le navigateur replier à la largeur réelle.
 *
 * Exception : un bloc dont chaque ligne est une phrase complète — les mentions
 * légales, éditeur puis contact puis hébergeur — garde ses retours, qui portent
 * là du sens.
 */
function parsePolicy(text: string): PolicyBlock[] {
  return text
    .split(/\n\s*\n/)
    .map((block) =>
      block
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
    )
    .filter((lines) => lines.length > 0)
    .map<PolicyBlock>((lines) => {
      if (lines.length === 1 && /^\d+\.\s/.test(lines[0])) {
        return { kind: "heading", text: lines[0] };
      }
      const oneSentencePerLine =
        lines.length > 1 && lines.every((line) => line.endsWith("."));
      return {
        kind: "paragraph",
        lines: oneSentencePerLine ? lines : [lines.join(" ")],
      };
    });
}

/**
 * Politique de confidentialité, lisible **sans compte**.
 *
 * Hors des groupes `(app)` et `(auth)` : ces deux-là redirigent vers la
 * connexion, or une politique que l'on ne peut lire qu'après avoir livré ses
 * données ne remplit pas son office.
 *
 * Le texte vient de l'API et n'est pas recopié ici : c'est la seule façon de
 * garantir que le parent lit exactement la version dont l'acceptation est
 * horodatée en base.
 */
export default function ConfidentialitePage() {
  const { data, isLoading, isError } = usePrivacyPolicy();

  return (
    <div className="min-h-screen bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light">
      <header className="bg-white/80 backdrop-blur-sm border-b-2 border-fun-border sticky top-0 z-40">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <Link href="/" className="text-2xl font-extrabold text-fun-green">
            Explorito
          </Link>
          <Link href="/login">
            <Button variant="ghost">Connexion</Button>
          </Link>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 pb-20 md:pb-12 max-w-3xl">
        <h1 className="text-3xl md:text-4xl font-extrabold text-fun-text mb-2">
          Confidentialité
        </h1>
        <p className="text-fun-text-muted mb-6">
          Ce que Explorito enregistre sur votre famille, pourquoi, et comment
          tout effacer.
        </p>

        {isLoading && (
          <div className="flex justify-center py-16">
            <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-fun-green-light border-t-fun-green" />
          </div>
        )}

        {isError && (
          <div className="bg-fun-red-light text-fun-red p-4 rounded-2xl border border-fun-red/20">
            Le texte n&apos;a pas pu être chargé. Réessayez dans un instant, ou
            écrivez-nous pour en recevoir une copie.
          </div>
        )}

        {data && (
          <article className="bg-white rounded-2xl candy-shadow p-5 md:p-8">
            <p className="text-xs text-fun-text-muted mb-4">
              Version {data.version}
            </p>
            <div className="space-y-4 text-sm md:text-base leading-relaxed text-fun-text">
              {parsePolicy(data.text).map((block, i) =>
                block.kind === "heading" ? (
                  <h2
                    key={i}
                    className="text-base md:text-lg font-extrabold text-fun-text pt-2"
                  >
                    {block.text}
                  </h2>
                ) : (
                  <div key={i} className="space-y-1">
                    {block.lines.map((line, j) => (
                      <p key={j}>{line}</p>
                    ))}
                  </div>
                )
              )}
            </div>
          </article>
        )}
      </main>
    </div>
  );
}
