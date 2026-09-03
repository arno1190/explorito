"""Modèle de lecture du chemin d'accueil de l'enfant, orienté packs.

Ce module répond à une seule question — « que voit cet enfant, et que doit-il
faire ensuite ? » — et il y répond **côté serveur**, pour trois raisons :

- le verrou est calculé par :func:`app.services.progression.lesson_locked`, seule
  source de vérité ; le client l'affiche mais ne le rejoue jamais ;
- la carte « Continuer » (décision 10) doit désigner la même leçon dans les deux
  lentilles et dans toute surface future — la résoudre dans un composant
  garantirait la divergence ;
- le cumul par pack (décision 17) doit porter étoiles, XP et date, sinon replier
  un pack terminé se lit comme un retrait de contenu.

Rien n'est filtré à la complétion : les leçons terminées **restent** dans la
charge utile (le client les replie), pour que le contenu de
:class:`app.models.review.ReviewQueue` reste atteignable depuis un pack fini.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.content import Exercise, LearningPath, Lesson, LevelEnum, Subject
from app.models.pack import Pack
from app.models.progress import ProgressStatus, UserProgress
from app.models.user import Profile
from app.schemas.pack import PackSummary
from app.schemas.pack_path import (
    ContinuerCard,
    PackLens,
    PackPathEntry,
    PackPathLesson,
    PackPathResponse,
    PackPathRollup,
)
from app.services.packs import accessible_pack_ids
from app.services.progression import lesson_locked

#: Étoiles maximales par leçon (barème de ``UserProgress.stars``).
STARS_PER_LESSON = 3

DEFAULT_LENS: PackLens = "themes"


def _lock_resolver(child_id: UUID, level: LevelEnum | None, db: Session) -> Callable[[Lesson], bool]:
    """Ferme mémoïsée autour de :func:`lesson_locked`.

    Le verrou reste calculé par le service de progression — jamais réimplémenté
    ici. Il ne dépend de la leçon que par sa **portée** (pack, parcours) et son
    **palier** : deux leçons du même palier d'un même pack ont donc forcément le
    même verrou, et une seule évaluation suffit pour tout le groupe. Sans ce
    cache, le chemin d'accueil ferait deux requêtes par leçon affichée.
    """
    cache: dict[tuple[UUID, UUID, int], bool] = {}

    def locked(lesson: Lesson) -> bool:
        key = (lesson.pack_id, lesson.path_id, int(lesson.order_index or 0))
        if key not in cache:
            cache[key] = lesson_locked(child_id, lesson, level, db)
        return cache[key]

    return locked


def _lesson_status(progress: UserProgress | None, locked: bool) -> ProgressStatus:
    """Statut affiché d'une leçon sans ligne de progression.

    Une leçon jamais ouverte n'a pas de ligne ``user_progress`` : son statut est
    déduit du verrou, ce qui évite de faire croire au client qu'elle est
    « disponible » alors qu'un palier inférieur la bloque.
    """
    if progress is not None:
        return ProgressStatus(progress.status)
    return ProgressStatus.LOCKED if locked else ProgressStatus.AVAILABLE


def _rollup(lessons: list[PackPathLesson]) -> PackPathRollup:
    """Cumul d'un pack : étoiles, XP et date de la dernière leçon terminée."""
    done = [lesson for lesson in lessons if lesson.status == ProgressStatus.COMPLETED]
    dates = [lesson.completed_at for lesson in done if lesson.completed_at is not None]
    return PackPathRollup(
        lessons_total=len(lessons),
        lessons_completed=len(done),
        stars_earned=sum(lesson.stars for lesson in lessons),
        stars_total=STARS_PER_LESSON * len(lessons),
        xp_banked=sum(lesson.xp_earned for lesson in lessons),
        xp_total=sum(lesson.xp_reward for lesson in lessons),
        completed_at=max(dates) if dates else None,
        complete=bool(lessons) and len(done) == len(lessons),
    )


def _pack_summary(pack: Pack, lessons: list[PackPathLesson]) -> PackSummary:
    """Carte du pack construite depuis les leçons **déjà chargées**.

    On ne passe pas par ``services.contribution.pack_summary`` : celle-ci
    requête par pack, ce qui rendrait le chemin d'accueil quadratique. Les
    statistiques de catalogue (``families_count``) restent à leur défaut, elles
    n'ont pas de sens dans la vue d'un enfant.
    """
    icons = [lesson.subject_icon for lesson in lessons if lesson.subject_icon]
    return PackSummary(
        id=pack.id,
        title=pack.title,
        emoji=pack.emoji,
        description=pack.description,
        origin=pack.origin,
        community_status=pack.community_status,
        author_handle=pack.author_handle,
        tags=list(pack.tags or []),
        quality_score=pack.quality_score,
        difficulty_ratified=bool(pack.difficulty_ratified),
        locked=bool(pack.locked),
        level_min=pack.level_min,
        level_max=pack.level_max,
        lesson_count=len(lessons),
        exercise_count=sum(lesson.exercise_count for lesson in lessons),
        subject_icons=list(dict.fromkeys(icons)),
        created_at=pack.created_at,
        submitted_at=pack.submitted_at,
    )


def _entry_sort_key(entry: PackPathEntry) -> tuple[int, float]:
    """Trie stable : packs en cours d'abord, trophées ensuite (plus récent devant).

    La longueur de l'écran doit rester proportionnelle au travail **restant**
    (décision 17) ; l'ordre éditorial ``Pack.order_index`` est préservé au sein
    de chaque groupe grâce à la stabilité du tri.
    """
    if not entry.rollup.complete:
        return (0, 0.0)
    stamp = entry.rollup.completed_at
    return (1, -stamp.timestamp() if stamp is not None else 0.0)


def pack_path_entries(
    child_id: UUID,
    level: LevelEnum | None,
    db: Session,
    *,
    only_pack_ids: set[UUID] | None = None,
) -> list[PackPathEntry]:
    """Packs accessibles à l'enfant, leçons ordonnées par palier, cumul par pack.

    Coût : 4 requêtes propres (packs, leçons+matières, progression, nombre
    d'exercices) quel que soit le nombre de packs, plus celles de
    :func:`app.services.packs.accessible_pack_ids` et deux requêtes par groupe
    (pack, palier) distinct pour le verrou.

    Args:
        child_id: Enfant dont on construit le chemin.
        level: Niveau de contenu (``None`` = parent/admin, aucun filtrage).
        db: Session de base de données.
        only_pack_ids: Restriction supplémentaire, pour la vue d'un seul pack.

    Returns:
        Les entrées du chemin, packs vides exclus.
    """
    allowed = accessible_pack_ids(child_id, level, db)

    packs_query = db.query(Pack)
    if allowed is not None:
        packs_query = packs_query.filter(Pack.id.in_(allowed))
    if only_pack_ids is not None:
        packs_query = packs_query.filter(Pack.id.in_(only_pack_ids))
    packs = packs_query.order_by(Pack.order_index, Pack.title).all()
    if not packs:
        return []

    rows = (
        db.query(Lesson, Subject, LearningPath.level)
        .join(LearningPath, Lesson.path_id == LearningPath.id)
        .join(Subject, LearningPath.subject_id == Subject.id)
        .filter(Lesson.pack_id.in_([pack.id for pack in packs]))
    )
    if level is not None:
        # Mêmes règles que /subjects/{id}/lessons : un enfant ne voit que son
        # niveau et le contenu publié, même dans un pack qui couvre plusieurs
        # niveaux.
        rows = rows.filter(LearningPath.level == level, Lesson.is_published.is_(True))
    lesson_rows = rows.order_by(Lesson.order_index, Lesson.created_at, Lesson.id).all()

    lesson_ids = [lesson.id for lesson, _, _ in lesson_rows]
    progress_by_lesson: dict[UUID, UserProgress] = {}
    exercise_counts: dict[UUID, int] = {}
    if lesson_ids:
        progress_by_lesson = {
            row.lesson_id: row
            for row in db.query(UserProgress).filter(
                UserProgress.user_id == child_id,
                UserProgress.lesson_id.in_(lesson_ids),
            )
        }
        exercise_counts = dict(
            db.query(Exercise.lesson_id, func.count(Exercise.id))
            .filter(Exercise.lesson_id.in_(lesson_ids))
            .group_by(Exercise.lesson_id)
            .all()
        )

    locked_for = _lock_resolver(child_id, level, db)
    by_pack: dict[UUID, list[PackPathLesson]] = {pack.id: [] for pack in packs}
    for lesson, subject, lesson_level in lesson_rows:
        progress = progress_by_lesson.get(lesson.id)
        locked = locked_for(lesson)
        status = _lesson_status(progress, locked)
        xp_reward = int(lesson.xp_reward or 0)
        by_pack[lesson.pack_id].append(
            PackPathLesson(
                id=lesson.id,
                name=lesson.name,
                description=lesson.description,
                subject_id=subject.id,
                subject_slug=subject.slug,
                subject_name=subject.name,
                subject_icon=subject.icon,
                level=lesson_level,
                tier=int(lesson.order_index or 0),
                xp_reward=xp_reward,
                exercise_count=exercise_counts.get(lesson.id, 0),
                locked=locked,
                status=status,
                stars=int(progress.stars or 0) if progress is not None else 0,
                score=int(progress.score or 0) if progress is not None else 0,
                attempts=int(progress.attempts or 0) if progress is not None else 0,
                started_at=progress.started_at if progress is not None else None,
                completed_at=progress.completed_at if progress is not None else None,
                # Aucune colonne ne stocke l'XP par leçon ; ``Lesson.xp_reward``
                # est dérivé du contenu côté serveur (services.packs), donc c'est
                # le seul chiffre stable à créditer au coffre du pack.
                xp_earned=xp_reward if status == ProgressStatus.COMPLETED else 0,
            )
        )

    entries = [
        PackPathEntry(
            pack=_pack_summary(pack, by_pack[pack.id]),
            lessons=by_pack[pack.id],
            rollup=_rollup(by_pack[pack.id]),
        )
        for pack in packs
        # Un pack dont aucune leçon ne concerne le niveau de l'enfant n'est pas
        # une ligne vide à afficher, c'est du bruit.
        if by_pack[pack.id]
    ]
    entries.sort(key=_entry_sort_key)
    return entries


def _next_lesson(entry: PackPathEntry) -> PackPathLesson | None:
    """Première leçon non terminée et non verrouillée du pack (ordre des paliers)."""
    for lesson in entry.lessons:
        if lesson.status != ProgressStatus.COMPLETED and not lesson.locked:
            return lesson
    return None


def _last_activity(entry: PackPathEntry) -> datetime | None:
    """Dernière trace d'activité de l'enfant dans ce pack, ou ``None`` s'il est intact."""
    stamps = [
        stamp for lesson in entry.lessons for stamp in (lesson.started_at, lesson.completed_at) if stamp is not None
    ]
    return max(stamps) if stamps else None


def _is_started(entry: PackPathEntry) -> bool:
    """Vrai si l'enfant a déjà touché ce pack (leçon terminée ou entamée)."""
    return entry.rollup.lessons_completed > 0 or any(
        lesson.status == ProgressStatus.STARTED for lesson in entry.lessons
    )


def _card(entry: PackPathEntry, lesson: PackPathLesson, reason: Literal["resume", "start"]) -> ContinuerCard:
    """Emballe la leçon retenue avec le pack qui lui donne son sens."""
    return ContinuerCard(
        pack_id=entry.pack.id,
        pack_title=entry.pack.title,
        pack_emoji=entry.pack.emoji,
        reason=reason,
        lesson=lesson,
    )


def continuer_from_entries(entries: list[PackPathEntry]) -> ContinuerCard | None:
    """Résout **une** leçon suivante à partir d'un chemin déjà construit.

    Deux étapes seulement : reprendre le pack entamé le plus récemment, sinon
    démarrer le pack le moins avancé — parmi les packs restants, aucun n'a de
    leçon terminée (sinon il serait « entamé »), donc le moins avancé est le
    premier dans l'ordre éditorial. ``None`` quand il n'y a réellement rien à
    proposer : l'API rend alors un état vide honnête plutôt qu'une
    recommandation inventée.
    """
    resumable: list[tuple[float, int, PackPathEntry, PackPathLesson]] = []
    fresh: list[tuple[PackPathEntry, PackPathLesson]] = []

    for index, entry in enumerate(entries):
        if entry.rollup.complete:
            continue
        target = _next_lesson(entry)
        if target is None:
            continue
        if _is_started(entry):
            stamp = _last_activity(entry)
            # Tri par activité décroissante ; l'index départage les packs entamés
            # sans horodatage exploitable, pour que la carte reste déterministe.
            resumable.append((-stamp.timestamp() if stamp is not None else 0.0, index, entry, target))
        else:
            fresh.append((entry, target))

    if resumable:
        resumable.sort(key=lambda item: (item[0], item[1]))
        return _card(resumable[0][2], resumable[0][3], "resume")
    if fresh:
        return _card(fresh[0][0], fresh[0][1], "start")
    return None


def continuer(child_id: UUID, level: LevelEnum | None, db: Session) -> ContinuerCard | None:
    """Carte « Continuer » seule (mêmes règles que dans :func:`pack_path`)."""
    return continuer_from_entries(pack_path_entries(child_id, level, db))


def pack_lens(child_id: UUID, db: Session) -> PackLens:
    """Lentille enregistrée pour cet enfant, « themes » par défaut."""
    profile = db.query(Profile).filter(Profile.user_id == child_id).first()
    value = profile.pack_lens if profile is not None else None
    return value if value in ("themes", "matieres") else DEFAULT_LENS


def set_pack_lens(child_id: UUID, lens: PackLens, db: Session) -> PackLens | None:
    """Persiste la lentille de cet enfant (sans commit).

    Renvoie ``None`` si l'utilisateur n'a pas de profil : sans profil il n'y a
    nulle part où stocker la préférence, et prétendre l'avoir enregistrée ferait
    réapparaître l'ancienne lentille au rechargement.
    """
    profile = db.query(Profile).filter(Profile.user_id == child_id).first()
    if profile is None:
        return None
    profile.pack_lens = lens
    return lens


def pack_path(child_id: UUID, level: LevelEnum | None, db: Session) -> PackPathResponse:
    """Chemin complet : lentille active, packs accessibles, carte « Continuer »."""
    entries = pack_path_entries(child_id, level, db)
    return PackPathResponse(
        lens=pack_lens(child_id, db),
        entries=entries,
        continuer=continuer_from_entries(entries),
    )
