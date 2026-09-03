"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Flag } from "lucide-react";
import {
  useDecideReportApiV1ModerationReportsReportIdPatch as useDecideReport,
  useGetReportsApiV1ModerationReportsGet as useReports,
} from "@/lib/api/generated/moderation/moderation";
import { ReportStatus } from "@/lib/api/model";
import type { ReportRow } from "@/lib/api/model";
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
  frDate,
  Pill,
  REPORT_REASON_LABELS,
  Toggle,
} from "@/app/(app)/bibliotheque/_components/pack-ui";

const STATUS_FILTERS = [
  { value: ReportStatus.open, label: "Ouverts" },
  { value: ReportStatus.actioned, label: "Traités" },
  { value: ReportStatus.dismissed, label: "Écartés" },
] as const;

const STATUS_TONES: Record<string, "red" | "green" | "sky"> = {
  open: "red",
  actioned: "green",
  dismissed: "sky",
};

export function ReportsTab({
  onOpenPack,
}: {
  onOpenPack: (packId: string) => void;
}) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<ReportStatus>(ReportStatus.open);
  const [target, setTarget] = useState<ReportRow | null>(null);
  const [blockPack, setBlockPack] = useState(false);

  const { data: reports, isPending } = useReports({ status, limit: 200 });
  const decide = useDecideReport({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({
          predicate: (query) =>
            typeof query.queryKey[0] === "string" &&
            query.queryKey[0].startsWith("/api/v1/moderation"),
        });
        setTarget(null);
        setBlockPack(false);
      },
    },
  });

  const rows = reports ?? [];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map((f) => (
          <Button
            key={f.value}
            variant={status === f.value ? "default" : "outline"}
            onClick={() => setStatus(f.value)}
          >
            {f.label}
          </Button>
        ))}
      </div>

      {isPending ? (
        <div className="flex justify-center py-12">
          <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
        </div>
      ) : rows.length === 0 ? (
        <p className="rounded-2xl border-2 border-fun-border bg-white p-4 text-sm text-fun-text-muted">
          Aucun signalement dans cette catégorie.
        </p>
      ) : (
        <ul className="space-y-2">
          {rows.map((report) => (
            <li
              key={report.id}
              className="rounded-2xl border-2 border-fun-border bg-white p-4 text-left candy-shadow transition-all"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="flex items-center gap-2 font-bold text-fun-text">
                    <Flag className="h-4 w-4 shrink-0 text-fun-red" />
                    {report.pack_title}
                  </p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <Pill tone="red">
                      {REPORT_REASON_LABELS[report.reason] ?? report.reason}
                    </Pill>
                    <Pill tone={STATUS_TONES[report.status] ?? "sky"}>
                      {report.status}
                    </Pill>
                    <span className="text-xs text-fun-text-muted">
                      {frDate(report.created_at, true)}
                    </span>
                  </div>
                  {report.details ? (
                    <p className="mt-2 text-sm text-fun-text-muted">
                      {report.details}
                    </p>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="ghost"
                    onClick={() => onOpenPack(report.pack_id)}
                  >
                    Relire le pack
                  </Button>
                  {report.status === ReportStatus.open ? (
                    <>
                      <Button
                        variant="outline"
                        disabled={decide.isPending}
                        onClick={() =>
                          decide.mutate({
                            reportId: report.id,
                            data: {
                              status: ReportStatus.dismissed,
                              block_pack: false,
                            },
                          })
                        }
                      >
                        Écarter
                      </Button>
                      <Button
                        onClick={() => {
                          setBlockPack(false);
                          setTarget(report);
                        }}
                      >
                        Traiter
                      </Button>
                    </>
                  ) : null}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      <Dialog
        open={target !== null}
        onOpenChange={(open) => !open && setTarget(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Traiter le signalement</DialogTitle>
            <DialogDescription>
              « {target?.pack_title} » —{" "}
              {target
                ? (REPORT_REASON_LABELS[target.reason] ?? target.reason)
                : ""}
            </DialogDescription>
          </DialogHeader>

          <div className="flex min-h-12 items-start justify-between gap-3 rounded-2xl border-2 border-fun-red bg-white p-3">
            <span className="text-sm font-semibold text-fun-text">
              Bloquer aussi le pack
              <span className="block text-xs font-normal text-fun-text-muted">
                Bloquer masque le pack pour tout le monde, auteur inclus, et ne
                supprime rien : aucune progression n&apos;est perdue.
              </span>
            </span>
            <Toggle
              checked={blockPack}
              onChange={setBlockPack}
              label="Bloquer le pack signalé"
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setTarget(null)}>
              Annuler
            </Button>
            <Button
              variant={blockPack ? "destructive" : "default"}
              disabled={decide.isPending}
              onClick={() => {
                if (!target) return;
                decide.mutate({
                  reportId: target.id,
                  data: {
                    status: ReportStatus.actioned,
                    block_pack: blockPack,
                  },
                });
              }}
            >
              {blockPack ? "Traiter et bloquer" : "Marquer traité"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
