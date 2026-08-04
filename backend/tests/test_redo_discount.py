"""
Tests de l'XP décoté au redo (issue #4).

- première réussite au premier essai  -> plein tarif
- première réussite après un échec     -> tarif réduit (XP_REDO_DISCOUNT)
- exercice déjà réussi                 -> 0 (anti-farm)
- rejouer une leçon déjà terminée      -> ~0 (pas de re-bonus)

Modèle d'auth : on s'authentifie en parent et on incarne l'enfant
(``X-Acting-Child-Id``) via les helpers de tests.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import (
    DifficultyEnum,
    Exercise,
    LearningPath,
    Lesson,
    LevelEnum,
    Subject,
)
from tests.helpers import child_headers, make_child


def _mcq(lesson_id, order_index: int) -> Exercise:
    return Exercise(
        lesson_id=lesson_id,
        type="multiple_choice",
        question="q?",
        content={"options": [{"id": "a", "text": "ok"}, {"id": "b", "text": "no"}], "multiple": False},
        correct_answer={"option_ids": ["a"]},
        order_index=order_index,
        difficulty=DifficultyEnum.EASY,
    )


def _seed_lesson(db: Session, n_exercises: int, xp_reward: int) -> tuple[Lesson, list[Exercise]]:
    subject = Subject(name="Maths", slug="maths")
    db.add(subject)
    db.flush()
    path = LearningPath(subject_id=subject.id, name="Calcul", level=LevelEnum.CP)
    db.add(path)
    db.flush()
    lesson = Lesson(path_id=path.id, name="Leçon", order_index=1, xp_reward=xp_reward, is_published=True)
    db.add(lesson)
    db.flush()
    exercises = [_mcq(lesson.id, i) for i in range(n_exercises)]
    db.add_all(exercises)
    db.commit()
    db.refresh(lesson)
    for e in exercises:
        db.refresh(e)
    return lesson, exercises


def _submit(client: TestClient, ex_id, correct: bool, h: dict[str, str]) -> dict:
    ans = {"option_ids": ["a"] if correct else ["b"]}
    r = client.post(f"/api/v1/exercises/{ex_id}/submit", json={"answer": ans}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def test_first_correct_full_then_redo_zero(client: TestClient, db_session: Session):
    child = make_child(db_session, name="A")
    _lesson, exercises = _seed_lesson(db_session, n_exercises=2, xp_reward=0)
    e1 = exercises[0]
    h = child_headers(client, child)

    first = _submit(client, e1.id, True, h)
    assert first["xp_awarded"] == settings.XP_PER_EXERCISE

    redo = _submit(client, e1.id, True, h)
    assert redo["xp_awarded"] == 0  # déjà réussi -> anti-farm


def test_missed_then_redo_is_discounted(client: TestClient, db_session: Session):
    child = make_child(db_session, name="B")
    _lesson, exercises = _seed_lesson(db_session, n_exercises=2, xp_reward=0)
    e1, e2 = exercises
    h = child_headers(client, child)

    assert _submit(client, e1.id, True, h)["xp_awarded"] == settings.XP_PER_EXERCISE
    assert _submit(client, e2.id, False, h)["xp_awarded"] == 0  # raté

    # Redo de e2 : première réussite mais après échec -> tarif réduit.
    expected_discount = int(settings.XP_PER_EXERCISE * settings.XP_REDO_DISCOUNT)
    redo = _submit(client, e2.id, True, h)
    assert redo["xp_awarded"] == expected_discount
    # La leçon se termine ici (tous corrects) ; xp_reward=0 donc pas de bonus.
    assert redo["lesson_completed"] is True

    # e1 déjà réussi -> 0.
    assert _submit(client, e1.id, True, h)["xp_awarded"] == 0


def test_replaying_completed_lesson_awards_zero(client: TestClient, db_session: Session):
    child = make_child(db_session, name="C")
    _lesson, exercises = _seed_lesson(db_session, n_exercises=2, xp_reward=50)
    e1, e2 = exercises
    h = child_headers(client, child)

    assert _submit(client, e1.id, True, h)["xp_awarded"] == settings.XP_PER_EXERCISE
    complete = _submit(client, e2.id, True, h)
    assert complete["lesson_completed"] is True
    # Bonus de leçon désactivé par défaut (issue #6) : seulement l'XP de l'exercice.
    assert complete["xp_awarded"] == settings.XP_PER_EXERCISE

    # Rejouer entièrement -> plus rien (exos déjà réussis, bonus non répété).
    assert _submit(client, e1.id, True, h)["xp_awarded"] == 0
    replay = _submit(client, e2.id, True, h)
    assert replay["xp_awarded"] == 0
    assert replay["lesson_completed"] is False  # déjà terminée, pas de re-complétion
