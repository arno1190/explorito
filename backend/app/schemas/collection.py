"""Schémas Pydantic pour les collections (multi-catalogue)."""

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
    """Porte-monnaie XP partagé + avancement par catalogue."""

    total_earned: int = Field(..., description="XP total gagné (inchangé, pilote les niveaux)")
    spent: int = Field(..., description="XP dépensé (tous catalogues confondus)")
    balance: int = Field(..., description="XP dépensable = gagné − dépensé")
    catalogs: list[CatalogInfo] = Field(default_factory=list)


class PurchaseRequest(BaseModel):
    """Requête d'achat d'un objet de collection."""

    catalog: str = Field(..., description="Slug du catalogue (pokemon, dinosaurs, solar_system)")
    item_id: int = Field(..., ge=1, description="ID de l'objet à débloquer")


class PurchaseResponse(BaseModel):
    """Résultat d'un achat."""

    item: CatalogItem
    catalog: str
    balance: int = Field(..., description="Nouveau solde XP après achat")
    unlocked_count: int = Field(..., description="Objets débloqués dans ce catalogue")
