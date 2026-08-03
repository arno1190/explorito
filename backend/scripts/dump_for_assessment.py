"""Exporte tous les exercices en lots JSON pour évaluation de difficulté (issue #6).

Chaque exercice est identifié par une CLÉ STABLE indépendante de l'UUID
(``subject_slug|level|lesson_name|order_index``) afin que l'évaluation faite
sur dev s'applique à l'identique sur prod (contenu semé par les mêmes scripts).

Les lots ne mélangent pas les niveaux scolaires : l'évaluation est relative au
niveau (« pour un enfant de ce niveau »).

Usage:
    DATABASE_URL=... uv run python scripts/dump_for_assessment.py <out_dir> [batch_size]
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.core.database import SessionLocal
from app.models.content import Exercise, LearningPath, Lesson, Subject


def _payload(ex: Exercise, subject_name: str) -> dict[str, Any]:
    """Extrait le minimum utile au jugement de difficulté selon le type."""
    content = ex.content or {}
    answer = ex.correct_answer or {}
    out: dict[str, Any] = {"type": ex.type, "question": ex.question}
    if ex.type == "multiple_choice":
        opts = [o.get("text", "") for o in content.get("options", [])]
        out["options"] = opts
        out["n_correct"] = len(answer.get("option_ids", []) or [])
    elif ex.type == "math_problem":
        out["answer"] = answer.get("value")
        if content.get("unit"):
            out["unit"] = content["unit"]
    elif ex.type == "fill_blanks":
        out["text"] = content.get("text", "")
        out["blanks"] = answer.get("blanks", [])
    elif ex.type == "reading":
        out["text"] = content.get("text", "")
    elif ex.type == "soroban":
        out["mode"] = content.get("mode")
        out["value"] = content.get("value")
    elif ex.type == "pythagore":
        out["tables"] = content.get("tables")
    out["subject"] = subject_name
    return out


def main(out_dir: str, batch_size: int = 40) -> int:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        rows = (
            db.query(Exercise, Lesson, LearningPath, Subject)
            .join(Lesson, Exercise.lesson_id == Lesson.id)
            .join(LearningPath, Lesson.path_id == LearningPath.id)
            .join(Subject, LearningPath.subject_id == Subject.id)
            .all()
        )
        by_grade: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for ex, lesson, path, subject in rows:
            grade = path.level.value
            key = f"{subject.slug}|{grade}|{lesson.name}|{ex.order_index}"
            item = {"key": key, **_payload(ex, subject.name)}
            by_grade[grade].append(item)

        manifest: list[dict[str, Any]] = []
        total = 0
        for grade, items in sorted(by_grade.items()):
            items.sort(key=lambda d: d["key"])
            for i in range(0, len(items), batch_size):
                chunk = items[i : i + batch_size]
                fname = f"batch_{grade}_{i // batch_size:02d}.json"
                (out / fname).write_text(
                    json.dumps({"grade": grade, "items": chunk}, ensure_ascii=False, indent=1),
                    encoding="utf-8",
                )
                manifest.append({"file": fname, "grade": grade, "count": len(chunk)})
                total += len(chunk)
        (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{total} exercices → {len(manifest)} lots dans {out}")
        for m in manifest:
            print(f"  {m['file']:26} {m['grade']:4} {m['count']}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: dump_for_assessment.py <out_dir> [batch_size]", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 40))
