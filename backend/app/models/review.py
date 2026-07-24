"""
Modèles pour le système de révision espacée (spaced repetition)
"""

import uuid

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReviewQueue(Base):
    """
    File de révision pour un exercice

    Implémente l'algorithme de répétition espacée (similaire à SuperMemo/Anki)
    """

    __tablename__ = "review_queue"
    __table_args__ = (UniqueConstraint("user_id", "exercise_id", name="uq_user_exercise_review"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    next_review_date = Column(Date, nullable=False, index=True)
    interval_days = Column(Integer, default=1)  # Intervalle avant prochaine révision
    ease_factor = Column(Numeric(3, 2), default=2.5)  # Facteur de facilité (2.5 = valeur initiale)
    repetitions = Column(Integer, default=0)  # Nombre de révisions réussies consécutives

    # Relations
    user = relationship("User", back_populates="review_queue")
    exercise = relationship("Exercise", back_populates="review_queue")

    def __repr__(self):
        return f"<ReviewQueue user={self.user_id} exercise={self.exercise_id} next={self.next_review_date}>"
