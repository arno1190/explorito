"""Tests du validateur `.explorito` : refus durs, avertissements, drapeaux.

Le validateur étant l'unique porte d'entrée du contenu, ces tests décrivent le
contrat que les trois chemins d'ingestion partagent (envoi parent, jeton
d'écriture, seeder ``--pack``).
"""

from typing import Any

import pytest

from app.core.config import settings
from app.services.pack_format import PackRejected, validate_pack


def mcq(question: str = "Combien font 2 + 2 ?", difficulty_level: int | None = 1) -> dict[str, Any]:
    """QCM valide à deux options."""
    exercise: dict[str, Any] = {
        "type": "multiple_choice",
        "question": question,
        "content": {"options": [{"id": "a", "text": "4"}, {"id": "b", "text": "5"}], "multiple": False},
        "correct_answer": {"option_ids": ["a"]},
    }
    if difficulty_level is not None:
        exercise["difficulty_level"] = difficulty_level
    return exercise


def problem(
    question: str = "Léa possède 5 billes et en donne 2 à Tom. Combien lui en reste-t-il ?",
    value: float = 3,
    difficulty_level: int = 3,
) -> dict[str, Any]:
    """Problème à réponse numérique valide."""
    return {
        "type": "math_problem",
        "question": question,
        "content": {},
        "correct_answer": {"value": value},
        "difficulty_level": difficulty_level,
    }


def lesson(
    name: str = "Additions faciles",
    exercises: list[dict[str, Any]] | None = None,
    level: str = "ce1",
    tier: int = 1,
    slug: str = "maths",
) -> dict[str, Any]:
    """Leçon valide d'un pack."""
    return {
        "subject_slug": slug,
        "level": level,
        "tier": tier,
        "name": name,
        "description": "Une petite série pour commencer en douceur.",
        "exercises": exercises if exercises is not None else [mcq(), problem()],
    }


def pack(lessons: list[dict[str, Any]] | None = None, **overrides: Any) -> dict[str, Any]:
    """Document `.explorito` valide, surchargeable clé par clé."""
    document: dict[str, Any] = {
        "format_version": settings.PACK_FORMAT_VERSION,
        "pack": {
            "title": "Coupe du Monde",
            "emoji": "⚽",
            "description": "Des maths et du français autour du football.",
            "tags": ["sport", "football"],
        },
        "lessons": lessons
        if lessons is not None
        else [
            lesson(),
            lesson(
                name="Additions difficiles", tier=2, exercises=[mcq(difficulty_level=4), problem(difficulty_level=5)]
            ),
        ],
        "self_check": {"math_verified": True, "notes": "Tous les calculs refaits à la main."},
    }
    document.update(overrides)
    return document


def codes(issues: list[Any]) -> set[str]:
    """Codes des constats, pour des assertions lisibles."""
    return {issue.code for issue in issues}


def test_valid_pack_passes_with_high_score():
    payload, issues, score = validate_pack(pack())

    assert [error for error in issues if error.severity == "error"] == []
    assert score == 100
    assert len(payload["lessons"]) == 2
    assert payload["lessons"][0]["exercises"][0]["difficulty_level"] == 1
    # L'ordre des exercices est réattribué par le validateur : la position en
    # base ne dépend pas d'un champ que l'auteur pourrait oublier.
    assert [exercise["order_index"] for exercise in payload["lessons"][0]["exercises"]] == [0, 1]


def test_unknown_format_version_is_refused_cleanly():
    with pytest.raises(PackRejected) as excinfo:
        validate_pack(pack(format_version=99))

    issues = excinfo.value.issues
    # Un seul constat : inutile de commenter le reste du fichier avec les règles
    # d'une version dont on ne sait rien.
    assert codes(issues) == {"format_version_unknown"}
    assert str(settings.PACK_FORMAT_VERSION) in issues[0].message
    assert issues[0].field == "format_version"


def test_missing_format_version_is_refused():
    document = pack()
    del document["format_version"]
    with pytest.raises(PackRejected) as excinfo:
        validate_pack(document)
    assert codes(excinfo.value.issues) == {"format_version_unknown"}


def test_missing_difficulty_level_names_the_offending_indices():
    faulty = pack(
        lessons=[
            lesson(),
            lesson(name="Deuxième leçon", exercises=[mcq(), mcq(question="Et 3 + 3 ?", difficulty_level=None)]),
        ]
    )

    with pytest.raises(PackRejected) as excinfo:
        validate_pack(faulty)

    missing = [issue for issue in excinfo.value.issues if issue.code == "difficulty_level_missing"]
    assert len(missing) == 1
    assert (missing[0].lesson_index, missing[0].exercise_index) == (1, 1)
    assert missing[0].field == "difficulty_level"
    # Le message doit désigner l'élément fautif ET l'action corrective : c'est ce
    # que relit l'IA du parent pour corriger son fichier.
    assert "leçon 2, exercice 2" in missing[0].message
    assert "difficulty_level" in missing[0].message


def test_lesson_dump_is_refused_by_the_caps():
    with pytest.raises(PackRejected) as excinfo:
        validate_pack(pack(lessons=[lesson(name=f"Leçon {index}") for index in range(500)]))

    issues = excinfo.value.issues
    assert "too_many_lessons" in codes(issues)
    too_many = next(issue for issue in issues if issue.code == "too_many_lessons")
    assert str(settings.PACK_MAX_LESSONS) in too_many.message


def test_too_many_exercises_per_lesson_is_refused():
    with pytest.raises(PackRejected) as excinfo:
        validate_pack(
            pack(
                lessons=[
                    lesson(
                        exercises=[
                            mcq(question=f"Question {index} ?")
                            for index in range(settings.PACK_MAX_EXERCISES_PER_LESSON + 3)
                        ]
                    )
                ]
            )
        )
    assert "too_many_exercises" in codes(excinfo.value.issues)


def test_text_longer_than_the_cap_is_refused():
    with pytest.raises(PackRejected) as excinfo:
        validate_pack(pack(lessons=[lesson(exercises=[mcq(question="a" * (settings.PACK_MAX_TEXT_LENGTH + 1))])]))
    assert "text_too_long" in codes(excinfo.value.issues)


def test_unknown_subject_and_level_are_refused_with_the_accepted_values():
    with pytest.raises(PackRejected) as excinfo:
        validate_pack(pack(lessons=[lesson(slug="quantique", level="terminale")]))

    issues = excinfo.value.issues
    assert {"subject_unknown", "level_unknown"} <= codes(issues)
    subject_issue = next(issue for issue in issues if issue.code == "subject_unknown")
    assert "maths" in subject_issue.message
    level_issue = next(issue for issue in issues if issue.code == "level_unknown")
    assert "ce1" in level_issue.message


def test_broken_exercise_shape_is_refused_by_the_shared_contract():
    broken = mcq()
    broken["correct_answer"] = {"option_ids": ["z"]}
    with pytest.raises(PackRejected) as excinfo:
        validate_pack(pack(lessons=[lesson(exercises=[broken])]))

    shape = next(issue for issue in excinfo.value.issues if issue.code == "exercise_shape")
    assert shape.lesson_index == 0 and shape.exercise_index == 0


def test_english_text_is_refused_but_short_math_strings_are_not():
    english = "How many marbles does Lea have left after giving two of them away?"
    with pytest.raises(PackRejected) as excinfo:
        validate_pack(pack(lessons=[lesson(exercises=[problem(question=english)])]))
    assert "not_french" in codes(excinfo.value.issues)

    # « 3 + 4 = ? » n'est pas du non-français : c'est du texte trop court pour
    # qu'une détection ait un sens. Un refus ici serait un faux positif garanti.
    _, issues, _ = validate_pack(pack(lessons=[lesson(exercises=[mcq(question="3 + 4 = ?"), problem()])]))
    assert "not_french" not in codes(issues)


def test_declared_xp_never_survives_normalisation():
    money_printer = pack(
        lessons=[
            lesson(
                name="Leçon très rentable",
                exercises=[mcq(question=f"Question facile {index} ?", difficulty_level=5) for index in range(15)],
            )
        ]
    )
    money_printer["pack"]["xp_reward"] = 99999
    money_printer["lessons"][0]["xp_reward"] = 99999
    money_printer["lessons"][0]["exercises"][0]["xp_reward"] = 99999

    payload, issues, _ = validate_pack(money_printer)

    assert "xp_reward" not in payload["pack"]
    assert "xp_reward" not in payload["lessons"][0]
    assert all("xp_reward" not in exercise for exercise in payload["lessons"][0]["exercises"])
    # L'auteur est prévenu que le champ est ignoré : c'est un avertissement, pas
    # un refus (le fichier reste ingérable tel quel).
    assert "xp_ignored" in codes(issues)


def test_profanity_and_near_duplicates_only_flag():
    rude = pack(
        lessons=[
            lesson(
                name="Les gros mots", exercises=[mcq(question="Pourquoi « merde » est-il un gros mot ?"), problem()]
            ),
            lesson(name="Les gros mots", tier=2, exercises=[mcq(question="Pourquoi « merde » est-il un gros mot ?")]),
        ]
    )

    payload, issues, score = validate_pack(rude)

    assert payload["lessons"][1]["name"] == "Les gros mots"
    flags = {issue.code for issue in issues if issue.severity == "flag"}
    assert flags == {"profanity", "near_duplicate"}
    # Un drapeau annote, il ne pénalise même pas le score.
    assert score == 100


def test_score_drops_for_a_flat_difficulty_curve_and_a_single_type():
    flat = pack(
        lessons=[
            lesson(exercises=[mcq(question=f"Combien font {index} + 1 ?") for index in range(6)]),
            lesson(name="Encore des QCM", tier=2, exercises=[mcq(question=f"Et {index} + 2 ?") for index in range(6)]),
        ]
    )

    _, issues, score = validate_pack(flat)

    assert {"flat_difficulty", "no_type_mix"} <= codes(issues)
    assert score == 70


def test_single_lesson_pack_and_missing_self_check_are_warnings():
    document = pack(lessons=[lesson()])
    del document["self_check"]

    _, issues, score = validate_pack(document)

    assert {"single_lesson", "self_check_missing"} <= codes(issues)
    assert score == 85
    assert all(issue.severity != "error" for issue in issues)


def test_text_too_long_for_the_declared_level_is_a_warning():
    verbose = "Dans la cour de récréation, " + "les enfants comptent leurs billes ensemble, " * 3 + "combien ?"
    _, issues, score = validate_pack(
        pack(lessons=[lesson(level="cp", exercises=[problem(question=verbose), mcq()]), lesson(name="Suite", tier=2)])
    )

    assert "text_too_long_for_level" in codes(issues)
    assert score == 90


def test_known_subject_slugs_can_be_widened_by_the_caller():
    document = pack(lessons=[lesson(slug="astronomie")])
    with pytest.raises(PackRejected):
        validate_pack(document)

    payload, _, _ = validate_pack(document, known_subject_slugs={"astronomie"})
    assert payload["lessons"][0]["subject_slug"] == "astronomie"
