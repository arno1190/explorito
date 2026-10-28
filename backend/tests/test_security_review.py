"""
Non-régression des failles relevées par la revue de sécurité d'octobre 2026.

Chaque test décrit un abus concret qui fonctionnait avant correction :
lecture anonyme des réponses, brouillon d'une autre famille, refresh token
utilisé comme jeton d'accès, compte suspendu toujours actif, suppression d'un
fichier partagé via ``avatar_url``, activation d'un pack non relu.
"""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import LevelEnum
from app.models.pack import CommunityStatus, PackOrigin
from app.models.user import User
from tests.helpers import (
    child_headers,
    dev_login,
    ensure_parent,
    make_child,
    make_exercise,
    make_lesson,
    make_pack,
)

OTHER_PARENT = "autre-famille@qa.fr"


def _official_exercise(db: Session):
    pack = make_pack(db)
    lesson = make_lesson(db, pack=pack)
    exercise = make_exercise(db, lesson=lesson)
    db.commit()
    return lesson, exercise


def test_reading_routes_require_a_session(client: TestClient, db_session: Session):
    lesson, exercise = _official_exercise(db_session)
    for url in (
        "/api/v1/exercises",
        f"/api/v1/exercises/{exercise.id}",
        "/api/v1/lessons",
        f"/api/v1/lessons/{lesson.id}",
        f"/api/v1/lessons/{lesson.id}/exercises",
    ):
        assert client.get(url).status_code == 401, url


def test_player_responses_never_carry_the_answer(client: TestClient, db_session: Session):
    child = make_child(db_session)
    lesson, exercise = _official_exercise(db_session)
    h = child_headers(client, child)

    one = client.get(f"/api/v1/exercises/{exercise.id}", headers=h)
    assert one.status_code == 200, one.text
    assert "correct_answer" not in one.json()

    listed = client.get(f"/api/v1/lessons/{lesson.id}/exercises", headers=h).json()
    assert listed and all("correct_answer" not in e for e in listed)

    full = client.get(f"/api/v1/lessons/{lesson.id}", headers=h).json()
    assert all("correct_answer" not in e for e in full["exercises"])


def test_raw_lists_are_admin_only(client: TestClient, db_session: Session):
    _official_exercise(db_session)
    h = dev_login(client)
    assert client.get("/api/v1/exercises", headers=h).status_code == 403
    assert client.get("/api/v1/lessons", headers=h).status_code == 403


def test_another_familys_draft_is_invisible(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, OTHER_PARENT)
    draft = make_pack(
        db_session,
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.DRAFT,
        author=author,
    )
    lesson = make_lesson(db_session, pack=draft, name="Brouillon de Léa")
    exercise = make_exercise(db_session, lesson=lesson)
    db_session.commit()

    stranger = child_headers(client, make_child(db_session))
    assert client.get(f"/api/v1/lessons/{lesson.id}", headers=stranger).status_code == 404
    assert client.get(f"/api/v1/lessons/{lesson.id}/exercises", headers=stranger).status_code == 404
    assert client.get(f"/api/v1/exercises/{exercise.id}", headers=stranger).status_code == 404

    # La famille de l'auteur, elle, joue son brouillon tout de suite.
    own_child = make_child(db_session, parent_email=OTHER_PARENT, name="Léa")
    own = child_headers(client, own_child, parent_email=OTHER_PARENT)
    assert client.get(f"/api/v1/lessons/{lesson.id}", headers=own).status_code == 200


def test_refresh_token_is_not_an_access_token(client: TestClient):
    r = client.post("/api/v1/auth/dev-login", json={"email": "parent@qa.fr"})
    refresh = r.json()["refresh_token"]
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"}).status_code == 401
    assert client.get("/api/v1/children", headers={"Authorization": f"Bearer {refresh}"}).status_code == 401


def test_suspended_parent_cannot_manage_children(client: TestClient, db_session: Session):
    h = dev_login(client)
    parent = db_session.query(User).filter(User.email == "parent@qa.fr").one()
    parent.is_active = False
    db_session.commit()

    r = client.post("/api/v1/children", json={"name": "Intrus", "level": "cp"}, headers=h)
    assert r.status_code == 403, r.text
    assert client.post("/api/v1/invitations", json={"kind": "all"}, headers=h).status_code == 403


def test_deleting_a_child_spares_files_it_does_not_own(client: TestClient, db_session: Session, tmp_path: Path):
    shared = tmp_path / "audio" / "consigne.mp3"
    shared.parent.mkdir(parents=True)
    shared.write_bytes(b"son partage")
    original = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = str(tmp_path)
    try:
        h = dev_login(client)
        child = make_child(db_session)
        r = client.put(f"/api/v1/children/{child.id}", json={"avatar_url": "/uploads/audio/consigne.mp3"}, headers=h)
        assert r.status_code == 200, r.text
        assert client.delete(f"/api/v1/children/{child.id}", headers=h).status_code == 204
    finally:
        settings.UPLOAD_DIR = original
    assert shared.exists()


def test_a_foreign_unreviewed_pack_cannot_be_enabled(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, OTHER_PARENT)
    draft = make_pack(
        db_session,
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.DRAFT,
        author=author,
        level=LevelEnum.CP,
    )
    approved = make_pack(db_session, origin=PackOrigin.COMMUNITY, author=author, level=LevelEnum.CP)
    child = make_child(db_session)
    db_session.commit()
    h = dev_login(client)
    h["X-Parent-Pin"] = "1234"

    def enable(pack_id):
        return client.put(f"/api/v1/library/children/{child.id}/access/{pack_id}", json={"enabled": True}, headers=h)

    assert enable(draft.id).status_code == 404
    assert enable(approved.id).status_code == 200


def test_a_disguised_path_to_another_avatar_is_spared(client: TestClient, db_session: Session, tmp_path: Path):
    name = "0123456789abcdef0123456789abcdef.png"
    victim = tmp_path / "avatars" / name
    victim.parent.mkdir(parents=True)
    victim.write_bytes(b"avatar d'une autre famille")
    original = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = str(tmp_path)
    try:
        h = dev_login(client)
        child = make_child(db_session)
        disguised = f"/uploads/avatars/./{name}"
        assert client.put(f"/api/v1/children/{child.id}", json={"avatar_url": disguised}, headers=h).status_code == 200
        assert client.delete(f"/api/v1/children/{child.id}", headers=h).status_code == 204
    finally:
        settings.UPLOAD_DIR = original
    assert victim.exists()
