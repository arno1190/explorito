"""
Modèles de gamification
"""

import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    Boolean,
    ForeignKey,
    JSON,
    Enum,
    Date,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class AchievementRarity(str, enum.Enum):
    """Rareté des achievements"""

    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class Achievement(Base):
    """
    Achievement / Badge déblocable

    Exemples: "Première leçon", "Série de 7 jours", "100 exercices réussis"
    """

    __tablename__ = "achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    criteria = Column(JSON, nullable=False)  # {type: 'streak', value: 7}
    rarity = Column(Enum(AchievementRarity), default=AchievementRarity.COMMON)
    category = Column(String, nullable=True)  # 'reading', 'math', 'global'

    # Relations
    user_achievements = relationship(
        "UserAchievement", back_populates="achievement", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Achievement {self.name} ({self.rarity})>"


class UserAchievement(Base):
    """
    Achievement débloqué par un utilisateur
    """

    __tablename__ = "user_achievements"
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    achievement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

    def __repr__(self):
        return (
            f"<UserAchievement user={self.user_id} achievement={self.achievement_id}>"
        )


class DailyGoal(Base):
    """
    Objectif quotidien d'un utilisateur

    Exemples: "Gagner 50 XP", "Faire 3 leçons"
    """

    __tablename__ = "daily_goals"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_daily_goal"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False, default=date.today, index=True)
    xp_target = Column(Integer, default=50)
    xp_earned = Column(Integer, default=0)
    lessons_target = Column(Integer, default=3)
    lessons_completed = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)

    # Relations
    user = relationship("User", back_populates="daily_goals")

    def __repr__(self):
        return f"<DailyGoal user={self.user_id} date={self.date} completed={self.is_completed}>"


class Streak(Base):
    """
    Série de jours consécutifs d'activité

    Enregistre la série actuelle et la plus longue
    """

    __tablename__ = "streaks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(Date, nullable=True)
    freeze_used = Column(Integer, default=0)  # Nombre de jokers utilisés

    # Relations
    user = relationship("User", back_populates="streak")

    def __repr__(self):
        return f"<Streak user={self.user_id} current={self.current_streak} longest={self.longest_streak}>"


class Reward(Base):
    """
    Récompense virtuelle débloquée

    Exemples: stickers, trophées, avatars, thèmes
    """

    __tablename__ = "rewards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(String, nullable=False)  # 'sticker', 'trophy', 'avatar', 'theme'
    name = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    user = relationship("User", back_populates="rewards")

    def __repr__(self):
        return f"<Reward user={self.user_id} type={self.type} name={self.name}>"
