"""
Tests de la collection Pokémon : porte-monnaie XP dérivé, achat (validité,
doublon, solde), et lecture de la collection / du catalogue.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.content import Subject
from app.models.progress import SubjectProgress
from app.models.user import Profile, User, UserRole

BULBIZARRE = 1  # prix 20
MEWTWO = 150  # prix 200


def _make_child_with_xp(db: Session, email: str, xp: int) -> User:
    user = User(
        email=email,
        password_hash=get_password_hash("SecurePass123"),
        role=UserRole.CHILD,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, display_name=email.split("@")[0], is_child=True))
    subject = Subject(name="Maths", slug=f"maths-{email}")
    db.add(subject)
    db.flush()
    db.add(SubjectProgress(user_id=user.id, subject_id=subject.id, total_xp=xp))
    db.commit()
    db.refresh(user)
    return user


def _auth(client: TestClient, email: str) -> dict[str, str]:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass123"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_collection_starts_empty_with_full_balance(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c1@x.fr", 250)
    h = _auth(client, "c1@x.fr")
    r = client.get("/api/v1/collection/me", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_earned"] == 250
    assert body["spent"] == 0
    assert body["balance"] == 250
    assert body["unlocked_count"] == 0
    assert body["total_count"] == 251
    assert body["collection"] == []


def test_purchase_deducts_and_adds_to_collection(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c2@x.fr", 250)
    h = _auth(client, "c2@x.fr")
    r = client.post("/api/v1/collection/purchase", json={"pokemon_id": BULBIZARRE}, headers=h)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["pokemon"]["name_fr"] == "Bulbizarre"
    assert body["balance"] == 250 - body["pokemon"]["price"]
    assert body["unlocked_count"] == 1

    me = client.get("/api/v1/collection/me", headers=h).json()
    assert me["spent"] == body["pokemon"]["price"]
    assert [p["id"] for p in me["collection"]] == [BULBIZARRE]


def test_cannot_buy_duplicate(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c3@x.fr", 250)
    h = _auth(client, "c3@x.fr")
    assert client.post("/api/v1/collection/purchase", json={"pokemon_id": BULBIZARRE}, headers=h).status_code == 201
    dup = client.post("/api/v1/collection/purchase", json={"pokemon_id": BULBIZARRE}, headers=h)
    assert dup.status_code == 409, dup.text


def test_insufficient_balance(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c4@x.fr", 15)
    h = _auth(client, "c4@x.fr")
    r = client.post("/api/v1/collection/purchase", json={"pokemon_id": BULBIZARRE}, headers=h)
    assert r.status_code == 400, r.text  # prix 20 > solde 15


def test_unknown_pokemon(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c5@x.fr", 500)
    h = _auth(client, "c5@x.fr")
    r = client.post("/api/v1/collection/purchase", json={"pokemon_id": 99999}, headers=h)
    assert r.status_code == 404, r.text


def test_balance_never_goes_negative_and_blocks_next(client: TestClient, db_session: Session):
    # 200 XP : peut acheter Mewtwo (200) puis plus rien.
    _make_child_with_xp(db_session, "c6@x.fr", 200)
    h = _auth(client, "c6@x.fr")
    r = client.post("/api/v1/collection/purchase", json={"pokemon_id": MEWTWO}, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["balance"] == 0
    # plus assez pour Bulbizarre (20)
    r2 = client.post("/api/v1/collection/purchase", json={"pokemon_id": BULBIZARRE}, headers=h)
    assert r2.status_code == 400, r2.text


def test_pokedex_grid_marks_owned(client: TestClient, db_session: Session):
    _make_child_with_xp(db_session, "c7@x.fr", 250)
    h = _auth(client, "c7@x.fr")
    client.post("/api/v1/collection/purchase", json={"pokemon_id": BULBIZARRE}, headers=h)
    grid = client.get("/api/v1/collection/pokedex", headers=h).json()
    assert len(grid) == 251
    by_id = {e["id"]: e for e in grid}
    assert by_id[BULBIZARRE]["owned"] is True
    assert by_id[MEWTWO]["owned"] is False
    assert by_id[MEWTWO]["price"] == 200
