"""« Découvrir » : l'enfant demande, l'adulte tranche.

Inverse le problème de la demande : la découverte est faite par l'enfant — ce
qu'il aime — et le travail de l'adulte se réduit à un oui/non derrière le PIN.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.subjects import acting_child, child_content_level
from app.core.database import get_db
from app.models.content import LevelEnum
from app.models.user import User
from app.schemas.library import DiscoverPack, PackRequestCreate, PackRequestResponse
from app.services import library as library_service

router = APIRouter()


def _child_level(acting: User, db: Session) -> LevelEnum:
    """Niveau de l'enfant dont la perspective s'applique.

    « Découvrir » est une surface d'enfant : sans enfant actif (parent sans
    en-tête ``X-Acting-Child-Id``) il n'y a pas de niveau, donc pas de
    catalogue à filtrer — on refuse plutôt que de renvoyer une liste vide qui
    ressemblerait à « la communauté n'a rien publié ».

    Raises:
        HTTPException: 400 s'il n'y a pas d'enfant actif (ou pas de niveau).
    """
    level = child_content_level(acting, db)
    if level is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun enfant actif : « Découvrir » se consulte depuis un profil enfant.",
        )
    return level


@router.get("", response_model=list[DiscoverPack])
async def discover(
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[DiscoverPack]:
    """Packs approuvés au niveau de l'enfant qu'il n'a pas encore.

    Ne renvoie **jamais** un pack ``draft``, ``pending``, ``rejected`` ou
    ``blocked``, et n'expose que des métadonnées d'enfant : titre, emoji,
    description, badges de matière, nombre de familles, pseudonyme de l'auteur.
    """
    level = _child_level(acting, db)
    return library_service.discoverable(db, child_id=acting.id, level=level, limit=limit)


@router.post("/requests", response_model=PackRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: PackRequestCreate,
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> PackRequestResponse:
    """« Je veux ça ! » : crée une demande en attente. N'accorde jamais l'accès."""
    _child_level(acting, db)
    request = library_service.request_pack(db, child_id=acting.id, pack_id=payload.pack_id)
    return library_service.request_response(db, request)


@router.get("/requests", response_model=list[PackRequestResponse])
async def list_requests(
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PackRequestResponse]:
    """Demandes de l'enfant encore en attente d'une décision parentale."""
    _child_level(acting, db)
    return [library_service.request_response(db, r) for r in library_service.child_requests(db, acting.id)]
