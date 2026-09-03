"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Flag,
  GitBranch,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { useGetQueueApiV1ModerationQueueGet as useQueue } from "@/lib/api/generated/moderation/moderation";
import { CommunityStatus } from "@/lib/api/model";
import { Button } from "@/components/ui/button";
import {
  frDate,
  levelRange,
  Pill,
  QualityScore,
} from "@/app/(app)/bibliotheque/_components/pack-ui";
import { ContributorsTab } from "./_components/ContributorsTab";
import { PackReviewDialog } from "./_components/PackReviewDialog";
import { ReportsTab } from "./_components/ReportsTab";

const TABS = [
  { value: "queue", label: "File de revue" },
  { value: "reports", label: "Signalements" },
  { value: "contributors", label: "Contributeurs" },
] as const;

const QUEUE_STATUSES = [
  { value: CommunityStatus.pending, label: "À relire" },
  { value: CommunityStatus.approved, label: "Approuvés" },
  { value: CommunityStatus.rejected, label: "Refusés" },
  { value: CommunityStatus.blocked, label: "Bloqués" },
  { value: CommunityStatus.draft, label: "Brouillons" },
] as const;

export default function ModerationPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const isAdmin = user?.role === "admin";

  const [tab, setTab] = useState<string>("queue");
  const [status, setStatus] = useState<CommunityStatus>(
    CommunityStatus.pending
  );
  const [reviewId, setReviewId] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAdmin) router.replace("/dashboard");
  }, [authLoading, isAdmin, router]);

  const { data: queue, isPending: queuePending } = useQueue(
    { status, limit: 200 },
    { query: { enabled: isAdmin } }
  );

  if (authLoading || !isAdmin) return null;

  const items = queue?.items ?? [];

  return (
    <div className="space-y-6">
      <div>
        <Button asChild variant="ghost" className="mb-2 -ml-3">
          <Link href="/admin">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Administration
          </Link>
        </Button>
        <h1 className="flex items-center gap-2 text-3xl font-extrabold text-fun-text">
          <ShieldCheck className="h-7 w-7 text-fun-green" />
          Modération
        </h1>
        <p className="mt-1 text-fun-text-muted">
          Relecture des packs communautaires, signalements des parents et
          paliers de confiance.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <Button
            key={t.value}
            variant={tab === t.value ? "default" : "outline"}
            onClick={() => setTab(t.value)}
          >
            {t.value === "reports" ? <Flag className="mr-2 h-4 w-4" /> : null}
            {t.value === "contributors" ? (
              <Users className="mr-2 h-4 w-4" />
            ) : null}
            {t.label}
          </Button>
        ))}
      </div>

      {tab === "queue" ? (
        <section className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {QUEUE_STATUSES.map((s) => (
              <Button
                key={s.value}
                variant={status === s.value ? "secondary" : "ghost"}
                onClick={() => setStatus(s.value)}
              >
                {s.label}
              </Button>
            ))}
            <span className="flex items-center px-2 text-sm font-bold text-fun-text-muted">
              {queue?.count ?? 0} pack{(queue?.count ?? 0) > 1 ? "s" : ""}
            </span>
          </div>

          {queuePending ? (
            <div className="flex justify-center py-12">
              <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
            </div>
          ) : items.length === 0 ? (
            <p className="rounded-2xl border-2 border-fun-border bg-white p-4 text-sm text-fun-text-muted">
              Rien dans cette file.
            </p>
          ) : (
            <ul className="space-y-2">
              {items.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => setReviewId(item.id)}
                    className={`w-full rounded-2xl border-2 bg-white p-4 text-left candy-shadow transition-all hover:candy-shadow-lg ${
                      (item.open_reports ?? 0) > 0
                        ? "border-fun-red"
                        : "border-fun-border"
                    }`}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="flex min-w-0 items-start gap-3">
                        <span className="text-3xl">{item.emoji ?? "📦"}</span>
                        <div className="min-w-0">
                          <p className="font-bold text-fun-text">
                            {item.title}
                          </p>
                          <p className="text-sm text-fun-text-muted">
                            @{item.author_handle ?? "auteur anonyme"} · soumis
                            le {frDate(item.submitted_at, true)}
                          </p>
                          {item.cloned_from_title ? (
                            <p className="mt-1 flex items-center gap-1 text-sm font-semibold text-fun-sky">
                              <GitBranch className="h-4 w-4 shrink-0" />
                              Révision de « {item.cloned_from_title} »
                            </p>
                          ) : null}
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Pill tone="sky">
                          {levelRange(item.level_min, item.level_max)}
                        </Pill>
                        <Pill tone="accent">
                          {item.lesson_count ?? 0} leçon
                          {(item.lesson_count ?? 0) > 1 ? "s" : ""} ·{" "}
                          {item.exercise_count ?? 0} exercice
                          {(item.exercise_count ?? 0) > 1 ? "s" : ""}
                        </Pill>
                        <QualityScore score={item.quality_score} />
                        {(item.warnings ?? []).length > 0 ? (
                          <Pill tone="violet">
                            <Sparkles className="mr-1 inline h-3 w-3" />
                            {item.warnings?.length} constat
                            {(item.warnings?.length ?? 0) > 1 ? "s" : ""}
                          </Pill>
                        ) : null}
                        {(item.open_reports ?? 0) > 0 ? (
                          <Pill tone="red">
                            <Flag className="mr-1 inline h-3 w-3" />
                            {item.open_reports} signalement
                            {(item.open_reports ?? 0) > 1 ? "s" : ""}
                          </Pill>
                        ) : null}
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : null}

      {tab === "reports" ? <ReportsTab onOpenPack={setReviewId} /> : null}
      {tab === "contributors" ? <ContributorsTab /> : null}

      <PackReviewDialog
        packId={reviewId}
        open={reviewId !== null}
        onOpenChange={(open) => !open && setReviewId(null)}
      />
    </div>
  );
}
