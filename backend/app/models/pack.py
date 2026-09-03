"""Modèles des « packs » de contenu (unité d'auteur, de revue, de thème et de verrou).

Un :class:`Pack` est **l'unité d'autorité** du contenu pédagogique : c'est à la
fois l'objet qu'un parent rédige, celui que l'admin passe en revue, celui qui est
publié à la communauté, celui qui porte le thème (« Coupe du Monde ⚽ ») **et**
celui qui borne la progression par paliers. Il n'existe volontairement pas de
table ``themes`` : le pack *est* le thème (décision 9 de l'issue #7).

Invariant central : rien n'est jamais supprimé physiquement. ``user_progress`` et
``exercise_results`` pointent sur ``lessons.id`` / ``exercises.id`` en
``ON DELETE CASCADE`` ; retirer du contenu doit donc toujours être un changement
d'état (``community_status``), jamais un ``DELETE``. C'est pourquoi
``Lesson.pack_id`` est en ``ON DELETE RESTRICT``.
"""

import enum
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.content import LevelEnum


class PackOrigin(str, enum.Enum):
    """Provenance d'un pack.

    ``OFFICIAL`` : rédigé par l'équipe Explorito ; activé implicitement pour tous
    les enfants du niveau (c'est ainsi que le contenu historique est repris).
    ``COMMUNITY`` : rédigé par un parent ; n'atteint un enfant que via une ligne
    d'accès explicite.
    """

    OFFICIAL = "official"
    COMMUNITY = "community"


class CommunityStatus(str, enum.Enum):
    """Cycle de vie communautaire d'un pack.

    La visibilité *familiale* (les enfants de l'auteur) est **indépendante** de ce
    statut, à l'exception de ``BLOCKED`` :

    - ``DRAFT`` : en cours de rédaction, visible du seul auteur.
    - ``PENDING`` : soumis à la modération, déjà utilisable par la famille.
    - ``APPROVED`` : listé au catalogue parent ; verrouillé et difficulté ratifiée.
    - ``REJECTED`` : refusé pour la communauté ; la famille de l'auteur le garde.
    - ``BLOCKED`` : masqué pour tout le monde, auteur inclus (contenu nuisible).
      Reste un simple changement d'état : aucune ligne de progression n'est perdue.
    """

    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"


#: Statuts pour lesquels un pack communautaire est proposable au catalogue parent.
PUBLIC_STATUSES = (CommunityStatus.APPROVED,)

#: Statuts pour lesquels le pack reste utilisable par la famille de l'auteur.
AUTHOR_VISIBLE_STATUSES = (
    CommunityStatus.DRAFT,
    CommunityStatus.PENDING,
    CommunityStatus.APPROVED,
    CommunityStatus.REJECTED,
)


class Pack(Base):
    """Un ensemble cohérent de leçons : thème, unité de revue et portée du verrou."""

    __tablename__ = "packs"
    __table_args__ = (
        CheckConstraint(
            "origin IN ('official', 'community')",
            name="ck_packs_origin",
        ),
        CheckConstraint(
            "community_status IN ('draft', 'pending', 'approved', 'rejected', 'blocked')",
            name="ck_packs_community_status",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False)
    emoji = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    origin = Column(String, nullable=False, default=PackOrigin.COMMUNITY.value, index=True)

    # ``SET NULL`` volontaire : un pack doit survivre à la suppression RGPD de son
    # auteur, sinon honorer la demande détruirait la progression d'autres enfants.
    # Le pseudonyme est dénormalisé pour que l'attribution survive elle aussi.
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    author_handle = Column(String, nullable=True)

    community_status = Column(String, nullable=False, default=CommunityStatus.DRAFT.value, index=True)
    # Pilote l'XP : tant que la difficulté n'a pas été ratifiée par un humain à la
    # revue, le pack paie un tarif forfaitaire (cf. services/gamification.py).
    difficulty_ratified = Column(Boolean, nullable=False, default=False)
    # Posé à l'approbation : l'auteur ne peut plus muter le pack (anti bait-and-switch).
    locked = Column(Boolean, nullable=False, default=False)

    tags = Column(JSON, nullable=False, default=list)
    quality_score = Column(SmallInteger, nullable=True)
    # Avertissements non bloquants produits par le validateur, conservés pour
    # l'aperçu parent et l'écran de modération.
    warnings = Column(JSON, nullable=False, default=list)

    level_min = Column(Enum(LevelEnum), nullable=False, default=LevelEnum.CP)
    level_max = Column(Enum(LevelEnum), nullable=False, default=LevelEnum.CP)

    order_index = Column(Integer, nullable=False, default=0)

    # Lignée de révision : un pack approuvé se révise en le clonant (issue #17).
    cloned_from_pack_id = Column(UUID(as_uuid=True), ForeignKey("packs.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    submitted_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_notes = Column(Text, nullable=True)

    author = relationship("User", foreign_keys=[author_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    cloned_from = relationship("Pack", remote_side=[id], foreign_keys=[cloned_from_pack_id])
    lessons = relationship("Lesson", back_populates="pack")

    @property
    def is_official(self) -> bool:
        """Vrai pour le contenu rédigé par l'équipe (activé implicitement)."""
        return self.origin == PackOrigin.OFFICIAL.value

    @property
    def is_public(self) -> bool:
        """Vrai si le pack est proposable au catalogue de toutes les familles."""
        return self.community_status == CommunityStatus.APPROVED.value

    @property
    def is_blocked(self) -> bool:
        """Vrai si le pack est masqué pour tout le monde, auteur inclus."""
        return self.community_status == CommunityStatus.BLOCKED.value

    def __repr__(self) -> str:
        return f"<Pack {self.title!r} {self.origin}/{self.community_status}>"


class ChildPackAccess(Base):
    """Liste blanche : un pack communautaire activé pour un enfant précis.

    ``enabled_by`` est indispensable : un enfant peut avoir plusieurs adultes
    responsables (cf. :class:`app.models.guardianship.Guardianship`) et il faut
    savoir lequel a activé quoi. Désactiver conserve la ligne (``enabled=False``)
    afin que l'historique d'audit reste lisible et que la progression survive.
    """

    __tablename__ = "child_pack_access"
    __table_args__ = (UniqueConstraint("child_id", "pack_id", name="uq_child_pack_access"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    child_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pack_id = Column(UUID(as_uuid=True), ForeignKey("packs.id", ondelete="CASCADE"), nullable=False, index=True)
    enabled = Column(Boolean, nullable=False, default=True)
    enabled_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    enabled_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())

    pack = relationship("Pack")
    child = relationship("User", foreign_keys=[child_id])
    guardian = relationship("User", foreign_keys=[enabled_by])

    def __repr__(self) -> str:
        return f"<ChildPackAccess child={self.child_id} pack={self.pack_id} enabled={self.enabled}>"


class PackRequestStatus(str, enum.Enum):
    """Statut d'une demande « Je veux ça ! » émise par un enfant."""

    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"


class PackRequest(Base):
    """Demande d'un enfant pour un pack communautaire (surface « Découvrir »).

    L'enfant fait la découverte — ce qu'il aime faire — et le travail de l'adulte
    se réduit à un oui/non sur une demande précise, derrière le code PIN parent.
    Une demande n'accorde **jamais** l'accès par elle-même.
    """

    __tablename__ = "pack_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    child_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pack_id = Column(UUID(as_uuid=True), ForeignKey("packs.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False, default=PackRequestStatus.PENDING.value, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    pack = relationship("Pack")
    child = relationship("User", foreign_keys=[child_id])

    def __repr__(self) -> str:
        return f"<PackRequest child={self.child_id} pack={self.pack_id} {self.status}>"
