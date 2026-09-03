"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Copy, GitBranch, Lock, Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  getGetMyPackApiV1ContributionsPackIdGetQueryKey,
  getListMyPacksApiV1ContributionsGetQueryKey,
  useCloneMyPackApiV1ContributionsPackIdClonePost as useClonePack,
  useGetMyPackApiV1ContributionsPackIdGet as usePackDetail,
  useSubmitMyPackApiV1ContributionsPackIdSubmitPost as useSubmitPack,
} from "@/lib/api/generated/contributions/contributions";

import { IssueList } from "../_components/IssueList";
import { LessonCard } from "../_components/LessonCard";
import { PackHeaderCard } from "../_components/PackHeaderCard";
import { SubmitDialog } from "../_components/SubmitDialog";
import { packIssues, parseApiFailure, type ApiFailure } from "../_lib/contrib";

/**
 * Aperçu d'un pack du parent : l'arbre leçons/exercices tel que l'enfant le
 * verra, les constats du validateur ancrés sur l'élément fautif, la correction
 * en ligne, la soumission et le clonage.
 */
export default function ContributionPreviewPage() {
  const params = useParams<{ id: string }>();
  const packId = params.id;
  const router = useRouter();
  const queryClient = useQueryClient();

  const [submitOpen, setSubmitOpen] = useState(false);
  const [submitFailure, setSubmitFailure] = useState<ApiFailure | null>(null);
  const [cloneError, setCloneError] = useState<string | null>(null);

  const { data: pack, isLoading, isError } = usePackDetail(packId);

  const clone = useClonePack({
    mutation: {
      onSuccess: (created) => {
        queryClient.invalidateQueries({
          queryKey: getListMyPacksApiV1ContributionsGetQueryKey(),
        });
        router.push(`/contributions/${created.id}`);
      },
      onError: (error: unknown) =>
        setCloneError(parseApiFailure(error).message),
    },
  });

  const submit = useSubmitPack({
    mutation: {
      onSuccess: (updated) => {
        setSubmitOpen(false);
        setSubmitFailure(null);
        queryClient.setQueryData(
          getGetMyPackApiV1ContributionsPackIdGetQueryKey(packId),
          updated
        );
        queryClient.invalidateQueries({
          queryKey: getListMyPacksApiV1ContributionsGetQueryKey(),
        });
      },
      onError: (error: unknown) => setSubmitFailure(parseApiFailure(error)),
    },
  });

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-fun-surface">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  if (isError || !pack) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light p-4">
        <div className="mx-auto max-w-3xl rounded-2xl bg-white p-5 candy-shadow">
          <p className="font-extrabold text-fun-text">Pack introuvable</p>
          <p className="mt-1 text-sm text-fun-text-muted">
            Ce pack n&apos;existe plus, ou il n&apos;a pas été écrit par votre
            compte.
          </p>
          <Link
            href="/contributions"
            className="mt-4 inline-flex min-h-12 items-center gap-2 rounded-xl border-2 border-fun-border bg-white px-4 font-semibold text-fun-text"
          >
            <ArrowLeft className="h-5 w-5" />
            Mes contributions
          </Link>
        </div>
      </div>
    );
  }

  const editable = !pack.locked;
  const isDraft = pack.community_status === "draft";
  const warnings = pack.warnings ?? [];
  const lessons = pack.lessons ?? [];
  const startClone = () => clone.mutate({ packId });

  return (
    <div className="min-h-screen bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light p-4 pb-20 md:pb-6">
      <div className="mx-auto max-w-3xl space-y-4">
        <Link
          href="/contributions"
          className="inline-flex min-h-12 items-center gap-2 rounded-xl border-2 border-fun-border bg-white px-4 font-semibold text-fun-text transition-transform active:scale-95"
        >
          <ArrowLeft className="h-5 w-5" />
          Mes contributions
        </Link>

        <PackHeaderCard
          pack={pack}
          editable={editable}
          onClone={startClone}
          cloning={clone.isPending}
        />

        {pack.locked && (
          <section className="rounded-2xl border-2 border-fun-violet bg-fun-violet-light p-4">
            <p className="flex items-center gap-2 font-extrabold text-fun-text">
              <Lock className="h-5 w-5 text-fun-violet" />
              Pack verrouillé
            </p>
            <p className="mt-1 text-sm text-fun-text">
              Il est approuvé et d&apos;autres familles l&apos;utilisent : plus
              personne ne peut le modifier sans nouvelle relecture, vous
              compris. C&apos;est ce qui garantit qu&apos;un pack validé reste
              celui qu&apos;on a validé. Clonez-le pour proposer une révision :
              le clone repart en brouillon et l&apos;original garde la
              progression déjà acquise.
            </p>
          </section>
        )}

        {pack.cloned_from_pack_id && (
          <section className="rounded-2xl border-2 border-fun-border bg-white p-4 candy-shadow">
            <p className="flex flex-wrap items-center gap-2 text-sm text-fun-text">
              <GitBranch className="h-5 w-5 text-fun-sky" />
              Révision d&apos;un pack existant.
              <Link
                href={`/contributions/${pack.cloned_from_pack_id}`}
                className="font-bold text-fun-sky underline"
              >
                Voir l&apos;original
              </Link>
            </p>
          </section>
        )}

        {pack.review_notes && (
          <section className="rounded-2xl border-2 border-fun-accent bg-fun-accent-light p-4">
            <p className="font-extrabold text-fun-text">
              Retour de la relecture
            </p>
            <p className="mt-1 text-sm text-fun-text">{pack.review_notes}</p>
          </section>
        )}

        <section className="rounded-2xl bg-white p-4 candy-shadow">
          <div className="flex flex-wrap gap-2">
            {isDraft && (
              <Button
                onClick={() => {
                  setSubmitFailure(null);
                  setSubmitOpen(true);
                }}
              >
                <Send className="h-4 w-4" />
                Soumettre
              </Button>
            )}
            <Button
              variant="outline"
              onClick={startClone}
              disabled={clone.isPending}
            >
              <Copy className="h-4 w-4" />
              {clone.isPending ? "Clonage…" : "Cloner pour réviser"}
            </Button>
          </div>
          <p className="mt-2 text-sm text-fun-text-muted">
            {isDraft
              ? "Relisez chaque exercice ci-dessous, corrigez ce qui doit l'être, puis soumettez."
              : "Ce pack n'est plus un brouillon : pour le faire évoluer, clonez-le et soumettez le clone."}
          </p>
          {cloneError && (
            <p className="mt-2 rounded-xl border-2 border-fun-red bg-fun-red-light p-3 text-sm font-semibold text-fun-text">
              {cloneError}
            </p>
          )}
        </section>

        <IssueList issues={packIssues(warnings)} />

        {lessons.map((lesson, index) => (
          <LessonCard
            key={lesson.id ?? index}
            packId={packId}
            lesson={lesson}
            index={index}
            issues={warnings}
            editable={editable}
            onClone={startClone}
            cloning={clone.isPending}
          />
        ))}

        {lessons.length === 0 && (
          <p className="rounded-2xl bg-white p-4 text-sm text-fun-text-muted candy-shadow">
            Ce pack ne contient aucune leçon.
          </p>
        )}
      </div>

      <SubmitDialog
        open={submitOpen}
        onOpenChange={(open) => {
          setSubmitOpen(open);
          if (!open) setSubmitFailure(null);
        }}
        pending={submit.isPending}
        failure={submitFailure}
        onConfirm={() => submit.mutate({ packId })}
      />
    </div>
  );
}
