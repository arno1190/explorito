"""
Seed du contenu pédagogique à partir de ``scripts/cp_content.json``.

Le JSON est dérivé du projet "explorateurs-cp" (240 exercices CP/CE1). Chaque
île devient une :class:`Subject`, chaque niveau scolaire (CP/CE1) un
:class:`LearningPath`, chaque difficulté (1/2/3) une :class:`Lesson` de 5
exercices, mappés vers le contrat d'exercice canonique :

- ``qcm``        -> ``multiple_choice``
- ``completion`` -> ``fill_blanks``  (le ``_`` devient le marqueur ``___``)
- ``blague``     -> ``reveal``

Chaque exercice est validé contre le contrat (:func:`validate_exercise_payload`)
avant insertion.

Usage:
    uv run python scripts/seed_cp_content.py            # seed si vide, sinon abandon
    uv run python scripts/seed_cp_content.py --reset     # DESTRUCTIF : purge le contenu puis reseed
"""

import argparse
import json
import re
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

CONTENT_JSON = Path(__file__).parent / "cp_content.json"

LEVEL_MAP = {"CP": LevelEnum.CP, "CE1": LevelEnum.CE1}
DIFFICULTY_MAP = {1: DifficultyEnum.EASY, 2: DifficultyEnum.MEDIUM, 3: DifficultyEnum.HARD}
LESSON_NAMES = {1: "Niveau 1 · Découverte", 2: "Niveau 2 · Entraînement", 3: "Niveau 3 · Défi"}
LESSON_XP_REWARD = 50
BLANK_RUN = re.compile(r"_+")


def build_exercise_payload(
    raw: dict,
) -> tuple[ExerciseType, str, dict, dict, dict] | None:
    """
    Convertit un exercice source vers (type, question, content, correct_answer, media).

    Retourne ``None`` pour un exercice source à ignorer (données incohérentes non
    récupérables), après un avertissement.

    Raises:
        ValueError: Si le type source est inconnu ou une réponse QCM est absente
            des options (erreurs dures).
    """
    kind = raw["type"]
    emoji = raw.get("img", "")
    media = {"emoji": emoji} if emoji else {}

    if kind == "qcm":
        options = [{"id": str(i), "text": opt} for i, opt in enumerate(raw["options"])]
        matching = [o["id"] for o in options if o["text"] == raw["answer"]]
        if not matching:
            raise ValueError(f"Réponse QCM '{raw['answer']}' absente des options: {raw['options']}")
        content = {"options": options, "multiple": False}
        correct = {"option_ids": matching[:1]}
        return ExerciseType.MULTIPLE_CHOICE, raw["q"], content, correct, media

    if kind == "completion":
        # Chaque `_` marque une lettre manquante. La réponse concatène les lettres
        # dans l'ordre : on répartit un caractère par trou. Si les comptes ne
        # correspondent pas (données source erronées), on ignore l'exercice.
        n_blanks = len(BLANK_RUN.findall(raw["q"]))
        text = BLANK_RUN.sub("___", raw["q"])
        answer = raw["answer"]
        if n_blanks == 0:
            print(f"  ! completion sans trou, ignorée: {raw['q']!r}")
            return None
        if n_blanks == 1:
            blanks = [answer]
        elif len(answer) == n_blanks:
            blanks = list(answer)
        else:
            print(f"  ! completion incohérente ({n_blanks} trous / réponse {answer!r}), ignorée: {raw['q']!r}")
            return None
        content = {"text": text}
        correct = {"blanks": blanks}
        return ExerciseType.FILL_BLANKS, "Complète le mot :", content, correct, media

    if kind == "blague":
        content = {"prompt": raw["q"], "reveal": raw["answer"]}
        return ExerciseType.REVEAL, raw["q"], content, {}, media

    raise ValueError(f"Type source inconnu: {kind}")


def content_exists(db) -> bool:
    """Retourne True si des matières existent déjà."""
    return db.query(Subject).first() is not None


def purge_content(db) -> None:
    """Supprime tout le contenu (cascade sur paths/leçons/exercices). DESTRUCTIF."""
    # La suppression des Subjects cascade aussi SubjectProgress/UserProgress.
    for subject in db.query(Subject).all():
        db.delete(subject)
    db.commit()


def seed(db, data: dict) -> dict[str, int]:
    """Insère le contenu. Retourne des compteurs."""
    counters = {"subjects": 0, "paths": 0, "lessons": 0, "exercises": 0, "skipped": 0}
    islands = {isl["id"]: isl for isl in data["islands"]}

    # Ordre stable des îles = ordre de la liste ISLANDS source.
    for order, island_id in enumerate(islands):
        island = islands[island_id]
        subject = Subject(
            name=island["desc"],
            slug=island_id,
            description=island["name"],
            icon=island.get("emoji"),
            color=island.get("color"),
            order_index=order,
            is_active=True,
        )
        db.add(subject)
        db.flush()  # pour disposer de subject.id
        counters["subjects"] += 1

        for level_key, level_enum in LEVEL_MAP.items():
            island_levels = data["exercises"][level_key].get(island_id)
            if not island_levels:
                continue
            path = LearningPath(
                subject_id=subject.id,
                name=f"{island['desc']} — {level_key}",
                description=f"{island['name']} ({level_key})",
                level=level_enum,
                order_index=list(LEVEL_MAP).index(level_key),
            )
            db.add(path)
            db.flush()
            counters["paths"] += 1

            for diff in sorted(int(d) for d in island_levels):
                raw_exercises = island_levels[str(diff)] if str(diff) in island_levels else island_levels[diff]
                lesson = Lesson(
                    path_id=path.id,
                    name=LESSON_NAMES.get(diff, f"Niveau {diff}"),
                    description=None,
                    order_index=diff,
                    unlock_criteria={},
                    xp_reward=LESSON_XP_REWARD,
                    is_published=True,
                )
                db.add(lesson)
                db.flush()
                counters["lessons"] += 1

                order = 0
                for raw in raw_exercises:
                    payload = build_exercise_payload(raw)
                    if payload is None:
                        counters["skipped"] += 1
                        continue
                    ex_type, question, content, correct, media = payload
                    # Filet de sécurité : valide contre le contrat avant insertion.
                    validate_exercise_payload(ex_type, content, correct)
                    db.add(
                        Exercise(
                            lesson_id=lesson.id,
                            type=ex_type.value,
                            question=question,
                            content=content,
                            correct_answer=correct,
                            hints=[],
                            explanation=None,
                            order_index=order,
                            difficulty=DIFFICULTY_MAP.get(diff, DifficultyEnum.EASY),
                            media_urls=media,
                        )
                    )
                    order += 1
                    counters["exercises"] += 1

    db.commit()
    return counters


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed du contenu CP/CE1")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Purge le contenu existant avant de reseed (DESTRUCTIF : efface aussi la progression)",
    )
    args = parser.parse_args()

    if not CONTENT_JSON.exists():
        print(f"Fichier introuvable: {CONTENT_JSON}", file=sys.stderr)
        return 1

    data = json.loads(CONTENT_JSON.read_text(encoding="utf-8"))
    db = SessionLocal()
    try:
        if content_exists(db):
            if not args.reset:
                print("Du contenu existe déjà. Utilisez --reset pour purger et reseed (DESTRUCTIF).")
                return 0
            print("--reset : purge du contenu existant…")
            purge_content(db)

        counters = seed(db, data)
        print("Seed terminé :", counters)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
