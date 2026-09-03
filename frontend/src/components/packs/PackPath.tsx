"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";

import {
  getChildPackPathApiV1PacksPathGetQueryKey,
  useChildPackPathApiV1PacksPathGet as usePackPath,
  useUpdatePackLensApiV1PacksLensPut as useUpdatePackLens,
} from "@/lib/api/generated/packs/packs";
import type { PackPathLesson } from "@/lib/api/model";

import { ContinuerCard } from "./ContinuerCard";
import { LensToggle, type PackLens } from "./LensToggle";
import { PackCard } from "./PackCard";
import { SubjectSection } from "./SubjectSection";

interface SubjectGroup {
  slug: string;
  name: string;
  icon?: string | null;
  lessons: PackPathLesson[];
}

export function PackPath() {
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = usePackPath();

  // Bascule optimiste : la lentille choisie s'applique tout de suite, la
  // persistance (profil de l'enfant, côté serveur) suit.
  const [pendingLens, setPendingLens] = useState<PackLens | null>(null);
  const updateLens = useUpdatePackLens({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getChildPackPathApiV1PacksPathGetQueryKey(),
        });
        setPendingLens(null);
      },
      onError: () => setPendingLens(null),
    },
  });

  const entries = data?.entries ?? [];
  const lens: PackLens = pendingLens ?? data?.lens ?? "themes";

  const subjectGroups = useMemo<SubjectGroup[]>(() => {
    // Une seule charge utile, deux lectures : la lentille Matières régroupe les
    // mêmes leçons par matière, sans requête supplémentaire.
    const groups: SubjectGroup[] = [];
    const indexBySlug = new Map<string, number>();
    for (const entry of entries) {
      for (const lesson of entry.lessons ?? []) {
        const at = indexBySlug.get(lesson.subject_slug);
        if (at === undefined) {
          indexBySlug.set(lesson.subject_slug, groups.length);
          groups.push({
            slug: lesson.subject_slug,
            name: lesson.subject_name ?? lesson.subject_slug,
            icon: lesson.subject_icon,
            lessons: [lesson],
          });
        } else {
          groups[at].lessons.push(lesson);
        }
      }
    }
    return groups;
  }, [entries]);

  if (isLoading) {
    return (
      <div className="flex min-h-[200px] items-center justify-center">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-3xl bg-white p-6 text-center candy-shadow">
        <div className="mb-2 text-4xl">🦊</div>
        <p className="font-bold text-fun-text">
          Ton chemin n&apos;a pas pu être chargé.
        </p>
        <p className="mt-1 text-sm font-semibold text-fun-text-muted">
          Réessaie dans un instant.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ContinuerCard continuer={data?.continuer} />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-2xl font-bold text-fun-text">🗺️ Ton chemin</h2>
        <LensToggle
          value={lens}
          disabled={updateLens.isPending}
          onChange={(next) => {
            setPendingLens(next);
            updateLens.mutate({ data: { lens: next } });
          }}
        />
      </div>

      {entries.length === 0 ? (
        <div className="rounded-3xl bg-white p-6 text-center candy-shadow">
          <div className="mb-2 text-5xl">🎒</div>
          <p className="text-xl font-extrabold text-fun-text">
            Aucun thème activé pour l&apos;instant
          </p>
          <p className="mt-1 text-sm font-semibold text-fun-text-muted">
            Demande à un parent d&apos;en ajouter, ou va en chercher.
          </p>
        </div>
      ) : lens === "themes" ? (
        <div className="space-y-4">
          {entries.map((entry) => (
            <PackCard key={entry.pack.id} entry={entry} />
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {subjectGroups.map((group) => (
            <SubjectSection
              key={group.slug}
              name={group.name}
              icon={group.icon}
              lessons={group.lessons}
            />
          ))}
        </div>
      )}

      <Link
        href="/decouvrir"
        className="flex min-h-[48px] items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-fun-border bg-white/60 px-4 text-sm font-bold text-fun-text-muted transition-all hover:border-fun-sky hover:text-fun-sky active:scale-95"
      >
        🔍 Découvrir d&apos;autres thèmes
      </Link>
    </div>
  );
}
