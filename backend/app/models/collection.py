"""
Modèle des collections (récompenses en XP).

Chaque ligne = un objet débloqué par un utilisateur dans un catalogue donné
(``pokemon``, ``dinosaurs``, ``solar_system``…), avec le prix payé. Le
« porte-monnaie » XP dépensable est dérivé et **partagé entre tous les
catalogues** : solde = XP total gagné − Σ prix payés (tous catalogues confondus).
Les catalogues (id → nom FR, prix, image, anecdote) vivent dans ``app/data``.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

# Porte-monnaies dépensables (deux registres distincts).
WALLET_POINTS = "points"  # XP d'exercices + points « hardskill » attribués par le parent
WALLET_BEHAVIOR = "behavior"  # points de « comportement » attribués par le parent
WALLETS = (WALLET_POINTS, WALLET_BEHAVIOR)


class CollectibleUnlock(Base):
    """Un objet de collection débloqué par un utilisateur (tous catalogues)."""

    __tablename__ = "collectible_unlocks"
    __table_args__ = (UniqueConstraint("user_id", "catalog", "item_id", name="uq_user_catalog_item"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    catalog = Column(String, nullable=False, default="pokemon")
    item_id = Column(Integer, nullable=False)
    price_paid = Column(Integer, nullable=False)
    # Porte-monnaie utilisé pour l'achat (voir WALLETS). Historique = "points".
    currency = Column(String, nullable=False, default=WALLET_POINTS)
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="collectible_unlocks", foreign_keys=[user_id])

    def __repr__(self):
        return f"<CollectibleUnlock user={self.user_id} {self.catalog}#{self.item_id}>"


class PointAward(Base):
    """Points attribués (ou retirés) par un parent pour une activité hors-ligne.

    ``wallet`` = ``points`` (hardskill, additif) ou ``behavior`` (comportement,
    +/-). Le solde d'un porte-monnaie intègre ces montants (voir services).
    """

    __tablename__ = "point_awards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    child_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    wallet = Column(String, nullable=False, default=WALLET_POINTS)
    amount = Column(Integer, nullable=False)  # négatif autorisé pour "behavior"
    reason = Column(String, nullable=True)
    awarded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    # Renseigné quand l'enfant a vu la notification (toast « +10 Dictée ! »).
    acknowledged_at = Column(DateTime, nullable=True)

    child = relationship("User", foreign_keys=[child_id])

    def __repr__(self):
        return f"<PointAward child={self.child_id} {self.wallet} {self.amount:+d}>"
