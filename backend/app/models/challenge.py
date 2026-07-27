"""
Modèles des défis « free XP » (mini-jeux hors leçon).

Une :class:`PythagoreSession` enregistre chaque session du défi de tables de
multiplication : score, série la plus longue et XP réellement attribué (après
plafond quotidien anti-farm). Sert d'audit et de base au plafond journalier.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PythagoreSession(Base):
    """Une session terminée du défi Pythagore pour un utilisateur."""

    __tablename__ = "pythagore_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    correct = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False, default=0)
    longest_streak = Column(Integer, nullable=False, default=0)
    xp_earned = Column(Integer, nullable=False, default=0)
    # Horodatage assigné par la base (server_default) pour un décompte quotidien
    # cohérent quel que soit le fuseau applicatif.
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User")

    def __repr__(self):
        return f"<PythagoreSession user={self.user_id} {self.correct}/{self.total} +{self.xp_earned}xp>"
