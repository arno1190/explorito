"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { AxiosError } from "axios";
import { useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Eye,
  Mail,
  Send,
  TestTube,
  Trash2,
  Users,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import {
  useCreateAnnouncementApiV1AnnouncementsPost as useCreateAnnouncement,
  useDeleteAnnouncementApiV1AnnouncementsAnnouncementIdDelete as useDeleteAnnouncement,
  useListAnnouncementsApiV1AnnouncementsGet as useAnnouncements,
  usePreviewAnnouncementApiV1AnnouncementsAnnouncementIdPreviewGet as useAnnouncementPreview,
  useSendApiV1AnnouncementsAnnouncementIdSendPost as useSendAnnouncement,
} from "@/lib/api/generated/announcements/announcements";
import type { AnnouncementSendResult } from "@/lib/api/model";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { frDate, Pill } from "@/app/(app)/bibliotheque/_components/pack-ui";

const STATUS_LABELS: Record<string, string> = {
  draft: "Brouillon",
  sending: "Envoi en cours",
  sent: "Envoyée",
  failed: "Échec partiel",
};

const STATUS_TONES: Record<string, "sky" | "sun" | "green" | "red"> = {
  draft: "sky",
  sending: "sun",
  sent: "green",
  failed: "red",
};

const DELIVERY_LABELS: Record<string, string> = {
  pending: "en attente",
  sent: "envoyés",
  failed: "échecs",
  skipped: "ignorés",
};

export default function AnnoncesPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const isAdmin = user?.role === "admin";
  const queryClient = useQueryClient();

  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [sendResult, setSendResult] = useState<AnnouncementSendResult | null>(
    null
  );
  const [smtpMissing, setSmtpMissing] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAdmin) router.replace("/dashboard");
  }, [authLoading, isAdmin, router]);

  const { data: announcements, isPending } = useAnnouncements({
    query: { enabled: isAdmin },
  });
  const { data: preview, isPending: previewPending } = useAnnouncementPreview(
    selectedId ?? "",
    { query: { enabled: !!selectedId } }
  );

  const invalidate = () =>
    queryClient.invalidateQueries({
      predicate: (query) =>
        typeof query.queryKey[0] === "string" &&
        query.queryKey[0].startsWith("/api/v1/announcements"),
    });

  const create = useCreateAnnouncement({
    mutation: {
      onSuccess: (created) => {
        setSubject("");
        setBody("");
        setSelectedId(created.id);
        invalidate();
      },
    },
  });

  const send = useSendAnnouncement<AxiosError<{ detail?: string }>>({
    mutation: {
      onSuccess: (result) => {
        setSendResult(result);
        setSmtpMissing(false);
        setSendError(null);
        setConfirming(false);
        invalidate();
      },
      onError: (err) => {
        setConfirming(false);
        setSendResult(null);
        if (err.response?.status === 503) {
          setSmtpMissing(true);
          setSendError(null);
          return;
        }
        setSmtpMissing(false);
        setSendError("L'envoi a échoué. Consultez les logs du backend.");
      },
    },
  });

  const remove = useDeleteAnnouncement({
    mutation: {
      onSuccess: () => {
        setSelectedId(null);
        invalidate();
      },
    },
  });

  if (authLoading || !isAdmin) return null;

  const rows = announcements ?? [];
  const selected = rows.find((a) => a.id === selectedId) ?? null;
  const recipientCount = preview?.recipient_count ?? 0;

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
          <Mail className="h-7 w-7 text-fun-green" />
          Annonces
        </h1>
        <p className="mt-1 text-fun-text-muted">
          Emails produit envoyés aux parents inscrits. Un envoi réel part
          immédiatement et ne peut pas être annulé.
        </p>
      </div>

      {/* ---- Rédaction d'un brouillon ---- */}
      <section className="space-y-3 rounded-2xl border-2 border-fun-border bg-white p-4 candy-shadow">
        <h2 className="text-xl font-bold text-fun-text">Nouveau brouillon</h2>
        <div className="space-y-2">
          <Label htmlFor="announcement-subject">Objet</Label>
          <Input
            id="announcement-subject"
            value={subject}
            maxLength={200}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Ce qui est nouveau dans Explorito"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="announcement-body">Corps (Markdown)</Label>
          <textarea
            id="announcement-body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={10}
            placeholder={"## Bonjour !\n\nCe mois-ci…"}
            className="w-full rounded-xl border-2 border-fun-border bg-white p-3 font-mono text-sm text-fun-text outline-none focus:border-fun-sky"
          />
        </div>
        {create.isError ? (
          <p className="rounded-xl bg-fun-red-light p-3 text-sm font-semibold text-fun-red">
            Le brouillon n&apos;a pas pu être créé. Objet et corps sont
            obligatoires.
          </p>
        ) : null}
        <Button
          disabled={
            create.isPending || subject.trim() === "" || body.trim() === ""
          }
          onClick={() =>
            create.mutate({
              data: { subject: subject.trim(), body_markdown: body },
            })
          }
        >
          Créer le brouillon
        </Button>
      </section>

      {/* ---- Liste ---- */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-fun-text">Annonces</h2>
        {isPending ? (
          <div className="flex justify-center py-12">
            <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
          </div>
        ) : rows.length === 0 ? (
          <p className="rounded-2xl border-2 border-fun-border bg-white p-4 text-sm text-fun-text-muted">
            Aucune annonce pour le moment.
          </p>
        ) : (
          <ul className="space-y-2">
            {rows.map((row) => (
              <li key={row.id}>
                <button
                  type="button"
                  onClick={() =>
                    setSelectedId(selectedId === row.id ? null : row.id)
                  }
                  className={`w-full rounded-2xl border-2 bg-white p-4 text-left candy-shadow transition-all ${
                    selectedId === row.id
                      ? "border-fun-green"
                      : "border-fun-border"
                  }`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-bold text-fun-text">{row.subject}</p>
                      <p className="text-xs text-fun-text-muted">
                        de {row.from_email} · créée le {frDate(row.created_at)}
                        {row.sent_at
                          ? ` · envoyée le ${frDate(row.sent_at, true)}`
                          : ""}
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Pill tone={STATUS_TONES[row.status] ?? "sky"}>
                        {STATUS_LABELS[row.status] ?? row.status}
                      </Pill>
                      {Object.entries(row.delivery_counts ?? {}).map(
                        ([key, value]) => (
                          <Pill key={key} tone="violet">
                            {value} {DELIVERY_LABELS[key] ?? key}
                          </Pill>
                        )
                      )}
                    </div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* ---- Aperçu et envoi ---- */}
      {selected ? (
        <section className="space-y-3 rounded-2xl border-2 border-fun-green bg-white p-4 candy-shadow">
          <h2 className="flex items-center gap-2 text-xl font-bold text-fun-text">
            <Eye className="h-5 w-5 text-fun-green" />
            Aperçu — {selected.subject}
          </h2>

          {previewPending || !preview ? (
            <div className="flex justify-center py-8">
              <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
            </div>
          ) : (
            <>
              <p className="flex items-center gap-2 text-sm font-semibold text-fun-text">
                <Users className="h-4 w-4 text-fun-sky" />
                {preview.recipient_count} destinataire
                {preview.recipient_count > 1 ? "s" : ""} (parents inscrits, non
                désinscrits).
              </p>
              {/* L'aperçu est l'email tel qu'il partira : on l'affiche brut,
                  dans une boîte, pour éviter toute confusion avec l'app. */}
              <div
                className="overflow-x-auto rounded-2xl border-2 border-fun-border bg-fun-surface p-4"
                dangerouslySetInnerHTML={{ __html: preview.html }}
              />
            </>
          )}

          {smtpMissing ? (
            <div className="rounded-2xl border-2 border-fun-red bg-fun-red-light p-4 text-sm text-fun-red">
              <p className="font-bold">SMTP non configuré</p>
              <p>
                Aucun email ne peut partir tant que les réglages{" "}
                <code className="font-mono font-bold">SMTP_HOST</code>,{" "}
                <code className="font-mono font-bold">SMTP_USER</code> et{" "}
                <code className="font-mono font-bold">MAIL_FROM</code> ne sont
                pas renseignés côté backend. Rien n&apos;a été envoyé.
              </p>
            </div>
          ) : null}

          {sendError ? (
            <p className="rounded-xl bg-fun-red-light p-3 text-sm font-semibold text-fun-red">
              {sendError}
            </p>
          ) : null}

          {sendResult ? (
            <p className="rounded-2xl border-2 border-fun-green bg-fun-green-light p-3 text-sm font-semibold text-fun-green-dark">
              {sendResult.dry_run
                ? "Test terminé : aucun email n'est parti."
                : "Envoi terminé."}{" "}
              {Object.entries(sendResult.counts)
                .map(
                  ([key, value]) => `${value} ${DELIVERY_LABELS[key] ?? key}`
                )
                .join(" · ")}
            </p>
          ) : null}

          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              disabled={send.isPending}
              onClick={() => {
                setSendResult(null);
                send.mutate({
                  announcementId: selected.id,
                  params: { dry_run: true },
                });
              }}
            >
              <TestTube className="mr-2 h-4 w-4" />
              Test (dry-run)
            </Button>
            {/* La confirmation doit pouvoir nommer un nombre réel de
                destinataires : on attend l'aperçu avant d'ouvrir la porte. */}
            <Button
              disabled={
                send.isPending ||
                selected.status === "sending" ||
                previewPending ||
                !preview
              }
              onClick={() => {
                setSendResult(null);
                setConfirming(true);
              }}
            >
              <Send className="mr-2 h-4 w-4" />
              Envoyer pour de vrai
            </Button>
            {selected.status === "draft" ? (
              <Button
                variant="destructive"
                disabled={remove.isPending}
                onClick={() => remove.mutate({ announcementId: selected.id })}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Supprimer le brouillon
              </Button>
            ) : null}
          </div>
          <p className="text-xs text-fun-text-muted">
            Le test prépare les livraisons sans envoyer d&apos;email. Une
            annonce déjà envoyée reste une trace : elle ne peut plus être
            supprimée.
          </p>
        </section>
      ) : null}

      {/* ---- Confirmation d'envoi réel ---- */}
      <Dialog open={confirming} onOpenChange={setConfirming}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Envoyer à {recipientCount} famille
              {recipientCount > 1 ? "s" : ""} ?
            </DialogTitle>
            <DialogDescription>
              « {selected?.subject} » va partir par email à {recipientCount}{" "}
              destinataire{recipientCount > 1 ? "s" : ""} réel
              {recipientCount > 1 ? "s" : ""}. Cet envoi est immédiat et
              irréversible.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirming(false)}>
              Annuler
            </Button>
            <Button
              variant="destructive"
              disabled={send.isPending || !selected}
              onClick={() => {
                if (!selected) return;
                send.mutate({
                  announcementId: selected.id,
                  params: { dry_run: false },
                });
              }}
            >
              Envoyer à {recipientCount} destinataire
              {recipientCount > 1 ? "s" : ""}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
