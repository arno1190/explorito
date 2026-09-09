"""Schémas de la politique de confidentialité des familles."""

from datetime import datetime

from pydantic import BaseModel, Field


class PrivacyPolicy(BaseModel):
    """Politique en vigueur, et son acceptation par le compte qui la demande."""

    version: str = Field(..., description="Version datée du texte en vigueur")
    text: str = Field(..., description="Texte intégral de la politique")
    accepted: bool = Field(False, description="Vrai si ce compte a accepté la version en vigueur")
    accepted_at: datetime | None = Field(None, description="Horodatage de l'acceptation enregistrée")


class PrivacyAccept(BaseModel):
    """Acceptation explicite d'une version précise.

    La version est envoyée par le client et vérifiée côté serveur : accepter
    « la version en vigueur » sans la nommer laisserait passer une acceptation
    portant sur un texte que le parent n'avait pas sous les yeux.
    """

    version: str = Field(..., description="Version affichée au parent au moment de la case cochée")
