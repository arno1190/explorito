"""Tests du parcours de contribution : envoi, conditions, quota, jeton, verrou, clone.

Ces tests décrivent les garanties de sécurité de la phase 3 : un brouillon
n'atteint que la famille de l'auteur, un jeton long ne publie rien, un pack
approuvé ne se modifie plus, et le clone n'abîme pas l'original (donc pas la
progression des enfants qui l'ont joué).
"""

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Exercise, Lesson
from app.models.pack import CommunityStatus, Pack
from tests.helpers import dev_login
from tests.test_pack_format import lesson, mcq, pack, problem

AUTHOR = "auteur@qa.fr"
OTHER = "autre@qa.fr"


def upload(client: TestClient, headers: dict[str, str], document: dict | None = None, **params: str) -> dict:
    """Envoie un document `.explorito` en corps JSON et renvoie la réponse HTTP brute."""
    query = "&".join(f"{key}={value}" for key, value in params.items())
    url = "/api/v1/contributions" + (f"?{query}" if query else "")
    return client.post(url, json=document if document is not None else pack(), headers=headers)


def first_upload(client: TestClient, headers: dict[str, str], document: dict | None = None) -> dict:
    """Premier envoi d'un compte : accepte les conditions et renvoie le corps 201."""
    response = upload(client, headers, document, accept_terms="true", handle="Toto")
    assert response.status_code == 201, response.text
    return response.json()


def test_upload_creates_a_draft_and_returns_a_preview_url(client: TestClient, db_session: Session):
    headers = dev_login(client, AUTHOR)

    body = first_upload(client, headers)

    assert body["community_status"] == CommunityStatus.DRAFT.value
    assert body["preview_url"] == f"{settings.PUBLIC_APP_URL}/contributions/{body['pack_id']}"
    assert body["quality_score"] == 100

    stored = db_session.query(Pack).filter(Pack.id == UUID(body["pack_id"])).first()
    assert stored.author_handle == "Toto"
    assert db_session.query(Lesson).filter(Lesson.pack_id == stored.id).count() == 2

    detail = client.get(f"/api/v1/contributions/{body['pack_id']}", headers=headers).json()
    assert [len(item["exercises"]) for item in detail["lessons"]] == [2, 2]
    assert client.get("/api/v1/contributions", headers=headers).json()[0]["id"] == body["pack_id"]


def test_terms_are_required_once_then_remembered(client: TestClient, db_session: Session):
    headers = dev_login(client, AUTHOR)

    refused = upload(client, headers)
    assert refused.status_code == 428
    detail = refused.json()["detail"]
    assert detail["code"] == "terms_required"
    assert detail["terms_version"] == settings.CONTRIBUTOR_TERMS_VERSION
    assert detail["terms"].strip()

    first_upload(client, headers)

    # Deuxième envoi sans rien accepter : les conditions sont déjà acceptées.
    again = upload(client, headers, pack(lessons=[lesson(name="Autre leçon"), lesson(name="Encore une", tier=2)]))
    assert again.status_code == 201, again.text
    assert client.get("/api/v1/contributions/terms", headers=headers).json()["accepted"] is True


def test_invalid_pack_returns_the_full_issue_list(client: TestClient, db_session: Session):
    headers = dev_login(client, AUTHOR)
    broken = pack(lessons=[lesson(exercises=[mcq(difficulty_level=None)])])

    response = upload(client, headers, broken, accept_terms="true")

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "pack_invalid"
    assert "difficulty_level_missing" in {issue["code"] for issue in detail["issues"]}
    assert detail["issues"][0]["lesson_index"] == 0
    # Le refus n'annule pas l'acceptation des conditions : l'auteur corrige et
    # renvoie sans repasser par le formulaire.
    assert client.get("/api/v1/contributions/terms", headers=headers).json()["accepted"] is True


def test_quota_exceeded_returns_429(client: TestClient, db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "PACK_MAX_UPLOADS_PER_DAY", 1)
    headers = dev_login(client, AUTHOR)
    first_upload(client, headers)

    refused = upload(client, headers)

    assert refused.status_code == 429
    assert refused.json()["detail"]["code"] == "quota_exceeded"


def test_declared_xp_never_reaches_the_database(client: TestClient, db_session: Session):
    headers = dev_login(client, AUTHOR)
    money_printer = pack(lessons=[lesson(exercises=[mcq(difficulty_level=5), problem(difficulty_level=5)])])
    money_printer["lessons"][0]["xp_reward"] = 99999

    body = first_upload(client, headers, money_printer)

    stored = db_session.query(Lesson).filter(Lesson.pack_id == UUID(body["pack_id"])).first()
    # 2 exercices, pack non ratifié → 2 × le forfait, et jamais 99999. Le tarif
    # gradué de la difficulté 5 n'arrive qu'après ratification à la revue, sinon
    # l'écran annoncerait une XP que l'enfant ne gagnerait pas (issue #10).
    assert stored.xp_reward == 2 * settings.XP_PER_EXERCISE


def test_upload_token_can_draft_but_never_publish(client: TestClient, db_session: Session):
    headers = dev_login(client, AUTHOR)
    first_upload(client, headers)  # accepte les conditions via la session

    created = client.post("/api/v1/contributions/tokens", json={"label": "claude-cli"}, headers=headers)
    assert created.status_code == 201, created.text
    secret = created.json()["token"]
    assert created.json()["prefix"] == secret[:8]

    # La liste ne réexpose jamais le secret.
    listed = client.get("/api/v1/contributions/tokens", headers=headers).json()
    assert "token" not in listed[0] and listed[0]["active"] is True

    token_headers = {"X-Upload-Token": secret}
    drafted = upload(client, token_headers, pack(lessons=[lesson(name="Depuis la compétence")]))
    assert drafted.status_code == 201, drafted.text
    pack_id = drafted.json()["pack_id"]

    for method, url in (
        ("post", f"/api/v1/contributions/{pack_id}/submit"),
        ("post", f"/api/v1/contributions/{pack_id}/clone"),
    ):
        refused = getattr(client, method)(url, headers=token_headers)
        assert refused.status_code == 403, refused.text
        assert refused.json()["detail"]["code"] == "token_scope"
    patched = client.patch(f"/api/v1/contributions/{pack_id}", json={"title": "Volé"}, headers=token_headers)
    assert patched.status_code == 403

    # La même soumission par session fonctionne.
    submitted = client.post(f"/api/v1/contributions/{pack_id}/submit", headers=headers)
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["community_status"] == CommunityStatus.PENDING.value


def test_revoked_token_stops_working_immediately(client: TestClient, db_session: Session):
    headers = dev_login(client, AUTHOR)
    first_upload(client, headers)
    created = client.post("/api/v1/contributions/tokens", json={"label": "portable"}, headers=headers).json()

    assert client.delete(f"/api/v1/contributions/tokens/{created['id']}", headers=headers).status_code == 204

    refused = upload(client, {"X-Upload-Token": created["token"]})
    assert refused.status_code == 401


def test_quick_edit_revalidates_and_refuses_an_invalid_result(client: TestClient, db_session: Session):
    headers = dev_login(client, AUTHOR)
    body = first_upload(client, headers)
    detail = client.get(f"/api/v1/contributions/{body['pack_id']}", headers=headers).json()
    target = detail["lessons"][0]["exercises"][0]

    refused = client.patch(
        f"/api/v1/contributions/{body['pack_id']}",
        json={
            "lessons": [
                {
                    "id": detail["lessons"][0]["id"],
                    "exercises": [{"id": target["id"], "correct_answer": {"option_ids": ["inconnu"]}}],
                }
            ]
        },
        headers=headers,
    )

    assert refused.status_code == 422
    assert "exercise_shape" in {issue["code"] for issue in refused.json()["detail"]["issues"]}
    # Rien n'a été écrit : la réponse correcte d'origine est intacte.
    exercise = db_session.query(Exercise).filter(Exercise.id == UUID(target["id"])).first()
    assert exercise.correct_answer == {"option_ids": ["a"]}


def test_quick_edit_applies_changes_and_recomputes_xp(client: TestClient, db_session: Session):
    headers = dev_login(client, AUTHOR)
    body = first_upload(client, headers)
    detail = client.get(f"/api/v1/contributions/{body['pack_id']}", headers=headers).json()
    first_lesson = detail["lessons"][0]

    response = client.patch(
        f"/api/v1/contributions/{body['pack_id']}",
        json={
            "title": "Coupe du Monde 2026",
            "lessons": [
                {
                    "id": first_lesson["id"],
                    "name": "Additions revues",
                    "tier": 3,
                    "exercises": [
                        {"id": exercise["id"], "difficulty_level": 5} for exercise in first_lesson["exercises"]
                    ],
                }
            ],
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["title"] == "Coupe du Monde 2026"
    edited = next(item for item in updated["lessons"] if item["id"] == first_lesson["id"])
    assert edited["name"] == "Additions revues" and edited["tier"] == 3
    assert edited["xp_reward"] == 2 * settings.XP_PER_EXERCISE


def test_locked_pack_refuses_author_edits_and_clone_leaves_it_untouched(client: TestClient, db_session: Session):
    headers = dev_login(client, AUTHOR)
    body = first_upload(client, headers)
    original_id = body["pack_id"]

    # Simule l'approbation par la modération : verrou + statut approuvé.
    original = db_session.query(Pack).filter(Pack.id == UUID(original_id)).first()
    original.locked = True
    original.community_status = CommunityStatus.APPROVED.value
    db_session.commit()
    original_lesson_ids = {
        str(row[0]) for row in db_session.query(Lesson.id).filter(Lesson.pack_id == UUID(original_id)).all()
    }

    refused = client.patch(f"/api/v1/contributions/{original_id}", json={"title": "Autre chose"}, headers=headers)
    assert refused.status_code == 409
    detail = refused.json()["detail"]
    assert detail["code"] == "pack_locked"
    assert "clone" in detail["message"].lower()

    cloned = client.post(f"/api/v1/contributions/{original_id}/clone", headers=headers)
    assert cloned.status_code == 201, cloned.text
    clone_body = cloned.json()
    assert clone_body["community_status"] == CommunityStatus.DRAFT.value
    assert clone_body["locked"] is False
    assert clone_body["cloned_from_pack_id"] == original_id

    clone_lesson_ids = {item["id"] for item in clone_body["lessons"]}
    assert clone_lesson_ids.isdisjoint(original_lesson_ids)
    assert len(clone_lesson_ids) == len(original_lesson_ids)

    # L'original garde exactement ses lignes : aucune progression ne se détache.
    still_there = {str(row[0]) for row in db_session.query(Lesson.id).filter(Lesson.pack_id == UUID(original_id)).all()}
    assert still_there == original_lesson_ids
    refreshed = db_session.query(Pack).filter(Pack.id == UUID(original_id)).first()
    assert refreshed.locked is True and refreshed.title == "Coupe du Monde"

    # Le clone est modifiable, lui.
    assert (
        client.patch(
            f"/api/v1/contributions/{clone_body['id']}", json={"title": "Coupe du Monde v2"}, headers=headers
        ).status_code
        == 200
    )


def test_another_parent_cannot_see_or_touch_the_pack(client: TestClient, db_session: Session):
    author_headers = dev_login(client, AUTHOR)
    body = first_upload(client, author_headers)
    intruder = dev_login(client, OTHER)

    assert client.get(f"/api/v1/contributions/{body['pack_id']}", headers=intruder).status_code == 404
    assert client.get("/api/v1/contributions", headers=intruder).json() == []
    assert (
        client.patch(f"/api/v1/contributions/{body['pack_id']}", json={"title": "À moi"}, headers=intruder).status_code
        == 404
    )
    assert client.post(f"/api/v1/contributions/{body['pack_id']}/submit", headers=intruder).status_code == 404


def test_unauthenticated_upload_is_refused(client: TestClient, db_session: Session):
    assert client.post("/api/v1/contributions", json=pack()).status_code == 401
    assert client.post("/api/v1/contributions", json=pack(), headers={"X-Upload-Token": "faux"}).status_code == 401


def test_oversized_file_is_refused_before_validation(client: TestClient, db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "PACK_MAX_FILE_SIZE", 256)
    headers = dev_login(client, AUTHOR)

    response = upload(client, headers, accept_terms="true")

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "file_too_large"


def test_multipart_upload_uses_the_same_endpoint(client: TestClient, db_session: Session):
    import json

    headers = dev_login(client, AUTHOR)
    response = client.post(
        "/api/v1/contributions",
        files={"file": ("theme.explorito", json.dumps(pack()), "application/json")},
        data={"accept_terms": "true", "handle": "Toto"},
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["community_status"] == CommunityStatus.DRAFT.value
