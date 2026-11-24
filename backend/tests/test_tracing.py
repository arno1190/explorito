"""Exercice ``tracing`` : tracé de lettres et chiffres au stylet ou au doigt.

La correction est faite par le serveur à partir de l'encre envoyée, jamais
sur la foi d'un score calculé par l'appareil : sinon un gribouillis rapporterait
l'XP d'une lettre bien tracée.
"""

import math
import random
import time

import pytest
from fastapi.testclient import TestClient

from app.api.exercises import check_answer_correctness
from app.models.content import Exercise, ExerciseType
from app.schemas.exercise import validate_exercise_payload
from app.services.pack_format import validate_pack
from app.services.tracing import evaluate, glyph_catalogue, resample
from app.services.tracing_glyphs import GLYPHS, METRICS
from tests.test_pack_format import codes, lesson, mcq, pack

ALL = [(style, glyph) for style, glyphs in GLYPHS.items() for glyph in glyphs]
MODES = ("guided", "model", "free")


def reference(style: str, glyph: str) -> list[list[tuple[float, float]]]:
    """L'encre d'un enfant qui suit exactement le tracé de référence."""
    return [list(stroke) for stroke in GLYPHS[style][glyph]]


def jitter(ink: list[list[tuple[float, float]]], amount: float, seed: int = 7) -> list[list[tuple[float, float]]]:
    rng = random.Random(seed)
    return [[(x + rng.uniform(-amount, amount), y + rng.uniform(-amount, amount)) for x, y in st] for st in ink]


# --------------------------------------------------------------------------- #
# Correction
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(("style", "glyph"), ALL)
@pytest.mark.parametrize("mode", MODES)
def test_following_the_reference_passes(style: str, glyph: str, mode: str):
    assert evaluate(style, glyph, mode, reference(style, glyph)).ok


@pytest.mark.parametrize(("style", "glyph"), [("capitale", "A"), ("script", "a"), ("cursive", "e"), ("chiffre", "5")])
def test_a_shaky_hand_still_passes(style: str, glyph: str):
    assert evaluate(style, glyph, "guided", jitter(reference(style, glyph), 3)).ok


@pytest.mark.parametrize("mode", MODES)
def test_empty_or_dot_ink_fails(mode: str):
    assert not evaluate("capitale", "A", mode, []).ok
    assert not evaluate("capitale", "A", mode, [[(50, 70)]]).ok


@pytest.mark.parametrize("mode", MODES)
def test_scribbling_over_the_whole_board_fails(mode: str):
    zigzag = [[(x, 10 + 120 * (i % 2)) for i, x in enumerate(range(0, 101, 4))]]
    assert not evaluate("capitale", "A", mode, zigzag).ok


@pytest.mark.parametrize("mode", MODES)
def test_another_letter_fails(mode: str):
    assert not evaluate("capitale", "L", mode, reference("capitale", "O")).ok
    assert not evaluate("script", "b", mode, reference("script", "o")).ok


def test_guided_mode_checks_the_direction_of_each_stroke():
    backwards = [list(reversed(stroke)) for stroke in reference("capitale", "L")]
    verdict = evaluate("capitale", "L", "guided", backwards)
    assert not verdict.ok
    assert not verdict.direction_ok


def test_guided_mode_checks_a_closed_loop_direction():
    backwards = [list(reversed(stroke)) for stroke in reference("script", "o")]
    assert not evaluate("script", "o", "guided", backwards).ok


def test_guided_mode_checks_stroke_order():
    stem_first = list(reversed(reference("capitale", "T")))
    verdict = evaluate("capitale", "T", "guided", stem_first)
    assert not verdict.ok
    assert not verdict.order_ok


def test_free_mode_forgives_order_and_direction_but_not_shape():
    stem_first = list(reversed(reference("capitale", "T")))
    assert evaluate("capitale", "T", "free", stem_first).ok


def test_strokes_drawn_as_one_continuous_line_keep_their_order():
    e_in_one_go = [[point for stroke in reference("capitale", "E") for point in stroke]]
    assert evaluate("capitale", "E", "guided", e_in_one_go).ok


def test_free_mode_accepts_a_letter_written_smaller_elsewhere():
    shifted = [[(30 + x * 0.6, 20 + y * 0.6) for x, y in st] for st in reference("capitale", "R")]
    assert evaluate("capitale", "R", "free", shifted).ok
    assert not evaluate("capitale", "R", "guided", shifted).ok


def test_free_mode_rejects_a_tiny_letter():
    tiny = [[(40 + x * 0.15, 60 + y * 0.15) for x, y in st] for st in reference("capitale", "R")]
    assert not evaluate("capitale", "R", "free", tiny).ok


def test_guided_mode_reports_the_missed_points_to_show():
    half_a = reference("capitale", "A")[:2]
    verdict = evaluate("capitale", "A", "guided", half_a)
    assert not verdict.ok
    assert verdict.missed
    assert all(abs(y - 88) < 1 for _, y in verdict.missed)


def test_evaluation_is_fast_on_a_densely_sampled_drawing():
    dense = [resample(stroke, 0.25) for stroke in reference("cursive", "m")]
    assert sum(len(stroke) for stroke in dense) > 1000
    start = time.perf_counter()
    assert evaluate("cursive", "m", "guided", dense).ok
    assert time.perf_counter() - start < 0.3


# --------------------------------------------------------------------------- #
# Contrat et réponse
# --------------------------------------------------------------------------- #
def tracing_exercise(glyph: str = "A", style: str = "capitale", mode: str = "guided") -> Exercise:
    return Exercise(
        type=ExerciseType.TRACING.value,
        question=f"Trace la lettre {glyph}.",
        content={"glyph": glyph, "style": style, "mode": mode},
        correct_answer={},
    )


def test_contract_accepts_every_style():
    for style, glyph in [("capitale", "A"), ("script", "g"), ("cursive", "l"), ("chiffre", "7")]:
        validate_exercise_payload(ExerciseType.TRACING, {"glyph": glyph, "style": style, "mode": "model"}, {})


def test_contract_defaults_to_guided_capitals():
    validate_exercise_payload(ExerciseType.TRACING, {"glyph": "B"}, {})


@pytest.mark.parametrize(
    "content",
    [
        {"glyph": "a", "style": "capitale"},
        {"glyph": "A", "style": "script"},
        {"glyph": "é", "style": "cursive"},
        {"glyph": "AB"},
        {"glyph": "A", "mode": "dictée"},
        {"glyph": "A", "style": "gothique"},
    ],
)
def test_contract_rejects_unknown_glyphs_styles_and_modes(content: dict):
    with pytest.raises(ValueError):
        validate_exercise_payload(ExerciseType.TRACING, content, {})


def test_contract_rejects_a_stored_answer():
    with pytest.raises(ValueError, match="correct_answer"):
        validate_exercise_payload(ExerciseType.TRACING, {"glyph": "A"}, {"ok": True})


def test_grading_uses_the_ink():
    exercise = tracing_exercise("A")
    assert check_answer_correctness(exercise, {"strokes": reference("capitale", "A")}) is True
    assert check_answer_correctness(exercise, {"strokes": reference("capitale", "O")}) is False


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"ok": True},
        {"strokes": "A"},
        {"strokes": [[["x", 1]]]},
        {"strokes": [[[math.nan, 1], [2, 3]]]},
        {"strokes": [[[1e9, 1], [2, 3]]]},
        {"strokes": [[[1, 2]] * 5000]},
        {"strokes": [[[1, 2], [3, 4]]] * 100},
    ],
)
def test_grading_refuses_malformed_or_oversized_ink(answer: dict):
    assert check_answer_correctness(tracing_exercise("A"), answer) is False


# --------------------------------------------------------------------------- #
# Catalogue servi au client et validateur de packs
# --------------------------------------------------------------------------- #
def test_catalogue_lists_every_glyph_with_its_lines():
    catalogue = glyph_catalogue()
    assert set(catalogue) == set(GLYPHS)
    for style, entry in catalogue.items():
        assert entry["lines"] == [{"y": y, "role": role} for y, role in METRICS[style]]
        assert set(entry["glyphs"]) == set(GLYPHS[style])
    assert len(catalogue["capitale"]["glyphs"]["A"]) == 3


def test_catalogue_endpoint_is_public(client: TestClient):
    response = client.get("/api/v1/exercises/tracing/glyphs")
    assert response.status_code == 200, response.text
    assert set(response.json()) == {"capitale", "chiffre", "script", "cursive"}


def tracing_item(glyph: str = "A", style: str = "capitale") -> dict:
    return {
        "type": "tracing",
        "question": f"Suis les pointillés pour tracer {glyph}.",
        "content": {"glyph": glyph, "style": style, "mode": "guided"},
        "correct_answer": {},
        "difficulty_level": 1,
    }


def test_pack_accepts_tracing_for_young_children():
    document = pack(
        lessons=[
            lesson(level="gs", slug="francais", exercises=[tracing_item("a", "script"), mcq()]),
            lesson(name="Suite", tier=2, level="cp", slug="francais", exercises=[tracing_item("l", "cursive"), mcq()]),
        ]
    )
    _, issues, _ = validate_pack(document)
    assert "tracing_level" not in codes(issues)


def test_pack_warns_about_tracing_after_cp():
    document = pack(lessons=[lesson(slug="francais", exercises=[tracing_item(), mcq()]), lesson(name="Suite", tier=2)])
    _, issues, _ = validate_pack(document)
    assert "tracing_level" in codes(issues)
