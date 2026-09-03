"""Tests de la bibliothèque parent (issue #18) : catalogue, opt-in, audit.

Ces tests défendent le cœur du modèle de confiance :

- les packs ``official`` restent visibles **sans aucune action parentale** ;
- un pack communautaire n'atteint un enfant que par une ligne d'accès explicite
  (ou l'interrupteur d'auto-activation) ;
- désactiver masque et ne détruit rien ;
- chaque bascule nomme le garde qui l'a faite.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import LevelEnum
from app.models.contribution import PackAuditLog, PackReport
from app.models.guardianship import ROLE_GUARDIAN
from app.models.pack import ChildPackAccess, CommunityStatus, PackOrigin
from app.models.progress import ProgressStatus, UserProgress
from app.models.user import Profile
from app.services.guardianship import grant
from app.services.packs import accessible_pack_ids
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


def _catalogue_ids(client: TestClient, headers: dict[str, str], **params) -> list[str]:
    r = client.get("/api/v1/library/catalogue", headers=headers, params=params)
    assert r.status_code == 200, r.text
    return [row["id"] for row in r.json()]


def _set_access(
    client: TestClient,
    headers: dict[str, str],
    child_id: str,
    pack_id: str,
    enabled: bool,
) -> dict:
    r = client.put(
        f"/api/v1/library/children/{child_id}/access/{pack_id}",
        json={"enabled": enabled},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


# --------------------------------------------------------------------------- #
# Catalogue
# --------------------------------------------------------------------------- #
def test_catalogue_lists_official_and_approved_only(client: TestClient, db_session: Session):
    official = make_pack(db_session, title="Officiel CP")
    approved = make_pack(
        db_session,
        title="Dinos",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        handle="Sofia",
    )
    hidden = [
        make_pack(db_session, title=t, origin=PackOrigin.COMMUNITY, community_status=s)
        for t, s in (
            ("Brouillon", CommunityStatus.DRAFT),
            ("En attente", CommunityStatus.PENDING),
            ("Refusé", CommunityStatus.REJECTED),
            ("Bloqué", CommunityStatus.BLOCKED),
        )
    ]
    blocked_official = make_pack(db_session, title="Officiel retiré", community_status=CommunityStatus.BLOCKED)
    db_session.commit()

    headers = dev_login(client, "lib1@qa.fr")
    ids = _catalogue_ids(client, headers)

    assert str(official.id) in ids
    assert str(approved.id) in ids
    assert str(blocked_official.id) not in ids
    for pack in hidden:
        assert str(pack.id) not in ids

    rows = client.get("/api/v1/library/catalogue", headers=headers).json()
    by_id = {row["id"]: row for row in rows}
    assert by_id[str(official.id)]["origin"] == "official"
    assert by_id[str(approved.id)]["origin"] == "community"
    assert by_id[str(approved.id)]["author_handle"] == "Sofia"


def test_catalogue_counts_content_and_families(client: TestClient, db_session: Session):
    maths = make_subject(db_session)
    pack = make_pack(
        db_session,
        title="Additions",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    lesson = make_lesson(db_session, pack=pack, subject=maths, name="Additions 1")
    make_exercise(db_session, lesson=lesson, order_index=0)
    make_exercise(db_session, lesson=lesson, order_index=1)
    make_lesson(db_session, pack=pack, subject=maths, tier=2, name="Additions 2")
    kid_a = make_child(db_session, parent_email="fam_a@qa.fr", name="A")
    kid_b = make_child(db_session, parent_email="fam_b@qa.fr", name="B")
    db_session.commit()

    _set_access(client, dev_login(client, "fam_a@qa.fr"), str(kid_a.id), str(pack.id), True)
    _set_access(client, dev_login(client, "fam_b@qa.fr"), str(kid_b.id), str(pack.id), True)

    rows = client.get("/api/v1/library/catalogue", headers=dev_login(client, "lib2@qa.fr")).json()
    card = next(row for row in rows if row["id"] == str(pack.id))
    assert card["lesson_count"] == 2
    assert card["exercise_count"] == 2
    assert card["families_count"] == 2
    assert card["subject_icons"] == [maths.icon]


def test_catalogue_filters_by_level_subject_and_tag(client: TestClient, db_session: Session):
    maths = make_subject(db_session)
    francais = make_subject(db_session, slug="francais", name="Français", icon="📚")

    cp_maths = make_pack(
        db_session,
        title="Maths CP",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    make_lesson(db_session, pack=cp_maths, subject=maths)
    cp_maths.tags = ["dinosaures"]

    ce1_francais = make_pack(
        db_session,
        title="Français CE1",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        level=LevelEnum.CE1,
    )
    make_lesson(db_session, pack=ce1_francais, subject=francais, level=LevelEnum.CE1)
    ce1_francais.tags = ["espace"]
    db_session.commit()

    headers = dev_login(client, "lib3@qa.fr")

    assert _catalogue_ids(client, headers, level="cp") == [str(cp_maths.id)]
    assert _catalogue_ids(client, headers, level="ce1") == [str(ce1_francais.id)]
    assert _catalogue_ids(client, headers, subject="francais") == [str(ce1_francais.id)]
    assert _catalogue_ids(client, headers, tag="dinosaures") == [str(cp_maths.id)]
    assert _catalogue_ids(client, headers, tag="inconnu") == []


def test_catalogue_sorts_by_most_enabled(client: TestClient, db_session: Session):
    quiet = make_pack(
        db_session,
        title="Aaa calme",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    popular = make_pack(
        db_session,
        title="Zzz populaire",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    kid_a = make_child(db_session, parent_email="pop_a@qa.fr", name="A")
    kid_b = make_child(db_session, parent_email="pop_b@qa.fr", name="B")
    db_session.commit()

    head_a = dev_login(client, "pop_a@qa.fr")
    head_b = dev_login(client, "pop_b@qa.fr")
    _set_access(client, head_a, str(kid_a.id), str(popular.id), True)
    _set_access(client, head_b, str(kid_b.id), str(popular.id), True)
    _set_access(client, head_a, str(kid_a.id), str(quiet.id), True)

    ids = _catalogue_ids(client, dev_login(client, "lib4@qa.fr"), sort="most_enabled")
    assert ids.index(str(popular.id)) < ids.index(str(quiet.id))


def test_parent_previews_full_content_before_enabling(client: TestClient, db_session: Session):
    pack = make_pack(
        db_session,
        title="Volcans",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    lesson = make_lesson(db_session, pack=pack, name="Le magma")
    make_exercise(db_session, lesson=lesson, question="Le magma est-il chaud ?")
    db_session.commit()

    headers = dev_login(client, "preview@qa.fr")
    r = client.get(f"/api/v1/library/packs/{pack.id}", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    # Aucun accès n'a été accordé : l'aperçu doit malgré tout être complet.
    assert db_session.query(ChildPackAccess).count() == 0
    assert [lesson["name"] for lesson in body["lessons"]] == ["Le magma"]
    assert [ex["question"] for ex in body["lessons"][0]["exercises"]] == ["Le magma est-il chaud ?"]

    draft = make_pack(db_session, origin=PackOrigin.COMMUNITY, community_status=CommunityStatus.DRAFT)
    db_session.commit()
    assert client.get(f"/api/v1/library/packs/{draft.id}", headers=headers).status_code == 404


# --------------------------------------------------------------------------- #
# Opt-in : officiel implicite, communautaire explicite
# --------------------------------------------------------------------------- #
def test_official_pack_reaches_child_without_any_access_row(client: TestClient, db_session: Session):
    official = make_pack(db_session, title="Officiel maths CP")
    make_lesson(db_session, pack=official, name="Compter jusqu'à 10")
    child = make_child(db_session, parent_email="implicit@qa.fr")
    db_session.commit()

    assert db_session.query(ChildPackAccess).count() == 0
    assert official.id in (accessible_pack_ids(child.id, LevelEnum.CP, db_session) or set())

    recent = client.get("/api/v1/lessons/recent", headers=child_headers(client, child, parent_email="implicit@qa.fr"))
    assert recent.status_code == 200, recent.text
    assert [row["name"] for row in recent.json()] == ["Compter jusqu'à 10"]

    # La bibliothèque ne liste aucune ligne d'accès : rien à activer côté parent.
    state = client.get(
        f"/api/v1/library/children/{child.id}/access",
        headers=dev_login(client, "implicit@qa.fr"),
    ).json()
    assert state["entries"] == []
    assert state["auto_enable_approved_packs"] is False


def test_community_pack_needs_explicit_access_row(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "author_a@qa.fr")
    pack = make_pack(
        db_session,
        title="Dinos",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
    )
    make_lesson(db_session, pack=pack, name="Le tyrannosaure")
    child = make_child(db_session, parent_email="optin@qa.fr")
    db_session.commit()

    child_head = child_headers(client, child, parent_email="optin@qa.fr")
    assert client.get("/api/v1/lessons/recent", headers=child_head).json() == []

    parent_head = dev_login(client, "optin@qa.fr")
    _set_access(client, parent_head, str(child.id), str(pack.id), True)
    assert [row["name"] for row in client.get("/api/v1/lessons/recent", headers=child_head).json()] == [
        "Le tyrannosaure"
    ]

    _set_access(client, parent_head, str(child.id), str(pack.id), False)
    assert client.get("/api/v1/lessons/recent", headers=child_head).json() == []


def test_auto_enable_defaults_off_and_is_per_child(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "author_b@qa.fr")
    pack = make_pack(
        db_session,
        title="Espace",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
    )
    make_lesson(db_session, pack=pack, name="Les planètes")
    first = make_child(db_session, parent_email="auto@qa.fr", name="Un")
    second = make_child(db_session, parent_email="auto@qa.fr", name="Deux")
    db_session.commit()

    for child in (first, second):
        profile = db_session.query(Profile).filter(Profile.user_id == child.id).first()
        assert profile.auto_enable_approved_packs is False

    parent_head = dev_login(client, "auto@qa.fr")
    r = client.put(
        f"/api/v1/library/children/{first.id}/auto-enable",
        json={"enabled": True},
        headers=parent_head,
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"child_id": str(first.id), "enabled": True}

    # Le robinet est ouvert pour le premier enfant seulement, et sans ligne d'accès.
    assert db_session.query(ChildPackAccess).count() == 0
    head_first = child_headers(client, first, parent_email="auto@qa.fr")
    head_second = child_headers(client, second, parent_email="auto@qa.fr")
    assert [row["name"] for row in client.get("/api/v1/lessons/recent", headers=head_first).json()] == ["Les planètes"]
    assert client.get("/api/v1/lessons/recent", headers=head_second).json() == []


def test_explicit_disable_vetoes_auto_enable(client: TestClient, db_session: Session):
    """Couper un pack précis doit tenir, même robinet grand ouvert.

    Régression : l'auto-activation réunissait tous les packs approuvés du niveau
    *après* la liste blanche, si bien qu'une ligne ``enabled = False`` était
    réécrasée au tour suivant. Un parent n'avait alors plus qu'un choix binaire :
    tout accepter, ou couper l'interrupteur entier.
    """
    author = ensure_parent(db_session, "author_veto@qa.fr")
    keep = make_pack(
        db_session,
        title="Les étoiles",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
    )
    make_lesson(db_session, pack=keep, name="La Grande Ourse")
    drop = make_pack(
        db_session,
        title="Les insectes",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
    )
    make_lesson(db_session, pack=drop, name="La fourmi")
    child = make_child(db_session, parent_email="veto@qa.fr", name="Véto")
    db_session.commit()

    parent_head = dev_login(client, "veto@qa.fr")
    assert (
        client.put(
            f"/api/v1/library/children/{child.id}/auto-enable",
            json={"enabled": True},
            headers=parent_head,
        ).status_code
        == 200
    )
    child_head = child_headers(client, child, parent_email="veto@qa.fr")
    assert sorted(row["name"] for row in client.get("/api/v1/lessons/recent", headers=child_head).json()) == [
        "La Grande Ourse",
        "La fourmi",
    ]

    refused = client.put(
        f"/api/v1/library/children/{child.id}/access/{drop.id}",
        json={"enabled": False},
        headers=parent_head,
    )
    assert refused.status_code == 200, refused.text

    # Le pack coupé disparaît ; l'autre reste, donc le robinet est toujours ouvert.
    assert [row["name"] for row in client.get("/api/v1/lessons/recent", headers=child_head).json()] == [
        "La Grande Ourse"
    ]


def test_disabling_preserves_all_progress(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "author_c@qa.fr")
    pack = make_pack(
        db_session,
        title="Volcans",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
    )
    lesson = make_lesson(db_session, pack=pack, name="Le magma")
    child = make_child(db_session, parent_email="keep@qa.fr")
    db_session.add(
        UserProgress(
            user_id=child.id,
            lesson_id=lesson.id,
            status=ProgressStatus.COMPLETED,
            score=90,
            stars=3,
            attempts=2,
        )
    )
    db_session.commit()

    parent_head = dev_login(client, "keep@qa.fr")
    _set_access(client, parent_head, str(child.id), str(pack.id), True)
    _set_access(client, parent_head, str(child.id), str(pack.id), False)

    progress = db_session.query(UserProgress).filter(UserProgress.user_id == child.id).all()
    assert len(progress) == 1
    assert (progress[0].status, progress[0].score, progress[0].stars, progress[0].attempts) == (
        ProgressStatus.COMPLETED,
        90,
        3,
        2,
    )
    # La ligne d'accès survit à la désactivation : réactiver est réversible.
    row = db_session.query(ChildPackAccess).filter(ChildPackAccess.child_id == child.id).one()
    assert row.enabled is False

    _set_access(client, parent_head, str(child.id), str(pack.id), True)
    child_head = child_headers(client, child, parent_email="keep@qa.fr")
    assert [r["name"] for r in client.get("/api/v1/lessons/recent", headers=child_head).json()] == ["Le magma"]


def test_every_toggle_records_the_acting_guardian(client: TestClient, db_session: Session):
    pack = make_pack(
        db_session,
        title="Dinos",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    child = make_child(db_session, parent_email="owner@qa.fr")
    owner = ensure_parent(db_session, "owner@qa.fr")
    grandma = ensure_parent(db_session, "grandma@qa.fr")
    grant(child.id, grandma.id, ROLE_GUARDIAN, owner.id, db_session)
    db_session.commit()

    _set_access(client, dev_login(client, "owner@qa.fr"), str(child.id), str(pack.id), True)
    row = db_session.query(ChildPackAccess).filter(ChildPackAccess.child_id == child.id).one()
    assert row.enabled_by == owner.id

    # Gardes concurrents : le dernier écrit gagne, et l'audit dit lequel.
    state = _set_access(client, dev_login(client, "grandma@qa.fr"), str(child.id), str(pack.id), False)
    db_session.refresh(row)
    assert row.enabled is False and row.enabled_by == grandma.id
    assert state["entries"][0]["enabled_by"] == str(grandma.id)

    logs = (
        db_session.query(PackAuditLog)
        .filter(PackAuditLog.pack_id == pack.id)
        .order_by(PackAuditLog.created_at.asc())
        .all()
    )
    actions = [(log.action, log.actor_id) for log in logs]
    assert ("access_enabled", owner.id) in actions
    assert ("access_disabled", grandma.id) in actions
    assert all(log.detail["child_id"] == str(child.id) for log in logs)


def test_non_guardian_cannot_read_or_change_access(client: TestClient, db_session: Session):
    pack = make_pack(db_session, origin=PackOrigin.COMMUNITY, community_status=CommunityStatus.APPROVED)
    child = make_child(db_session, parent_email="mine@qa.fr")
    db_session.commit()

    stranger = dev_login(client, "stranger@qa.fr")
    assert client.get(f"/api/v1/library/children/{child.id}/access", headers=stranger).status_code == 404
    assert (
        client.put(
            f"/api/v1/library/children/{child.id}/access/{pack.id}",
            json={"enabled": True},
            headers=stranger,
        ).status_code
        == 404
    )
    assert (
        client.put(
            f"/api/v1/library/children/{child.id}/auto-enable",
            json={"enabled": True},
            headers=stranger,
        ).status_code
        == 404
    )
    assert db_session.query(ChildPackAccess).count() == 0


# --------------------------------------------------------------------------- #
# Contributeur, signalement
# --------------------------------------------------------------------------- #
def test_contributor_stats_count_real_usage(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "stats@qa.fr")
    approved = make_pack(
        db_session,
        title="Approuvé",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
        handle="Sofia",
    )
    make_pack(
        db_session,
        title="En attente",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.PENDING,
        author=author,
    )
    kid_a = make_child(db_session, parent_email="user_a@qa.fr", name="A")
    kid_b = make_child(db_session, parent_email="user_b@qa.fr", name="B")
    db_session.commit()

    _set_access(client, dev_login(client, "user_a@qa.fr"), str(kid_a.id), str(approved.id), True)
    _set_access(client, dev_login(client, "user_b@qa.fr"), str(kid_b.id), str(approved.id), True)

    stats = client.get("/api/v1/library/me/contributor-stats", headers=dev_login(client, "stats@qa.fr")).json()
    assert stats["packs_approved"] == 1
    assert stats["packs_pending"] == 1
    assert stats["times_enabled"] == 2
    assert stats["families_reached"] == 2

    # Une désactivation retire l'usage : la reconnaissance doit rester honnête.
    _set_access(client, dev_login(client, "user_b@qa.fr"), str(kid_b.id), str(approved.id), False)
    stats = client.get("/api/v1/library/me/contributor-stats", headers=dev_login(client, "stats@qa.fr")).json()
    assert stats["times_enabled"] == 1 and stats["families_reached"] == 1


def test_report_pack_opens_a_moderation_report(client: TestClient, db_session: Session):
    pack = make_pack(db_session, origin=PackOrigin.COMMUNITY, community_status=CommunityStatus.APPROVED)
    db_session.commit()

    headers = dev_login(client, "reporter@qa.fr")
    r = client.post(
        f"/api/v1/library/packs/{pack.id}/report",
        json={"reason": "inappropriate", "details": "Vocabulaire inadapté"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "open" and r.json()["reason"] == "inappropriate"

    report = db_session.query(PackReport).one()
    assert report.pack_id == pack.id and report.details == "Vocabulaire inadapté"

    # Motif hors liste fermée : rejeté par le schéma.
    assert (
        client.post(
            f"/api/v1/library/packs/{pack.id}/report",
            json={"reason": "parce que"},
            headers=headers,
        ).status_code
        == 422
    )


# --------------------------------------------------------------------------- #
# Décision parentale sur une demande (PIN)
# --------------------------------------------------------------------------- #
def test_decide_request_is_pin_gated_and_writes_audited_access(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "author_d@qa.fr")
    pack = make_pack(
        db_session,
        title="Dinos",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
    )
    make_lesson(db_session, pack=pack, name="Le tyrannosaure")
    child = make_child(db_session, parent_email="pin@qa.fr")
    db_session.commit()

    child_head = child_headers(client, child, parent_email="pin@qa.fr")
    created = client.post("/api/v1/discover/requests", json={"pack_id": str(pack.id)}, headers=child_head)
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]

    parent_head = dev_login(client, "pin@qa.fr")
    pending = client.get("/api/v1/library/requests", headers=parent_head).json()
    assert [row["id"] for row in pending] == [request_id]
    assert pending[0]["pack_title"] == "Dinos"

    url = f"/api/v1/library/requests/{request_id}/decide"
    # Aucun PIN défini sur le compte : 403 « pin_not_set », à distinguer d'un
    # PIN faux — le frontend doit pouvoir renvoyer le parent vers la création.
    no_pin = client.post(url, json={"approve": True, "pin": "1234"}, headers=parent_head)
    assert no_pin.status_code == 403
    assert no_pin.json()["detail"]["code"] == "pin_not_set"
    assert client.post("/api/v1/auth/pin", json={"pin": "1234"}, headers=parent_head).status_code == 200
    # PIN erroné : 403 (et non 401, qui déconnecterait le parent côté frontend
    # pour une faute de frappe), et toujours aucun accès accordé.
    refused = client.post(url, json={"approve": True, "pin": "9999"}, headers=parent_head)
    assert refused.status_code == 403
    assert refused.json()["detail"]["code"] == "invalid_pin"
    assert db_session.query(ChildPackAccess).count() == 0

    ok = client.post(url, json={"approve": True, "pin": "1234"}, headers=parent_head)
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "approved"

    row = db_session.query(ChildPackAccess).one()
    parent = ensure_parent(db_session, "pin@qa.fr")
    assert row.enabled is True and row.enabled_by == parent.id
    assert [r["name"] for r in client.get("/api/v1/lessons/recent", headers=child_head).json()] == ["Le tyrannosaure"]
    actions = {log.action for log in db_session.query(PackAuditLog).all()}
    assert {"request_created", "request_approved", "access_enabled"} <= actions

    # Une demande déjà tranchée ne se rejoue pas.
    assert client.post(url, json={"approve": True, "pin": "1234"}, headers=parent_head).status_code == 409


def test_decline_request_grants_nothing(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "author_e@qa.fr")
    pack = make_pack(
        db_session,
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
    )
    child = make_child(db_session, parent_email="decline@qa.fr")
    db_session.commit()

    child_head = child_headers(client, child, parent_email="decline@qa.fr")
    request_id = client.post("/api/v1/discover/requests", json={"pack_id": str(pack.id)}, headers=child_head).json()[
        "id"
    ]

    parent_head = dev_login(client, "decline@qa.fr")
    client.post("/api/v1/auth/pin", json={"pin": "4321"}, headers=parent_head)
    r = client.post(
        f"/api/v1/library/requests/{request_id}/decide",
        json={"approve": False, "pin": "4321"},
        headers=parent_head,
    )
    assert r.status_code == 200 and r.json()["status"] == "declined"
    assert db_session.query(ChildPackAccess).count() == 0


def test_stranger_cannot_decide_another_familys_request(client: TestClient, db_session: Session):
    author = ensure_parent(db_session, "author_f@qa.fr")
    pack = make_pack(
        db_session,
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
    )
    child = make_child(db_session, parent_email="theirs@qa.fr")
    db_session.commit()

    request_id = client.post(
        "/api/v1/discover/requests",
        json={"pack_id": str(pack.id)},
        headers=child_headers(client, child, parent_email="theirs@qa.fr"),
    ).json()["id"]

    stranger = dev_login(client, "nosy@qa.fr")
    client.post("/api/v1/auth/pin", json={"pin": "1111"}, headers=stranger)
    assert client.get("/api/v1/library/requests", headers=stranger).json() == []
    assert (
        client.post(
            f"/api/v1/library/requests/{request_id}/decide",
            json={"approve": True, "pin": "1111"},
            headers=stranger,
        ).status_code
        == 404
    )
    assert db_session.query(ChildPackAccess).count() == 0
