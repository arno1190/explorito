"""
Modèles de suivi de progression
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Boolean,
    ForeignKey,
    Numeric,
    JSON,
    UniqueConstraint,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ProgressStatus(str, enum.Enum):
    """Statut de progression d'une leçon"""

    LOCKED = "locked"
    AVAILABLE = "available"
    STARTED = "started"
    COMPLETED = "completed"


class UserProgress(Base):
    """
    Progression de l'utilisateur sur une leçon

    Enregistre les tentatives, le score, les étoiles obten ues, etc.
    """

    __tablename__ = "user_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(Enum(ProgressStatus), default=ProgressStatus.LOCKED, nullable=False)
    score = Column(Integer, default=0)  # 0-100
    stars = Column(Integer, default=0)  # 0-3
    attempts = Column(Integer, default=0)
    time_spent = Column(Integer, default=0)  # en secondes
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relations
    user = relationship("User", back_populates="progress")
    lesson = relationship("Lesson", back_populates="user_progress")

    def __repr__(self):
        return f"<UserProgress user={self.user_id} lesson={self.lesson_id} status={self.status}>"


class ExerciseResult(Base):
    """
    Résultat d'un exercice individuel

    Enregistre chaque tentative sur un exercice
    """

    __tablename__ = "exercise_results"

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
    answer = Column(JSON, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    time_taken = Column(Integer, nullable=True)  # en secondes
    hints_used = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relations
    user = relationship("User", back_populates="exercise_results")
    exercise = relationship("Exercise", back_populates="results")

    def __repr__(self):
        return f"<ExerciseResult user={self.user_id} exercise={self.exercise_id} correct={self.is_correct}>"


class SubjectProgress(Base):
    """
    Progression globale de l'utilisateur par matière

    Agrège les statistiques pour une matière entière
    """

    __tablename__ = "subject_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "subject_id", name="uq_user_subject"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    lessons_completed = Column(Integer, default=0)
    accuracy_rate = Column(Numeric(5, 2), default=0)  # Pourcentage de réussite
    last_activity = Column(DateTime, nullable=True)

    # Relations
    user = relationship("User", back_populates="subject_progress")
    subject = relationship("Subject", back_populates="subject_progress")

    def __repr__(self):
        return f"<SubjectProgress user={self.user_id} subject={self.subject_id} level={self.level}>"
