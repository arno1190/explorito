"""
Schémas Pydantic pour le suivi de progression
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.progress import ProgressStatus


class LessonProgressResponse(BaseModel):
    """
    Schéma pour la progression d'une leçon
    """

    id: UUID
    lesson_id: UUID
    lesson_name: str | None = None
    status: ProgressStatus
    score: int = Field(..., ge=0, le=100, description="Score en pourcentage (0-100)")
    stars: int = Field(..., ge=0, le=3, description="Étoiles obtenues (0-3)")
    attempts: int = Field(..., ge=0, description="Nombre de tentatives")
    time_spent: int = Field(..., ge=0, description="Temps passé en secondes")
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "lesson_id": "123e4567-e89b-12d3-a456-426614174001",
                "lesson_name": "Le son [a]",
                "status": "completed",
                "score": 85,
                "stars": 2,
                "attempts": 2,
                "time_spent": 420,
                "started_at": "2024-01-15T10:00:00",
                "completed_at": "2024-01-15T10:07:00",
            }
        }


class SubjectProgressResponse(BaseModel):
    """
    Schéma pour la progression d'une matière
    """

    id: UUID
    subject_id: UUID
    subject_name: str | None = None
    total_xp: int = Field(..., ge=0, description="XP total gagné dans cette matière")
    level: int = Field(..., ge=1, description="Niveau atteint dans cette matière")
    lessons_completed: int = Field(..., ge=0, description="Nombre de leçons complétées")
    accuracy_rate: Decimal = Field(..., ge=0, le=100, description="Taux de réussite en pourcentage")
    last_activity: datetime | None = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "subject_id": "123e4567-e89b-12d3-a456-426614174001",
                "subject_name": "Français",
                "total_xp": 450,
                "level": 3,
                "lessons_completed": 12,
                "accuracy_rate": 87.5,
                "last_activity": "2024-01-15T10:30:00",
            }
        }


class SubjectOverviewItem(BaseModel):
    """Avancement d'une matière pour l'enfant : leçons terminées / total.

    Calculé au niveau scolaire de l'enfant (leçons publiées uniquement). Permet
    d'afficher une barre de progression par matière (où l'enfant est en retard).
    """

    subject_id: UUID
    total_lessons: int = Field(..., ge=0, description="Leçons publiées à son niveau")
    completed_lessons: int = Field(..., ge=0, description="Leçons terminées")

    class Config:
        from_attributes = True


class ProgressDashboard(BaseModel):
    """
    Schéma pour le tableau de bord de progression
    """

    total_xp: int = Field(..., ge=0, description="XP total de l'utilisateur")
    overall_level: int = Field(..., ge=1, description="Niveau global de l'utilisateur")
    current_streak: int = Field(..., ge=0, description="Série de jours consécutifs")
    lessons_completed_today: int = Field(..., ge=0, description="Leçons complétées aujourd'hui")
    total_lessons_completed: int = Field(..., ge=0, description="Total de leçons complétées")
    subjects_progress: list[SubjectProgressResponse] = Field(
        default_factory=list, description="Progression par matière"
    )
    recent_lessons: list[LessonProgressResponse] = Field(default_factory=list, description="Leçons récentes")
    achievements_count: int = Field(..., ge=0, description="Nombre d'achievements débloqués")
    next_level_xp: int = Field(..., gt=0, description="XP nécessaire pour le prochain niveau")

    class Config:
        json_schema_extra = {
            "example": {
                "total_xp": 1250,
                "overall_level": 5,
                "current_streak": 7,
                "lessons_completed_today": 3,
                "total_lessons_completed": 45,
                "subjects_progress": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "subject_id": "123e4567-e89b-12d3-a456-426614174001",
                        "subject_name": "Français",
                        "total_xp": 450,
                        "level": 3,
                        "lessons_completed": 12,
                        "accuracy_rate": 87.5,
                        "last_activity": "2024-01-15T10:30:00",
                    }
                ],
                "recent_lessons": [],
                "achievements_count": 8,
                "next_level_xp": 1500,
            }
        }
