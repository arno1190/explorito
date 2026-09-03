"""
Tests du verrou de progression à l'échelle du **pack** (issue #9).

Avant, la portée était le parcours (matière + niveau) : un enfant ne pouvait
atteindre le palier 2 qu'après avoir terminé *toutes* les leçons de palier 1 du
parcours, y compris celles déposées par d'autres familles. Le verrou dépendait
donc du volume de contenu. Désormais chaque pack progresse pour lui-même.

Auth : parent (dev-login) incarnant l'enfant via ``X-Acting-Child-Id``.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import LevelEnum
from app.services.progression import lesson_locked, lesson_locked_by_id
from tests.helpers import (
    child_headers,
    dev_login,
    make_child,
    make_exercise,
    make_lesson,
    make_pack,
    make_subject,
)


def test_sibling_packs_progress_independently(client: TestClient, db_session: Session):
    """Deux packs de la même matière et du même niveau ne se verrouillent pas mutuellement."""
    child = make_child(db_session, level=LevelEnum.CP)
    subject = make_subject(db_session)
    dinos = make_pack(db_session, title="Les Dinosaures", level=LevelEnum.CP)
    coupe = make_pack(db_session, title="Coupe du Monde", level=LevelEnum.CP)
    dinos_t1 = make_lesson(db_session, pack=dinos, subject=subject, tier=1, name="Dino P1")
    dinos_t2 = make_lesson(db_session, pack=dinos, subject=subject, tier=2, name="Dino P2")
    coupe_t1 = make_lesson(db_session, pack=coupe, subject=subject, tier=1, name="Coupe P1")
    coupe_t2 = make_lesson(db_session, pack=coupe, subject=subject, tier=2, name="Coupe P2")
    e_dinos = make_exercise(db_session, lesson=dinos_t1)
    db_session.commit()

    h = child_headers(client, child)
    # Terminer le palier 1 des dinosaures ne doit rien changer pour l'autre pack.
    r = client.post(f"/api/v1/exercises/{e_dinos.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["lesson_completed"] is True

    assert lesson_locked(child.id, dinos_t1, LevelEnum.CP, db_session) is False
    assert lesson_locked(child.id, dinos_t2, LevelEnum.CP, db_session) is False
    assert lesson_locked(child.id, coupe_t1, LevelEnum.CP, db_session) is False
    assert lesson_locked(child.id, coupe_t2, LevelEnum.CP, db_session) is True


def test_tier_two_unlocks_on_own_pack_tier_one_only(client: TestClient, db_session: Session):
    """Le palier 2 d'un pack ne dépend que du palier 1 *de ce pack*."""
    child = make_child(db_session, level=LevelEnum.CP)
    subject = make_subject(db_session)
    mine = make_pack(db_session, title="Mon pack", level=LevelEnum.CP)
    other = make_pack(db_session, title="Pack voisin", level=LevelEnum.CP)
    mine_t1 = make_lesson(db_session, pack=mine, subject=subject, tier=1, name="Mien P1")
    mine_t2 = make_lesson(db_session, pack=mine, subject=subject, tier=2, name="Mien P2")
    # Palier 1 du pack voisin, jamais terminé : il ne doit pas retenir mine_t2.
    make_lesson(db_session, pack=other, subject=subject, tier=1, name="Voisin P1")
    e_mine = make_exercise(db_session, lesson=mine_t1)
    e_mine_t2 = make_exercise(db_session, lesson=mine_t2)
    db_session.commit()

    h = child_headers(client, child)
    # Verrouillé tant que le palier 1 du même pack n'est pas terminé (403 à la soumission).
    blocked = client.post(f"/api/v1/exercises/{e_mine_t2.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)
    assert blocked.status_code == 403, blocked.text

    assert (
        client.post(
            f"/api/v1/exercises/{e_mine.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h
        ).status_code
        == 201
    )

    assert lesson_locked(child.id, mine_t2, LevelEnum.CP, db_session) is False
    assert lesson_locked_by_id(child.id, mine_t2.id, LevelEnum.CP, db_session) is False
    opened = client.post(f"/api/v1/exercises/{e_mine_t2.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)
    assert opened.status_code == 201, opened.text


def test_new_pack_never_relocks_existing_lesson(client: TestClient, db_session: Session):
    """Téléverser un pack ne change l'état de verrou d'aucune leçon existante."""
    child = make_child(db_session, level=LevelEnum.CP)
    subject = make_subject(db_session)
    existing = make_pack(db_session, title="Pack en place", level=LevelEnum.CP)
    tier1 = make_lesson(db_session, pack=existing, subject=subject, tier=1, name="P1")
    tier2 = make_lesson(db_session, pack=existing, subject=subject, tier=2, name="P2")
    e1 = make_exercise(db_session, lesson=tier1)
    db_session.commit()

    h = child_headers(client, child)
    client.post(f"/api/v1/exercises/{e1.id}/submit", json={"answer": {"option_ids": ["a"]}}, headers=h)
    before = [lesson_locked(child.id, lz, LevelEnum.CP, db_session) for lz in (tier1, tier2)]

    # Un nouveau pack arrive avec des paliers 1 ET 0 dans la même matière+niveau.
    newcomer = make_pack(db_session, title="Pack tout neuf", level=LevelEnum.CP)
    make_lesson(db_session, pack=newcomer, subject=subject, tier=0, name="Neuf P0")
    make_lesson(db_session, pack=newcomer, subject=subject, tier=1, name="Neuf P1")
    db_session.commit()

    after = [lesson_locked(child.id, lz, LevelEnum.CP, db_session) for lz in (tier1, tier2)]
    assert after == before == [False, False]


def test_parent_is_never_locked(client: TestClient, db_session: Session):
    """``level`` à ``None`` (parent/admin) court-circuite le verrou, quel que soit le pack."""
    subject = make_subject(db_session)
    pack = make_pack(db_session, title="Calcul CP", level=LevelEnum.CP)
    tier1 = make_lesson(db_session, pack=pack, subject=subject, tier=1, name="P1")
    tier2 = make_lesson(db_session, pack=pack, subject=subject, tier=2, name="P2")
    db_session.commit()

    parent = make_child(db_session, level=LevelEnum.CP)  # crée aussi le parent par défaut
    assert lesson_locked(parent.id, tier2, None, db_session) is False
    assert lesson_locked_by_id(parent.id, tier2.id, None, db_session) is False

    h = dev_login(client)  # parent, sans incarnation
    lessons = client.get(f"/api/v1/subjects/{subject.id}/lessons", headers=h).json()
    by_id = {lz["id"]: lz for lz in lessons}
    assert by_id[str(tier1.id)]["locked"] is False
    assert by_id[str(tier2.id)]["locked"] is False
