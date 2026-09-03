"""Schémas Pydantic partagés autour des packs.

Ces DTO sont **communs** à quatre surfaces (aperçu de contribution, catalogue
parent, file de modération, chemin d'accueil de l'enfant). Ils vivent donc dans
un module unique : dupliquer « ce qu'est un pack vu de l'extérieur » garantirait
que les quatre écrans divergent.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.content import LevelEnum
from app.models.pack import CommunityStatus, PackOrigin


class ValidationIssue(BaseModel):
    """Un constat du validateur, ancré sur la leçon/l'exercice fautif.

    ``severity`` porte toute la sémantique :

    - ``error`` : refus dur (forme, ``difficulty_level`` manquant, plafonds, langue) ;
    - ``warning`` : compte dans le score de qualité, ne bloque pas ;
    - ``flag`` : annotation à l'attention d'un humain (grossièreté, quasi-doublon),
      qui ne bloque jamais parce que ces détecteurs ont de vrais faux positifs.
    """

    severity: Literal["error", "warning", "flag"]
    code: str
    message: str
    lesson_index: int | None = None
    exercise_index: int | None = None
    field: str | None = None


class PackExercisePreview(BaseModel):
    """Un exercice tel qu'il sera présenté à l'enfant (aperçu et revue)."""

    id: UUID | None = None
    order_index: int
    type: str
    question: str
    content: dict = Field(default_factory=dict)
    correct_answer: dict = Field(default_factory=dict)
    explanation: str | None = None
    difficulty_level: int | None = None


class PackLessonPreview(BaseModel):
    """Une leçon du pack, avec sa matière, son niveau et son palier."""

    id: UUID | None = None
    name: str
    description: str | None = None
    subject_slug: str
    subject_name: str | None = None
    subject_icon: str | None = None
    level: LevelEnum
    tier: int
    xp_reward: int = 0
    exercises: list[PackExercisePreview] = Field(default_factory=list)


class PackSummary(BaseModel):
    """Carte de pack : ce qui suffit à lister, filtrer et décider."""

    id: UUID
    title: str
    emoji: str | None = None
    description: str | None = None
    origin: PackOrigin
    community_status: CommunityStatus
    author_handle: str | None = None
    tags: list[str] = Field(default_factory=list)
    quality_score: int | None = None
    difficulty_ratified: bool = False
    locked: bool = False
    level_min: LevelEnum
    level_max: LevelEnum
    lesson_count: int = 0
    exercise_count: int = 0
    subject_icons: list[str] = Field(default_factory=list)
    families_count: int = 0
    created_at: datetime | None = None
    submitted_at: datetime | None = None

    model_config = {"from_attributes": True}


class PackDetail(PackSummary):
    """Pack complet : le contenu que l'adulte doit pouvoir lire avant d'activer."""

    lessons: list[PackLessonPreview] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    cloned_from_pack_id: UUID | None = None
    review_notes: str | None = None
    reviewed_at: datetime | None = None
