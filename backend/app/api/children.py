"""
Endpoints pour la gestion des profils enfants (garde partagée).

L'accès aux enfants passe par la table ``guardianships`` : plusieurs adultes
peuvent être responsables d'un même enfant. Le ``owner`` (créateur) est seul à
pouvoir supprimer l'enfant et gérer les accès ; tout responsable peut consulter,
attribuer des points, incarner l'enfant et éditer son profil.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.collection import WALLET_POINTS, WALLETS
from app.models.guardianship import ROLE_GUARDIAN, ROLE_OWNER
from app.models.user import Profile, User, UserRole
from app.schemas.children import ChildCreate, ChildResponse, ChildUpdate
from app.schemas.collection import AwardCreate, AwardResponse
from app.schemas.guardianship import GuardianResponse
from app.services.collection import award_points, list_awards
from app.services.guardianship import (
    guarded_child_ids,
    guardians_of,
    guardianship_for,
    is_guardian,
    is_owner,
    on_child_created,
    remove_guardian,
)
from app.services.uploads import save_avatar

router = APIRouter()


def _require_parent(current_user: User) -> None:
    """Rejette les comptes non parent/admin."""
    if current_user.role not in (UserRole.PARENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les parents peuvent accéder à cette ressource",
        )


def _get_child_profile(child_id: UUID, db: Session) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == child_id, Profile.is_child.is_(True)).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enfant non trouvé")
    return profile


def _require_guardian(child_id: UUID, current_user: User, db: Session) -> Profile:
    """L'appelant doit être responsable de l'enfant (n'importe quel rôle). Admin = accès total."""
    _require_parent(current_user)
    profile = _get_child_profile(child_id, db)
    if current_user.role == UserRole.ADMIN or is_guardian(current_user.id, child_id, db):
        return profile
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enfant non trouvé")


def _require_owner(child_id: UUID, current_user: User, db: Session) -> Profile:
    """L'appelant doit être propriétaire (créateur) de l'enfant. Admin autorisé."""
    _require_parent(current_user)
    profile = _get_child_profile(child_id, db)
    if current_user.role == UserRole.ADMIN or is_owner(current_user.id, child_id, db):
        return profile
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Seul le propriétaire de l'enfant peut effectuer cette action",
    )


def _child_response(profile: Profile, current_user: User, db: Session) -> ChildResponse:
    """Construit la réponse enrichie du rôle de l'appelant sur cet enfant."""
    g = guardianship_for(current_user.id, profile.user_id, db)
    if g is not None:
        role = g.role
    elif current_user.role == UserRole.ADMIN:
        role = ROLE_OWNER
    else:
        role = ROLE_GUARDIAN
    return ChildResponse(
        id=profile.user_id,
        name=profile.display_name,
        birth_date=profile.date_of_birth,
        parent_id=profile.parent_id,
        level=profile.level,
        avatar_url=profile.avatar_url,
        created_at=profile.created_at,
        disabled_collections=list((profile.settings or {}).get("disabled_collections") or []),
        role=role,
        is_owner=role == ROLE_OWNER,
    )


@router.get("", response_model=list[ChildResponse])
async def get_children(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Liste des enfants dont l'appelant est responsable (union propriétaire + partagés)."""
    _require_parent(current_user)
    child_ids = guarded_child_ids(current_user.id, db)
    if not child_ids:
        return []
    profiles = db.query(Profile).filter(Profile.user_id.in_(child_ids), Profile.is_child.is_(True)).all()
    return [_child_response(p, current_user, db) for p in profiles]


@router.get("/{child_id}", response_model=ChildResponse)
async def get_child(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Détails d'un enfant dont l'appelant est responsable."""
    profile = _require_guardian(child_id, current_user, db)
    return _child_response(profile, current_user, db)


@router.post("", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    child_data: ChildCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Crée un enfant (compte sans connexion). L'appelant en devient le propriétaire ;
    les co-parents éventuels reçoivent automatiquement une garde."""
    _require_parent(current_user)

    child_user = User(email=None, password_hash=None, role=UserRole.CHILD, is_active=True)
    db.add(child_user)
    db.flush()

    child_profile = Profile(
        user_id=child_user.id,
        display_name=child_data.name,
        date_of_birth=child_data.birth_date,
        is_child=True,
        level=child_data.level,
        parent_id=current_user.id,
    )
    db.add(child_profile)
    db.flush()
    on_child_created(child_user.id, current_user.id, db)
    db.commit()
    db.refresh(child_profile)

    return _child_response(child_profile, current_user, db)


@router.put("/{child_id}", response_model=ChildResponse)
async def update_child(
    child_id: UUID,
    child_data: ChildUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChildResponse:
    """Met à jour le profil d'un enfant (tout responsable)."""
    profile = _require_guardian(child_id, current_user, db)

    if child_data.name is not None:
        profile.display_name = child_data.name
    if child_data.birth_date is not None:
        profile.date_of_birth = child_data.birth_date
    if child_data.level is not None:
        profile.level = child_data.level
    if child_data.avatar_url is not None:
        profile.avatar_url = child_data.avatar_url or None
    if child_data.disabled_collections is not None:
        profile.settings = {
            **(profile.settings or {}),
            "disabled_collections": sorted(set(child_data.disabled_collections)),
        }
        flag_modified(profile, "settings")

    db.commit()
    db.refresh(profile)
    return _child_response(profile, current_user, db)


@router.post("/{child_id}/avatar", response_model=ChildResponse)
async def upload_child_avatar(
    child_id: UUID,
    file: Annotated[UploadFile, File(description="Image d'avatar (PNG, JPEG, WebP, GIF)")],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChildResponse:
    """Téléverse l'avatar d'un enfant (tout responsable)."""
    profile = _require_guardian(child_id, current_user, db)
    profile.avatar_url = save_avatar(file)
    db.commit()
    db.refresh(profile)
    return _child_response(profile, current_user, db)


@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Supprime définitivement un enfant (propriétaire uniquement)."""
    _require_owner(child_id, current_user, db)
    child_user = db.query(User).filter(User.id == child_id).first()
    db.delete(child_user)  # cascade : profil, progression, gardes
    db.commit()
    return None


@router.post("/{child_id}/awards", response_model=AwardResponse, status_code=status.HTTP_201_CREATED)
async def create_award(
    child_id: UUID,
    body: AwardCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AwardResponse:
    """Attribue (ou retire) des points à un enfant (tout responsable)."""
    _require_guardian(child_id, current_user, db)
    if body.wallet not in WALLETS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Porte-monnaie inconnu")
    if body.amount == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le montant ne peut pas être nul")
    if body.wallet == WALLET_POINTS and body.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Les points de compétence ne peuvent pas être retirés",
        )
    award = award_points(child_id, body.wallet, body.amount, body.reason, current_user.id, db)
    return AwardResponse.model_validate(award)


@router.get("/{child_id}/awards", response_model=list[AwardResponse])
async def get_awards(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AwardResponse]:
    """Historique des points attribués à un enfant (tout responsable)."""
    _require_guardian(child_id, current_user, db)
    return [AwardResponse.model_validate(a) for a in list_awards(child_id, db)]


@router.get("/{child_id}/guardians", response_model=list[GuardianResponse])
async def get_guardians(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[GuardianResponse]:
    """Liste des responsables d'un enfant (propriétaire uniquement)."""
    _require_owner(child_id, current_user, db)
    out: list[GuardianResponse] = []
    for g in guardians_of(child_id, db):
        profile = db.query(Profile).filter(Profile.user_id == g.guardian_id).first()
        guardian_user = db.query(User).filter(User.id == g.guardian_id).first()
        name = (profile.display_name if profile else None) or (guardian_user.email if guardian_user else "—")
        out.append(
            GuardianResponse(
                guardian_id=g.guardian_id,
                name=name,
                avatar_url=profile.avatar_url if profile else None,
                role=g.role,
                is_self=g.guardian_id == current_user.id,
            )
        )
    return out


@router.delete("/{child_id}/guardians/{guardian_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_child_guardian(
    child_id: UUID,
    guardian_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retire un responsable.

    - Se retirer soi-même (« quitter ») : autorisé pour tout responsable **non**
      propriétaire.
    - Retirer quelqu'un d'autre : réservé au propriétaire ; on ne peut pas
      retirer le propriétaire.
    """
    _require_parent(current_user)
    target = guardianship_for(guardian_id, child_id, db)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responsable non trouvé")
    if target.role == ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le propriétaire ne peut pas être retiré")

    is_self = guardian_id == current_user.id
    if not is_self and not (current_user.role == UserRole.ADMIN or is_owner(current_user.id, child_id, db)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le propriétaire peut retirer un autre responsable",
        )
    remove_guardian(child_id, guardian_id, db)
    return None
