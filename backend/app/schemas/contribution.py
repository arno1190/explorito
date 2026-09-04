"""Schémas Pydantic de la contribution : envoi, retouche rapide, jetons, conditions.

Les DTO de *lecture* d'un pack (résumé, détail, constats) vivent dans
:mod:`app.schemas.pack` parce que quatre surfaces les partagent. Ce module ne
contient donc que ce qui est propre au parcours de contribution.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.pack import CommunityStatus
from app.schemas.pack import ValidationIssue


class UploadResult(BaseModel):
    """Réponse d'un envoi accepté : de quoi ouvrir l'aperçu et lire les constats."""

    pack_id: UUID
    preview_url: str
    community_status: CommunityStatus
    quality_score: int = Field(..., ge=0, le=100)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    flags: list[ValidationIssue] = Field(default_factory=list)


class ExerciseEdit(BaseModel):
    """Retouche rapide d'un exercice existant. Les champs absents sont conservés."""

    id: UUID
    question: str | None = Field(None, min_length=1)
    content: dict[str, Any] | None = None
    correct_answer: dict[str, Any] | None = None
    difficulty_level: int | None = Field(None, ge=1, le=5)
    order_index: int | None = Field(None, ge=0, description="Position dans la leçon")


class LessonEdit(BaseModel):
    """Retouche rapide d'une leçon existante et de ses exercices."""

    id: UUID
    name: str | None = Field(None, min_length=1)
    description: str | None = None
    # Le palier **est** l'ordre de la leçon dans le pack (``Lesson.order_index``) :
    # une seule valeur pour éviter deux notions d'ordre qui divergeraient.
    tier: int | None = Field(None, ge=1, description="Palier (1 Découverte, 2 Entraînement, 3 Défi)")
    exercises: list[ExerciseEdit] = Field(default_factory=list)


class PackQuickEdit(BaseModel):
    """Corrections apportées depuis l'écran d'aperçu, revalidées avant écriture."""

    title: str | None = Field(None, min_length=1)
    emoji: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    lessons: list[LessonEdit] = Field(default_factory=list)


class UploadTokenCreate(BaseModel):
    """Demande d'émission d'un jeton d'envoi."""

    label: str | None = Field(None, max_length=80, description="Étiquette pour reconnaître le jeton")


class UploadTokenResponse(BaseModel):
    """Jeton d'envoi tel qu'affiché dans le profil (jamais le secret)."""

    id: UUID
    prefix: str
    label: str | None = None
    created_at: datetime | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    active: bool = True


class UploadTokenCreated(UploadTokenResponse):
    """Jeton fraîchement émis : seule et unique occasion de lire le secret."""

    token: str = Field(..., description="Secret en clair — non récupérable ensuite")


class ContributorTerms(BaseModel):
    """Conditions de contribution en vigueur et état d'acceptation du compte."""

    version: str
    text: str
    accepted: bool = False
    handle: str | None = None
    trusted: bool = False


class ContributorTermsAccept(BaseModel):
    """Acceptation explicite des conditions, avec le pseudonyme public choisi.

    Le pseudonyme est obligatoire ici : c'est la seule identité publiée d'un
    contributeur, et la faire choisir au moment de l'acceptation évite qu'un
    pseudonyme généré (``Parent-a1b2c3``) devienne son nom public par défaut.
    """

    handle: str = Field(..., min_length=3, max_length=24, description="Pseudonyme public")


class PairingCode(BaseModel):
    """Code court à dicter à son assistant, en échange d'un jeton d'envoi."""

    code: str = Field(..., description="Code à usage unique, à lire à voix haute")
    expires_at: datetime
    expires_in_seconds: int


class PairingClaim(BaseModel):
    """Code présenté par un assistant pour se configurer."""

    code: str = Field(..., min_length=4, max_length=32)


class PairingResult(BaseModel):
    """Jeton d'envoi remis à l'assistant, plus ce qu'il doit savoir du compte."""

    token: str = Field(..., description="Secret en clair — à stocker localement, non récupérable ensuite")
    prefix: str
    handle: str | None = None
    terms_accepted: bool = False
    terms_version: str
    app_url: str = Field(..., description="URL publique de l'application, à mémoriser avec le jeton")
