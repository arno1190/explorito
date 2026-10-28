"""
Tests de l'exercice de lecture de notes (portée musicale) : contrat et correction.
"""

import pytest

from app.api.exercises import check_answer_correctness
from app.models.content import Exercise, ExerciseType
from app.schemas.exercise import note_name, staff_step, validate_exercise_payload


def _exercise(pitch: str, name: str, clef: str = "sol", mode: str = "name") -> Exercise:
    return Exercise(
        type=ExerciseType.MUSIC_NOTE.value,
        question="Quelle est cette note ?",
        content={"clef": clef, "mode": mode, "pitch": pitch},
        correct_answer={"name": name},
    )


def test_note_name_and_staff_step():
    assert note_name("G4") == "sol"
    assert note_name("C4") == "do"
    # Clé de sol : la 1re ligne (en bas) est mi4, le sol est sur la 2e ligne.
    assert staff_step("sol", "E4") == 0
    assert staff_step("sol", "G4") == 2
    assert staff_step("sol", "C4") == -2  # do sur la ligne supplémentaire du bas
    # Clé d'ut 3e ligne (alto) : le do du milieu (C4) est sur la 3e ligne.
    assert staff_step("ut3", "C4") == 4
    assert staff_step("ut3", "F3") == 0
    assert staff_step("ut3", "C3") == -3  # corde de do de l'alto, sous une ligne supplémentaire


def test_music_note_contract_ok():
    validate_exercise_payload(ExerciseType.MUSIC_NOTE, {"clef": "sol", "mode": "name", "pitch": "G4"}, {"name": "sol"})
    validate_exercise_payload(
        ExerciseType.MUSIC_NOTE,
        {"clef": "ut3", "mode": "place", "pitch": "C4", "choices": ["do", "ré", "si"]},
        {"name": "do"},
    )


def test_music_note_contract_rejects_name_mismatch():
    with pytest.raises(ValueError, match="content.pitch"):
        validate_exercise_payload(ExerciseType.MUSIC_NOTE, {"clef": "sol", "pitch": "G4"}, {"name": "la"})


def test_music_note_contract_rejects_off_staff_pitch():
    with pytest.raises(ValueError, match="portée"):
        validate_exercise_payload(ExerciseType.MUSIC_NOTE, {"clef": "sol", "pitch": "C3"}, {"name": "do"})


def test_music_note_contract_rejects_choices_without_answer():
    with pytest.raises(ValueError, match="choices"):
        validate_exercise_payload(
            ExerciseType.MUSIC_NOTE, {"clef": "sol", "pitch": "G4", "choices": ["la", "si"]}, {"name": "sol"}
        )


def test_music_note_contract_rejects_bad_clef():
    with pytest.raises(ValueError):
        validate_exercise_payload(ExerciseType.MUSIC_NOTE, {"clef": "ut4", "pitch": "G4"}, {"name": "sol"})


def test_music_note_grading():
    ex = _exercise("D4", "ré")
    assert check_answer_correctness(ex, {"name": "ré"}) is True
    # tolère l'absence d'accent et la casse (saisie ou bouton)
    assert check_answer_correctness(ex, {"name": "Re"}) is True
    assert check_answer_correctness(ex, {"name": "mi"}) is False
    assert check_answer_correctness(ex, {}) is False


def test_music_note_place_grading_accepts_any_octave():
    # En mode « place », poser un sol sur n'importe quel sol de la portée est juste.
    ex = _exercise("G4", "sol", mode="place")
    assert check_answer_correctness(ex, {"name": "sol"}) is True
    assert check_answer_correctness(ex, {"name": "fa"}) is False
