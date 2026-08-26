"""
Schémas Pydantic pour la gestion des enfants
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.content import LevelEnum


class ChildCreate(BaseModel):
    """
    Schéma pour la création d'un profil enfant
    """

    name: str = Field(..., min_length=2, max_length=100, description="Nom de l'enfant")
    birth_date: date | None = Field(None, description="Date de naissance")
    level: LevelEnum | None = Field(None, description="Niveau scolaire (PS à CM2)")

    class Config:
        json_schema_extra = {"example": {"name": "Alice", "birth_date": "2015-06-15", "level": "ce1"}}


class ChildUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'un profil enfant.

    Tous les champs sont optionnels ; seuls ceux fournis sont modifiés.
    """

    name: str | None = Field(None, min_length=2, max_length=100, description="Nom de l'enfant")
    birth_date: date | None = Field(None, description="Date de naissance")
    level: LevelEnum | None = Field(None, description="Niveau scolaire (PS à CM2)")
    avatar_url: str | None = Field(None, max_length=512, description="Avatar (emoji ou URL d'image)")
    disabled_collections: list[str] | None = Field(
        None, description="Slugs de collections masquées pour cet enfant (ex. ['harry_potter'])"
    )

    class Config:
        json_schema_extra = {"example": {"name": "Alice", "birth_date": "2015-06-15"}}


class ChildResponse(BaseModel):
    """
    Schéma pour la réponse avec les informations d'un enfant
    """

    id: UUID
    name: str
    birth_date: date | None = None
    parent_id: UUID
    level: LevelEnum | None = None
    avatar_url: str | None = None
    created_at: datetime
    # Collections masquées pour cet enfant (choix du parent).
    disabled_collections: list[str] = []
    # Garde partagée : rôle de l'appelant sur cet enfant et s'il en est propriétaire.
    role: str = "owner"
    is_owner: bool = True

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Alice",
                "birth_date": "2015-06-15",
                "parent_id": "123e4567-e89b-12d3-a456-426614174001",
                "created_at": "2024-01-15T10:30:00",
            }
        }
