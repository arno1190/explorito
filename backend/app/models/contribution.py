"""Modèles de la contribution communautaire : contributeur, jeton d'envoi, signalement, audit.

Trois principes de conception, tous issus du fait que le contenu vient d'inconnus
et est montré aux enfants d'autres familles :

1. **Pseudonymat.** L'inscription se fait via Google : le nom d'affichage est un
   vrai nom. Aucune surface communautaire ne l'expose ; seul un pseudonyme choisi
   par l'auteur est publié (:class:`ContributorProfile.handle`).
2. **Aucun canal de contact.** Pas de messagerie, pas d'abonnement, pas de page
   profil. Deux familles ne peuvent pas communiquer via l'application.
3. **Un jeton long ne peut jamais publier.** :class:`UploadToken` n'autorise que
   la création de brouillons ; la modération vit derrière un jeton distinct.
"""

import enum
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ContributorProfile(Base):
    """Identité publique (pseudonyme) et statut de confiance d'un parent auteur."""

    __tablename__ = "contributor_profiles"
    __table_args__ = (UniqueConstraint("handle", name="uq_contributor_handle"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    handle = Column(String, nullable=False, index=True)
    # Acceptation des conditions de contribution : version + horodatage. Bloquant
    # au premier envoi, car la licence « distribuer **et modifier** » est ce qui
    # autorise l'admin à corriger un pack à la revue.
    terms_version = Column(String, nullable=True)
    terms_accepted_at = Column(DateTime, nullable=True)
    # Palier de confiance : à partir de ``trusted``, les soumissions sont publiées
    # directement, avec contrôle a posteriori et bouton de signalement en filet.
    # Explicite, visible côté admin et révocable.
    trusted = Column(Boolean, nullable=False, default=False)
    trusted_at = Column(DateTime, nullable=True)
    trusted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<ContributorProfile {self.handle} trusted={self.trusted}>"


class UploadToken(Base):
    """Jeton personnel, révocable, valable **uniquement** pour créer des brouillons.

    Le secret n'est jamais stocké en clair : seul son SHA-256 l'est, avec un
    préfixe lisible pour que le parent reconnaisse le jeton dans son profil.
    """

    __tablename__ = "upload_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    prefix = Column(String, nullable=False)
    label = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])

    @property
    def is_active(self) -> bool:
        """Vrai si le jeton est encore utilisable."""
        return self.revoked_at is None

    def __repr__(self) -> str:
        return f"<UploadToken {self.prefix}… user={self.user_id} active={self.is_active}>"


class UploadPairing(Base):
    """Code d'appariement court, à lire à voix haute à son assistant.

    Existe pour une seule raison : un parent ne configurera pas de variable
    d'environnement, et recopier un secret de 43 caractères depuis un téléphone
    fait abandonner. Le parent lit huit caractères, l'assistant les échange
    contre un vrai jeton d'envoi et le stocke lui-même.

    Compromis de sécurité assumé et borné : l'échange est **non authentifié**
    (le code *est* la preuve), donc le code est à usage unique, expire en
    quelques minutes, et n'ouvre au mieux que la création de brouillons sur un
    compte. Comme pour les jetons, seul le SHA-256 du code est stocké.
    """

    __tablename__ = "upload_pairings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    # Jeton émis lors de l'échange : garde la trace de ce que ce code a produit,
    # pour que révoquer le jeton reste lisible depuis l'appariement.
    token_id = Column(UUID(as_uuid=True), ForeignKey("upload_tokens.id", ondelete="SET NULL"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<UploadPairing user={self.user_id} claimed={self.claimed_at is not None}>"


class ReportStatus(str, enum.Enum):
    """Statut d'un signalement de pack."""

    OPEN = "open"
    ACTIONED = "actioned"
    DISMISSED = "dismissed"


class PackReport(Base):
    """Signalement d'un pack communautaire par un parent ; alimente la modération."""

    __tablename__ = "pack_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    pack_id = Column(UUID(as_uuid=True), ForeignKey("packs.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    status = Column(String, nullable=False, default=ReportStatus.OPEN.value, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    pack = relationship("Pack")

    def __repr__(self) -> str:
        return f"<PackReport pack={self.pack_id} {self.reason} {self.status}>"


class PackAuditLog(Base):
    """Journal des actions sur un pack : verdicts, éditions admin, accès, confiance.

    Sert deux besoins distincts : la traçabilité des éditions admin sur un pack
    verrouillé (l'auteur n'y a plus la main, il faut savoir qui a changé quoi) et
    la trace du garde ayant activé un pack pour un enfant.
    """

    __tablename__ = "pack_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    pack_id = Column(UUID(as_uuid=True), ForeignKey("packs.id", ondelete="CASCADE"), nullable=True, index=True)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # Étiquette libre mais stable : 'submitted', 'verdict', 'admin_edit',
    # 'access_enabled', 'access_disabled', 'trust_granted', 'report'…
    action = Column(String, nullable=False, index=True)
    detail = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    actor = relationship("User", foreign_keys=[actor_id])

    def __repr__(self) -> str:
        return f"<PackAuditLog {self.action} pack={self.pack_id}>"


class ContributionQuota(Base):
    """Compteur journalier d'envois par compte (limitation de débit).

    Une ligne par (utilisateur, jour) : suffisant pour « N packs/jour » sans
    balayer la table ``packs``, et purgeable trivialement.
    """

    __tablename__ = "contribution_quotas"
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_contribution_quota_user_day"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    day = Column(String, nullable=False)  # ISO 'YYYY-MM-DD' (jour serveur)
    uploads = Column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<ContributionQuota user={self.user_id} {self.day}={self.uploads}>"
