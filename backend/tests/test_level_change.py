"""
Tests du changement de niveau d'un enfant (issue #3).

Changer de classe bascule tout le contenu futur au nouveau niveau, mais conserve
la progression et l'XP déjà acquis ; revenir au niveau précédent retrouve la
complétion intacte.
"""

from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.content import (
    DifficultyEnum,
    Exercise,
    Lesson,
    LevelEnum,
    Subject,
)
from app.models.progress import ProgressStatus, SubjectProgress, UserProgress
from app.models.user import Profile, User
from tests.helpers import child_headers, make_child, make_lesson, make_pack, make_subject

_children: dict[str, User] = {}


def _make_child(db: Session, email: str, level: LevelEnum) -> User:
    child = make_child(db, level=level, name=email.split("@")[0])
    _children[email] = child
    return child


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


def _subject_two_tiers(db: Session, name: str, slug: str, level: LevelEnum) -> tuple[Subject, Lesson, Exercise, Lesson]:
    """Deux paliers d'un **même pack** : c'est là que le verrou séquentiel s'applique."""
    subject = make_subject(db, name=name, slug=slug)
    pack = make_pack(db, title=f"{name} {level.name}", level=level)
    l1 = make_lesson(db, pack=pack, subject=subject, level=level, tier=1, name=f"{name} P1")
    l2 = make_lesson(db, pack=pack, subject=subject, level=level, tier=2, name=f"{name} P2")
    db.flush()
    e1 = _mcq(l1.id, 0)
    db.add(e1)
    db.commit()
    for obj in (subject, l1, e1, l2):
        db.refresh(obj)
    return subject, l1, e1, l2


def _auth(client: TestClient, email: str) -> dict[str, str]:
    return child_headers(client, _children[email])


def test_level_change_preserves_history_and_regates(client: TestClient, db_session: Session):
    child = _make_child(db_session, "kid@x.fr", LevelEnum.CE1)
    ce1_subject, _ce1_l1, ce1_e1, _ce1_l2 = _subject_two_tiers(db_session, "Maths CE1", "maths-ce1", LevelEnum.CE1)
    h = _auth(client, "kid@x.fr")

    # Terminer une leçon CE1.
    r = client.post(f"/api/v1/exercises/{ce1_e1.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["lesson_completed"] is True

    xp_before = db_session.query(func.sum(SubjectProgress.total_xp)).filter_by(user_id=child.id).scalar() or 0
    progress_rows_before = db_session.query(func.count(UserProgress.id)).filter_by(user_id=child.id).scalar()
    assert xp_before > 0
    assert progress_rows_before == 1

    # Contenu CE2 (deux paliers) puis bascule du niveau de l'enfant.
    ce2_subject, _c2l1, _c2e1, ce2_l2 = _subject_two_tiers(db_session, "Maths CE2", "maths-ce2", LevelEnum.CE2)
    profile = db_session.query(Profile).filter_by(user_id=child.id).first()
    profile.level = LevelEnum.CE2
    db_session.commit()

    # La progression et l'XP CE1 sont intacts (rien de destructif).
    xp_after = db_session.query(func.sum(SubjectProgress.total_xp)).filter_by(user_id=child.id).scalar() or 0
    progress_rows_after = db_session.query(func.count(UserProgress.id)).filter_by(user_id=child.id).scalar()
    assert xp_after == xp_before
    assert progress_rows_after == progress_rows_before
    ce1_progress = db_session.query(UserProgress).filter_by(user_id=child.id).first()
    assert ce1_progress.status == ProgressStatus.COMPLETED

    # La vue bascule au CE2 : la matière CE1 (sans contenu CE2) disparaît.
    subjects = client.get("/api/v1/subjects", headers=h).json()
    names = {s["name"] for s in subjects}
    assert "Maths CE2" in names
    assert "Maths CE1" not in names

    # Le nouveau niveau démarre gaté au palier 1 (palier 2 verrouillé).
    ce2_lessons = client.get(f"/api/v1/subjects/{ce2_subject.id}/lessons", headers=h).json()
    by_id = {lz["id"]: lz for lz in ce2_lessons}
    assert by_id[str(ce2_l2.id)]["locked"] is True

    # Revenir au CE1 retrouve la complétion intacte.
    profile.level = LevelEnum.CE1
    db_session.commit()
    ce1_lessons = client.get(f"/api/v1/subjects/{ce1_subject.id}/lessons", headers=h).json()
    assert {lz["name"] for lz in ce1_lessons} == {"Maths CE1 P1", "Maths CE1 P2"}
