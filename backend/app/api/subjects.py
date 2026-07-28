"""
Endpoints de gestion des matières
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user
from app.core.database import get_db
from app.models.content import LearningPath, Lesson, LevelEnum, Subject
from app.models.user import Profile, User, UserRole
from app.schemas.lesson import LessonResponse
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.services.progression import lesson_locked

router = APIRouter()


def child_content_level(current_user: User, db: Session) -> LevelEnum | None:
    """
    Niveau de contenu à afficher pour l'utilisateur.

    Pour un enfant, son niveau scolaire (profil) filtre le contenu. Pour un
    parent/admin (gestion, navigation), aucun filtre (None).
    """
    if current_user.role != UserRole.CHILD:
        return None
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    return profile.level if profile else None


def acting_child(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    x_acting_child_id: Annotated[str | None, Header()] = None,
) -> User:
    """
    Utilisateur dont la perspective de contenu s'applique (niveau + verrouillage).

    - Un enfant : lui-même.
    - Un parent (ou admin) « incarnant » un enfant via l'en-tête
      ``X-Acting-Child-Id`` : cet enfant, à condition que le parent le possède
      (l'admin peut incarner n'importe quel enfant). Sinon, l'utilisateur courant
      (aucun filtrage/verrouillage).
    """
    if current_user.role == UserRole.CHILD:
        return current_user
    if not x_acting_child_id:
        return current_user
    try:
        child_id = UUID(x_acting_child_id)
    except ValueError:
        return current_user
    child = db.query(User).filter(User.id == child_id, User.role == UserRole.CHILD).first()
    if child is None:
        return current_user
    if current_user.role == UserRole.ADMIN:
        return child
    profile = db.query(Profile).filter(Profile.user_id == child.id).first()
    if profile is not None and profile.parent_id == current_user.id:
        return child
    return current_user


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


@router.get("", response_model=list[SubjectResponse])
async def list_subjects(
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments à retourner"),
    is_active: bool | None = Query(None, description="Filtrer par statut actif"),
) -> list[SubjectResponse]:
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

    level = child_content_level(acting, db)

    query = db.query(Subject).order_by(Subject.order_index, Subject.name)

    if is_active is not None:
        query = query.filter(Subject.is_active == is_active)

    subjects = query.offset(skip).limit(limit).all()

    # Enrichir avec lesson_count (filtré au niveau de l'enfant, leçons publiées).
    result = []
    for subject in subjects:
        count_query = (
            db.query(func.count(Lesson.id))
            .join(LearningPath, Lesson.path_id == LearningPath.id)
            .filter(LearningPath.subject_id == subject.id)
        )
        if level is not None:
            count_query = count_query.filter(
                LearningPath.level == level,
                Lesson.is_published.is_(True),
            )
        lesson_count = int(count_query.scalar() or 0)

        # Pour un enfant, masquer les matières sans contenu à son niveau.
        if level is not None and lesson_count == 0:
            continue

        subject_dict = SubjectResponse.model_validate(subject).model_dump()
        subject_dict["lesson_count"] = lesson_count
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
async def get_subject(subject_id: UUID, db: Annotated[Session, Depends(get_db)]) -> SubjectResponse:
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matière non trouvée")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matière non trouvée")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matière non trouvée")

    db.delete(subject)
    db.commit()


@router.get("/{subject_id}/lessons", response_model=list[LessonResponse])
async def get_subject_lessons(
    subject_id: UUID,
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> list[LessonResponse]:
    """
    Récupère les leçons d'une matière (filtrées au niveau de l'enfant).

    Args:
        subject_id: ID de la matière
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Leçons des parcours de cette matière ; pour un enfant, limitées à son
        niveau scolaire et aux leçons publiées.

    Raises:
        HTTPException: Si la matière n'existe pas
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matière non trouvée")

    level = child_content_level(acting, db)

    paths_query = db.query(LearningPath).filter(LearningPath.subject_id == subject_id)
    if level is not None:
        paths_query = paths_query.filter(LearningPath.level == level)
    learning_paths = paths_query.all()

    lessons: list[Lesson] = []
    for path in learning_paths:
        lessons_query = db.query(Lesson).filter(Lesson.path_id == path.id)
        if level is not None:
            lessons_query = lessons_query.filter(Lesson.is_published.is_(True))
        lessons.extend(lessons_query.order_by(Lesson.order_index).all())

    # ``locked`` calculé côté serveur : source de vérité unique du verrouillage.
    return [
        LessonResponse.model_validate(lesson).model_copy(
            update={
                "subject_id": subject_id,
                "locked": lesson_locked(acting.id, lesson, level, db),
            }
        )
        for lesson in lessons
    ]
