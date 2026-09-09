"""Endpoints d'administration : métriques d'usage + gestion des comptes (admin only)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.subjects import require_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.guardianship import INVITE_SIGNUP, Invitation
from app.models.user import User
from app.schemas.admin import AdminOverview, AdminUserRow, SignupInviteRow
from app.services.admin import delete_user, list_users, overview, set_active
from app.services.guardianship import create_signup_invitation, revoke_invitation

router = APIRouter()


@router.get("/overview", response_model=AdminOverview)
async def get_overview(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminOverview:
    """Métriques opérationnelles (totaux, actifs 7/30 j, exercices, connexions récentes)."""
    return AdminOverview(**overview(db))


@router.get("/users", response_model=list[AdminUserRow])
async def get_users(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AdminUserRow]:
    """Tous les comptes avec statut et activité."""
    return [AdminUserRow(**row) for row in list_users(db)]


@router.post("/users/{user_id}/suspend", response_model=AdminUserRow)
async def suspend_user(
    user_id: UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminUserRow:
    """Suspend un compte (bloque connexion et accès). Interdit sur soi-même."""
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impossible de se suspendre soi-même.")
    user = set_active(db, user_id, False)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable.")
    return _row(user, db)


@router.post("/users/{user_id}/reactivate", response_model=AdminUserRow)
async def reactivate_user(
    user_id: UUID,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminUserRow:
    """Réactive un compte suspendu."""
    user = set_active(db, user_id, True)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable.")
    return _row(user, db)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(
    user_id: UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Suppression définitive d'un compte et de ses données (cascade). Irréversible."""
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impossible de se supprimer soi-même.")
    if not delete_user(db, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable.")


# --------------------------------------------------------------------------- #
# Codes d'inscription (issue #22)
# --------------------------------------------------------------------------- #
def _invite_row(inv: Invitation, db: Session) -> SignupInviteRow:
    """Ligne admin d'un code d'inscription, avec le lien prêt à transmettre."""
    accepted_by_email = None
    if inv.accepted_by is not None:
        accepted = db.query(User).filter(User.id == inv.accepted_by).first()
        accepted_by_email = accepted.email if accepted else None
    return SignupInviteRow(
        token=inv.token,
        expires_at=inv.expires_at,
        created_at=inv.created_at,
        accepted_at=inv.accepted_at,
        accepted_by_email=accepted_by_email,
        revoked_at=inv.revoked_at,
        is_usable=inv.is_usable,
        url=f"{settings.PUBLIC_APP_URL.rstrip('/')}/register?invite={inv.token}",
    )


@router.get("/signup-invites", response_model=list[SignupInviteRow])
async def get_signup_invites(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[SignupInviteRow]:
    """Tous les codes d'inscription, du plus récent au plus ancien."""
    invites = db.query(Invitation).filter(Invitation.kind == INVITE_SIGNUP).order_by(Invitation.created_at.desc()).all()
    return [_invite_row(inv, db) for inv in invites]


@router.post("/signup-invites", response_model=SignupInviteRow, status_code=status.HTTP_201_CREATED)
async def create_signup_invite(
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SignupInviteRow:
    """Ouvre la porte à une famille : un code, une inscription."""
    inv = create_signup_invitation(admin.id, db)
    db.commit()
    db.refresh(inv)
    return _invite_row(inv, db)


@router.delete("/signup-invites/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_signup_invite(
    token: str,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Révoque un code non encore utilisé (un code déjà consommé reste tracé)."""
    inv = db.query(Invitation).filter(Invitation.token == token, Invitation.kind == INVITE_SIGNUP).first()
    if inv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code introuvable.")
    revoke_invitation(inv, db)


def _row(user: User, db: Session) -> AdminUserRow:
    """Recharge la ligne admin d'un utilisateur après modification."""
    for row in list_users(db):
        if row["id"] == user.id:
            return AdminUserRow(**row)
    return AdminUserRow(
        id=user.id,
        email=user.email,
        name=user.email or "—",
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
    )
