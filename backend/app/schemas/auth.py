"""
Schémas Pydantic pour l'authentification
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


class GoogleAuthRequest(BaseModel):
    """Connexion via Google Identity Services (flux id_token)."""

    credential: str = Field(..., description="ID token (JWT) renvoyé par Google Identity Services")


class DevLoginRequest(BaseModel):
    """Connexion de développement/tests (montée uniquement si DEBUG)."""

    email: EmailStr = Field(..., description="Email du parent (créé si absent)")
    display_name: str | None = Field(None, max_length=100, description="Nom d'affichage à la création")


class PinRequest(BaseModel):
    """Définition ou vérification d'un code PIN parent (4 chiffres)."""

    pin: str = Field(..., description="Code PIN à 4 chiffres")

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v: str) -> str:
        """Le PIN doit être exactement 4 chiffres."""
        if not (len(v) == 4 and v.isdigit()):
            raise ValueError("Le code PIN doit contenir exactement 4 chiffres.")
        return v


class Token(BaseModel):
    """
    Schéma pour la réponse avec le token JWT
    """

    access_token: str = Field(..., description="Token d'accès JWT")
    refresh_token: str | None = Field(None, description="Token de rafraîchissement")
    token_type: str = Field(default="bearer", description="Type de token")
    expires_in: int = Field(..., description="Durée de validité en secondes")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
            }
        }


class TokenData(BaseModel):
    """
    Schéma pour les données contenues dans le token
    """

    user_id: UUID = Field(..., description="ID de l'utilisateur")
    email: str = Field(..., description="Email de l'utilisateur")
    role: UserRole = Field(..., description="Rôle de l'utilisateur")


class ProfileResponse(BaseModel):
    """
    Schéma pour les informations du profil
    """

    id: UUID
    display_name: str
    avatar_url: str | None = None
    date_of_birth: date | None = None
    is_child: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    """Mise à jour de son propre profil (avatar, nom d'affichage)."""

    display_name: str | None = Field(None, min_length=1, max_length=100, description="Nom d'affichage")
    avatar_url: str | None = Field(None, max_length=512, description="Avatar (emoji ou URL d'image)")


class UserResponse(BaseModel):
    """
    Schéma pour la réponse avec les informations utilisateur
    """

    id: UUID
    email: str | None = None
    role: UserRole
    is_active: bool
    has_pin: bool = False
    created_at: datetime
    profile: ProfileResponse | None = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "alice@example.com",
                "role": "child",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00",
                "profile": {
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                    "display_name": "Alice",
                    "avatar_url": "/uploads/avatars/alice.png",
                    "date_of_birth": "2015-06-15",
                    "is_child": True,
                    "created_at": "2024-01-15T10:30:00",
                },
            }
        }


class RefreshTokenRequest(BaseModel):
    """
    Schéma pour la requête de rafraîchissement du token
    """

    refresh_token: str = Field(..., description="Token de rafraîchissement")

    class Config:
        json_schema_extra = {"example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}}
