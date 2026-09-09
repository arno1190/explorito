"""Parcours d'accueil : de l'inscription au premier exercice (issue #24).

Le trou que l'issue décrit est côté interface — un tableau de bord vide, sans
rien qui mène au premier exercice. Ces tests couvrent l'autre moitié : que le
chemin qu'un compte neuf emprunte réellement, étape par étape, réponde bien.
C'est la garantie que le parcours d'accueil a quelque chose à appeler.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import LevelEnum
from tests.helpers import dev_login, make_exercise, make_lesson, make_pack, make_subject

BRAND_NEW_PARENT = "toute.nouvelle.famille@exemple.fr"


def _seed_playable_content(db: Session) -> None:
    """Un minimum de contenu publié, sans quoi aucun niveau n'est proposable."""
    subject = make_subject(db)
    pack = make_pack(db, level=LevelEnum.CP)
    lesson = make_lesson(db, pack=pack, subject=subject, level=LevelEnum.CP)
    make_exercise(db, lesson=lesson)
    db.commit()


def test_a_brand_new_account_can_reach_the_first_exercise(client: TestClient, db_session: Session):
    """Compte neuf → enfant créé → `/play` répond. Le parcours d'accueil au complet.

    Chaque étape est celle que l'écran d'accueil enchaîne : on choisit un niveau
    dans la liste proposée, on crée l'enfant, puis on « incarne » l'enfant comme
    le fait le bouton « Lancer ».
    """
    _seed_playable_content(db_session)
    headers = dev_login(client, BRAND_NEW_PARENT)

    # Le tableau de bord est bien vide : c'est ce qui déclenche le parcours.
    assert client.get("/api/v1/children", headers=headers).json() == []

    # Étape 1 — la classe se choisit dans une liste qui a du contenu.
    levels = client.get("/api/v1/children/levels", headers=headers).json()
    assert levels, "sans niveau proposable, le parcours n'a rien à offrir"

    created = client.post(
        "/api/v1/children",
        json={"name": "Louise", "birth_date": "2018-04-02", "level": levels[0]},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    child_id = created.json()["id"]

    # Bouton « Lancer Louise » : le parent agit désormais pour l'enfant.
    playing = {**headers, "X-Acting-Child-Id": child_id}

    subjects = client.get("/api/v1/subjects", headers=playing)
    assert subjects.status_code == 200, subjects.text
    assert any(s["is_active"] for s in subjects.json()), "l'écran de jeu serait vide"

    overview = client.get("/api/v1/progress/subjects-overview", headers=playing)
    assert overview.status_code == 200, overview.text


def test_the_optional_steps_are_really_optional(client: TestClient, db_session: Session):
    """Sauter le centre d'intérêt et le code PIN ne bloque pas le lancement.

    « Le parcours ne bloque jamais » : un enfant créé sans rien d'autre doit
    déjà pouvoir jouer.
    """
    _seed_playable_content(db_session)
    headers = dev_login(client, BRAND_NEW_PARENT)
    levels = client.get("/api/v1/children/levels", headers=headers).json()

    created = client.post(
        "/api/v1/children",
        json={"name": "Sans Fioritures", "level": levels[0]},
        headers=headers,
    )
    assert created.status_code == 201, created.text

    assert client.get("/api/v1/auth/me", headers=headers).json()["has_pin"] is False

    playing = {**headers, "X-Acting-Child-Id": created.json()["id"]}
    assert client.get("/api/v1/subjects", headers=playing).status_code == 200


def test_choosing_a_first_interest_leaves_only_that_collection(client: TestClient, db_session: Session):
    """Étape 2 : mettre une collection en avant masque les autres, et c'est réversible.

    C'est ce qui rend le premier écran désirable pour l'enfant plutôt qu'un mur
    de sept catalogues.
    """
    _seed_playable_content(db_session)
    headers = dev_login(client, BRAND_NEW_PARENT)
    child_id = client.post("/api/v1/children", json={"name": "Nina"}, headers=headers).json()["id"]

    catalogs = client.get("/api/v1/collection/catalogs", headers=headers).json()
    assert len(catalogs) > 1, "le test n'a de sens qu'avec plusieurs catalogues"
    chosen = catalogs[0]["slug"]
    others = [c["slug"] for c in catalogs if c["slug"] != chosen]

    updated = client.put(
        f"/api/v1/children/{child_id}",
        json={"disabled_collections": others},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert chosen not in updated.json()["disabled_collections"]
    assert sorted(updated.json()["disabled_collections"]) == sorted(others)

    # Réversible : le parent réactive tout depuis la fiche de l'enfant.
    restored = client.put(
        f"/api/v1/children/{child_id}",
        json={"disabled_collections": []},
        headers=headers,
    )
    assert restored.status_code == 200, restored.text
    assert restored.json()["disabled_collections"] == []


def test_the_parent_pin_can_be_set_during_onboarding(client: TestClient, db_session: Session):
    """Étape 3 : le code PIN se pose depuis le parcours et devient effectif."""
    headers = dev_login(client, BRAND_NEW_PARENT)
    assert client.get("/api/v1/auth/me", headers=headers).json()["has_pin"] is False

    response = client.post("/api/v1/auth/pin", json={"pin": "4271"}, headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["has_pin"] is True
    assert client.post("/api/v1/auth/verify-pin", json={"pin": "4271"}, headers=headers).status_code == 204
