"""Schémas de la bibliothèque parent et de la surface « Découvrir ».

Deux publics, deux DTO **distincts** pour le même pack :

- l'adulte lit :class:`app.schemas.pack.PackSummary` / ``PackDetail`` — statut de
  modération, score qualité, notes de revue compris : c'est lui qui décide ;
- l'enfant ne lit que :class:`DiscoverPack`, un sous-ensemble volontairement
  pauvre. Réutiliser ``PackSummary`` côté enfant exposerait le statut
  communautaire et le score qualité, deux informations qui n'ont aucun sens
  pour un enfant de six ans et qui fuiteraient la mécanique de modération.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.pack import PackSummary
from app.services.contributor_legal import ReportReason

__all__ = [
    "AccessEntry",
    "AccessUpdate",
    "AutoEnableState",
    "AutoEnableUpdate",
    "CatalogueSort",
    "ChildAccessState",
    "ContributorStats",
    "DiscoverPack",
    "PackRequestCreate",
    "PackRequestDecision",
    "PackRequestResponse",
    "ReportCreate",
    "ReportReason",
    "ReportResponse",
]

#: Tris du catalogue. ``most_enabled`` est le signal social (« N familles »),
#: ``newest`` la surface « Nouveautés de la communauté ».
CatalogueSort = Literal["newest", "most_enabled"]


class AccessEntry(BaseModel):
    """Une ligne de liste blanche : ce pack est (ou a été) activé pour cet enfant.

    ``enabled_by`` est exposé parce qu'un enfant peut avoir plusieurs adultes
    responsables : le co-parent doit voir qui a activé quoi.
    """

    pack_id: UUID
    enabled: bool
    enabled_by: UUID | None = None
    enabled_at: datetime | None = None
    updated_at: datetime | None = None
    pack: PackSummary


class ChildAccessState(BaseModel):
    """État d'accès complet d'un enfant : l'interrupteur global et les lignes.

    Les packs ``official`` sont absents volontairement : ils sont activés
    implicitement au niveau de l'enfant et n'ont jamais de ligne d'accès.
    """

    child_id: UUID
    auto_enable_approved_packs: bool
    entries: list[AccessEntry] = Field(default_factory=list)


class AccessUpdate(BaseModel):
    """Activation ou désactivation d'un pack pour un enfant."""

    enabled: bool


class AutoEnableUpdate(BaseModel):
    """Interrupteur « activer automatiquement les packs approuvés à son niveau »."""

    enabled: bool


class AutoEnableState(BaseModel):
    """État de l'interrupteur d'auto-activation, par enfant."""

    child_id: UUID
    enabled: bool


class ContributorStats(BaseModel):
    """Statistiques d'un auteur. La reconnaissance est la seule récompense
    offerte aux contributeurs : ces nombres doivent donc être réels."""

    handle: str | None = None
    trusted: bool = False
    packs_approved: int = 0
    packs_pending: int = 0
    times_enabled: int = 0
    families_reached: int = 0


class ReportCreate(BaseModel):
    """Signalement d'un pack par un parent."""

    reason: ReportReason
    details: str | None = Field(None, max_length=2000)


class ReportResponse(BaseModel):
    """Signalement enregistré (le parent n'a pas accès à la suite du traitement)."""

    id: UUID
    pack_id: UUID
    reason: str
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DiscoverPack(BaseModel):
    """Carte « Découvrir » : le strict minimum visible par un enfant.

    Ces métadonnées sont visibles **avant** activation — c'est assumé, et c'est
    pourquoi la revue de modération porte aussi sur le titre, l'emoji et la
    description, pas seulement sur les exercices.
    """

    id: UUID
    title: str
    emoji: str | None = None
    description: str | None = None
    subject_icons: list[str] = Field(default_factory=list)
    lesson_count: int = 0
    families_count: int = 0
    author_handle: str | None = None
    requested: bool = False


class PackRequestCreate(BaseModel):
    """« Je veux ça ! » — une demande, jamais un accès."""

    pack_id: UUID


class PackRequestResponse(BaseModel):
    """Demande d'un enfant, telle que la voient l'enfant et ses responsables."""

    id: UUID
    child_id: UUID
    child_name: str | None = None
    pack_id: UUID
    pack_title: str
    pack_emoji: str | None = None
    status: str
    created_at: datetime | None = None
    decided_at: datetime | None = None
    decided_by: UUID | None = None


class PackRequestDecision(BaseModel):
    """Verdict d'un responsable sur une demande, derrière le code PIN parent.

    Le PIN voyage dans le corps (et non en en-tête) pour rester identique à
    ``POST /auth/verify-pin`` : un seul geste côté enfant-qui-passe-le-téléphone.
    """

    approve: bool
    pin: str = Field(..., description="Code PIN parent à 4 chiffres")
