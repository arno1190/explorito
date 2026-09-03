"""Applique un plan de regroupement thématique ratifié par l'admin (issue #12).

Le regroupement est un simple ``UPDATE`` de ``lessons.pack_id`` (et du palier
``lessons.order_index``) : **aucune ligne de leçon, de progression ou de
résultat n'est créée ni supprimée**. C'est ce qui rend l'opération rejouable et
réversible, donc sans risque pour la progression des enfants.

Le plan est un JSON portant sur **un seul couple (matière, niveau)** :

    {
      "subject": "maths",
      "level": "cp",
      "packs": [
        {"title": "Les nombres jusqu'à 100", "emoji": "🔢",
         "description": "…", "tags": ["nombres"],
         "lessons": ["CP — Les nombres jusqu'à 10 🔟",
                     {"lesson": "CP — Comparer et ranger 📊", "tier": 2}]}
      ]
    }

Une entrée de ``lessons`` est un nom de leçon, un UUID, ou un objet
``{"lesson": …, "tier": N}``. Les paliers déclarés sont **compactés en 1..N**
dans chaque pack (rang dense) ; sans palier déclaré, l'ordre de la liste fait le
palier. Le verrou de progression étant désormais à l'échelle du pack, ce palier
est la courbe Découverte → Entraînement → Défi *interne* au pack.

Garde-fous (le script refuse plutôt que d'écrire à moitié) :
  - toute leçon de la matière+niveau doit apparaître dans exactement un pack ;
  - aucun pack du plan ne peut être vide ;
  - une référence de leçon inconnue ou ambiguë est une erreur.

Le pack officiel « en gros » d'origine se retrouve vidé : c'est le résultat
attendu, et il est **conservé** — c'est la cible du retour arrière
(``--revert-to-official``), et le supprimer serait de toute façon bloqué par le
``RESTRICT`` de ``lessons.pack_id``.

Usage:
    DATABASE_URL=... uv run python scripts/apply_pack_grouping.py plan.json [--dry-run]
    DATABASE_URL=... uv run python scripts/apply_pack_grouping.py --subject=maths --level=cp \\
        --revert-to-official [--dry-run]
"""

import argparse
import json
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.content import LearningPath, Lesson, LevelEnum, Subject
from app.models.contribution import PackAuditLog
from app.models.pack import CommunityStatus, Pack, PackOrigin
from app.services.packs import OFFICIAL_AUTHOR_HANDLE, PACK_NAMESPACE, ensure_official_pack, log_pack_action

#: Action journalisée par ce script. Le détail porte l'affectation *précédente*,
#: ce qui fait du retour arrière une restauration et non une reconstruction.
REGROUP_ACTION = "regroup"


class PlanError(Exception):
    """Plan inapplicable : rien n'a été écrit."""


@dataclass
class Group:
    """Un pack cible et les leçons qu'il doit contenir, avec leur palier final."""

    pack: Pack
    entries: list[tuple[Lesson, int]] = field(default_factory=list)


def grouping_pack_id(subject_id: uuid.UUID, level: LevelEnum, title: str) -> uuid.UUID:
    """Identifiant déterministe d'un pack thématique, dérivé de son titre.

    Rejouer le même plan retombe donc sur les mêmes lignes ``packs`` au lieu d'en
    créer des doublons. Corollaire : **renommer** un pack dans le plan crée un
    nouveau pack — pour un simple changement de titre, épinglez l'identifiant
    existant avec la clé ``"id"`` de l'entrée du plan.
    """
    return uuid.uuid5(PACK_NAMESPACE, f"grouping:{subject_id}:{LevelEnum(level).name}:{title}")


def _dense_ranks(keys: list[int]) -> list[int]:
    """Compacte des paliers quelconques en 1..N, en préservant l'ordre et les groupes."""
    ranks = {key: rank for rank, key in enumerate(sorted(set(keys)), start=1)}
    return [ranks[key] for key in keys]


def _scope(db: Session, subject_slug: str, level: LevelEnum) -> tuple[Subject, list[Lesson]]:
    """Matière et **toutes** ses leçons au niveau demandé, tous parcours confondus."""
    subject = db.query(Subject).filter(Subject.slug == subject_slug).first()
    if subject is None:
        raise PlanError(f"matière inconnue : {subject_slug!r}")
    lessons = (
        db.query(Lesson)
        .join(LearningPath, Lesson.path_id == LearningPath.id)
        .filter(LearningPath.subject_id == subject.id, LearningPath.level == level)
        .order_by(Lesson.order_index, Lesson.name)
        .all()
    )
    if not lessons:
        raise PlanError(f"aucune leçon pour {subject_slug}/{level.value}")
    return subject, lessons


def _index(lessons: list[Lesson]) -> dict[str, Lesson]:
    """Index des leçons par UUID et par nom. Un nom en doublon devient inutilisable."""
    by_key: dict[str, Lesson] = {}
    ambiguous: set[str] = set()
    for lesson in lessons:
        by_key[str(lesson.id)] = lesson
        if lesson.name in by_key:
            ambiguous.add(lesson.name)
        by_key[lesson.name] = lesson
    for name in ambiguous:
        del by_key[name]
    return by_key


def _entry_ref(entry: Any, pack_title: str) -> tuple[str, int | None]:
    """Normalise une entrée de ``lessons`` en (référence, palier déclaré)."""
    if isinstance(entry, str):
        return entry, None
    if isinstance(entry, dict):
        ref = entry.get("lesson") or entry.get("name") or entry.get("id")
        if not isinstance(ref, str):
            raise PlanError(f"pack {pack_title!r} : entrée sans 'lesson'/'name'/'id' — {entry!r}")
        tier = entry.get("tier")
        if tier is not None and not isinstance(tier, int):
            raise PlanError(f"pack {pack_title!r} : 'tier' doit être un entier — {entry!r}")
        return ref, tier
    raise PlanError(f"pack {pack_title!r} : entrée de leçon invalide — {entry!r}")


def _upsert_pack(db: Session, spec: dict[str, Any], subject: Subject, level: LevelEnum, order_index: int) -> Pack:
    """Crée ou met à jour le pack thématique décrit par le plan (sans commit)."""
    title = spec["title"]
    pack_id = uuid.UUID(spec["id"]) if spec.get("id") else grouping_pack_id(subject.id, level, title)
    pack = db.query(Pack).filter(Pack.id == pack_id).first()
    if pack is None:
        pack = Pack(id=pack_id)
        db.add(pack)
    pack.title = title
    pack.emoji = spec.get("emoji") or subject.icon
    pack.description = spec.get("description")
    pack.tags = list(spec.get("tags") or [])
    pack.origin = PackOrigin.OFFICIAL.value
    pack.author_handle = OFFICIAL_AUTHOR_HANDLE
    pack.community_status = CommunityStatus.APPROVED.value
    # Contenu de l'équipe : difficulté déjà évaluée (issue #6), et pack laissé
    # déverrouillé pour que le regroupement reste une activité continue.
    pack.difficulty_ratified = True
    pack.locked = False
    pack.level_min = level
    pack.level_max = level
    pack.order_index = order_index
    if pack.warnings is None:
        pack.warnings = []
    db.flush()
    return pack


def plan_groups(
    db: Session,
    plan: dict[str, Any],
    subject: Subject,
    level: LevelEnum,
    lessons: list[Lesson],
) -> list[Group]:
    """Traduit le plan en affectations, ou lève ``PlanError`` sans rien écrire."""
    specs = plan.get("packs")
    if not isinstance(specs, list) or not specs:
        raise PlanError("le plan doit contenir une liste 'packs' non vide")

    by_key = _index(lessons)
    owner: dict[uuid.UUID, str] = {}
    groups: list[Group] = []

    for order_index, spec in enumerate(specs):
        if not isinstance(spec, dict) or not spec.get("title"):
            raise PlanError(f"pack #{order_index} : 'title' manquant")
        title = spec["title"]
        refs = spec.get("lessons")
        if not isinstance(refs, list) or not refs:
            raise PlanError(f"pack {title!r} : aucun 'lessons' — un pack vide est refusé")

        resolved: list[Lesson] = []
        declared: list[int] = []
        for position, entry in enumerate(refs):
            ref, tier = _entry_ref(entry, title)
            lesson = by_key.get(ref)
            if lesson is None:
                raise PlanError(f"pack {title!r} : leçon introuvable ou nom ambigu — {ref!r}")
            if lesson.id in owner:
                raise PlanError(f"leçon {lesson.name!r} affectée deux fois ({owner[lesson.id]!r} et {title!r})")
            owner[lesson.id] = title
            resolved.append(lesson)
            declared.append(tier if tier is not None else position + 1)

        pack = _upsert_pack(db, spec, subject, level, order_index)
        groups.append(Group(pack=pack, entries=list(zip(resolved, _dense_ranks(declared), strict=True))))

    missing = [lesson.name for lesson in lessons if lesson.id not in owner]
    if missing:
        raise PlanError(
            f"{len(missing)} leçon(s) absente(s) du plan — une leçon sans pack serait mal verrouillée : "
            + ", ".join(repr(name) for name in missing[:10])
            + ("…" if len(missing) > 10 else "")
        )
    return groups


def _previous_tiers(db: Session, subject_slug: str, level: LevelEnum) -> dict[str, int]:
    """Paliers d'avant le **premier** regroupement de ce couple (matière, niveau)."""
    rows = (
        db.query(PackAuditLog)
        .filter(PackAuditLog.action == REGROUP_ACTION)
        .order_by(PackAuditLog.created_at, PackAuditLog.id)
        .all()
    )
    tiers: dict[str, int] = {}
    for row in rows:
        detail = row.detail or {}
        if detail.get("subject") != subject_slug or detail.get("level") != level.value:
            continue
        for lesson_id, snapshot in (detail.get("previous") or {}).items():
            tiers.setdefault(lesson_id, snapshot.get("tier") or 1)
    return tiers


def official_groups(db: Session, subject: Subject, level: LevelEnum, lessons: list[Lesson]) -> list[Group]:
    """Affectation de retour arrière : tout le niveau dans le pack officiel de la matière.

    Les paliers d'origine sont relus dans le journal d'audit du regroupement
    lorsqu'il existe ; à défaut, les paliers courants sont simplement compactés.
    """
    pack = ensure_official_pack(db, subject.id, level, subject.name, subject.icon)
    previous = _previous_tiers(db, subject.slug, level)
    keys = [previous.get(str(lesson.id), lesson.order_index or 1) for lesson in lessons]
    return [Group(pack=pack, entries=list(zip(lessons, _dense_ranks(keys), strict=True)))]


def write_groups(db: Session, groups: list[Group], subject_slug: str, level: LevelEnum) -> tuple[int, set[uuid.UUID]]:
    """Écrit les affectations et journalise l'état précédent.

    Returns:
        Nombre de leçons modifiées, et identifiants des packs qu'elles quittent.
    """
    previous: dict[str, dict[str, Any]] = {}
    vacated: set[uuid.UUID] = set()
    for group in groups:
        for lesson, tier in group.entries:
            if lesson.pack_id == group.pack.id and lesson.order_index == tier:
                continue
            previous[str(lesson.id)] = {"pack_id": str(lesson.pack_id), "tier": lesson.order_index}
            if lesson.pack_id != group.pack.id:
                vacated.add(lesson.pack_id)
            lesson.pack_id = group.pack.id
            lesson.order_index = tier
    if previous:
        # Journalisé une seule fois, et seulement s'il y a eu un changement :
        # rejouer un plan déjà appliqué doit être un vrai no-op, journal compris.
        log_pack_action(
            db,
            pack_id=None,
            actor_id=None,
            action=REGROUP_ACTION,
            detail={"subject": subject_slug, "level": level.value, "previous": previous},
        )
    return len(previous), vacated - {group.pack.id for group in groups}


def describe(groups: list[Group], lessons: list[Lesson]) -> list[str]:
    """Rendu lisible du plan résolu, pour la relecture admin (``--dry-run``)."""
    lines = [f"{len(groups)} pack(s) pour {len(lessons)} leçon(s)"]
    for group in groups:
        lines.append(f"  {group.pack.emoji or '·'} {group.pack.title}  ({len(group.entries)} leçons)")
        for lesson, tier in group.entries:
            moved = "" if lesson.pack_id == group.pack.id and lesson.order_index == tier else "  ←"
            lines.append(f"      palier {tier}  {lesson.name}{moved}")
    return lines


def main(
    plan_path: str | None,
    *,
    subject_slug: str | None = None,
    level_value: str | None = None,
    revert: bool = False,
    dry_run: bool = False,
) -> int:
    plan: dict[str, Any] = {}
    if plan_path:
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
        subject_slug = subject_slug or plan.get("subject")
        level_value = level_value or plan.get("level")
    if not subject_slug or not level_value:
        print("il faut une matière et un niveau (--subject/--level, ou dans le plan)", file=sys.stderr)
        return 2

    db = SessionLocal()
    try:
        level = LevelEnum(level_value)
        subject, lessons = _scope(db, subject_slug, level)
        if revert:
            groups = official_groups(db, subject, level, lessons)
        else:
            groups = plan_groups(db, plan, subject, level, lessons)

        for line in describe(groups, lessons):
            print(line)

        if dry_run:
            db.rollback()
            print(f"(dry-run) rien écrit pour {subject_slug}/{level.value}")
            return 0

        changed, vacated = write_groups(db, groups, subject_slug, level)
        db.commit()
        print(f"{changed} leçon(s) réaffectée(s) pour {subject_slug}/{level.value}")
        for pack in db.query(Pack).filter(Pack.id.in_(vacated)).all() if vacated else []:
            if not pack.lessons:
                print(f"  pack vidé, conservé pour le retour arrière : {pack.title}")
        return 0
    except PlanError as exc:
        db.rollback()
        print(f"plan refusé : {exc}", file=sys.stderr)
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Applique un plan de regroupement thématique (matière + niveau).")
    parser.add_argument(
        "plan", nargs="?", default=None, help="Fichier JSON du plan (inutile avec --revert-to-official)"
    )
    parser.add_argument("--subject", dest="subject", default=None, help="Slug de matière (défaut : celui du plan).")
    parser.add_argument("--level", dest="level", default=None, help="Niveau ps…cm2 (défaut : celui du plan).")
    parser.add_argument(
        "--revert-to-official",
        dest="revert",
        action="store_true",
        help="Remet toutes les leçons du niveau dans le pack officiel de la matière.",
    )
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Affiche le plan sans rien écrire.")
    args = parser.parse_args()
    if not args.plan and not args.revert:
        parser.error("fournir un plan JSON, ou --revert-to-official avec --subject/--level")
    raise SystemExit(
        main(
            args.plan,
            subject_slug=args.subject,
            level_value=args.level,
            revert=args.revert,
            dry_run=args.dry_run,
        )
    )
