"""Schémas Pydantic pour la garde partagée (invitations & responsables)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InvitationCreate(BaseModel):
    """Création d'une invitation.

    - ``kind='child'`` : partage d'un enfant précis (``child_id`` requis).
    - ``kind='all'`` : invitation d'un co-parent (tous les enfants + futurs).
    """

    kind: str = Field(..., description="'child' ou 'all'")
    child_id: UUID | None = Field(None, description="Enfant partagé (kind='child')")
    role: str = Field("guardian", description="Rôle accordé (kind='child')")


class InvitationResponse(BaseModel):
    """Invitation créée : le jeton sert à construire le lien à partager."""

    token: str
    kind: str
    child_id: UUID | None = None
    expires_at: datetime


class InvitationPreview(BaseModel):
    """Aperçu public d'une invitation (page d'acceptation, avant connexion)."""

    valid: bool
    kind: str | None = None
    inviter_name: str | None = None
    child_name: str | None = None
    child_avatar: str | None = None
    children_names: list[str] = Field(default_factory=list)


class AcceptResponse(BaseModel):
    """Résultat de l'acceptation : nombre d'enfants nouvellement accessibles."""

    granted: int


class GuardianResponse(BaseModel):
    """Un responsable d'un enfant (pour l'écran de gestion des accès)."""

    guardian_id: UUID
    name: str
    avatar_url: str | None = None
    role: str
    is_self: bool
