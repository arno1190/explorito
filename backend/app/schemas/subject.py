"""
Schémas Pydantic pour les matières
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SubjectBase(BaseModel):
    """Schéma de base pour les matières"""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Nom de la matière"
    )
    slug: str = Field(
        ..., min_length=1, max_length=100, description="Slug unique pour l'URL"
    )
    description: Optional[str] = Field(None, description="Description de la matière")
    icon: Optional[str] = Field(None, description="Emoji ou URL d'icône")
    color: Optional[str] = Field(None, description="Code couleur hexadécimal")
    order_index: int = Field(default=0, ge=0, description="Ordre d'affichage")
    is_active: bool = Field(default=True, description="Matière active ou non")


class SubjectCreate(SubjectBase):
    """Schéma pour la création d'une matière"""

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Mathématiques",
                "slug": "mathematiques",
                "description": "Apprendre les nombres, les calculs et la géométrie",
                "icon": "🔢",
                "color": "#3B82F6",
                "order_index": 1,
                "is_active": True,
            }
        }


class SubjectUpdate(BaseModel):
    """Schéma pour la mise à jour d'une matière"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Nom de la matière"
    )
    slug: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Slug unique pour l'URL"
    )
    description: Optional[str] = Field(None, description="Description de la matière")
    icon: Optional[str] = Field(None, description="Emoji ou URL d'icône")
    color: Optional[str] = Field(None, description="Code couleur hexadécimal")
    order_index: Optional[int] = Field(None, ge=0, description="Ordre d'affichage")
    is_active: Optional[bool] = Field(None, description="Matière active ou non")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Mathématiques",
                "description": "Apprendre les nombres, les calculs et la géométrie",
                "is_active": True,
            }
        }


class SubjectResponse(SubjectBase):
    """Schéma de réponse pour une matière"""

    id: UUID
    lesson_count: int = Field(
        default=0, description="Nombre total de leçons dans cette matière"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Mathématiques",
                "slug": "mathematiques",
                "description": "Apprendre les nombres, les calculs et la géométrie",
                "icon": "🔢",
                "color": "#3B82F6",
                "order_index": 1,
                "is_active": True,
                "lesson_count": 24,
            }
        }
