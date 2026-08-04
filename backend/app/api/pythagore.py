"""
Endpoints du défi Pythagore (mini-jeu de tables de multiplication, XP « libre »).

La correction et le calcul d'XP sont faits côté serveur (voir
``app.services.pythagore``) : le client n'annonce jamais son score, il envoie ses
réponses et le serveur recalcule tout.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.subjects import acting_child
from app.core.database import get_db
from app.models.user import User
from app.schemas.pythagore import PythagoreSessionRequest, PythagoreSessionResponse
from app.services.pythagore import run_session

router = APIRouter()


@router.post("/session", response_model=PythagoreSessionResponse)
async def play_session(
    payload: PythagoreSessionRequest,
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> PythagoreSessionResponse:
    """
    Joue une session du défi Pythagore et attribue l'XP gagné.

    Le serveur corrige chaque question (``a * b``), calcule le bonus de série et la
    pénalité d'erreur, applique le plafond quotidien anti-farm puis crédite le
    porte-monnaie XP (alimente le Pokédex).

    Args:
        payload: Difficulté choisie et réponses de l'enfant.
        current_user: Utilisateur authentifié.
        db: Session de base de données.

    Returns:
        Correction détaillée, série la plus longue, XP attribué (après plafond) et
        nouveau solde dépensable.
    """
    summary = run_session(acting.id, payload.items, payload.difficulty, db)
    return PythagoreSessionResponse(**summary)
