"""Schémas Pydantic pour la collection Pokémon."""

from pydantic import BaseModel, Field


class PokedexEntry(BaseModel):
    """Une entrée du catalogue Pokémon."""

    id: int
    name_fr: str
    price: int
    image_url: str


class PokedexGridEntry(PokedexEntry):
    """Entrée du catalogue enrichie de l'état de possession (pour la grille)."""

    owned: bool = False


class CollectionSummary(BaseModel):
    """État du porte-monnaie XP et de la collection de l'utilisateur."""

    total_earned: int = Field(..., description="XP total gagné (inchangé, pilote les niveaux)")
    spent: int = Field(..., description="XP dépensé en Pokémon")
    balance: int = Field(..., description="XP dépensable = gagné − dépensé")
    total_count: int = Field(..., description="Nombre total de Pokémon du catalogue")
    unlocked_count: int = Field(..., description="Nombre de Pokémon débloqués")
    collection: list[PokedexEntry] = Field(default_factory=list, description="Pokémon débloqués (données complètes)")


class PurchaseRequest(BaseModel):
    """Requête d'achat d'un Pokémon."""

    pokemon_id: int = Field(..., ge=1, description="ID du Pokémon à débloquer")


class PurchaseResponse(BaseModel):
    """Résultat d'un achat."""

    pokemon: PokedexEntry
    balance: int = Field(..., description="Nouveau solde XP après achat")
    unlocked_count: int
