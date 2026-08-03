"""Applique la difficulté fine (difficulty_level 1-5) à tous les exercices (issue #6).

Lit ``app/data/difficulty_assessment.json`` (évaluation IA relative au niveau,
figée dans le dépôt pour une parité dev/prod stricte) et renseigne
``Exercise.difficulty_level`` en identifiant chaque exercice par une CLÉ STABLE
``subject_slug|level|lesson_name|order_index`` (indépendante de l'UUID).

Tout exercice absent de l'évaluation (ex. contenu ajouté après coup) reçoit un
niveau de repli déduit de l'ancienne colonne ``difficulty`` afin qu'aucun
exercice ne reste sans note.

Idempotent : réexécutable sans effet de bord. Utiliser --dry-run pour simuler.

Usage:
    DATABASE_URL=... uv run python scripts/assess_backfill.py [--dry-run]
"""

import json
import sys
from pathlib import Path

from app.core.database import SessionLocal
from app.models.content import Exercise, LearningPath, Lesson, Subject

ASSESSMENT = Path(__file__).resolve().parent.parent / "app" / "data" / "difficulty_assessment.json"

# Repli quand un exercice n'est pas dans l'évaluation figée.
_FALLBACK_BY_DIFFICULTY = {"easy": 2, "medium": 3, "hard": 4}


def main(dry_run: bool = False) -> int:
    mapping: dict[str, int] = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
    db = SessionLocal()
    matched = fallback = unchanged = 0
    dist: dict[int, int] = {}
    try:
        rows = (
            db.query(Exercise, Lesson, LearningPath, Subject)
            .join(Lesson, Exercise.lesson_id == Lesson.id)
            .join(LearningPath, Lesson.path_id == LearningPath.id)
            .join(Subject, LearningPath.subject_id == Subject.id)
            .all()
        )
        for ex, lesson, path, subject in rows:
            key = f"{subject.slug}|{path.level.value}|{lesson.name}|{ex.order_index}"
            level = mapping.get(key)
            if level is not None:
                matched += 1
            else:
                diff = getattr(ex.difficulty, "value", None)
                level = _FALLBACK_BY_DIFFICULTY.get(str(diff), 2)
                fallback += 1
            dist[level] = dist.get(level, 0) + 1
            if ex.difficulty_level == level:
                unchanged += 1
            elif not dry_run:
                ex.difficulty_level = level
        if not dry_run:
            db.commit()
        print(
            f"{'(dry-run) ' if dry_run else ''}{matched + fallback} exercices — "
            f"évalués: {matched}, repli difficulté: {fallback}, déjà à jour: {unchanged}"
        )
        print("Répartition des niveaux:", {k: dist[k] for k in sorted(dist)})
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
