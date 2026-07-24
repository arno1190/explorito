"""
Tests unitaires de la correction (``check_answer_correctness``) pour le jeu de
types canonique : multiple_choice, fill_blanks, reveal, pythagore.
"""

from types import SimpleNamespace

import pytest

from app.api.exercises import check_answer_correctness


def _exercise(exercise_type: str, correct_answer: dict) -> SimpleNamespace:
    """Fabrique un exercice minimal pour la correction (type + correct_answer)."""
    return SimpleNamespace(type=exercise_type, correct_answer=correct_answer)


# --- multiple_choice ---------------------------------------------------------
def test_mcq_correct_single():
    ex = _exercise("multiple_choice", {"option_ids": ["a"]})
    assert check_answer_correctness(ex, {"option_ids": ["a"]}) is True


def test_mcq_wrong_single():
    ex = _exercise("multiple_choice", {"option_ids": ["a"]})
    assert check_answer_correctness(ex, {"option_ids": ["b"]}) is False


def test_mcq_multiple_order_insensitive():
    ex = _exercise("multiple_choice", {"option_ids": ["a", "c"]})
    assert check_answer_correctness(ex, {"option_ids": ["c", "a"]}) is True


def test_mcq_multiple_missing_one():
    ex = _exercise("multiple_choice", {"option_ids": ["a", "c"]})
    assert check_answer_correctness(ex, {"option_ids": ["a"]}) is False


def test_mcq_empty_answer():
    ex = _exercise("multiple_choice", {"option_ids": ["a"]})
    assert check_answer_correctness(ex, {"option_ids": []}) is False
    assert check_answer_correctness(ex, {}) is False


# --- fill_blanks -------------------------------------------------------------
def test_fill_correct_case_and_space_insensitive():
    ex = _exercise("fill_blanks", {"blanks": ["Hat"]})
    assert check_answer_correctness(ex, {"blanks": [" hat "]}) is True


def test_fill_multi_blank_ordered():
    ex = _exercise("fill_blanks", {"blanks": ["a", "i"]})
    assert check_answer_correctness(ex, {"blanks": ["a", "i"]}) is True
    assert check_answer_correctness(ex, {"blanks": ["i", "a"]}) is False


def test_fill_length_mismatch():
    ex = _exercise("fill_blanks", {"blanks": ["a", "i"]})
    assert check_answer_correctness(ex, {"blanks": ["a"]}) is False


# --- reveal ------------------------------------------------------------------
def test_reveal_always_correct():
    ex = _exercise("reveal", {})
    assert check_answer_correctness(ex, {}) is True
    assert check_answer_correctness(ex, {"anything": "x"}) is True


# --- pythagore ---------------------------------------------------------------
def test_pythagore_all_cells_correct():
    ex = _exercise("pythagore", {})
    assert check_answer_correctness(ex, {"cells": {"3x4": 12, "2x5": 10}}) is True


def test_pythagore_one_cell_wrong():
    ex = _exercise("pythagore", {})
    assert check_answer_correctness(ex, {"cells": {"3x4": 12, "2x5": 11}}) is False


def test_pythagore_empty():
    ex = _exercise("pythagore", {})
    assert check_answer_correctness(ex, {"cells": {}}) is False
    assert check_answer_correctness(ex, {}) is False


def test_pythagore_malformed_key():
    ex = _exercise("pythagore", {})
    assert check_answer_correctness(ex, {"cells": {"bad": 12}}) is False


# --- math_problem ------------------------------------------------------------
def test_math_problem_exact():
    ex = _exercise("math_problem", {"value": 12})
    assert check_answer_correctness(ex, {"value": 12}) is True
    assert check_answer_correctness(ex, {"value": 13}) is False


def test_math_problem_accepts_comma_decimal():
    ex = _exercise("math_problem", {"value": 12.5})
    assert check_answer_correctness(ex, {"value": "12,5"}) is True
    assert check_answer_correctness(ex, {"value": "12.5"}) is True


def test_math_problem_tolerance():
    ex = _exercise("math_problem", {"value": 3.14, "tolerance": 0.01})
    assert check_answer_correctness(ex, {"value": 3.15}) is True
    assert check_answer_correctness(ex, {"value": 3.2}) is False


def test_math_problem_non_numeric():
    ex = _exercise("math_problem", {"value": 5})
    assert check_answer_correctness(ex, {"value": "cinq"}) is False
    assert check_answer_correctness(ex, {}) is False


# --- reading -----------------------------------------------------------------
def test_reading_always_correct():
    ex = _exercise("reading", {})
    assert check_answer_correctness(ex, {"read": True}) is True
    assert check_answer_correctness(ex, {}) is True


# --- type inconnu ------------------------------------------------------------
@pytest.mark.parametrize("legacy", ["mcq", "drag_drop", "true_false", "unknown"])
def test_unknown_type_rejected(legacy: str):
    ex = _exercise(legacy, {"option_ids": ["a"]})
    assert check_answer_correctness(ex, {"option_ids": ["a"]}) is False
