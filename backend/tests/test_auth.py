"""
Tests pour les endpoints d'authentification
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.user import UserRole

# Base de données de test en mémoire
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Crée une nouvelle session de base de données pour chaque test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Crée un client de test avec une base de données de test"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_register_parent(client):
    """Test d'inscription d'un parent"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "parent@example.com",
            "password": "SecurePass123",
            "display_name": "Parent Test",
            "role": "parent",
            "date_of_birth": "1985-06-15"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "parent@example.com"
    assert data["role"] == "parent"
    assert data["is_active"] is True
    assert "profile" in data
    assert data["profile"]["display_name"] == "Parent Test"


def test_register_child(client):
    """Test d'inscription d'un enfant"""
    # D'abord créer un parent
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "parent@example.com",
            "password": "SecurePass123",
            "display_name": "Parent Test",
            "role": "parent"
        }
    )

    # Puis créer un enfant
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "child@example.com",
            "password": "ChildPass123",
            "display_name": "Child Test",
            "role": "child",
            "date_of_birth": "2015-03-20",
            "parent_email": "parent@example.com"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "child@example.com"
    assert data["role"] == "child"
    assert data["profile"]["is_child"] is True


def test_register_duplicate_email(client):
    """Test d'inscription avec un email déjà utilisé"""
    # Première inscription
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePass123",
            "display_name": "Test User",
            "role": "parent"
        }
    )

    # Tentative de réinscription avec le même email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "AnotherPass123",
            "display_name": "Another User",
            "role": "child"
        }
    )
    assert response.status_code == 400
    assert "existe déjà" in response.json()["detail"]


def test_register_weak_password(client):
    """Test d'inscription avec un mot de passe faible"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "weak",
            "display_name": "Test User",
            "role": "parent"
        }
    )
    assert response.status_code == 422  # Validation error


def test_login_success(client):
    """Test de connexion réussie"""
    # Inscription
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "SecurePass123",
            "display_name": "Test User",
            "role": "parent"
        }
    )

    # Connexion
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "SecurePass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_wrong_password(client):
    """Test de connexion avec mauvais mot de passe"""
    # Inscription
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "SecurePass123",
            "display_name": "Test User",
            "role": "parent"
        }
    )

    # Tentative de connexion avec mauvais mot de passe
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "WrongPassword123"
        }
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    """Test de connexion avec un utilisateur inexistant"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123"
        }
    )
    assert response.status_code == 401


def test_get_current_user(client):
    """Test de récupération des informations de l'utilisateur courant"""
    # Inscription
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "SecurePass123",
            "display_name": "Test User",
            "role": "parent"
        }
    )

    # Connexion
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "SecurePass123"
        }
    )
    token = login_response.json()["access_token"]

    # Récupération des infos utilisateur
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["role"] == "parent"
    assert "profile" in data


def test_get_current_user_without_token(client):
    """Test de récupération des infos sans token"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    """Test de récupération des infos avec token invalide"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_refresh_token(client):
    """Test de rafraîchissement du token"""
    # Inscription et connexion
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "SecurePass123",
            "display_name": "Test User",
            "role": "parent"
        }
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "SecurePass123"
        }
    )
    refresh_token = login_response.json()["refresh_token"]

    # Rafraîchir le token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] == refresh_token  # Le refresh token reste le même


def test_refresh_invalid_token(client):
    """Test de rafraîchissement avec token invalide"""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401


def test_logout(client):
    """Test de déconnexion"""
    # Inscription et connexion
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "SecurePass123",
            "display_name": "Test User",
            "role": "parent"
        }
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "SecurePass123"
        }
    )
    token = login_response.json()["access_token"]

    # Déconnexion
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204
