"""Niveaux proposables à un enfant (issue #23).

Le CM2 était annoncé sans être semé : une famille dont l'enfant est en CM2
créait un compte, choisissait CM2, et arrivait sur une application vide. Ces
tests décrivent la règle qui l'empêche — la liste dérive du contenu publié, et
rien d'autre.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import LevelEnum
from app.models.pack import CommunityStatus, PackOrigin
from tests.helpers import dev_login, make_child, make_lesson, make_pack


def test_a_level_without_content_is_never_offered(client: TestClient, db_session: Session):
    """Semer le CP ne fait pas apparaître le CM2 : c'est tout le sujet de l'issue."""
    pack = make_pack(db_session, level=LevelEnum.CP)
    make_lesson(db_session, pack=pack, level=LevelEnum.CP)
    db_session.commit()

    levels = client.get("/api/v1/children/levels", headers=dev_login(client)).json()

    assert levels == ["cp"]
    assert "cm2" not in levels


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


def test_a_pack_spanning_levels_offers_all_of_them(client: TestClient, db_session: Session):
    """Un pack CP→CE2 rend jouables le CP, le CE1 et le CE2."""
    pack = make_pack(db_session, level=LevelEnum.CP, level_max=LevelEnum.CE2)
    make_lesson(db_session, pack=pack, level=LevelEnum.CP)
    db_session.commit()

    levels = client.get("/api/v1/children/levels", headers=dev_login(client)).json()

    assert levels == ["cp", "ce1", "ce2"]


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

    assert "cm2" not in levels


def test_a_pack_without_a_published_lesson_does_not_open_a_level(client: TestClient, db_session: Session):
    """Un pack visible mais vide ouvre sur du vide : identique à un niveau non semé."""
    pack = make_pack(db_session, level=LevelEnum.CM1)
    make_lesson(db_session, pack=pack, level=LevelEnum.CM1, published=False)
    db_session.commit()

    levels = client.get("/api/v1/children/levels", headers=dev_login(client)).json()

    assert "cm1" not in levels


def test_an_empty_catalogue_offers_nothing(client: TestClient):
    """Base sans contenu : aucun niveau promis, plutôt qu'une liste en dur mensongère."""
    assert client.get("/api/v1/children/levels", headers=dev_login(client)).json() == []


def test_a_child_already_in_an_unseeded_level_still_works(client: TestClient, db_session: Session):
    """Un enfant déjà enregistré en CM2 ne casse pas et garde son niveau.

    Masquer un niveau est une décision d'affichage : elle ne doit jamais
    réécrire les données d'une famille déjà installée.
    """
    child = make_child(db_session, level=LevelEnum.CM2, name="Aîné")
    cp_pack = make_pack(db_session, level=LevelEnum.CP)
    make_lesson(db_session, pack=cp_pack, level=LevelEnum.CP)
    db_session.commit()
    headers = dev_login(client)

    assert "cm2" not in client.get("/api/v1/children/levels", headers=headers).json()

    detail = client.get(f"/api/v1/children/{child.id}", headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["level"] == "cm2"

    # Renommer l'enfant sans toucher au niveau le laisse en CM2.
    renamed = client.put(f"/api/v1/children/{child.id}", json={"name": "Aînée"}, headers=headers)
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["level"] == "cm2"


def test_levels_is_not_read_as_a_child_id(client: TestClient):
    """« levels » ne doit pas être capturé par la route ``/{child_id}``."""
    response = client.get("/api/v1/children/levels", headers=dev_login(client))

    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)
