"""
Schémas Pydantic pour la gamification
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.gamification import AchievementRarity


class AchievementResponse(BaseModel):
    """
    Schéma pour un achievement
    """

    id: UUID
    name: str
    description: str | None = None
    icon: str | None = None
    rarity: AchievementRarity
    category: str | None = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Première Leçon",
                "description": "Complétez votre première leçon",
                "icon": "🎯",
                "rarity": "common",
                "category": "global",
            }
        }


class UserAchievementResponse(BaseModel):
    """
    Schéma pour un achievement débloqué par l'utilisateur
    """

    id: UUID
    achievement_id: UUID
    achievement: AchievementResponse
    unlocked_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "achievement_id": "123e4567-e89b-12d3-a456-426614174000",
                "achievement": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Première Leçon",
                    "description": "Complétez votre première leçon",
                    "icon": "🎯",
                    "rarity": "common",
                    "category": "global",
                },
                "unlocked_at": "2024-01-15T10:30:00",
            }
        }


class StreakResponse(BaseModel):
    """
    Schéma pour la série de jours consécutifs
    """

    current_streak: int = Field(..., ge=0, description="Série actuelle de jours")
    longest_streak: int = Field(..., ge=0, description="Plus longue série de jours")
    last_activity_date: date | None = None
    freeze_used: int = Field(..., ge=0, description="Nombre de jokers utilisés")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "current_streak": 7,
                "longest_streak": 12,
                "last_activity_date": "2024-01-15",
                "freeze_used": 2,
            }
        }


class DailyGoalResponse(BaseModel):
    """
    Schéma pour l'objectif quotidien
    """

    id: UUID
    date: date
    xp_target: int = Field(..., gt=0, description="XP à gagner aujourd'hui")
    xp_earned: int = Field(..., ge=0, description="XP gagné aujourd'hui")
    lessons_target: int = Field(..., gt=0, description="Leçons à compléter aujourd'hui")
    lessons_completed: int = Field(..., ge=0, description="Leçons complétées aujourd'hui")
    is_completed: bool = Field(..., description="Objectif complété")
    progress_percentage: float = Field(..., ge=0, le=100, description="Pourcentage de progression")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "date": "2024-01-15",
                "xp_target": 50,
                "xp_earned": 35,
                "lessons_target": 3,
                "lessons_completed": 2,
                "is_completed": False,
                "progress_percentage": 66.7,
            }
        }


class DailyGoalCreate(BaseModel):
    """
    Schéma pour créer/mettre à jour un objectif quotidien
    """

    xp_target: int = Field(..., gt=0, le=500, description="XP à gagner (1-500)")
    lessons_target: int = Field(..., gt=0, le=20, description="Leçons à compléter (1-20)")

    class Config:
        json_schema_extra = {"example": {"xp_target": 50, "lessons_target": 3}}


class RewardResponse(BaseModel):
    """
    Schéma pour une récompense débloquée
    """

    id: UUID
    type: str = Field(..., description="Type de récompense: sticker, trophy, avatar, theme")
    name: str
    image_url: str | None = None
    unlocked_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "type": "sticker",
                "name": "Étoile d'Or",
                "image_url": "/uploads/rewards/golden_star.png",
                "unlocked_at": "2024-01-15T10:30:00",
            }
        }


class LeaderboardEntry(BaseModel):
    """
    Schéma pour une entrée du classement familial
    """

    user_id: UUID
    display_name: str
    avatar_url: str | None = None
    total_xp: int = Field(..., ge=0, description="XP total")
    level: int = Field(..., ge=1, description="Niveau")
    current_streak: int = Field(..., ge=0, description="Série actuelle")
    lessons_completed: int = Field(..., ge=0, description="Leçons complétées")
    rank: int = Field(..., ge=1, description="Position dans le classement")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "display_name": "Alice",
                "avatar_url": "/uploads/avatars/alice.png",
                "total_xp": 1250,
                "level": 5,
                "current_streak": 7,
                "lessons_completed": 45,
                "rank": 1,
            }
        }


class ChildStatsResponse(BaseModel):
    """Statistiques de gamification d'un enfant (tableau de bord parent/enfant)."""

    child_id: UUID
    total_xp: int
    level: int
    current_level_xp: int
    next_level_xp: int
    current_streak: int
    longest_streak: int
    total_exercises_completed: int
    achievements: list[UserAchievementResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
