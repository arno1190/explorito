"""
Endpoints de gestion des leçons
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.auth import get_current_active_user
from app.api.subjects import require_admin
from app.core.database import get_db
from app.models.content import Exercise, LearningPath, Lesson
from app.models.progress import ProgressStatus, UserProgress
from app.models.user import User
from app.schemas.exercise import ExerciseResponse
from app.schemas.lesson import (
    LessonCreate,
    LessonResponse,
    LessonUpdate,
    LessonWithExercises,
)

router = APIRouter()


@router.get("", response_model=list[LessonResponse])
async def list_lessons(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments à retourner"),
    subject_id: UUID | None = Query(None, description="Filtrer par matière"),
    path_id: UUID | None = Query(None, description="Filtrer par parcours"),
    is_published: bool | None = Query(None, description="Filtrer par statut de publication"),
) -> list[Lesson]:
    """
    Liste les leçons avec filtres optionnels

    Args:
        db: Session de base de données
        skip: Nombre d'éléments à ignorer pour la pagination
        limit: Nombre maximum d'éléments à retourner
        subject_id: Filtrer par ID de matière (optionnel)
        path_id: Filtrer par ID de parcours (optionnel)
        is_published: Filtrer par statut de publication (optionnel)

    Returns:
        Liste des leçons
    """
    query = db.query(Lesson).order_by(Lesson.order_index, Lesson.name)

    # Filtrer par parcours
    if path_id:
        query = query.filter(Lesson.path_id == path_id)

    # Filtrer par matière (via le parcours)
    if subject_id:
        query = query.join(LearningPath).filter(LearningPath.subject_id == subject_id)

    # Filtrer par statut de publication
    if is_published is not None:
        query = query.filter(Lesson.is_published == is_published)

    lessons = query.offset(skip).limit(limit).all()
    return lessons


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson_data: LessonCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> Lesson:
    """
    Crée une nouvelle leçon (admin uniquement)

    Args:
        lesson_data: Données de la leçon à créer
        db: Session de base de données
        current_user: Utilisateur administrateur authentifié

    Returns:
        Leçon créée

    Raises:
        HTTPException: Si le parcours n'existe pas
    """
    # Vérifier que le parcours existe
    path = db.query(LearningPath).filter(LearningPath.id == lesson_data.path_id).first()
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcours d'apprentissage non trouvé",
        )

    # Créer la leçon
    new_lesson = Lesson(**lesson_data.model_dump())
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)

    return new_lesson


@router.get("/{lesson_id}", response_model=LessonWithExercises)
async def get_lesson(lesson_id: UUID, db: Annotated[Session, Depends(get_db)]) -> dict:
    """
    Récupère les détails d'une leçon avec ses exercices

    Args:
        lesson_id: ID de la leçon
        db: Session de base de données

    Returns:
        Détails de la leçon avec exercices

    Raises:
        HTTPException: Si la leçon n'existe pas
    """
    lesson = (
        db.query(Lesson)
        .options(joinedload(Lesson.exercises), joinedload(Lesson.path))
        .filter(Lesson.id == lesson_id)
        .first()
    )

    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée")

    # Build response with subject_id from path (learning_path)
    response = {
        "id": lesson.id,
        "path_id": lesson.path_id,
        "subject_id": lesson.path.subject_id if lesson.path else None,
        "name": lesson.name,
        "description": lesson.description,
        "order_index": lesson.order_index,
        "unlock_criteria": lesson.unlock_criteria,
        "xp_reward": lesson.xp_reward,
        "estimated_duration": lesson.estimated_duration,
        "cover_image": lesson.cover_image,
        "is_published": lesson.is_published,
        "exercises": lesson.exercises,
    }

    return response


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: UUID,
    lesson_data: LessonUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> Lesson:
    """
    Met à jour une leçon (admin uniquement)

    Args:
        lesson_id: ID de la leçon
        lesson_data: Données de mise à jour
        db: Session de base de données
        current_user: Utilisateur administrateur authentifié

    Returns:
        Leçon mise à jour

    Raises:
        HTTPException: Si la leçon ou le parcours n'existe pas
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée")

    # Vérifier le parcours si modifié
    if lesson_data.path_id and lesson_data.path_id != lesson.path_id:
        path = db.query(LearningPath).filter(LearningPath.id == lesson_data.path_id).first()
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parcours d'apprentissage non trouvé",
            )

    # Mettre à jour les champs
    update_data = lesson_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lesson, field, value)

    db.commit()
    db.refresh(lesson)

    return lesson


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> None:
    """
    Supprime une leçon (admin uniquement)

    Args:
        lesson_id: ID de la leçon
        db: Session de base de données
        current_user: Utilisateur administrateur authentifié

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: Si la leçon n'existe pas
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée")

    db.delete(lesson)
    db.commit()


@router.post("/{lesson_id}/start", response_model=dict, status_code=status.HTTP_201_CREATED)
async def start_lesson(
    lesson_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Démarre une leçon pour l'utilisateur (crée ou met à jour la progression)

    Args:
        lesson_id: ID de la leçon
        db: Session de base de données
        current_user: Utilisateur authentifié

    Returns:
        Informations sur la progression créée/mise à jour

    Raises:
        HTTPException: Si la leçon n'existe pas
    """
    # Vérifier que la leçon existe
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée")

    # Vérifier si une progression existe déjà
    progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == current_user.id, UserProgress.lesson_id == lesson_id)
        .first()
    )

    if progress:
        # Mettre à jour la progression existante
        if progress.status == ProgressStatus.LOCKED:
            progress.status = ProgressStatus.AVAILABLE
        if progress.status == ProgressStatus.AVAILABLE:
            progress.status = ProgressStatus.STARTED
            progress.started_at = datetime.utcnow()
            progress.attempts += 1
    else:
        # Créer une nouvelle progression
        progress = UserProgress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            status=ProgressStatus.STARTED,
            started_at=datetime.utcnow(),
            attempts=1,
        )
        db.add(progress)

    db.commit()
    db.refresh(progress)

    return {
        "message": "Leçon démarrée",
        "progress_id": str(progress.id),
        "status": progress.status.value,
        "attempts": progress.attempts,
    }


@router.get("/{lesson_id}/exercises", response_model=list[ExerciseResponse])
async def get_lesson_exercises(lesson_id: UUID, db: Annotated[Session, Depends(get_db)]) -> list[Exercise]:
    """
    Récupère tous les exercices d'une leçon

    Args:
        lesson_id: ID de la leçon
        db: Session de base de données

    Returns:
        Liste des exercices de la leçon

    Raises:
        HTTPException: Si la leçon n'existe pas
    """
    # Vérifier que la leçon existe
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée")

    # Récupérer tous les exercices de cette leçon
    exercises = db.query(Exercise).filter(Exercise.lesson_id == lesson_id).order_by(Exercise.order_index).all()

    return exercises
