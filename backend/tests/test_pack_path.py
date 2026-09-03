"""Chemin d'accueil orienté packs (issue #11).

Couvre l'accès (un pack communautaire non activé ne fuite ni dans le chemin, ni
dans la lentille « Matières », ni dans « Nouveautés »), la fidélité du verrou au
service de progression, le cumul qui permet la ligne trophée, et la résolution
serveur de la carte « Continuer ».
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import LevelEnum
from app.models.pack import ChildPackAccess, CommunityStatus, PackOrigin
from app.models.progress import ProgressStatus, UserProgress
from app.models.user import Profile
from app.services.pack_path import pack_path
from app.services.progression import lesson_locked
from tests.helpers import (
    child_headers,
    make_child,
    make_exercise,
    make_lesson,
    make_pack,
    make_subject,
)


def _complete(db: Session, child_id, lesson, *, stars: int = 3, when: datetime | None = None) -> UserProgress:
    """Marque une leçon terminée pour l'enfant (étoiles + horodatage)."""
    progress = UserProgress(
        user_id=child_id,
        lesson_id=lesson.id,
        status=ProgressStatus.COMPLETED,
        score=100,
        stars=stars,
        attempts=1,
        started_at=(when or datetime(2026, 1, 1, 8, 0)) - timedelta(minutes=5),
        completed_at=when or datetime(2026, 1, 1, 8, 0),
    )
    db.add(progress)
    db.flush()
    return progress


def _start(db: Session, child_id, lesson, *, when: datetime | None = None) -> UserProgress:
    """Marque une leçon entamée (sans complétion)."""
    progress = UserProgress(
        user_id=child_id,
        lesson_id=lesson.id,
        status=ProgressStatus.STARTED,
        score=0,
        stars=0,
        attempts=1,
        started_at=when or datetime(2026, 1, 2, 9, 0),
    )
    db.add(progress)
    db.flush()
    return progress


def test_path_contains_only_accessible_packs(client: TestClient, db_session: Session):
    child = make_child(db_session, name="Lila")
    official = make_pack(db_session, title="Officiel CP")
    make_lesson(db_session, pack=official, name="Officielle")
    stranger = make_pack(
        db_session,
        title="Pack d'un inconnu",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    make_lesson(db_session, pack=stranger, name="Inconnue")
    db_session.commit()

    r = client.get("/api/v1/packs/path", headers=child_headers(client, child))
    assert r.status_code == 200, r.text
    titles = [entry["pack"]["title"] for entry in r.json()["entries"]]
    assert titles == ["Officiel CP"]

    # Une fois l'accès posé par un garde, le pack apparaît.
    db_session.add(ChildPackAccess(child_id=child.id, pack_id=stranger.id, enabled=True))
    db_session.commit()
    r = client.get("/api/v1/packs/path", headers=child_headers(client, child))
    assert sorted(entry["pack"]["title"] for entry in r.json()["entries"]) == ["Officiel CP", "Pack d'un inconnu"]


def test_lock_state_comes_from_progression_service(client: TestClient, db_session: Session):
    child = make_child(db_session, name="Noé")
    pack = make_pack(db_session, title="Deux paliers")
    first = make_lesson(db_session, pack=pack, tier=1, name="Palier 1")
    second = make_lesson(db_session, pack=pack, tier=2, name="Palier 2")
    db_session.commit()

    response = pack_path(child.id, LevelEnum.CP, db_session)
    payload = {lesson.id: lesson.locked for lesson in response.entries[0].lessons}
    assert payload == {
        first.id: lesson_locked(child.id, first, LevelEnum.CP, db_session),
        second.id: lesson_locked(child.id, second, LevelEnum.CP, db_session),
    }
    assert payload[second.id] is True

    _complete(db_session, child.id, first)
    db_session.commit()

    response = pack_path(child.id, LevelEnum.CP, db_session)
    payload = {lesson.id: lesson.locked for lesson in response.entries[0].lessons}
    assert payload == {
        first.id: lesson_locked(child.id, first, LevelEnum.CP, db_session),
        second.id: lesson_locked(child.id, second, LevelEnum.CP, db_session),
    }
    assert payload[second.id] is False


def test_completed_pack_rollup_banks_stars_xp_and_date(client: TestClient, db_session: Session):
    child = make_child(db_session, name="Sami")
    pack = make_pack(db_session, title="Coupe du Monde")
    lessons = [make_lesson(db_session, pack=pack, tier=tier, name=f"L{tier}") for tier in (1, 2)]
    for lesson in lessons:
        lesson.xp_reward = 30
    db_session.flush()
    _complete(db_session, child.id, lessons[0], stars=3, when=datetime(2026, 2, 1, 10, 0))
    _complete(db_session, child.id, lessons[1], stars=2, when=datetime(2026, 2, 3, 11, 0))
    db_session.commit()

    r = client.get("/api/v1/packs/path", headers=child_headers(client, child))
    entry = r.json()["entries"][0]
    rollup = entry["rollup"]
    assert rollup["complete"] is True
    assert rollup["lessons_completed"] == 2
    assert rollup["lessons_total"] == 2
    assert rollup["stars_earned"] == 5
    assert rollup["stars_total"] == 6
    assert rollup["xp_banked"] == 60
    assert rollup["completed_at"].startswith("2026-02-03T11:00:00")
    # Décision 17 : le pack est replié par le client, jamais retiré par le
    # serveur — sinon le contenu de révision deviendrait inatteignable.
    assert len(entry["lessons"]) == 2
    assert [lesson["status"] for lesson in entry["lessons"]] == ["completed", "completed"]


def test_cross_subject_pack_carries_subject_badges(client: TestClient, db_session: Session):
    child = make_child(db_session, name="Iris")
    maths = make_subject(db_session, slug="maths", name="Mathématiques", icon="🔢")
    francais = make_subject(db_session, slug="francais", name="Français", icon="📖")
    pack = make_pack(db_session, title="Coupe du Monde ⚽")
    make_lesson(db_session, pack=pack, subject=maths, tier=1, name="Compter les buts")
    make_lesson(db_session, pack=pack, subject=francais, tier=1, name="Lire l'affiche")
    db_session.commit()

    r = client.get("/api/v1/packs/path", headers=child_headers(client, child))
    entry = r.json()["entries"][0]
    badges = {(lesson["subject_slug"], lesson["subject_name"], lesson["subject_icon"]) for lesson in entry["lessons"]}
    assert badges == {("maths", "Mathématiques", "🔢"), ("francais", "Français", "📖")}
    assert sorted(entry["pack"]["subject_icons"]) == ["📖", "🔢"]


def test_continuer_resumes_in_progress_pack(client: TestClient, db_session: Session):
    child = make_child(db_session, name="Théo")
    intact = make_pack(db_session, title="A — intact")
    make_lesson(db_session, pack=intact, tier=1, name="Jamais ouverte")
    entame = make_pack(db_session, title="B — entamé")
    done = make_lesson(db_session, pack=entame, tier=1, name="Faite")
    todo = make_lesson(db_session, pack=entame, tier=2, name="À faire")
    _complete(db_session, child.id, done)
    db_session.commit()

    r = client.get("/api/v1/packs/continuer", headers=child_headers(client, child))
    assert r.status_code == 200, r.text
    card = r.json()
    assert card["reason"] == "resume"
    assert card["pack_id"] == str(entame.id)
    assert card["lesson"]["id"] == str(todo.id)
    assert card["lesson"]["locked"] is False


def test_continuer_falls_back_to_least_advanced_pack(client: TestClient, db_session: Session):
    child = make_child(db_session, name="Zoé")
    first = make_pack(db_session, title="A — premier")
    first.order_index = 0
    lesson = make_lesson(db_session, pack=first, tier=1, name="Première")
    second = make_pack(db_session, title="B — second")
    second.order_index = 1
    make_lesson(db_session, pack=second, tier=1, name="Seconde")
    db_session.commit()

    card = client.get("/api/v1/packs/continuer", headers=child_headers(client, child)).json()
    assert card["reason"] == "start"
    assert card["pack_id"] == str(first.id)
    assert card["lesson"]["id"] == str(lesson.id)


def test_continuer_is_none_when_nothing_is_available(client: TestClient, db_session: Session):
    child = make_child(db_session, name="Hugo")
    pack = make_pack(db_session, title="Tout terminé")
    lesson = make_lesson(db_session, pack=pack, tier=1, name="Finie")
    _complete(db_session, child.id, lesson)
    db_session.commit()

    r = client.get("/api/v1/packs/continuer", headers=child_headers(client, child))
    assert r.status_code == 200, r.text
    assert r.json() is None

    body = client.get("/api/v1/packs/path", headers=child_headers(client, child)).json()
    assert body["continuer"] is None
    assert body["entries"][0]["rollup"]["complete"] is True


def test_lens_toggle_round_trips_per_child(client: TestClient, db_session: Session):
    first = make_child(db_session, name="Ana")
    second = make_child(db_session, name="Bob")
    db_session.commit()

    assert client.get("/api/v1/packs/path", headers=child_headers(client, first)).json()["lens"] == "themes"

    r = client.put("/api/v1/packs/lens", json={"lens": "matieres"}, headers=child_headers(client, first))
    assert r.status_code == 200, r.text
    assert r.json() == {"lens": "matieres"}

    assert client.get("/api/v1/packs/path", headers=child_headers(client, first)).json()["lens"] == "matieres"
    # La bascule est par enfant : le frère garde la lentille par défaut.
    assert client.get("/api/v1/packs/path", headers=child_headers(client, second)).json()["lens"] == "themes"
    assert db_session.query(Profile).filter(Profile.user_id == second.id).first().pack_lens == "themes"

    r = client.put("/api/v1/packs/lens", json={"lens": "bidon"}, headers=child_headers(client, first))
    assert r.status_code == 422, r.text


def test_pack_entry_endpoint_hides_inaccessible_pack(client: TestClient, db_session: Session):
    child = make_child(db_session, name="Emma")
    mine = make_pack(db_session, title="Le mien")
    make_lesson(db_session, pack=mine, name="Ok")
    stranger = make_pack(
        db_session,
        title="Pas le mien",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    make_lesson(db_session, pack=stranger, name="Cachée")
    db_session.commit()

    headers = child_headers(client, child)
    assert client.get(f"/api/v1/packs/{mine.id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/packs/{stranger.id}", headers=headers).status_code == 404


def test_subject_lessons_hide_community_pack_until_access(client: TestClient, db_session: Session):
    child = make_child(db_session, name="Léo")
    subject = make_subject(db_session)
    official = make_pack(db_session, title="Officiel")
    make_lesson(db_session, pack=official, subject=subject, name="Officielle")
    community = make_pack(
        db_session,
        title="Communautaire",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    make_lesson(db_session, pack=community, subject=subject, name="Communautaire")
    db_session.commit()

    headers = child_headers(client, child)
    r = client.get(f"/api/v1/subjects/{subject.id}/lessons", headers=headers)
    assert r.status_code == 200, r.text
    assert [lesson["name"] for lesson in r.json()] == ["Officielle"]

    db_session.add(ChildPackAccess(child_id=child.id, pack_id=community.id, enabled=True))
    db_session.commit()
    r = client.get(f"/api/v1/subjects/{subject.id}/lessons", headers=headers)
    assert sorted(lesson["name"] for lesson in r.json()) == ["Communautaire", "Officielle"]


def test_recent_lessons_hide_community_pack_until_access(client: TestClient, db_session: Session):
    child = make_child(db_session, name="Maya")
    official = make_pack(db_session, title="Officiel")
    make_lesson(db_session, pack=official, name="Officielle")
    community = make_pack(
        db_session,
        title="Communautaire",
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.APPROVED,
    )
    make_lesson(db_session, pack=community, name="Communautaire")
    db_session.commit()

    headers = child_headers(client, child)
    r = client.get("/api/v1/lessons/recent", headers=headers)
    assert r.status_code == 200, r.text
    assert [lesson["name"] for lesson in r.json()] == ["Officielle"]

    db_session.add(ChildPackAccess(child_id=child.id, pack_id=community.id, enabled=True))
    db_session.commit()
    r = client.get("/api/v1/lessons/recent", headers=headers)
    assert sorted(lesson["name"] for lesson in r.json()) == ["Communautaire", "Officielle"]


def test_path_reports_exercise_count_and_started_lesson(client: TestClient, db_session: Session):
    child = make_child(db_session, name="Jules")
    pack = make_pack(db_session, title="Avec exercices")
    lesson = make_lesson(db_session, pack=pack, tier=1, name="Entamée")
    make_exercise(db_session, lesson=lesson, order_index=0)
    make_exercise(db_session, lesson=lesson, order_index=1)
    _start(db_session, child.id, lesson)
    db_session.commit()

    entry = client.get("/api/v1/packs/path", headers=child_headers(client, child)).json()["entries"][0]
    assert entry["lessons"][0]["exercise_count"] == 2
    assert entry["lessons"][0]["status"] == "started"
    assert entry["lessons"][0]["xp_earned"] == 0
    assert entry["rollup"]["complete"] is False
