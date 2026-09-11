"""Politique de confidentialité côté famille (issue #21).

Ces tests décrivent ce qu'un parent observe : il peut lire la politique **avant**
de livrer quoi que ce soit, son acceptation est datée et versionnée en base, et
supprimer un compte efface réellement le travail scolaire qu'il promet d'effacer
— y compris les fichiers, et y compris les enfants que plus personne ne suit.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.progress import ExerciseResult, ProgressStatus, UserProgress
from app.models.user import Profile, User
from app.services.admin import delete_user
from app.services.family_privacy import current_policy_version
from app.services.guardianship import ROLE_PARENT, grant, is_guardian
from tests.helpers import (
    DEFAULT_PARENT_EMAIL,
    dev_login,
    ensure_parent,
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
    assert body["version"] == current_policy_version()
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
        json={"version": current_policy_version()},
        headers=headers,
    )

    assert accept.status_code == 200, accept.text
    assert accept.json()["accepted"] is True

    parent = db_session.query(User).filter(User.email == DEFAULT_PARENT_EMAIL).one()
    assert parent.privacy_version == current_policy_version()
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


def test_a_new_policy_version_asks_the_parent_again_and_can_be_satisfied(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """Une nouvelle version périme l'ancien consentement — et le parent peut en sortir.

    Le tour complet compte : redemander sans pouvoir accepter serait un blocage
    définitif (la case revient à chaque visite, l'acceptation reste sans effet).
    C'est exactement ce qui arrive si le texte servi, le refus 409 et
    ``privacy_accepted`` ne lisent pas la version au même endroit — d'où
    l'aller-retour complet plutôt qu'une seule assertion.
    """
    headers = dev_login(client)
    client.post("/api/v1/legal/privacy/accept", json={"version": current_policy_version()}, headers=headers)
    assert client.get("/api/v1/auth/me", headers=headers).json()["privacy_accepted"] is True

    monkeypatch.setattr(settings, "PRIVACY_POLICY_VERSION", "2099-12-31")

    # 1. On redemande le consentement, et le texte affiché porte la nouvelle version.
    assert client.get("/api/v1/auth/me", headers=headers).json()["privacy_accepted"] is False
    policy = client.get("/api/v1/legal/privacy", headers=headers).json()
    assert policy["version"] == "2099-12-31"
    assert policy["accepted"] is False

    # 2. L'ancienne version n'est plus acceptable.
    stale = client.post("/api/v1/legal/privacy/accept", json={"version": "2026-09-10"}, headers=headers)
    assert stale.status_code == 409, stale.text

    # 3. Accepter la version affichée débloque réellement le parent.
    accept = client.post("/api/v1/legal/privacy/accept", json={"version": policy["version"]}, headers=headers)
    assert accept.status_code == 200, accept.text
    assert client.get("/api/v1/auth/me", headers=headers).json()["privacy_accepted"] is True


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


def test_deleting_a_parent_takes_its_children_and_their_work_with_it(client: TestClient, db_session: Session):
    """« Ses enfants et leurs données sont supprimés avec lui » — promesse du point 9.

    ``profiles.parent_id`` est ``ON DELETE SET NULL`` : sans traitement
    explicite, le compte enfant et tout son travail scolaire survivraient en
    orphelins que plus aucun adulte ne peut voir ni effacer.
    """
    child = make_child(db_session, name="Léa")
    pack = make_pack(db_session)
    lesson = make_lesson(db_session, pack=pack)
    exercise = make_exercise(db_session, lesson=lesson)
    db_session.add(UserProgress(user_id=child.id, lesson_id=lesson.id, status=ProgressStatus.COMPLETED, score=100))
    db_session.add(
        ExerciseResult(user_id=child.id, exercise_id=exercise.id, answer={"option_ids": ["a"]}, is_correct=True)
    )
    db_session.commit()
    parent = db_session.query(User).filter(User.email == DEFAULT_PARENT_EMAIL).one()

    assert delete_user(db_session, parent.id) is True

    assert db_session.query(User).filter(User.id == parent.id).first() is None
    assert db_session.query(User).filter(User.id == child.id).first() is None
    assert db_session.query(Profile).filter(Profile.user_id == child.id).first() is None
    assert db_session.query(ExerciseResult).filter(ExerciseResult.user_id == child.id).count() == 0
    assert db_session.query(UserProgress).filter(UserProgress.user_id == child.id).count() == 0


def test_deleting_one_guardian_spares_a_child_another_adult_still_follows(db_session: Session):
    """La garde partagée borne la promesse : on n'efface pas l'enfant d'un autre.

    Le co-parent n'a rien demandé ; l'enfant reste le sien, avec sa progression,
    et le compte qui part perd seulement son accès.
    """
    child = make_child(db_session, name="Tom")
    pack = make_pack(db_session)
    lesson = make_lesson(db_session, pack=pack)
    exercise = make_exercise(db_session, lesson=lesson)
    db_session.add(
        ExerciseResult(user_id=child.id, exercise_id=exercise.id, answer={"option_ids": ["a"]}, is_correct=True)
    )
    owner = db_session.query(User).filter(User.email == DEFAULT_PARENT_EMAIL).one()
    coparent = ensure_parent(db_session, "coparent@qa.fr")
    grant(child.id, coparent.id, ROLE_PARENT, owner.id, db_session)
    db_session.commit()

    assert delete_user(db_session, owner.id) is True

    assert db_session.query(User).filter(User.id == child.id).first() is not None
    assert db_session.query(ExerciseResult).filter(ExerciseResult.user_id == child.id).count() == 1
    assert is_guardian(coparent.id, child.id, db_session) is True
    assert is_guardian(owner.id, child.id, db_session) is False


def test_deleting_a_child_removes_its_avatar_from_disk(
    client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    """L'image d'un enfant supprimé disparaît du disque, pas seulement de la base.

    ``/uploads`` est servi par ``StaticFiles`` : un fichier laissé sur place
    reste téléchargeable par quiconque connaît son URL, longtemps après la
    suppression promise « immédiate et définitive » au point 9.
    """
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    child = make_child(db_session, name="Nils")
    headers = dev_login(client)

    upload = client.post(
        f"/api/v1/children/{child.id}/avatar",
        headers=headers,
        files={"file": ("nils.png", b"fausse-image-png", "image/png")},
    )
    assert upload.status_code == 200, upload.text
    stored = tmp_path / "avatars" / upload.json()["avatar_url"].rsplit("/", 1)[1]
    assert stored.exists()

    response = client.delete(f"/api/v1/children/{child.id}", headers=headers)

    assert response.status_code in (200, 204), response.text
    assert db_session.query(User).filter(User.id == child.id).first() is None
    assert not stored.exists()
