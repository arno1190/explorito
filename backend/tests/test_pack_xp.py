"""
Tests de l'XP dérivée côté serveur et du tarif forfaitaire (issue #10).

Les étiquettes ``difficulty_level`` viennent de l'auteur du pack, et l'XP achète
des collectionnables : un pack non ratifié serait donc une imprimante à billets
(15 exercices triviaux déclarés en difficulté 5). Tant qu'un humain n'a pas
ratifié la difficulté à la revue, chaque exercice paie ``XP_PER_EXERCISE``.

Auth : parent (dev-login) incarnant l'enfant via ``X-Acting-Child-Id``.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import LevelEnum
from app.models.pack import CommunityStatus, Pack, PackOrigin
from app.models.progress import SubjectProgress
from app.services.gamification import xp_for_exercise
from tests.helpers import (
    child_headers,
    make_child,
    make_exercise,
    make_lesson,
    make_pack,
    make_subject,
)


def _community_pack(db: Session, *, ratified: bool = False, title: str = "Pack communautaire") -> Pack:
    return make_pack(
        db,
        title=title,
        origin=PackOrigin.COMMUNITY,
        community_status=CommunityStatus.PENDING,
        level=LevelEnum.CP,
        difficulty_ratified=ratified,
    )


def _submit(client: TestClient, ex_id, h: dict[str, str]) -> dict:
    r = client.post(f"/api/v1/exercises/{ex_id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def test_unratified_pack_pays_flat_xp(client: TestClient, db_session: Session):
    """Un exercice déclaré en difficulté 5 dans un pack non ratifié paie le tarif forfaitaire."""
    child = make_child(db_session, level=LevelEnum.CP)
    subject = make_subject(db_session)
    pack = _community_pack(db_session)
    lesson = make_lesson(db_session, pack=pack, subject=subject, tier=1, name="Trivial")
    ex = make_exercise(db_session, lesson=lesson, difficulty_level=5)
    db_session.commit()

    assert settings.XP_BY_LEVEL[5] > settings.XP_PER_EXERCISE  # sinon le test ne prouve rien
    assert xp_for_exercise(ex, pack) == settings.XP_PER_EXERCISE

    h = child_headers(client, child)
    assert _submit(client, ex.id, h)["xp_awarded"] == settings.XP_PER_EXERCISE


def test_ratification_raises_subsequent_awards(client: TestClient, db_session: Session):
    """Après ratification, les attributions *suivantes* repassent au tarif gradué."""
    child = make_child(db_session, level=LevelEnum.CP)
    subject = make_subject(db_session)
    pack = _community_pack(db_session)
    lesson = make_lesson(db_session, pack=pack, subject=subject, tier=1, name="Deux exos")
    first = make_exercise(db_session, lesson=lesson, order_index=0, difficulty_level=5)
    second = make_exercise(db_session, lesson=lesson, order_index=1, difficulty_level=5)
    db_session.commit()

    h = child_headers(client, child)
    assert _submit(client, first.id, h)["xp_awarded"] == settings.XP_PER_EXERCISE

    pack.difficulty_ratified = True
    db_session.commit()

    assert _submit(client, second.id, h)["xp_awarded"] == settings.XP_BY_LEVEL[5]


def test_ratification_does_not_rewrite_awarded_xp(client: TestClient, db_session: Session):
    """La ratification n'est pas rétroactive : l'XP déjà attribuée reste au tarif forfaitaire."""
    child = make_child(db_session, level=LevelEnum.CP)
    subject = make_subject(db_session)
    pack = _community_pack(db_session)
    lesson = make_lesson(db_session, pack=pack, subject=subject, tier=1, name="Un exo")
    ex = make_exercise(db_session, lesson=lesson, difficulty_level=5)
    db_session.commit()

    h = child_headers(client, child)
    _submit(client, ex.id, h)
    total_before = client.get("/api/v1/progress/me", headers=h).json()["total_xp"]
    assert total_before == settings.XP_PER_EXERCISE
    # L'XP est cumulée dans SubjectProgress, jamais recalculée depuis les difficultés.
    stored_before = [row.total_xp for row in db_session.query(SubjectProgress).all()]
    assert stored_before == [settings.XP_PER_EXERCISE]

    pack.difficulty_ratified = True
    db_session.commit()

    total_after = client.get("/api/v1/progress/me", headers=h).json()["total_xp"]
    assert total_after == total_before
    db_session.expire_all()
    assert [row.total_xp for row in db_session.query(SubjectProgress).all()] == stored_before

    # Refaire l'exercice déjà réussi reste à zéro (anti-farm), la ratification n'y change rien.
    assert _submit(client, ex.id, h)["xp_awarded"] == 0


def test_money_printer_payload_yields_flat_xp(client: TestClient, db_session: Session):
    """Charge utile « imprimante à billets » : 15 exercices en difficulté 5, non ratifiés."""
    child = make_child(db_session, level=LevelEnum.CP)
    subject = make_subject(db_session)
    pack = _community_pack(db_session, title="Imprimante")
    lesson = make_lesson(db_session, pack=pack, subject=subject, tier=1, name="Farm")
    exercises = [
        make_exercise(db_session, lesson=lesson, order_index=i, difficulty_level=5, question=f"q{i} ?")
        for i in range(15)
    ]
    db_session.commit()

    h = child_headers(client, child)
    awarded = [_submit(client, ex.id, h)["xp_awarded"] for ex in exercises]
    assert awarded == [settings.XP_PER_EXERCISE] * 15
    # Le total reste celui du tarif forfaitaire, sans bonus de leçon déclaré par l'auteur.
    assert client.get("/api/v1/progress/me", headers=h).json()["total_xp"] == 15 * settings.XP_PER_EXERCISE


def test_ratified_pack_pays_graded_xp(client: TestClient, db_session: Session):
    """Contrôle : le contenu ratifié (packs officiels) garde la pondération par difficulté."""
    child = make_child(db_session, level=LevelEnum.CP)
    subject = make_subject(db_session)
    pack = make_pack(db_session, title="Officiel CP", level=LevelEnum.CP)  # ratifié par défaut
    lesson = make_lesson(db_session, pack=pack, subject=subject, tier=1, name="Officielle")
    ex = make_exercise(db_session, lesson=lesson, difficulty_level=5)
    db_session.commit()

    h = child_headers(client, child)
    assert _submit(client, ex.id, h)["xp_awarded"] == settings.XP_BY_LEVEL[5]


def test_announced_lesson_xp_matches_what_the_child_will_earn(client: TestClient, db_session: Session):
    """L'XP *annoncée* d'une leçon suit le tarif réellement payé, avant et après ratification.

    Régression : ``derive_lesson_xp`` graduait la difficulté déclarée même sur un
    pack non ratifié, si bien qu'une leçon de 5 exercices marqués « difficulté 5 »
    affichait « +150 XP » alors que l'enfant en gagnait 50. L'écran promettait la
    récompense que l'issue #10 vient précisément de fermer.
    """
    from app.models.content import Lesson
    from app.services.moderation import apply_verdict
    from app.services.packs import derive_lesson_xp

    difficulties = [5, 5, 5, 5, 5]
    assert derive_lesson_xp(difficulties, ratified=False) == 5 * settings.XP_PER_EXERCISE
    assert derive_lesson_xp(difficulties, ratified=True) == 5 * settings.XP_BY_LEVEL[5]

    subject = make_subject(db_session)
    pack = _community_pack(db_session, ratified=False, title="Additions faciles")
    lesson = make_lesson(db_session, pack=pack, subject=subject, tier=1, name="Additions")
    for index, level in enumerate(difficulties):
        make_exercise(db_session, lesson=lesson, order_index=index, difficulty_level=level)
    from app.services.packs import refresh_pack_lesson_xp

    refresh_pack_lesson_xp(db_session, pack)
    db_session.commit()

    stored = db_session.query(Lesson.xp_reward).filter(Lesson.id == lesson.id).scalar()
    assert stored == 5 * settings.XP_PER_EXERCISE

    apply_verdict(
        db_session,
        pack=pack,
        verdict=CommunityStatus.APPROVED,
        actor_id=None,
        notes=None,
        quality_score=None,
        ratify_difficulty=True,
    )
    graded = db_session.query(Lesson.xp_reward).filter(Lesson.id == lesson.id).scalar()
    assert graded == 5 * settings.XP_BY_LEVEL[5]


def test_ingested_pack_stores_flat_announced_xp(client: TestClient, db_session: Session):
    """Un pack ingéré non ratifié stocke d'emblée l'XP forfaitaire, sans passer par un refresh."""
    from app.models.content import Lesson
    from app.services.contribution import ingest_pack
    from tests.helpers import ensure_parent

    author = ensure_parent(db_session, "auteur-xp@qa.fr")
    document = {
        "format_version": 1,
        "pack": {
            "title": "Additions très simples",
            "emoji": "💰",
            "description": "Des additions à un chiffre, pour démarrer en douceur.",
            "tags": ["maths"],
        },
        "lessons": [
            {
                "subject_slug": "maths",
                "level": "cp",
                "tier": 1,
                "name": "Additions",
                "description": "Ajouter un, encore et encore.",
                # xp_reward déclaré exprès : il ne doit jamais atteindre la base.
                "xp_reward": 5000,
                "exercises": [
                    {
                        "type": "math_problem",
                        "question": f"Combien font {value} + 1 ?",
                        "difficulty_level": 5,
                        "content": {"unit": None},
                        "correct_answer": {"value": value + 1, "tolerance": 0},
                    }
                    for value in range(1, 6)
                ],
            }
        ],
        "self_check": {"math_verified": True, "notes": "Trivial, revérifié."},
    }

    pack = ingest_pack(db_session, payload=document, author=author)
    db_session.commit()

    stored = db_session.query(Lesson.xp_reward).filter(Lesson.pack_id == pack.id).scalar()
    assert stored == 5 * settings.XP_PER_EXERCISE
