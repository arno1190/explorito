"""
Tests des endpoints d'authentification (modèle Google-only).

- ``/auth/dev-login`` (monté seulement si DEBUG) : connexion parent sans Google.
- ``/auth/google`` : vérification de l'``id_token`` (moquée), upsert parent,
  promotion admin via ADMIN_EMAILS.
- ``/auth/pin`` et ``/auth/verify-pin`` : PIN parent.
- ``/auth/me``, ``/auth/refresh``, ``/auth/logout``.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.api.auth as auth_module
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _fake_google(monkeypatch, email: str, *, verified: bool = True, name: str = "Google User", sub: str = "sub-123"):
    """Remplace la vérification Google par un jeu de claims contrôlé."""
    monkeypatch.setattr(
        auth_module,
        "verify_google_id_token",
        lambda token: {"email": email, "email_verified": verified, "name": name, "sub": sub},
    )


# --- dev-login --------------------------------------------------------------
def test_dev_login_creates_parent(client):
    r = client.post("/api/v1/auth/dev-login", json={"email": "user@qa.fr"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    data = me.json()
    assert data["email"] == "user@qa.fr"
    assert data["role"] == "parent"
    assert data["has_pin"] is False
    assert data["profile"]["is_child"] is False


def test_me_without_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_invalid_token(client):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"})
    assert r.status_code == 401


def test_refresh_token(client):
    login = client.post("/api/v1/auth/dev-login", json={"email": "user@qa.fr"}).json()
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert data["refresh_token"] == login["refresh_token"]


def test_refresh_invalid_token(client):
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid"})
    assert r.status_code == 401


def test_logout(client):
    token = client.post("/api/v1/auth/dev-login", json={"email": "user@qa.fr"}).json()["access_token"]
    r = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 204


# --- Google -----------------------------------------------------------------
def test_google_login_creates_parent(client, monkeypatch):
    _fake_google(monkeypatch, "newparent@gmail.com")
    r = client.post("/api/v1/auth/google", json={"credential": "any"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["email"] == "newparent@gmail.com"
    assert me["role"] == "parent"


def test_google_admin_via_allowlist(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "boss@qa.fr, other@qa.fr")
    _fake_google(monkeypatch, "boss@qa.fr")
    r = client.post("/api/v1/auth/google", json={"credential": "any"})
    token = r.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["role"] == "admin"


def test_google_unverified_email_rejected(client, monkeypatch):
    _fake_google(monkeypatch, "shady@gmail.com", verified=False)
    r = client.post("/api/v1/auth/google", json={"credential": "any"})
    assert r.status_code == 401


def test_google_invalid_token_rejected(client, monkeypatch):
    def _raise(_token):
        raise ValueError("bad token")

    monkeypatch.setattr(auth_module, "verify_google_id_token", _raise)
    r = client.post("/api/v1/auth/google", json={"credential": "any"})
    assert r.status_code == 401


# --- PIN --------------------------------------------------------------------
def test_set_and_verify_pin(client):
    token = client.post("/api/v1/auth/dev-login", json={"email": "user@qa.fr"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    r = client.post("/api/v1/auth/pin", json={"pin": "1234"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["has_pin"] is True

    assert client.post("/api/v1/auth/verify-pin", json={"pin": "1234"}, headers=h).status_code == 204
    assert client.post("/api/v1/auth/verify-pin", json={"pin": "0000"}, headers=h).status_code == 401


def test_verify_pin_without_pin_set(client):
    token = client.post("/api/v1/auth/dev-login", json={"email": "nopin@qa.fr"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/v1/auth/verify-pin", json={"pin": "1234"}, headers=h).status_code == 400


def test_pin_must_be_four_digits(client):
    token = client.post("/api/v1/auth/dev-login", json={"email": "user@qa.fr"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/v1/auth/pin", json={"pin": "12"}, headers=h).status_code == 422
    assert client.post("/api/v1/auth/pin", json={"pin": "abcd"}, headers=h).status_code == 422
