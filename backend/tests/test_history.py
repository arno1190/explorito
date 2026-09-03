"""
Tests de l'historique de progression d'un enfant (parent-facing) :
activité quotidienne, frise des leçons, journal des erreurs, réussite/matière.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import DifficultyEnum, Exercise, Lesson, LevelEnum, Subject
from tests.helpers import child_headers, dev_login, make_child, make_lesson, make_pack, make_subject


def _mcq(lesson_id, order_index: int) -> Exercise:
    return Exercise(
        lesson_id=lesson_id,
        type="multiple_choice",
        question=f"question {order_index} ?",
        content={"options": [{"id": "a", "text": "ok"}, {"id": "b", "text": "no"}], "multiple": False},
        correct_answer={"option_ids": ["a"]},
        order_index=order_index,
        difficulty=DifficultyEnum.EASY,
    )


def _seed_lesson(db: Session) -> tuple[Subject, Lesson, list[Exercise]]:
    subject = make_subject(db, name="Maths", slug="maths", icon="🌋")
    pack = make_pack(db, title="Additions CP", level=LevelEnum.CP)
    lesson = make_lesson(db, pack=pack, subject=subject, level=LevelEnum.CP, tier=1, name="Additions")
    lesson.xp_reward = 50
    db.flush()
    exercises = [_mcq(lesson.id, 0), _mcq(lesson.id, 1)]
    db.add_all(exercises)
    db.commit()
    for o in (subject, lesson, *exercises):
        db.refresh(o)
    return subject, lesson, exercises


def test_history_captures_lessons_errors_and_daily(client: TestClient, db_session: Session):
    child = make_child(db_session, level=LevelEnum.CP)
    subject, lesson, (e1, e2) = _seed_lesson(db_session)
    h = child_headers(client, child)  # parent propriétaire incarnant l'enfant

    # un exercice réussi, un raté
    client.post(f"/api/v1/exercises/{e1.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)
    client.post(f"/api/v1/exercises/{e2.id}/submit", json={"answer": {"option_ids": ["b"]}}, headers=h)

    r = client.get(f"/api/v1/gamification/{child.id}/history", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()

    # frise des leçons
    assert any(lz["lesson_name"] == "Additions" and lz["subject_name"] == "Maths" for lz in body["lessons"])
    # journal des erreurs contient l'exercice raté
    assert any(err["question"] == "question 1 ?" for err in body["errors"])
    # activité quotidienne : au moins 2 exercices, 1 correct, 1 faux
    assert body["daily"], body
    today = body["daily"][-1]
    assert today["exercises"] >= 2
    assert today["correct"] >= 1 and today["wrong"] >= 1
    # réussite par matière
    maths = next(s for s in body["by_subject"] if s["subject_name"] == "Maths")
    assert maths["attempts"] >= 2
    assert 0 <= maths["accuracy"] <= 100


def test_history_access_control(client: TestClient, db_session: Session):
    child = make_child(db_session, level=LevelEnum.CP)  # rattaché au parent par défaut

    # le parent propriétaire y accède
    owner = dev_login(client)
    assert client.get(f"/api/v1/gamification/{child.id}/history", headers=owner).status_code == 200
    # un autre parent : non
    stranger = dev_login(client, "stranger@qa.fr")
    assert client.get(f"/api/v1/gamification/{child.id}/history", headers=stranger).status_code == 404
