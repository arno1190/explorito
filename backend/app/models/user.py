"""
Modèles utilisateur et profil
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    """Rôles utilisateur"""

    ADMIN = "admin"
    PARENT = "parent"
    CHILD = "child"


class User(Base):
    """
    Utilisateur de l'application

    Un utilisateur peut être:
    - Un administrateur (gestion du contenu)
    - Un parent (gestion de famille)
    - Un enfant (apprenant)
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CHILD)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    profile = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="Profile.user_id",
    )
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    exercise_results = relationship("ExerciseResult", back_populates="user", cascade="all, delete-orphan")
    subject_progress = relationship("SubjectProgress", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    daily_goals = relationship("DailyGoal", back_populates="user", cascade="all, delete-orphan")
    streak = relationship("Streak", back_populates="user", uselist=False, cascade="all, delete-orphan")
    rewards = relationship("Reward", back_populates="user", cascade="all, delete-orphan")
    review_queue = relationship("ReviewQueue", back_populates="user", cascade="all, delete-orphan")
    pokemon_unlocks = relationship("PokemonUnlock", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Profile(Base):
    """
    Profil utilisateur avec informations personnelles
    """

    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    display_name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    is_child = Column(Boolean, default=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    settings = Column(JSON, default={})  # Préférences UI, son, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    user = relationship("User", back_populates="profile", foreign_keys=[user_id])
    parent = relationship("User", foreign_keys=[parent_id])

    def __repr__(self):
        return f"<Profile {self.display_name}>"
