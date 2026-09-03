"use client";

import Link from "next/link";
import { GraduationCap, Library } from "lucide-react";

import { MyPackList } from "./_components/MyPackList";
import { TokenPanel } from "./_components/TokenPanel";
import { UploadPanel } from "./_components/UploadPanel";

/**
 * Espace de contribution du parent : ses packs, le dépôt d'un nouveau pack et
 * le jeton d'envoi de son assistant IA. Rien ici n'est visible d'un enfant.
 */
export default function ContributionsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light p-4 pb-20 md:pb-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <header className="rounded-2xl bg-white p-5 candy-shadow">
          <h1 className="text-2xl font-extrabold text-fun-text">
            Mes contributions
          </h1>
          <p className="mt-1 text-sm text-fun-text-muted">
            Écrivez des leçons avec votre assistant IA, relisez-les, puis
            partagez-les avec les autres familles si vous le souhaitez.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              href="/tutoriel/lecons-communautaires"
              className="inline-flex min-h-12 items-center gap-2 rounded-xl border-2 border-fun-sky bg-fun-sky-light px-4 font-semibold text-fun-text transition-transform active:scale-95"
            >
              <GraduationCap className="h-5 w-5 text-fun-sky" />
              Comment ça marche&nbsp;?
            </Link>
            <Link
              href="/bibliotheque"
              className="inline-flex min-h-12 items-center gap-2 rounded-xl border-2 border-fun-border bg-white px-4 font-semibold text-fun-text transition-transform active:scale-95"
            >
              <Library className="h-5 w-5 text-fun-violet" />
              Bibliothèque
            </Link>
          </div>
        </header>

        <section className="rounded-2xl bg-white p-5 candy-shadow">
          <h2 className="mb-4 text-xl font-extrabold text-fun-text">
            Mes packs
          </h2>
          <MyPackList />
        </section>

        <UploadPanel />
        <TokenPanel />
      </div>
    </div>
  );
}
