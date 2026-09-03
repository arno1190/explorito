"""Bibliothèque parent : catalogue des packs, activation par enfant, signalements.

L'accès communautaire est en opt-in : « approuvé » signifie « listé au catalogue
parent », pas « livré aux enfants ». Deux adultes restent dans la chaîne.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user
from app.core.database import get_db
from app.core.security import verify_password
from app.models.content import LevelEnum
from app.models.pack import PackRequest
from app.models.user import Profile, User, UserRole
from app.schemas.library import (
    AccessUpdate,
    AutoEnableState,
    AutoEnableUpdate,
    ChildAccessState,
    ContributorStats,
    PackRequestDecision,
    PackRequestResponse,
    ReportCreate,
    ReportResponse,
)
from app.schemas.pack import PackDetail, PackSummary
from app.services import library as library_service
from app.services.contribution import pack_detail
from app.services.guardianship import guarded_child_ids, is_guardian

router = APIRouter()


def _require_adult(current_user: User) -> None:
    """La bibliothèque est une surface d'adulte : un compte enfant n'y entre pas."""
    if current_user.role not in (UserRole.PARENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les parents peuvent accéder à la bibliothèque",
        )


def _require_guardian(child_id: UUID, current_user: User, db: Session) -> None:
    """Seul un responsable de cet enfant (ou un admin) lit ou change ses accès.

    Réutilise :func:`app.services.guardianship.is_guardian` : inventer une
    seconde règle d'autorisation ici garantirait qu'elles divergent. Le refus
    est un 404, comme dans ``/children`` : ne pas révéler l'existence d'un
    enfant dont on n'est pas responsable.
    """
    _require_adult(current_user)
    if current_user.role == UserRole.ADMIN or is_guardian(current_user.id, child_id, db):
        return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enfant non trouvé")


def _require_pin(current_user: User, pin: str) -> None:
    """Vérifie le code PIN parent, avec le même hash que ``POST /auth/verify-pin``.

    Même helper (:func:`app.core.security.verify_password`), même colonne
    (``User.pin_hash``) : le PIN reste une seule et même porte, quel que soit
    l'écran qui la franchit.

    Le statut est un **403, jamais un 401** : l'appelant *est* authentifié, il
    s'est seulement trompé de code. Un 401 déclencherait la déconnexion globale
    de l'intercepteur axios du frontend, et un parent perdrait sa session pour
    une faute de frappe à quatre chiffres.

    Raises:
        HTTPException: 403 ``pin_not_set`` si aucun PIN n'est défini, 403
        ``invalid_pin`` si le PIN est erroné.
    """
    if not current_user.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "pin_not_set", "message": "Aucun code PIN défini."},
        )
    if not verify_password(pin, current_user.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "invalid_pin", "message": "Code PIN incorrect."},
        )


# --------------------------------------------------------------------------- #
# Catalogue et aperçu
# --------------------------------------------------------------------------- #
@router.get("/catalogue", response_model=list[PackSummary])
async def get_catalogue(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    level: Annotated[LevelEnum | None, Query(description="Ne garder que les packs couvrant ce niveau")] = None,
    subject: Annotated[str | None, Query(description="Slug de matière")] = None,
    tag: Annotated[str | None, Query(description="Étiquette de thème")] = None,
    sort: Annotated[str, Query(pattern="^(newest|most_enabled)$")] = "newest",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[PackSummary]:
    """Catalogue parent : packs officiels et packs communautaires approuvés."""
    _require_adult(current_user)
    return library_service.catalogue(
        db,
        level=level,
        subject_slug=subject,
        tag=tag,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/packs/{pack_id}", response_model=PackDetail)
async def get_pack_preview(
    pack_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PackDetail:
    """Aperçu complet d'un pack **avant** activation : toutes les leçons, tous
    les exercices. Un parent ne peut pas consentir à ce qu'il n'a pas pu lire."""
    _require_adult(current_user)
    pack = library_service.catalogue_pack(db, pack_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pack non trouvé.")
    return pack_detail(db, pack)


# --------------------------------------------------------------------------- #
# Liste blanche par enfant
# --------------------------------------------------------------------------- #
def _access_state(child_id: UUID, db: Session) -> ChildAccessState:
    """État d'accès d'un enfant : l'interrupteur global et les lignes explicites."""
    profile = db.query(Profile).filter(Profile.user_id == child_id).first()
    return ChildAccessState(
        child_id=child_id,
        auto_enable_approved_packs=bool(profile.auto_enable_approved_packs) if profile else False,
        entries=library_service.access_entries(db, child_id),
    )


@router.get("/children/{child_id}/access", response_model=ChildAccessState)
async def get_child_access(
    child_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChildAccessState:
    """Packs communautaires activés (ou désactivés) pour cet enfant.

    Les packs officiels n'y figurent pas : ils sont implicites au niveau de
    l'enfant et ne demandent aucune action parentale.
    """
    _require_guardian(child_id, current_user, db)
    return _access_state(child_id, db)


@router.put("/children/{child_id}/access/{pack_id}", response_model=ChildAccessState)
async def put_child_access(
    child_id: UUID,
    pack_id: UUID,
    payload: AccessUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChildAccessState:
    """Active ou désactive un pack pour un enfant (le garde acteur est journalisé).

    Désactiver masque le pack et ne détruit aucune progression.
    """
    _require_guardian(child_id, current_user, db)
    library_service.set_access(
        db,
        child_id=child_id,
        pack_id=pack_id,
        enabled=payload.enabled,
        guardian=current_user,
    )
    return _access_state(child_id, db)


@router.put("/children/{child_id}/auto-enable", response_model=AutoEnableState)
async def put_auto_enable(
    child_id: UUID,
    payload: AutoEnableUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AutoEnableState:
    """Interrupteur « activer automatiquement les packs approuvés à son niveau ».

    Par enfant, désactivé par défaut.
    """
    _require_guardian(child_id, current_user, db)
    profile = library_service.set_auto_enable(db, child_id=child_id, enabled=payload.enabled, guardian=current_user)
    return AutoEnableState(child_id=child_id, enabled=bool(profile.auto_enable_approved_packs))


# --------------------------------------------------------------------------- #
# Contributeur et signalements
# --------------------------------------------------------------------------- #
@router.get("/me/contributor-stats", response_model=ContributorStats)
async def get_contributor_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ContributorStats:
    """Statistiques d'auteur de l'appelant : la reconnaissance est la seule
    récompense offerte, ces nombres doivent donc être réels."""
    _require_adult(current_user)
    return ContributorStats(**library_service.contributor_stats(db, current_user.id))


@router.post("/packs/{pack_id}/report", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def report_pack(
    pack_id: UUID,
    payload: ReportCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReportResponse:
    """Signale un pack. Filet de sécurité des auteurs « de confiance », dont le
    contenu publie sans revue préalable."""
    _require_adult(current_user)
    report = library_service.report_pack(
        db,
        pack_id=pack_id,
        reporter_id=current_user.id,
        reason=payload.reason,
        details=payload.details,
    )
    return ReportResponse.model_validate(report)


# --------------------------------------------------------------------------- #
# Demandes des enfants
# --------------------------------------------------------------------------- #
@router.get("/requests", response_model=list[PackRequestResponse])
async def get_pending_requests(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PackRequestResponse]:
    """Demandes « Je veux ça ! » en attente, tous enfants de l'appelant confondus."""
    _require_adult(current_user)
    child_ids = guarded_child_ids(current_user.id, db)
    requests = library_service.pending_requests_for_guardian(db, child_ids)
    return [library_service.request_response(db, r) for r in requests]


@router.post("/requests/{request_id}/decide", response_model=PackRequestResponse)
async def decide_request(
    request_id: UUID,
    payload: PackRequestDecision,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PackRequestResponse:
    """Tranche une demande, derrière le code PIN parent.

    Le PIN est vérifié **ici**, côté serveur, avec le même helper que
    ``POST /auth/verify-pin`` : l'écran de décision est atteignable depuis un
    téléphone que l'enfant a en main, un simple garde côté client ne suffirait
    pas. L'approbation écrit la ligne d'accès et l'audite.
    """
    _require_adult(current_user)
    request = db.query(PackRequest).filter(PackRequest.id == request_id).first()
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demande non trouvée.")
    _require_guardian(request.child_id, current_user, db)
    _require_pin(current_user, payload.pin)

    decided = library_service.decide_request(db, request=request, approve=payload.approve, guardian=current_user)
    return library_service.request_response(db, decided)
