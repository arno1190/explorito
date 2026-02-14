"""
Schémas Pydantic pour la gestion des enfants
"""

from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field


class ChildCreate(BaseModel):
    """
    Schéma pour la création d'un profil enfant
    """

    name: str = Field(..., min_length=2, max_length=100, description="Nom de l'enfant")
    birth_date: date = Field(..., description="Date de naissance")
    email: str = Field(..., description="Email de l'enfant (pour créer le compte)")
    password: str = Field(
        ..., min_length=8, description="Mot de passe (minimum 8 caractères)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alice",
                "birth_date": "2015-06-15",
                "email": "alice.child@example.com",
                "password": "SecurePass123",
            }
        }


class ChildResponse(BaseModel):
    """
    Schéma pour la réponse avec les informations d'un enfant
    """

    id: UUID
    name: str
    birth_date: date
    parent_id: UUID
    created_at: datetime

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
