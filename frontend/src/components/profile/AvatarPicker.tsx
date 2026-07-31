"use client";

import { useRef, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AVATAR_OPTIONS } from "@/lib/avatars";
import { cn } from "@/lib/utils";

/**
 * Sélecteur d'avatar : grille d'emoji + (optionnel) import d'une photo.
 *
 * `uploader` reçoit le fichier choisi et se charge de l'envoyer au bon endpoint
 * (soi-même ou un enfant), puis de rafraîchir l'affichage.
 */
export function AvatarPicker({
  open,
  onOpenChange,
  current,
  onSelect,
  uploader,
  title = "Choisis ton avatar",
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  current?: string | null;
  onSelect: (avatar: string) => void;
  uploader?: (file: File) => Promise<void>;
  title?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !uploader) return;
    setUploading(true);
    setError(null);
    try {
      await uploader(file);
      onOpenChange(false);
    } catch {
      setError("Import impossible (format non supporté ou image trop lourde).");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-2xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-6 gap-2 py-2">
          {AVATAR_OPTIONS.map((a) => (
            <button
              key={a}
              type="button"
              onClick={() => {
                onSelect(a);
                onOpenChange(false);
              }}
              aria-label={`Avatar ${a}`}
              className={cn(
                "flex h-12 w-12 items-center justify-center rounded-xl text-2xl transition-all hover:scale-110 active:scale-95",
                current === a
                  ? "bg-fun-green-light ring-2 ring-fun-green"
                  : "bg-fun-sky-light"
              )}
            >
              {a}
            </button>
          ))}
        </div>

        {uploader && (
          <div className="mt-1 border-t border-fun-border pt-3">
            <input
              ref={inputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              className="hidden"
              onChange={onFile}
            />
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
              className="flex min-h-[44px] w-full items-center justify-center gap-2 rounded-xl bg-fun-sky px-4 py-2 font-bold text-white transition-all active:scale-95 disabled:opacity-60"
            >
              {uploading ? "Import…" : "📷 Importer une photo"}
            </button>
            {error && (
              <p className="mt-2 text-center text-sm font-semibold text-fun-red">
                {error}
              </p>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
