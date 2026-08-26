"""
Service des collections (récompenses en XP), multi-catalogue.

Porte-monnaie XP à deux registres, **partagé entre tous les catalogues** :
- ``total_earned`` = somme des ``SubjectProgress.total_xp`` (pilote les niveaux)
- ``spent`` = somme des ``CollectibleUnlock.price_paid`` (tous catalogues)
- ``balance`` = total_earned − spent  (XP dépensable partout)

Chaque catalogue (``pokemon``, ``dinosaurs``, ``solar_system``) est un fichier
JSON (id → nom FR, prix, image, anecdote) chargé et mis en cache.
"""

import functools
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.collection import (
    WALLET_BEHAVIOR,
    WALLET_POINTS,
    WALLETS,
    CollectibleUnlock,
    PointAward,
)
from app.models.progress import SubjectProgress
from app.models.user import Profile

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Registre des catalogues disponibles : slug -> métadonnées d'affichage + fichier.
CATALOGS: dict[str, dict[str, str]] = {
    "pokemon": {"name": "Pokémon", "icon": "📕", "file": "pokedex.json"},
    "dinosaurs": {"name": "Dinosaures", "icon": "🦕", "file": "dinosaurs.json"},
    "solar_system": {"name": "Système solaire", "icon": "🪐", "file": "solar_system.json"},
    "dragon_ball": {"name": "Dragon Ball", "icon": "🐉", "file": "dragon_ball.json"},
    "harry_potter": {"name": "Harry Potter", "icon": "⚡", "file": "harry_potter.json"},
    "mario": {"name": "Super Mario", "icon": "🍄", "file": "mario.json"},
    "paw_patrol": {"name": "Pat' Patrouille", "icon": "🐾", "file": "paw_patrol.json"},
}


class CollectionError(Exception):
    """Erreur métier de collection (mappée en HTTP par l'endpoint)."""


class CatalogNotFoundError(CollectionError):
    """Le catalogue demandé n'existe pas."""


class ItemNotFoundError(CollectionError):
    """L'objet n'existe pas dans le catalogue."""


class AlreadyOwnedError(CollectionError):
    """L'objet est déjà débloqué par l'utilisateur."""


class InsufficientBalanceError(CollectionError):
    """Solde XP insuffisant pour l'achat."""


def catalog_slugs() -> list[str]:
    """Slugs des catalogues effectivement disponibles (fichier présent)."""
    return [slug for slug, meta in CATALOGS.items() if (DATA_DIR / meta["file"]).exists()]


@functools.cache
def load_catalog(slug: str) -> dict[int, dict[str, Any]]:
    """Charge un catalogue indexé par id (mis en cache). Lève si inconnu."""
    meta = CATALOGS.get(slug)
    if meta is None:
        raise CatalogNotFoundError(f"Catalogue « {slug} » inconnu")
    path = DATA_DIR / meta["file"]
    if not path.exists():
        raise CatalogNotFoundError(f"Catalogue « {slug} » indisponible")
    data = json.loads(path.read_text(encoding="utf-8"))
    return {int(p["id"]): p for p in data}


def _item(entry: dict[str, Any]) -> dict[str, Any]:
    """Projette une entrée brute sur les champs exposés (id, name_fr, price, image, fact)."""
    return {
        "id": int(entry["id"]),
        "name_fr": entry["name_fr"],
        "price": int(entry["price"]),
        "image_url": entry["image_url"],
        "fact": entry.get("fact"),
    }


def _lock_user_purchases(user_id: UUID, db: Session) -> None:
    """Sérialise les achats d'un même utilisateur (anti double-dépense concurrente)."""
    if db.get_bind().dialect.name == "postgresql":
        db.execute(select(func.pg_advisory_xact_lock(func.hashtext(str(user_id)))))


def get_total_earned_xp(user_id: UUID, db: Session) -> int:
    """XP total gagné par l'utilisateur (toutes matières)."""
    total = db.query(func.sum(SubjectProgress.total_xp)).filter(SubjectProgress.user_id == user_id).scalar()
    return int(total or 0)


def _awards_sum(user_id: UUID, wallet: str, db: Session) -> int:
    """Somme (nette) des points attribués par le parent pour un porte-monnaie."""
    total = (
        db.query(func.sum(PointAward.amount))
        .filter(PointAward.child_id == user_id, PointAward.wallet == wallet)
        .scalar()
    )
    return int(total or 0)


def get_points_earned(user_id: UUID, db: Session) -> int:
    """« Gagné » du porte-monnaie Points = XP d'exercices + attributions hardskill."""
    return get_total_earned_xp(user_id, db) + _awards_sum(user_id, WALLET_POINTS, db)


def get_behavior_earned(user_id: UUID, db: Session) -> int:
    """« Gagné » (net) du porte-monnaie Comportement."""
    return _awards_sum(user_id, WALLET_BEHAVIOR, db)


def wallet_earned(user_id: UUID, wallet: str, db: Session) -> int:
    """Total gagné d'un porte-monnaie donné."""
    if wallet == WALLET_BEHAVIOR:
        return get_behavior_earned(user_id, db)
    return get_points_earned(user_id, db)


def get_spent(user_id: UUID, currency: str, db: Session) -> int:
    """XP/points dépensés avec un porte-monnaie donné (tous catalogues)."""
    spent = (
        db.query(func.sum(CollectibleUnlock.price_paid))
        .filter(CollectibleUnlock.user_id == user_id, CollectibleUnlock.currency == currency)
        .scalar()
    )
    return int(spent or 0)


def wallet_balance(user_id: UUID, wallet: str, db: Session) -> int:
    """Solde dépensable d'un porte-monnaie = gagné − dépensé (jamais négatif)."""
    return max(0, wallet_earned(user_id, wallet, db) - get_spent(user_id, wallet, db))


def get_spent_xp(user_id: UUID, db: Session) -> int:
    """Rétro-compat : XP dépensé avec le porte-monnaie Points."""
    return get_spent(user_id, WALLET_POINTS, db)


def get_balance(user_id: UUID, db: Session) -> int:
    """Rétro-compat : solde dépensable du porte-monnaie Points."""
    return wallet_balance(user_id, WALLET_POINTS, db)


def get_unlocked_ids(user_id: UUID, catalog: str, db: Session) -> list[int]:
    """IDs débloqués par l'utilisateur dans un catalogue, triés."""
    rows = (
        db.query(CollectibleUnlock.item_id)
        .filter(CollectibleUnlock.user_id == user_id, CollectibleUnlock.catalog == catalog)
        .all()
    )
    return sorted(int(r[0]) for r in rows)


def unlocked_counts(user_id: UUID, db: Session) -> dict[str, int]:
    """Nombre d'objets débloqués par catalogue pour l'utilisateur."""
    rows = (
        db.query(CollectibleUnlock.catalog, func.count(CollectibleUnlock.id))
        .filter(CollectibleUnlock.user_id == user_id)
        .group_by(CollectibleUnlock.catalog)
        .all()
    )
    return {str(cat): int(n) for cat, n in rows}


def all_catalog_metas() -> list[dict[str, Any]]:
    """Liste complète des catalogues (non filtrée) — pour la gestion parentale."""
    return [
        {"slug": slug, "name": CATALOGS[slug]["name"], "icon": CATALOGS[slug]["icon"], "total": len(load_catalog(slug))}
        for slug in catalog_slugs()
    ]


def disabled_collections_for(user_id: UUID, db: Session) -> set[str]:
    """Slugs de catalogues masqués pour cet enfant (choix du parent).

    Stocké dans ``Profile.settings["disabled_collections"]`` (défaut : aucun).
    """
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile or not profile.settings:
        return set()
    raw = profile.settings.get("disabled_collections") or []
    return {str(s) for s in raw} if isinstance(raw, list) else set()


def catalog_allowed(user_id: UUID, slug: str, db: Session) -> bool:
    """Un catalogue est-il accessible à cet enfant ?"""
    return slug not in disabled_collections_for(user_id, db)


def catalog_infos(user_id: UUID, db: Session) -> list[dict[str, Any]]:
    """Résumé de chaque catalogue disponible (total + débloqués)."""
    counts = unlocked_counts(user_id, db)
    disabled = disabled_collections_for(user_id, db)
    infos: list[dict[str, Any]] = []
    for slug in catalog_slugs():
        if slug in disabled:
            continue
        meta = CATALOGS[slug]
        infos.append(
            {
                "slug": slug,
                "name": meta["name"],
                "icon": meta["icon"],
                "total": len(load_catalog(slug)),
                "unlocked": counts.get(slug, 0),
            }
        )
    return infos


def purchase_item(
    user_id: UUID, catalog: str, item_id: int, db: Session, currency: str = WALLET_POINTS
) -> dict[str, Any]:
    """
    Achète un objet d'un catalogue et l'ajoute à la collection de l'utilisateur.

    Args:
        user_id: ID de l'utilisateur (enfant) acheteur.
        catalog: Slug du catalogue.
        item_id: ID de l'objet (valide, non possédé, abordable).
        db: Session de base de données.

    Returns:
        L'objet débloqué (id, name_fr, price, image_url, fact).

    Raises:
        CatalogNotFoundError, ItemNotFoundError, AlreadyOwnedError, InsufficientBalanceError.
    """
    entry = load_catalog(catalog).get(int(item_id))
    if entry is None:
        raise ItemNotFoundError(f"Objet #{item_id} inconnu dans « {catalog} »")

    # Sérialise les achats concurrents du même utilisateur.
    _lock_user_purchases(user_id, db)

    already = (
        db.query(CollectibleUnlock)
        .filter(
            CollectibleUnlock.user_id == user_id,
            CollectibleUnlock.catalog == catalog,
            CollectibleUnlock.item_id == int(item_id),
        )
        .first()
    )
    if already is not None:
        raise AlreadyOwnedError(f"{entry['name_fr']} est déjà dans ta collection")

    if currency not in WALLETS:
        raise ItemNotFoundError(f"Porte-monnaie « {currency} » inconnu")

    price = int(entry["price"])
    if wallet_balance(user_id, currency, db) < price:
        raise InsufficientBalanceError(f"Il te faut {price} points pour débloquer {entry['name_fr']}")

    db.add(
        CollectibleUnlock(
            user_id=user_id,
            catalog=catalog,
            item_id=int(item_id),
            price_paid=price,
            currency=currency,
        )
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AlreadyOwnedError(f"{entry['name_fr']} est déjà dans ta collection") from exc
    return _item(entry)


# --------------------------------------------------------------------------- #
# Points attribués par le parent (hardskill / comportement)
# --------------------------------------------------------------------------- #
def award_points(
    child_id: UUID,
    wallet: str,
    amount: int,
    reason: str | None,
    awarded_by: UUID | None,
    db: Session,
) -> PointAward:
    """Enregistre une attribution (ou un retrait) de points par le parent.

    La validation métier (Points > 0 ; Comportement ≠ 0) est faite par l'endpoint.
    """
    award = PointAward(
        child_id=child_id,
        wallet=wallet,
        amount=int(amount),
        reason=(reason or None),
        awarded_by=awarded_by,
    )
    db.add(award)
    db.commit()
    db.refresh(award)
    return award


def list_awards(child_id: UUID, db: Session, limit: int = 100) -> list[PointAward]:
    """Historique des attributions d'un enfant (plus récentes d'abord)."""
    return (
        db.query(PointAward)
        .filter(PointAward.child_id == child_id)
        .order_by(PointAward.created_at.desc())
        .limit(limit)
        .all()
    )


def unseen_awards(child_id: UUID, db: Session) -> list[PointAward]:
    """Attributions non encore vues par l'enfant (pour la notification)."""
    return (
        db.query(PointAward)
        .filter(PointAward.child_id == child_id, PointAward.acknowledged_at.is_(None))
        .order_by(PointAward.created_at.asc())
        .all()
    )


def acknowledge_awards(child_id: UUID, db: Session) -> int:
    """Marque toutes les attributions non vues comme vues. Renvoie le nombre traité."""
    now = datetime.utcnow()
    n = (
        db.query(PointAward)
        .filter(PointAward.child_id == child_id, PointAward.acknowledged_at.is_(None))
        .update({PointAward.acknowledged_at: now}, synchronize_session=False)
    )
    db.commit()
    return int(n)
