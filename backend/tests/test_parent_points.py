"""
Points attribués par le parent : deux porte-monnaies (Points / Comportement),
attribution/retrait, et achat de collectibles avec le porte-monnaie choisi.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import child_headers, dev_login, make_child

BULBIZARRE = 1  # pokemon, prix 20
TYRANNO = 1  # dinosaurs, prix 20


def _wallet(client: TestClient, child) -> dict:
    return client.get("/api/v1/collection/me", headers=child_headers(client, child)).json()


def _award(client: TestClient, child, wallet: str, amount: int, reason: str = "") -> "object":
    return client.post(
        f"/api/v1/children/{child.id}/awards",
        json={"wallet": wallet, "amount": amount, "reason": reason},
        headers=dev_login(client),
    )


def test_hardskill_award_tops_up_points_wallet(client: TestClient, db_session: Session):
    child = make_child(db_session)
    assert _award(client, child, "points", 30, "dictée").status_code == 201
    w = _wallet(client, child)
    assert w["total_earned"] == 30
    assert w["balance"] == 30
    assert w["behavior_balance"] == 0  # séparé


def test_points_award_cannot_be_negative(client: TestClient, db_session: Session):
    child = make_child(db_session)
    assert _award(client, child, "points", -5).status_code == 400


def test_zero_amount_rejected(client: TestClient, db_session: Session):
    child = make_child(db_session)
    assert _award(client, child, "behavior", 0).status_code == 400


def test_behavior_net_and_floored(client: TestClient, db_session: Session):
    child = make_child(db_session)
    assert _award(client, child, "behavior", 15, "bonne action").status_code == 201
    assert _award(client, child, "behavior", -5, "dispute").status_code == 201
    w = _wallet(client, child)
    assert w["behavior_balance"] == 10  # 15 - 5
    # gros retrait -> plancher à 0 (pas de solde négatif affiché)
    assert _award(client, child, "behavior", -100).status_code == 201
    assert _wallet(client, child)["behavior_balance"] == 0


def test_purchase_with_each_wallet(client: TestClient, db_session: Session):
    child = make_child(db_session)
    h = child_headers(client, child)
    _award(client, child, "points", 25)
    _award(client, child, "behavior", 25)

    # Achat en Points.
    r1 = client.post(
        "/api/v1/collection/purchase",
        json={"catalog": "pokemon", "item_id": BULBIZARRE, "currency": "points"},
        headers=h,
    )
    assert r1.status_code == 201, r1.text
    # Achat en Comportement (autre catalogue).
    r2 = client.post(
        "/api/v1/collection/purchase",
        json={"catalog": "dinosaurs", "item_id": TYRANNO, "currency": "behavior"},
        headers=h,
    )
    assert r2.status_code == 201, r2.text

    w = _wallet(client, child)
    assert w["balance"] == 5  # 25 - 20 (points)
    assert w["behavior_balance"] == 5  # 25 - 20 (comportement)


def test_purchase_insufficient_in_chosen_wallet(client: TestClient, db_session: Session):
    child = make_child(db_session)
    h = child_headers(client, child)
    _award(client, child, "points", 100)  # plein de Points, zéro Comportement
    r = client.post(
        "/api/v1/collection/purchase",
        json={"catalog": "pokemon", "item_id": BULBIZARRE, "currency": "behavior"},
        headers=h,
    )
    assert r.status_code == 400  # solde Comportement insuffisant malgré des Points


def test_award_requires_ownership(client: TestClient, db_session: Session):
    child = make_child(db_session)  # possédé par parent@qa.fr
    stranger = dev_login(client, "stranger@qa.fr")
    r = client.post(
        f"/api/v1/children/{child.id}/awards",
        json={"wallet": "points", "amount": 10},
        headers=stranger,
    )
    assert r.status_code in (403, 404)


def test_unseen_awards_and_ack(client: TestClient, db_session: Session):
    child = make_child(db_session)
    h = child_headers(client, child)
    _award(client, child, "points", 10, "dictée")
    _award(client, child, "behavior", 5, "aide")

    unseen = client.get("/api/v1/collection/awards/unseen", headers=h).json()
    assert len(unseen) == 2
    assert {a["reason"] for a in unseen} == {"dictée", "aide"}

    assert client.post("/api/v1/collection/awards/ack", headers=h).status_code == 204
    assert client.get("/api/v1/collection/awards/unseen", headers=h).json() == []


def test_history_visible_to_parent(client: TestClient, db_session: Session):
    child = make_child(db_session)
    _award(client, child, "points", 10, "dictée")
    hist = client.get(f"/api/v1/children/{child.id}/awards", headers=dev_login(client)).json()
    assert len(hist) == 1
    assert hist[0]["reason"] == "dictée"
    assert hist[0]["wallet"] == "points"
    assert hist[0]["amount"] == 10
