"use client";

import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LEVELS } from "@/lib/levels";
import { updateChildApiV1ChildrenChildIdPut } from "@/lib/api/generated/children/children";
import { listCatalogsApiV1CollectionCatalogsGet } from "@/lib/api/generated/collection/collection";
import type { CatalogMeta, ChildResponse, LevelEnum } from "@/lib/api/model";

interface EditChildDialogProps {
  child: ChildResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: (child: ChildResponse) => void;
}

/**
 * Édition d'un enfant : nom, date de naissance, niveau, et collections
 * accessibles (le parent peut masquer certaines collections, ex. Harry Potter
 * en maternelle).
 */
export function EditChildDialog({
  child,
  open,
  onOpenChange,
  onSaved,
}: EditChildDialogProps) {
  const [name, setName] = useState(child.name);
  const [birthDate, setBirthDate] = useState(child.birth_date ?? "");
  const [level, setLevel] = useState<LevelEnum | "">(child.level ?? "");
  const [catalogs, setCatalogs] = useState<CatalogMeta[]>([]);
  const [disabled, setDisabled] = useState<Set<string>>(
    new Set(child.disabled_collections ?? [])
  );
  const [saving, setSaving] = useState(false);

  // Réinitialise le formulaire à chaque ouverture / changement d'enfant.
  useEffect(() => {
    if (!open) return;
    setName(child.name);
    setBirthDate(child.birth_date ?? "");
    setLevel(child.level ?? "");
    setDisabled(new Set(child.disabled_collections ?? []));
    listCatalogsApiV1CollectionCatalogsGet()
      .then(setCatalogs)
      .catch(() => setCatalogs([]));
  }, [open, child]);

  const toggle = (slug: string) => {
    setDisabled((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  };

  const save = async () => {
    setSaving(true);
    try {
      const updated = await updateChildApiV1ChildrenChildIdPut(child.id, {
        name,
        birth_date: birthDate || null,
        level: level || null,
        disabled_collections: [...disabled],
      });
      onSaved(updated);
      onOpenChange(false);
    } catch (err) {
      console.error("Échec de la mise à jour de l'enfant :", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto rounded-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-extrabold text-fun-text">
            Modifier {child.name}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="edit-name">Prénom</Label>
            <Input
              id="edit-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-birth">Date de naissance</Label>
            <Input
              id="edit-birth"
              type="date"
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-level">Niveau scolaire</Label>
            <select
              id="edit-level"
              value={level}
              onChange={(e) => setLevel(e.target.value as LevelEnum)}
              className="h-11 w-full rounded-xl border-2 border-fun-border bg-white px-3 text-fun-text outline-none focus:border-fun-sky"
            >
              <option value="">Choisir…</option>
              {LEVELS.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label>Collections accessibles</Label>
            <p className="text-xs text-fun-text-muted">
              Décoche une collection pour la masquer à cet enfant.
            </p>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {catalogs.map((cat) => {
                const enabled = !disabled.has(cat.slug);
                return (
                  <button
                    key={cat.slug}
                    type="button"
                    onClick={() => toggle(cat.slug)}
                    aria-pressed={enabled}
                    className={`flex items-center gap-2 rounded-xl border-2 px-3 py-2 text-left text-sm font-semibold transition-all active:scale-95 ${
                      enabled
                        ? "border-fun-green bg-fun-green-light text-fun-text"
                        : "border-fun-border bg-white text-fun-text-muted opacity-70"
                    }`}
                  >
                    <span className="text-lg" aria-hidden>
                      {cat.icon}
                    </span>
                    <span className="flex-1">{cat.name}</span>
                    <span aria-hidden>{enabled ? "✅" : "🚫"}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={saving}
          >
            Annuler
          </Button>
          <Button onClick={save} disabled={saving || name.trim().length < 2}>
            {saving ? "Enregistrement…" : "Enregistrer"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
