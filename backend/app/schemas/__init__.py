"""
Schémas Pydantic pour la validation et sérialisation des données
"""

from app.schemas.auth import (
    Token,
    TokenData,
    UserLogin,
    UserRegister,
    UserResponse,
    ProfileResponse,
    RefreshTokenRequest,
)
from app.schemas.subject import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
)
from app.schemas.lesson import (
    LessonCreate,
    LessonUpdate,
    LessonResponse,
    LessonWithExercises,
)
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseUpdate,
    ExerciseResponse,
    ExerciseSubmit,
    ExerciseResultResponse,
)
from app.schemas.progress import (
    ProgressDashboard,
    SubjectProgressResponse,
    LessonProgressResponse,
)
from app.schemas.gamification import (
    AchievementResponse,
    UserAchievementResponse,
    StreakResponse,
    DailyGoalResponse,
    DailyGoalCreate,
    RewardResponse,
    LeaderboardEntry,
)

__all__ = [
    "Token",
    "TokenData",
    "UserLogin",
    "UserRegister",
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
