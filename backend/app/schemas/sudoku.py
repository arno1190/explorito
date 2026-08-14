"""Schémas Pydantic pour le défi Sudoku (mini-jeu « free XP »).

Trois niveaux : ``easy`` (grille 4×4, 10 XP), ``medium`` (6×6, 20 XP) et ``hard``
(8×8, 30 XP). Le serveur génère la grille et valide la solution (règles du Sudoku
+ respect des indices) : le client n'annonce jamais son gain.
"""

from enum import Enum

from pydantic import BaseModel, Field


class SudokuDifficulty(str, Enum):
    """Niveau du défi Sudoku (détermine la taille de grille et l'XP)."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class NewPuzzleRequest(BaseModel):
    """Demande d'une nouvelle grille pour un niveau donné."""

    difficulty: SudokuDifficulty = SudokuDifficulty.EASY


class PuzzleResponse(BaseModel):
    """Grille générée : indices de départ (0 = case vide) et métadonnées."""

    session_id: str
    difficulty: SudokuDifficulty
    size: int = Field(description="Côté de la grille (4, 6 ou 8)")
    box_rows: int = Field(description="Hauteur d'un bloc")
    box_cols: int = Field(description="Largeur d'un bloc")
    puzzle: list[list[int]] = Field(description="Grille de départ, 0 pour les cases à remplir")
    xp_reward: int = Field(description="XP attribué en cas de résolution")


class SolveRequest(BaseModel):
    """Solution soumise : grille complète size×size (valeurs 1..size)."""

    grid: list[list[int]]


class SolveResponse(BaseModel):
    """Résultat de la vérification serveur."""

    correct: bool
    already_solved: bool = Field(default=False, description="Grille déjà validée auparavant")
    xp_earned: int = Field(default=0, description="XP crédité (0 si déjà résolu ou incorrect)")
    balance: int = Field(default=0, description="Solde XP dépensable (Pokédex) après vérification")
