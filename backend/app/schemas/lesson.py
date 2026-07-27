"""
Schémas Pydantic pour les leçons
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.exercise import ExerciseResponse


class RecentLessonResponse(BaseModel):
    """Leçon récente pour le fil « Nouveautés » (avec infos matière)."""

    id: UUID
    name: str
    subject_id: UUID
    subject_name: str
    subject_icon: str | None = None
    subject_color: str | None = None
    created_at: datetime
    locked: bool = False  # verrouillée si un palier inférieur n'est pas terminé


class LessonBase(BaseModel):
    """Schéma de base pour les leçons"""

    name: str = Field(..., min_length=1, max_length=200, description="Nom de la leçon")
    description: str | None = Field(None, description="Description de la leçon")
    order_index: int = Field(default=0, ge=0, description="Ordre dans le parcours")
    unlock_criteria: dict[str, Any] = Field(default_factory=dict, description="Critères de déverrouillage")
    xp_reward: int = Field(default=10, ge=0, description="Récompense XP")
    estimated_duration: int | None = Field(None, ge=0, description="Durée estimée en minutes")
    cover_image: str | None = Field(None, description="URL de l'image de couverture")
    is_published: bool = Field(default=False, description="Leçon publiée ou non")


class LessonCreate(LessonBase):
    """Schéma pour la création d'une leçon"""

    path_id: UUID = Field(..., description="ID du parcours d'apprentissage")

    class Config:
        json_schema_extra = {
            "example": {
                "path_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Le son [a]",
                "description": "Apprendre à reconnaître et écrire le son [a]",
                "order_index": 1,
                "unlock_criteria": {},
                "xp_reward": 50,
                "estimated_duration": 15,
                "cover_image": "/uploads/lessons/son-a.png",
                "is_published": True,
            }
        }


class LessonUpdate(BaseModel):
    """Schéma pour la mise à jour d'une leçon"""

    path_id: UUID | None = Field(None, description="ID du parcours d'apprentissage")
    name: str | None = Field(None, min_length=1, max_length=200, description="Nom de la leçon")
    description: str | None = Field(None, description="Description de la leçon")
    order_index: int | None = Field(None, ge=0, description="Ordre dans le parcours")
    unlock_criteria: dict[str, Any] | None = Field(None, description="Critères de déverrouillage")
    xp_reward: int | None = Field(None, ge=0, description="Récompense XP")
    estimated_duration: int | None = Field(None, ge=0, description="Durée estimée en minutes")
    cover_image: str | None = Field(None, description="URL de l'image de couverture")
    is_published: bool | None = Field(None, description="Leçon publiée ou non")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Le son [a]",
                "description": "Apprendre à reconnaître et écrire le son [a]",
                "is_published": True,
            }
        }


class LessonResponse(LessonBase):
    """Schéma de réponse pour une leçon"""

    id: UUID
    path_id: UUID
    subject_id: UUID | None = Field(None, description="ID de la matière (via le parcours)")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "path_id": "123e4567-e89b-12d3-a456-426614174000",
                "subject_id": "123e4567-e89b-12d3-a456-426614174002",
                "name": "Le son [a]",
                "description": "Apprendre à reconnaître et écrire le son [a]",
                "order_index": 1,
                "unlock_criteria": {},
                "xp_reward": 50,
                "estimated_duration": 15,
                "cover_image": "/uploads/lessons/son-a.png",
                "is_published": True,
            }
        }


class LessonWithExercises(LessonResponse):
    """Schéma de réponse pour une leçon avec ses exercices"""

    exercises: list[ExerciseResponse] = Field(default_factory=list, description="Liste des exercices")

    class Config:
        from_attributes = True
