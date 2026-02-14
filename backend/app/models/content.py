"""
Modèles de contenu pédagogique
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    Text,
    ForeignKey,
    JSON,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class LevelEnum(str, enum.Enum):
    """Niveaux scolaires"""

    CP = "cp"
    CE1 = "ce1"
    CE2 = "ce2"


class DifficultyEnum(str, enum.Enum):
    """Niveaux de difficulté"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Subject(Base):
    """
    Matière scolaire

    Exemples: Français, Mathématiques, Questionner le Monde, etc.
    """

    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)  # "Français", "Mathématiques", etc.
    slug = Column(
        String, unique=True, nullable=False, index=True
    )  # "francais", "mathematiques"
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)  # emoji ou URL d'image
    color = Column(String, nullable=True)  # code couleur hex
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Relations
    learning_paths = relationship(
        "LearningPath", back_populates="subject", cascade="all, delete-orphan"
    )
    subject_progress = relationship(
        "SubjectProgress", back_populates="subject", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Subject {self.name}>"


class LearningPath(Base):
    """
    Parcours d'apprentissage au sein d'une matière

    Exemple: "Lecture Ratus" dans la matière "Français"
    """

    __tablename__ = "learning_paths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    level = Column(Enum(LevelEnum), default=LevelEnum.CP)
    order_index = Column(Integer, default=0)
    prerequisites = Column(JSON, default=[])  # Liste d'IDs de parcours prérequis

    # Relations
    subject = relationship("Subject", back_populates="learning_paths")
    lessons = relationship(
        "Lesson", back_populates="path", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<LearningPath {self.name}>"


class Lesson(Base):
    """
    Leçon individuelle dans un parcours

    Exemple: "Le son [a]" dans le parcours "Lecture Ratus"
    """

    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    path_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    unlock_criteria = Column(
        JSON, default={}
    )  # {required_xp: 100, required_lessons: [...]}
    xp_reward = Column(Integer, default=10)
    estimated_duration = Column(Integer, nullable=True)  # en minutes
    cover_image = Column(String, nullable=True)
    is_published = Column(Boolean, default=False)

    # Relations
    path = relationship("LearningPath", back_populates="lessons")
    exercises = relationship(
        "Exercise", back_populates="lesson", cascade="all, delete-orphan"
    )
    user_progress = relationship(
        "UserProgress", back_populates="lesson", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Lesson {self.name}>"


class Exercise(Base):
    """
    Exercice individuel dans une leçon

    Supporte 12 types différents: mcq, drag_drop, fill_blanks, etc.
    """

    __tablename__ = "exercises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lesson_id = Column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    type = Column(String, nullable=False)  # 'mcq', 'drag_drop', 'fill_blanks', etc.
    question = Column(Text, nullable=False)
    content = Column(JSON, nullable=False)  # Structure dépend du type
    correct_answer = Column(JSON, nullable=False)
    hints = Column(JSON, default=[])  # [{text: "...", delay: 10}]
    explanation = Column(Text, nullable=True)  # Explication après réponse
    order_index = Column(Integer, default=0)
    difficulty = Column(Enum(DifficultyEnum), default=DifficultyEnum.EASY)
    media_urls = Column(JSON, default={})  # {images: [...], audio: "..."}

    # Relations
    lesson = relationship("Lesson", back_populates="exercises")
    results = relationship(
        "ExerciseResult", back_populates="exercise", cascade="all, delete-orphan"
    )
    review_queue = relationship(
        "ReviewQueue", back_populates="exercise", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Exercise {self.type} - {self.question[:30]}>"


class Media(Base):
    """
    Bibliothèque de médias (images, sons)

    Stocke tous les assets utilisés dans les leçons
    """

    __tablename__ = "media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    url = Column(String, nullable=False)
    source = Column(String, nullable=True)  # 'ratus_extraction', 'upload', 'generated'
    tags = Column(JSON, default=[])  # ['character', 'ratus', 'syllable', 'ma']
    meta_info = Column(JSON, default={})  # Infos extraction
    uploaded_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<Media {self.filename}>"
