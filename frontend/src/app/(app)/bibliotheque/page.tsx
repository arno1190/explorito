"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { CheckCircle, Library, Sparkles, Users } from "lucide-react";
import { useGetChildrenApiV1ChildrenGet as useChildren } from "@/lib/api/generated/children/children";
import { useGetCatalogueApiV1LibraryCatalogueGet as useCatalogue } from "@/lib/api/generated/library/library";
import { useListSubjectsApiV1SubjectsGet as useSubjects } from "@/lib/api/generated/subjects/subjects";
import type { LevelEnum } from "@/lib/api/model";
import { Button } from "@/components/ui/button";
import { ContributorCard } from "./_components/ContributorCard";
import { ChildAutoEnableRow } from "./_components/ChildAccessControls";
import { PackCard } from "./_components/PackCard";
import { PackPreviewDialog } from "./_components/PackPreviewDialog";
import { RequestsPanel } from "./_components/RequestsPanel";
import { LEVEL_LABELS, LEVEL_VALUES } from "./_components/pack-ui";

const SORTS = [
  { value: "newest", label: "Plus récents" },
  { value: "most_enabled", label: "Les plus activés" },
] as const;

const SELECT_CLASS =
  "h-12 w-full rounded-xl border-2 border-fun-border bg-white px-3 font-semibold text-fun-text outline-none focus:border-fun-sky";

export default function BibliothequePage() {
  const [level, setLevel] = useState("");
  const [subject, setSubject] = useState("");
  const [tag, setTag] = useState("");
  const [sort, setSort] = useState<string>("newest");
  const [previewId, setPreviewId] = useState<string | null>(null);

  const { data: children } = useChildren();
  const { data: subjects } = useSubjects({ is_active: true, limit: 100 });
  const { data: catalogue, isPending: cataloguePending } = useCatalogue({
    level: (level || undefined) as LevelEnum | undefined,
    subject: subject || undefined,
    tag: tag || undefined,
    sort,
    limit: 100,
  });
  // Requête non filtrée : elle alimente « Nouveautés » et la liste des
  // étiquettes proposées au filtre (le catalogue filtré ne les contient plus).
  const { data: allPacks } = useCatalogue({ sort: "newest", limit: 100 });

  const childProfiles = useMemo(() => children ?? [], [children]);

  const tags = useMemo(() => {
    const seen = new Set<string>();
    for (const pack of allPacks ?? []) {
      for (const t of pack.tags ?? []) seen.add(t);
    }
    return [...seen].sort((a, b) => a.localeCompare(b, "fr"));
  }, [allPacks]);

  const newest = useMemo(
    () => (allPacks ?? []).filter((p) => p.origin === "community").slice(0, 6),
    [allPacks]
  );

  const official = (catalogue ?? []).filter((p) => p.origin === "official");
  const community = (catalogue ?? []).filter((p) => p.origin === "community");
  const filtered = !!level || !!subject || !!tag;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="flex items-center gap-2 text-3xl font-extrabold text-fun-text">
          <Library className="h-7 w-7 text-fun-green" />
          Bibliothèque
        </h1>
        <p className="mt-1 text-fun-text-muted">
          Le contenu officiel est déjà actif pour vos enfants. Les packs écrits
          par d&apos;autres parents n&apos;atteignent un enfant que si vous les
          activez.
        </p>
      </div>

      <ContributorCard />

      {/* ---- Demandes des enfants ---- */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-fun-text">
          Demandes des enfants
        </h2>
        <RequestsPanel onPreview={setPreviewId} />
      </section>

      {/* ---- Réglages par enfant ---- */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-fun-text">Réglages par enfant</h2>
        <p className="text-sm text-fun-text-muted">
          Activer l&apos;automatisation revient à faire confiance à la relecture
          : les packs approuvés du niveau de l&apos;enfant arriveront sans
          passer par vous.
        </p>
        {childProfiles.length === 0 ? (
          <p className="rounded-2xl border-2 border-fun-border bg-white p-4 text-sm text-fun-text-muted">
            Aucun enfant pour l&apos;instant.{" "}
            <Link
              href="/dashboard"
              className="font-bold text-fun-green underline"
            >
              Ajoutez un enfant
            </Link>{" "}
            pour activer des packs.
          </p>
        ) : (
          <div className="space-y-2">
            {childProfiles.map((child) => (
              <ChildAutoEnableRow key={child.id} child={child} />
            ))}
          </div>
        )}
      </section>

      {/* ---- Nouveautés de la communauté ---- */}
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-xl font-bold text-fun-text">
          <Sparkles className="h-5 w-5 text-fun-violet" />
          Nouveautés de la communauté
        </h2>
        {newest.length === 0 ? (
          <p className="rounded-2xl border-2 border-fun-border bg-white p-4 text-sm text-fun-text-muted">
            Aucun pack communautaire approuvé pour le moment.
          </p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {newest.map((pack) => (
              <PackCard
                key={`new-${pack.id}`}
                pack={pack}
                childProfiles={childProfiles}
                onOpen={setPreviewId}
              />
            ))}
          </div>
        )}
      </section>

      {/* ---- Catalogue filtrable ---- */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-fun-text">Tout le catalogue</h2>

        <div className="grid gap-3 rounded-2xl border-2 border-fun-border bg-white p-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="space-y-1">
            <span className="text-xs font-bold uppercase tracking-wide text-fun-text-muted">
              Niveau
            </span>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className={SELECT_CLASS}
            >
              <option value="">Tous les niveaux</option>
              {LEVEL_VALUES.map((value) => (
                <option key={value} value={value}>
                  {LEVEL_LABELS[value]}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-xs font-bold uppercase tracking-wide text-fun-text-muted">
              Matière
            </span>
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className={SELECT_CLASS}
            >
              <option value="">Toutes les matières</option>
              {(subjects ?? []).map((s) => (
                <option key={s.id} value={s.slug}>
                  {s.icon ? `${s.icon} ` : ""}
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-xs font-bold uppercase tracking-wide text-fun-text-muted">
              Thème
            </span>
            <select
              value={tag}
              onChange={(e) => setTag(e.target.value)}
              className={SELECT_CLASS}
            >
              <option value="">Tous les thèmes</option>
              {tags.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-xs font-bold uppercase tracking-wide text-fun-text-muted">
              Tri
            </span>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className={SELECT_CLASS}
            >
              {SORTS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
          {filtered ? (
            <Button
              variant="ghost"
              className="sm:col-span-2 lg:col-span-4"
              onClick={() => {
                setLevel("");
                setSubject("");
                setTag("");
              }}
            >
              Effacer les filtres
            </Button>
          ) : null}
        </div>

        {cataloguePending ? (
          <div className="flex justify-center py-12">
            <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
          </div>
        ) : (
          <div className="space-y-8">
            {/* Officiel : implicitement actif, donc jamais d'interrupteur. */}
            <div className="space-y-3">
              <h3 className="flex items-center gap-2 text-lg font-bold text-fun-text">
                <CheckCircle className="h-5 w-5 text-fun-green" />
                Contenu officiel Explorito
                <span className="rounded-full bg-fun-green-light px-2 py-0.5 text-xs font-bold text-fun-green-dark">
                  {official.length}
                </span>
              </h3>
              <p className="text-sm text-fun-text-muted">
                Déjà actif pour chaque enfant à son niveau : aucune action de
                votre part.
              </p>
              {official.length === 0 ? (
                <p className="rounded-2xl border-2 border-fun-border bg-white p-4 text-sm text-fun-text-muted">
                  Aucun pack officiel ne correspond à ces filtres.
                </p>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {official.map((pack) => (
                    <PackCard
                      key={pack.id}
                      pack={pack}
                      childProfiles={childProfiles}
                      onOpen={setPreviewId}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Communauté : n'atteint un enfant que par un interrupteur explicite. */}
            <div className="space-y-3">
              <h3 className="flex items-center gap-2 text-lg font-bold text-fun-text">
                <Users className="h-5 w-5 text-fun-sky" />
                Packs de la communauté
                <span className="rounded-full bg-fun-sky-light px-2 py-0.5 text-xs font-bold text-fun-sky">
                  {community.length}
                </span>
              </h3>
              <p className="text-sm text-fun-text-muted">
                Relus par un modérateur, puis activés par vous, enfant par
                enfant. Désactiver un pack le masque seulement : la progression
                est conservée.
              </p>
              {community.length === 0 ? (
                <p className="rounded-2xl border-2 border-fun-border bg-white p-4 text-sm text-fun-text-muted">
                  Aucun pack communautaire ne correspond à ces filtres.
                </p>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {community.map((pack) => (
                    <PackCard
                      key={pack.id}
                      pack={pack}
                      childProfiles={childProfiles}
                      onOpen={setPreviewId}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      <PackPreviewDialog
        packId={previewId}
        childProfiles={childProfiles}
        open={previewId !== null}
        onOpenChange={(open) => !open && setPreviewId(null)}
      />
    </div>
  );
}
