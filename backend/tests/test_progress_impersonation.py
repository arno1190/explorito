"""
Régression : les endpoints de progression « self-serve » doivent suivre
l'enfant incarné (X-Acting-Child-Id), pas le parent authentifié.

Sinon, un parent qui « joue comme » son enfant voit une progression vide
(bug : aucune leçon terminée).
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import (
    DifficultyEnum,
    Exercise,
    LearningPath,
    Lesson,
    LevelEnum,
    Subject,
)
from tests.helpers import child_headers, dev_login, make_child


def _seed_lesson(db: Session) -> tuple[Lesson, Exercise]:
    subject = Subject(name="Maths", slug="maths")
    db.add(subject)
    db.flush()
    path = LearningPath(subject_id=subject.id, name="Calcul", level=LevelEnum.CP)
    db.add(path)
    db.flush()
    lesson = Lesson(path_id=path.id, name="Additions", order_index=1, xp_reward=0, is_published=True)
    db.add(lesson)
    db.flush()
    ex = Exercise(
        lesson_id=lesson.id,
        type="multiple_choice",
        question="1+1?",
        content={"options": [{"id": "a", "text": "2"}, {"id": "b", "text": "3"}], "multiple": False},
        correct_answer={"option_ids": ["a"]},
        order_index=0,
        difficulty=DifficultyEnum.EASY,
    )
    db.add(ex)
    db.commit()
    db.refresh(lesson)
    db.refresh(ex)
    return lesson, ex


def test_completed_exercises_follow_acting_child(client: TestClient, db_session: Session):
    child = make_child(db_session, level=LevelEnum.CP)
    lesson, ex = _seed_lesson(db_session)
    h = child_headers(client, child)  # parent incarnant l'enfant

    # L'enfant (incarné) réussit l'exercice.
    r = client.post(f"/api/v1/exercises/{ex.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["lesson_completed"] is True

    # En mode enfant, la leçon apparaît complétée (endpoint self-serve).
    done = client.get(f"/api/v1/progress/lessons/{lesson.id}/completed-exercises", headers=h)
    assert done.status_code == 200, done.text
    assert str(ex.id) in done.json()

    # Le tableau de bord self-serve reflète la progression de l'enfant.
    me = client.get("/api/v1/progress/me", headers=h).json()
    assert me["total_lessons_completed"] >= 1
    assert me["total_xp"] > 0


def test_progress_empty_for_parent_without_acting(client: TestClient, db_session: Session):
    # Sans en-tête d'incarnation, le parent n'a aucune progression propre.
    child = make_child(db_session, level=LevelEnum.CP)
    lesson, ex = _seed_lesson(db_session)
    h_child = child_headers(client, child)
    client.post(f"/api/v1/exercises/{ex.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h_child)

    h_parent = dev_login(client)  # même parent, mais sans X-Acting-Child-Id
    done = client.get(f"/api/v1/progress/lessons/{lesson.id}/completed-exercises", headers=h_parent)
    assert done.status_code == 200
    assert done.json() == []  # la progression de l'enfant ne fuite pas vers le parent


def test_subjects_overview_counts_completed_for_acting_child(client: TestClient, db_session: Session):
    # Matière avec 2 leçons CP publiées ; l'enfant en termine 1.
    subject = Subject(name="Maths", slug="maths")
    db_session.add(subject)
    db_session.flush()
    path = LearningPath(subject_id=subject.id, name="Calcul", level=LevelEnum.CP)
    db_session.add(path)
    db_session.flush()
    l1 = Lesson(path_id=path.id, name="P1", order_index=1, xp_reward=0, is_published=True)
    l2 = Lesson(path_id=path.id, name="P2", order_index=2, xp_reward=0, is_published=True)
    db_session.add_all([l1, l2])
    db_session.flush()
    e1 = Exercise(
        lesson_id=l1.id,
        type="multiple_choice",
        question="1+1?",
        content={"options": [{"id": "a", "text": "2"}, {"id": "b", "text": "3"}], "multiple": False},
        correct_answer={"option_ids": ["a"]},
        order_index=0,
        difficulty=DifficultyEnum.EASY,
    )
    db_session.add(e1)
    db_session.commit()
    db_session.refresh(e1)

    child = make_child(db_session, level=LevelEnum.CP)
    h = child_headers(client, child)
    client.post(f"/api/v1/exercises/{e1.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)

    overview = client.get("/api/v1/progress/subjects-overview", headers=h)
    assert overview.status_code == 200, overview.text
    by_id = {o["subject_id"]: o for o in overview.json()}
    assert by_id[str(subject.id)]["total_lessons"] == 2
    assert by_id[str(subject.id)]["completed_lessons"] == 1
