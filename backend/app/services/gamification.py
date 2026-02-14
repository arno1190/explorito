"""
Service de gamification

Logique métier pour les achievements, XP, niveaux, et streaks
"""

from datetime import date, datetime, timedelta
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.gamification import Achievement, UserAchievement, Streak, DailyGoal
from app.models.progress import SubjectProgress, UserProgress, ProgressStatus


def calculate_level_from_xp(xp: int) -> int:
    """
    Calcule le niveau à partir de l'XP total

    Formule: Level = floor(sqrt(XP / 100)) + 1
    - Level 1: 0 XP
    - Level 2: 100 XP
    - Level 3: 400 XP
    - Level 4: 900 XP
    - Level 5: 1600 XP

    Args:
        xp: Total XP de l'utilisateur

    Returns:
        Niveau calculé (minimum 1)
    """
    import math

    if xp < 0:
        return 1
    return int(math.sqrt(xp / 100)) + 1


def calculate_next_level_xp(current_level: int) -> int:
    """
    Calcule l'XP nécessaire pour atteindre le prochain niveau

    Args:
        current_level: Niveau actuel

    Returns:
        XP nécessaire pour le prochain niveau
    """
    next_level = current_level + 1
    return (next_level - 1) ** 2 * 100


def award_xp(user_id: UUID, amount: int, subject_id: UUID | None, db: Session) -> int:
    """
    Attribue de l'XP à un utilisateur et met à jour son niveau

    Args:
        user_id: ID de l'utilisateur
        amount: Quantité d'XP à attribuer
        subject_id: ID de la matière (optionnel)
        db: Session de base de données

    Returns:
        Nouveau total d'XP de l'utilisateur
    """
    if amount <= 0:
        return 0

    # Mettre à jour la progression de la matière si fournie
    if subject_id:
        subject_progress = (
            db.query(SubjectProgress)
            .filter(
                SubjectProgress.user_id == user_id,
                SubjectProgress.subject_id == subject_id,
            )
            .first()
        )

        if not subject_progress:
            subject_progress = SubjectProgress(
                user_id=user_id,
                subject_id=subject_id,
                total_xp=amount,
                level=calculate_level_from_xp(amount),
                last_activity=datetime.utcnow(),
            )
            db.add(subject_progress)
        else:
            subject_progress.total_xp += amount
            subject_progress.level = calculate_level_from_xp(subject_progress.total_xp)
            subject_progress.last_activity = datetime.utcnow()

    # Calculer l'XP total de l'utilisateur à travers toutes les matières
    total_xp = (
        db.query(func.sum(SubjectProgress.total_xp))
        .filter(SubjectProgress.user_id == user_id)
        .scalar()
        or 0
    )

    # Mettre à jour l'objectif quotidien
    today = date.today()
    daily_goal = (
        db.query(DailyGoal)
        .filter(DailyGoal.user_id == user_id, DailyGoal.date == today)
        .first()
    )

    if daily_goal:
        daily_goal.xp_earned += amount
        if (
            daily_goal.xp_earned >= daily_goal.xp_target
            and daily_goal.lessons_completed >= daily_goal.lessons_target
        ):
            daily_goal.is_completed = True

    db.commit()
    return int(total_xp)


def update_streak(user_id: UUID, db: Session) -> Streak:
    """
    Met à jour la série de jours consécutifs d'un utilisateur

    Args:
        user_id: ID de l'utilisateur
        db: Session de base de données

    Returns:
        Objet Streak mis à jour
    """
    today = date.today()
    yesterday = today - timedelta(days=1)

    # Récupérer ou créer le streak
    streak = db.query(Streak).filter(Streak.user_id == user_id).first()

    if not streak:
        streak = Streak(
            user_id=user_id,
            current_streak=1,
            longest_streak=1,
            last_activity_date=today,
        )
        db.add(streak)
    else:
        # Si dernière activité était hier, incrémenter le streak
        if streak.last_activity_date == yesterday:
            streak.current_streak += 1
            streak.last_activity_date = today
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
        # Si dernière activité était aujourd'hui, ne rien faire
        elif streak.last_activity_date == today:
            pass
        # Sinon, réinitialiser le streak
        else:
            streak.current_streak = 1
            streak.last_activity_date = today

    db.commit()
    db.refresh(streak)
    return streak


def check_and_unlock_achievements(user_id: UUID, db: Session) -> List[Achievement]:
    """
    Vérifie et débloque les achievements pour un utilisateur

    Args:
        user_id: ID de l'utilisateur
        db: Session de base de données

    Returns:
        Liste des nouveaux achievements débloqués
    """
    newly_unlocked = []

    # Récupérer tous les achievements
    all_achievements = db.query(Achievement).all()

    # Récupérer les achievements déjà débloqués
    unlocked_ids = set(
        ua.achievement_id
        for ua in db.query(UserAchievement)
        .filter(UserAchievement.user_id == user_id)
        .all()
    )

    # Récupérer les statistiques de l'utilisateur
    total_xp = (
        db.query(func.sum(SubjectProgress.total_xp))
        .filter(SubjectProgress.user_id == user_id)
        .scalar()
        or 0
    )

    lessons_completed = (
        db.query(func.count(UserProgress.id))
        .filter(
            UserProgress.user_id == user_id,
            UserProgress.status == ProgressStatus.COMPLETED,
        )
        .scalar()
        or 0
    )

    streak = db.query(Streak).filter(Streak.user_id == user_id).first()
    current_streak = streak.current_streak if streak else 0

    # Vérifier chaque achievement
    for achievement in all_achievements:
        if achievement.id in unlocked_ids:
            continue

        criteria = achievement.criteria
        criteria_type = criteria.get("type")
        criteria_value = criteria.get("value", 0)

        should_unlock = False

        # Vérifier les critères selon le type
        if criteria_type == "xp" and total_xp >= criteria_value:
            should_unlock = True
        elif criteria_type == "lessons" and lessons_completed >= criteria_value:
            should_unlock = True
        elif criteria_type == "streak" and current_streak >= criteria_value:
            should_unlock = True
        elif criteria_type == "first_lesson" and lessons_completed >= 1:
            should_unlock = True
        elif criteria_type == "perfect_lesson":
            # Vérifier s'il y a au moins une leçon avec 100% de score
            perfect_lessons = (
                db.query(UserProgress)
                .filter(
                    UserProgress.user_id == user_id,
                    UserProgress.score == 100,
                    UserProgress.status == ProgressStatus.COMPLETED,
                )
                .count()
            )
            if perfect_lessons >= criteria_value:
                should_unlock = True

        # Débloquer l'achievement
        if should_unlock:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                unlocked_at=datetime.utcnow(),
            )
            db.add(user_achievement)
            newly_unlocked.append(achievement)

    if newly_unlocked:
        db.commit()

    return newly_unlocked


def get_or_create_daily_goal(user_id: UUID, db: Session) -> DailyGoal:
    """
    Récupère ou crée l'objectif quotidien pour aujourd'hui

    Args:
        user_id: ID de l'utilisateur
        db: Session de base de données

    Returns:
        Objectif quotidien
    """
    today = date.today()

    daily_goal = (
        db.query(DailyGoal)
        .filter(DailyGoal.user_id == user_id, DailyGoal.date == today)
        .first()
    )

    if not daily_goal:
        daily_goal = DailyGoal(
            user_id=user_id,
            date=today,
            xp_target=50,
            xp_earned=0,
            lessons_target=3,
            lessons_completed=0,
            is_completed=False,
        )
        db.add(daily_goal)
        db.commit()
        db.refresh(daily_goal)

    return daily_goal


def update_daily_goal_lesson_count(user_id: UUID, db: Session) -> None:
    """
    Met à jour le compte de leçons complétées dans l'objectif quotidien

    Args:
        user_id: ID de l'utilisateur
        db: Session de base de données
    """
    today = date.today()
    daily_goal = get_or_create_daily_goal(user_id, db)

    # Compter les leçons complétées aujourd'hui
    lessons_today = (
        db.query(func.count(UserProgress.id))
        .filter(
            UserProgress.user_id == user_id,
            UserProgress.status == ProgressStatus.COMPLETED,
            func.date(UserProgress.completed_at) == today,
        )
        .scalar()
        or 0
    )

    daily_goal.lessons_completed = int(lessons_today)

    if (
        daily_goal.xp_earned >= daily_goal.xp_target
        and daily_goal.lessons_completed >= daily_goal.lessons_target
    ):
        daily_goal.is_completed = True

    db.commit()
