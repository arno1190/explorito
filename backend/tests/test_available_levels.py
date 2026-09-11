"""Niveaux proposables à un enfant (issue #23).

Le CM2 était annoncé sans être semé : une famille dont l'enfant est en CM2
créait un compte, choisissait CM2, et arrivait sur une application vide. Ces
tests décrivent la règle qui l'empêche — un niveau est annoncé si, et seulement
si, un enfant qu'on y placerait recevrait vraiment une leçon publiée de ce
niveau, sans qu'un garde ait rien à activer.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import LevelEnum
from app.models.pack import CommunityStatus, PackOrigin
from tests.helpers import dev_login, make_child, make_lesson, make_pack, make_subject


def test_a_level_without_content_is_never_offered(client: TestClient, db_session: Session):
    """Semer le CP ne fait pas apparaître le CM2 : c'est tout le sujet de l'issue."""
    pack = make_pack(db_session, level=LevelEnum.CP)
    make_lesson(db_session, pack=pack, level=LevelEnum.CP)
    db_session.commit()

    levels = client.get("/api/v1/children/levels", headers=dev_login(client)).json()

    assert levels == ["cp"]


def test_the_list_follows_the_content_that_exists(client: TestClient, db_session: Session):
    """Semer un niveau suffit à le proposer — la liste n'est pas une liste en dur.

    Elle suit aussi l'ordre pédagogique, jamais l'ordre alphabétique des valeurs
    (« ce1 » < « cp » en ASCII, mais le CP vient avant le CE1 à l'école).
    """
    cp_pack = make_pack(db_session, level=LevelEnum.CP)
    make_lesson(db_session, pack=cp_pack, level=LevelEnum.CP)
    ce1_pack = make_pack(db_session, level=LevelEnum.CE1)
    make_lesson(db_session, pack=ce1_pack, level=LevelEnum.CE1)
    db_session.commit()

    levels = client.get("/api/v1/children/levels", headers=dev_login(client)).json()

    assert levels == ["cp", "ce1"]


def test_a_pack_spanning_levels_offers_only_the_levels_it_teaches(client: TestClient, db_session: Session):
    """Un pack CP→CE2 dont les leçons sont en CP et en CE2 laisse le CE1 fermé.

    L'intervalle du pack est déduit de l'étendue de ses leçons : il peut être
    creux au milieu. Toutes les routes qui servent un enfant filtrent sur le
    niveau du parcours de la leçon, donc un enfant de CE1 n'y trouverait rien.
    """
    pack = make_pack(db_session, level=LevelEnum.CP, level_max=LevelEnum.CE2)
    make_lesson(db_session, pack=pack, level=LevelEnum.CP)
    make_lesson(db_session, pack=pack, level=LevelEnum.CE2, name="Leçon CE2")
    db_session.commit()

    levels = client.get("/api/v1/children/levels", headers=dev_login(client)).json()

    assert levels == ["cp", "ce2"]


def test_a_pack_awaiting_review_does_not_open_a_level(client: TestClient, db_session: Session):
    """Un pack communautaire non approuvé n'est pas du contenu : le niveau reste fermé."""
    pending = make_pack(
        db_session,
        level=LevelEnum.CM2,
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.PENDING,
    )
    make_lesson(db_session, pack=pending, level=LevelEnum.CM2)
    db_session.commit()

    levels = client.get("/api/v1/children/levels", headers=dev_login(client)).json()

    assert levels == []


def test_an_approved_community_pack_alone_does_not_open_a_level(client: TestClient, db_session: Session):
    """Approuvé = listé au catalogue parent, jamais livré à un enfant par défaut.

    Un pack communautaire n'atteint un enfant que par une activation explicite
    ou l'interrupteur d'auto-activation, éteint à la création. Annoncer son
    niveau enverrait chaque nouvelle famille sur une application vide.
    """
    approved = make_pack(
        db_session,
        level=LevelEnum.CM2,
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    make_lesson(db_session, pack=approved, level=LevelEnum.CM2)
    db_session.commit()

    levels = client.get("/api/v1/children/levels", headers=dev_login(client)).json()

    assert levels == []


def test_a_pack_without_a_published_lesson_does_not_open_a_level(client: TestClient, db_session: Session):
    """Un pack visible mais vide ouvre sur du vide : identique à un niveau non semé."""
    pack = make_pack(db_session, level=LevelEnum.CM1)
    make_lesson(db_session, pack=pack, level=LevelEnum.CM1, published=False)
    db_session.commit()

    levels = client.get("/api/v1/children/levels", headers=dev_login(client)).json()

    assert levels == []


def test_an_empty_catalogue_offers_nothing(client: TestClient):
    """Base sans contenu : aucun niveau promis, plutôt qu'une liste en dur mensongère."""
    assert client.get("/api/v1/children/levels", headers=dev_login(client)).json() == []


def test_a_child_keeps_a_level_that_is_no_longer_offered(client: TestClient, db_session: Session):
    """Masquer un niveau est un choix d'affichage : il ne réécrit pas une famille installée.

    L'enfant est en CM2 ; seul le CP est semé. Le CM2 disparaît de la liste, et
    une mise à jour qui ne parle pas du niveau le laisse intact.
    """
    child = make_child(db_session, level=LevelEnum.CM2, name="Aîné")
    cp_pack = make_pack(db_session, level=LevelEnum.CP)
    make_lesson(db_session, pack=cp_pack, level=LevelEnum.CP)
    db_session.commit()
    headers = dev_login(client)

    assert client.get("/api/v1/children/levels", headers=headers).json() == ["cp"]

    renamed = client.put(f"/api/v1/children/{child.id}", json={"name": "Aînée"}, headers=headers)
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["level"] == "cm2"


def test_choosing_a_first_interest_leaves_only_that_collection(client: TestClient, db_session: Session):
    """Parcours d'accueil, étape 2 : mettre une collection en avant masque les autres.

    Le parcours enregistre le choix en désactivant toutes les autres
    collections, et la fiche de l'enfant doit pouvoir revenir en arrière.
    """
    subject = make_subject(db_session)
    pack = make_pack(db_session, level=LevelEnum.CP)
    make_lesson(db_session, pack=pack, subject=subject, level=LevelEnum.CP)
    db_session.commit()
    headers = dev_login(client)

    created = client.post(
        "/api/v1/children",
        json={"name": "Louise", "level": "cp"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    child_id = created.json()["id"]

    chosen = client.put(
        f"/api/v1/children/{child_id}",
        json={"disabled_collections": ["dinosaures", "espace"]},
        headers=headers,
    )
    assert chosen.status_code == 200, chosen.text
    assert sorted(chosen.json()["disabled_collections"]) == ["dinosaures", "espace"]

    restored = client.put(f"/api/v1/children/{child_id}", json={"disabled_collections": []}, headers=headers)
    assert restored.status_code == 200, restored.text
    assert restored.json()["disabled_collections"] == []


def test_levels_is_not_read_as_a_child_id(client: TestClient):
    """« levels » ne doit pas être capturé par la route ``/{child_id}``."""
    response = client.get("/api/v1/children/levels", headers=dev_login(client))

    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)
