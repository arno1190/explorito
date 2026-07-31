"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AVATAR_OPTIONS } from "@/lib/avatars";
import { cn } from "@/lib/utils";

/** Sélecteur d'avatar (grille d'emoji) dans une boîte de dialogue. */
export function AvatarPicker({
  open,
  onOpenChange,
  current,
  onSelect,
  title = "Choisis ton avatar",
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  current?: string | null;
  onSelect: (avatar: string) => void;
  title?: string;
}) {
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
      </DialogContent>
    </Dialog>
  );
}
