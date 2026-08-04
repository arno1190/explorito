"""
Sécurité et authentification JWT
"""

from datetime import datetime, timedelta
from typing import Any

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Context pour le hashing des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Requête HTTP réutilisée pour récupérer (et mettre en cache) les clés Google.
_google_request = google_requests.Request()


def verify_google_id_token(token: str) -> dict[str, Any]:
    """Vérifie un ID token Google et renvoie ses claims.

    Contrôle la signature (clés publiques Google), l'audience
    (``settings.GOOGLE_CLIENT_ID``), l'émetteur et l'expiration.

    Args:
        token: ID token (JWT) émis par Google Identity Services.

    Returns:
        Dictionnaire des claims (``sub``, ``email``, ``email_verified``, ``name``…).

    Raises:
        ValueError: Si le token est invalide, expiré, ou d'audience inattendue.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID n'est pas configuré côté serveur.")
    info: dict[str, Any] = google_id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
        token, _google_request, settings.GOOGLE_CLIENT_ID
    )
    if info.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise ValueError("Émetteur du token Google inattendu.")
    return info


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu'un mot de passe en clair correspond au hash

    Args:
        plain_password: Mot de passe en clair
        hashed_password: Mot de passe hashé

    Returns:
        True si le mot de passe est correct
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash un mot de passe

    Args:
        password: Mot de passe en clair

    Returns:
        Mot de passe hashé
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Crée un token JWT

    Args:
        data: Données à encoder dans le token
        expires_delta: Durée de validité du token

    Returns:
        Token JWT encodé
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    Décode un token JWT

    Args:
        token: Token JWT encodé

    Returns:
        Données décodées ou None si le token est invalide
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
