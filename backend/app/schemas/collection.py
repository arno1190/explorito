"""Schémas Pydantic pour les collections (multi-catalogue)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CatalogItem(BaseModel):
    """Un objet d'un catalogue (Pokémon, dinosaure, astre…)."""

    id: int
    name_fr: str
    price: int
    image_url: str
    fact: str | None = Field(default=None, description="Anecdote / description (contenu éducatif)")


class CatalogGridItem(CatalogItem):
    """Objet enrichi de l'état de possession (pour la grille)."""

    owned: bool = False


class CatalogInfo(BaseModel):
    """Résumé d'un catalogue pour le hub des collections."""

    slug: str
    name: str
    icon: str
    total: int
    unlocked: int


class WalletSummary(BaseModel):
    """Deux porte-monnaies dépensables + avancement par catalogue.

    ``total_earned/spent/balance`` = porte-monnaie **Points** (XP + hardskill).
    ``behavior_*`` = porte-monnaie **Comportement**.
    """

    total_earned: int = Field(..., description="Points gagnés (XP exercices + hardskill)")
    spent: int = Field(..., description="Points dépensés")
    balance: int = Field(..., description="Solde Points = gagné − dépensé")
    behavior_earned: int = Field(default=0, description="Points de comportement gagnés (net)")
    behavior_spent: int = Field(default=0, description="Points de comportement dépensés")
    behavior_balance: int = Field(default=0, description="Solde Comportement")
    catalogs: list[CatalogInfo] = Field(default_factory=list)


class PurchaseRequest(BaseModel):
    """Requête d'achat d'un objet de collection."""

    catalog: str = Field(..., description="Slug du catalogue (pokemon, dinosaurs, solar_system)")
    item_id: int = Field(..., ge=1, description="ID de l'objet à débloquer")
    currency: str = Field(default="points", description="Porte-monnaie : points | behavior")


class AwardCreate(BaseModel):
    """Attribution (ou retrait) de points par un parent."""

    wallet: str = Field(..., description="points | behavior")
    amount: int = Field(..., description="Montant (négatif autorisé pour behavior)")
    reason: str | None = Field(default=None, max_length=200, description="Motif (dictée, bonne action…)")


class AwardResponse(BaseModel):
    """Une ligne d'attribution de points."""

    id: UUID
    wallet: str
    amount: int
    reason: str | None = None
    created_at: datetime
    acknowledged_at: datetime | None = None

    class Config:
        from_attributes = True


class PurchaseResponse(BaseModel):
    """Résultat d'un achat."""

    item: CatalogItem
    catalog: str
    balance: int = Field(..., description="Nouveau solde XP après achat")
    unlocked_count: int = Field(..., description="Objets débloqués dans ce catalogue")
