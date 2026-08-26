"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { resolveMediaSrc } from "@/lib/media";

interface InstructionAudioProps {
  /** Chemin de l'audio de consigne (`/uploads/audio/...`). */
  src: string;
  /** Change à chaque exercice → relance la lecture automatique. */
  exerciseId: string;
}

/**
 * Lit la consigne à voix haute (pour les enfants non-lecteurs).
 *
 * Lecture automatique à l'affichage de l'exercice ; un gros bouton rond permet
 * de réécouter. Les navigateurs bloquent parfois l'autoplay tant qu'il n'y a pas
 * eu d'interaction : le bouton reste alors le moyen fiable de déclencher le son.
 */
export function InstructionAudio({ src, exerciseId }: InstructionAudioProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const resolved = resolveMediaSrc(src);

  const play = useCallback(() => {
    const el = audioRef.current;
    if (!el) return;
    el.currentTime = 0;
    void el.play().catch(() => {
      // Autoplay refusé (pas encore d'interaction) : l'enfant tapera le bouton.
      setPlaying(false);
    });
  }, []);

  // Relance la lecture à chaque nouvel exercice.
  useEffect(() => {
    play();
  }, [exerciseId, resolved, play]);

  if (!resolved) return null;

  return (
    <div className="mb-2 flex items-center gap-3">
      <button
        type="button"
        onClick={play}
        aria-label="Écouter la consigne"
        className={cn(
          "flex h-14 w-14 flex-none items-center justify-center rounded-full bg-fun-sky text-white shadow-[0_4px_0_var(--fun-sky)] transition-all active:translate-y-[4px] active:shadow-none",
          playing && "animate-[candy-glow_2s_infinite]"
        )}
      >
        <Volume2 className="h-7 w-7" />
      </button>
      <span className="text-sm font-semibold text-fun-text-muted">
        Écoute la consigne
      </span>
      <audio
        ref={audioRef}
        src={resolved}
        preload="auto"
        onPlay={() => setPlaying(true)}
        onEnded={() => setPlaying(false)}
        onPause={() => setPlaying(false)}
      />
    </div>
  );
}
