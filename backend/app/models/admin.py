"""Modèles pour l'administration (journal de connexion parent)."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class LoginEvent(Base):
    """Une connexion parent (audit léger, minimisation des données).

    On ne stocke que ``user_id`` + horodatage — **pas d'IP ni de user-agent**.
    Les lignes sont purgées au-delà de 90 jours (cf. ``services.admin.prune``).
    """

    __tablename__ = "login_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<LoginEvent user={self.user_id} at={self.created_at}>"
