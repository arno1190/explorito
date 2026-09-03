"""
Modèles SQLAlchemy pour l'application Explorito
"""

from app.models.admin import LoginEvent
from app.models.announcement import Announcement, AnnouncementDelivery
from app.models.challenge import PythagoreSession, SudokuSession
from app.models.collection import CollectibleUnlock, PointAward
from app.models.content import Exercise, LearningPath, Lesson, Media, Subject
from app.models.contribution import (
    ContributionQuota,
    ContributorProfile,
    PackAuditLog,
    PackReport,
    UploadToken,
)
from app.models.gamification import (
    Achievement,
    DailyGoal,
    Reward,
    Streak,
    UserAchievement,
)
from app.models.guardianship import CoParentLink, Guardianship, Invitation
from app.models.pack import ChildPackAccess, Pack, PackRequest
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
    "Pack",
    "ChildPackAccess",
    "PackRequest",
    "ContributorProfile",
    "UploadToken",
    "PackReport",
    "PackAuditLog",
    "ContributionQuota",
    "Announcement",
    "AnnouncementDelivery",
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
    "Guardianship",
    "CoParentLink",
    "Invitation",
    "LoginEvent",
]
