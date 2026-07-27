"""
Insère une leçon thématique (générée) dans la base Explorito.

Prend un fichier JSON décrivant une matière, un niveau, un palier (tier) et une
liste d'exercices typés, valide chaque exercice contre le contrat, puis crée
(au besoin) la matière et le parcours, et insère la leçon publiée avec ses
exercices. Idempotent par (parcours, nom de leçon).

Usage:
    uv run python scripts/seed_theme.py <theme.json>

Format JSON attendu:
{
  "subject_slug": "maths",
  "subject_name": "Mathématiques",      # utilisé si la matière doit être créée
  "subject_icon": "🔢",                  # idem (optionnel)
  "level": "ce1",                        # ps|ms|gs|cp|ce1|ce2|cm1|cm2
  "tier": 1,                             # 1=Découverte, 2=Entraînement, 3=Défi
  "lesson": {"name": "...", "description": "...", "xp_reward": 50},
  "exercises": [
    {"type": "math_problem", "question": "...", "content": {"unit": "€"},
     "correct_answer": {"value": 12}, "media_urls": {"emoji": "🦕"}},
    ...
  ]
}
"""

import json
import sys
from pathlib import Path

from app.core.database import SessionLocal
from app.models.content import (
    DifficultyEnum,
    Exercise,
    ExerciseType,
    LearningPath,
    Lesson,
    LevelEnum,
    Subject,
)
from app.schemas.exercise import validate_exercise_payload

TIER_DIFFICULTY = {1: DifficultyEnum.EASY, 2: DifficultyEnum.MEDIUM, 3: DifficultyEnum.HARD}


def main(theme_path: str) -> int:
    data = json.loads(Path(theme_path).read_text(encoding="utf-8"))
    level = LevelEnum(data["level"])
    tier = int(data.get("tier", 1))
    lesson_spec = data["lesson"]

    db = SessionLocal()
    try:
        # Matière (find-or-create par slug)
        subject = db.query(Subject).filter(Subject.slug == data["subject_slug"]).first()
        if subject is None:
            subject = Subject(
                name=data.get("subject_name", data["subject_slug"].title()),
                slug=data["subject_slug"],
                icon=data.get("subject_icon"),
                is_active=True,
            )
            db.add(subject)
            db.flush()
            print(f"+ matière créée: {subject.name}")

        # Parcours (find-or-create par matière + niveau)
        path = db.query(LearningPath).filter(LearningPath.subject_id == subject.id, LearningPath.level == level).first()
        if path is None:
            path = LearningPath(
                subject_id=subject.id,
                name=f"{subject.name} — {level.value.upper()}",
                level=level,
            )
            db.add(path)
            db.flush()
            print(f"+ parcours créé: {path.name}")

        # Idempotence : ne pas recréer une leçon de même nom dans ce parcours.
        existing = db.query(Lesson).filter(Lesson.path_id == path.id, Lesson.name == lesson_spec["name"]).first()
        if existing is not None:
            print(f"= leçon '{lesson_spec['name']}' déjà présente — ignorée")
            return 0

        lesson = Lesson(
            path_id=path.id,
            name=lesson_spec["name"],
            description=lesson_spec.get("description"),
            order_index=tier,
            xp_reward=int(lesson_spec.get("xp_reward", 50)),
            is_published=True,
        )
        db.add(lesson)
        db.flush()

        for idx, raw in enumerate(data["exercises"]):
            ex_type = ExerciseType(raw["type"])
            content = raw.get("content", {})
            correct = raw.get("correct_answer", {})
            # Filet de sécurité : la forme doit respecter le contrat.
            validate_exercise_payload(ex_type, content, correct)
            db.add(
                Exercise(
                    lesson_id=lesson.id,
                    type=ex_type.value,
                    question=raw["question"],
                    content=content,
                    correct_answer=correct,
                    hints=raw.get("hints", []),
                    explanation=raw.get("explanation"),
                    order_index=idx,
                    difficulty=TIER_DIFFICULTY.get(tier, DifficultyEnum.EASY),
                    media_urls=raw.get("media_urls", {}),
                )
            )

        db.commit()
        print(
            f"✓ leçon '{lesson.name}' ({subject.name} / {level.value} / palier {tier}) "
            f"créée avec {len(data['exercises'])} exercices — publiée."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: uv run python scripts/seed_theme.py <theme.json>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
