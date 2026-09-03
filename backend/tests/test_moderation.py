"""Tests de la modération : jeton restreint, verdicts, verrou, audit.

Ce qui est vérifié ici n'est pas « l'endpoint répond 200 » mais les propriétés
qui rendent la fonctionnalité défendable : un jeton qui fuit ne peut pas
supprimer de compte, un refus communautaire ne coûte rien à la famille de
l'auteur, un blocage ne détruit aucune progression, et aucun verdict n'apparaît
sans qu'un humain l'ait prononcé.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Exercise, Lesson, LevelEnum
from app.models.contribution import ContributorProfile, PackAuditLog, PackReport, ReportStatus
from app.models.pack import ChildPackAccess, CommunityStatus, Pack, PackOrigin
from app.models.progress import ExerciseResult, ProgressStatus, UserProgress
from app.models.user import User
from app.services.contributor_legal import ReportReason
from app.services.gamification import award_xp, total_xp_for
from app.services.moderation import queue
from app.services.packs import accessible_pack_ids
from tests.helpers import (
    dev_login,
    ensure_parent,
    make_child,
    make_exercise,
    make_lesson,
    make_pack,
    make_subject,
)

MOD_TOKEN = "jeton-moderation-de-test"
AUTHOR_EMAIL = "auteur@qa.fr"


@pytest.fixture
def mod_headers(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """En-têtes du jeton de modération, avec la configuration qui l'active."""
    monkeypatch.setattr(settings, "MODERATION_TOKEN", MOD_TOKEN)
    return {"X-Moderation-Token": MOD_TOKEN}


def _authored_pack(
    db: Session,
    *,
    community_status: CommunityStatus = CommunityStatus.PENDING,
    locked: bool = False,
    ratified: bool = False,
) -> tuple[User, User, Pack, Lesson, Exercise]:
    """Un pack communautaire avec son auteur, l'enfant de l'auteur et son contenu."""
    author = ensure_parent(db, AUTHOR_EMAIL)
    child = make_child(db, parent_email=AUTHOR_EMAIL, name="Momo")
    subject = make_subject(db)
    pack = make_pack(
        db,
        title="Dinosaures",
        origin=PackOrigin.COMMUNITY,
        community_status=community_status,
        level=LevelEnum.CP,
        author=author,
        difficulty_ratified=ratified,
        locked=locked,
        handle="TRex",
    )
    lesson = make_lesson(db, pack=pack, subject=subject, level=LevelEnum.CP)
    exercise = make_exercise(db, lesson=lesson)
    db.commit()
    return author, child, pack, lesson, exercise


def _work_done(db: Session, child: User, lesson: Lesson, exercise: Exercise) -> None:
    """Simule du travail fait par un enfant sur le pack (progression + XP).

    On écrit les lignes directement : ce test porte sur ce qu'un verdict
    *préserve*, pas sur le chemin de notation.
    """
    subject = make_subject(db)
    db.add(
        UserProgress(
            user_id=child.id,
            lesson_id=lesson.id,
            status=ProgressStatus.COMPLETED,
            score=100,
            stars=3,
            attempts=1,
        )
    )
    db.add(
        ExerciseResult(
            user_id=child.id,
            exercise_id=exercise.id,
            answer={"option_ids": ["a"]},
            is_correct=True,
        )
    )
    db.commit()
    award_xp(child.id, 20, subject.id, db)


def _counts(db: Session, child: User) -> tuple[int, int, int]:
    """(progressions, résultats, accès) d'un enfant — l'empreinte à préserver."""
    return (
        db.query(UserProgress).filter(UserProgress.user_id == child.id).count(),
        db.query(ExerciseResult).filter(ExerciseResult.user_id == child.id).count(),
        db.query(ChildPackAccess).filter(ChildPackAccess.child_id == child.id).count(),
    )


def test_moderation_token_opens_only_the_moderation_surface(
    client: TestClient, db_session: Session, mod_headers: dict[str, str]
):
    author, _child, _pack, _lesson, _exercise = _authored_pack(db_session)

    r = client.get("/api/v1/moderation/queue", headers=mod_headers)
    assert r.status_code == 200, r.text
    assert [item["title"] for item in r.json()["items"]] == ["Dinosaures"]

    # Le même jeton ne vaut rien ailleurs : ni lecture des comptes…
    assert client.get("/api/v1/admin/users", headers=mod_headers).status_code == 401
    # …ni suppression de compte — le scénario que le cloisonnement borne.
    assert client.delete(f"/api/v1/admin/users/{author.id}", headers=mod_headers).status_code == 401
    assert db_session.query(User).filter(User.id == author.id).first() is not None

    assert client.get("/api/v1/moderation/queue", headers={"X-Moderation-Token": "faux"}).status_code == 403
    assert client.get("/api/v1/moderation/queue").status_code == 401


def test_empty_moderation_token_disables_the_header_path(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    """Sans jeton configuré, l'en-tête n'ouvre rien : « vide == vide » n'est pas une preuve."""
    monkeypatch.setattr(settings, "MODERATION_TOKEN", "")
    assert client.get("/api/v1/moderation/queue", headers={"X-Moderation-Token": ""}).status_code == 401
    assert client.get("/api/v1/moderation/queue", headers={"X-Moderation-Token": "quoi-que-ce-soit"}).status_code == 403


def test_approval_ratifies_difficulty_and_locks_the_pack(
    client: TestClient, db_session: Session, mod_headers: dict[str, str]
):
    _author, _child, pack, _lesson, _exercise = _authored_pack(db_session)

    r = client.patch(
        f"/api/v1/moderation/packs/{pack.id}",
        json={"verdict": "approved", "notes": "Impeccable.", "quality_score": 88},
        headers=mod_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["community_status"] == "approved"
    assert body["difficulty_ratified"] is True
    assert body["locked"] is True

    db_session.refresh(pack)
    assert pack.quality_score == 88
    assert pack.review_notes == "Impeccable."
    assert pack.reviewed_at is not None


def test_rejected_leaves_the_author_family_untouched(
    client: TestClient, db_session: Session, mod_headers: dict[str, str]
):
    author, child, pack, lesson, exercise = _authored_pack(db_session)
    db_session.add(ChildPackAccess(child_id=child.id, pack_id=pack.id, enabled=True, enabled_by=author.id))
    db_session.commit()
    _work_done(db_session, child, lesson, exercise)

    before_xp = total_xp_for(child.id, db_session)
    before_counts = _counts(db_session, child)
    assert before_xp > 0 and before_counts == (1, 1, 1)

    r = client.patch(
        f"/api/v1/moderation/packs/{pack.id}",
        json={"verdict": "rejected", "notes": "Hors programme."},
        headers=mod_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["community_status"] == "rejected"

    assert total_xp_for(child.id, db_session) == before_xp
    assert _counts(db_session, child) == before_counts
    # Et le pack reste utilisable par l'enfant de l'auteur : on n'est pas la
    # police du programme scolaire de l'enfant de quelqu'un d'autre.
    assert pack.id in (accessible_pack_ids(child.id, LevelEnum.CP, db_session) or set())


def test_blocked_hides_everywhere_and_deletes_nothing(
    client: TestClient, db_session: Session, mod_headers: dict[str, str]
):
    author, child, pack, lesson, exercise = _authored_pack(db_session, community_status=CommunityStatus.APPROVED)
    other_child = make_child(db_session, parent_email="autre@qa.fr", name="Lila")
    db_session.add(ChildPackAccess(child_id=other_child.id, pack_id=pack.id, enabled=True))
    db_session.commit()
    _work_done(db_session, other_child, lesson, exercise)
    before_counts = _counts(db_session, other_child)

    r = client.patch(
        f"/api/v1/moderation/packs/{pack.id}",
        json={"verdict": "blocked", "notes": "Contenu nuisible."},
        headers=mod_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["community_status"] == "blocked"

    # Masqué partout : la visibilité de toutes les surfaces enfant est dérivée
    # de ce résolveur, auteur compris.
    assert pack.id not in (accessible_pack_ids(child.id, LevelEnum.CP, db_session) or set())
    assert pack.id not in (accessible_pack_ids(other_child.id, LevelEnum.CP, db_session) or set())

    # Et rien n'est supprimé : contenu, progression et résultats survivent.
    assert _counts(db_session, other_child) == before_counts
    assert db_session.query(Lesson).filter(Lesson.id == lesson.id).first() is not None
    assert db_session.query(Exercise).filter(Exercise.id == exercise.id).first() is not None
    assert [entry["id"] for entry in queue(db_session, status=CommunityStatus.BLOCKED)] == [pack.id]


def test_admin_edit_of_a_locked_pack_succeeds_and_is_audited(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "chef@qa.fr")
    headers = dev_login(client, "chef@qa.fr")
    admin = db_session.query(User).filter(User.email == "chef@qa.fr").first()
    _author, _child, pack, _lesson, _exercise = _authored_pack(
        db_session, community_status=CommunityStatus.APPROVED, locked=True, ratified=True
    )

    r = client.patch(
        f"/api/v1/moderation/packs/{pack.id}",
        json={"changes": {"title": "Les dinosaures", "emoji": "🦖"}},
        headers=headers,
    )
    assert r.status_code == 200, r.text

    db_session.refresh(pack)
    assert pack.title == "Les dinosaures" and pack.emoji == "🦖"
    # Le verrou protège le pack de son auteur, pas de l'admin.
    assert pack.locked is True

    row = db_session.query(PackAuditLog).filter(PackAuditLog.action == "admin_edit").one()
    assert row.actor_id == admin.id
    assert row.detail["locked"] is True
    assert row.detail["fields"]["title"] == {"before": "Dinosaures", "after": "Les dinosaures"}
    assert row.detail["fields"]["emoji"] == {"before": None, "after": "🦖"}


def test_a_verdict_the_admin_did_not_give_is_never_written(
    client: TestClient, db_session: Session, mod_headers: dict[str, str]
):
    _author, _child, pack, _lesson, _exercise = _authored_pack(db_session)

    r = client.patch(
        f"/api/v1/moderation/packs/{pack.id}",
        json={"changes": {"description": "Du Trias au Crétacé."}, "notes": "note de relecture"},
        headers=mod_headers,
    )
    assert r.status_code == 200, r.text

    db_session.refresh(pack)
    assert pack.description == "Du Trias au Crétacé."
    assert pack.community_status == CommunityStatus.PENDING.value
    assert pack.reviewed_at is None and pack.review_notes is None
    assert db_session.query(PackAuditLog).filter(PackAuditLog.action == "verdict").count() == 0


def test_queue_exposes_clone_lineage_open_reports_and_full_content(
    client: TestClient, db_session: Session, mod_headers: dict[str, str]
):
    """La lignée évite de relire de zéro une révision de pack déjà approuvé."""
    _author, _child, pack, _lesson, _exercise = _authored_pack(db_session)
    original = make_pack(
        db_session,
        title="Dinosaures (v1)",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    pack.cloned_from_pack_id = original.id
    db_session.add(PackReport(pack_id=pack.id, reason=ReportReason.WRONG_CONTENT.value, status=ReportStatus.OPEN.value))
    db_session.commit()

    entry = client.get("/api/v1/moderation/queue", headers=mod_headers).json()["items"][0]
    assert entry["cloned_from_pack_id"] == str(original.id)
    assert entry["cloned_from_title"] == "Dinosaures (v1)"
    assert entry["open_reports"] == 1
    assert entry["lesson_count"] == 1 and entry["exercise_count"] == 1
    assert entry["author_handle"] == "TRex"

    detail = client.get(f"/api/v1/moderation/packs/{pack.id}", headers=mod_headers).json()
    assert detail["cloned_from_title"] == "Dinosaures (v1)"
    assert [report["reason"] for report in detail["reports"]] == ["wrong_content"]
    # L'admin doit pouvoir vérifier l'arithmétique : les exercices sont là.
    assert detail["lessons"][0]["exercises"][0]["question"] == "1+1 ?"


def test_trust_is_explicit_revocable_and_never_automatic(
    client: TestClient, db_session: Session, mod_headers: dict[str, str]
):
    """Atteindre le seuil rend *éligible*, jamais confiant : la barrière reste humaine."""
    author = ensure_parent(db_session, AUTHOR_EMAIL)
    db_session.add(ContributorProfile(user_id=author.id, handle="TRex"))
    for index in range(settings.PACK_TRUST_THRESHOLD):
        make_pack(
            db_session,
            title=f"Pack {index}",
            origin=PackOrigin.COMMUNITY,
            community_status=CommunityStatus.APPROVED,
            author=author,
        )
    db_session.commit()

    row = client.get("/api/v1/moderation/contributors", headers=mod_headers).json()[0]
    assert row["approved_packs"] == settings.PACK_TRUST_THRESHOLD
    assert row["trust_eligible"] is True and row["trusted"] is False

    granted = client.post(
        f"/api/v1/moderation/contributors/{author.id}/trust", json={"trusted": True}, headers=mod_headers
    )
    assert granted.status_code == 200, granted.text
    assert granted.json()["trusted"] is True and granted.json()["trusted_at"] is not None
    assert db_session.query(PackAuditLog).filter(PackAuditLog.action == "trust_granted").count() == 1

    revoked = client.post(
        f"/api/v1/moderation/contributors/{author.id}/trust", json={"trusted": False}, headers=mod_headers
    )
    assert revoked.status_code == 200 and revoked.json()["trusted"] is False
    assert db_session.query(PackAuditLog).filter(PackAuditLog.action == "trust_revoked").count() == 1
