"""
Tests de la mise à jour de profil : avatar de soi (PATCH /auth/me) et avatar
d'un enfant par le parent (PUT /children/{id}).
"""

import base64

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import Profile, User, UserRole

# PNG 1×1 transparent minimal (pour tester l'upload sans dépendance image).
PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def _make_user(db: Session, email: str, role: UserRole) -> User:
    user = User(email=email, password_hash=get_password_hash("SecurePass123"), role=role, is_active=True)
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, display_name=email.split("@")[0], is_child=(role == UserRole.CHILD)))
    db.commit()
    db.refresh(user)
    return user


def _auth(client: TestClient, email: str) -> dict[str, str]:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_user_sets_own_avatar(client: TestClient, db_session: Session):
    _make_user(db_session, "kid@x.fr", UserRole.CHILD)
    h = _auth(client, "kid@x.fr")
    r = client.patch("/api/v1/auth/me", json={"avatar_url": "🦊"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["profile"]["avatar_url"] == "🦊"
    # persiste et revient via /me
    me = client.get("/api/v1/auth/me", headers=h).json()
    assert me["profile"]["avatar_url"] == "🦊"


def test_parent_sets_child_avatar(client: TestClient, db_session: Session):
    parent = _make_user(db_session, "papa@x.fr", UserRole.PARENT)
    child = _make_user(db_session, "kid2@x.fr", UserRole.CHILD)
    prof = db_session.query(Profile).filter(Profile.user_id == child.id).first()
    prof.parent_id = parent.id
    db_session.commit()

    h = _auth(client, "papa@x.fr")
    r = client.put(f"/api/v1/children/{child.id}", json={"avatar_url": "🐼"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["avatar_url"] == "🐼"
    # visible dans la liste des enfants
    kids = client.get("/api/v1/children", headers=h).json()
    assert kids[0]["avatar_url"] == "🐼"


def test_upload_avatar_image(client: TestClient, db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    _make_user(db_session, "kid3@x.fr", UserRole.CHILD)
    h = _auth(client, "kid3@x.fr")
    r = client.post(
        "/api/v1/auth/me/avatar",
        headers=h,
        files={"file": ("moi.png", PNG_1x1, "image/png")},
    )
    assert r.status_code == 200, r.text
    url = r.json()["profile"]["avatar_url"]
    assert url.startswith("/uploads/avatars/")
    assert url.endswith(".png")
    # le fichier a bien été écrit
    assert (tmp_path / "avatars").exists()


def test_upload_avatar_rejects_non_image(
    client: TestClient, db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    _make_user(db_session, "kid4@x.fr", UserRole.CHILD)
    h = _auth(client, "kid4@x.fr")
    r = client.post(
        "/api/v1/auth/me/avatar",
        headers=h,
        files={"file": ("notes.txt", b"pas une image", "text/plain")},
    )
    assert r.status_code == 400, r.text


def test_parent_uploads_child_avatar(
    client: TestClient, db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    parent = _make_user(db_session, "papa2@x.fr", UserRole.PARENT)
    child = _make_user(db_session, "kid5@x.fr", UserRole.CHILD)
    prof = db_session.query(Profile).filter(Profile.user_id == child.id).first()
    prof.parent_id = parent.id
    db_session.commit()

    h = _auth(client, "papa2@x.fr")
    r = client.post(
        f"/api/v1/children/{child.id}/avatar",
        headers=h,
        files={"file": ("kid.png", PNG_1x1, "image/png")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["avatar_url"].startswith("/uploads/avatars/")
