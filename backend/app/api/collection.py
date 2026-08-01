"""
Endpoints des collections (récompenses en XP), multi-catalogue.

Le porte-monnaie XP est partagé entre tous les catalogues. Les endpoints sont
« acting-child aware » : un parent qui incarne un enfant agit sur la collection
de l'enfant (en-tête ``X-Acting-Child-Id``).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.subjects import acting_child
from app.core.database import get_db
from app.models.user import User
from app.schemas.collection import (
    CatalogGridItem,
    PurchaseRequest,
    PurchaseResponse,
    WalletSummary,
)
from app.services.collection import (
    AlreadyOwnedError,
    CatalogNotFoundError,
    InsufficientBalanceError,
    ItemNotFoundError,
    catalog_infos,
    get_balance,
    get_spent_xp,
    get_total_earned_xp,
    get_unlocked_ids,
    load_catalog,
    purchase_item,
)

router = APIRouter()


@router.get("/me", response_model=WalletSummary)
async def get_wallet(
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> WalletSummary:
    """Porte-monnaie XP partagé + avancement par catalogue."""
    total_earned = get_total_earned_xp(acting.id, db)
    spent = get_spent_xp(acting.id, db)
    return WalletSummary(
        total_earned=total_earned,
        spent=spent,
        balance=max(0, total_earned - spent),
        catalogs=catalog_infos(acting.id, db),
    )


@router.get("/catalogs/{slug}", response_model=list[CatalogGridItem])
async def get_catalog(
    slug: str,
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> list[CatalogGridItem]:
    """Catalogue complet avec l'état de possession de l'utilisateur."""
    try:
        catalog = load_catalog(slug)
    except CatalogNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    owned = set(get_unlocked_ids(acting.id, slug, db))
    return [
        CatalogGridItem(
            id=int(entry["id"]),
            name_fr=entry["name_fr"],
            price=int(entry["price"]),
            image_url=entry["image_url"],
            fact=entry.get("fact"),
            owned=int(entry["id"]) in owned,
        )
        for entry in sorted(catalog.values(), key=lambda e: e["id"])
    ]


@router.post("/purchase", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def purchase(
    body: PurchaseRequest,
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> PurchaseResponse:
    """Débloque un objet d'un catalogue en dépensant l'XP de l'utilisateur."""
    try:
        item = purchase_item(acting.id, body.catalog, body.item_id, db)
    except (CatalogNotFoundError, ItemNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AlreadyOwnedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InsufficientBalanceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PurchaseResponse(
        item=item,
        catalog=body.catalog,
        balance=get_balance(acting.id, db),
        unlocked_count=len(get_unlocked_ids(acting.id, body.catalog, db)),
    )
