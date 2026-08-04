"""
Schémas Pydantic pour la validation et sérialisation des données
"""

from app.schemas.auth import (
    DevLoginRequest,
    GoogleAuthRequest,
    PinRequest,
    ProfileResponse,
    RefreshTokenRequest,
    Token,
    TokenData,
    UserResponse,
)
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseResponse,
    ExerciseResultResponse,
    ExerciseSubmit,
    ExerciseUpdate,
)
from app.schemas.gamification import (
    AchievementResponse,
    DailyGoalCreate,
    DailyGoalResponse,
    LeaderboardEntry,
    RewardResponse,
    StreakResponse,
    UserAchievementResponse,
)
from app.schemas.lesson import (
    LessonCreate,
    LessonResponse,
    LessonUpdate,
    LessonWithExercises,
)
from app.schemas.progress import (
    LessonProgressResponse,
    ProgressDashboard,
    SubjectProgressResponse,
)
from app.schemas.subject import (
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)

__all__ = [
    "Token",
    "TokenData",
    "GoogleAuthRequest",
    "DevLoginRequest",
    "PinRequest",
    "UserResponse",
    "ProfileResponse",
    "RefreshTokenRequest",
    "SubjectCreate",
    "SubjectUpdate",
    "SubjectResponse",
    "LessonCreate",
    "LessonUpdate",
    "LessonResponse",
    "LessonWithExercises",
    "ExerciseCreate",
    "ExerciseUpdate",
    "ExerciseResponse",
    "ExerciseSubmit",
    "ExerciseResultResponse",
    "ProgressDashboard",
    "SubjectProgressResponse",
    "LessonProgressResponse",
    "AchievementResponse",
    "UserAchievementResponse",
    "StreakResponse",
    "DailyGoalResponse",
    "DailyGoalCreate",
    "RewardResponse",
    "LeaderboardEntry",
]
