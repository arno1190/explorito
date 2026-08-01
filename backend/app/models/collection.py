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
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="collectible_unlocks")

    def __repr__(self):
        return f"<CollectibleUnlock user={self.user_id} {self.catalog}#{self.item_id}>"
