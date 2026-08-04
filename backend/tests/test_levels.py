"""
Tests du système de niveaux : niveau sur le profil enfant (défini par le parent)
et filtrage du contenu au niveau de l'enfant.

Auth : parent (dev-login) pour la gestion des enfants, parent incarnant l'enfant
pour la vue de contenu, admin (allowlist) pour la vue non filtrée.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import LearningPath, Lesson, LevelEnum, Subject
from tests.helpers import child_headers, dev_login, make_child


def _subject_with_lesson(db: Session, name: str, level: LevelEnum, published: bool = True) -> Subject:
    subject = Subject(name=name, slug=f"{name.lower()}-{level.value}")
    db.add(subject)
    db.flush()
    path = LearningPath(subject_id=subject.id, name=f"{name} {level.value}", level=level)
    db.add(path)
    db.flush()
    db.add(Lesson(path_id=path.id, name=f"Leçon {level.value}", is_published=published))
    db.commit()
    return subject


def test_parent_creates_child_with_level(client: TestClient, db_session: Session):
    h = dev_login(client)
    r = client.post(
        "/api/v1/children",
        json={"name": "Léa", "birth_date": "2017-09-01", "level": "ce1"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    assert r.json()["level"] == "ce1"


def test_parent_updates_child_level(client: TestClient, db_session: Session):
    child = make_child(db_session, level=LevelEnum.CP)
    h = dev_login(client)
    r = client.put(f"/api/v1/children/{child.id}", json={"level": "ce2"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["level"] == "ce2"


def test_child_sees_only_their_level_subjects_and_lessons(client: TestClient, db_session: Session):
    child = make_child(db_session, level=LevelEnum.CE1)
    maths = _subject_with_lesson(db_session, "Maths", LevelEnum.CE1)
    # même matière, une leçon CP (autre parcours) — ne doit pas apparaître pour un CE1
    cp_path = LearningPath(subject_id=maths.id, name="Maths cp", level=LevelEnum.CP)
    db_session.add(cp_path)
    db_session.flush()
    db_session.add(Lesson(path_id=cp_path.id, name="Leçon cp", is_published=True))
    # matière uniquement CP -> masquée pour un CE1
    _subject_with_lesson(db_session, "LectureCP", LevelEnum.CP)
    db_session.commit()

    h = child_headers(client, child)
    subjects = client.get("/api/v1/subjects", headers=h).json()
    names = {s["name"] for s in subjects}
    assert "Maths" in names
    assert "LectureCP" not in names  # pas de contenu CE1

    lessons = client.get(f"/api/v1/subjects/{maths.id}/lessons", headers=h).json()
    lesson_names = {lz["name"] for lz in lessons}
    assert lesson_names == {"Leçon ce1"}  # la leçon CP est exclue


def test_child_does_not_see_unpublished_lessons(client: TestClient, db_session: Session):
    child = make_child(db_session, level=LevelEnum.CP)
    subj = _subject_with_lesson(db_session, "Français", LevelEnum.CP, published=True)
    # ajouter une leçon non publiée au même parcours CP
    path = db_session.query(LearningPath).filter(LearningPath.subject_id == subj.id).first()
    db_session.add(Lesson(path_id=path.id, name="Brouillon", is_published=False))
    db_session.commit()

    h = child_headers(client, child)
    lessons = client.get(f"/api/v1/subjects/{subj.id}/lessons", headers=h).json()
    assert {lz["name"] for lz in lessons} == {"Leçon cp"}


def test_admin_sees_all_levels_unfiltered(client: TestClient, db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "admin@qa.fr")
    _subject_with_lesson(db_session, "HistoireCM2", LevelEnum.CM2, published=False)
    h = dev_login(client, "admin@qa.fr")
    subjects = client.get("/api/v1/subjects", headers=h).json()
    # admin voit la matière même si non publiée / autre niveau
    assert any(s["name"] == "HistoireCM2" for s in subjects)
