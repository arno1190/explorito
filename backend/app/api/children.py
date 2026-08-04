"""
Endpoints pour la gestion des profils enfants
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.user import Profile, User, UserRole
from app.schemas.children import ChildCreate, ChildResponse, ChildUpdate
from app.services.uploads import save_avatar

router = APIRouter()


def _require_owned_child(child_id: UUID, current_user: User, db: Session) -> Profile:
    """
    Vérifie que l'appelant est un parent et que l'enfant lui appartient.

    Returns:
        Le profil de l'enfant.

    Raises:
        HTTPException: 403 si non-parent, 404 si l'enfant n'appartient pas au parent.
    """
    if current_user.role not in (UserRole.PARENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les parents peuvent accéder à cette ressource",
        )
    profile = (
        db.query(Profile)
        .filter(
            Profile.user_id == child_id,
            Profile.parent_id == current_user.id,
            Profile.is_child.is_(True),
        )
        .first()
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enfant non trouvé")
    return profile


@router.get("", response_model=list[ChildResponse])
async def get_children(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Récupère la liste des enfants du parent connecté

    Returns:
        Liste des profils enfants liés au parent
    """
    # Vérifier que l'utilisateur est un parent
    if current_user.role not in (UserRole.PARENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les parents peuvent accéder à cette ressource",
        )

    # Récupérer tous les profils enfants liés à ce parent
    children_profiles = db.query(Profile).filter(Profile.parent_id == current_user.id, Profile.is_child.is_(True)).all()

    # Convertir en ChildResponse
    children = []
    for profile in children_profiles:
        children.append(
            ChildResponse(
                id=profile.user_id,
                name=profile.display_name,
                birth_date=profile.date_of_birth,
                parent_id=profile.parent_id,
                level=profile.level,
                avatar_url=profile.avatar_url,
                created_at=profile.created_at,
            )
        )

    return children


@router.get("/{child_id}", response_model=ChildResponse)
async def get_child(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Récupère les détails d'un enfant spécifique

    Args:
        child_id: ID de l'utilisateur enfant

    Returns:
        Profil de l'enfant
    """
    # Vérifier que l'utilisateur est un parent
    if current_user.role not in (UserRole.PARENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les parents peuvent accéder à cette ressource",
        )

    # Récupérer le profil de l'enfant
    profile = (
        db.query(Profile)
        .filter(
            Profile.user_id == child_id,
            Profile.parent_id == current_user.id,
            Profile.is_child.is_(True),
        )
        .first()
    )

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enfant non trouvé")

    return ChildResponse(
        id=profile.user_id,
        name=profile.display_name,
        birth_date=profile.date_of_birth,
        parent_id=profile.parent_id,
        level=profile.level,
        avatar_url=profile.avatar_url,
        created_at=profile.created_at,
    )


@router.post("", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    child_data: ChildCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Crée un nouveau profil enfant

    Args:
        child_data: Données du profil enfant à créer

    Returns:
        Profil de l'enfant créé
    """
    # Parents (et admin) peuvent créer des enfants.
    if current_user.role not in (UserRole.PARENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les parents peuvent créer des profils enfants",
        )

    # Enfant = compte sans connexion (ni email ni mot de passe).
    child_user = User(
        email=None,
        password_hash=None,
        role=UserRole.CHILD,
        is_active=True,
    )
    db.add(child_user)
    db.flush()  # Pour obtenir l'ID sans faire le commit

    # Créer le profil enfant
    child_profile = Profile(
        user_id=child_user.id,
        display_name=child_data.name,
        date_of_birth=child_data.birth_date,
        is_child=True,
        level=child_data.level,
        parent_id=current_user.id,
    )
    db.add(child_profile)
    db.commit()
    db.refresh(child_profile)

    return ChildResponse(
        id=child_user.id,
        name=child_profile.display_name,
        birth_date=child_profile.date_of_birth,
        parent_id=child_profile.parent_id,
        level=child_profile.level,
        avatar_url=child_profile.avatar_url,
        created_at=child_profile.created_at,
    )


@router.put("/{child_id}", response_model=ChildResponse)
async def update_child(
    child_id: UUID,
    child_data: ChildUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChildResponse:
    """
    Met à jour le profil d'un enfant du parent connecté.

    Args:
        child_id: ID de l'utilisateur enfant.
        child_data: Champs à modifier (nom, date de naissance, mot de passe).

    Returns:
        Profil de l'enfant mis à jour.
    """
    profile = _require_owned_child(child_id, current_user, db)

    if child_data.name is not None:
        profile.display_name = child_data.name
    if child_data.birth_date is not None:
        profile.date_of_birth = child_data.birth_date
    if child_data.level is not None:
        profile.level = child_data.level
    if child_data.avatar_url is not None:
        profile.avatar_url = child_data.avatar_url or None

    db.commit()
    db.refresh(profile)

    return ChildResponse(
        id=profile.user_id,
        name=profile.display_name,
        birth_date=profile.date_of_birth,
        parent_id=profile.parent_id,
        level=profile.level,
        avatar_url=profile.avatar_url,
        created_at=profile.created_at,
    )


@router.post("/{child_id}/avatar", response_model=ChildResponse)
async def upload_child_avatar(
    child_id: UUID,
    file: Annotated[UploadFile, File(description="Image d'avatar (PNG, JPEG, WebP, GIF)")],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChildResponse:
    """
    Téléverse une image comme avatar d'un enfant du parent connecté.

    Args:
        child_id: ID de l'utilisateur enfant.
        file: Fichier image (multipart).

    Returns:
        Profil de l'enfant mis à jour.
    """
    profile = _require_owned_child(child_id, current_user, db)
    profile.avatar_url = save_avatar(file)
    db.commit()
    db.refresh(profile)
    return ChildResponse(
        id=profile.user_id,
        name=profile.display_name,
        birth_date=profile.date_of_birth,
        parent_id=profile.parent_id,
        level=profile.level,
        avatar_url=profile.avatar_url,
        created_at=profile.created_at,
    )


@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Supprime un profil enfant

    Args:
        child_id: ID de l'utilisateur enfant à supprimer
    """
    # Vérifier que l'utilisateur est un parent
    if current_user.role not in (UserRole.PARENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les parents peuvent supprimer des profils enfants",
        )

    # Récupérer le profil de l'enfant
    profile = (
        db.query(Profile)
        .filter(
            Profile.user_id == child_id,
            Profile.parent_id == current_user.id,
            Profile.is_child.is_(True),
        )
        .first()
    )

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enfant non trouvé")

    # Supprimer l'utilisateur (cascade supprimera le profil)
    child_user = db.query(User).filter(User.id == child_id).first()
    db.delete(child_user)
    db.commit()

    return None
