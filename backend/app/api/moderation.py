"""Surface de modération : file d'attente, verdicts, ratification de difficulté.

Surface volontairement isolée et joignable avec un jeton *restreint* : une fuite
se borne alors à « quelqu'un peut approuver ou refuser des packs », ce qui est
réparable, contrairement à « quelqu'un peut supprimer des comptes ».

Le jeton n'ouvre **que** ce routeur : il n'est lu nulle part ailleurs, et aucune
dépendance de ce module ne se substitue à ``get_current_active_user``. Une
session admin normale reste acceptée, ce qui garde l'écran admin fonctionnel
sans distribuer le jeton.
"""

import secrets
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user, get_current_user
from app.api.subjects import require_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.contribution import PackReport, ReportStatus
from app.models.pack import CommunityStatus, Pack
from app.models.user import User
from app.schemas.moderation import (
    AuditRow,
    ContributorRow,
    ModerationPackDetail,
    ModerationQueue,
    ModerationQueueEntry,
    PackReviewRequest,
    ReportDecisionRequest,
    ReportRow,
    TrustRequest,
)
from app.services import moderation as service

router = APIRouter()

#: Extraction du porteur JWT **sans** erreur automatique : l'absence de session
#: n'est pas un échec ici, puisque le jeton de modération est l'autre entrée.
_bearer = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/dev-login", auto_error=False)


@dataclass(frozen=True)
class ModerationActor:
    """Qui agit : un admin identifié, ou le jeton de modération (anonyme).

    ``actor_id`` vaut ``None`` pour le jeton : l'audit enregistre alors une
    action sans compte, ce qui est exactement l'information disponible.
    """

    user: User | None
    via: str

    @property
    def actor_id(self) -> UUID | None:
        """Identifiant de l'admin, ou ``None`` si l'action vient du jeton."""
        return self.user.id if self.user is not None else None


async def require_moderation(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Depends(_bearer)] = None,
    x_moderation_token: Annotated[str | None, Header()] = None,
) -> ModerationActor:
    """Autorise l'accès à ``/moderation/*`` : session admin **ou** jeton dédié.

    Le jeton est comparé en temps constant. ``MODERATION_TOKEN`` vide désactive
    entièrement cette entrée : sans ce garde, une configuration par défaut
    (chaîne vide de part et d'autre) rendrait la modération publique.

    L'incarnation (``X-Impersonate-User-Id``) est neutralisée sur cette surface :
    modérer « en tant que » quelqu'un n'a aucun sens et brouillerait l'audit.

    Raises:
        HTTPException: 401 sans authentification, 403 si le jeton est refusé ou
            si le compte n'est pas administrateur.
    """
    if x_moderation_token:
        expected = settings.MODERATION_TOKEN
        if not expected or not secrets.compare_digest(x_moderation_token, expected):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Jeton de modération invalide.")
        return ModerationActor(user=None, via="token")

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise (session administrateur ou jeton de modération).",
            headers={"WWW-Authenticate": "Bearer"},
        )
    current = await get_current_user(request=request, token=token, db=db, x_impersonate_user_id=None)
    admin = require_admin(current_user=await get_current_active_user(current_user=current))
    return ModerationActor(user=admin, via="admin")


def _pack_or_404(db: Session, pack_id: UUID) -> Pack:
    pack = db.query(Pack).filter(Pack.id == pack_id).first()
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pack introuvable.")
    return pack


def _detail(db: Session, pack: Pack) -> ModerationPackDetail:
    """Détail complet d'un pack pour la revue (contenu + signalements + audit)."""
    from app.services.contribution import pack_detail

    base = pack_detail(db, pack).model_dump()
    pack_reports = [ReportRow(**row) for row in service.reports(db, status=None, pack_id=pack.id)]
    parent_title = None
    if pack.cloned_from_pack_id:
        parent_title = db.query(Pack.title).filter(Pack.id == pack.cloned_from_pack_id).scalar()
    return ModerationPackDetail(
        **base,
        author_id=pack.author_id,
        open_reports=sum(1 for r in pack_reports if r.status is ReportStatus.OPEN),
        cloned_from_title=parent_title,
        reports=pack_reports,
        audit=[AuditRow.model_validate(row) for row in service.audit_trail(db, pack_id=pack.id)],
    )


@router.get("/queue", response_model=ModerationQueue)
async def get_queue(
    _actor: Annotated[ModerationActor, Depends(require_moderation)],
    db: Annotated[Session, Depends(get_db)],
    community_status: Annotated[CommunityStatus, Query(alias="status")] = CommunityStatus.PENDING,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> ModerationQueue:
    """File de revue : packs d'un statut donné, du plus récemment soumis au plus ancien."""
    items = [ModerationQueueEntry(**row) for row in service.queue(db, status=community_status, limit=limit)]
    return ModerationQueue(status=community_status, count=len(items), items=items)


@router.get("/packs/{pack_id}", response_model=ModerationPackDetail)
async def get_pack(
    pack_id: UUID,
    _actor: Annotated[ModerationActor, Depends(require_moderation)],
    db: Annotated[Session, Depends(get_db)],
) -> ModerationPackDetail:
    """Pack complet à relire : leçons, exercices, avertissements, signalements, lignée."""
    return _detail(db, _pack_or_404(db, pack_id))


@router.patch("/packs/{pack_id}", response_model=ModerationPackDetail)
async def review_pack(
    pack_id: UUID,
    payload: PackReviewRequest,
    actor: Annotated[ModerationActor, Depends(require_moderation)],
    db: Annotated[Session, Depends(get_db)],
) -> ModerationPackDetail:
    """Corrige et/ou décide un pack.

    Les corrections sont appliquées avant le verdict : à la revue, on répare
    d'abord, on décide ensuite. Sans ``verdict``, aucun statut n'est écrit — un
    verdict que l'admin n'a pas prononcé ne doit jamais atterrir en base.
    """
    pack = _pack_or_404(db, pack_id)
    if payload.changes is not None:
        changes = payload.changes.model_dump(exclude_unset=True)
        if changes:
            service.admin_edit(db, pack=pack, actor_id=actor.actor_id, changes=changes)
    if payload.verdict is not None:
        service.apply_verdict(
            db,
            pack=pack,
            verdict=payload.verdict,
            actor_id=actor.actor_id,
            notes=payload.notes,
            quality_score=payload.quality_score,
            ratify_difficulty=payload.ratify_difficulty,
        )
    return _detail(db, pack)


@router.get("/reports", response_model=list[ReportRow])
async def get_reports(
    _actor: Annotated[ModerationActor, Depends(require_moderation)],
    db: Annotated[Session, Depends(get_db)],
    report_status: Annotated[ReportStatus | None, Query(alias="status")] = ReportStatus.OPEN,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ReportRow]:
    """Signalements de parents (``status=`` vide pour tous les statuts)."""
    return [ReportRow(**row) for row in service.reports(db, status=report_status, limit=limit)]


@router.patch("/reports/{report_id}", response_model=ReportRow)
async def decide_report(
    report_id: UUID,
    payload: ReportDecisionRequest,
    actor: Annotated[ModerationActor, Depends(require_moderation)],
    db: Annotated[Session, Depends(get_db)],
) -> ReportRow:
    """Clôt un signalement, et bloque le pack visé si ``block_pack`` est demandé."""
    report = db.query(PackReport).filter(PackReport.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signalement introuvable.")
    service.resolve_report(
        db,
        report=report,
        actor_id=actor.actor_id,
        decision=payload.status,
        block_pack=payload.block_pack,
    )
    return ReportRow(**service.report_row(db, report))


@router.get("/contributors", response_model=list[ContributorRow])
async def get_contributors(
    _actor: Annotated[ModerationActor, Depends(require_moderation)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[ContributorRow]:
    """Contributeurs : conditions acceptées, packs approuvés, familles touchées, éligibilité."""
    return [ContributorRow(**row) for row in service.contributors(db, limit=limit)]


@router.post("/contributors/{user_id}/trust", response_model=ContributorRow)
async def set_trust(
    user_id: UUID,
    payload: TrustRequest,
    actor: Annotated[ModerationActor, Depends(require_moderation)],
    db: Annotated[Session, Depends(get_db)],
) -> ContributorRow:
    """Accorde ou retire le palier de confiance d'un contributeur (jamais automatique)."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable.")
    profile = service.grant_trust(db, user=user, actor_id=actor.actor_id, trusted=payload.trusted)
    return ContributorRow(**service.contributor_row(db, profile))
