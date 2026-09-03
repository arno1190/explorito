"""Regroupement thématique du contenu existant (issue #12).

Le regroupement est le seul chemin qui déplace des leçons entre packs. Comme
``user_progress.lesson_id`` et ``exercise_results.exercise_id`` sont en
``ON DELETE CASCADE``, une erreur d'implémentation qui recréerait des leçons
effacerait silencieusement la progression des enfants : ces tests vérifient donc
la conservation **ligne par ligne**, pas seulement le résultat visible.
"""

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.models.content import Lesson, LevelEnum
from app.models.contribution import PackAuditLog
from app.models.pack import Pack
from app.models.progress import ExerciseResult, ProgressStatus, UserProgress
from app.services.packs import ensure_official_pack, official_pack_id
from tests.helpers import make_child, make_exercise, make_lesson, make_pack, make_subject


def _load_script(name: str) -> ModuleType:
    """Charge un script de ``backend/scripts`` (hors package) par son chemin."""
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


grouping = _load_script("apply_pack_grouping")
dumping = _load_script("dump_packs_for_grouping")

#: Paliers d'origine des six leçons de la scène, comme les posent les seeders.
ORIGINAL_TIERS = {"L1": 1, "L2": 1, "L3": 2, "L4": 2, "L5": 3, "L6": 3}


@pytest.fixture
def scene(db_session: Session) -> dict[str, Any]:
    """Six leçons CP de maths dans le pack officiel « en gros », avec de la progression."""
    subject = make_subject(db_session, slug="maths", name="Mathématiques", icon="🔢")
    official = ensure_official_pack(db_session, subject.id, LevelEnum.CP, subject.name, subject.icon)
    lessons = {
        name: make_lesson(db_session, pack=official, subject=subject, level=LevelEnum.CP, tier=tier, name=name)
        for name, tier in ORIGINAL_TIERS.items()
    }
    exercises = {
        name: [make_exercise(db_session, lesson=lesson, order_index=i) for i in range(2)]
        for name, lesson in lessons.items()
    }
    child = make_child(db_session, level=LevelEnum.CP)

    # De la progression réelle : deux leçons terminées, quatre résultats d'exercices.
    for name in ("L1", "L2"):
        db_session.add(
            UserProgress(
                user_id=child.id,
                lesson_id=lessons[name].id,
                status=ProgressStatus.COMPLETED,
                score=90,
                stars=3,
                attempts=1,
            )
        )
        for exercise in exercises[name]:
            db_session.add(
                ExerciseResult(
                    user_id=child.id,
                    exercise_id=exercise.id,
                    answer={"option_ids": ["a"]},
                    is_correct=True,
                )
            )
    db_session.commit()
    return {"subject": subject, "official": official, "lessons": lessons, "child": child}


def _plan(scene: dict[str, Any]) -> dict[str, Any]:
    """Plan à deux packs thématiques, dont un avec des paliers déclarés non contigus."""
    return {
        "subject": "maths",
        "level": "cp",
        "packs": [
            {
                "title": "Les nombres jusqu'à 100",
                "emoji": "🔢",
                "description": "Compter, comparer, ranger.",
                "tags": ["nombres"],
                "lessons": ["L1", "L2", "L3"],
            },
            {
                "title": "Additions et soustractions",
                "emoji": "➕",
                "lessons": [
                    {"lesson": "L4", "tier": 5},
                    {"lesson": "L5", "tier": 5},
                    {"lesson": "L6", "tier": 9},
                ],
            },
        ],
    }


def _apply(db: Session, scene: dict[str, Any], plan: dict[str, Any] | None = None) -> int:
    """Applique un plan comme le fait le script, et renvoie le nombre de leçons déplacées."""
    subject, lessons = grouping._scope(db, "maths", LevelEnum.CP)
    groups = grouping.plan_groups(db, plan or _plan(scene), subject, LevelEnum.CP, lessons)
    changed, _ = grouping.write_groups(db, groups, "maths", LevelEnum.CP)
    db.commit()
    return changed


def _snapshot(db: Session) -> dict[str, Any]:
    """Photo des lignes que le regroupement ne doit jamais toucher."""
    return {
        "lesson_ids": sorted(str(row.id) for row in db.query(Lesson).all()),
        "progress": sorted(
            (str(row.id), str(row.lesson_id), row.status.value, row.score, row.stars)
            for row in db.query(UserProgress).all()
        ),
        "results": sorted(
            (str(row.id), str(row.exercise_id), row.is_correct) for row in db.query(ExerciseResult).all()
        ),
    }


def test_regroup_preserves_lesson_ids_and_progress(db_session: Session, scene: dict[str, Any]) -> None:
    before = _snapshot(db_session)

    assert _apply(db_session, scene) == 6

    assert _snapshot(db_session) == before
    packs = {lesson.name: lesson.pack.title for lesson in db_session.query(Lesson).all()}
    assert packs == {
        "L1": "Les nombres jusqu'à 100",
        "L2": "Les nombres jusqu'à 100",
        "L3": "Les nombres jusqu'à 100",
        "L4": "Additions et soustractions",
        "L5": "Additions et soustractions",
        "L6": "Additions et soustractions",
    }


def test_tiers_are_contiguous_within_each_pack(db_session: Session, scene: dict[str, Any]) -> None:
    _apply(db_session, scene)

    by_pack: dict[str, list[int]] = {}
    for lesson in db_session.query(Lesson).all():
        by_pack.setdefault(lesson.pack.title, []).append(lesson.order_index)
    for title, tiers in by_pack.items():
        assert sorted(set(tiers)) == list(range(1, len(set(tiers)) + 1)), f"paliers non contigus dans {title!r}"
    # Les paliers déclarés 5, 5 et 9 sont compactés en 1, 1 et 2.
    assert sorted(by_pack["Additions et soustractions"]) == [1, 1, 2]


def test_reapplying_the_same_plan_changes_nothing(db_session: Session, scene: dict[str, Any]) -> None:
    _apply(db_session, scene)
    assignment = {lesson.name: (str(lesson.pack_id), lesson.order_index) for lesson in db_session.query(Lesson).all()}
    audits = db_session.query(PackAuditLog).count()
    packs = db_session.query(Pack).count()

    assert _apply(db_session, scene) == 0

    assert {
        lesson.name: (str(lesson.pack_id), lesson.order_index) for lesson in db_session.query(Lesson).all()
    } == assignment
    assert db_session.query(PackAuditLog).count() == audits
    assert db_session.query(Pack).count() == packs


def test_revert_restores_the_official_pack(db_session: Session, scene: dict[str, Any]) -> None:
    before = _snapshot(db_session)
    _apply(db_session, scene)

    subject, lessons = grouping._scope(db_session, "maths", LevelEnum.CP)
    groups = grouping.official_groups(db_session, subject, LevelEnum.CP, lessons)
    grouping.write_groups(db_session, groups, "maths", LevelEnum.CP)
    db_session.commit()

    expected_pack = official_pack_id(scene["subject"].id, LevelEnum.CP)
    restored = db_session.query(Lesson).all()
    assert {lesson.pack_id for lesson in restored} == {expected_pack}
    # Les paliers d'origine sont relus dans le journal du regroupement.
    assert {lesson.name: lesson.order_index for lesson in restored} == ORIGINAL_TIERS
    assert _snapshot(db_session) == before


def test_a_plan_omitting_a_lesson_is_refused(db_session: Session, scene: dict[str, Any]) -> None:
    plan = _plan(scene)
    plan["packs"][1]["lessons"] = [{"lesson": "L4", "tier": 5}, {"lesson": "L5", "tier": 5}]

    with pytest.raises(grouping.PlanError, match="'L6'"):
        _apply(db_session, scene, plan)
    db_session.rollback()

    assert {lesson.pack_id for lesson in db_session.query(Lesson).all()} == {scene["official"].id}


def test_an_empty_pack_is_refused(db_session: Session, scene: dict[str, Any]) -> None:
    plan = _plan(scene)
    plan["packs"].append({"title": "Pack vide", "lessons": []})

    with pytest.raises(grouping.PlanError, match="pack vide est refusé"):
        _apply(db_session, scene, plan)
    db_session.rollback()

    assert {lesson.pack_id for lesson in db_session.query(Lesson).all()} == {scene["official"].id}


def test_an_unknown_lesson_reference_is_refused(db_session: Session, scene: dict[str, Any]) -> None:
    plan = _plan(scene)
    plan["packs"][0]["lessons"] = ["L1", "L2", "L3", "L42"]

    with pytest.raises(grouping.PlanError, match="introuvable"):
        _apply(db_session, scene, plan)
    db_session.rollback()


def test_a_lesson_assigned_twice_is_refused(db_session: Session, scene: dict[str, Any]) -> None:
    plan = _plan(scene)
    plan["packs"][1]["lessons"].append("L1")

    with pytest.raises(grouping.PlanError, match="deux fois"):
        _apply(db_session, scene, plan)
    db_session.rollback()


def test_dry_run_writes_nothing(
    db_session: Session,
    scene: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(_plan(scene), ensure_ascii=False), encoding="utf-8")
    # ``main`` ferme la session en sortie : on retient l'identifiant avant l'appel.
    official_id = scene["official"].id
    monkeypatch.setattr(grouping, "SessionLocal", lambda: db_session)

    assert grouping.main(str(plan_file), dry_run=True) == 0

    out = capsys.readouterr().out
    assert "Les nombres jusqu'à 100" in out
    assert "dry-run" in out
    assert {lesson.pack_id for lesson in db_session.query(Lesson).all()} == {official_id}
    assert db_session.query(Pack).count() == 1


def test_dump_emits_one_file_per_subject_and_level(
    db_session: Session,
    scene: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Une leçon CE1 dans un autre pack : le dump ne doit pas mélanger les niveaux.
    other = make_pack(db_session, title="Maths — CE1", level=LevelEnum.CE1)
    make_lesson(db_session, pack=other, subject=scene["subject"], level=LevelEnum.CE1, tier=1, name="CE1-1")
    db_session.commit()
    monkeypatch.setattr(dumping, "SessionLocal", lambda: db_session)

    assert dumping.main(str(tmp_path)) == 0

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert {(m["subject"], m["level"], m["lessons"]) for m in manifest} == {("maths", "cp", 6), ("maths", "ce1", 1)}
    cp = json.loads((tmp_path / "grouping_maths_cp.json").read_text(encoding="utf-8"))
    assert [item["name"] for item in cp["lessons"]] == ["L1", "L2", "L3", "L4", "L5", "L6"]
    first = cp["lessons"][0]
    assert first["tier"] == 1
    assert first["exercise_count"] == 2
    assert first["exercise_types"] == {"multiple_choice": 2}
    assert first["difficulty_levels"] == [1, 1]
    assert first["pack_title"] == scene["official"].title
