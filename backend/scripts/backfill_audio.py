"""Génère l'audio (consigne lue à voix haute) des exercices d'un ou plusieurs niveaux.

L'audio est dérivable du seul texte de l'énoncé : ce script parcourt les
exercices des niveaux demandés, synthétise le MP3 (via ``media_gen.tts``) et
renseigne ``media_urls["audio"]``. Idempotent : un exercice qui a déjà un audio
valide est ignoré (sauf ``--force``).

Usage:
    uv run python scripts/backfill_audio.py --levels ps,ms,gs,cp [--force] [--dry-run]
"""

import argparse
from pathlib import Path

from media_gen import clean_for_tts, tts
from sqlalchemy.orm.attributes import flag_modified

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.content import Exercise, LearningPath, Lesson, LevelEnum

VALID = {e.value for e in LevelEnum}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--levels", default="ps,ms,gs,cp", help="niveaux séparés par des virgules")
    parser.add_argument("--force", action="store_true", help="regénère même si un audio existe déjà")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    levels = [lvl.strip().lower() for lvl in args.levels.split(",") if lvl.strip()]
    unknown = [lvl for lvl in levels if lvl not in VALID]
    if unknown:
        print(f"Niveaux inconnus: {unknown}. Valides: {sorted(VALID)}")
        return 2

    db = SessionLocal()
    generated = skipped = empty = 0
    try:
        rows = (
            db.query(Exercise)
            .join(Lesson, Lesson.id == Exercise.lesson_id)
            .join(LearningPath, LearningPath.id == Lesson.path_id)
            .filter(LearningPath.level.in_([LevelEnum(lvl) for lvl in levels]))
            .all()
        )
        print(f"{len(rows)} exercices trouvés pour {levels}.")
        for ex in rows:
            media = dict(ex.media_urls or {})
            existing = media.get("audio")
            if existing and not args.force:
                # Vérifie que le fichier est bien présent sur le disque.
                fp = Path(settings.UPLOAD_DIR) / existing.replace("/uploads/", "", 1)
                if fp.exists() and fp.stat().st_size > 0:
                    skipped += 1
                    continue
            if not clean_for_tts(ex.question or ""):
                empty += 1
                continue
            if args.dry_run:
                generated += 1
                continue
            url = tts(ex.question)
            if not url:
                empty += 1
                continue
            media["audio"] = url
            ex.media_urls = media
            flag_modified(ex, "media_urls")
            db.commit()
            generated += 1
            if generated % 25 == 0:
                print(f"  … {generated} audios générés")

        print(
            f"\n{'(dry-run) ' if args.dry_run else ''}Audio — générés: {generated}, "
            f"déjà présents: {skipped}, sans texte: {empty}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
