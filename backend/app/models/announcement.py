"""Modèles d'annonce par email (nouveautés produit envoyées aux parents).

Deux tables plutôt qu'une seule, pour la seule raison qui compte : un envoi
partiellement échoué doit être **reprenable sans doublon**. L'annonce porte le
contenu, la livraison porte l'état par destinataire ; relancer un envoi ne
réexpédie que les lignes non ``sent``.
"""

import enum
import uuid

from sqlalchemy import (
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


class AnnouncementStatus(str, enum.Enum):
    """Statut global d'une annonce."""

    DRAFT = "draft"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class DeliveryStatus(str, enum.Enum):
    """Statut d'une livraison individuelle."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"  # destinataire sans email, désinscrit, ou compte inactif


class Announcement(Base):
    """Une annonce rédigée par l'admin et diffusée aux parents."""

    __tablename__ = "announcements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subject = Column(String, nullable=False)
    # Corps en Markdown restreint (titres, gras, listes, liens) : rendu en HTML
    # à l'envoi et servi tel quel en repli texte.
    body_markdown = Column(Text, nullable=False)
    # Expéditeur effectif, figé à la création pour que l'audit reste vrai même si
    # la configuration change ensuite.
    from_email = Column(String, nullable=False)
    status = Column(String, nullable=False, default=AnnouncementStatus.DRAFT.value, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    sent_at = Column(DateTime, nullable=True)

    deliveries = relationship(
        "AnnouncementDelivery",
        back_populates="announcement",
        cascade="all, delete-orphan",
    )
    author = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Announcement {self.subject!r} {self.status}>"


class AnnouncementDelivery(Base):
    """État d'envoi d'une annonce vers un destinataire donné."""

    __tablename__ = "announcement_deliveries"
    __table_args__ = (UniqueConstraint("announcement_id", "email", name="uq_delivery_announcement_email"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    announcement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("announcements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    email = Column(String, nullable=False)
    status = Column(String, nullable=False, default=DeliveryStatus.PENDING.value, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    announcement = relationship("Announcement", back_populates="deliveries")

    def __repr__(self) -> str:
        return f"<AnnouncementDelivery {self.email} {self.status}>"
