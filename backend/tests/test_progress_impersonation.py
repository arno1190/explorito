"""
Régression : les endpoints de progression « self-serve » doivent suivre
l'enfant incarné (X-Acting-Child-Id), pas le parent authentifié.

Sinon, un parent qui « joue comme » son enfant voit une progression vide
(bug : aucune leçon terminée).
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import Exercise, Lesson, LevelEnum
from tests.helpers import (
    child_headers,
    dev_login,
    make_child,
    make_exercise,
    make_lesson,
    make_pack,
    make_subject,
)


def _seed_lesson(db: Session) -> tuple[Lesson, Exercise]:
    subject = make_subject(db, name="Maths", slug="maths")
    pack = make_pack(db, title="Calcul CP", level=LevelEnum.CP)
    lesson = make_lesson(db, pack=pack, subject=subject, level=LevelEnum.CP, tier=1, name="Additions")
    ex = make_exercise(db, lesson=lesson, question="1+1?")
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
    subject = make_subject(db_session, name="Maths", slug="maths")
    pack = make_pack(db_session, title="Calcul CP", level=LevelEnum.CP)
    l1 = make_lesson(db_session, pack=pack, subject=subject, level=LevelEnum.CP, tier=1, name="P1")
    make_lesson(db_session, pack=pack, subject=subject, level=LevelEnum.CP, tier=2, name="P2")
    e1 = make_exercise(db_session, lesson=l1, question="1+1?")
    db_session.commit()

    child = make_child(db_session, level=LevelEnum.CP)
    h = child_headers(client, child)
    client.post(f"/api/v1/exercises/{e1.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)

    overview = client.get("/api/v1/progress/subjects-overview", headers=h)
    assert overview.status_code == 200, overview.text
    by_id = {o["subject_id"]: o for o in overview.json()}
    assert by_id[str(subject.id)]["total_lessons"] == 2
    assert by_id[str(subject.id)]["completed_lessons"] == 1
