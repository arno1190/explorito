"""
Endpoints de la collection Pokémon (récompense en XP).

L'utilisateur authentifié agit sur sa propre collection (enfant qui dépense son
XP). Le catalogue et les prix font autorité côté serveur.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.subjects import acting_child
from app.core.database import get_db
from app.models.user import User
from app.schemas.collection import (
    CollectionSummary,
    PokedexEntry,
    PokedexGridEntry,
    PurchaseRequest,
    PurchaseResponse,
)
from app.services.collection import (
    AlreadyOwnedError,
    InsufficientBalanceError,
    PokemonNotFoundError,
    get_balance,
    get_spent_xp,
    get_total_earned_xp,
    get_unlocked_ids,
    load_pokedex,
    purchase_pokemon,
)

router = APIRouter()


@router.get("/me", response_model=CollectionSummary)
async def get_user_collection(
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> CollectionSummary:
    """Porte-monnaie XP + Pokémon débloqués de l'utilisateur courant."""
    pokedex = load_pokedex()
    unlocked_ids = get_unlocked_ids(acting.id, db)
    total_earned = get_total_earned_xp(acting.id, db)
    spent = get_spent_xp(acting.id, db)
    collection = [PokedexEntry(**pokedex[pid]) for pid in unlocked_ids if pid in pokedex]
    return CollectionSummary(
        total_earned=total_earned,
        spent=spent,
        balance=max(0, total_earned - spent),
        total_count=len(pokedex),
        unlocked_count=len(collection),
        collection=collection,
    )


@router.get("/pokedex", response_model=list[PokedexGridEntry])
async def get_pokedex(
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PokedexGridEntry]:
    """Catalogue complet avec l'état de possession de l'utilisateur courant."""
    pokedex = load_pokedex()
    owned = set(get_unlocked_ids(acting.id, db))
    return [
        PokedexGridEntry(**entry, owned=entry["id"] in owned)
        for entry in sorted(pokedex.values(), key=lambda e: e["id"])
    ]


@router.post("/purchase", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def purchase(
    body: PurchaseRequest,
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> PurchaseResponse:
    """Débloque un Pokémon en dépensant l'XP de l'utilisateur courant."""
    try:
        entry = purchase_pokemon(acting.id, body.pokemon_id, db)
    except PokemonNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AlreadyOwnedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InsufficientBalanceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PurchaseResponse(
        pokemon=PokedexEntry(**entry),
        balance=get_balance(acting.id, db),
        unlocked_count=len(get_unlocked_ids(acting.id, db)),
    )
