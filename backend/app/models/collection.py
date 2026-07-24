"""
Modèle de collection Pokémon (récompense en XP).

Chaque ligne = un Pokémon débloqué par un utilisateur, avec le prix payé.
Le "porte-monnaie" XP dépensable est dérivé : solde = XP total gagné − Σ prix payés.
Le catalogue (id → nom FR, prix, artwork) vit dans ``app/data/pokedex.json``.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PokemonUnlock(Base):
    """Un Pokémon débloqué par un utilisateur."""

    __tablename__ = "pokemon_unlocks"
    __table_args__ = (UniqueConstraint("user_id", "pokemon_id", name="uq_user_pokemon"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pokemon_id = Column(Integer, nullable=False)
    price_paid = Column(Integer, nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="pokemon_unlocks")

    def __repr__(self):
        return f"<PokemonUnlock user={self.user_id} pokemon={self.pokemon_id}>"
