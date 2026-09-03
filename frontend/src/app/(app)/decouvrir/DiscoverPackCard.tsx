"use client";

import { BookOpen, Users } from "lucide-react";

import type { DiscoverPack } from "@/lib/api/model";

interface DiscoverPackCardProps {
  pack: DiscoverPack;
  /** Déjà demandé (par le serveur ou à l'instant) : le bouton se verrouille. */
  requested: boolean;
  /** Demande en cours d'envoi pour ce pack. */
  pending: boolean;
  /** Un seul effet festif : la carte que l'enfant vient de demander. */
  flourish: boolean;
  error?: string;
  onRequest: () => void;
}

export function DiscoverPackCard({
  pack,
  requested,
  pending,
  flourish,
  error,
  onRequest,
}: DiscoverPackCardProps) {
  const lessons = pack.lesson_count ?? 0;
  const families = pack.families_count ?? 0;
  const icons = pack.subject_icons ?? [];

  return (
    <div
      className={`flex flex-col rounded-2xl border-2 bg-white p-5 text-left candy-shadow transition-all ${
        requested ? "border-fun-sun" : "border-fun-sky hover:candy-shadow-lg"
      }`}
    >
      <div className="flex items-start gap-3">
        <span className="text-5xl leading-none" aria-hidden="true">
          {pack.emoji || "📦"}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-extrabold leading-tight text-fun-text">
            {pack.title}
          </h3>
          {pack.author_handle ? (
            <p className="mt-1 text-xs font-semibold text-fun-text-muted">
              par {pack.author_handle}
            </p>
          ) : null}
        </div>
      </div>

      {pack.description ? (
        <p className="mt-3 line-clamp-3 text-sm font-medium text-fun-text-muted">
          {pack.description}
        </p>
      ) : null}

      {icons.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {icons.map((icon, i) => (
            <span
              key={`${icon}-${i}`}
              className="rounded-full bg-fun-sky-light px-2 py-0.5 text-lg"
              aria-hidden="true"
            >
              {icon}
            </span>
          ))}
        </div>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="flex items-center gap-1 rounded-full bg-fun-violet-light px-2 py-0.5 text-xs font-bold text-fun-violet">
          <BookOpen className="h-3.5 w-3.5" />
          {lessons} {lessons > 1 ? "leçons" : "leçon"}
        </span>
        <span className="flex items-center gap-1 rounded-full bg-fun-green-light px-2 py-0.5 text-xs font-bold text-fun-green-dark">
          <Users className="h-3.5 w-3.5" />
          {families} {families > 1 ? "familles" : "famille"}
        </span>
      </div>

      <div className="mt-auto pt-4">
        <button
          type="button"
          onClick={onRequest}
          disabled={requested || pending}
          className={`min-h-[48px] w-full rounded-xl border-2 px-4 text-base font-extrabold transition-all ${
            requested
              ? "cursor-not-allowed border-fun-sun bg-fun-sun-light text-fun-text"
              : pending
                ? "cursor-wait border-fun-green-dark bg-fun-green-light text-fun-green-dark"
                : "border-fun-green-dark bg-fun-green text-white hover:bg-fun-green-dark active:scale-95"
          } ${flourish ? "animate-[candy-pop_0.6s_ease-out]" : ""}`}
        >
          {requested
            ? "Demandé ✓ — en attente d'un adulte"
            : pending
              ? "On envoie ta demande…"
              : "Je veux ça !"}
        </button>
        <p className="mt-2 text-center text-xs font-semibold text-fun-text-muted">
          {requested
            ? "Un adulte doit dire oui pour l'ouvrir."
            : "Ça ne l'ouvre pas tout de suite : un adulte décide."}
        </p>
        {error ? (
          <p className="mt-2 rounded-xl bg-fun-red-light px-3 py-2 text-center text-sm font-bold text-fun-red">
            {error}
          </p>
        ) : null}
      </div>
    </div>
  );
}
