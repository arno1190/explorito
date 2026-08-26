"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { resolveMediaSrc } from "@/lib/media";

/** Carte détaillée d'un objet de collection (dinosaure, astre…) : image + anecdote. */
export function CollectibleModal({
  open,
  onClose,
  name,
  imageUrl,
  fact,
}: {
  open: boolean;
  onClose: () => void;
  name: string;
  imageUrl: string;
  fact?: string | null;
}) {
  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="rounded-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-extrabold text-fun-text">
            {name}
          </DialogTitle>
        </DialogHeader>
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-48 w-full items-center justify-center rounded-2xl bg-fun-sky-light p-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={resolveMediaSrc(imageUrl)}
              alt={name}
              className="max-h-44 max-w-full rounded-xl object-contain"
            />
          </div>
          {fact && (
            <p className="text-center text-fun-text leading-relaxed">{fact}</p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
