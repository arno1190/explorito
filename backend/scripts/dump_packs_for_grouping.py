"""Exporte le contenu existant, par (matière, niveau), pour décider d'un regroupement thématique (issue #12).

Lecture seule : ce script n'écrit **rien** en base. Il produit le matériau que
l'admin (ou une compétence d'agent) lit pour proposer un plan de regroupement,
lequel est ensuite appliqué par ``apply_pack_grouping.py``.

Un fichier par couple (matière, niveau) — jamais un dump global : le jugement
« ces leçons forment un thème » est relatif au niveau scolaire, et mélanger les
niveaux dans un même lot pousse à des packs à cheval sur deux programmes.

Usage:
    DATABASE_URL=... uv run python scripts/dump_packs_for_grouping.py <out_dir> [--subject=maths] [--level=cp]
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.core.database import SessionLocal
from app.models.content import Exercise, LearningPath, Lesson, LevelEnum, Subject
from app.models.pack import Pack

#: Longueur de l'extrait d'énoncé conservé. Assez pour reconnaître le thème d'un
#: exercice, trop court pour transformer le dump en copie du contenu.
QUESTION_EXCERPT = 120


def _excerpt(text: str | None) -> str:
    """Énoncé tronqué, sur une seule ligne."""
    flat = " ".join((text or "").split())
    return flat if len(flat) <= QUESTION_EXCERPT else flat[: QUESTION_EXCERPT - 1] + "…"


def _lesson_payload(lesson: Lesson, pack: Pack, exercises: list[Exercise]) -> dict[str, Any]:
    """Fiche d'une leçon : identité, palier actuel, silhouette de ses exercices."""
    types = Counter(ex.type for ex in exercises)
    return {
        "id": str(lesson.id),
        "name": lesson.name,
        "description": lesson.description,
        "tier": lesson.order_index,
        "published": bool(lesson.is_published),
        "pack_id": str(lesson.pack_id),
        "pack_title": pack.title if pack is not None else None,
        "exercise_count": len(exercises),
        "exercise_types": dict(sorted(types.items())),
        "difficulty_levels": [ex.difficulty_level for ex in exercises],
        "exercises": [
            {
                "order_index": ex.order_index,
                "type": ex.type,
                "difficulty_level": ex.difficulty_level,
                "question": _excerpt(ex.question),
            }
            for ex in exercises
        ],
    }


def main(out_dir: str, subject_slug: str | None = None, level: str | None = None) -> int:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        query = (
            db.query(Lesson, LearningPath, Subject, Pack)
            .join(LearningPath, Lesson.path_id == LearningPath.id)
            .join(Subject, LearningPath.subject_id == Subject.id)
            .outerjoin(Pack, Lesson.pack_id == Pack.id)
        )
        if subject_slug:
            query = query.filter(Subject.slug == subject_slug)
        if level:
            query = query.filter(LearningPath.level == LevelEnum(level))

        exercises_by_lesson: dict[Any, list[Exercise]] = defaultdict(list)
        for ex in db.query(Exercise).order_by(Exercise.order_index).all():
            exercises_by_lesson[ex.lesson_id].append(ex)

        # Regroupement par (matière, niveau) ; on garde les métadonnées de matière
        # pour que le plan appliqué plus tard n'ait pas à les redécouvrir.
        buckets: dict[tuple[str, str], dict[str, Any]] = {}
        for lesson, path, subject, pack in query.all():
            key = (subject.slug, path.level.value)
            bucket = buckets.setdefault(
                key,
                {
                    "subject": {"slug": subject.slug, "name": subject.name, "icon": subject.icon},
                    "level": path.level.value,
                    "packs": {},
                    "lessons": [],
                },
            )
            if pack is not None:
                bucket["packs"][str(pack.id)] = {
                    "id": str(pack.id),
                    "title": pack.title,
                    "emoji": pack.emoji,
                    "origin": pack.origin,
                    "community_status": pack.community_status,
                    "tags": pack.tags or [],
                }
            bucket["lessons"].append(_lesson_payload(lesson, pack, exercises_by_lesson.get(lesson.id, [])))

        manifest: list[dict[str, Any]] = []
        for (slug, lvl), bucket in sorted(buckets.items()):
            bucket["packs"] = sorted(bucket["packs"].values(), key=lambda p: p["title"])
            bucket["lessons"].sort(key=lambda item: (item["tier"], item["name"]))
            fname = f"grouping_{slug}_{lvl}.json"
            (out / fname).write_text(json.dumps(bucket, ensure_ascii=False, indent=1), encoding="utf-8")
            manifest.append(
                {
                    "file": fname,
                    "subject": slug,
                    "level": lvl,
                    "lessons": len(bucket["lessons"]),
                    "exercises": sum(item["exercise_count"] for item in bucket["lessons"]),
                    "packs": len(bucket["packs"]),
                }
            )
        (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

        total = sum(m["lessons"] for m in manifest)
        print(f"{total} leçons → {len(manifest)} lots dans {out}")
        for m in manifest:
            print(f"  {m['file']:34} {m['lessons']:4} leçons  {m['exercises']:5} exercices  {m['packs']} pack(s)")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dump du contenu par matière+niveau pour un regroupement thématique.")
    parser.add_argument("out_dir", help="Répertoire de sortie (créé au besoin).")
    parser.add_argument("--subject", dest="subject", default=None, help="Slug de matière à filtrer (ex. maths).")
    parser.add_argument("--level", dest="level", default=None, help="Niveau à filtrer (ps…cm2).")
    args = parser.parse_args()
    raise SystemExit(main(args.out_dir, args.subject, args.level))
