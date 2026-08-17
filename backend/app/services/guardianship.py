"""Service de garde partagée : accès, invitations, co-parents.

Toutes les vérifications d'accès aux enfants passent par :func:`is_guardian` /
:func:`guarded_child_ids` (source de vérité : la table ``guardianships``). Le
créateur d'un enfant en est le ``owner`` (seul à pouvoir supprimer l'enfant et
gérer les accès).
"""

import secrets
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.guardianship import (
    INVITE_ALL,
    INVITE_CHILD,
    ROLE_OWNER,
    ROLE_PARENT,
    CoParentLink,
    Guardianship,
    Invitation,
)

INVITE_TTL_DAYS = 7


# --------------------------------------------------------------------------- #
# Lecture des accès
# --------------------------------------------------------------------------- #
def guarded_child_ids(user_id: UUID, db: Session) -> list[UUID]:
    """IDs des enfants dont ``user_id`` est responsable (tous rôles confondus)."""
    rows = db.query(Guardianship.child_id).filter(Guardianship.guardian_id == user_id).all()
    return [r[0] for r in rows]


def guardianship_for(user_id: UUID, child_id: UUID, db: Session) -> Guardianship | None:
    """Le lien de garde de ``user_id`` sur ``child_id``, ou ``None``."""
    return db.query(Guardianship).filter(Guardianship.guardian_id == user_id, Guardianship.child_id == child_id).first()


def is_guardian(user_id: UUID, child_id: UUID, db: Session) -> bool:
    """Vrai si ``user_id`` a un accès (quel que soit le rôle) à ``child_id``."""
    return guardianship_for(user_id, child_id, db) is not None


def is_owner(user_id: UUID, child_id: UUID, db: Session) -> bool:
    """Vrai si ``user_id`` est le propriétaire (créateur) de ``child_id``."""
    g = guardianship_for(user_id, child_id, db)
    return g is not None and g.role == ROLE_OWNER


def guardians_of(child_id: UUID, db: Session) -> list[Guardianship]:
    """Tous les liens de garde d'un enfant (ordre : propriétaire d'abord)."""
    rows = db.query(Guardianship).filter(Guardianship.child_id == child_id).all()
    return sorted(rows, key=lambda g: (g.role != ROLE_OWNER, g.created_at))


# --------------------------------------------------------------------------- #
# Écriture des accès
# --------------------------------------------------------------------------- #
def grant(child_id: UUID, guardian_id: UUID, role: str, invited_by: UUID | None, db: Session) -> Guardianship:
    """Accorde (idempotent) une garde. Ne rétrograde jamais un ``owner`` existant."""
    existing = guardianship_for(guardian_id, child_id, db)
    if existing is not None:
        return existing
    g = Guardianship(child_id=child_id, guardian_id=guardian_id, role=role, invited_by=invited_by)
    db.add(g)
    db.flush()
    return g


def co_parent_ids(owner_id: UUID, db: Session) -> list[UUID]:
    """Co-parents de ``owner_id`` (recevront automatiquement les enfants futurs)."""
    rows = db.query(CoParentLink.coparent_id).filter(CoParentLink.owner_id == owner_id).all()
    return [r[0] for r in rows]


def on_child_created(child_id: UUID, owner_id: UUID, db: Session) -> None:
    """À la création d'un enfant : garde ``owner`` + gardes ``parent`` des co-parents."""
    grant(child_id, owner_id, ROLE_OWNER, None, db)
    for coparent_id in co_parent_ids(owner_id, db):
        grant(child_id, coparent_id, ROLE_PARENT, owner_id, db)


def owned_child_ids(owner_id: UUID, db: Session) -> list[UUID]:
    """Enfants dont ``owner_id`` est propriétaire."""
    rows = (
        db.query(Guardianship.child_id)
        .filter(Guardianship.guardian_id == owner_id, Guardianship.role == ROLE_OWNER)
        .all()
    )
    return [r[0] for r in rows]


# --------------------------------------------------------------------------- #
# Invitations
# --------------------------------------------------------------------------- #
def create_invitation(inviter_id: UUID, kind: str, child_id: UUID | None, role: str, db: Session) -> Invitation:
    """Crée une invitation (jeton opaque, expiration ``INVITE_TTL_DAYS``)."""
    inv = Invitation(
        token=secrets.token_urlsafe(24),
        inviter_id=inviter_id,
        kind=kind,
        child_id=child_id,
        role=role,
        expires_at=datetime.utcnow() + timedelta(days=INVITE_TTL_DAYS),
    )
    db.add(inv)
    db.flush()
    return inv


def get_usable_invitation(token: str, db: Session) -> Invitation | None:
    """Invitation encore acceptable pour ce jeton, ou ``None``."""
    inv = db.query(Invitation).filter(Invitation.token == token).first()
    if inv is None or not inv.is_usable:
        return None
    return inv


def accept_invitation(token: str, accepting_user_id: UUID, db: Session) -> list[UUID]:
    """Accepte une invitation et crée les gardes. Renvoie les IDs d'enfants accordés.

    - ``child`` : garde du rôle indiqué sur l'enfant.
    - ``all`` : garde ``parent`` sur tous les enfants possédés par l'invitant +
      lien co-parent persistant (enfants futurs partagés automatiquement).

    Lève ``ValueError`` si l'invitation est invalide/expirée/déjà utilisée, ou si
    l'utilisateur accepte sa propre invitation.
    """
    inv = get_usable_invitation(token, db)
    if inv is None:
        raise ValueError("invitation invalide ou expirée")
    if inv.inviter_id == accepting_user_id:
        raise ValueError("on ne peut pas accepter sa propre invitation")

    granted: list[UUID] = []
    if inv.kind == INVITE_CHILD and inv.child_id is not None:
        grant(inv.child_id, accepting_user_id, inv.role, inv.inviter_id, db)
        granted.append(inv.child_id)
    elif inv.kind == INVITE_ALL:
        for child_id in owned_child_ids(inv.inviter_id, db):
            grant(child_id, accepting_user_id, ROLE_PARENT, inv.inviter_id, db)
            granted.append(child_id)
        # Lien co-parent persistant (idempotent).
        exists = (
            db.query(CoParentLink)
            .filter(CoParentLink.owner_id == inv.inviter_id, CoParentLink.coparent_id == accepting_user_id)
            .first()
        )
        if exists is None:
            db.add(CoParentLink(owner_id=inv.inviter_id, coparent_id=accepting_user_id))

    inv.accepted_at = datetime.utcnow()
    inv.accepted_by = accepting_user_id
    db.commit()
    return granted


def revoke_invitation(inv: Invitation, db: Session) -> None:
    """Annule une invitation en attente."""
    inv.revoked_at = datetime.utcnow()
    db.commit()


def remove_guardian(child_id: UUID, guardian_id: UUID, db: Session) -> None:
    """Retire une garde (révocation par l'owner, ou départ volontaire)."""
    g = guardianship_for(guardian_id, child_id, db)
    if g is not None:
        db.delete(g)
    db.commit()
