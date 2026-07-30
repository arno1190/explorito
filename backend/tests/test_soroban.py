"""
Tests de l'exercice boulier (soroban) : validation du contrat et correction.
"""

import pytest

from app.api.exercises import check_answer_correctness
from app.models.content import Exercise, ExerciseType
from app.schemas.exercise import validate_exercise_payload


def _exercise(value: int, mode: str = "read") -> Exercise:
    return Exercise(
        type=ExerciseType.SOROBAN.value,
        question="Quel nombre ?",
        content={"mode": mode, "value": value, "columns": 2},
        correct_answer={"value": value},
    )


def test_soroban_contract_ok():
    validate_exercise_payload(ExerciseType.SOROBAN, {"mode": "read", "value": 42, "columns": 2}, {"value": 42})
    validate_exercise_payload(ExerciseType.SOROBAN, {"mode": "build", "value": 7}, {"value": 7})


def test_soroban_contract_rejects_answer_value_mismatch():
    with pytest.raises(ValueError, match="content.value"):
        validate_exercise_payload(ExerciseType.SOROBAN, {"mode": "read", "value": 5}, {"value": 6})


def test_soroban_contract_rejects_bad_mode():
    with pytest.raises(ValueError):
        validate_exercise_payload(ExerciseType.SOROBAN, {"mode": "compute", "value": 5}, {"value": 5})


def test_soroban_grading_correct_and_wrong():
    ex = _exercise(42)
    assert check_answer_correctness(ex, {"value": 42}) is True
    assert check_answer_correctness(ex, {"value": 24}) is False
    # accepte une valeur numérique en chaîne
    assert check_answer_correctness(ex, {"value": "42"}) is True
    # réponse manquante / invalide -> faux, pas d'exception
    assert check_answer_correctness(ex, {}) is False
    assert check_answer_correctness(ex, {"value": "abc"}) is False


def test_soroban_build_grading():
    ex = _exercise(7, mode="build")
    assert check_answer_correctness(ex, {"value": 7}) is True
    assert check_answer_correctness(ex, {"value": 8}) is False
