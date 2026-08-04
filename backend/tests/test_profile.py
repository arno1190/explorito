"""
Tests de la mise à jour de profil : avatar de soi (PATCH /auth/me) et avatar
d'un enfant par le parent (PUT /children/{id}).
"""

import base64

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from tests.helpers import dev_login, make_child

# PNG 1×1 transparent minimal (pour tester l'upload sans dépendance image).
PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def test_user_sets_own_avatar(client: TestClient, db_session: Session):
    h = dev_login(client)
    r = client.patch("/api/v1/auth/me", json={"avatar_url": "🦊"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["profile"]["avatar_url"] == "🦊"
    # persiste et revient via /me
    me = client.get("/api/v1/auth/me", headers=h).json()
    assert me["profile"]["avatar_url"] == "🦊"


def test_parent_sets_child_avatar(client: TestClient, db_session: Session):
    child = make_child(db_session)
    h = dev_login(client)
    r = client.put(f"/api/v1/children/{child.id}", json={"avatar_url": "🐼"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["avatar_url"] == "🐼"
    # visible dans la liste des enfants
    kids = client.get("/api/v1/children", headers=h).json()
    assert kids[0]["avatar_url"] == "🐼"


def test_upload_avatar_image(client: TestClient, db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    h = dev_login(client)
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
    h = dev_login(client)
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
    child = make_child(db_session)
    h = dev_login(client)
    r = client.post(
        f"/api/v1/children/{child.id}/avatar",
        headers=h,
        files={"file": ("kid.png", PNG_1x1, "image/png")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["avatar_url"].startswith("/uploads/avatars/")
