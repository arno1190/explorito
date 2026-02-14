"""
Endpoints de gestion des matières
"""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.content import Subject, Lesson, LearningPath
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse
from app.schemas.lesson import LessonResponse
from app.api.auth import get_current_active_user

router = APIRouter()


def require_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Vérifie que l'utilisateur actuel est un administrateur

    Args:
        current_user: Utilisateur authentifié

    Returns:
        Utilisateur si admin

    Raises:
        HTTPException: Si l'utilisateur n'est pas admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs",
        )
    return current_user


@router.get("", response_model=List[SubjectResponse])
async def list_subjects(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(
        100, ge=1, le=100, description="Nombre maximum d'éléments à retourner"
    ),
    is_active: bool | None = Query(None, description="Filtrer par statut actif"),
) -> List[SubjectResponse]:
    """
    Liste toutes les matières

    Args:
        db: Session de base de données
        skip: Nombre d'éléments à ignorer pour la pagination
        limit: Nombre maximum d'éléments à retourner
        is_active: Filtrer par statut actif (optionnel)

    Returns:
        Liste des matières
    """
    from sqlalchemy import func

    query = db.query(Subject).order_by(Subject.order_index, Subject.name)

    if is_active is not None:
        query = query.filter(Subject.is_active == is_active)

    subjects = query.offset(skip).limit(limit).all()

    # Enrichir avec lesson_count
    result = []
    for subject in subjects:
        # Compter les leçons à travers les learning paths
        lesson_count = (
            db.query(func.count(Lesson.id))
            .join(LearningPath, Lesson.path_id == LearningPath.id)
            .filter(LearningPath.subject_id == subject.id)
            .scalar()
            or 0
        )

        subject_dict = SubjectResponse.model_validate(subject).model_dump()
        subject_dict["lesson_count"] = int(lesson_count)
        result.append(SubjectResponse(**subject_dict))

    return result


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> Subject:
    """
    Crée une nouvelle matière (admin uniquement)

    Args:
        subject_data: Données de la matière à créer
        db: Session de base de données
        current_user: Utilisateur administrateur authentifié

    Returns:
        Matière créée

    Raises:
        HTTPException: Si le slug existe déjà
    """
    # Vérifier si le slug existe déjà
    existing = db.query(Subject).filter(Subject.slug == subject_data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Une matière avec le slug '{subject_data.slug}' existe déjà",
        )

    # Créer la matière
    new_subject = Subject(**subject_data.model_dump())
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)

    subject_dict = SubjectResponse.model_validate(new_subject).model_dump()
    subject_dict["lesson_count"] = 0

    return SubjectResponse(**subject_dict)


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: UUID, db: Annotated[Session, Depends(get_db)]
) -> SubjectResponse:
    """
    Récupère les détails d'une matière

    Args:
        subject_id: ID de la matière
        db: Session de base de données

    Returns:
        Détails de la matière

    Raises:
        HTTPException: Si la matière n'existe pas
    """
    from sqlalchemy import func

    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Matière non trouvée"
        )

    # Compter les leçons
    lesson_count = (
        db.query(func.count(Lesson.id))
        .join(LearningPath, Lesson.path_id == LearningPath.id)
        .filter(LearningPath.subject_id == subject.id)
        .scalar()
        or 0
    )

    subject_dict = SubjectResponse.model_validate(subject).model_dump()
    subject_dict["lesson_count"] = int(lesson_count)

    return SubjectResponse(**subject_dict)


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: UUID,
    subject_data: SubjectUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> Subject:
    """
    Met à jour une matière (admin uniquement)

    Args:
        subject_id: ID de la matière
        subject_data: Données de mise à jour
        db: Session de base de données
        current_user: Utilisateur administrateur authentifié

    Returns:
        Matière mise à jour

    Raises:
        HTTPException: Si la matière n'existe pas ou si le slug existe déjà
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Matière non trouvée"
        )

    # Vérifier le slug si modifié
    if subject_data.slug and subject_data.slug != subject.slug:
        existing = db.query(Subject).filter(Subject.slug == subject_data.slug).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une matière avec le slug '{subject_data.slug}' existe déjà",
            )

    # Mettre à jour les champs
    update_data = subject_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subject, field, value)

    db.commit()
    db.refresh(subject)

    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> None:
    """
    Supprime une matière (admin uniquement)

    Args:
        subject_id: ID de la matière
        db: Session de base de données
        current_user: Utilisateur administrateur authentifié

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: Si la matière n'existe pas
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Matière non trouvée"
        )

    db.delete(subject)
    db.commit()


@router.get("/{subject_id}/lessons", response_model=List[LessonResponse])
async def get_subject_lessons(
    subject_id: UUID, db: Annotated[Session, Depends(get_db)]
) -> List[Lesson]:
    """
    Récupère toutes les leçons d'une matière

    Args:
        subject_id: ID de la matière
        db: Session de base de données

    Returns:
        Liste des leçons de toutes les learning paths de cette matière

    Raises:
        HTTPException: Si la matière n'existe pas
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Matière non trouvée"
        )

    # Récupérer tous les learning paths de cette matière
    learning_paths = (
        db.query(LearningPath).filter(LearningPath.subject_id == subject_id).all()
    )

    # Récupérer toutes les leçons de ces learning paths
    lessons = []
    for path in learning_paths:
        path_lessons = (
            db.query(Lesson)
            .filter(Lesson.path_id == path.id)
            .order_by(Lesson.order_index)
            .all()
        )
        lessons.extend(path_lessons)

    return lessons
