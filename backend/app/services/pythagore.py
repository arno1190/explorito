"""
Service du défi Pythagore : correction serveur, calcul d'XP et attribution.

Règles d'XP (toutes réglables dans ``settings``) :
- tarif de base par bonne réponse selon la difficulté ;
- bonus de série : +``PYTHAGORE_STREAK_BONUS`` par bonne réponse au-delà de 2
  consécutives ;
- pénalité par erreur : −``PYTHAGORE_FAILURE_PENALTY`` (le total est planché à 0) ;
- plafond quotidien : ``PYTHAGORE_DAILY_XP_CAP`` XP/jour (anti-farm).

L'XP est attribué via :func:`app.services.gamification.award_xp` sur une matière
« Défis » dédiée, afin d'alimenter le porte-monnaie dépensable du Pokédex.
"""

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.challenge import PythagoreSession
from app.models.content import Subject
from app.schemas.pythagore import (
    PythagoreDifficulty,
    PythagoreItem,
    PythagoreItemResult,
)
from app.services.collection import get_balance
from app.services.gamification import award_xp

CHALLENGE_SUBJECT_SLUG = "defis"

_BASE_XP: dict[PythagoreDifficulty, int] = {
    PythagoreDifficulty.FACILE: settings.PYTHAGORE_BASE_XP_EASY,
    PythagoreDifficulty.MOYEN: settings.PYTHAGORE_BASE_XP_MEDIUM,
    PythagoreDifficulty.DIFFICILE: settings.PYTHAGORE_BASE_XP_HARD,
}


def _challenge_subject_id(db: Session) -> UUID:
    """Récupère (ou crée) la matière « Défis » servant de support à l'XP des mini-jeux.

    Sans parcours ni leçon, elle reste invisible dans la liste des matières de
    l'enfant (filtrée sur les matières ayant du contenu à son niveau).
    """
    subject = db.query(Subject).filter(Subject.slug == CHALLENGE_SUBJECT_SLUG).first()
    if subject is None:
        subject = Subject(
            name="Défis",
            slug=CHALLENGE_SUBJECT_SLUG,
            description="Mini-jeux pour gagner de l'XP",
            icon="🏆",
            is_active=False,
        )
        db.add(subject)
        db.flush()
    return subject.id


def grade_items(
    items: list[PythagoreItem],
    difficulty: PythagoreDifficulty,
) -> tuple[list[PythagoreItemResult], int, int, int]:
    """
    Corrige les réponses côté serveur et calcule le gain d'XP brut.

    Args:
        items: Questions répondues (opérandes + réponse donnée).
        difficulty: Difficulté choisie (détermine le tarif de base).

    Returns:
        ``(results, payout, correct, longest_streak)`` où ``payout`` est l'XP brut
        (avant plafond quotidien), planché à 0.
    """
    base = _BASE_XP[difficulty]
    results: list[PythagoreItemResult] = []
    payout = 0
    streak = 0
    longest_streak = 0
    correct = 0
    for item in items:
        expected = item.a * item.b
        is_correct = item.answer == expected
        results.append(
            PythagoreItemResult(a=item.a, b=item.b, answer=item.answer, expected=expected, correct=is_correct)
        )
        if is_correct:
            correct += 1
            streak += 1
            longest_streak = max(longest_streak, streak)
            payout += base
            if streak >= 3:
                payout += settings.PYTHAGORE_STREAK_BONUS
        else:
            streak = 0
            payout -= settings.PYTHAGORE_FAILURE_PENALTY
    return results, max(0, payout), correct, longest_streak


def _xp_earned_today(user_id: UUID, db: Session) -> int:
    """Somme de l'XP Pythagore déjà attribué à l'utilisateur aujourd'hui."""
    total = (
        db.query(func.sum(PythagoreSession.xp_earned))
        .filter(
            PythagoreSession.user_id == user_id,
            func.date(PythagoreSession.created_at) == date.today(),
        )
        .scalar()
    )
    return int(total or 0)


def run_session(
    user_id: UUID,
    items: list[PythagoreItem],
    difficulty: PythagoreDifficulty,
    db: Session,
) -> dict[str, Any]:
    """
    Corrige une session, applique le plafond quotidien, attribue l'XP et journalise.

    Returns:
        Dictionnaire prêt pour :class:`PythagoreSessionResponse`.
    """
    results, payout, correct, longest_streak = grade_items(items, difficulty)

    remaining = max(0, settings.PYTHAGORE_DAILY_XP_CAP - _xp_earned_today(user_id, db))
    xp_earned = min(payout, remaining)
    capped = xp_earned < payout

    if xp_earned > 0:
        award_xp(user_id, xp_earned, _challenge_subject_id(db), db)

    db.add(
        PythagoreSession(
            user_id=user_id,
            correct=correct,
            total=len(items),
            longest_streak=longest_streak,
            xp_earned=xp_earned,
        )
    )
    db.commit()

    return {
        "correct": correct,
        "total": len(items),
        "longest_streak": longest_streak,
        "xp_earned": xp_earned,
        "capped": capped,
        "balance": get_balance(user_id, db),
        "results": results,
    }
