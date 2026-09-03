"""
Tests d'intégration de la boucle cœur : soumission d'exercice -> progression,
XP, série, complétion de leçon ; plus le contrôle d'accès (RBAC) sur le CRUD
de contenu.

Auth : parent (via dev-login) incarnant un enfant (X-Acting-Child-Id) pour le
jeu ; parent/admin pour le CRUD de contenu.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Exercise, Lesson, LevelEnum
from app.models.progress import ProgressStatus, UserProgress
from tests.helpers import (
    child_headers,
    dev_login,
    make_child,
    make_exercise,
    make_lesson,
    make_pack,
    make_subject,
)


def _seed_lesson_with_two_mcq(db: Session) -> tuple[Lesson, list[Exercise]]:
    subject = make_subject(db, name="Maths", slug="maths")
    pack = make_pack(db, title="Calcul CP", level=LevelEnum.CP)
    lesson = make_lesson(db, pack=pack, subject=subject, level=LevelEnum.CP, tier=0, name="Additions")
    lesson.xp_reward = 50
    e1 = make_exercise(db, lesson=lesson, order_index=0, question="1+1?")
    e2 = make_exercise(db, lesson=lesson, order_index=1, question="2+2?")
    db.commit()
    db.refresh(e1)
    db.refresh(e2)
    return lesson, [e1, e2]


def _admin_headers(client: TestClient, monkeypatch, email: str = "admin@x.fr") -> dict[str, str]:
    monkeypatch.setattr(settings, "ADMIN_EMAILS", email)
    return dev_login(client, email)


def test_submit_awards_xp_and_completes_lesson(client: TestClient, db_session: Session):
    child = make_child(db_session, name="kid")
    lesson, (e1, e2) = _seed_lesson_with_two_mcq(db_session)
    h = child_headers(client, child)

    # Premier exercice réussi : +10 XP, série 1, leçon pas encore terminée.
    r1 = client.post(
        f"/api/v1/exercises/{e1.id}/submit",
        json={"answer": {"option_ids": ["a"]}, "time_taken": 5},
        headers=h,
    )
    assert r1.status_code == 201, r1.text
    body1 = r1.json()
    assert body1["is_correct"] is True
    assert body1["xp_awarded"] == 10
    assert body1["current_streak"] == 1
    assert body1["lesson_completed"] is False

    # Second exercice réussi : leçon terminée, 3 étoiles. Pas de bonus forfaitaire
    # (désactivé par défaut, issue #6) -> seulement l'XP de l'exercice (easy = 10).
    r2 = client.post(
        f"/api/v1/exercises/{e2.id}/submit",
        json={"answer": {"option_ids": ["a"]}, "time_taken": 7},
        headers=h,
    )
    assert r2.status_code == 201, r2.text
    body2 = r2.json()
    assert body2["is_correct"] is True
    assert body2["lesson_completed"] is True
    assert body2["lesson_stars"] == 3
    assert body2["lesson_score"] == 100
    assert body2["xp_awarded"] == 10
    assert body2["total_xp"] == 20

    # Progression persistée en base (attribuée à l'enfant incarné).
    progress = db_session.query(UserProgress).filter_by(lesson_id=lesson.id).first()
    assert progress is not None
    assert progress.user_id == child.id
    assert progress.status == ProgressStatus.COMPLETED
    assert progress.stars == 3
    assert progress.attempts == 2
    assert progress.completed_at is not None


def test_wrong_answer_no_xp(client: TestClient, db_session: Session):
    child = make_child(db_session, name="kid2")
    _lesson, (e1, _e2) = _seed_lesson_with_two_mcq(db_session)
    h = child_headers(client, child)

    r = client.post(
        f"/api/v1/exercises/{e1.id}/submit",
        json={"answer": {"option_ids": ["b"]}},
        headers=h,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["is_correct"] is False
    assert body["xp_awarded"] == 0
    assert body["lesson_completed"] is False


# --- RBAC sur le CRUD de contenu (réservé à l'admin) ------------------------
def test_parent_cannot_create_subject(client: TestClient, db_session: Session):
    h = dev_login(client, "parent1@x.fr")
    r = client.post("/api/v1/subjects", json={"name": "Hack", "slug": "hack"}, headers=h)
    assert r.status_code == 403, r.text


def test_parent_cannot_create_exercise(client: TestClient, db_session: Session):
    lesson, _ = _seed_lesson_with_two_mcq(db_session)
    h = dev_login(client, "parent2@x.fr")
    r = client.post(
        "/api/v1/exercises",
        json={
            "lesson_id": str(lesson.id),
            "type": "multiple_choice",
            "question": "hack?",
            "content": {"options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}]},
            "correct_answer": {"option_ids": ["a"]},
        },
        headers=h,
    )
    assert r.status_code == 403, r.text


def test_unauthenticated_cannot_create_subject(client: TestClient):
    r = client.post("/api/v1/subjects", json={"name": "Hack", "slug": "hack"})
    assert r.status_code in (401, 403), r.text


def test_admin_can_create_subject(client: TestClient, db_session: Session, monkeypatch):
    h = _admin_headers(client, monkeypatch)
    r = client.post("/api/v1/subjects", json={"name": "Maths", "slug": "maths-admin"}, headers=h)
    assert r.status_code == 201, r.text


# --- validation du contrat d'exercice ---------------------------------------
def test_create_exercise_rejects_bad_contract(client: TestClient, db_session: Session, monkeypatch):
    lesson, _ = _seed_lesson_with_two_mcq(db_session)
    h = _admin_headers(client, monkeypatch, "admin2@x.fr")
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
        headers=h,
    )
    assert r.status_code == 422, r.text
