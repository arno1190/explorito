"""
Tests des collections (multi-catalogue) : porte-monnaie XP partagé, achats
(validité, doublon, solde), grille avec état de possession, et partage du
solde entre catalogues (pokemon, dinosaures).
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import Subject
from app.models.progress import SubjectProgress
from app.models.user import User
from tests.helpers import child_headers, make_child

BULBIZARRE = 1  # pokemon, prix 20
MEWTWO = 150  # pokemon, prix 200
TYRANNO = 1  # dinosaurs, prix 20

# Registre email -> enfant, pour conserver la signature _auth(client, email).
_children: dict[str, User] = {}


def _make_child_with_xp(db: Session, email: str, xp: int) -> User:
    child = make_child(db, name=email.split("@")[0])
    subject = Subject(name="Maths", slug=f"maths-{email}")
    db.add(subject)
    db.flush()
    db.add(SubjectProgress(user_id=child.id, subject_id=subject.id, total_xp=xp))
    db.commit()
    db.refresh(child)
    _children[email] = child
    return child


def _auth(client: TestClient, email: str) -> dict[str, str]:
    return child_headers(client, _children[email])


def _buy(client: TestClient, h: dict[str, str], catalog: str, item_id: int):
    return client.post("/api/v1/collection/purchase", json={"catalog": catalog, "item_id": item_id}, headers=h)


def test_wallet_starts_full_with_catalogs(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c1@x.fr", 250)
    h = _auth(client, "c1@x.fr")
    body = client.get("/api/v1/collection/me", headers=h).json()
    assert body["total_earned"] == 250
    assert body["spent"] == 0
    assert body["balance"] == 250
    by_slug = {c["slug"]: c for c in body["catalogs"]}
    assert by_slug["pokemon"]["total"] == 251
    assert by_slug["pokemon"]["unlocked"] == 0
    assert by_slug["dinosaurs"]["total"] == 40
    assert by_slug["solar_system"]["total"] == 17


def test_purchase_deducts_and_adds(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c2@x.fr", 250)
    h = _auth(client, "c2@x.fr")
    r = _buy(client, h, "pokemon", BULBIZARRE)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["item"]["name_fr"] == "Bulbizarre"
    assert body["catalog"] == "pokemon"
    assert body["balance"] == 250 - body["item"]["price"]
    assert body["unlocked_count"] == 1

    me = client.get("/api/v1/collection/me", headers=h).json()
    assert me["spent"] == body["item"]["price"]
    assert {c["slug"]: c["unlocked"] for c in me["catalogs"]}["pokemon"] == 1


def test_shared_wallet_across_catalogs(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c3@x.fr", 250)
    h = _auth(client, "c3@x.fr")
    assert _buy(client, h, "pokemon", BULBIZARRE).status_code == 201  # 20
    assert _buy(client, h, "dinosaurs", TYRANNO).status_code == 201  # 20
    me = client.get("/api/v1/collection/me", headers=h).json()
    assert me["spent"] == 40  # le solde est partagé entre catalogues
    assert me["balance"] == 210
    counts = {c["slug"]: c["unlocked"] for c in me["catalogs"]}
    assert counts["pokemon"] == 1
    assert counts["dinosaurs"] == 1


def test_cannot_buy_duplicate(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c4@x.fr", 250)
    h = _auth(client, "c4@x.fr")
    assert _buy(client, h, "pokemon", BULBIZARRE).status_code == 201
    assert _buy(client, h, "pokemon", BULBIZARRE).status_code == 409


def test_same_id_different_catalog_is_allowed(client: TestClient, db_session: Session):
    # id=1 existe dans pokemon ET dinosaurs : ce ne sont pas des doublons.
    _make_child_with_xp(db_session, "c5@x.fr", 250)
    h = _auth(client, "c5@x.fr")
    assert _buy(client, h, "pokemon", 1).status_code == 201
    assert _buy(client, h, "dinosaurs", 1).status_code == 201


def test_insufficient_balance(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c6@x.fr", 15)
    h = _auth(client, "c6@x.fr")
    assert _buy(client, h, "pokemon", BULBIZARRE).status_code == 400  # prix 20 > 15


def test_unknown_item_and_catalog(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c7@x.fr", 500)
    h = _auth(client, "c7@x.fr")
    assert _buy(client, h, "pokemon", 99999).status_code == 404
    assert _buy(client, h, "licornes", 1).status_code == 404


def test_balance_never_negative_blocks_next(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c8@x.fr", 200)
    h = _auth(client, "c8@x.fr")
    r = _buy(client, h, "pokemon", MEWTWO)
    assert r.status_code == 201, r.text
    assert r.json()["balance"] == 0
    assert _buy(client, h, "pokemon", BULBIZARRE).status_code == 400


def test_catalog_grid_marks_owned(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c9@x.fr", 250)
    h = _auth(client, "c9@x.fr")
    _buy(client, h, "pokemon", BULBIZARRE)
    grid = client.get("/api/v1/collection/catalogs/pokemon", headers=h).json()
    assert len(grid) == 251
    by_id = {e["id"]: e for e in grid}
    assert by_id[BULBIZARRE]["owned"] is True
    assert by_id[MEWTWO]["owned"] is False


def test_dinosaur_grid_has_facts(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c10@x.fr", 100)
    h = _auth(client, "c10@x.fr")
    grid = client.get("/api/v1/collection/catalogs/dinosaurs", headers=h).json()
    assert len(grid) == 40
    assert grid[0]["fact"]  # contenu éducatif présent


def test_unknown_catalog_grid_404(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c11@x.fr", 100)
    h = _auth(client, "c11@x.fr")
    assert client.get("/api/v1/collection/catalogs/zzz", headers=h).status_code == 404
