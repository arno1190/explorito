"use client";

import { useCallback, useRef } from "react";

type SoundName =
  | "correct"
  | "wrong"
  | "complete"
  | "tap"
  | "levelup"
  | "achievement";

function getAudioContext(): AudioContext | null {
  if (typeof window === "undefined") return null;
  const AudioCtx =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext: typeof AudioContext })
      .webkitAudioContext;
  if (!AudioCtx) return null;
  return new AudioCtx();
}

function playNote(
  ctx: AudioContext,
  frequency: number,
  startTime: number,
  duration: number,
  type: OscillatorType = "sine",
  volume: number = 0.3
) {
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(frequency, startTime);
  gain.gain.setValueAtTime(volume, startTime);
  gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start(startTime);
  osc.stop(startTime + duration);
}

const sounds: Record<SoundName, (ctx: AudioContext) => void> = {
  correct: (ctx) => {
    const t = ctx.currentTime;
    playNote(ctx, 523.25, t, 0.15, "sine", 0.3);
    playNote(ctx, 659.25, t + 0.1, 0.15, "sine", 0.3);
    playNote(ctx, 783.99, t + 0.2, 0.25, "sine", 0.25);
  },
  wrong: (ctx) => {
    const t = ctx.currentTime;
    playNote(ctx, 220, t, 0.3, "triangle", 0.2);
    playNote(ctx, 196, t + 0.15, 0.3, "triangle", 0.15);
  },
  complete: (ctx) => {
    const t = ctx.currentTime;
    const notes = [523.25, 587.33, 659.25, 783.99, 880];
    notes.forEach((freq, i) => {
      playNote(ctx, freq, t + i * 0.1, 0.2, "sine", 0.25);
    });
  },
  tap: (ctx) => {
    const t = ctx.currentTime;
    playNote(ctx, 800, t, 0.05, "square", 0.1);
  },
  levelup: (ctx) => {
    const t = ctx.currentTime;
    const notes = [523.25, 659.25, 783.99, 1046.5];
    notes.forEach((freq, i) => {
      playNote(ctx, freq, t + i * 0.12, 0.25, "sine", 0.3);
    });
    playNote(ctx, 1046.5, t + 0.48, 0.4, "triangle", 0.2);
  },
  achievement: (ctx) => {
    const t = ctx.currentTime;
    const notes = [1200, 1400, 1600, 1800, 1600, 1800];
    notes.forEach((freq, i) => {
      playNote(ctx, freq, t + i * 0.06, 0.1, "sine", 0.15);
    });
  },
};

export function useSound() {
  const ctxRef = useRef<AudioContext | null>(null);

  const play = useCallback((name: SoundName) => {
    try {
      if (!ctxRef.current || ctxRef.current.state === "closed") {
        ctxRef.current = getAudioContext();
      }
      const ctx = ctxRef.current;
      if (!ctx) return;

      if (ctx.state === "suspended") {
        ctx.resume();
      }

      sounds[name](ctx);
    } catch {
      // Audio not available - fail silently
    }
  }, []);

  return { play };
}
