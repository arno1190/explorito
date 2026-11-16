"use client";

import { useEffect, useRef, useState } from "react";

export interface MusicSound {
  frequency: number | null;
  beats: number;
}

/** Schedule on the audio clock; cancel playback on reset, replay or unmount. */
export function useMusicPlayback() {
  const context = useRef<AudioContext | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [playing, setPlaying] = useState(false);
  const [audioError, setAudioError] = useState(false);

  const stop = () => {
    if (timer.current) clearTimeout(timer.current);
    const previous = context.current;
    context.current = null;
    if (previous) void previous.close();
    setPlaying(false);
  };

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
      const previous = context.current;
      context.current = null;
      if (previous) void previous.close();
    },
    []
  );

  const play = async (sounds: MusicSound[], bpm: number) => {
    stop();
    let playbackContext: AudioContext | null = null;
    try {
      const AudioCtx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext })
          .webkitAudioContext;
      if (!AudioCtx) throw new Error("Audio unavailable");
      const ctx = new AudioCtx();
      playbackContext = ctx;
      context.current = ctx;
      await ctx.resume();
      if (context.current !== ctx) return;
      setAudioError(false);
      setPlaying(true);
      let time = ctx.currentTime + 0.08;
      for (const sound of sounds) {
        const duration = (sound.beats * 60) / bpm;
        if (sound.frequency !== null) {
          const oscillator = ctx.createOscillator();
          const gain = ctx.createGain();
          oscillator.type = "triangle";
          oscillator.frequency.value = sound.frequency;
          gain.gain.setValueAtTime(0, time);
          gain.gain.linearRampToValueAtTime(0.22, time + 0.01);
          gain.gain.setValueAtTime(0.22, time + duration * 0.7);
          gain.gain.exponentialRampToValueAtTime(0.001, time + duration * 0.9);
          oscillator.connect(gain);
          gain.connect(ctx.destination);
          oscillator.start(time);
          oscillator.stop(time + duration);
        }
        time += duration;
      }
      timer.current = setTimeout(
        () => {
          if (context.current === ctx) {
            setPlaying(false);
            context.current = null;
            void ctx.close();
          }
        },
        (time - ctx.currentTime) * 1000 + 50
      );
    } catch {
      if (playbackContext && context.current !== playbackContext) return;
      stop();
      setAudioError(true);
    }
  };
  return { play, stop, playing, audioError };
}

export function pitchFrequency(pitch: string) {
  const semitones: Record<string, number> = {
    C: 0,
    D: 2,
    E: 4,
    F: 5,
    G: 7,
    A: 9,
    B: 11,
  };
  const midi = 12 * (Number(pitch[1]) + 1) + semitones[pitch[0]];
  return 440 * 2 ** ((midi - 69) / 12);
}
