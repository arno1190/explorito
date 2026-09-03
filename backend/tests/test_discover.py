"""Tests de « Découvrir » (issue #20) : l'enfant demande, il n'obtient jamais.

Deux garde-fous non négociables :

- aucune route enfant n'expose un pack ``draft``, ``pending``, ``rejected`` ou
  ``blocked``, ni les métadonnées de modération d'un pack approuvé ;
- « Je veux ça ! » crée une demande, rien de plus, et le débit est limité.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import LevelEnum
from app.models.pack import ChildPackAccess, CommunityStatus, PackOrigin, PackRequest
from tests.helpers import (
    child_headers,
    dev_login,
    ensure_parent,
    make_child,
    make_exercise,
    make_lesson,
    make_pack,
    make_subject,
)

#: Champs autorisés sur la carte « Découvrir ». Tout ajout doit être un choix
#: conscient : ces métadonnées sont visibles par un enfant de six ans.
CHILD_SAFE_FIELDS = {
    "id",
    "title",
    "emoji",
    "description",
    "subject_icons",
    "lesson_count",
    "families_count",
    "author_handle",
    "requested",
}


def _discover(client: TestClient, headers: dict[str, str]) -> list[dict]:
    r = client.get("/api/v1/discover", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def _community_pack(db: Session, author, title: str, status: CommunityStatus, level: LevelEnum = LevelEnum.CP):
    return make_pack(
        db,
        title=title,
        origin=PackOrigin.COMMUNITY,
        community_status=status,
        level=level,
        author=author,
        handle="Sofia",
    )


def test_discover_only_shows_approved_community_packs_at_level(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "d_author@qa.fr")
    approved = _community_pack(db_session, author, "Dinos", CommunityStatus.APPROVED)
    hidden = {
        status.value: _community_pack(db_session, author, f"Caché {status.value}", status)
        for status in (
            CommunityStatus.DRAFT,
            CommunityStatus.PENDING,
            CommunityStatus.REJECTED,
            CommunityStatus.BLOCKED,
        )
    }
    wrong_level = _community_pack(db_session, author, "CM2", CommunityStatus.APPROVED, level=LevelEnum.CM2)
    official = make_pack(db_session, title="Officiel")
    child = make_child(db_session, parent_email="d_parent@qa.fr", level=LevelEnum.CP)
    db_session.commit()

    rows = _discover(client, child_headers(client, child, parent_email="d_parent@qa.fr"))
    ids = {row["id"] for row in rows}
    assert ids == {str(approved.id)}
    for pack in hidden.values():
        assert str(pack.id) not in ids
    assert str(wrong_level.id) not in ids
    # Les packs officiels sont déjà là, implicitement : rien à découvrir.
    assert str(official.id) not in ids


def test_discover_exposes_only_child_safe_metadata(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "meta_author@qa.fr")
    maths = make_subject(db_session)
    pack = _community_pack(db_session, author, "Additions", CommunityStatus.APPROVED)
    pack.quality_score = 42
    pack.review_notes = "Note interne de modération"
    lesson = make_lesson(db_session, pack=pack, subject=maths)
    make_exercise(db_session, lesson=lesson)
    child = make_child(db_session, parent_email="meta_parent@qa.fr")
    db_session.commit()

    rows = _discover(client, child_headers(client, child, parent_email="meta_parent@qa.fr"))
    assert len(rows) == 1
    card = rows[0]
    assert set(card) == CHILD_SAFE_FIELDS
    assert card["title"] == "Additions"
    assert card["author_handle"] == "Sofia"
    assert card["subject_icons"] == [maths.icon]
    assert card["lesson_count"] == 1
    assert card["families_count"] == 0
    assert card["requested"] is False


def test_discover_hides_already_accessible_packs(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "hide_author@qa.fr")
    pack = _community_pack(db_session, author, "Dinos", CommunityStatus.APPROVED)
    child = make_child(db_session, parent_email="hide_parent@qa.fr")
    db_session.commit()

    child_head = child_headers(client, child, parent_email="hide_parent@qa.fr")
    assert len(_discover(client, child_head)) == 1

    assert (
        client.put(
            f"/api/v1/library/children/{child.id}/access/{pack.id}",
            json={"enabled": True},
            headers=dev_login(client, "hide_parent@qa.fr"),
        ).status_code
        == 200
    )
    assert _discover(client, child_head) == []


def test_discover_requires_an_acting_child(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "solo_author@qa.fr")
    _community_pack(db_session, author, "Dinos", CommunityStatus.APPROVED)
    db_session.commit()

    # Parent sans X-Acting-Child-Id : pas de niveau, donc pas de catalogue enfant.
    assert client.get("/api/v1/discover", headers=dev_login(client, "solo@qa.fr")).status_code == 400


def test_request_creates_a_pending_row_and_grants_nothing(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "req_author@qa.fr")
    pack = _community_pack(db_session, author, "Dinos", CommunityStatus.APPROVED)
    make_lesson(db_session, pack=pack, name="Le tyrannosaure")
    child = make_child(db_session, parent_email="req_parent@qa.fr")
    db_session.commit()

    child_head = child_headers(client, child, parent_email="req_parent@qa.fr")
    r = client.post("/api/v1/discover/requests", json={"pack_id": str(pack.id)}, headers=child_head)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "pending" and body["pack_title"] == "Dinos"

    assert db_session.query(ChildPackAccess).count() == 0
    assert client.get("/api/v1/lessons/recent", headers=child_head).json() == []

    mine = client.get("/api/v1/discover/requests", headers=child_head).json()
    assert [row["id"] for row in mine] == [body["id"]]
    assert _discover(client, child_head)[0]["requested"] is True


def test_duplicate_request_does_not_burn_quota(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "dup_author@qa.fr")
    pack = _community_pack(db_session, author, "Dinos", CommunityStatus.APPROVED)
    child = make_child(db_session, parent_email="dup_parent@qa.fr")
    db_session.commit()

    child_head = child_headers(client, child, parent_email="dup_parent@qa.fr")
    first = client.post("/api/v1/discover/requests", json={"pack_id": str(pack.id)}, headers=child_head)
    second = client.post("/api/v1/discover/requests", json={"pack_id": str(pack.id)}, headers=child_head)
    assert first.json()["id"] == second.json()["id"]
    assert db_session.query(PackRequest).count() == 1


def test_requests_are_rate_limited_per_child(client: TestClient, db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "PACK_MAX_REQUESTS_PER_CHILD_PER_DAY", 2)
    author = ensure_parent(db_session, "rate_author@qa.fr")
    packs = [_community_pack(db_session, author, f"Pack {i}", CommunityStatus.APPROVED) for i in range(3)]
    child = make_child(db_session, parent_email="rate_parent@qa.fr", name="Un")
    other = make_child(db_session, parent_email="rate_parent@qa.fr", name="Deux")
    db_session.commit()

    child_head = child_headers(client, child, parent_email="rate_parent@qa.fr")
    for pack in packs[:2]:
        assert (
            client.post("/api/v1/discover/requests", json={"pack_id": str(pack.id)}, headers=child_head).status_code
            == 201
        )
    third = client.post("/api/v1/discover/requests", json={"pack_id": str(packs[2].id)}, headers=child_head)
    assert third.status_code == 429, third.text

    # Le quota est par enfant : le frère ou la sœur n'est pas puni.
    other_head = child_headers(client, other, parent_email="rate_parent@qa.fr")
    assert (
        client.post("/api/v1/discover/requests", json={"pack_id": str(packs[2].id)}, headers=other_head).status_code
        == 201
    )


def test_request_on_a_non_approved_pack_is_rejected(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "bad_author@qa.fr")
    draft = _community_pack(db_session, author, "Brouillon", CommunityStatus.DRAFT)
    blocked = _community_pack(db_session, author, "Bloqué", CommunityStatus.BLOCKED)
    official = make_pack(db_session, title="Officiel")
    child = make_child(db_session, parent_email="bad_parent@qa.fr")
    db_session.commit()

    child_head = child_headers(client, child, parent_email="bad_parent@qa.fr")
    for pack in (draft, blocked, official):
        r = client.post("/api/v1/discover/requests", json={"pack_id": str(pack.id)}, headers=child_head)
        assert r.status_code == 404, (pack.title, r.text)
    assert db_session.query(PackRequest).count() == 0
