"""Tests de la suppression d'un pack par son auteur.

C'est la seule opération destructrice de contenu de l'application, ajoutée
parce qu'un envoi raté restait sinon à vie dans « Mes packs ». Les garanties
testées ici sont celles qui la rendent acceptable : jamais un pack publié,
jamais un pack verrouillé, et **jamais** un pack dans lequel un enfant a déjà
travaillé — ``user_progress`` et ``exercise_results`` cascadent depuis les
leçons, donc une suppression trop permissive effacerait une progression.
"""

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import Exercise, Lesson
from app.models.contribution import PackAuditLog
from app.models.pack import CommunityStatus, Pack
from app.models.progress import ExerciseResult, ProgressStatus, UserProgress
from tests.helpers import dev_login, make_child
from tests.test_pack_format import pack

AUTHOR = "suppression@qa.fr"
OTHER = "voisin-suppression@qa.fr"


def _draft(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post("/api/v1/contributions?accept_terms=true&handle=Supprimeur", json=pack(), headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["pack_id"]


def test_author_deletes_a_draft_and_its_content_goes_with_it(client: TestClient, db_session: Session):
    headers = dev_login(client, AUTHOR)
    pack_id = _draft(client, headers)
    assert db_session.query(Lesson).filter(Lesson.pack_id == UUID(pack_id)).count() == 2

    assert client.delete(f"/api/v1/contributions/{pack_id}", headers=headers).status_code == 204

    assert db_session.query(Pack).filter(Pack.id == UUID(pack_id)).first() is None
    assert db_session.query(Lesson).filter(Lesson.pack_id == UUID(pack_id)).count() == 0
    assert client.get(f"/api/v1/contributions/{pack_id}", headers=headers).status_code == 404
    assert client.get("/api/v1/contributions", headers=headers).json() == []


def test_deletion_leaves_an_audit_trace_that_survives_the_pack(client: TestClient, db_session: Session):
    """La ligne d'audit est en CASCADE sur le pack : elle doit être détachée pour subsister."""
    headers = dev_login(client, AUTHOR)
    pack_id = _draft(client, headers)
    client.delete(f"/api/v1/contributions/{pack_id}", headers=headers)

    trace = db_session.query(PackAuditLog).filter(PackAuditLog.action == "pack_deleted").one()
    assert trace.pack_id is None
    assert trace.detail["pack_id"] == pack_id
    assert trace.detail["lessons"] == 2


def test_a_pack_a_child_has_played_is_never_deleted(client: TestClient, db_session: Session):
    """Le garde-fou central : supprimer effacerait la progression de l'enfant."""
    headers = dev_login(client, AUTHOR)
    pack_id = _draft(client, headers)
    child = make_child(db_session, parent_email=AUTHOR, name="Joueur")
    lesson = db_session.query(Lesson).filter(Lesson.pack_id == UUID(pack_id)).first()
    exercise = db_session.query(Exercise).filter(Exercise.lesson_id == lesson.id).first()
    db_session.add(
        UserProgress(user_id=child.id, lesson_id=lesson.id, status=ProgressStatus.STARTED, attempts=1),
    )
    db_session.add(
        ExerciseResult(user_id=child.id, exercise_id=exercise.id, is_correct=True, answer={"option_ids": ["a"]})
    )
    db_session.commit()

    refused = client.delete(f"/api/v1/contributions/{pack_id}", headers=headers)
    assert refused.status_code == 409
    detail = refused.json()["detail"]
    assert detail["code"] == "pack_has_progress"
    assert detail["progress_rows"] == 1 and detail["result_rows"] == 1

    # Rien n'a bougé : ni le pack, ni la progression.
    assert db_session.query(Pack).filter(Pack.id == UUID(pack_id)).first() is not None
    assert db_session.query(UserProgress).count() == 1
    assert db_session.query(ExerciseResult).count() == 1


def test_a_published_pack_cannot_be_deleted_by_its_author(client: TestClient, db_session: Session):
    """D'autres familles l'utilisent : il se retire par la modération, pas unilatéralement."""
    headers = dev_login(client, AUTHOR)
    pack_id = _draft(client, headers)
    stored = db_session.query(Pack).filter(Pack.id == UUID(pack_id)).one()
    stored.community_status = CommunityStatus.APPROVED.value
    stored.locked = True
    db_session.commit()

    refused = client.delete(f"/api/v1/contributions/{pack_id}", headers=headers)
    assert refused.status_code == 409
    assert refused.json()["detail"]["code"] == "pack_not_deletable"
    assert db_session.query(Pack).filter(Pack.id == UUID(pack_id)).first() is not None


def test_a_rejected_pack_stays_deletable(client: TestClient, db_session: Session):
    """Refusé pour la communauté = la famille le garde, donc elle doit pouvoir le jeter."""
    headers = dev_login(client, AUTHOR)
    pack_id = _draft(client, headers)
    stored = db_session.query(Pack).filter(Pack.id == UUID(pack_id)).one()
    stored.community_status = CommunityStatus.REJECTED.value
    db_session.commit()

    assert client.delete(f"/api/v1/contributions/{pack_id}", headers=headers).status_code == 204


def test_a_pending_pack_is_not_deletable_while_it_waits_for_review(client: TestClient, db_session: Session):
    headers = dev_login(client, AUTHOR)
    pack_id = _draft(client, headers)
    assert client.post(f"/api/v1/contributions/{pack_id}/submit", headers=headers).status_code == 200

    refused = client.delete(f"/api/v1/contributions/{pack_id}", headers=headers)
    assert refused.status_code == 409
    assert refused.json()["detail"]["code"] == "pack_not_deletable"


def test_another_parent_cannot_delete_someone_elses_draft(client: TestClient, db_session: Session):
    author_headers = dev_login(client, AUTHOR)
    pack_id = _draft(client, author_headers)

    stranger = dev_login(client, OTHER)
    # 404 et non 403 : l'existence d'un brouillon d'autrui ne se confirme pas.
    assert client.delete(f"/api/v1/contributions/{pack_id}", headers=stranger).status_code == 404
    assert db_session.query(Pack).filter(Pack.id == UUID(pack_id)).first() is not None


def test_an_upload_token_cannot_delete(client: TestClient, db_session: Session):
    """Un jeton d'envoi crée des brouillons ; il n'en détruit pas."""
    headers = dev_login(client, AUTHOR)
    pack_id = _draft(client, headers)
    code = client.post("/api/v1/contributions/pairing", headers=headers).json()["code"]
    token = client.post("/api/v1/contributions/pairing/claim", json={"code": code}).json()["token"]

    refused = client.delete(f"/api/v1/contributions/{pack_id}", headers={"X-Upload-Token": token})
    assert refused.status_code == 403
    assert db_session.query(Pack).filter(Pack.id == UUID(pack_id)).first() is not None
