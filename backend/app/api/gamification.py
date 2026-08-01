"""
Endpoints de gamification
"""

from datetime import date
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user
from app.api.children import _require_owned_child
from app.core.database import get_db
from app.models.content import Exercise, LearningPath, Lesson, Subject
from app.models.gamification import (
    Achievement,
    DailyGoal,
    Reward,
    Streak,
    UserAchievement,
)
from app.models.progress import ExerciseResult, ProgressStatus, SubjectProgress, UserProgress
from app.models.user import Profile, User, UserRole
from app.schemas.gamification import (
    AchievementResponse,
    ChildHistoryResponse,
    ChildStatsResponse,
    DailyActivity,
    DailyGoalCreate,
    DailyGoalResponse,
    ErrorLogItem,
    LeaderboardEntry,
    LessonHistoryItem,
    RewardResponse,
    StreakResponse,
    SubjectAccuracy,
    UserAchievementResponse,
)
from app.services.gamification import (
    calculate_level_from_xp,
    calculate_next_level_xp,
    get_or_create_daily_goal,
)

router = APIRouter()


@router.get("/achievements", response_model=list[AchievementResponse])
async def list_achievements(db: Annotated[Session, Depends(get_db)], category: str | None = None) -> list[Achievement]:
    """
    Liste tous les achievements disponibles

    Args:
        db: Session de base de données
        category: Filtrer par catégorie (optionnel)

    Returns:
        Liste des achievements
    """
    query = db.query(Achievement)

    if category:
        query = query.filter(Achievement.category == category)

    achievements = query.all()
    return achievements


@router.get("/achievements/me", response_model=list[UserAchievementResponse])
async def get_user_achievements(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UserAchievement]:
    """
    Récupère les achievements débloqués par l'utilisateur actuel

    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Liste des achievements débloqués avec leurs détails
    """
    user_achievements = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == current_user.id)
        .order_by(desc(UserAchievement.unlocked_at))
        .all()
    )

    return user_achievements


@router.get("/streak", response_model=StreakResponse)
async def get_user_streak(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StreakResponse:
    """
    Récupère la série de jours consécutifs de l'utilisateur

    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Informations sur le streak
    """
    # Récupérer ou créer le streak
    streak = db.query(Streak).filter(Streak.user_id == current_user.id).first()

    if not streak:
        # Créer un nouveau streak
        streak = Streak(
            user_id=current_user.id,
            current_streak=0,
            longest_streak=0,
            last_activity_date=None,
            freeze_used=0,
        )
        db.add(streak)
        db.commit()
        db.refresh(streak)

    return StreakResponse(
        current_streak=streak.current_streak,
        longest_streak=streak.longest_streak,
        last_activity_date=streak.last_activity_date,
        freeze_used=streak.freeze_used,
    )


@router.get("/daily-goal", response_model=DailyGoalResponse)
async def get_daily_goal(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DailyGoalResponse:
    """
    Récupère l'objectif quotidien de l'utilisateur pour aujourd'hui

    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Objectif quotidien avec progression
    """
    daily_goal = get_or_create_daily_goal(current_user.id, db)

    # Calculer le pourcentage de progression
    xp_progress = (daily_goal.xp_earned / daily_goal.xp_target * 100) if daily_goal.xp_target > 0 else 0
    lessons_progress = (
        (daily_goal.lessons_completed / daily_goal.lessons_target * 100) if daily_goal.lessons_target > 0 else 0
    )
    progress_percentage = (xp_progress + lessons_progress) / 2

    return DailyGoalResponse(
        id=daily_goal.id,
        date=daily_goal.date,
        xp_target=daily_goal.xp_target,
        xp_earned=daily_goal.xp_earned,
        lessons_target=daily_goal.lessons_target,
        lessons_completed=daily_goal.lessons_completed,
        is_completed=daily_goal.is_completed,
        progress_percentage=round(progress_percentage, 1),
    )


@router.post("/daily-goal", response_model=DailyGoalResponse)
async def create_or_update_daily_goal(
    goal_data: DailyGoalCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DailyGoalResponse:
    """
    Crée ou met à jour l'objectif quotidien de l'utilisateur

    Args:
        goal_data: Nouveaux objectifs XP et leçons
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Objectif quotidien mis à jour
    """
    today = date.today()

    # Récupérer ou créer l'objectif du jour
    daily_goal = db.query(DailyGoal).filter(DailyGoal.user_id == current_user.id, DailyGoal.date == today).first()

    if not daily_goal:
        daily_goal = DailyGoal(
            user_id=current_user.id,
            date=today,
            xp_target=goal_data.xp_target,
            xp_earned=0,
            lessons_target=goal_data.lessons_target,
            lessons_completed=0,
            is_completed=False,
        )
        db.add(daily_goal)
    else:
        # Mettre à jour uniquement les cibles, pas la progression
        daily_goal.xp_target = goal_data.xp_target
        daily_goal.lessons_target = goal_data.lessons_target

        # Recalculer si l'objectif est complété
        if daily_goal.xp_earned >= daily_goal.xp_target and daily_goal.lessons_completed >= daily_goal.lessons_target:
            daily_goal.is_completed = True
        else:
            daily_goal.is_completed = False

    db.commit()
    db.refresh(daily_goal)

    # Calculer le pourcentage de progression
    xp_progress = (daily_goal.xp_earned / daily_goal.xp_target * 100) if daily_goal.xp_target > 0 else 0
    lessons_progress = (
        (daily_goal.lessons_completed / daily_goal.lessons_target * 100) if daily_goal.lessons_target > 0 else 0
    )
    progress_percentage = (xp_progress + lessons_progress) / 2

    return DailyGoalResponse(
        id=daily_goal.id,
        date=daily_goal.date,
        xp_target=daily_goal.xp_target,
        xp_earned=daily_goal.xp_earned,
        lessons_target=daily_goal.lessons_target,
        lessons_completed=daily_goal.lessons_completed,
        is_completed=daily_goal.is_completed,
        progress_percentage=round(progress_percentage, 1),
    )


@router.post("/{child_id}/daily-goal", response_model=DailyGoalResponse)
async def set_child_daily_goal(
    child_id: UUID,
    goal_data: DailyGoalCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DailyGoalResponse:
    """
    Définit l'objectif quotidien d'un enfant (parent uniquement).

    Args:
        child_id: ID de l'enfant.
        goal_data: Cibles XP et leçons.
        current_user: Parent authentifié.
        db: Session de base de données.

    Returns:
        Objectif quotidien de l'enfant.

    Raises:
        HTTPException: 403 si non-parent, 404 si l'enfant n'appartient pas au parent.
    """
    _require_owned_child(child_id, current_user, db)

    today = date.today()
    daily_goal = db.query(DailyGoal).filter(DailyGoal.user_id == child_id, DailyGoal.date == today).first()

    if not daily_goal:
        daily_goal = DailyGoal(
            user_id=child_id,
            date=today,
            xp_target=goal_data.xp_target,
            xp_earned=0,
            lessons_target=goal_data.lessons_target,
            lessons_completed=0,
            is_completed=False,
        )
        db.add(daily_goal)
    else:
        daily_goal.xp_target = goal_data.xp_target
        daily_goal.lessons_target = goal_data.lessons_target
        daily_goal.is_completed = bool(
            daily_goal.xp_earned >= daily_goal.xp_target and daily_goal.lessons_completed >= daily_goal.lessons_target
        )

    db.commit()
    db.refresh(daily_goal)

    xp_progress = (daily_goal.xp_earned / daily_goal.xp_target * 100) if daily_goal.xp_target > 0 else 0
    lessons_progress = (
        (daily_goal.lessons_completed / daily_goal.lessons_target * 100) if daily_goal.lessons_target > 0 else 0
    )
    progress_percentage = (xp_progress + lessons_progress) / 2

    return DailyGoalResponse(
        id=daily_goal.id,
        date=daily_goal.date,
        xp_target=daily_goal.xp_target,
        xp_earned=daily_goal.xp_earned,
        lessons_target=daily_goal.lessons_target,
        lessons_completed=daily_goal.lessons_completed,
        is_completed=daily_goal.is_completed,
        progress_percentage=round(progress_percentage, 1),
    )


@router.get("/rewards", response_model=list[RewardResponse])
async def get_user_rewards(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Reward]:
    """
    Récupère les récompenses débloquées par l'utilisateur

    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Liste des récompenses débloquées
    """
    rewards = db.query(Reward).filter(Reward.user_id == current_user.id).order_by(desc(Reward.unlocked_at)).all()

    return rewards


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_family_leaderboard(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[LeaderboardEntry]:
    """
    Récupère le classement de la famille de l'utilisateur

    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Classement trié par XP total

    Raises:
        HTTPException: Si l'utilisateur n'appartient à aucune famille
    """
    # Déterminer l'unité familiale via Profile.parent_id.
    # L'ancre est le parent : si l'utilisateur courant est un enfant rattaché,
    # on remonte à son parent ; sinon l'utilisateur est lui-même l'ancre.
    current_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()

    if current_profile and current_profile.parent_id:
        anchor_id = current_profile.parent_id
    else:
        anchor_id = current_user.id

    # Membres = l'ancre (parent) + tous les enfants rattachés à l'ancre
    child_profiles = db.query(Profile).filter(Profile.parent_id == anchor_id).all()
    member_ids = [anchor_id] + [profile.user_id for profile in child_profiles]

    if len(member_ids) <= 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune famille trouvée. Le classement est disponible uniquement pour les familles ayant plusieurs membres.",
        )

    # Construire le classement
    leaderboard = []

    for user_id in member_ids:
        # Récupérer l'utilisateur et son profil
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            continue

        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            continue

        # Calculer l'XP total
        total_xp = db.query(func.sum(SubjectProgress.total_xp)).filter(SubjectProgress.user_id == user_id).scalar() or 0

        # Récupérer le streak
        streak = db.query(Streak).filter(Streak.user_id == user_id).first()
        current_streak = streak.current_streak if streak else 0

        # Compter les leçons complétées
        from app.models.progress import ProgressStatus, UserProgress

        lessons_completed = (
            db.query(func.count(UserProgress.id))
            .filter(
                UserProgress.user_id == user_id,
                UserProgress.status == ProgressStatus.COMPLETED,
            )
            .scalar()
            or 0
        )

        # Calculer le niveau
        level = calculate_level_from_xp(int(total_xp))

        leaderboard.append(
            LeaderboardEntry(
                user_id=user_id,
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
                total_xp=int(total_xp),
                level=level,
                current_streak=current_streak,
                lessons_completed=int(lessons_completed),
                rank=0,  # Sera calculé après le tri
            )
        )

    # Trier par XP décroissant
    leaderboard.sort(key=lambda x: x.total_xp, reverse=True)

    # Attribuer les rangs
    for idx, entry in enumerate(leaderboard, start=1):
        entry.rank = idx

    return leaderboard


@router.get("/{child_id}/stats", response_model=ChildStatsResponse)
async def get_child_stats(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChildStatsResponse:
    """
    Récupère les statistiques de gamification d'un enfant

    Args:
        child_id: ID de l'enfant
        current_user: Utilisateur authentifié (admin, parent, ou enfant)
        db: Session de base de données

    Returns:
        Statistiques de gamification de l'enfant

    Raises:
        HTTPException: Si l'utilisateur n'a pas accès aux stats de cet enfant
    """
    # Permission check: Allow admins, parents accessing their children, or children accessing their OWN stats
    if current_user.role == UserRole.ADMIN:
        # Admin can access any child stats
        pass
    elif current_user.role == UserRole.CHILD:
        # Child can only access their OWN stats
        if str(current_user.id) != str(child_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez accéder qu'à vos propres statistiques",
            )
    elif current_user.role == UserRole.PARENT:
        # Parent can only access their children's stats
        child_profile = (
            db.query(Profile).filter(Profile.user_id == child_id, Profile.parent_id == current_user.id).first()
        )
        if not child_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enfant non trouvé ou n'appartient pas à ce parent",
            )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    # Calculer l'XP total
    total_xp = db.query(func.sum(SubjectProgress.total_xp)).filter(SubjectProgress.user_id == child_id).scalar() or 0

    # Calculer le niveau
    level = calculate_level_from_xp(int(total_xp))
    next_level_xp = calculate_next_level_xp(level)
    current_level_xp = int(total_xp) % 100  # XP dans le niveau actuel (simplifié)

    # Récupérer le streak
    streak = db.query(Streak).filter(Streak.user_id == child_id).first()
    current_streak = streak.current_streak if streak else 0
    longest_streak = streak.longest_streak if streak else 0

    # Compter les exercices complétés (basé sur UserProgress)
    total_exercises = (
        db.query(func.count(UserProgress.id))
        .filter(
            UserProgress.user_id == child_id,
            UserProgress.status == ProgressStatus.COMPLETED,
        )
        .scalar()
        or 0
    )

    # Récupérer les achievements
    user_achievements = db.query(UserAchievement).filter(UserAchievement.user_id == child_id).all()

    return ChildStatsResponse.model_validate(
        {
            "child_id": child_id,
            "total_xp": int(total_xp),
            "level": level,
            "current_level_xp": current_level_xp,
            "next_level_xp": next_level_xp,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_exercises_completed": int(total_exercises),
            "achievements": user_achievements,
        }
    )


@router.get("/{child_id}/achievements", response_model=list[UserAchievementResponse])
async def get_child_achievements(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UserAchievement]:
    """
    Récupère les achievements d'un enfant

    Args:
        child_id: ID de l'enfant
        current_user: Utilisateur authentifié (admin, parent, ou enfant)
        db: Session de base de données

    Returns:
        Liste des achievements de l'enfant

    Raises:
        HTTPException: Si l'utilisateur n'a pas accès aux achievements de cet enfant
    """
    # Permission check: Allow admins, parents accessing their children, or children accessing their OWN achievements
    if current_user.role == UserRole.ADMIN:
        # Admin can access any child achievements
        pass
    elif current_user.role == UserRole.CHILD:
        # Child can only access their OWN achievements
        if str(current_user.id) != str(child_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez accéder qu'à vos propres achievements",
            )
    elif current_user.role == UserRole.PARENT:
        # Parent can only access their children's achievements
        child_profile = (
            db.query(Profile).filter(Profile.user_id == child_id, Profile.parent_id == current_user.id).first()
        )
        if not child_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enfant non trouvé ou n'appartient pas à ce parent",
            )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    # Récupérer les achievements de l'enfant
    user_achievements = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == child_id)
        .order_by(desc(UserAchievement.unlocked_at))
        .all()
    )

    return user_achievements


def _assert_child_access(child_id: "UUID", current_user: "User", db: "Session") -> None:
    """Autorise l'admin, le parent propriétaire, ou l'enfant lui-même."""
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.CHILD:
        if str(current_user.id) != str(child_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
        return
    if current_user.role == UserRole.PARENT:
        owned = db.query(Profile).filter(Profile.user_id == child_id, Profile.parent_id == current_user.id).first()
        if not owned:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enfant non trouvé")
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")


@router.get("/{child_id}/history", response_model=ChildHistoryResponse)
async def get_child_history(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChildHistoryResponse:
    """
    Historique de progression d'un enfant : activité quotidienne, frise des
    leçons, journal des erreurs et réussite par matière (parent-facing).
    """
    _assert_child_access(child_id, current_user, db)

    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=14)

    # --- Activité quotidienne (14 derniers jours) ---
    def _blank() -> dict[str, int]:
        return {"lessons_completed": 0, "exercises": 0, "correct": 0, "wrong": 0, "minutes": 0}

    daily_map: dict[Any, dict[str, int]] = {}
    for ts, is_correct in db.query(ExerciseResult.timestamp, ExerciseResult.is_correct).filter(
        ExerciseResult.user_id == child_id, ExerciseResult.timestamp >= cutoff
    ):
        entry = daily_map.setdefault(ts.date(), _blank())
        entry["exercises"] += 1
        entry["correct" if is_correct else "wrong"] += 1
    for completed_at, time_spent in db.query(UserProgress.completed_at, UserProgress.time_spent).filter(
        UserProgress.user_id == child_id,
        UserProgress.status == ProgressStatus.COMPLETED,
        UserProgress.completed_at >= cutoff,
    ):
        if completed_at is None:
            continue
        entry = daily_map.setdefault(completed_at.date(), _blank())
        entry["lessons_completed"] += 1
        entry["minutes"] += int((time_spent or 0) / 60)
    daily = [DailyActivity(date=d, **v) for d, v in sorted(daily_map.items())]

    # --- Frise des leçons (terminées ou en cours), plus récentes d'abord ---
    lesson_rows = (
        db.query(UserProgress, Lesson, Subject)
        .join(Lesson, UserProgress.lesson_id == Lesson.id)
        .join(LearningPath, Lesson.path_id == LearningPath.id)
        .join(Subject, LearningPath.subject_id == Subject.id)
        .filter(UserProgress.user_id == child_id)
        .order_by(desc(func.coalesce(UserProgress.completed_at, UserProgress.started_at)))
        .limit(40)
        .all()
    )
    lessons = [
        LessonHistoryItem(
            lesson_id=lesson.id,
            lesson_name=lesson.name,
            subject_name=subject.name,
            subject_icon=subject.icon,
            status=up.status.value,
            score=up.score,
            stars=up.stars,
            attempts=up.attempts or 0,
            completed_at=up.completed_at,
        )
        for up, lesson, subject in lesson_rows
    ]

    # --- Journal des erreurs (exercices ratés), plus récents d'abord ---
    error_rows = (
        db.query(ExerciseResult, Exercise, Lesson, Subject)
        .join(Exercise, ExerciseResult.exercise_id == Exercise.id)
        .join(Lesson, Exercise.lesson_id == Lesson.id)
        .join(LearningPath, Lesson.path_id == LearningPath.id)
        .join(Subject, LearningPath.subject_id == Subject.id)
        .filter(ExerciseResult.user_id == child_id, ExerciseResult.is_correct.is_(False))
        .order_by(desc(ExerciseResult.timestamp))
        .limit(40)
        .all()
    )
    errors = [
        ErrorLogItem(
            exercise_id=exercise.id,
            question=exercise.question,
            lesson_name=lesson.name,
            subject_name=subject.name,
            timestamp=result.timestamp,
        )
        for result, exercise, lesson, subject in error_rows
    ]

    # --- Réussite par matière ---
    subject_rows = (
        db.query(
            Subject.name,
            Subject.icon,
            func.count(ExerciseResult.id),
            func.sum(case((ExerciseResult.is_correct, 1), else_=0)),
        )
        .join(Exercise, ExerciseResult.exercise_id == Exercise.id)
        .join(Lesson, Exercise.lesson_id == Lesson.id)
        .join(LearningPath, Lesson.path_id == LearningPath.id)
        .join(Subject, LearningPath.subject_id == Subject.id)
        .filter(ExerciseResult.user_id == child_id)
        .group_by(Subject.name, Subject.icon)
        .all()
    )
    by_subject = [
        SubjectAccuracy(
            subject_name=name,
            subject_icon=icon,
            attempts=int(attempts),
            correct=int(correct or 0),
            accuracy=round(100 * int(correct or 0) / int(attempts)) if attempts else 0,
        )
        for name, icon, attempts, correct in subject_rows
    ]
    by_subject.sort(key=lambda s: s.attempts, reverse=True)

    return ChildHistoryResponse(daily=daily, lessons=lessons, errors=errors, by_subject=by_subject)
