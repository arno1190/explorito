"""Correction des exercices ``tracing`` à partir de l'encre de l'enfant.

Portage serveur de la correction du prototype « Ardoise des lettres » (Thomas),
avec deux ajouts : l'**ordre** et le **sens** des traits, qui sont ce qu'on
enseigne en maternelle, sont vérifiés en modes ``guided`` et ``model``.

Principe : le tracé de référence et l'encre sont rééchantillonnés tous les
``STEP`` unités. On mesure

- la **couverture** : part des points de référence qui ont de l'encre à proximité ;
- l'**encre perdue** : part des points d'encre loin de tout point de référence.

En modes ``model`` et ``free`` l'encre est d'abord recadrée sur la boîte de la
lettre : l'enfant écrit seul, on ne lui demande pas de tomber pile sur le gabarit.
"""

import math
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import cache
from statistics import median
from typing import Any, Final, Literal

from app.services.tracing_glyphs import GLYPHS, METRICS, Point, Stroke

TracingMode = Literal["guided", "model", "free"]
STEP: Final = 2.0
#: Au-delà de ce multiple de la longueur de la lettre, l'encre est un gribouillis.
MAX_INK_RATIO: Final = 3.0
#: Les minuscules sont deux à trois fois plus petites que les capitales dans la
#: même case : les tolérances suivent, sinon un « a » à peu près rond passerait pour un « o ».
_STYLE_SCALE: Final[dict[str, float]] = {"capitale": 1.0, "chiffre": 1.0, "script": 0.8, "cursive": 0.8}


@dataclass(frozen=True)
class _Rules:
    near: float  # rayon de couverture d'un point de référence
    stray: float  # au-delà, un point d'encre est « perdu »
    min_coverage: float
    max_stray: float


_RULES: Final[dict[str, _Rules]] = {
    "guided": _Rules(near=10, stray=16, min_coverage=0.88, max_stray=0.20),
    "model": _Rules(near=14, stray=20, min_coverage=0.75, max_stray=0.25),
    "free": _Rules(near=14, stray=20, min_coverage=0.75, max_stray=0.25),
}


@dataclass(frozen=True)
class TraceVerdict:
    """Résultat détaillé d'une correction.

    Attributes:
        ok: Tracé accepté.
        coverage: Part du tracé de référence recouverte (0–1).
        stray: Part de l'encre hors du tracé (0–1).
        order_ok: Les traits ont été faits dans l'ordre enseigné.
        direction_ok: Chaque trait a été parcouru dans le bon sens.
        missed: Points de référence non recouverts (pour les montrer à l'enfant).
    """

    ok: bool
    coverage: float = 0.0
    stray: float = 1.0
    order_ok: bool = True
    direction_ok: bool = True
    missed: tuple[Point, ...] = field(default_factory=tuple)


def resample(points: Sequence[Sequence[float]], step: float = STEP) -> Stroke:
    """Rééchantillonne une polyligne pour qu'aucun écart ne dépasse ``step``."""
    if not points:
        return []
    out: Stroke = [(float(points[0][0]), float(points[0][1]))]
    for previous, current in zip(points, points[1:], strict=False):
        x0, y0, x1, y1 = float(previous[0]), float(previous[1]), float(current[0]), float(current[1])
        n = max(1, math.ceil(math.hypot(x1 - x0, y1 - y0) / step))
        out.extend((x0 + (x1 - x0) * j / n, y0 + (y1 - y0) * j / n) for j in range(1, n + 1))
    return out


class _Grid:
    """Index spatial à cases carrées : recherche du plus proche voisin dans un rayon."""

    def __init__(self, points: Sequence[Point], cell: float) -> None:
        self.points = points
        self.cell = cell
        self.cells: dict[tuple[int, int], list[int]] = defaultdict(list)
        for index, (x, y) in enumerate(points):
            self.cells[(int(x // cell), int(y // cell))].append(index)

    def all_within(self, point: Point, radius: float) -> list[int]:
        """Indices de tous les points à moins de ``radius``."""
        x, y = point
        reach = math.ceil(radius / self.cell)
        cx, cy = int(x // self.cell), int(y // self.cell)
        r2 = radius * radius
        found: list[int] = []
        for i in range(cx - reach, cx + reach + 1):
            for j in range(cy - reach, cy + reach + 1):
                for index in self.cells.get((i, j), ()):
                    px, py = self.points[index]
                    if (px - x) ** 2 + (py - y) ** 2 <= r2:
                        found.append(index)
        return found

    def first_within(self, point: Point, radius: float) -> int | None:
        """Plus petit indice parmi les points à moins de ``radius``, sinon ``None``.

        Sur l'encre, le plus petit indice est le **premier passage** du stylet :
        un enfant qui remonte le long d'un trait déjà fait (E sans lever le
        stylet) ne doit pas brouiller le sens du trait d'origine.
        """
        x, y = point
        reach = math.ceil(radius / self.cell)
        cx, cy = int(x // self.cell), int(y // self.cell)
        r2 = radius * radius
        best: int | None = None
        for i in range(cx - reach, cx + reach + 1):
            for j in range(cy - reach, cy + reach + 1):
                for index in self.cells.get((i, j), ()):
                    if best is not None and index >= best:
                        continue
                    px, py = self.points[index]
                    if (px - x) ** 2 + (py - y) ** 2 <= r2:
                        best = index
        return best


def _length(points: Sequence[Point], stroke_of: Sequence[int]) -> float:
    """Longueur totale des traits (sans compter les sauts entre deux traits)."""
    return sum(math.dist(points[i - 1], points[i]) for i in range(1, len(points)) if stroke_of[i] == stroke_of[i - 1])


def _bbox(points: Sequence[Point]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _fit_to(ink: list[Point], guide: list[Point]) -> list[Point] | None:
    """Recadre l'encre sur la boîte du tracé de référence ; ``None`` si l'encre est minuscule."""
    gx0, gy0, gx1, gy1 = _bbox(guide)
    ix0, iy0, ix1, iy1 = _bbox(ink)
    gw, gh, iw, ih = gx1 - gx0, gy1 - gy0, ix1 - ix0, iy1 - iy0
    if max(iw, ih) < 0.35 * max(gw, gh):
        return None
    sy = gh / max(ih, 1.0)
    if gw < 8:  # lettre filiforme (I, l, 1) : on garde les proportions sur la hauteur
        return [((gx0 + gx1) / 2 + (x - (ix0 + ix1) / 2) * sy, gy0 + (y - iy0) * sy) for x, y in ink]
    sx = gw / max(iw, 1.0)
    return [(gx0 + (x - ix0) * sx, gy0 + (y - iy0) * sy) for x, y in ink]


def _order_and_direction(guide_strokes: list[Stroke], passes: list[list[dict[int, int]]]) -> tuple[bool, bool]:
    """Vérifie l'ordre des traits et leur sens.

    ``passes[s][k]`` associe, pour le k-ième point du trait de référence ``s``,
    chaque trait d'encre passé à proximité à l'indice de son **premier passage**.

    Pour chaque trait de référence, le trait d'encre qui en recouvre le plus de
    points en est le « propriétaire » : deux traits qui se superposent (la hampe
    du d sur son rond) ne se volent donc pas leurs points. Le sens est bon si le
    dernier tiers du trait de référence a été tracé après le premier ; l'ordre est
    bon si les traits de référence sont tracés l'un après l'autre. Un enfant qui
    enchaîne plusieurs traits sans lever le stylet garde un ordre correct.
    """
    order_ok = direction_ok = True
    previous_moment = -1.0
    owners: set[int] = set()
    for stroke, stroke_passes in zip(guide_strokes, passes, strict=True):
        covered = [p for p in stroke_passes if p]
        if len(covered) < 3:
            continue  # trop peu recouvert : la couverture s'en charge (points, petits traits)
        counts = Counter(ink_stroke for p in covered for ink_stroke in p)
        best = max(counts.values())
        # À couverture quasi égale (un trait qui repasse sur le précédent, comme la
        # canne du a sur son rond), le trait d'encre encore libre l'emporte.
        owner = max(
            (ink_stroke for ink_stroke, count in counts.items() if count >= 0.9 * best),
            key=lambda ink_stroke: (ink_stroke not in owners, counts[ink_stroke], ink_stroke),
        )
        owners.add(owner)
        owned = [p[owner] for p in covered if owner in p]
        moment = median(owned)
        if moment < previous_moment:
            order_ok = False
        previous_moment = max(previous_moment, moment)
        length = sum(math.dist(a, b) for a, b in zip(stroke, stroke[1:], strict=False))
        if length >= 8 and len(owned) >= 3:
            third = max(1, len(owned) // 3)
            if median(owned[-third:]) <= median(owned[:third]):
                direction_ok = False
    return order_ok, direction_ok


def evaluate(style: str, glyph: str, mode: str, ink: Sequence[Sequence[Sequence[float]]]) -> TraceVerdict:
    """Corrige un tracé.

    Args:
        style: ``capitale``, ``chiffre``, ``script`` ou ``cursive``.
        glyph: Caractère attendu (doit exister pour ce style).
        mode: ``guided`` (pointillés), ``model`` (modèle à côté) ou ``free``.
        ink: Traits de l'enfant, dans l'ordre, en coordonnées de la case 100 × 140.

    Returns:
        Le verdict, avec les points de référence manqués.

    Raises:
        KeyError: Style ou glyphe inconnu.

    Example:
        >>> evaluate("capitale", "I", "guided", [[(50, 10), (50, 130)]]).ok
        True
    """
    rules = _RULES[mode]
    scale = _STYLE_SCALE[style]
    near, stray_radius = rules.near * scale, rules.stray * scale

    guide_strokes = [resample(stroke) for stroke in GLYPHS[style][glyph]]
    guide = [point for stroke in guide_strokes for point in stroke]
    stroke_of_guide = [i for i, stroke in enumerate(guide_strokes) for _ in stroke]

    ink_strokes = [resample(stroke) for stroke in ink if len(stroke) > 0]
    points = [point for stroke in ink_strokes for point in stroke]
    ink_stroke_of = [i for i, stroke in enumerate(ink_strokes) for _ in stroke]
    if len(points) < 6:
        return TraceVerdict(ok=False, missed=tuple(guide))

    if mode != "guided":
        fitted = _fit_to(points, guide)
        if fitted is None:
            return TraceVerdict(ok=False, missed=tuple(guide))
        points = fitted

    # Gribouillis : une encre bien plus longue que la lettre recouvre tout sans rien tracer.
    if _length(points, ink_stroke_of) > MAX_INK_RATIO * _length(guide, stroke_of_guide):
        return TraceVerdict(ok=False, missed=tuple(guide))

    ink_grid = _Grid(points, near)
    guide_grid = _Grid(guide, stray_radius)
    passes: list[list[dict[int, int]]] = [[] for _ in guide_strokes]
    missed: list[Point] = []
    for index, point in enumerate(guide):
        first_pass: dict[int, int] = {}
        for hit in ink_grid.all_within(point, near):
            ink_stroke = ink_stroke_of[hit]
            if hit < first_pass.get(ink_stroke, len(points)):
                first_pass[ink_stroke] = hit
        if not first_pass:
            missed.append(point)
        passes[stroke_of_guide[index]].append(first_pass)

    coverage = 1 - len(missed) / len(guide)
    stray = sum(1 for point in points if guide_grid.first_within(point, stray_radius) is None) / len(points)
    order_ok = direction_ok = True
    if mode != "free":
        order_ok, direction_ok = _order_and_direction(guide_strokes, passes)

    ok = coverage >= rules.min_coverage and stray <= rules.max_stray and order_ok and direction_ok
    return TraceVerdict(
        ok=ok,
        coverage=round(coverage, 3),
        stray=round(stray, 3),
        order_ok=order_ok,
        direction_ok=direction_ok,
        missed=tuple(missed),
    )


@cache
def glyph_catalogue() -> dict[str, dict[str, Any]]:
    """Tracés de référence servis au client : lignes du cahier et traits ordonnés de chaque glyphe.

    Le client dessine les pointillés et anime « Regarde » à partir de ces traits ;
    c'est la même donnée que celle qui corrige, d'où une seule source.
    """
    return {
        style: {
            "lines": [{"y": y, "role": role} for y, role in METRICS[style]],
            "glyphs": {
                glyph: [[[round(x, 1), round(y, 1)] for x, y in stroke] for stroke in strokes]
                for glyph, strokes in glyphs.items()
            },
        }
        for style, glyphs in GLYPHS.items()
    }
