"""
Endpoints des collections (récompenses en points), multi-catalogue.

Deux porte-monnaies dépensables et **partagés entre tous les catalogues** :
« points » (XP d'exercices + hardskill) et « behavior » (comportement). Les
endpoints sont « acting-child aware » : un parent qui incarne un enfant agit sur
la collection de l'enfant (en-tête ``X-Acting-Child-Id``).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user
from app.api.subjects import acting_child
from app.core.database import get_db
from app.models.collection import WALLETS
from app.models.user import User
from app.schemas.collection import (
    AwardResponse,
    CatalogGridItem,
    CatalogMeta,
    PurchaseRequest,
    PurchaseResponse,
    WalletSummary,
)
from app.services.collection import (
    AlreadyOwnedError,
    CatalogNotFoundError,
    InsufficientBalanceError,
    ItemNotFoundError,
    acknowledge_awards,
    all_catalog_metas,
    catalog_allowed,
    catalog_infos,
    get_behavior_earned,
    get_points_earned,
    get_spent,
    get_unlocked_ids,
    load_catalog,
    purchase_item,
    unseen_awards,
    wallet_balance,
)

router = APIRouter()


@router.get("/me", response_model=WalletSummary)
async def get_wallet(
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> WalletSummary:
    """Les deux porte-monnaies (Points, Comportement) + avancement par catalogue."""
    points_earned = get_points_earned(acting.id, db)
    points_spent = get_spent(acting.id, "points", db)
    behavior_earned = get_behavior_earned(acting.id, db)
    behavior_spent = get_spent(acting.id, "behavior", db)
    return WalletSummary(
        total_earned=points_earned,
        spent=points_spent,
        balance=max(0, points_earned - points_spent),
        behavior_earned=behavior_earned,
        behavior_spent=behavior_spent,
        behavior_balance=max(0, behavior_earned - behavior_spent),
        catalogs=catalog_infos(acting.id, db),
    )


@router.get("/catalogs", response_model=list[CatalogMeta])
async def list_catalogs(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[CatalogMeta]:
    """Liste complète des catalogues (non filtrée) — pour la gestion parentale."""
    return [CatalogMeta(**m) for m in all_catalog_metas()]


@router.get("/catalogs/{slug}", response_model=list[CatalogGridItem])
async def get_catalog(
    slug: str,
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> list[CatalogGridItem]:
    """Catalogue complet avec l'état de possession de l'utilisateur."""
    if not catalog_allowed(acting.id, slug, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Collection non accessible.")
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
    """Débloque un objet en dépensant le porte-monnaie choisi (points | behavior)."""
    if body.currency not in WALLETS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Porte-monnaie inconnu")
    if not catalog_allowed(acting.id, body.catalog, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Collection non accessible.")
    try:
        item = purchase_item(acting.id, body.catalog, body.item_id, db, currency=body.currency)
    except (CatalogNotFoundError, ItemNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AlreadyOwnedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InsufficientBalanceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PurchaseResponse(
        item=item,
        catalog=body.catalog,
        balance=wallet_balance(acting.id, body.currency, db),
        unlocked_count=len(get_unlocked_ids(acting.id, body.catalog, db)),
    )


@router.get("/awards/unseen", response_model=list[AwardResponse])
async def get_unseen_awards(
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AwardResponse]:
    """Points attribués non encore vus par l'enfant (pour la notification)."""
    return [AwardResponse.model_validate(a) for a in unseen_awards(acting.id, db)]


@router.post("/awards/ack", status_code=status.HTTP_204_NO_CONTENT)
async def ack_awards(
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Marque comme vues les attributions de points de l'enfant."""
    acknowledge_awards(acting.id, db)
