"use client";

import { useState } from "react";
import { Pencil } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { frDate } from "@/components/packs/utils";
import type { PackDetail } from "@/lib/api/model";

import { statusStyle } from "../_lib/contrib";
import { useQuickEdit } from "../_lib/useQuickEdit";
import { EditFailure } from "./EditFailure";
import { StatusBadge } from "./StatusBadge";

export function PackHeaderCard({
  pack,
  editable,
  onClone,
  cloning,
}: {
  pack: PackDetail;
  editable: boolean;
  onClone: () => void;
  cloning: boolean;
}) {
  const quickEdit = useQuickEdit(pack.id);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(pack.title);
  const [emoji, setEmoji] = useState(pack.emoji ?? "");
  const [description, setDescription] = useState(pack.description ?? "");
  const [tags, setTags] = useState((pack.tags ?? []).join(", "));

  const submit = () =>
    quickEdit.save(
      {
        title,
        emoji,
        description,
        tags: tags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
      },
      () => setEditing(false)
    );

  return (
    <section className="rounded-2xl bg-white p-5 candy-shadow">
      <div className="flex flex-wrap items-start gap-4">
        <span className="text-4xl" aria-hidden>
          {pack.emoji || "📦"}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-extrabold text-fun-text">
              {pack.title}
            </h1>
            <StatusBadge status={pack.community_status} />
          </div>
          <p className="mt-1 text-sm text-fun-text-muted">
            {statusStyle(pack.community_status).hint}
          </p>
          {pack.description && (
            <p className="mt-2 text-sm text-fun-text">{pack.description}</p>
          )}
          <p className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-full bg-fun-green-light px-2 py-0.5 text-xs font-bold text-fun-green">
              {pack.level_min.toUpperCase()} → {pack.level_max.toUpperCase()}
            </span>
            <span className="rounded-full bg-fun-sky-light px-2 py-0.5 text-xs font-bold text-fun-sky">
              {pack.lesson_count ?? 0} leçons · {pack.exercise_count ?? 0}{" "}
              exercices
            </span>
            <span className="rounded-full bg-fun-sun-light px-2 py-0.5 text-xs font-bold text-fun-text">
              Qualité{" "}
              {pack.quality_score == null
                ? "—"
                : `${Math.round(pack.quality_score)}/100`}
            </span>
            {(pack.tags ?? []).map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-fun-violet-light px-2 py-0.5 text-xs font-bold text-fun-violet"
              >
                {tag}
              </span>
            ))}
          </p>
          <p className="mt-2 text-xs text-fun-text-muted">
            Créé le {frDate(pack.created_at)}
            {pack.submitted_at && ` · Soumis le ${frDate(pack.submitted_at)}`}
            {pack.author_handle && ` · Signé « ${pack.author_handle} »`}
          </p>
        </div>
        {editable && !editing && (
          <Button variant="ghost" size="sm" onClick={() => setEditing(true)}>
            <Pencil className="h-4 w-4" />
            Corriger
          </Button>
        )}
      </div>

      {editing && (
        <div className="mt-4 space-y-3">
          <div className="grid gap-3 sm:grid-cols-[6rem_1fr]">
            <div className="space-y-1">
              <Label htmlFor="pack-emoji" className="text-fun-text">
                Emoji
              </Label>
              <Input
                id="pack-emoji"
                value={emoji}
                onChange={(event) => setEmoji(event.target.value)}
                maxLength={4}
                className="text-center text-2xl"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="pack-title" className="text-fun-text">
                Titre
              </Label>
              <Input
                id="pack-title"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />
            </div>
          </div>
          <div className="space-y-1">
            <Label htmlFor="pack-description" className="text-fun-text">
              Description
            </Label>
            <textarea
              id="pack-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={3}
              className="w-full rounded-xl border-2 border-fun-border bg-white p-3 text-sm text-fun-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fun-sky"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="pack-tags" className="text-fun-text">
              Étiquettes
            </Label>
            <Input
              id="pack-tags"
              value={tags}
              onChange={(event) => setTags(event.target.value)}
              placeholder="dinosaures, additions"
            />
            <p className="text-xs text-fun-text-muted">
              Séparées par des virgules. Elles servent aux autres parents à
              trouver le pack.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={submit} disabled={quickEdit.isPending}>
              {quickEdit.isPending ? "Enregistrement…" : "Enregistrer"}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setEditing(false);
                quickEdit.clearFailure();
              }}
            >
              Annuler
            </Button>
          </div>
          {quickEdit.failure && (
            <EditFailure
              failure={quickEdit.failure}
              onClone={onClone}
              cloning={cloning}
            />
          )}
        </div>
      )}
    </section>
  );
}
