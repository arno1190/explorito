"""Endpoints du défi Sudoku (mini-jeu « free XP », 3 niveaux).

La génération et la validation sont serveur : le client demande une grille, la
remplit, puis renvoie sa solution. Le serveur valide et crédite l'XP (une seule
fois par grille). L'XP est attribué à l'enfant actif (``acting_child``).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.subjects import acting_child
from app.core.database import get_db
from app.models.challenge import SudokuSession
from app.models.user import User
from app.schemas.sudoku import (
    NewPuzzleRequest,
    PuzzleResponse,
    SolveRequest,
    SolveResponse,
)
from app.services.sudoku import new_puzzle, solve

router = APIRouter()


@router.post("/new", response_model=PuzzleResponse)
async def create_puzzle(
    payload: NewPuzzleRequest,
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> PuzzleResponse:
    """Génère une nouvelle grille de Sudoku pour le niveau demandé."""
    return PuzzleResponse(**new_puzzle(acting.id, payload.difficulty, db))


@router.post("/{session_id}/solve", response_model=SolveResponse)
async def solve_puzzle(
    session_id: UUID,
    payload: SolveRequest,
    acting: Annotated[User, Depends(acting_child)],
    db: Annotated[Session, Depends(get_db)],
) -> SolveResponse:
    """Vérifie la solution d'une grille et crédite l'XP si elle est correcte."""
    session = db.query(SudokuSession).filter(SudokuSession.id == session_id).first()
    if session is None or session.user_id != acting.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grille introuvable")
    return SolveResponse(**solve(session, payload.grid, db))
