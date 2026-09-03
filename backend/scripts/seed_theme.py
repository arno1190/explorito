"""
Insère du contenu thématique (généré) dans la base Explorito.

Deux formats d'entrée, un seul validateur :

1. **Format `.explorito` (recommandé)** — ``--pack <fichier.explorito>``. Un pack
   entier : plusieurs leçons, éventuellement sur plusieurs matières et niveaux.
   Le fichier passe par ``app.services.pack_format.validate_pack`` puis
   ``app.services.contribution.ingest_pack``, exactement comme un envoi de
   parent : c'est le même code qui valide le contenu de l'équipe et celui de la
   communauté, donc aucun des deux chemins ne peut être plus permissif que
   l'autre. Le pack créé a l'origine ``official`` (activé implicitement pour tous
   les enfants du niveau).

2. **Format « thème » historique (une leçon)** — conservé parce que la
   compétence ``.claude/skills/explorito-seed`` l'émet encore. La leçon rejoint
   le pack officiel de sa matière et de son niveau
   (``services.packs.ensure_official_pack``) : aucune leçon ne peut naître sans
   pack, ``lessons.pack_id`` étant NOT NULL.

Idempotent : par (parcours, nom de leçon) en format historique, par titre de pack
en format `.explorito`.

Usage:
    uv run python scripts/seed_theme.py <theme.json>
    uv run python scripts/seed_theme.py --pack <pack.explorito>

Format `.explorito` attendu:
{
  "format_version": 1,
  "pack": {"title": "Coupe du Monde", "emoji": "⚽", "description": "...", "tags": ["sport"]},
  "lessons": [
    {"subject_slug": "maths", "level": "ce1", "tier": 1, "name": "...", "description": "...",
     "exercises": [{"type": "math_problem", "question": "...", "content": {"unit": "€"},
                    "correct_answer": {"value": 12}, "difficulty_level": 2}]}
  ],
  "self_check": {"math_verified": true, "notes": "..."}
}

Format « thème » historique attendu:
{
  "subject_slug": "maths",
  "subject_name": "Mathématiques",      # utilisé si la matière doit être créée
  "subject_icon": "🔢",                  # idem (optionnel)
  "level": "ce1",                        # ps|ms|gs|cp|ce1|ce2|cm1|cm2
  "tier": 1,                             # 1=Découverte, 2=Entraînement, 3=Défi
  "lesson": {"name": "...", "description": "..."},
  "exercises": [
    {"type": "math_problem", "question": "...", "content": {"unit": "€"},
     "correct_answer": {"value": 12}, "level": 2, "media_urls": {"emoji": "🦕"}},
    ...
  ]
}
Note : ``lesson.xp_reward`` est ignoré dans les deux formats — l'XP est dérivée
des difficultés des exercices (``services.packs.derive_lesson_xp``).
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
from app.models.pack import Pack, PackOrigin
from app.schemas.exercise import validate_exercise_payload
from app.services.contribution import ingest_pack, known_subject_slugs
from app.services.pack_format import PackRejected, normalised_title, validate_pack
from app.services.packs import derive_lesson_xp, ensure_official_pack

TIER_DIFFICULTY = {1: DifficultyEnum.EASY, 2: DifficultyEnum.MEDIUM, 3: DifficultyEnum.HARD}


def seed_pack(pack_path: str) -> int:
    """Ingère un fichier `.explorito` comme pack officiel."""
    document = json.loads(Path(pack_path).read_text(encoding="utf-8"))

    db = SessionLocal()
    try:
        # Validation d'abord : un fichier cassé doit toujours être signalé, même
        # si un pack de même titre existe déjà (sinon une régénération fautive
        # passerait inaperçue derrière un « déjà présent »).
        try:
            payload, issues, score = validate_pack(document, known_subject_slugs=known_subject_slugs(db))
        except PackRejected as rejected:
            for issue in rejected.issues:
                print(f"✗ {issue.code}: {issue.message}", file=sys.stderr)
            return 1

        title = payload["pack"]["title"]
        key = normalised_title(title)
        existing = [
            row[0]
            for row in db.query(Pack.title).filter(Pack.origin == PackOrigin.OFFICIAL.value).all()
            if normalised_title(row[0]) == key
        ]
        if existing:
            print(f"= pack '{title}' déjà présent — ignoré")
            return 0

        pack = ingest_pack(
            db,
            payload=payload,
            author=None,
            origin=PackOrigin.OFFICIAL,
            issues=issues,
            quality_score=score,
        )
        db.commit()
        lessons = payload["lessons"]
        total_ex = sum(len(lesson["exercises"]) for lesson in lessons)
        print(f"✓ pack '{pack.title}' créé — {len(lessons)} leçons, {total_ex} exercices, qualité {score}/100.")
        for issue in issues:
            print(f"  · [{issue.severity}] {issue.code}: {issue.message}")
        return 0
    finally:
        db.close()


def seed_theme(theme_path: str) -> int:
    """Ingère une leçon au format « thème » historique (une matière, un niveau)."""
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

        # Pack officiel de (matière, niveau) : identité déterministe, donc aucun
        # doublon même si la migration l'a déjà créé.
        pack = ensure_official_pack(db, subject.id, level, subject.name, subject.icon)

        # Idempotence : ne pas recréer une leçon de même nom dans ce parcours.
        existing = db.query(Lesson).filter(Lesson.path_id == path.id, Lesson.name == lesson_spec["name"]).first()
        if existing is not None:
            print(f"= leçon '{lesson_spec['name']}' déjà présente — ignorée")
            return 0

        exercises = data["exercises"]
        lesson = Lesson(
            path_id=path.id,
            pack_id=pack.id,
            name=lesson_spec["name"],
            description=lesson_spec.get("description"),
            order_index=tier,
            # XP dérivée du contenu : un xp_reward du fichier serait une XP
            # déclarée par l'auteur, donc une imprimante à billets.
            xp_reward=derive_lesson_xp([raw.get("level") for raw in exercises]),
            is_published=True,
        )
        db.add(lesson)
        db.flush()

        for idx, raw in enumerate(exercises):
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
                    difficulty_level=raw.get("level"),
                    media_urls=raw.get("media_urls", {}),
                )
            )

        db.commit()
        print(
            f"✓ leçon '{lesson.name}' ({subject.name} / {level.value} / palier {tier}) "
            f"créée avec {len(exercises)} exercices — publiée dans le pack '{pack.title}'."
        )
        return 0
    finally:
        db.close()


def main(argv: list[str]) -> int:
    """Route vers le format `.explorito` (``--pack``) ou le format historique."""
    if len(argv) == 2 and argv[0] == "--pack":
        return seed_pack(argv[1])
    if len(argv) == 1 and not argv[0].startswith("-"):
        return seed_theme(argv[0])
    print(
        "usage: uv run python scripts/seed_theme.py <theme.json>\n"
        "       uv run python scripts/seed_theme.py --pack <pack.explorito>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
