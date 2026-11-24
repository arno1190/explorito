"use client";

import { Eraser, Eye, PenLine } from "lucide-react";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { useTracingGlyphsApiV1ExercisesTracingGlyphsGet } from "@/lib/api/generated/exercises/exercises";
import type { TracingStyle } from "@/lib/api/model";
import { cn } from "@/lib/utils";
import type { ExerciseTypeComponentProps, TracingContent } from "./types";

/**
 * Ardoise de tracé : l'enfant trace une lettre ou un chiffre au stylet ou au doigt.
 *
 * Portage du prototype « Ardoise des lettres » de Thomas. Les tracés de
 * référence viennent du serveur (`GET /exercises/tracing/glyphs`), qui corrige
 * aussi l'encre envoyée : ce composant ne décide jamais si c'est juste, il ne
 * fait que dessiner, enregistrer les traits et montrer ce qui a été manqué.
 *
 * Repère : une case de 100 × 140 (y vers le bas), centrée dans l'ardoise.
 */

type Point = [number, number];
type InkStroke = { id: number; pts: [number, number, number][] }; // x, y, épaisseur

const BOX_W = 100;
const BOX_H = 140;
const MARGIN = 12;
const PEN_ONLY_KEY = "explorito-tracing-pen-only";
/** Pas minimal entre deux points enregistrés : borne la taille de la réponse. */
const MIN_STEP = 0.8;
const MAX_POINTS = 3500;

function token(name: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

function resample(pts: Point[], step: number): Point[] {
  if (pts.length === 0) return [];
  const out: Point[] = [pts[0]];
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1];
    const [x1, y1] = pts[i];
    const n = Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0) / step));
    for (let j = 1; j <= n; j++)
      out.push([x0 + ((x1 - x0) * j) / n, y0 + ((y1 - y0) * j) / n]);
  }
  return out;
}

function pointAlong(pts: Point[], dist: number) {
  let acc = 0;
  for (let i = 1; i < pts.length; i++) {
    const [ax, ay] = pts[i - 1];
    const [bx, by] = pts[i];
    const d = Math.hypot(bx - ax, by - ay);
    if (d > 0 && acc + d >= dist) {
      const t = (dist - acc) / d;
      return {
        x: ax + (bx - ax) * t,
        y: ay + (by - ay) * t,
        dx: (bx - ax) / d,
        dy: (by - ay) / d,
      };
    }
    acc += d;
  }
  const [ax, ay] = pts[pts.length - 2] ?? pts[0];
  const [bx, by] = pts[pts.length - 1];
  const d = Math.hypot(bx - ax, by - ay) || 1;
  return { x: bx, y: by, dx: (bx - ax) / d, dy: (by - ay) / d };
}

function wipe(c: CanvasRenderingContext2D) {
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.clearRect(0, 0, c.canvas.width, c.canvas.height);
}

function polyline(c: CanvasRenderingContext2D, pts: Point[]) {
  c.beginPath();
  c.moveTo(pts[0][0], pts[0][1]);
  for (const p of pts.slice(1)) c.lineTo(p[0], p[1]);
}

export function Tracing({
  content,
  onAnswer,
  disabled,
  showResult,
  isCorrect,
}: ExerciseTypeComponentProps<TracingContent>) {
  const style = content.style ?? "capitale";
  const mode = content.mode ?? "guided";
  const catalogue = useTracingGlyphsApiV1ExercisesTracingGlyphsGet({
    query: { staleTime: Infinity, gcTime: Infinity },
  });
  const sheet: TracingStyle | undefined = catalogue.data?.[style];
  const strokes = sheet?.glyphs[content.glyph] as Point[][] | undefined;
  const lines = sheet?.lines;

  const boardRef = useRef<HTMLDivElement>(null);
  const guideRef = useRef<HTMLCanvasElement>(null);
  const inkRef = useRef<HTMLCanvasElement>(null);
  const fxRef = useRef<HTMLCanvasElement>(null);
  const view = useRef({ s: 1, ox: 0, oy: 0, dpr: 1, w: 0 });
  const ink = useRef<InkStroke[]>([]);
  const current = useRef<InkStroke | null>(null);
  const anim = useRef(0);
  const [penOnly, setPenOnly] = useState(false);
  const [showModel, setShowModel] = useState(true);
  const [hasInk, setHasInk] = useState(false);
  const [hint, setHint] = useState<"missed" | "direction">("missed");

  useEffect(() => {
    try {
      setPenOnly(localStorage.getItem(PEN_ONLY_KEY) === "1");
    } catch {
      /* stockage indisponible : réglage par défaut */
    }
  }, []);

  const togglePenOnly = () => {
    setPenOnly((on) => {
      try {
        localStorage.setItem(PEN_ONLY_KEY, on ? "0" : "1");
      } catch {
        /* réglage non mémorisé */
      }
      return !on;
    });
  };

  const apply = useCallback((c: CanvasRenderingContext2D) => {
    const { s, ox, oy, dpr } = view.current;
    c.setTransform(dpr * s, 0, 0, dpr * s, dpr * ox, dpr * oy);
    c.lineCap = "round";
    c.lineJoin = "round";
  }, []);

  const drawGuide = useCallback(() => {
    const c = guideRef.current?.getContext("2d");
    if (!c || !strokes || !lines) return;
    wipe(c);
    apply(c);
    const { s, ox, w } = view.current;
    const x0 = -ox / s;
    const x1 = (w - ox) / s;
    for (const line of lines) {
      c.beginPath();
      c.moveTo(x0, line.y);
      c.lineTo(x1, line.y);
      c.setLineDash(line.role === "base" ? [] : [3, 4]);
      c.lineWidth = line.role === "base" ? 1.6 : 1;
      c.strokeStyle = token(
        line.role === "base" ? "--fun-text-muted" : "--fun-border"
      );
      c.stroke();
    }
    c.setLineDash([]);
    if (mode !== "guided") return;

    const dots = token("--fun-text-muted");
    const start = token("--fun-green");
    const arrow = token("--fun-violet") || token("--fun-sky");
    for (const st of strokes) {
      polyline(c, st);
      c.lineWidth = 12;
      c.strokeStyle = token("--fun-sky-light");
      c.stroke();
      c.setLineDash([0.1, 6]);
      c.lineWidth = 3.6;
      c.strokeStyle = dots;
      c.stroke();
      c.setLineDash([]);
    }
    strokes.forEach((st, i) => {
      const a = pointAlong(st, 16);
      const b = pointAlong(st, 8);
      c.beginPath();
      c.moveTo(b.x, b.y);
      c.lineTo(a.x, a.y);
      c.moveTo(a.x - a.dx * 4.5 + a.dy * 3.5, a.y - a.dy * 4.5 - a.dx * 3.5);
      c.lineTo(a.x, a.y);
      c.lineTo(a.x - a.dx * 4.5 - a.dy * 3.5, a.y - a.dy * 4.5 + a.dx * 3.5);
      c.lineWidth = 2.2;
      c.strokeStyle = arrow;
      c.stroke();
      let [x, y] = st[0];
      // Deux traits partant du même point : on décale la pastille du second.
      if (
        strokes
          .slice(0, i)
          .some((o) => Math.hypot(o[0][0] - x, o[0][1] - y) < 4)
      ) {
        x += 10 * (a.dx >= 0 ? 1 : -1);
        y -= 9;
      }
      c.beginPath();
      c.arc(x, y, 5.5, 0, Math.PI * 2);
      c.fillStyle = start;
      c.fill();
      if (strokes.length > 1) {
        c.fillStyle = "#fff";
        c.font = "800 7.5px var(--font-nunito), sans-serif";
        c.textAlign = "center";
        c.textBaseline = "middle";
        c.fillText(String(i + 1), x, y + 0.5);
      }
    });
  }, [apply, lines, mode, strokes]);

  const drawInk = useCallback(() => {
    const c = inkRef.current?.getContext("2d");
    if (!c) return;
    wipe(c);
    apply(c);
    c.strokeStyle = token(
      showResult ? (isCorrect ? "--fun-green" : "--fun-red") : "--fun-sky"
    );
    for (const st of ink.current) {
      for (let i = 0; i < st.pts.length; i++) {
        const p = st.pts[i];
        const q = st.pts[Math.max(0, i - 1)];
        c.beginPath();
        c.moveTo(q[0], q[1]);
        c.lineTo(p[0], p[1]);
        c.lineWidth = p[2];
        c.stroke();
      }
    }
  }, [apply, isCorrect, showResult]);

  const clearFx = useCallback(() => {
    cancelAnimationFrame(anim.current);
    const c = fxRef.current?.getContext("2d");
    if (c) wipe(c);
  }, []);

  /** Après une erreur : points manqués (pointillés) ou modèle fantôme (seul). */
  const drawHint = useCallback(() => {
    const c = fxRef.current?.getContext("2d");
    if (!c || !strokes) return;
    wipe(c);
    apply(c);
    if (mode === "guided") {
      const inkPts = ink.current.flatMap((st) =>
        resample(
          st.pts.map((p) => [p[0], p[1]] as Point),
          2
        )
      );
      const r2 = style === "capitale" || style === "chiffre" ? 100 : 64;
      c.fillStyle = token("--fun-sun");
      const missed = strokes
        .flatMap((st) => resample(st, 2))
        .filter(
          (g, i) =>
            i % 2 === 0 &&
            !inkPts.some((p) => (p[0] - g[0]) ** 2 + (p[1] - g[1]) ** 2 <= r2)
        );
      for (const [x, y] of missed) {
        c.beginPath();
        c.arc(x, y, 2.4, 0, Math.PI * 2);
        c.fill();
      }
      // Rien de manqué mais refusé : c'est l'ordre ou le sens des traits.
      setHint(missed.length > 0 ? "missed" : "direction");
    } else {
      c.lineWidth = 9;
      c.strokeStyle = token("--fun-green-light");
      for (const st of strokes) {
        polyline(c, st);
        c.stroke();
      }
    }
  }, [apply, mode, strokes, style]);

  const layout = useCallback(() => {
    const board = boardRef.current;
    if (!board) return;
    const r = board.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    for (const cv of [guideRef.current, inkRef.current, fxRef.current]) {
      if (!cv) continue;
      cv.width = Math.round(r.width * dpr);
      cv.height = Math.round(r.height * dpr);
    }
    const s = Math.min(
      r.width / (BOX_W + 2 * MARGIN),
      r.height / (BOX_H + 2 * MARGIN)
    );
    view.current = {
      s,
      ox: (r.width - BOX_W * s) / 2,
      oy: (r.height - BOX_H * s) / 2,
      dpr,
      w: r.width,
    };
    drawGuide();
    drawInk();
    clearFx();
  }, [clearFx, drawGuide, drawInk]);

  useLayoutEffect(() => {
    const board = boardRef.current;
    if (!board) return;
    const ro = new ResizeObserver(layout);
    ro.observe(board);
    return () => ro.disconnect();
  }, [layout]);

  // Résultat : l'encre prend la couleur du verdict, et l'aide apparaît après une erreur.
  useEffect(() => {
    drawInk();
    if (showResult && isCorrect === false) drawHint();
  }, [drawHint, drawInk, isCorrect, showResult]);

  // « Réessayer » réactive l'ardoise : on repart d'une ardoise propre.
  const wasDisabled = useRef(disabled);
  useEffect(() => {
    if (wasDisabled.current && !disabled) {
      ink.current = [];
      setHasInk(false);
      drawInk();
      clearFx();
    }
    wasDisabled.current = disabled;
  }, [clearFx, disabled, drawInk]);

  const report = () => {
    const total = ink.current.reduce((n, st) => n + st.pts.length, 0);
    setHasInk(total > 0);
    onAnswer(
      total >= 6
        ? {
            strokes: ink.current.map((st) =>
              st.pts.map(([x, y]) => [
                Math.round(x * 10) / 10,
                Math.round(y * 10) / 10,
              ])
            ),
          }
        : null
    );
  };

  const toBox = (
    e: React.PointerEvent | PointerEvent
  ): [number, number, number] => {
    const r = inkRef.current!.getBoundingClientRect();
    const { s, ox, oy } = view.current;
    const width = e.pointerType === "pen" ? 3 + (e.pressure || 0.5) * 4.5 : 5.5;
    return [(e.clientX - r.left - ox) / s, (e.clientY - r.top - oy) / s, width];
  };

  const onPointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (disabled || !e.isPrimary || current.current) return;
    if (penOnly && e.pointerType === "touch") return;
    if (ink.current.reduce((n, st) => n + st.pts.length, 0) >= MAX_POINTS)
      return;
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    clearFx();
    current.current = { id: e.pointerId, pts: [toBox(e)] };
    ink.current.push(current.current);
    drawInk();
  };

  const onPointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const st = current.current;
    if (!st || e.pointerId !== st.id) return;
    e.preventDefault();
    const events = e.nativeEvent.getCoalescedEvents?.() ?? [e.nativeEvent];
    const c = inkRef.current?.getContext("2d");
    if (c) {
      apply(c);
      c.strokeStyle = token("--fun-sky");
    }
    for (const ev of events.length ? events : [e.nativeEvent]) {
      const p = toBox(ev);
      const last = st.pts[st.pts.length - 1];
      if (Math.hypot(p[0] - last[0], p[1] - last[1]) < MIN_STEP) continue;
      st.pts.push(p);
      if (c) {
        c.beginPath();
        c.moveTo(last[0], last[1]);
        c.lineTo(p[0], p[1]);
        c.lineWidth = p[2];
        c.stroke();
      }
    }
  };

  const onPointerUp = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!current.current || e.pointerId !== current.current.id) return;
    current.current = null;
    report();
  };

  const erase = () => {
    ink.current = [];
    drawInk();
    clearFx();
    report();
  };

  const watch = () => {
    if (!strokes) return;
    clearFx();
    const segs = strokes.map((st) => resample(st, 1));
    let si = 0;
    let pi = 0;
    let last = 0;
    let wait = 0;
    const frame = (ts: number) => {
      const c = fxRef.current?.getContext("2d");
      if (!c) return;
      const dt = last ? Math.min(50, ts - last) : 0;
      last = ts;
      if (wait > 0) wait -= dt;
      else if (si < segs.length) {
        pi += dt * 0.11;
        if (pi >= segs[si].length - 1) {
          si++;
          pi = 0;
          wait = 380;
        }
      }
      wipe(c);
      apply(c);
      c.lineWidth = 6;
      c.strokeStyle = token("--fun-violet") || token("--fun-sky");
      for (let i = 0; i < Math.min(si, segs.length); i++) {
        polyline(c, segs[i]);
        c.stroke();
      }
      if (si < segs.length) {
        const part = segs[si].slice(0, Math.max(1, Math.floor(pi) + 1));
        if (part.length > 1) {
          polyline(c, part);
          c.stroke();
        }
        const [hx, hy] = part[part.length - 1];
        c.beginPath();
        c.arc(hx, hy, 5.5, 0, Math.PI * 2);
        c.fillStyle = c.strokeStyle;
        c.fill();
        anim.current = requestAnimationFrame(frame);
      } else if (wait > -700) {
        wait -= dt;
        anim.current = requestAnimationFrame(frame);
      } else {
        wipe(c);
      }
    };
    anim.current = requestAnimationFrame(frame);
  };

  useEffect(() => () => cancelAnimationFrame(anim.current), []);

  const button =
    "inline-flex h-12 min-w-12 items-center justify-center gap-2 rounded-xl border-2 border-fun-border bg-fun-surface px-4 font-bold text-fun-text active:scale-95 disabled:opacity-50";

  if (catalogue.isError || (catalogue.data && !strokes)) {
    return (
      <div className="rounded-xl bg-fun-sun-light p-4 text-fun-text">
        Ce tracé n&apos;est pas disponible pour le moment.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div
        ref={boardRef}
        className="relative h-[58vh] max-h-[560px] min-h-[320px] w-full touch-none select-none overflow-hidden rounded-2xl border-2 border-fun-border bg-fun-surface"
        onTouchMove={(e) => e.preventDefault()}
      >
        <canvas
          ref={guideRef}
          className="absolute inset-0 h-full w-full"
          aria-hidden="true"
        />
        <canvas
          ref={inkRef}
          className="absolute inset-0 h-full w-full touch-none"
          aria-label={`Ardoise : trace ${content.glyph}`}
          role="img"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        />
        <canvas
          ref={fxRef}
          className="pointer-events-none absolute inset-0 h-full w-full"
          aria-hidden="true"
        />
        {mode === "model" && strokes && (
          <button
            type="button"
            onClick={() => setShowModel((v) => !v)}
            className="absolute left-3 top-3 flex h-28 w-20 flex-col items-center justify-end rounded-xl border-2 border-dashed border-fun-border bg-fun-green-light/60 pb-1 text-sm font-semibold text-fun-text-muted"
            aria-label={showModel ? "Cacher le modèle" : "Montrer le modèle"}
          >
            <svg
              viewBox="-6 -6 112 152"
              className={cn("w-full flex-1", !showModel && "opacity-0")}
              aria-hidden="true"
            >
              {strokes.map((st, i) => (
                <polyline
                  key={i}
                  points={st.map(([x, y]) => `${x},${y}`).join(" ")}
                  fill="none"
                  stroke="var(--fun-green)"
                  strokeWidth={8}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              ))}
            </svg>
            modèle
          </button>
        )}
        {catalogue.isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        {mode !== "free" && (
          <button
            type="button"
            className={button}
            onClick={watch}
            disabled={!strokes}
          >
            <Eye className="h-5 w-5" /> Regarde
          </button>
        )}
        <button
          type="button"
          className={button}
          onClick={erase}
          disabled={disabled || !hasInk}
        >
          <Eraser className="h-5 w-5" /> Effacer
        </button>
        <button
          type="button"
          className={cn(button, penOnly && "border-fun-sky bg-fun-sky-light")}
          onClick={togglePenOnly}
          aria-pressed={penOnly}
        >
          <PenLine className="h-5 w-5" /> Stylet seulement
        </button>
      </div>

      {showResult && isCorrect === false && (
        <p className="text-center text-lg font-bold text-fun-text">
          {mode !== "guided"
            ? "Essaie encore ! Regarde bien le modèle."
            : hint === "direction"
              ? "Presque ! Pars du point vert et suis les flèches."
              : "Presque ! Repasse sur les points jaunes."}
        </p>
      )}
    </div>
  );
}
