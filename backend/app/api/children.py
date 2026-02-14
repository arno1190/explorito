"""
Endpoints pour la gestion des profils enfants
"""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User, Profile, UserRole
from app.schemas.children import ChildCreate, ChildResponse
from app.api.auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[ChildResponse])
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
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les parents peuvent accéder à cette ressource",
        )

    # Récupérer tous les profils enfants liés à ce parent
    children_profiles = (
        db.query(Profile)
        .filter(Profile.parent_id == current_user.id, Profile.is_child == True)
        .all()
    )

    # Convertir en ChildResponse
    children = []
    for profile in children_profiles:
        children.append(
            ChildResponse(
                id=profile.user_id,
                name=profile.display_name,
                birth_date=profile.date_of_birth,
                parent_id=profile.parent_id,
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
    if current_user.role != UserRole.PARENT:
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
            Profile.is_child == True,
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Enfant non trouvé"
        )

    return ChildResponse(
        id=profile.user_id,
        name=profile.display_name,
        birth_date=profile.date_of_birth,
        parent_id=profile.parent_id,
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
    # Vérifier que l'utilisateur est un parent
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les parents peuvent créer des profils enfants",
        )

    # Vérifier que l'email n'existe pas déjà
    existing_user = db.query(User).filter(User.email == child_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà",
        )

    # Créer l'utilisateur enfant
    child_user = User(
        email=child_data.email,
        password_hash=get_password_hash(child_data.password),
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
        created_at=child_profile.created_at,
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
    if current_user.role != UserRole.PARENT:
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
            Profile.is_child == True,
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Enfant non trouvé"
        )

    # Supprimer l'utilisateur (cascade supprimera le profil)
    child_user = db.query(User).filter(User.id == child_id).first()
    db.delete(child_user)
    db.commit()

    return None
