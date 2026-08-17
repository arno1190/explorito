"""Endpoints des invitations de garde partagée (liens à partager).

Un propriétaire crée une invitation (partage d'un enfant, ou de tous ses enfants
pour un co-parent). Le lien contient un jeton opaque, à usage unique, valable 7
jours. L'aperçu (``GET``) est public pour afficher la page d'acceptation avant
connexion ; l'acceptation exige une connexion Google.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.guardianship import (
    INVITE_ALL,
    INVITE_CHILD,
    ROLE_GRANDPARENT,
    ROLE_GUARDIAN,
    ROLE_PARENT,
    Invitation,
)
from app.models.user import Profile, User, UserRole
from app.schemas.guardianship import AcceptResponse, InvitationCreate, InvitationPreview, InvitationResponse
from app.services.guardianship import (
    accept_invitation,
    create_invitation,
    is_owner,
    owned_child_ids,
    revoke_invitation,
)

router = APIRouter()

_SHAREABLE_ROLES = {ROLE_PARENT, ROLE_GRANDPARENT, ROLE_GUARDIAN}


def _display_name(user_id, db: Session) -> str | None:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    return profile.display_name if profile else None


@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create(
    body: InvitationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InvitationResponse:
    """Crée une invitation. Réservé au propriétaire (créateur) de l'enfant."""
    if current_user.role not in (UserRole.PARENT, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Réservé aux parents")

    if body.kind == INVITE_CHILD:
        if body.child_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="child_id requis")
        if current_user.role != UserRole.ADMIN and not is_owner(current_user.id, body.child_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul le propriétaire de l'enfant peut le partager",
            )
        role = body.role if body.role in _SHAREABLE_ROLES else ROLE_GUARDIAN
        inv = create_invitation(current_user.id, INVITE_CHILD, body.child_id, role, db)
    elif body.kind == INVITE_ALL:
        inv = create_invitation(current_user.id, INVITE_ALL, None, ROLE_PARENT, db)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type d'invitation inconnu")

    db.commit()
    return InvitationResponse(token=inv.token, kind=inv.kind, child_id=inv.child_id, expires_at=inv.expires_at)


@router.get("/{token}", response_model=InvitationPreview)
async def preview(token: str, db: Annotated[Session, Depends(get_db)]) -> InvitationPreview:
    """Aperçu public d'une invitation (sans authentification)."""
    inv = db.query(Invitation).filter(Invitation.token == token).first()
    if inv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation introuvable")
    if not inv.is_usable:
        return InvitationPreview(valid=False, kind=inv.kind)

    inviter_name = _display_name(inv.inviter_id, db)
    if inv.kind == INVITE_CHILD and inv.child_id is not None:
        child = db.query(Profile).filter(Profile.user_id == inv.child_id).first()
        return InvitationPreview(
            valid=True,
            kind=inv.kind,
            inviter_name=inviter_name,
            child_name=child.display_name if child else None,
            child_avatar=child.avatar_url if child else None,
        )
    names = [
        p.display_name for p in db.query(Profile).filter(Profile.user_id.in_(owned_child_ids(inv.inviter_id, db))).all()
    ]
    return InvitationPreview(valid=True, kind=inv.kind, inviter_name=inviter_name, children_names=names)


@router.post("/{token}/accept", response_model=AcceptResponse)
async def accept(
    token: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AcceptResponse:
    """Accepte une invitation : crée les gardes pour l'utilisateur connecté."""
    if current_user.role not in (UserRole.PARENT, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Réservé aux parents")
    try:
        granted = accept_invitation(token, current_user.id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AcceptResponse(granted=len(granted))


@router.delete("/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke(
    token: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Annule une invitation en attente (invitant uniquement)."""
    inv = db.query(Invitation).filter(Invitation.token == token).first()
    if inv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation introuvable")
    if inv.inviter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
    revoke_invitation(inv, db)
    return None
