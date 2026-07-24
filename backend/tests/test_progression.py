"""
Tests d'intégration de la boucle cœur : soumission d'exercice -> progression,
XP, série, complétion de leçon ; plus le contrôle d'accès (RBAC) sur le CRUD
de contenu.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.content import (
    DifficultyEnum,
    Exercise,
    LearningPath,
    Lesson,
    LevelEnum,
    Subject,
)
from app.models.progress import ProgressStatus, UserProgress
from app.models.user import Profile, User, UserRole


def _make_user(db: Session, email: str, role: UserRole, password: str = "SecurePass123") -> User:
    user = User(email=email, password_hash=get_password_hash(password), role=role, is_active=True)
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, display_name=email.split("@")[0], is_child=(role == UserRole.CHILD)))
    db.commit()
    db.refresh(user)
    return user


def _seed_lesson_with_two_mcq(db: Session) -> tuple[Lesson, list[Exercise]]:
    subject = Subject(name="Maths", slug="maths")
    db.add(subject)
    db.flush()
    path = LearningPath(subject_id=subject.id, name="Calcul", level=LevelEnum.CP)
    db.add(path)
    db.flush()
    lesson = Lesson(path_id=path.id, name="Additions", xp_reward=50, is_published=True)
    db.add(lesson)
    db.flush()
    e1 = Exercise(
        lesson_id=lesson.id,
        type="multiple_choice",
        question="1+1?",
        content={"options": [{"id": "a", "text": "2"}, {"id": "b", "text": "3"}], "multiple": False},
        correct_answer={"option_ids": ["a"]},
        order_index=0,
        difficulty=DifficultyEnum.EASY,
    )
    e2 = Exercise(
        lesson_id=lesson.id,
        type="multiple_choice",
        question="2+2?",
        content={"options": [{"id": "a", "text": "4"}, {"id": "b", "text": "5"}], "multiple": False},
        correct_answer={"option_ids": ["a"]},
        order_index=1,
        difficulty=DifficultyEnum.EASY,
    )
    db.add_all([e1, e2])
    db.commit()
    db.refresh(e1)
    db.refresh(e2)
    return lesson, [e1, e2]


def _login(client: TestClient, email: str, password: str = "SecurePass123") -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_submit_awards_xp_and_completes_lesson(client: TestClient, db_session: Session):
    _make_user(db_session, "kid@x.fr", UserRole.CHILD)
    lesson, (e1, e2) = _seed_lesson_with_two_mcq(db_session)
    token = _login(client, "kid@x.fr")

    # Premier exercice réussi : +10 XP, série 1, leçon pas encore terminée.
    r1 = client.post(
        f"/api/v1/exercises/{e1.id}/submit",
        json={"answer": {"option_ids": ["a"]}, "time_taken": 5},
        headers=_auth(token),
    )
    assert r1.status_code == 201, r1.text
    body1 = r1.json()
    assert body1["is_correct"] is True
    assert body1["xp_awarded"] == 10
    assert body1["current_streak"] == 1
    assert body1["lesson_completed"] is False

    # Second exercice réussi : leçon terminée, 3 étoiles, +10 exo +50 bonus.
    r2 = client.post(
        f"/api/v1/exercises/{e2.id}/submit",
        json={"answer": {"option_ids": ["a"]}, "time_taken": 7},
        headers=_auth(token),
    )
    assert r2.status_code == 201, r2.text
    body2 = r2.json()
    assert body2["is_correct"] is True
    assert body2["lesson_completed"] is True
    assert body2["lesson_stars"] == 3
    assert body2["lesson_score"] == 100
    assert body2["xp_awarded"] == 60
    assert body2["total_xp"] == 70

    # Progression persistée en base.
    progress = db_session.query(UserProgress).filter_by(lesson_id=lesson.id).first()
    assert progress is not None
    assert progress.status == ProgressStatus.COMPLETED
    assert progress.stars == 3
    assert progress.attempts == 2
    assert progress.completed_at is not None


def test_wrong_answer_no_xp(client: TestClient, db_session: Session):
    _make_user(db_session, "kid2@x.fr", UserRole.CHILD)
    _lesson, (e1, _e2) = _seed_lesson_with_two_mcq(db_session)
    token = _login(client, "kid2@x.fr")

    r = client.post(
        f"/api/v1/exercises/{e1.id}/submit",
        json={"answer": {"option_ids": ["b"]}},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["is_correct"] is False
    assert body["xp_awarded"] == 0
    assert body["lesson_completed"] is False


# --- RBAC sur le CRUD de contenu --------------------------------------------
def test_child_cannot_create_subject(client: TestClient, db_session: Session):
    _make_user(db_session, "kid3@x.fr", UserRole.CHILD)
    token = _login(client, "kid3@x.fr")
    r = client.post(
        "/api/v1/subjects",
        json={"name": "Hack", "slug": "hack"},
        headers=_auth(token),
    )
    assert r.status_code == 403, r.text


def test_child_cannot_create_exercise(client: TestClient, db_session: Session):
    _make_user(db_session, "kid4@x.fr", UserRole.CHILD)
    lesson, _ = _seed_lesson_with_two_mcq(db_session)
    token = _login(client, "kid4@x.fr")
    r = client.post(
        "/api/v1/exercises",
        json={
            "lesson_id": str(lesson.id),
            "type": "multiple_choice",
            "question": "hack?",
            "content": {"options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}]},
            "correct_answer": {"option_ids": ["a"]},
        },
        headers=_auth(token),
    )
    assert r.status_code == 403, r.text


def test_unauthenticated_cannot_create_subject(client: TestClient):
    r = client.post("/api/v1/subjects", json={"name": "Hack", "slug": "hack"})
    assert r.status_code in (401, 403), r.text


def test_admin_can_create_subject(client: TestClient, db_session: Session):
    _make_user(db_session, "admin@x.fr", UserRole.ADMIN)
    token = _login(client, "admin@x.fr")
    r = client.post(
        "/api/v1/subjects",
        json={"name": "Maths", "slug": "maths-admin"},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text


# --- validation du contrat d'exercice ---------------------------------------
def test_create_exercise_rejects_bad_contract(client: TestClient, db_session: Session):
    _make_user(db_session, "admin2@x.fr", UserRole.ADMIN)
    lesson, _ = _seed_lesson_with_two_mcq(db_session)
    token = _login(client, "admin2@x.fr")
    # correct_answer référence une option inexistante -> 422
    r = client.post(
        "/api/v1/exercises",
        json={
            "lesson_id": str(lesson.id),
            "type": "multiple_choice",
            "question": "1+1?",
            "content": {"options": [{"id": "a", "text": "2"}, {"id": "b", "text": "3"}]},
            "correct_answer": {"option_ids": ["z"]},
        },
        headers=_auth(token),
    )
    assert r.status_code == 422, r.text
