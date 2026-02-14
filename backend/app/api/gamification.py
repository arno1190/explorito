"""
Endpoints de gamification
"""

from typing import Annotated, List
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.models.user import User, Profile, UserRole
from app.models.gamification import (
    Achievement,
    UserAchievement,
    Streak,
    DailyGoal,
    Reward,
)
from app.models.progress import SubjectProgress, UserProgress, ProgressStatus
from app.models.family import FamilyMember
from app.schemas.gamification import (
    AchievementResponse,
    UserAchievementResponse,
    StreakResponse,
    DailyGoalResponse,
    DailyGoalCreate,
    RewardResponse,
    LeaderboardEntry,
)
from app.api.auth import get_current_active_user
from app.services.gamification import (
    get_or_create_daily_goal,
    calculate_level_from_xp,
    calculate_next_level_xp,
)


router = APIRouter()


@router.get("/achievements", response_model=List[AchievementResponse])
async def list_achievements(
    db: Annotated[Session, Depends(get_db)], category: str | None = None
) -> List[Achievement]:
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


@router.get("/achievements/me", response_model=List[UserAchievementResponse])
async def get_user_achievements(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> List[UserAchievement]:
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
    xp_progress = (
        (daily_goal.xp_earned / daily_goal.xp_target * 100)
        if daily_goal.xp_target > 0
        else 0
    )
    lessons_progress = (
        (daily_goal.lessons_completed / daily_goal.lessons_target * 100)
        if daily_goal.lessons_target > 0
        else 0
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
    daily_goal = (
        db.query(DailyGoal)
        .filter(DailyGoal.user_id == current_user.id, DailyGoal.date == today)
        .first()
    )

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
        if (
            daily_goal.xp_earned >= daily_goal.xp_target
            and daily_goal.lessons_completed >= daily_goal.lessons_target
        ):
            daily_goal.is_completed = True
        else:
            daily_goal.is_completed = False

    db.commit()
    db.refresh(daily_goal)

    # Calculer le pourcentage de progression
    xp_progress = (
        (daily_goal.xp_earned / daily_goal.xp_target * 100)
        if daily_goal.xp_target > 0
        else 0
    )
    lessons_progress = (
        (daily_goal.lessons_completed / daily_goal.lessons_target * 100)
        if daily_goal.lessons_target > 0
        else 0
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


@router.get("/rewards", response_model=List[RewardResponse])
async def get_user_rewards(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> List[Reward]:
    """
    Récupère les récompenses débloquées par l'utilisateur

    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Liste des récompenses débloquées
    """
    rewards = (
        db.query(Reward)
        .filter(Reward.user_id == current_user.id)
        .order_by(desc(Reward.unlocked_at))
        .all()
    )

    return rewards


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_family_leaderboard(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> List[LeaderboardEntry]:
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
    # Trouver la famille de l'utilisateur
    family_membership = (
        db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).first()
    )

    if not family_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vous n'appartenez à aucune famille. Le classement est disponible uniquement pour les familles.",
        )

    family_id = family_membership.family_id

    # Récupérer tous les membres de la famille
    family_members = (
        db.query(FamilyMember).filter(FamilyMember.family_id == family_id).all()
    )

    member_ids = [fm.user_id for fm in family_members]

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
        total_xp = (
            db.query(func.sum(SubjectProgress.total_xp))
            .filter(SubjectProgress.user_id == user_id)
            .scalar()
            or 0
        )

        # Récupérer le streak
        streak = db.query(Streak).filter(Streak.user_id == user_id).first()
        current_streak = streak.current_streak if streak else 0

        # Compter les leçons complétées
        from app.models.progress import UserProgress, ProgressStatus

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


@router.get("/{child_id}/stats")
async def get_child_stats(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
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
            db.query(Profile)
            .filter(Profile.user_id == child_id, Profile.parent_id == current_user.id)
            .first()
        )
        if not child_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enfant non trouvé ou n'appartient pas à ce parent",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé"
        )

    # Calculer l'XP total
    total_xp = (
        db.query(func.sum(SubjectProgress.total_xp))
        .filter(SubjectProgress.user_id == child_id)
        .scalar()
        or 0
    )

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
    user_achievements = (
        db.query(UserAchievement).filter(UserAchievement.user_id == child_id).all()
    )

    return {
        "child_id": str(child_id),
        "total_xp": int(total_xp),
        "level": level,
        "current_level_xp": current_level_xp,
        "next_level_xp": next_level_xp,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_exercises_completed": int(total_exercises),
        "achievements": user_achievements,
    }


@router.get("/{child_id}/achievements", response_model=List[UserAchievementResponse])
async def get_child_achievements(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> List[UserAchievement]:
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
            db.query(Profile)
            .filter(Profile.user_id == child_id, Profile.parent_id == current_user.id)
            .first()
        )
        if not child_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enfant non trouvé ou n'appartient pas à ce parent",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé"
        )

    # Récupérer les achievements de l'enfant
    user_achievements = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == child_id)
        .order_by(desc(UserAchievement.unlocked_at))
        .all()
    )

    return user_achievements
