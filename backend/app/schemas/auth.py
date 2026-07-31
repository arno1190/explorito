"""
Schémas Pydantic pour l'authentification
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserRegister(BaseModel):
    """
    Schéma pour l'inscription d'un nouvel utilisateur
    """

    email: EmailStr = Field(..., description="Adresse email de l'utilisateur")
    password: str = Field(..., min_length=8, description="Mot de passe (minimum 8 caractères)")
    display_name: str = Field(..., min_length=2, max_length=100, description="Nom d'affichage")
    role: UserRole = Field(default=UserRole.PARENT, description="Rôle de l'utilisateur")
    date_of_birth: date | None = Field(None, description="Date de naissance")
    parent_email: EmailStr | None = Field(None, description="Email du parent (pour les enfants)")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Valide la force du mot de passe"""
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        if not any(char.isdigit() for char in v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        if not any(char.isalpha() for char in v):
            raise ValueError("Le mot de passe doit contenir au moins une lettre")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "alice@example.com",
                "password": "SecurePass123",
                "display_name": "Alice",
                "role": "child",
                "date_of_birth": "2015-06-15",
            }
        }


class UserLogin(BaseModel):
    """
    Schéma pour la connexion
    """

    email: EmailStr = Field(..., description="Adresse email")
    password: str = Field(..., description="Mot de passe")

    class Config:
        json_schema_extra = {"example": {"email": "alice@example.com", "password": "SecurePass123"}}


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
    email: str
    role: UserRole
    is_active: bool
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
