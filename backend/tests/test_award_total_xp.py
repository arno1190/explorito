"""Les points ⭐ attribués par le parent comptent dans l'XP total (niveau).

Décision produit : une attribution « compétence » (⭐ Points) — p. ex. « a appris
à lacer ses chaussures » — doit gonfler l'XP total affiché et le niveau, au même
titre que l'XP d'exercices. Les points de **comportement** (💚) restent un
porte-monnaie séparé et n'entrent PAS dans l'XP total. Aucun double comptage :
le solde dépensable du porte-monnaie Points reste « gagné − dépensé ».
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import Subject
from app.models.progress import SubjectProgress
from app.models.user import User
from tests.helpers import child_headers, dev_login, make_child

BULBIZARRE = 1  # pokemon, prix 20


def _child_with_xp(db: Session, name: str, xp: int) -> User:
    child = make_child(db, name=name)
    subject = Subject(name="Maths", slug=f"maths-{name}")
    db.add(subject)
    db.flush()
    db.add(SubjectProgress(user_id=child.id, subject_id=subject.id, total_xp=xp))
    db.commit()
    db.refresh(child)
    return child


def _award(client: TestClient, child_id, wallet: str, amount: int, reason: str) -> None:
    r = client.post(
        f"/api/v1/children/{child_id}/awards",
        json={"wallet": wallet, "amount": amount, "reason": reason},
        headers=dev_login(client),
    )
    assert r.status_code == 201, r.text


def test_points_award_raises_total_xp_behavior_does_not(client: TestClient, db_session: Session):
    child = _child_with_xp(db_session, "lacets", 250)
    _award(client, child.id, "points", 10, "Lacets")  # ⭐ compétence
    _award(client, child.id, "behavior", 5, "Bonne action")  # 💚 comportement

    h = child_headers(client, child)
    dash = client.get("/api/v1/progress/me", headers=h).json()
    # 250 (exercices) + 10 (⭐) ; le +5 comportement n'entre pas.
    assert dash["total_xp"] == 260


def test_points_award_flows_to_level(client: TestClient, db_session: Session):
    # 90 XP -> niveau 1 ; +10 ⭐ = 100 XP -> niveau 2 (floor(sqrt(xp/100))+1).
    child = _child_with_xp(db_session, "niveau", 90)
    h = child_headers(client, child)
    assert client.get("/api/v1/progress/me", headers=h).json()["overall_level"] == 1
    _award(client, child.id, "points", 10, "Lacets")
    assert client.get("/api/v1/progress/me", headers=h).json()["overall_level"] == 2


def test_award_not_double_counted_in_wallet(client: TestClient, db_session: Session):
    child = _child_with_xp(db_session, "wallet", 250)
    _award(client, child.id, "points", 10, "Lacets")
    h = child_headers(client, child)
    me = client.get("/api/v1/collection/me", headers=h).json()
    assert me["total_earned"] == 260  # 250 + 10, pas 270
    assert me["balance"] == 260


def test_spending_does_not_lower_total_xp(client: TestClient, db_session: Session):
    child = _child_with_xp(db_session, "spend", 250)
    _award(client, child.id, "points", 10, "Lacets")
    h = child_headers(client, child)
    r = client.post(
        "/api/v1/collection/purchase",
        json={"catalog": "pokemon", "item_id": BULBIZARRE},
        headers=h,
    )
    assert r.status_code == 201, r.text
    price = r.json()["item"]["price"]
    # Le niveau/XP total reste basé sur le gagné, pas le solde.
    assert client.get("/api/v1/progress/me", headers=h).json()["total_xp"] == 260
    me = client.get("/api/v1/collection/me", headers=h).json()
    assert me["total_earned"] == 260
    assert me["balance"] == 260 - price
