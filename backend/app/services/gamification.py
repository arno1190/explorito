"""
Service de gamification

Logique métier pour les achievements, XP, niveaux, et streaks
"""

from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Exercise, Lesson
from app.models.gamification import Achievement, DailyGoal, Streak, UserAchievement
from app.models.progress import (
    ExerciseResult,
    ProgressStatus,
    SubjectProgress,
    UserProgress,
)


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

        # La session applicative utilise autoflush=False : on force le flush pour
        # que l'agrégat SUM ci-dessous voie la modification qu'on vient de faire.
        db.flush()

    # Calculer l'XP total de l'utilisateur à travers toutes les matières
    total_xp = db.query(func.sum(SubjectProgress.total_xp)).filter(SubjectProgress.user_id == user_id).scalar() or 0

    # Mettre à jour l'objectif quotidien
    today = date.today()
    daily_goal = db.query(DailyGoal).filter(DailyGoal.user_id == user_id, DailyGoal.date == today).first()

    if daily_goal:
        daily_goal.xp_earned += amount
        if daily_goal.xp_earned >= daily_goal.xp_target and daily_goal.lessons_completed >= daily_goal.lessons_target:
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


def check_and_unlock_achievements(user_id: UUID, db: Session) -> list[Achievement]:
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
    unlocked_ids = {
        ua.achievement_id for ua in db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()
    }

    # Récupérer les statistiques de l'utilisateur
    total_xp = db.query(func.sum(SubjectProgress.total_xp)).filter(SubjectProgress.user_id == user_id).scalar() or 0

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

    daily_goal = db.query(DailyGoal).filter(DailyGoal.user_id == user_id, DailyGoal.date == today).first()

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

    if daily_goal.xp_earned >= daily_goal.xp_target and daily_goal.lessons_completed >= daily_goal.lessons_target:
        daily_goal.is_completed = True

    db.commit()


def xp_for_exercise(exercise: Exercise) -> int:
    """XP de base d'un exercice selon sa difficulté (issue #6).

    Un exercice « hard » rapporte plus qu'un « easy ». La correspondance est
    configurable via ``settings.XP_BY_DIFFICULTY`` ; on retombe sur
    ``settings.XP_PER_EXERCISE`` pour toute difficulté inconnue ou absente.

    Args:
        exercise: Exercice évalué (sa ``difficulty`` peut être un enum ou None).

    Returns:
        Nombre de points de base à attribuer pour une première bonne réponse.
    """
    raw = getattr(exercise.difficulty, "value", exercise.difficulty)
    difficulty = str(raw) if raw is not None else ""
    return settings.XP_BY_DIFFICULTY.get(difficulty, settings.XP_PER_EXERCISE)


def _stars_from_score(score: int) -> int:
    """Convertit un score (0-100) en nombre d'étoiles (1-3) pour une leçon terminée."""
    if score >= 90:
        return 3
    if score >= 75:
        return 2
    return 1


def process_exercise_result(
    user_id: UUID,
    exercise: Exercise,
    is_correct: bool,
    time_taken: int | None,
    db: Session,
) -> dict[str, Any]:
    """
    Orchestre la progression après la soumission d'un exercice.

    Met à jour :class:`UserProgress` de la leçon (tentatives, temps, statut),
    attribue l'XP et met à jour la série en cas de bonne réponse, détecte la
    complétion de la leçon (tous les exercices réussis au moins une fois) et
    débloque les achievements éligibles.

    Args:
        user_id: ID de l'utilisateur.
        exercise: Exercice soumis (avec ``lesson`` chargeable).
        is_correct: Résultat de la correction.
        time_taken: Temps passé sur l'exercice (secondes), optionnel.
        db: Session de base de données.

    Returns:
        Résumé de progression : xp attribué, xp total, série courante, complétion
        de la leçon, score/étoiles éventuels et nouveaux achievements.
    """
    lesson: Lesson = exercise.lesson
    subject_id: UUID = lesson.path.subject_id

    # --- UserProgress de la leçon (créé au premier passage) ---
    progress = (
        db.query(UserProgress)
        .filter(
            UserProgress.user_id == user_id,
            UserProgress.lesson_id == lesson.id,
        )
        .first()
    )
    now = datetime.utcnow()
    if progress is None:
        progress = UserProgress(
            user_id=user_id,
            lesson_id=lesson.id,
            status=ProgressStatus.STARTED,
            attempts=0,
            time_spent=0,
            started_at=now,
        )
        db.add(progress)

    progress.attempts = (progress.attempts or 0) + 1
    progress.time_spent = (progress.time_spent or 0) + (time_taken or 0)
    if progress.status in (ProgressStatus.LOCKED, ProgressStatus.AVAILABLE):
        progress.status = ProgressStatus.STARTED
    if progress.started_at is None:
        progress.started_at = now

    xp_awarded = 0
    total_xp = 0
    current_streak = 0
    lesson_completed = False
    lesson_score: int | None = None
    lesson_stars: int | None = None
    new_achievements: list[Achievement] = []

    if is_correct:
        # XP par exercice, anti-farm : le résultat courant est déjà persisté par
        # l'endpoint avant cet appel, donc les décomptes ci-dessous l'incluent.
        # - première réussite au tout premier essai  -> plein tarif
        # - première réussite après un ou des échecs  -> tarif réduit (redo)
        # - exercice déjà réussi auparavant           -> 0 (anti-farm)
        result_count = (
            db.query(func.count(ExerciseResult.id))
            .filter(
                ExerciseResult.user_id == user_id,
                ExerciseResult.exercise_id == exercise.id,
            )
            .scalar()
            or 0
        )
        correct_count = (
            db.query(func.count(ExerciseResult.id))
            .filter(
                ExerciseResult.user_id == user_id,
                ExerciseResult.exercise_id == exercise.id,
                ExerciseResult.is_correct.is_(True),
            )
            .scalar()
            or 0
        )
        prior_correct = int(correct_count) - 1  # hors résultat courant
        prior_attempts = int(result_count) - 1
        base_xp = xp_for_exercise(exercise)  # pondéré par la difficulté (issue #6)
        if prior_correct > 0:
            exercise_xp = 0
        elif prior_attempts > 0:
            exercise_xp = int(base_xp * settings.XP_REDO_DISCOUNT)
        else:
            exercise_xp = base_xp

        if exercise_xp > 0:
            xp_awarded += exercise_xp
            total_xp = award_xp(user_id, exercise_xp, subject_id, db)
        else:
            # Pas d'XP à attribuer, mais renvoyer le total courant.
            total_xp = (
                db.query(func.sum(SubjectProgress.total_xp)).filter(SubjectProgress.user_id == user_id).scalar() or 0
            )
        streak = update_streak(user_id, db)
        current_streak = int(streak.current_streak)

        # --- Détection de complétion : chaque exercice de la leçon réussi ---
        lesson_exercise_ids = db.query(Exercise.id).filter(Exercise.lesson_id == lesson.id).subquery()
        total_exercises = db.query(func.count(Exercise.id)).filter(Exercise.lesson_id == lesson.id).scalar() or 0
        correctly_answered = (
            db.query(func.count(func.distinct(ExerciseResult.exercise_id)))
            .filter(
                ExerciseResult.user_id == user_id,
                ExerciseResult.is_correct.is_(True),
                ExerciseResult.exercise_id.in_(db.query(lesson_exercise_ids.c.id)),
            )
            .scalar()
            or 0
        )

        already_completed = progress.status == ProgressStatus.COMPLETED
        if total_exercises > 0 and correctly_answered >= total_exercises and not already_completed:
            # Score = ratio de résultats corrects sur l'ensemble des tentatives
            total_results = (
                db.query(func.count(ExerciseResult.id))
                .filter(
                    ExerciseResult.user_id == user_id,
                    ExerciseResult.exercise_id.in_(db.query(lesson_exercise_ids.c.id)),
                )
                .scalar()
                or 0
            )
            correct_results = (
                db.query(func.count(ExerciseResult.id))
                .filter(
                    ExerciseResult.user_id == user_id,
                    ExerciseResult.is_correct.is_(True),
                    ExerciseResult.exercise_id.in_(db.query(lesson_exercise_ids.c.id)),
                )
                .scalar()
                or 0
            )
            score = round(100 * correct_results / total_results) if total_results else 0
            progress.status = ProgressStatus.COMPLETED
            progress.completed_at = now
            progress.score = score
            progress.stars = _stars_from_score(score)
            lesson_completed = True
            lesson_score = score
            lesson_stars = int(progress.stars)
            # autoflush=False : rendre la complétion visible pour le décompte des
            # leçons du jour ci-dessous.
            db.flush()

            # Bonus XP forfaitaire de leçon (désactivé par défaut, issue #6) +
            # mise à jour de l'objectif quotidien.
            lesson_reward = int(lesson.xp_reward or 0)
            if settings.AWARD_LESSON_COMPLETION_BONUS and lesson_reward > 0:
                xp_awarded += lesson_reward
                total_xp = award_xp(user_id, lesson_reward, subject_id, db)
            update_daily_goal_lesson_count(user_id, db)

        new_achievements = check_and_unlock_achievements(user_id, db)

    db.commit()

    return {
        "xp_awarded": xp_awarded,
        "total_xp": int(total_xp),
        "current_streak": current_streak,
        "lesson_completed": lesson_completed,
        "lesson_score": lesson_score,
        "lesson_stars": lesson_stars,
        "new_achievements": new_achievements,
    }
