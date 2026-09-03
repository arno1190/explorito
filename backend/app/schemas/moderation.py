"""Schémas de la surface de modération (file d'attente, verdicts, signalements).

Les DTO héritent de :mod:`app.schemas.pack` : la file de modération montre le
même pack que le catalogue parent, augmenté de ce que seul un modérateur doit
voir (lignée de clonage, signalements ouverts, identifiant de l'auteur).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.content import LevelEnum
from app.models.contribution import ReportStatus
from app.models.pack import CommunityStatus
from app.schemas.pack import PackDetail, PackSummary, ValidationIssue


class ModerationQueueEntry(PackSummary):
    """Une ligne de file : de quoi trier et prioriser sans ouvrir le pack."""

    author_id: UUID | None = None
    warnings: list[ValidationIssue] = Field(default_factory=list)
    open_reports: int = 0
    # Lignée : un pack cloné d'un pack approuvé se revoit en le comparant à son
    # parent, pas en le relisant intégralement.
    cloned_from_pack_id: UUID | None = None
    cloned_from_title: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None


class ModerationQueue(BaseModel):
    """File d'attente d'un statut donné."""

    status: CommunityStatus
    count: int
    items: list[ModerationQueueEntry] = Field(default_factory=list)


class ReportRow(BaseModel):
    """Signalement de parent, tel que listé côté modération."""

    id: UUID
    pack_id: UUID
    pack_title: str
    reason: str
    details: str | None = None
    status: ReportStatus
    created_at: datetime | None = None
    resolved_at: datetime | None = None


class AuditRow(BaseModel):
    """Ligne du journal d'audit d'un pack."""

    action: str
    actor_id: UUID | None = None
    detail: dict = Field(default_factory=dict)
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ModerationPackDetail(PackDetail):
    """Pack complet vu par un modérateur : contenu, signalements, lignée, audit."""

    author_id: UUID | None = None
    open_reports: int = 0
    cloned_from_title: str | None = None
    reports: list[ReportRow] = Field(default_factory=list)
    audit: list[AuditRow] = Field(default_factory=list)


class PackEditChanges(BaseModel):
    """Corrections admin. Seuls les champs *fournis* sont écrits.

    Le titre, l'emoji et la description sont éditables parce qu'ils sont
    visibles par l'enfant avant toute activation.
    """

    title: str | None = None
    emoji: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    level_min: LevelEnum | None = None
    level_max: LevelEnum | None = None


class PackReviewRequest(BaseModel):
    """Décision et/ou correction sur un pack.

    ``verdict`` omis signifie « correction seule » : aucun statut n'est écrit.
    C'est l'invariant du dispositif — l'analyse peut être automatisée, la
    décision non ; un verdict que l'admin n'a pas prononcé ne doit jamais
    apparaître en base.
    """

    verdict: CommunityStatus | None = None
    notes: str | None = None
    quality_score: int | None = Field(default=None, ge=0, le=100)
    ratify_difficulty: bool | None = None
    changes: PackEditChanges | None = None


class ReportDecisionRequest(BaseModel):
    """Clôture d'un signalement, avec blocage éventuel du pack visé.

    ``open`` est refusé par le service : rouvrir un signalement traité se fait
    en en créant un nouveau, sinon le journal devient illisible.
    """

    status: ReportStatus
    block_pack: bool = False


class TrustRequest(BaseModel):
    """Promotion (ou révocation) explicite du palier de confiance."""

    trusted: bool


class ContributorRow(BaseModel):
    """Contributeur vu côté modération : reconnaissance, conditions, confiance."""

    user_id: UUID
    handle: str
    terms_version: str | None = None
    terms_accepted_at: datetime | None = None
    trusted: bool = False
    trusted_at: datetime | None = None
    approved_packs: int = 0
    pending_packs: int = 0
    families_reached: int = 0
    trust_threshold: int
    trust_eligible: bool = False
