"""
Modèles SQLAlchemy pour l'application Explorito
"""

from app.models.challenge import PythagoreSession, SudokuSession
from app.models.collection import CollectibleUnlock, PointAward
from app.models.content import Exercise, LearningPath, Lesson, Media, Subject
from app.models.gamification import (
    Achievement,
    DailyGoal,
    Reward,
    Streak,
    UserAchievement,
)
from app.models.progress import ExerciseResult, SubjectProgress, UserProgress
from app.models.review import ReviewQueue
from app.models.user import Profile, User

__all__ = [
    "User",
    "Profile",
    "Subject",
    "LearningPath",
    "Lesson",
    "Exercise",
    "Media",
    "UserProgress",
    "ExerciseResult",
    "SubjectProgress",
    "Achievement",
    "UserAchievement",
    "DailyGoal",
    "Streak",
    "Reward",
    "ReviewQueue",
    "CollectibleUnlock",
    "PointAward",
    "PythagoreSession",
    "SudokuSession",
]
