"""
Service de collection Pokémon.

Porte-monnaie XP à deux registres :
- ``total_earned`` = somme des ``SubjectProgress.total_xp`` (inchangé, pilote les niveaux)
- ``spent`` = somme des ``PokemonUnlock.price_paid``
- ``balance`` = total_earned − spent  (XP dépensable)

Le catalogue (id → nom FR, prix, artwork) est chargé depuis
``app/data/pokedex.json`` (immuable, mis en cache).
"""

import functools
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.collection import PokemonUnlock
from app.models.progress import SubjectProgress

POKEDEX_PATH = Path(__file__).resolve().parent.parent / "data" / "pokedex.json"


class CollectionError(Exception):
    """Erreur métier de collection (mappée en HTTP par l'endpoint)."""


class PokemonNotFoundError(CollectionError):
    """L'ID Pokémon n'existe pas dans le catalogue."""


class AlreadyOwnedError(CollectionError):
    """Le Pokémon est déjà débloqué par l'utilisateur."""


class InsufficientBalanceError(CollectionError):
    """Solde XP insuffisant pour l'achat."""


@functools.lru_cache(maxsize=1)
def load_pokedex() -> dict[int, dict[str, Any]]:
    """Charge le catalogue Pokémon indexé par id (mis en cache)."""
    data = json.loads(POKEDEX_PATH.read_text(encoding="utf-8"))
    return {int(p["id"]): p for p in data}


def get_total_earned_xp(user_id: UUID, db: Session) -> int:
    """XP total gagné par l'utilisateur (toutes matières)."""
    total = db.query(func.sum(SubjectProgress.total_xp)).filter(SubjectProgress.user_id == user_id).scalar()
    return int(total or 0)


def get_spent_xp(user_id: UUID, db: Session) -> int:
    """XP dépensé (somme des prix payés)."""
    spent = db.query(func.sum(PokemonUnlock.price_paid)).filter(PokemonUnlock.user_id == user_id).scalar()
    return int(spent or 0)


def get_balance(user_id: UUID, db: Session) -> int:
    """Solde XP dépensable = gagné − dépensé (jamais négatif)."""
    return max(0, get_total_earned_xp(user_id, db) - get_spent_xp(user_id, db))


def get_unlocked_ids(user_id: UUID, db: Session) -> list[int]:
    """IDs Pokémon débloqués par l'utilisateur, triés."""
    rows = db.query(PokemonUnlock.pokemon_id).filter(PokemonUnlock.user_id == user_id).all()
    return sorted(int(r[0]) for r in rows)


def purchase_pokemon(user_id: UUID, pokemon_id: int, db: Session) -> dict[str, Any]:
    """
    Achète un Pokémon du pool verrouillé et l'ajoute à la collection.

    Args:
        user_id: ID de l'utilisateur (enfant) acheteur.
        pokemon_id: ID du Pokémon choisi (doit être valide, non possédé, abordable).
        db: Session de base de données.

    Returns:
        L'objet catalogue complet du Pokémon débloqué (id, name_fr, price, image_url).

    Raises:
        PokemonNotFoundError: id absent du catalogue.
        AlreadyOwnedError: déjà débloqué.
        InsufficientBalanceError: solde insuffisant.
    """
    pokedex = load_pokedex()
    entry = pokedex.get(int(pokemon_id))
    if entry is None:
        raise PokemonNotFoundError(f"Pokémon #{pokemon_id} inconnu")

    already = (
        db.query(PokemonUnlock)
        .filter(
            PokemonUnlock.user_id == user_id,
            PokemonUnlock.pokemon_id == int(pokemon_id),
        )
        .first()
    )
    if already is not None:
        raise AlreadyOwnedError(f"{entry['name_fr']} est déjà dans ta collection")

    price = int(entry["price"])
    if get_balance(user_id, db) < price:
        raise InsufficientBalanceError(f"Il te faut {price} XP pour débloquer {entry['name_fr']}")

    db.add(
        PokemonUnlock(
            user_id=user_id,
            pokemon_id=int(pokemon_id),
            price_paid=price,
        )
    )
    db.commit()
    return entry
