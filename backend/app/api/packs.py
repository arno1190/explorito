"""Chemin d'accueil de l'enfant orienté packs (lentilles Thèmes / Matières).

Le modèle de lecture vit ici plutôt que dans le frontend : le verrou est calculé
par ``services/progression.py`` (source de vérité unique) et la carte
« Continuer » est résolue côté serveur, pour que toutes les surfaces s'accordent.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.subjects import acting_child, child_content_level
from app.core.database import get_db
from app.models.user import User
from app.schemas.pack_path import (
    ContinuerCard,
    PackLensResponse,
    PackLensUpdate,
    PackPathEntry,
    PackPathResponse,
)
from app.services.pack_path import continuer, pack_path, pack_path_entries, set_pack_lens

router = APIRouter()


@router.get("/path", response_model=PackPathResponse)
async def child_pack_path(
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> PackPathResponse:
    """
    Chemin d'accueil de l'enfant courant : packs, leçons, verrous, cumuls.

    Les deux lentilles (Thèmes, Matières) consomment cette **même** charge utile ;
    seul le regroupement diffère côté client. Les leçons terminées sont incluses
    (le client les replie), afin que le contenu de révision reste atteignable.

    Args:
        acting: Enfant dont la perspective s'applique.
        db: Session de base de données.

    Returns:
        Lentille active, entrées de packs et carte « Continuer ».
    """
    return pack_path(acting.id, child_content_level(acting, db), db)


@router.get("/continuer", response_model=ContinuerCard | None)
async def child_continuer(
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> ContinuerCard | None:
    """
    Unique leçon recommandée pour l'enfant courant.

    ``null`` n'est pas une erreur : c'est l'état vide honnête (plus rien à faire,
    ou aucun pack activé).

    Args:
        acting: Enfant dont la perspective s'applique.
        db: Session de base de données.

    Returns:
        La carte « Continuer », ou ``None``.
    """
    return continuer(acting.id, child_content_level(acting, db), db)


@router.put("/lens", response_model=PackLensResponse)
async def update_pack_lens(
    payload: PackLensUpdate,
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> PackLensResponse:
    """
    Enregistre la lentille d'accueil de l'enfant courant.

    Persistée **par enfant** (``Profile.pack_lens``) : deux enfants d'une même
    famille n'ont pas la même façon de chercher leur contenu.

    Args:
        payload: Lentille choisie (``themes`` ou ``matieres``).
        acting: Enfant dont la perspective s'applique.
        db: Session de base de données.

    Returns:
        La lentille effective.

    Raises:
        HTTPException: Si l'utilisateur courant n'a pas de profil.
    """
    lens = set_pack_lens(acting.id, payload.lens, db)
    if lens is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil non trouvé")
    db.commit()
    return PackLensResponse(lens=lens)


@router.get("/{pack_id}", response_model=PackPathEntry)
async def get_pack_path_entry(
    pack_id: UUID,
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> PackPathEntry:
    """
    Entrée de chemin d'un seul pack (dépliage d'une ligne trophée).

    Args:
        pack_id: ID du pack.
        acting: Enfant dont la perspective s'applique.
        db: Session de base de données.

    Returns:
        L'entrée du pack : carte, leçons et cumul.

    Raises:
        HTTPException: 404 si le pack n'existe pas, est vide au niveau de
            l'enfant, ou ne lui est pas accessible — on ne distingue pas les
            trois cas, pour ne pas révéler l'existence d'un pack non activé.
    """
    entries = pack_path_entries(acting.id, child_content_level(acting, db), db, only_pack_ids={pack_id})
    if not entries:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pack non trouvé")
    return entries[0]
