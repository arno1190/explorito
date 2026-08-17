"""Modèles de la garde partagée (plusieurs adultes responsables d'un enfant).

- :class:`Guardianship` : lien N-N adulte ↔ enfant, source de vérité des accès.
  Rôles : ``owner`` (créateur, seul à pouvoir supprimer l'enfant et gérer les
  accès), ``parent`` (co-parent), ``grandparent``/``guardian`` (partage ciblé).
- :class:`CoParentLink` : lien familial persistant ``owner → co-parent`` ; à la
  création d'un nouvel enfant, les co-parents reçoivent automatiquement une garde.
- :class:`Invitation` : jeton d'invitation (lien à partager), à usage unique et
  avec expiration.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

# Rôles de garde.
ROLE_OWNER = "owner"
ROLE_PARENT = "parent"
ROLE_GRANDPARENT = "grandparent"
ROLE_GUARDIAN = "guardian"
GUARDIAN_ROLES = {ROLE_OWNER, ROLE_PARENT, ROLE_GRANDPARENT, ROLE_GUARDIAN}

# Types d'invitation.
INVITE_CHILD = "child"  # partage d'un enfant précis
INVITE_ALL = "all"  # invitation d'un co-parent (tous les enfants + enfants futurs)
INVITE_KINDS = {INVITE_CHILD, INVITE_ALL}


class Guardianship(Base):
    """Un adulte responsable d'un enfant (lien N-N)."""

    __tablename__ = "guardianships"
    __table_args__ = (UniqueConstraint("child_id", "guardian_id", name="uq_guardianship_child_guardian"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    child_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False, default=ROLE_GUARDIAN)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    child = relationship("User", foreign_keys=[child_id])
    guardian = relationship("User", foreign_keys=[guardian_id])

    def __repr__(self):
        return f"<Guardianship guardian={self.guardian_id} child={self.child_id} {self.role}>"


class CoParentLink(Base):
    """Lien co-parent persistant : les enfants futurs de ``owner`` iront au co-parent."""

    __tablename__ = "co_parent_links"
    __table_args__ = (UniqueConstraint("owner_id", "coparent_id", name="uq_coparent_owner_coparent"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    coparent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<CoParentLink owner={self.owner_id} coparent={self.coparent_id}>"


class Invitation(Base):
    """Invitation à partager un enfant (``child``) ou tous ses enfants (``all``)."""

    __tablename__ = "invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    inviter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String, nullable=False)  # 'child' | 'all'
    # Enfant partagé (kind='child') ; NULL pour une invitation co-parent.
    child_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    role = Column(String, nullable=False, default=ROLE_GUARDIAN)  # rôle accordé à l'acceptation
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    accepted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    inviter = relationship("User", foreign_keys=[inviter_id])
    child = relationship("User", foreign_keys=[child_id])

    @property
    def is_usable(self) -> bool:
        """Vrai si l'invitation peut encore être acceptée."""
        return self.accepted_at is None and self.revoked_at is None and self.expires_at > datetime.utcnow()

    def __repr__(self):
        return f"<Invitation {self.kind} inviter={self.inviter_id} usable={self.is_usable}>"
