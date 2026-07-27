"""
Schémas Pydantic pour le défi Pythagore (mini-jeu de tables de multiplication).

La correction est faite côté serveur : le client renvoie les opérandes ``a`` et
``b`` et sa réponse ; le serveur recalcule ``a * b`` (jamais confiance au score
annoncé). L'XP dépend d'un tarif de base par difficulté, d'un bonus de série et
d'une pénalité par erreur, le tout borné par un plafond quotidien.
"""

from enum import Enum

from pydantic import BaseModel, Field


class PythagoreDifficulty(str, Enum):
    """Difficulté du défi (détermine les tables proposées et l'XP de base)."""

    FACILE = "facile"
    MOYEN = "moyen"
    DIFFICILE = "difficile"


class PythagoreItem(BaseModel):
    """Une question répondue : opérandes + réponse donnée par l'enfant."""

    a: int = Field(..., ge=1, le=12, description="Premier opérande")
    b: int = Field(..., ge=1, le=12, description="Second opérande")
    answer: int = Field(..., description="Réponse donnée par l'enfant")


class PythagoreSessionRequest(BaseModel):
    """Session soumise : difficulté choisie + questions répondues (1 à 20)."""

    difficulty: PythagoreDifficulty = PythagoreDifficulty.MOYEN
    items: list[PythagoreItem] = Field(..., min_length=1, max_length=20)


class PythagoreItemResult(BaseModel):
    """Correction d'une question (réponse attendue vs donnée)."""

    a: int
    b: int
    answer: int
    expected: int
    correct: bool


class PythagoreSessionResponse(BaseModel):
    """Résultat de la session : score, série, XP attribué (après plafond) et solde."""

    correct: int
    total: int
    longest_streak: int
    xp_earned: int
    capped: bool = Field(description="Vrai si le plafond quotidien a limité l'XP")
    balance: int = Field(description="Solde XP dépensable (Pokédex) après la session")
    results: list[PythagoreItemResult]
