"""
Tests du défi Pythagore standalone (issue #5).

Correction et XP calculés côté serveur : tarif de base par difficulté, bonus de
série, pénalité d'erreur, plafond quotidien anti-farm. L'XP alimente le
porte-monnaie dépensable (Pokédex).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import LevelEnum
from app.models.user import User
from tests.helpers import child_headers, make_child

_children: dict[str, User] = {}


def _make_child(db: Session, email: str) -> User:
    child = make_child(db, level=LevelEnum.CE1, name=email.split("@")[0])
    _children[email] = child
    return child


def _auth(client: TestClient, email: str) -> dict[str, str]:
    return child_headers(client, _children[email])


def _session(client: TestClient, h: dict[str, str], difficulty: str, items: list[tuple[int, int, int]]) -> dict:
    payload = {"difficulty": difficulty, "items": [{"a": a, "b": b, "answer": ans} for a, b, ans in items]}
    r = client.post("/api/v1/pythagore/session", json=payload, headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def test_perfect_session_awards_base_plus_streak(client: TestClient, db_session: Session):
    _make_child(db_session, "a@x.fr")
    h = _auth(client, "a@x.fr")
    # 3 bonnes réponses d'affilée en « moyen » : 3*3 + 1 bonus de série = 10.
    body = _session(client, h, "moyen", [(2, 3, 6), (4, 5, 20), (6, 7, 42)])
    base = settings.PYTHAGORE_BASE_XP_MEDIUM
    assert body["correct"] == 3
    assert body["total"] == 3
    assert body["longest_streak"] == 3
    assert body["xp_earned"] == base * 3 + settings.PYTHAGORE_STREAK_BONUS
    assert body["capped"] is False
    # L'XP alimente le solde dépensable.
    assert body["balance"] == body["xp_earned"]


def test_failure_penalty_and_server_grading(client: TestClient, db_session: Session):
    _make_child(db_session, "b@x.fr")
    h = _auth(client, "b@x.fr")
    # correct, faux (réponse client fausse), correct -> pas de confiance au client.
    body = _session(client, h, "moyen", [(2, 3, 6), (4, 5, 99), (6, 7, 42)])
    base = settings.PYTHAGORE_BASE_XP_MEDIUM
    assert body["correct"] == 2
    assert body["longest_streak"] == 1
    # 3 (correct) - 1 (pénalité) + 3 (correct) = 5
    assert body["xp_earned"] == base * 2 - settings.PYTHAGORE_FAILURE_PENALTY
    # Le serveur recalcule la réponse attendue (a*b), indépendamment du client.
    wrong = next(r for r in body["results"] if not r["correct"])
    assert wrong["expected"] == wrong["a"] * wrong["b"]


def test_all_wrong_floors_at_zero(client: TestClient, db_session: Session):
    _make_child(db_session, "c@x.fr")
    h = _auth(client, "c@x.fr")
    body = _session(client, h, "facile", [(2, 3, 0), (4, 5, 0)])
    assert body["correct"] == 0
    assert body["xp_earned"] == 0  # planché à 0, jamais négatif


def test_daily_cap_limits_farming(client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "PYTHAGORE_DAILY_XP_CAP", 5)
    _make_child(db_session, "d@x.fr")
    h = _auth(client, "d@x.fr")

    first = _session(client, h, "moyen", [(2, 3, 6), (4, 5, 20), (6, 7, 42)])
    assert first["xp_earned"] == 5  # payout 10 plafonné à 5
    assert first["capped"] is True

    # Deuxième session le même jour : plafond déjà atteint -> 0.
    second = _session(client, h, "moyen", [(2, 3, 6), (4, 5, 20), (6, 7, 42)])
    assert second["xp_earned"] == 0
    assert second["capped"] is True
    assert second["balance"] == 5
