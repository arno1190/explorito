"""
Modèles SQLAlchemy pour l'application Explorito
"""

from app.models.collection import PokemonUnlock
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
    "PokemonUnlock",
]
