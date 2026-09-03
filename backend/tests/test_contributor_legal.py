"""Tests de l'appareil juridique de la contribution (issue #19).

Quatre propriétés, toutes non négociables dès qu'on accepte du contenu
d'inconnus dans une application pour enfants : le pseudonyme ne fuit pas
l'identité réelle, l'acceptation des conditions est datée et versionnée, un
signalement de parent atteint la modération et peut bloquer, et une suppression
de compte RGPD ne détruit pas la progression d'une autre famille.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Exercise, Lesson, LevelEnum
from app.models.contribution import ContributorProfile, PackReport
from app.models.pack import ChildPackAccess, CommunityStatus, PackOrigin
from app.models.progress import ExerciseResult, ProgressStatus, UserProgress
from app.models.user import Profile, User
from app.services.admin import delete_user
from app.services.contributor_legal import (
    ANONYMOUS_AUTHOR_HANDLE,
    CONTRIBUTOR_TERMS,
    ReportReason,
    record_terms_acceptance,
    terms_accepted,
    validate_handle,
)
from app.services.moderation import queue
from app.services.packs import accessible_pack_ids
from tests.helpers import ensure_parent, make_child, make_exercise, make_lesson, make_pack, make_subject

MOD_TOKEN = "jeton-moderation-de-test"
AUTHOR_EMAIL = "jean.dupont@qa.fr"


@pytest.fixture
def mod_headers(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """En-têtes du jeton de modération, avec la configuration qui l'active."""
    monkeypatch.setattr(settings, "MODERATION_TOKEN", MOD_TOKEN)
    return {"X-Moderation-Token": MOD_TOKEN}


def _contributor(db: Session, email: str, handle: str) -> tuple[User, ContributorProfile]:
    user = ensure_parent(db, email)
    profile = ContributorProfile(user_id=user.id, handle=handle)
    db.add(profile)
    db.commit()
    return user, profile


def test_handles_are_validated_and_unique(db_session: Session):
    author = ensure_parent(db_session, AUTHOR_EMAIL)
    profile = db_session.query(Profile).filter(Profile.user_id == author.id).first()
    profile.display_name = "Jean Dupont"
    db_session.commit()

    assert validate_handle(db_session, "  Prof  Dino ", user=author) == "Prof Dino"
    # Pseudonyme généré à la volée par le flux de contribution.
    assert validate_handle(db_session, "Parent-a1b2c3", user=author) == "Parent-a1b2c3"

    for invalid in ("ab", "x" * 25, "prof@dino.fr", "Prof.Dino", "Explorito", ANONYMOUS_AUTHOR_HANDLE):
        with pytest.raises(HTTPException) as exc:
            validate_handle(db_session, invalid, user=author)
        assert exc.value.status_code == 422, invalid

    # Ni l'adresse email ni le nom Google ne peuvent servir de pseudonyme : le
    # pseudonymat est la seule protection de l'identité de la famille.
    for identity in ("jean.dupont", "JeanDupont", "Jean Dupont"):
        with pytest.raises(HTTPException) as exc:
            validate_handle(db_session, identity, user=author)
        assert exc.value.status_code == 422, identity

    other, _ = _contributor(db_session, "autre@qa.fr", "Prof Dino")
    with pytest.raises(HTTPException) as exc:
        validate_handle(db_session, "prof dino", user=author)
    assert exc.value.status_code == 409
    # Idempotent pour son propriétaire : réenvoyer son propre pseudonyme est licite.
    assert validate_handle(db_session, "Prof Dino", user=other) == "Prof Dino"


def test_terms_acceptance_is_recorded_with_version_and_timestamp(db_session: Session):
    _user, profile = _contributor(db_session, "contrib@qa.fr", "Prof Dino")
    assert terms_accepted(profile) is False

    record_terms_acceptance(profile)
    db_session.commit()
    db_session.refresh(profile)
    assert profile.terms_version == settings.CONTRIBUTOR_TERMS_VERSION
    assert profile.terms_accepted_at is not None
    assert terms_accepted(profile) is True

    # Une version périmée vaut refus : le texte de licence a changé.
    profile.terms_version = "2020-01-01"
    assert terms_accepted(profile) is False


def test_terms_state_the_two_load_bearing_clauses(db_session: Session):
    """La licence de modification et la survie anonymisée doivent être écrites.

    Sans la première, l'admin ne peut pas corriger un pack à la revue ; sans la
    seconde, une demande de suppression ne peut pas être honorée sans effacer la
    progression d'enfants d'autres familles.
    """
    assert "modifier" in CONTRIBUTOR_TERMS
    assert "anonymisés" in CONTRIBUTOR_TERMS
    assert settings.CONTRIBUTOR_TERMS_VERSION in CONTRIBUTOR_TERMS


def test_report_reaches_the_queue_and_can_drive_blocked(
    client: TestClient, db_session: Session, mod_headers: dict[str, str]
):
    author, _profile = _contributor(db_session, AUTHOR_EMAIL, "Prof Dino")
    subject = make_subject(db_session)
    pack = make_pack(
        db_session,
        title="Les vacances d'Arthur a Biarritz",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
        handle="Prof Dino",
    )
    lesson = make_lesson(db_session, pack=pack, subject=subject, level=LevelEnum.CP)
    make_exercise(db_session, lesson=lesson)
    child = make_child(db_session, parent_email="autre@qa.fr", name="Lila")
    db_session.add(ChildPackAccess(child_id=child.id, pack_id=pack.id, enabled=True))
    report = PackReport(
        pack_id=pack.id,
        reporter_id=child.id,
        reason=ReportReason.PERSONAL_DATA.value,
        details="Prénom d'un enfant réel et ville.",
    )
    db_session.add(report)
    db_session.commit()

    rows = client.get("/api/v1/moderation/reports", headers=mod_headers).json()
    assert [row["reason"] for row in rows] == ["personal_data"]
    assert rows[0]["pack_title"] == "Les vacances d'Arthur a Biarritz"

    r = client.patch(
        f"/api/v1/moderation/reports/{report.id}",
        json={"status": "actioned", "block_pack": True},
        headers=mod_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "actioned"

    db_session.refresh(pack)
    assert pack.community_status == CommunityStatus.BLOCKED.value
    assert pack.id not in (accessible_pack_ids(child.id, LevelEnum.CP, db_session) or set())
    assert [entry["id"] for entry in queue(db_session, status=CommunityStatus.BLOCKED)] == [pack.id]


def test_author_deletion_anonymises_packs_and_preserves_other_family_progress(db_session: Session):
    author, _profile = _contributor(db_session, AUTHOR_EMAIL, "Prof Dino")
    subject = make_subject(db_session)
    # `handle=None` : le pseudonyme doit être rebasculé sur le pack au moment de
    # l'anonymisation, sinon l'attribution disparaît avec le compte.
    pack = make_pack(
        db_session,
        title="Dinosaures",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
    )
    lesson = make_lesson(db_session, pack=pack, subject=subject, level=LevelEnum.CP)
    exercise = make_exercise(db_session, lesson=lesson)
    other_child = make_child(db_session, parent_email="autre@qa.fr", name="Lila")
    db_session.add(ChildPackAccess(child_id=other_child.id, pack_id=pack.id, enabled=True))
    db_session.add(
        UserProgress(
            user_id=other_child.id,
            lesson_id=lesson.id,
            status=ProgressStatus.COMPLETED,
            score=100,
            stars=3,
            attempts=1,
        )
    )
    db_session.add(
        ExerciseResult(
            user_id=other_child.id,
            exercise_id=exercise.id,
            answer={"option_ids": ["a"]},
            is_correct=True,
        )
    )
    db_session.commit()

    before = (
        db_session.query(UserProgress).filter(UserProgress.user_id == other_child.id).count(),
        db_session.query(ExerciseResult).filter(ExerciseResult.user_id == other_child.id).count(),
    )
    assert before == (1, 1)

    assert delete_user(db_session, author.id) is True

    assert db_session.query(User).filter(User.id == author.id).first() is None
    db_session.refresh(pack)
    assert pack.author_id is None
    assert pack.author_handle == "Prof Dino"
    assert pack.community_status == CommunityStatus.APPROVED.value
    # La progression d'une autre famille est intacte, contenu inclus.
    assert (
        db_session.query(UserProgress).filter(UserProgress.user_id == other_child.id).count(),
        db_session.query(ExerciseResult).filter(ExerciseResult.user_id == other_child.id).count(),
    ) == before
    assert db_session.query(Lesson).filter(Lesson.id == lesson.id).first() is not None
    assert db_session.query(Exercise).filter(Exercise.id == exercise.id).first() is not None
    assert pack.id in (accessible_pack_ids(other_child.id, LevelEnum.CP, db_session) or set())


def test_anonymised_pack_without_handle_falls_back_to_a_pseudonym(db_session: Session):
    """Sans profil de contributeur, l'attribution retombe sur un pseudonyme neutre.

    Jamais l'email ni le nom Google : l'anonymisation ne doit pas publier ce que
    le pseudonymat protégeait.
    """
    author = ensure_parent(db_session, "sans.profil@qa.fr")
    pack = make_pack(
        db_session,
        title="Orphelin",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
        author=author,
    )
    db_session.commit()

    assert delete_user(db_session, author.id) is True
    db_session.refresh(pack)
    assert pack.author_id is None
    assert pack.author_handle == ANONYMOUS_AUTHOR_HANDLE


def test_no_contact_route_between_families(client: TestClient):
    """Aucune surface de contact : ni messagerie, ni abonnement, ni page profil.

    Deux familles capables de communiquer via une application pour enfants en
    feraient un produit de sécurité enfance, plus un produit éducatif.
    """
    paths = {route.path for route in client.app.routes}
    # Comparaison par segment : « admin » contient « dm ».
    segments = {segment for path in paths for segment in path.lower().split("/")}
    assert not segments & {"messages", "message", "chat", "dm", "dms", "follow", "followers", "following", "inbox"}
    # Les contributeurs ne sont listés que derrière la modération.
    assert {path for path in paths if "contributors" in path} <= {
        "/api/v1/moderation/contributors",
        "/api/v1/moderation/contributors/{user_id}/trust",
    }
