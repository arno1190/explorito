"""Tests de la garde partagée (invitations, co-parents, permissions)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.helpers import dev_login


def _uid(db: Session, email: str) -> str:
    return str(db.query(User).filter(User.email == email).first().id)


def _new_child(client: TestClient, headers: dict[str, str], name: str) -> str:
    r = client.post("/api/v1/children", json={"name": name, "level": "ce1"}, headers=headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["is_owner"] is True and body["role"] == "owner"
    return body["id"]


def test_creator_is_owner_and_others_have_no_access(client: TestClient, db_session: Session):
    owner = dev_login(client, "owner1@qa.fr")
    other = dev_login(client, "other1@qa.fr")
    _new_child(client, owner, "Alice")

    assert len(client.get("/api/v1/children", headers=owner).json()) == 1
    assert client.get("/api/v1/children", headers=other).json() == []


def test_share_child_invitation_flow(client: TestClient, db_session: Session):
    owner = dev_login(client, "owner2@qa.fr")
    grandma = dev_login(client, "grandma2@qa.fr")
    alice = _new_child(client, owner, "Alice")

    # Owner crée une invitation pour partager Alice.
    r = client.post("/api/v1/invitations", json={"kind": "child", "child_id": alice}, headers=owner)
    assert r.status_code == 201, r.text
    token = r.json()["token"]

    # Aperçu public (sans auth).
    prev = client.get(f"/api/v1/invitations/{token}").json()
    assert prev["valid"] is True and prev["child_name"] == "Alice"

    # Grand-mère accepte → voit Alice, en tant que responsable non-propriétaire.
    acc = client.post(f"/api/v1/invitations/{token}/accept", headers=grandma)
    assert acc.status_code == 200 and acc.json()["granted"] == 1
    kids = client.get("/api/v1/children", headers=grandma).json()
    assert [k["name"] for k in kids] == ["Alice"]
    assert kids[0]["is_owner"] is False and kids[0]["role"] == "guardian"

    # Elle peut attribuer des points, mais pas supprimer l'enfant.
    assert (
        client.post(
            f"/api/v1/children/{alice}/awards",
            json={"wallet": "points", "amount": 5, "reason": "Lecture"},
            headers=grandma,
        ).status_code
        == 201
    )
    assert client.delete(f"/api/v1/children/{alice}", headers=grandma).status_code == 403

    # Invitation à usage unique : une 2e acceptation échoue.
    other = dev_login(client, "other2@qa.fr")
    assert client.post(f"/api/v1/invitations/{token}/accept", headers=other).status_code == 400


def test_non_owner_cannot_invite(client: TestClient, db_session: Session):
    owner = dev_login(client, "owner3@qa.fr")
    grandma = dev_login(client, "grandma3@qa.fr")
    alice = _new_child(client, owner, "Alice")
    token = client.post("/api/v1/invitations", json={"kind": "child", "child_id": alice}, headers=owner).json()["token"]
    client.post(f"/api/v1/invitations/{token}/accept", headers=grandma)
    # Grand-mère (responsable non-propriétaire) ne peut pas re-partager Alice.
    r = client.post("/api/v1/invitations", json={"kind": "child", "child_id": alice}, headers=grandma)
    assert r.status_code == 403


def test_coparent_gets_current_and_future_children(client: TestClient, db_session: Session):
    owner = dev_login(client, "owner4@qa.fr")
    coparent = dev_login(client, "coparent4@qa.fr")
    _new_child(client, owner, "Alice")

    token = client.post("/api/v1/invitations", json={"kind": "all"}, headers=owner).json()["token"]
    assert client.post(f"/api/v1/invitations/{token}/accept", headers=coparent).json()["granted"] == 1
    assert {k["name"] for k in client.get("/api/v1/children", headers=coparent).json()} == {"Alice"}

    # L'owner ajoute un nouvel enfant → le co-parent le voit automatiquement.
    _new_child(client, owner, "Bob")
    assert {k["name"] for k in client.get("/api/v1/children", headers=coparent).json()} == {"Alice", "Bob"}


def test_leave_and_owner_cannot_be_removed(client: TestClient, db_session: Session):
    owner = dev_login(client, "owner5@qa.fr")
    grandma = dev_login(client, "grandma5@qa.fr")
    alice = _new_child(client, owner, "Alice")
    token = client.post("/api/v1/invitations", json={"kind": "child", "child_id": alice}, headers=owner).json()["token"]
    client.post(f"/api/v1/invitations/{token}/accept", headers=grandma)

    owner_id = _uid(db_session, "owner5@qa.fr")
    grandma_id = _uid(db_session, "grandma5@qa.fr")

    # Le propriétaire ne peut pas être retiré.
    assert client.delete(f"/api/v1/children/{alice}/guardians/{owner_id}", headers=owner).status_code == 400

    # La grand-mère se retire elle-même → n'a plus accès.
    assert client.delete(f"/api/v1/children/{alice}/guardians/{grandma_id}", headers=grandma).status_code == 204
    assert client.get("/api/v1/children", headers=grandma).json() == []

    # L'owner voit la liste des responsables (lui-même en propriétaire).
    guardians = client.get(f"/api/v1/children/{alice}/guardians", headers=owner).json()
    assert any(g["role"] == "owner" and g["is_self"] for g in guardians)
