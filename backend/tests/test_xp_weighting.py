"""
Tests de la pondération de l'XP par difficulté et du bonus de leçon (issue #6).

- Un exercice de niveau élevé rapporte plus (XP_BY_LEVEL) ; le redo reste décoté.
- L'ancienne difficulté (easy/medium/hard) sert de repli si difficulty_level
  n'est pas renseigné (XP_BY_DIFFICULTY).
- Le bonus forfaitaire de complétion est désactivé par défaut, réactivable via
  AWARD_LESSON_COMPLETION_BONUS.

Auth : parent incarnant l'enfant via les helpers de tests.
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


def _mcq(lesson_id, order_index: int, difficulty: DifficultyEnum) -> Exercise:
    return Exercise(
        lesson_id=lesson_id,
        type="multiple_choice",
        question="q?",
        content={"options": [{"id": "a", "text": "ok"}, {"id": "b", "text": "no"}], "multiple": False},
        correct_answer={"option_ids": ["a"]},
        order_index=order_index,
        difficulty=difficulty,
    )


def _seed_lesson(db: Session, difficulties: list[DifficultyEnum], xp_reward: int = 50) -> list[Exercise]:
    subject = Subject(name="Maths", slug="maths")
    db.add(subject)
    db.flush()
    path = LearningPath(subject_id=subject.id, name="Calcul", level=LevelEnum.CP)
    db.add(path)
    db.flush()
    lesson = Lesson(path_id=path.id, name="Leçon", order_index=1, xp_reward=xp_reward, is_published=True)
    db.add(lesson)
    db.flush()
    exercises = [_mcq(lesson.id, i, d) for i, d in enumerate(difficulties)]
    db.add_all(exercises)
    db.commit()
    for e in exercises:
        db.refresh(e)
    return exercises


def _seed_level_lesson(db: Session, levels: list[int]) -> list[Exercise]:
    """Leçon dont chaque exercice porte un difficulty_level explicite (1-5)."""
    subject = Subject(name="Maths", slug="maths")
    db.add(subject)
    db.flush()
    path = LearningPath(subject_id=subject.id, name="Calcul", level=LevelEnum.CP)
    db.add(path)
    db.flush()
    lesson = Lesson(path_id=path.id, name="Leçon", order_index=1, xp_reward=0, is_published=True)
    db.add(lesson)
    db.flush()
    exercises = [_mcq(lesson.id, i, DifficultyEnum.EASY) for i in range(len(levels))]
    for e, lvl in zip(exercises, levels, strict=True):
        e.difficulty_level = lvl
    db.add_all(exercises)
    db.commit()
    for e in exercises:
        db.refresh(e)
    return exercises


def _submit(client: TestClient, ex_id, correct: bool, h: dict[str, str]) -> dict:
    ans = {"option_ids": ["a"] if correct else ["b"]}
    r = client.post(f"/api/v1/exercises/{ex_id}/submit", json={"answer": ans}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def test_xp_scales_with_difficulty(client: TestClient, db_session: Session):
    child = make_child(db_session, name="W1")
    easy, medium, hard = _seed_lesson(db_session, [DifficultyEnum.EASY, DifficultyEnum.MEDIUM, DifficultyEnum.HARD])
    h = child_headers(client, child)

    assert _submit(client, easy.id, True, h)["xp_awarded"] == settings.XP_BY_DIFFICULTY["easy"]
    assert _submit(client, medium.id, True, h)["xp_awarded"] == settings.XP_BY_DIFFICULTY["medium"]
    assert _submit(client, hard.id, True, h)["xp_awarded"] == settings.XP_BY_DIFFICULTY["hard"]


def test_redo_discount_uses_weighted_base(client: TestClient, db_session: Session):
    child = make_child(db_session, name="W2")
    (hard,) = _seed_lesson(db_session, [DifficultyEnum.HARD])
    h = child_headers(client, child)

    # Rater d'abord, puis réussir : tarif réduit calculé sur la base « hard ».
    assert _submit(client, hard.id, False, h)["xp_awarded"] == 0
    expected = int(settings.XP_BY_DIFFICULTY["hard"] * settings.XP_REDO_DISCOUNT)
    assert _submit(client, hard.id, True, h)["xp_awarded"] == expected


def test_completion_bonus_off_by_default(client: TestClient, db_session: Session):
    child = make_child(db_session, name="W3")
    (only,) = _seed_lesson(db_session, [DifficultyEnum.EASY], xp_reward=50)
    h = child_headers(client, child)

    body = _submit(client, only.id, True, h)
    assert body["lesson_completed"] is True
    # Aucun bonus forfaitaire : uniquement l'XP de l'exercice.
    assert body["xp_awarded"] == settings.XP_BY_DIFFICULTY["easy"]


def test_difficulty_level_drives_xp(client: TestClient, db_session: Session):
    child = make_child(db_session, name="W5")
    exercises = _seed_level_lesson(db_session, [1, 3, 5])
    h = child_headers(client, child)

    for ex, level in zip(exercises, [1, 3, 5], strict=True):
        assert _submit(client, ex.id, True, h)["xp_awarded"] == settings.XP_BY_LEVEL[level]


def test_difficulty_level_takes_priority_over_enum(client: TestClient, db_session: Session):
    # Enum = EASY (10) mais difficulty_level = 4 -> l'XP suit le niveau fin (25).
    child = make_child(db_session, name="W6")
    (ex,) = _seed_level_lesson(db_session, [4])
    assert ex.difficulty == DifficultyEnum.EASY
    h = child_headers(client, child)
    assert _submit(client, ex.id, True, h)["xp_awarded"] == settings.XP_BY_LEVEL[4]


def test_completion_bonus_awarded_when_enabled(client: TestClient, db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "AWARD_LESSON_COMPLETION_BONUS", True)
    child = make_child(db_session, name="W4")
    (only,) = _seed_lesson(db_session, [DifficultyEnum.EASY], xp_reward=50)
    h = child_headers(client, child)

    body = _submit(client, only.id, True, h)
    assert body["lesson_completed"] is True
    # Exercice (easy) + bonus forfaitaire réactivé.
    assert body["xp_awarded"] == settings.XP_BY_DIFFICULTY["easy"] + 50
