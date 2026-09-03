"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Ban, Check, GitBranch, History, X } from "lucide-react";
import {
  useGetPackApiV1ModerationPacksPackIdGet as useModerationPack,
  useReviewPackApiV1ModerationPacksPackIdPatch as useReviewPack,
} from "@/lib/api/generated/moderation/moderation";
import { CommunityStatus } from "@/lib/api/model";
import type { ModerationPackDetail } from "@/lib/api/model";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  frDate,
  levelRange,
  PackContent,
  Pill,
  QualityScore,
  readableValue,
  REPORT_REASON_LABELS,
  Toggle,
  ValidationIssues,
} from "@/app/(app)/bibliotheque/_components/pack-ui";

/**
 * Conséquence de chaque verdict, écrite dans l'interface : c'est la seule
 * façon pour l'admin de trancher sans avoir à connaître le modèle de données.
 */
const VERDICTS = [
  {
    value: CommunityStatus.approved,
    label: "Approuver",
    consequence:
      "Approuver ratifie la difficulté et verrouille le pack : il est listé au catalogue parent, et l'auteur ne peut plus le modifier (il devra le cloner).",
    box: "border-fun-green bg-fun-green-light text-fun-green-dark",
    icon: <Check className="h-5 w-5 shrink-0" />,
  },
  {
    value: CommunityStatus.rejected,
    label: "Refuser",
    consequence:
      "Refuser ne retire rien à la famille de l'auteur : elle garde le pack, sa progression et son XP. Seule la publication communautaire est refusée.",
    box: "border-fun-accent bg-fun-accent-light text-fun-accent-dark",
    icon: <X className="h-5 w-5 shrink-0" />,
  },
  {
    value: CommunityStatus.blocked,
    label: "Bloquer",
    consequence:
      "Bloquer masque le pack pour tout le monde, auteur inclus, et ne supprime rien : aucune ligne de progression n'est perdue. Réservé au contenu nuisible.",
    box: "border-fun-red bg-fun-red-light text-fun-red",
    icon: <Ban className="h-5 w-5 shrink-0" />,
  },
] as const;

/**
 * Panneau de verdict. Monté avec ``key={pack.id}`` : changer de pack remonte
 * le composant, ce qui remet l'état à zéro sans effet de synchronisation.
 */
function VerdictPanel({
  pack,
  onDone,
}: {
  pack: ModerationPackDetail;
  onDone: () => void;
}) {
  const queryClient = useQueryClient();
  const [verdict, setVerdict] = useState<string | null>(null);
  const [notes, setNotes] = useState(pack.review_notes ?? "");
  const [score, setScore] = useState(
    pack.quality_score === null || pack.quality_score === undefined
      ? ""
      : String(pack.quality_score)
  );
  const [ratify, setRatify] = useState(true);

  const review = useReviewPack({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({
          predicate: (query) =>
            typeof query.queryKey[0] === "string" &&
            query.queryKey[0].startsWith("/api/v1/moderation"),
        });
        onDone();
      },
    },
  });

  const submit = (withVerdict: boolean) => {
    const parsed = score.trim() === "" ? null : Number(score);
    review.mutate({
      packId: pack.id,
      data: {
        verdict: withVerdict ? (verdict as CommunityStatus) : null,
        notes: notes.trim() || null,
        quality_score:
          parsed === null || Number.isNaN(parsed) ? null : Math.round(parsed),
        ratify_difficulty:
          withVerdict && verdict === CommunityStatus.approved ? ratify : null,
      },
    });
  };

  return (
    <section className="space-y-3 rounded-2xl border-2 border-fun-border bg-fun-card p-4">
      <h3 className="text-base font-bold text-fun-text">Verdict</h3>
      <p className="text-sm text-fun-text-muted">
        L&apos;analyse peut être automatisée, la décision non : aucun verdict
        n&apos;est écrit tant que vous n&apos;en choisissez pas un.
      </p>
      <div className="space-y-2">
        {VERDICTS.map((v) => (
          <label
            key={v.value}
            className={`flex min-h-12 cursor-pointer items-start gap-3 rounded-2xl border-2 p-3 text-sm transition-all ${
              verdict === v.value ? v.box : "border-fun-border bg-white"
            }`}
          >
            <input
              type="radio"
              name="verdict"
              value={v.value}
              checked={verdict === v.value}
              onChange={() => setVerdict(v.value)}
              className="mt-1 h-4 w-4"
            />
            {v.icon}
            <span>
              <span className="block font-bold text-fun-text">{v.label}</span>
              <span className="block text-fun-text-muted">{v.consequence}</span>
            </span>
          </label>
        ))}
      </div>

      {verdict === CommunityStatus.approved ? (
        <div className="flex min-h-12 items-center justify-between gap-3 rounded-2xl border-2 border-fun-green bg-white p-3">
          <span className="text-sm font-semibold text-fun-text">
            Ratifier la difficulté annoncée
            <span className="block text-xs font-normal text-fun-text-muted">
              Les niveaux et paliers du pack sont considérés vérifiés.
            </span>
          </span>
          <Toggle
            checked={ratify}
            onChange={setRatify}
            label="Ratifier la difficulté"
          />
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="space-y-1 sm:col-span-1">
          <Label htmlFor="quality-score">Score de qualité (0-100)</Label>
          <Input
            id="quality-score"
            inputMode="numeric"
            value={score}
            onChange={(e) =>
              setScore(e.target.value.replace(/\D/g, "").slice(0, 3))
            }
            placeholder="—"
          />
        </div>
        <div className="space-y-1 sm:col-span-2">
          <Label htmlFor="review-notes">
            Notes de relecture (visibles par l&apos;auteur)
          </Label>
          <textarea
            id="review-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="w-full rounded-xl border-2 border-fun-border bg-white p-3 text-fun-text outline-none focus:border-fun-sky"
          />
        </div>
      </div>

      {review.isError ? (
        <p className="rounded-xl bg-fun-red-light p-3 text-sm font-semibold text-fun-red">
          Le verdict n&apos;a pas pu être enregistré. Réessayez.
        </p>
      ) : null}

      <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
        <Button
          variant="outline"
          disabled={review.isPending}
          onClick={() => submit(false)}
        >
          Enregistrer sans verdict
        </Button>
        <Button
          disabled={review.isPending || verdict === null}
          onClick={() => submit(true)}
        >
          Prononcer le verdict
        </Button>
      </div>
    </section>
  );
}

export function PackReviewDialog({
  packId,
  open,
  onOpenChange,
}: {
  packId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { data: pack, isPending } = useModerationPack(packId ?? "", {
    query: { enabled: open && !!packId },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] max-w-4xl overflow-y-auto">
        {isPending || !pack ? (
          <>
            <DialogHeader>
              <DialogTitle>Relecture</DialogTitle>
              <DialogDescription>Chargement du pack…</DialogDescription>
            </DialogHeader>
            <div className="flex justify-center py-12">
              <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
            </div>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-left">
                <span className="text-3xl">{pack.emoji ?? "📦"}</span>
                {pack.title}
              </DialogTitle>
              <DialogDescription className="text-left">
                {pack.description ?? "Pas de description."}
              </DialogDescription>
            </DialogHeader>

            <div className="flex flex-wrap items-center gap-2">
              <Pill tone="violet">
                @{pack.author_handle ?? "auteur anonyme"}
              </Pill>
              <Pill tone="sky">
                {levelRange(pack.level_min, pack.level_max)}
              </Pill>
              <Pill tone="accent">
                {pack.lesson_count ?? 0} leçon
                {(pack.lesson_count ?? 0) > 1 ? "s" : ""} ·{" "}
                {pack.exercise_count ?? 0} exercice
                {(pack.exercise_count ?? 0) > 1 ? "s" : ""}
              </Pill>
              <QualityScore score={pack.quality_score} />
              <Pill tone="green">{pack.community_status}</Pill>
              {pack.difficulty_ratified ? (
                <Pill tone="green">Difficulté ratifiée</Pill>
              ) : null}
              {pack.locked ? <Pill tone="sun">Verrouillé</Pill> : null}
              {(pack.open_reports ?? 0) > 0 ? (
                <Pill tone="red">
                  {pack.open_reports} signalement
                  {(pack.open_reports ?? 0) > 1 ? "s" : ""} ouvert
                  {(pack.open_reports ?? 0) > 1 ? "s" : ""}
                </Pill>
              ) : null}
              {pack.tags?.map((tag) => (
                <Pill key={tag} tone="violet">
                  #{tag}
                </Pill>
              ))}
            </div>

            {pack.cloned_from_title ? (
              <p className="flex items-center gap-2 rounded-2xl border-2 border-fun-sky bg-fun-sky-light p-3 text-sm font-semibold text-fun-sky">
                <GitBranch className="h-4 w-4 shrink-0" />
                Révision de « {pack.cloned_from_title} » — pas un doublon.
              </p>
            ) : null}

            {/* ---- Constats du validateur ---- */}
            <section className="space-y-2">
              <h3 className="text-base font-bold text-fun-text">
                Constats du validateur
              </h3>
              <ValidationIssues issues={pack.warnings} />
            </section>

            {/* ---- Signalements ---- */}
            {(pack.reports ?? []).length > 0 ? (
              <section className="space-y-2">
                <h3 className="text-base font-bold text-fun-text">
                  Signalements
                </h3>
                <ul className="space-y-2">
                  {(pack.reports ?? []).map((report) => (
                    <li
                      key={report.id}
                      className="rounded-2xl border-2 border-fun-red bg-fun-red-light p-3 text-sm text-fun-text"
                    >
                      <span className="font-bold text-fun-red">
                        {REPORT_REASON_LABELS[report.reason] ?? report.reason}
                      </span>{" "}
                      · {report.status} · {frDate(report.created_at, true)}
                      {report.details ? (
                        <span className="block text-fun-text-muted">
                          {report.details}
                        </span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {/* ---- Contenu intégral, bonnes réponses comprises ---- */}
            <section className="space-y-2">
              <h3 className="text-base font-bold text-fun-text">
                Contenu intégral (bonnes réponses affichées)
              </h3>
              <PackContent lessons={pack.lessons} showAnswers />
            </section>

            {/* ---- Journal d'audit ---- */}
            <section className="space-y-2">
              <h3 className="flex items-center gap-2 text-base font-bold text-fun-text">
                <History className="h-5 w-5 text-fun-text-muted" />
                Journal d&apos;audit
              </h3>
              {(pack.audit ?? []).length === 0 ? (
                <p className="text-sm text-fun-text-muted">
                  Aucune action enregistrée sur ce pack.
                </p>
              ) : (
                <ul className="space-y-1">
                  {(pack.audit ?? []).map((row, i) => (
                    <li
                      key={`${row.action}-${i}`}
                      className="rounded-xl border-2 border-fun-border bg-white p-2 text-sm text-fun-text"
                    >
                      <span className="font-bold">{row.action}</span> ·{" "}
                      {frDate(row.created_at, true)}
                      {row.actor_id ? ` · ${row.actor_id}` : ""}
                      {row.detail && Object.keys(row.detail).length > 0 ? (
                        <span className="block text-xs text-fun-text-muted">
                          {readableValue(row.detail)}
                        </span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* ---- Verdict ---- */}
            <VerdictPanel
              key={pack.id}
              pack={pack}
              onDone={() => onOpenChange(false)}
            />
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
