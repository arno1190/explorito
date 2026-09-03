"""Annonces produit par email (surface admin).

Rédaction, aperçu, envoi reprenable et journal de livraison. Les destinataires
sont les comptes parents actifs non désinscrits.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.subjects import require_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.announcement import (
    Announcement,
    AnnouncementDelivery,
    AnnouncementStatus,
    DeliveryStatus,
)
from app.models.user import User
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementDeliveryItem,
    AnnouncementDetail,
    AnnouncementPreview,
    AnnouncementSendResult,
    AnnouncementSummary,
    UnsubscribeRequest,
    UnsubscribeResponse,
)
from app.services.mail import (
    MailNotConfigured,
    build_html,
    build_text,
    read_unsubscribe_token,
    recipients,
    send_announcement,
)

router = APIRouter()


def _delivery_counts(db: Session, announcement_id: UUID) -> dict[str, int]:
    """Compteurs par statut, tous les statuts présents (même à zéro)."""
    counts = {member.value: 0 for member in DeliveryStatus}
    rows = db.query(AnnouncementDelivery).filter(AnnouncementDelivery.announcement_id == announcement_id).all()
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    return counts


def _summary(db: Session, announcement: Announcement) -> AnnouncementSummary:
    return AnnouncementSummary(
        id=announcement.id,
        subject=announcement.subject,
        from_email=announcement.from_email,
        status=announcement.status,
        created_at=announcement.created_at,
        sent_at=announcement.sent_at,
        delivery_counts=_delivery_counts(db, announcement.id),
    )


def _detail(db: Session, announcement: Announcement) -> AnnouncementDetail:
    deliveries = (
        db.query(AnnouncementDelivery)
        .filter(AnnouncementDelivery.announcement_id == announcement.id)
        .order_by(AnnouncementDelivery.email)
        .all()
    )
    return AnnouncementDetail(
        **_summary(db, announcement).model_dump(),
        body_markdown=announcement.body_markdown,
        deliveries=[
            AnnouncementDeliveryItem(
                email=row.email,
                status=row.status,
                attempts=row.attempts or 0,
                error=row.error,
                sent_at=row.sent_at,
            )
            for row in deliveries
        ],
    )


def _get_announcement(announcement_id: UUID, db: Session) -> Announcement:
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if announcement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annonce introuvable")
    return announcement


@router.post("/unsubscribe", response_model=UnsubscribeResponse)
async def unsubscribe(
    payload: UnsubscribeRequest,
    db: Annotated[Session, Depends(get_db)],
) -> UnsubscribeResponse:
    """Désinscrit un compte des annonces produit depuis le lien d'un email.

    Route volontairement **non authentifiée** : un parent qui ne veut plus de
    ces emails ne doit pas avoir à se connecter pour le dire. La signature du
    jeton (et son claim ``typ``) est la seule autorisation.
    """
    user_id = read_unsubscribe_token(payload.token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien de désinscription invalide ou expiré")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable")
    user.email_opt_out = True
    db.commit()
    return UnsubscribeResponse(unsubscribed=True, email=user.email)


@router.get("", response_model=list[AnnouncementSummary])
async def list_announcements(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AnnouncementSummary]:
    """Liste les annonces, de la plus récente à la plus ancienne."""
    announcements = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return [_summary(db, announcement) for announcement in announcements]


@router.post("", response_model=AnnouncementDetail, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    payload: AnnouncementCreate,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AnnouncementDetail:
    """Crée un brouillon d'annonce (aucun email n'est envoyé ici)."""
    announcement = Announcement(
        subject=payload.subject,
        body_markdown=payload.body_markdown,
        # Expéditeur figé à la création : l'audit doit rester vrai même si la
        # configuration change après coup.
        from_email=settings.MAIL_FROM,
        status=AnnouncementStatus.DRAFT.value,
        created_by=admin.id,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return _detail(db, announcement)


@router.get("/{announcement_id}", response_model=AnnouncementDetail)
async def get_announcement(
    announcement_id: UUID,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AnnouncementDetail:
    """Détail d'une annonce et journal de ses livraisons."""
    return _detail(db, _get_announcement(announcement_id, db))


@router.get("/{announcement_id}/preview", response_model=AnnouncementPreview)
async def preview_announcement(
    announcement_id: UUID,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AnnouncementPreview:
    """Rend l'email tel qu'il partira, avec le nombre de destinataires.

    Le lien de désinscription de l'aperçu est celui de l'admin connecté : il
    reste cliquable sans piéger un vrai destinataire.
    """
    announcement = _get_announcement(announcement_id, db)
    targets = recipients(db)
    link = f"{settings.PUBLIC_APP_URL.rstrip('/')}/desinscription?token=apercu"
    return AnnouncementPreview(
        subject=announcement.subject,
        html=build_html(announcement.subject, announcement.body_markdown, link),
        text=build_text(announcement.body_markdown, link),
        recipient_count=len(targets),
    )


@router.post("/{announcement_id}/send", response_model=AnnouncementSendResult)
async def send(
    announcement_id: UUID,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    dry_run: bool = Query(False, description="Prépare les livraisons sans envoyer d'email"),
) -> AnnouncementSendResult:
    """Envoie (ou simule) l'annonce. Relancer ne réexpédie que les échecs."""
    announcement = _get_announcement(announcement_id, db)

    if dry_run:
        counts = send_announcement(db, announcement, dry_run=True)
        return AnnouncementSendResult(dry_run=True, status=announcement.status, counts=counts)

    previous_status = announcement.status
    announcement.status = AnnouncementStatus.SENDING.value
    db.commit()
    try:
        counts = send_announcement(db, announcement)
    except MailNotConfigured as exc:
        # Rien n'est parti : on rend son statut initial à l'annonce.
        announcement.status = previous_status
        db.commit()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    announcement.status = AnnouncementStatus.FAILED.value if counts["failed"] else AnnouncementStatus.SENT.value
    announcement.sent_at = datetime.utcnow()
    db.commit()
    return AnnouncementSendResult(dry_run=False, status=announcement.status, counts=counts)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: UUID,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Supprime un brouillon. Une annonce envoyée est une trace : elle reste."""
    announcement = _get_announcement(announcement_id, db)
    if announcement.status != AnnouncementStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seul un brouillon peut être supprimé",
        )
    db.delete(announcement)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
