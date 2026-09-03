"""Schémas Pydantic des annonces produit (surface admin + désinscription).

Le corps circule toujours en Markdown : le HTML n'est produit qu'à l'aperçu et
à l'envoi, jamais stocké, pour qu'une correction du gabarit profite aux annonces
déjà rédigées.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    """Rédaction d'un brouillon d'annonce."""

    subject: str = Field(min_length=1, max_length=200)
    body_markdown: str = Field(min_length=1)


class AnnouncementSummary(BaseModel):
    """Ligne de liste : de quoi savoir où en est chaque annonce."""

    id: UUID
    subject: str
    from_email: str
    status: str
    created_at: datetime
    sent_at: datetime | None = None
    # Compteurs par statut de livraison (pending/sent/failed/skipped).
    delivery_counts: dict[str, int] = Field(default_factory=dict)


class AnnouncementDeliveryItem(BaseModel):
    """État d'envoi vers un destinataire."""

    email: str
    status: str
    attempts: int
    error: str | None = None
    sent_at: datetime | None = None


class AnnouncementDetail(AnnouncementSummary):
    """Annonce complète, avec son corps et son journal de livraison."""

    body_markdown: str
    deliveries: list[AnnouncementDeliveryItem] = Field(default_factory=list)


class AnnouncementPreview(BaseModel):
    """Aperçu avant envoi : ce que verra un parent, et combien en recevront un."""

    subject: str
    html: str
    text: str
    recipient_count: int


class AnnouncementSendResult(BaseModel):
    """Bilan d'un envoi (ou d'une simulation)."""

    dry_run: bool
    status: str
    counts: dict[str, int]


class UnsubscribeRequest(BaseModel):
    """Désinscription depuis le lien d'un email (jeton signé, sans connexion)."""

    token: str = Field(min_length=1)


class UnsubscribeResponse(BaseModel):
    """Confirmation de désinscription."""

    unsubscribed: bool
    email: str | None = None
