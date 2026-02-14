"""
Modèles de gestion de famille
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class FamilyRole(str, enum.Enum):
    """Rôle dans un groupe familial"""

    PARENT = "parent"
    CHILD = "child"


class FamilyGroup(Base):
    """
    Groupe familial

    Permet de regrouper plusieurs utilisateurs (parents + enfants)
    """

    __tablename__ = "family_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship(
        "FamilyMember", back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<FamilyGroup {self.name}>"


class FamilyMember(Base):
    """
    Membre d'un groupe familial

    Lie un utilisateur à un groupe avec un rôle
    """

    __tablename__ = "family_members"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("family_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(Enum(FamilyRole), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    group = relationship("FamilyGroup", back_populates="members")
    user = relationship("User", back_populates="family_memberships")

    def __repr__(self):
        return (
            f"<FamilyMember group={self.group_id} user={self.user_id} role={self.role}>"
        )
