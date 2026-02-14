"""
Endpoints de suivi de progression
"""

from typing import Annotated, List
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.user import User
from app.models.content import Subject, Lesson, Exercise
from app.models.progress import UserProgress, SubjectProgress, ProgressStatus, ExerciseResult
from app.models.gamification import Streak
from app.schemas.progress import (
    ProgressDashboard,
    SubjectProgressResponse,
    LessonProgressResponse,
)
from app.api.auth import get_current_active_user
from app.services.gamification import calculate_level_from_xp, calculate_next_level_xp


router = APIRouter()


@router.get("/me", response_model=ProgressDashboard)
async def get_user_progress(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProgressDashboard:
    """
    Récupère la progression globale de l'utilisateur actuel

    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Tableau de bord de progression complet
    """
    # Calculer l'XP total
    total_xp = (
        db.query(func.sum(SubjectProgress.total_xp))
        .filter(SubjectProgress.user_id == current_user.id)
        .scalar()
        or 0
    )

    # Calculer le niveau global
    overall_level = calculate_level_from_xp(int(total_xp))
    next_level_xp = calculate_next_level_xp(overall_level)

    # Récupérer le streak
    streak = db.query(Streak).filter(Streak.user_id == current_user.id).first()
    current_streak = streak.current_streak if streak else 0

    # Compter les leçons complétées aujourd'hui
    today = date.today()
    lessons_today = (
        db.query(func.count(UserProgress.id))
        .filter(
            UserProgress.user_id == current_user.id,
            UserProgress.status == ProgressStatus.COMPLETED,
            func.date(UserProgress.completed_at) == today,
        )
        .scalar()
        or 0
    )

    # Compter le total de leçons complétées
    total_lessons = (
        db.query(func.count(UserProgress.id))
        .filter(
            UserProgress.user_id == current_user.id,
            UserProgress.status == ProgressStatus.COMPLETED,
        )
        .scalar()
        or 0
    )

    # Récupérer la progression par matière
    subject_progress_list = (
        db.query(SubjectProgress)
        .filter(SubjectProgress.user_id == current_user.id)
        .all()
    )

    # Enrichir avec le nom de la matière
    subjects_progress = []
    for sp in subject_progress_list:
        subject = db.query(Subject).filter(Subject.id == sp.subject_id).first()
        sp_dict = SubjectProgressResponse.model_validate(sp).model_dump()
        sp_dict["subject_name"] = subject.name if subject else None
        subjects_progress.append(SubjectProgressResponse(**sp_dict))

    # Récupérer les leçons récentes (5 dernières)
    recent_progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == current_user.id)
        .order_by(UserProgress.completed_at.desc())
        .limit(5)
        .all()
    )

    recent_lessons = []
    for rp in recent_progress:
        lesson = db.query(Lesson).filter(Lesson.id == rp.lesson_id).first()
        rp_dict = LessonProgressResponse.model_validate(rp).model_dump()
        rp_dict["lesson_name"] = lesson.name if lesson else None
        recent_lessons.append(LessonProgressResponse(**rp_dict))

    # Compter les achievements
    achievements_count = (
        db.query(func.count("*"))
        .select_from(
            db.query(User).filter(User.id == current_user.id).join(User.achievements)
        )
        .scalar()
        or 0
    )

    return ProgressDashboard(
        total_xp=int(total_xp),
        overall_level=overall_level,
        current_streak=current_streak,
        lessons_completed_today=int(lessons_today),
        total_lessons_completed=int(total_lessons),
        subjects_progress=subjects_progress,
        recent_lessons=recent_lessons,
        achievements_count=int(achievements_count),
        next_level_xp=next_level_xp,
    )


@router.get("/subjects/{subject_id}", response_model=SubjectProgressResponse)
async def get_subject_progress(
    subject_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SubjectProgressResponse:
    """
    Récupère la progression de l'utilisateur pour une matière spécifique

    Args:
        subject_id: ID de la matière
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Progression de la matière

    Raises:
        HTTPException: Si la matière n'existe pas ou si aucune progression n'est trouvée
    """
    # Vérifier que la matière existe
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Matière non trouvée"
        )

    # Récupérer la progression
    subject_progress = (
        db.query(SubjectProgress)
        .filter(
            SubjectProgress.user_id == current_user.id,
            SubjectProgress.subject_id == subject_id,
        )
        .first()
    )

    if not subject_progress:
        # Créer une progression vide si elle n'existe pas
        subject_progress = SubjectProgress(
            user_id=current_user.id,
            subject_id=subject_id,
            total_xp=0,
            level=1,
            lessons_completed=0,
            accuracy_rate=0,
            last_activity=None,
        )

    # Enrichir avec le nom de la matière
    sp_dict = SubjectProgressResponse.model_validate(subject_progress).model_dump()
    sp_dict["subject_name"] = subject.name

    return SubjectProgressResponse(**sp_dict)


@router.get("/lessons/{lesson_id}", response_model=LessonProgressResponse)
async def get_lesson_progress(
    lesson_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LessonProgressResponse:
    """
    Récupère la progression de l'utilisateur pour une leçon spécifique

    Args:
        lesson_id: ID de la leçon
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Progression de la leçon

    Raises:
        HTTPException: Si la leçon n'existe pas
    """
    # Vérifier que la leçon existe
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée"
        )

    # Récupérer la progression
    lesson_progress = (
        db.query(UserProgress)
        .filter(
            UserProgress.user_id == current_user.id, UserProgress.lesson_id == lesson_id
        )
        .first()
    )

    if not lesson_progress:
        # Retourner une progression vide si elle n'existe pas
        lesson_progress = UserProgress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            status=ProgressStatus.LOCKED,
            score=0,
            stars=0,
            attempts=0,
            time_spent=0,
            started_at=None,
            completed_at=None,
        )

    # Enrichir avec le nom de la leçon
    lp_dict = LessonProgressResponse.model_validate(lesson_progress).model_dump()
    lp_dict["lesson_name"] = lesson.name

    return LessonProgressResponse(**lp_dict)


@router.get("/dashboard", response_model=ProgressDashboard)
async def get_dashboard(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProgressDashboard:
    """
    Récupère un résumé du tableau de bord (alias pour /me)

    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Tableau de bord de progression
    """
    return await get_user_progress(current_user, db)


@router.get("/lessons/{lesson_id}/completed-exercises", response_model=List[str])
async def get_completed_exercises(
    lesson_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> List[str]:
    """
    Récupère la liste des IDs d'exercices complétés (avec succès) pour une leçon

    Args:
        lesson_id: ID de la leçon
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Liste des IDs d'exercices complétés avec succès
    """
    # Vérifier que la leçon existe
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée"
        )

    # Récupérer les exercices de cette leçon
    exercise_ids = (
        db.query(Exercise.id).filter(Exercise.lesson_id == lesson_id).all()
    )
    exercise_id_list = [str(e[0]) for e in exercise_ids]

    # Récupérer les exercices complétés avec succès par l'utilisateur
    completed = (
        db.query(ExerciseResult.exercise_id)
        .filter(
            ExerciseResult.user_id == current_user.id,
            ExerciseResult.exercise_id.in_([UUID(e) for e in exercise_id_list]),
            ExerciseResult.is_correct == True,
        )
        .distinct()
        .all()
    )

    return [str(c[0]) for c in completed]


@router.get("/{child_id}", response_model=List[LessonProgressResponse])
async def get_child_progress(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> List[LessonProgressResponse]:
    """
    Récupère la progression d'un enfant (parent access only)

    Args:
        child_id: ID de l'enfant
        current_user: Utilisateur authentifié (doit être parent)
        db: Session de base de données

    Returns:
        Liste de toutes les progressions de leçons de l'enfant

    Raises:
        HTTPException: Si l'utilisateur n'est pas parent ou si l'enfant ne lui appartient pas
    """
    from app.models.user import UserRole, Profile

    # Vérifier que l'utilisateur est un parent
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les parents peuvent accéder à la progression de leurs enfants",
        )

    # Vérifier que l'enfant appartient à ce parent
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

    # Récupérer toutes les progressions de l'enfant
    progress_list = (
        db.query(UserProgress).filter(UserProgress.user_id == child_id).all()
    )

    # Enrichir avec les noms de leçons
    result = []
    for progress in progress_list:
        lesson = db.query(Lesson).filter(Lesson.id == progress.lesson_id).first()
        progress_dict = LessonProgressResponse.model_validate(progress).model_dump()
        progress_dict["lesson_name"] = lesson.name if lesson else None
        result.append(LessonProgressResponse(**progress_dict))

    return result


@router.get("/{child_id}/lesson/{lesson_id}", response_model=LessonProgressResponse)
async def get_child_lesson_progress(
    child_id: UUID,
    lesson_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LessonProgressResponse:
    """
    Récupère la progression d'un enfant pour une leçon spécifique

    Args:
        child_id: ID de l'enfant
        lesson_id: ID de la leçon
        current_user: Utilisateur authentifié (doit être parent)
        db: Session de base de données

    Returns:
        Progression de la leçon pour l'enfant

    Raises:
        HTTPException: Si l'utilisateur n'est pas parent, si l'enfant ne lui appartient pas, ou si la leçon n'existe pas
    """
    from app.models.user import UserRole, Profile

    # Vérifier que l'utilisateur est un parent
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les parents peuvent accéder à la progression de leurs enfants",
        )

    # Vérifier que l'enfant appartient à ce parent
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

    # Vérifier que la leçon existe
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée"
        )

    # Récupérer la progression
    lesson_progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == child_id, UserProgress.lesson_id == lesson_id)
        .first()
    )

    if not lesson_progress:
        # Retourner une progression vide si elle n'existe pas
        lesson_progress = UserProgress(
            user_id=child_id,
            lesson_id=lesson_id,
            status=ProgressStatus.LOCKED,
            score=0,
            stars=0,
            attempts=0,
            time_spent=0,
            started_at=None,
            completed_at=None,
        )

    # Enrichir avec le nom de la leçon
    lp_dict = LessonProgressResponse.model_validate(lesson_progress).model_dump()
    lp_dict["lesson_name"] = lesson.name

    return LessonProgressResponse(**lp_dict)
