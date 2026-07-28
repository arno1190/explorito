"""
Tests du verrouillage par paliers comme source de vérité unique (issue #2).

Vérifie que ``GET /subjects/{id}/lessons`` renvoie un champ ``locked`` cohérent
avec le fil « Nouveautés », et que la soumission d'un exercice d'une leçon
verrouillée est refusée (403) — pas de contournement par lien direct.
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
from app.models.user import Profile, User, UserRole


def _make_user(db: Session, email: str, role: UserRole, level: LevelEnum | None = None) -> User:
    user = User(email=email, password_hash=get_password_hash("SecurePass123"), role=role, is_active=True)
    db.add(user)
    db.flush()
    db.add(
        Profile(
            user_id=user.id,
            display_name=email.split("@")[0],
            is_child=(role == UserRole.CHILD),
            level=level,
        )
    )
    db.commit()
    db.refresh(user)
    return user


def _mcq(lesson_id, order_index: int) -> Exercise:
    return Exercise(
        lesson_id=lesson_id,
        type="multiple_choice",
        question="1+1?",
        content={"options": [{"id": "a", "text": "2"}, {"id": "b", "text": "3"}], "multiple": False},
        correct_answer={"option_ids": ["a"]},
        order_index=order_index,
        difficulty=DifficultyEnum.EASY,
    )


def _seed_two_tiers(db: Session) -> tuple[Subject, Lesson, Exercise, Lesson, Exercise]:
    subject = Subject(name="Maths", slug="maths")
    db.add(subject)
    db.flush()
    path = LearningPath(subject_id=subject.id, name="Calcul", level=LevelEnum.CP)
    db.add(path)
    db.flush()
    l1 = Lesson(path_id=path.id, name="Palier 1", order_index=1, xp_reward=0, is_published=True)
    l2 = Lesson(path_id=path.id, name="Palier 2", order_index=2, xp_reward=0, is_published=True)
    db.add_all([l1, l2])
    db.flush()
    e1 = _mcq(l1.id, 0)
    e2 = _mcq(l2.id, 0)
    db.add_all([e1, e2])
    db.commit()
    for obj in (subject, l1, e1, l2, e2):
        db.refresh(obj)
    return subject, l1, e1, l2, e2


def _auth(client: TestClient, email: str) -> dict[str, str]:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_subject_lessons_expose_locked_flag(client: TestClient, db_session: Session):
    _make_user(db_session, "kid@x.fr", UserRole.CHILD, level=LevelEnum.CP)
    subject, l1, _e1, l2, _e2 = _seed_two_tiers(db_session)
    h = _auth(client, "kid@x.fr")

    lessons = client.get(f"/api/v1/subjects/{subject.id}/lessons", headers=h).json()
    by_id = {lz["id"]: lz for lz in lessons}
    assert by_id[str(l1.id)]["locked"] is False
    assert by_id[str(l2.id)]["locked"] is True


def test_submit_on_locked_lesson_is_forbidden(client: TestClient, db_session: Session):
    _make_user(db_session, "kid2@x.fr", UserRole.CHILD, level=LevelEnum.CP)
    _subject, _l1, _e1, _l2, e2 = _seed_two_tiers(db_session)
    h = _auth(client, "kid2@x.fr")

    # Lien direct vers l'exercice du palier 2 (verrouillé) -> 403, pas de contournement.
    r = client.post(
        f"/api/v1/exercises/{e2.id}/submit",
        json={"answer": {"option_ids": ["a"]}},
        headers=h,
    )
    assert r.status_code == 403, r.text


def test_completing_lower_tier_unlocks_next(client: TestClient, db_session: Session):
    _make_user(db_session, "kid3@x.fr", UserRole.CHILD, level=LevelEnum.CP)
    subject, _l1, e1, l2, e2 = _seed_two_tiers(db_session)
    h = _auth(client, "kid3@x.fr")

    # Terminer le palier 1 (son unique exercice).
    r1 = client.post(f"/api/v1/exercises/{e1.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)
    assert r1.status_code == 201, r1.text
    assert r1.json()["lesson_completed"] is True

    # Le palier 2 est maintenant déverrouillé, à la fois dans la liste et à la soumission.
    lessons = client.get(f"/api/v1/subjects/{subject.id}/lessons", headers=h).json()
    by_id = {lz["id"]: lz for lz in lessons}
    assert by_id[str(l2.id)]["locked"] is False

    r2 = client.post(f"/api/v1/exercises/{e2.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)
    assert r2.status_code == 201, r2.text


def test_parent_is_never_locked(client: TestClient, db_session: Session):
    _make_user(db_session, "parent@x.fr", UserRole.PARENT)
    subject, _l1, _e1, l2, _e2 = _seed_two_tiers(db_session)
    h = _auth(client, "parent@x.fr")
    lessons = client.get(f"/api/v1/subjects/{subject.id}/lessons", headers=h).json()
    assert all(lz["locked"] is False for lz in lessons)


def _link_child(db: Session, child: User, parent: User) -> None:
    prof = db.query(Profile).filter(Profile.user_id == child.id).first()
    prof.parent_id = parent.id
    db.commit()


def test_impersonating_parent_sees_child_level_and_locks(client: TestClient, db_session: Session):
    # Un parent « incarne » son enfant CP : le contenu est filtré à son niveau et
    # verrouillé selon SA progression (via l'en-tête X-Acting-Child-Id).
    parent = _make_user(db_session, "papa@x.fr", UserRole.PARENT)
    child = _make_user(db_session, "kid@x.fr", UserRole.CHILD, level=LevelEnum.CP)
    _link_child(db_session, child, parent)
    subject, l1, _e1, l2, _e2 = _seed_two_tiers(db_session)  # contenu CP
    # une matière d'un autre niveau ne doit pas apparaître pour l'enfant CP
    other = Subject(name="Histoire", slug="histoire")
    db_session.add(other)
    db_session.flush()
    ce2_path = LearningPath(subject_id=other.id, name="Hist CE2", level=LevelEnum.CE2)
    db_session.add(ce2_path)
    db_session.flush()
    db_session.add(Lesson(path_id=ce2_path.id, name="Hist P1", order_index=1, is_published=True))
    db_session.commit()

    h = _auth(client, "papa@x.fr")
    h_imp = {**h, "X-Acting-Child-Id": str(child.id)}

    subjects = client.get("/api/v1/subjects", headers=h_imp).json()
    names = {s["name"] for s in subjects}
    assert "Maths" in names
    assert "Histoire" not in names  # pas de contenu CP

    lessons = client.get(f"/api/v1/subjects/{subject.id}/lessons", headers=h_imp).json()
    by_id = {lz["id"]: lz for lz in lessons}
    assert by_id[str(l1.id)]["locked"] is False
    assert by_id[str(l2.id)]["locked"] is True


def test_impersonation_header_ignored_for_non_owned_child(client: TestClient, db_session: Session):
    # Un parent ne peut pas incarner un enfant qu'il ne possède pas : l'en-tête
    # est ignoré et il retrouve sa vue de parent (non filtrée, non verrouillée).
    _make_user(db_session, "stranger@x.fr", UserRole.PARENT)
    real_parent = _make_user(db_session, "owner@x.fr", UserRole.PARENT)
    child = _make_user(db_session, "kid2@x.fr", UserRole.CHILD, level=LevelEnum.CP)
    _link_child(db_session, child, real_parent)
    subject, _l1, _e1, l2, _e2 = _seed_two_tiers(db_session)

    h = _auth(client, "stranger@x.fr")
    h_imp = {**h, "X-Acting-Child-Id": str(child.id)}
    lessons = client.get(f"/api/v1/subjects/{subject.id}/lessons", headers=h_imp).json()
    # Vue parent : rien n'est verrouillé (l'en-tête a été ignoré).
    assert all(lz["locked"] is False for lz in lessons)
