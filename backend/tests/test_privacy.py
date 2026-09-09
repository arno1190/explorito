"""Politique de confidentialité côté famille (issue #21).

Ces tests décrivent ce qu'un parent observe : il peut lire la politique **avant**
de livrer quoi que ce soit, son acceptation est datée et versionnée en base, et
supprimer un enfant efface réellement le travail de cet enfant.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.progress import ExerciseResult, ProgressStatus, UserProgress
from app.models.user import User
from app.services.family_privacy import PRIVACY_POLICY_VERSION
from tests.helpers import (
    DEFAULT_PARENT_EMAIL,
    dev_login,
    make_child,
    make_exercise,
    make_lesson,
    make_pack,
)


def test_policy_is_readable_without_an_account(client: TestClient):
    """Le parent lit la politique sans être connecté — sinon elle ne sert à rien."""
    response = client.get("/api/v1/legal/privacy")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["version"] == PRIVACY_POLICY_VERSION
    assert body["accepted"] is False
    # Les points que l'issue #21 exige de dire explicitement à la famille.
    assert "Les enfants n'ont aucun compte" in body["text"]
    assert settings.PRIVACY_CONTACT_EMAIL in body["text"]
    assert settings.PRIVACY_HOST in body["text"]


def test_a_new_parent_has_not_accepted_anything(client: TestClient):
    """Un compte neuf n'a rien accepté : la case à cocher doit donc s'afficher."""
    headers = dev_login(client)

    me = client.get("/api/v1/auth/me", headers=headers)

    assert me.status_code == 200, me.text
    assert me.json()["privacy_accepted"] is False


def test_acceptance_is_recorded_with_its_version_and_date(client: TestClient, db_session: Session):
    """Cocher la case horodate la version acceptée en base, et /me le reflète."""
    headers = dev_login(client)
    before = datetime.utcnow()

    accept = client.post(
        "/api/v1/legal/privacy/accept",
        json={"version": PRIVACY_POLICY_VERSION},
        headers=headers,
    )

    assert accept.status_code == 200, accept.text
    assert accept.json()["accepted"] is True

    parent = db_session.query(User).filter(User.email == DEFAULT_PARENT_EMAIL).one()
    assert parent.privacy_version == PRIVACY_POLICY_VERSION
    assert parent.privacy_accepted_at is not None
    assert parent.privacy_accepted_at >= before.replace(microsecond=0)

    assert client.get("/api/v1/auth/me", headers=headers).json()["privacy_accepted"] is True
    assert client.get("/api/v1/legal/privacy", headers=headers).json()["accepted"] is True


def test_accepting_a_stale_version_is_refused(client: TestClient):
    """Une case cochée sur un texte périmé n'engage pas : 409, et rien n'est écrit."""
    headers = dev_login(client)

    response = client.post(
        "/api/v1/legal/privacy/accept",
        json={"version": "1999-01-01"},
        headers=headers,
    )

    assert response.status_code == 409, response.text
    assert client.get("/api/v1/auth/me", headers=headers).json()["privacy_accepted"] is False


def test_a_new_policy_version_asks_the_parent_again(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """Publier une nouvelle version périme l'ancien consentement.

    Le parent revoit la case : l'acceptation de l'ancien texte ne couvre pas le
    nouveau.
    """
    headers = dev_login(client)
    client.post("/api/v1/legal/privacy/accept", json={"version": PRIVACY_POLICY_VERSION}, headers=headers)
    assert client.get("/api/v1/auth/me", headers=headers).json()["privacy_accepted"] is True

    monkeypatch.setattr(settings, "PRIVACY_POLICY_VERSION", "2099-12-31")

    assert client.get("/api/v1/auth/me", headers=headers).json()["privacy_accepted"] is False


def test_deleting_a_child_erases_its_school_work(client: TestClient, db_session: Session):
    """« Supprimer un enfant supprime bien ses résultats » — promesse du point 9.

    Garde-fou : la politique promet un effacement en cascade et immédiat. Si une
    table de progression cessait un jour de cascader, la promesse deviendrait
    fausse sans que rien d'autre ne casse.
    """
    child = make_child(db_session, name="Zoé")
    pack = make_pack(db_session)
    lesson = make_lesson(db_session, pack=pack)
    exercise = make_exercise(db_session, lesson=lesson)
    db_session.add(UserProgress(user_id=child.id, lesson_id=lesson.id, status=ProgressStatus.COMPLETED, score=100))
    db_session.add(
        ExerciseResult(user_id=child.id, exercise_id=exercise.id, answer={"option_ids": ["a"]}, is_correct=True)
    )
    db_session.commit()
    assert db_session.query(ExerciseResult).filter(ExerciseResult.user_id == child.id).count() == 1

    headers = dev_login(client)
    response = client.delete(f"/api/v1/children/{child.id}", headers=headers)

    assert response.status_code in (200, 204), response.text
    assert db_session.query(User).filter(User.id == child.id).first() is None
    assert db_session.query(ExerciseResult).filter(ExerciseResult.user_id == child.id).count() == 0
    assert db_session.query(UserProgress).filter(UserProgress.user_id == child.id).count() == 0
