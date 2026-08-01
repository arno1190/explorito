"""
Tests de l'historique de progression d'un enfant (parent-facing) :
activité quotidienne, frise des leçons, journal des erreurs, réussite/matière.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.content import DifficultyEnum, Exercise, LearningPath, Lesson, LevelEnum, Subject
from app.models.user import Profile, User, UserRole


def _make_user(db: Session, email: str, role: UserRole, level: LevelEnum | None = None) -> User:
    user = User(email=email, password_hash=get_password_hash("SecurePass123"), role=role, is_active=True)
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, display_name=email.split("@")[0], is_child=(role == UserRole.CHILD), level=level))
    db.commit()
    db.refresh(user)
    return user


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
    subject = Subject(name="Maths", slug="maths", icon="🌋")
    db.add(subject)
    db.flush()
    path = LearningPath(subject_id=subject.id, name="Calcul", level=LevelEnum.CP)
    db.add(path)
    db.flush()
    lesson = Lesson(path_id=path.id, name="Additions", order_index=1, xp_reward=50, is_published=True)
    db.add(lesson)
    db.flush()
    exercises = [_mcq(lesson.id, 0), _mcq(lesson.id, 1)]
    db.add_all(exercises)
    db.commit()
    for o in (subject, lesson, *exercises):
        db.refresh(o)
    return subject, lesson, exercises


def _auth(client: TestClient, email: str) -> dict[str, str]:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_history_captures_lessons_errors_and_daily(client: TestClient, db_session: Session):
    child = _make_user(db_session, "kid@x.fr", UserRole.CHILD, level=LevelEnum.CP)
    subject, lesson, (e1, e2) = _seed_lesson(db_session)
    h = _auth(client, "kid@x.fr")

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
    parent = _make_user(db_session, "papa@x.fr", UserRole.PARENT)
    child = _make_user(db_session, "kid2@x.fr", UserRole.CHILD, level=LevelEnum.CP)
    prof = db_session.query(Profile).filter(Profile.user_id == child.id).first()
    prof.parent_id = parent.id
    db_session.commit()
    _make_user(db_session, "stranger@x.fr", UserRole.PARENT)

    # le parent propriétaire y accède
    assert client.get(f"/api/v1/gamification/{child.id}/history", headers=_auth(client, "papa@x.fr")).status_code == 200
    # un autre parent : non
    assert (
        client.get(f"/api/v1/gamification/{child.id}/history", headers=_auth(client, "stranger@x.fr")).status_code
        == 404
    )
