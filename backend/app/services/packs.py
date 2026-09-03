"""Substrat des packs : identité des packs officiels, résolution d'accès, audit.

Ce module est la **source de vérité unique** de deux questions que plusieurs
surfaces se posent :

1. « Quel est le pack officiel de cette matière et de ce niveau ? » — utilisé par
   les seeders et par la création de leçon, et dérivé de façon déterministe pour
   que la migration Alembic et le code applicatif tombent sur le même pack.
2. « Quels packs cet enfant a-t-il le droit de voir ? » — la liste blanche
   d'accès. Le contenu ``official`` est implicite (sinon le tableau de bord de
   tous les enfants se viderait le jour où l'opt-in est livré) ; le contenu
   ``community`` exige une ligne d'accès explicite, ou l'interrupteur
   « activer automatiquement les packs approuvés de mon niveau ».
"""

import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Exercise, LevelEnum, levels_between
from app.models.pack import (
    ChildPackAccess,
    CommunityStatus,
    Pack,
    PackOrigin,
)
from app.models.user import Profile

#: Même espace de noms que la migration ``d4a1c9e05b21`` : les identifiants des
#: packs officiels doivent être identiques côté migration et côté application,
#: sinon un seeder recréerait un pack parallèle pour la même matière+niveau.
PACK_NAMESPACE = uuid.UUID("6f1b2c94-8a1d-4f7e-9c3b-2f5d7a0e91c4")

OFFICIAL_AUTHOR_HANDLE = "Explorito"


def official_pack_id(subject_id: UUID, level: LevelEnum) -> UUID:
    """Identifiant déterministe du pack officiel d'un couple (matière, niveau).

    La clé utilise le **nom** du membre d'énumération (``CP``), comme la colonne
    ``learning_paths.level`` en base, pour rester alignée avec la migration.
    """
    return uuid.uuid5(PACK_NAMESPACE, f"official:{subject_id}:{LevelEnum(level).name}")


def ensure_official_pack(db: Session, subject_id: UUID, level: LevelEnum, subject_name: str, emoji: str | None) -> Pack:
    """Récupère (ou crée) le pack officiel d'une matière et d'un niveau.

    Appelé par tous les chemins d'ingestion « équipe » (seeders, création de leçon
    par un admin) afin qu'aucune leçon ne puisse naître sans pack.

    Args:
        db: Session de base de données.
        subject_id: Matière de la leçon.
        level: Niveau scolaire du parcours.
        subject_name: Nom de la matière, pour le titre du pack.
        emoji: Icône de la matière, réutilisée comme emoji du pack.

    Returns:
        Le pack officiel correspondant, créé si nécessaire (non commité).
    """
    level = LevelEnum(level)
    pack_id = official_pack_id(subject_id, level)
    pack = db.query(Pack).filter(Pack.id == pack_id).first()
    if pack is not None:
        return pack

    label = level.name
    pack = Pack(
        id=pack_id,
        title=f"{subject_name} — {label}",
        emoji=emoji,
        description=f"Contenu officiel Explorito — {subject_name}, niveau {label}.",
        origin=PackOrigin.OFFICIAL.value,
        author_handle=OFFICIAL_AUTHOR_HANDLE,
        community_status=CommunityStatus.APPROVED.value,
        difficulty_ratified=True,
        locked=False,
        tags=[],
        warnings=[],
        level_min=level,
        level_max=level,
    )
    db.add(pack)
    db.flush()
    return pack


def official_pack_ids_for_level(db: Session, level: LevelEnum) -> set[UUID]:
    """Packs officiels dont l'intervalle de niveaux couvre ``level``."""
    rows = (
        db.query(Pack.id)
        .filter(
            Pack.origin == PackOrigin.OFFICIAL.value,
            Pack.community_status != CommunityStatus.BLOCKED.value,
            Pack.level_min.in_(levels_between(LevelEnum.PS, level)),
            Pack.level_max.in_(levels_between(level, LevelEnum.CM2)),
        )
        .all()
    )
    return {row[0] for row in rows}


def accessible_pack_ids(child_id: UUID, level: LevelEnum | None, db: Session) -> set[UUID] | None:
    """Packs visibles par un enfant, ou ``None`` s'il n'y a pas de filtrage.

    ``None`` (parent, admin — ``level`` non défini) signifie « aucune
    restriction », ce qui laisse les écrans d'administration voir tout le contenu.

    La résolution réunit quatre sources, puis retire deux vetos :

    - les packs ``official`` couvrant le niveau de l'enfant (implicites) ;
    - les packs pour lesquels un garde a créé une ligne d'accès active ;
    - si l'enfant a l'interrupteur d'auto-activation, tous les packs
      communautaires approuvés couvrant son niveau ;
    - les packs rédigés par un garde de l'enfant (:func:`author_family_pack_ids`).

    Vetos, appliqués **après** l'union :

    - une ligne d'accès explicitement désactivée (``enabled = False``) : sans ce
      veto, l'auto-activation réactiverait le pack au tour suivant et un parent
      ne pourrait plus retirer un pack précis sans couper tout l'interrupteur ;
    - ``community_status = blocked``, qui masque pour tout le monde, auteur inclus.
    """
    if level is None:
        return None

    allowed = official_pack_ids_for_level(db, level)

    # Une seule lecture des lignes d'accès : les actives autorisent, les
    # désactivées interdisent.
    access_rows = (
        db.query(ChildPackAccess.pack_id, ChildPackAccess.enabled).filter(ChildPackAccess.child_id == child_id).all()
    )
    allowed.update(pack_id for pack_id, enabled in access_rows if enabled)
    vetoed = {pack_id for pack_id, enabled in access_rows if not enabled}

    profile = db.query(Profile).filter(Profile.user_id == child_id).first()
    if profile is not None and bool(profile.auto_enable_approved_packs):
        auto = (
            db.query(Pack.id)
            .filter(
                Pack.origin == PackOrigin.COMMUNITY.value,
                Pack.community_status == CommunityStatus.APPROVED.value,
                Pack.level_min.in_(levels_between(LevelEnum.PS, level)),
                Pack.level_max.in_(levels_between(level, LevelEnum.CM2)),
            )
            .all()
        )
        allowed.update(row[0] for row in auto)

    allowed.update(author_family_pack_ids(child_id, db))
    allowed -= vetoed

    blocked = {
        row[0]
        for row in db.query(Pack.id)
        .filter(Pack.id.in_(allowed), Pack.community_status == CommunityStatus.BLOCKED.value)
        .all()
    }
    return allowed - blocked


def author_family_pack_ids(child_id: UUID, db: Session) -> set[UUID]:
    """Packs rédigés par un garde de cet enfant, utilisables immédiatement.

    C'est la promesse de la phase « contribution » : un parent ajoute des leçons
    **pour son propre enfant** sans attendre de modération. Le refus
    communautaire (``rejected``) ne retire donc rien à la famille de l'auteur ;
    seul ``blocked`` le fait.
    """
    from app.models.guardianship import Guardianship

    guardian_ids = [row[0] for row in db.query(Guardianship.guardian_id).filter(Guardianship.child_id == child_id)]
    if not guardian_ids:
        return set()
    rows = (
        db.query(Pack.id)
        .filter(
            Pack.author_id.in_(guardian_ids),
            Pack.community_status != CommunityStatus.BLOCKED.value,
        )
        .all()
    )
    return {row[0] for row in rows}


def log_pack_action(
    db: Session,
    *,
    pack_id: UUID | None,
    actor_id: UUID | None,
    action: str,
    detail: dict[str, Any] | None = None,
) -> None:
    """Ajoute une ligne au journal d'audit des packs (non commitée)."""
    from app.models.contribution import PackAuditLog

    db.add(
        PackAuditLog(
            pack_id=pack_id,
            actor_id=actor_id,
            action=action,
            detail=detail or {},
        )
    )


def derive_lesson_xp(difficulty_levels: list[int | None], *, ratified: bool = True) -> int:
    """XP d'une leçon **dérivée du contenu**, jamais de la déclaration de l'auteur.

    Somme des XP de base par exercice selon ``difficulty_level`` (repli sur le
    tarif forfaitaire quand la difficulté n'est pas renseignée). Utilisée à
    l'insertion pour écraser tout ``xp_reward`` présent dans un fichier
    ``.explorito`` : l'XP achète des collectionnables, donc un champ libre serait
    une imprimante à billets.

    ``ratified=False`` applique le tarif forfaitaire, exactement comme
    :func:`app.services.gamification.xp_for_exercise`. Sans cela la valeur
    stockée mentirait à l'écran : une leçon non ratifiée afficherait
    « +150 XP » alors que l'enfant en gagnerait 50.

    Args:
        difficulty_levels: Difficultés fines (1→5) des exercices de la leçon.
        ratified: Vrai si la difficulté du pack a été ratifiée à la revue.

    Returns:
        XP de complétion de la leçon.
    """
    if not ratified:
        return len(difficulty_levels) * settings.XP_PER_EXERCISE
    total = 0
    for level in difficulty_levels:
        if level is not None and int(level) in settings.XP_BY_LEVEL:
            total += settings.XP_BY_LEVEL[int(level)]
        else:
            total += settings.XP_PER_EXERCISE
    return total


def _write_lesson_xp(db: Session, lesson_id: UUID, *, ratified: bool) -> int:
    """Écrit ``Lesson.xp_reward`` d'après les difficultés de ses exercices."""
    from app.models.content import Lesson

    levels = [row[0] for row in db.query(Exercise.difficulty_level).filter(Exercise.lesson_id == lesson_id)]
    xp = derive_lesson_xp(levels, ratified=ratified)
    db.query(Lesson).filter(Lesson.id == lesson_id).update({"xp_reward": xp}, synchronize_session=False)
    return xp


def refresh_lesson_xp(db: Session, lesson_id: UUID) -> int:
    """Recalcule et écrit ``Lesson.xp_reward`` depuis les exercices de la leçon.

    Le tarif suit l'état de ratification du pack propriétaire, pour que la
    valeur stockée soit celle que l'enfant gagnera réellement.
    """
    from app.models.content import Lesson

    row = (
        db.query(Pack.difficulty_ratified)
        .join(Lesson, Lesson.pack_id == Pack.id)
        .filter(Lesson.id == lesson_id)
        .first()
    )
    return _write_lesson_xp(db, lesson_id, ratified=bool(row[0]) if row is not None else True)


def refresh_pack_lesson_xp(db: Session, pack: Pack) -> None:
    """Recalcule l'XP de toutes les leçons d'un pack.

    À appeler après un changement de ``difficulty_ratified`` : la ratification
    fait passer le pack du tarif forfaitaire au tarif gradué, et les valeurs
    affichées doivent suivre. N'altère jamais l'XP **déjà attribuée** — seule la
    récompense annoncée des leçons est recalculée.

    L'état de ratification est lu sur **l'instance**, pas en base : l'appelant
    vient typiquement de le modifier sans flush, et une relecture SQL renverrait
    l'ancienne valeur.
    """
    from app.models.content import Lesson

    ratified = bool(pack.difficulty_ratified)
    for (lesson_id,) in db.query(Lesson.id).filter(Lesson.pack_id == pack.id):
        _write_lesson_xp(db, lesson_id, ratified=ratified)


def mark_reviewed(pack: Pack, reviewer_id: UUID | None, status: CommunityStatus) -> None:
    """Applique un verdict de modération sur un pack (sans commit)."""
    pack.community_status = status.value
    pack.reviewed_at = datetime.utcnow()
    pack.reviewed_by = reviewer_id
    if status is CommunityStatus.APPROVED:
        # L'approbation ratifie la difficulté (donc l'XP gradué) et verrouille le
        # pack : à partir de là, l'auteur révise en clonant.
        pack.difficulty_ratified = True
        pack.locked = True
