"""Bibliothèque parent et surface « Découvrir » : catalogue, opt-in, demandes.

Trois invariants gouvernent ce module ; les enfreindre casse le modèle de
confiance de l'épopée « packs communautaires » :

1. **Opt-in.** « Approuvé » signifie « listé au catalogue parent », jamais
   « livré aux enfants ». Un pack communautaire n'atteint un enfant que par une
   ligne :class:`~app.models.pack.ChildPackAccess` active, ou par
   l'interrupteur d'auto-activation du profil. Deux adultes restent dans la
   chaîne : l'admin qui approuve, puis le garde qui active.
2. **Les packs officiels restent implicites.** Ils n'ont **jamais** de ligne
   d'accès : leur visibilité vient de leur intervalle de niveaux
   (:func:`app.services.packs.official_pack_ids_for_level`). Créer des lignes
   pour eux viderait le tableau de bord de tous les enfants existants le jour
   du déploiement de l'opt-in.
3. **Désactiver masque, ne détruit pas.** La ligne d'accès passe à
   ``enabled=False`` et aucune ligne de progression n'est touchée : la
   réactivation doit retrouver l'enfant là où il s'était arrêté.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Text, and_, cast, distinct, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Exercise, LearningPath, Lesson, LevelEnum, Subject, levels_between
from app.models.contribution import ContributorProfile, PackReport, ReportStatus
from app.models.pack import (
    ChildPackAccess,
    CommunityStatus,
    Pack,
    PackOrigin,
    PackRequest,
    PackRequestStatus,
)
from app.models.user import Profile, User
from app.schemas.library import AccessEntry, DiscoverPack, PackRequestResponse
from app.schemas.pack import PackSummary
from app.services.contributor_legal import ReportReason
from app.services.packs import accessible_pack_ids, log_pack_action


def _catalogue_visible() -> Any:
    """Condition SQL « ce pack a sa place dans un catalogue d'adulte ».

    Les packs officiels y sont quel que soit leur statut communautaire (ils ne
    passent pas par la revue) sauf ``blocked`` ; les packs communautaires
    uniquement une fois approuvés.
    """
    return or_(
        and_(
            Pack.origin == PackOrigin.OFFICIAL.value,
            Pack.community_status != CommunityStatus.BLOCKED.value,
        ),
        and_(
            Pack.origin == PackOrigin.COMMUNITY.value,
            Pack.community_status == CommunityStatus.APPROVED.value,
        ),
    )


def _level_covered(level: LevelEnum) -> Any:
    """Condition SQL « l'intervalle [level_min, level_max] du pack couvre ``level`` ».

    Passe par :func:`app.models.content.levels_between` : l'ordre alphabétique
    des valeurs de niveau est faux (``ce1`` < ``cp``), donc aucune comparaison
    de chaînes n'est permise.
    """
    return and_(
        Pack.level_min.in_(levels_between(LevelEnum.PS, level)),
        Pack.level_max.in_(levels_between(level, LevelEnum.CM2)),
    )


def _subject_exists(subject_slug: str) -> Any:
    """Condition SQL « ce pack contient au moins une leçon de cette matière »."""
    return (
        select(Lesson.id)
        .join(LearningPath, LearningPath.id == Lesson.path_id)
        .join(Subject, Subject.id == LearningPath.subject_id)
        .where(Lesson.pack_id == Pack.id, Subject.slug == subject_slug)
        .exists()
    )


# --------------------------------------------------------------------------- #
# Agrégats de cartes (comptages en lot, jamais N+1)
# --------------------------------------------------------------------------- #
def _families_counts(db: Session, pack_ids: list[UUID]) -> dict[UUID, int]:
    """Nombre d'enfants distincts pour lesquels chaque pack est activé.

    C'est le « N familles utilisent ce pack » du catalogue **et** le
    ``families_reached`` des statistiques d'auteur : les deux surfaces doivent
    afficher le même nombre, sinon l'auteur et le parent se contredisent.
    """
    if not pack_ids:
        return {}
    rows = (
        db.query(ChildPackAccess.pack_id, func.count(distinct(ChildPackAccess.child_id)))
        .filter(ChildPackAccess.pack_id.in_(pack_ids), ChildPackAccess.enabled.is_(True))
        .group_by(ChildPackAccess.pack_id)
        .all()
    )
    return {row[0]: int(row[1]) for row in rows}


def _content_counts(
    db: Session, pack_ids: list[UUID]
) -> tuple[dict[UUID, int], dict[UUID, int], dict[UUID, list[str]]]:
    """(leçons, exercices, icônes de matière) par pack, en trois requêtes groupées."""
    if not pack_ids:
        return {}, {}, {}

    lesson_rows = (
        db.query(Lesson.pack_id, func.count(Lesson.id))
        .filter(Lesson.pack_id.in_(pack_ids))
        .group_by(Lesson.pack_id)
        .all()
    )
    exercise_rows = (
        db.query(Lesson.pack_id, func.count(Exercise.id))
        .join(Exercise, Exercise.lesson_id == Lesson.id)
        .filter(Lesson.pack_id.in_(pack_ids))
        .group_by(Lesson.pack_id)
        .all()
    )
    icon_rows = (
        db.query(Lesson.pack_id, Subject.icon)
        .join(LearningPath, LearningPath.id == Lesson.path_id)
        .join(Subject, Subject.id == LearningPath.subject_id)
        .filter(Lesson.pack_id.in_(pack_ids))
        .distinct()
        .all()
    )
    icons: dict[UUID, list[str]] = {}
    for pack_id, icon in icon_rows:
        if icon:
            icons.setdefault(pack_id, []).append(icon)
    return (
        {row[0]: int(row[1]) for row in lesson_rows},
        {row[0]: int(row[1]) for row in exercise_rows},
        icons,
    )


def summaries(db: Session, packs: list[Pack]) -> list[PackSummary]:
    """Cartes de packs enrichies des comptages, en lot.

    Variante *bulk* de :func:`app.services.contribution.pack_summary` : le
    catalogue liste des dizaines de packs et ne peut pas payer une requête par
    ligne. L'aperçu unitaire, lui, délègue toujours à ``pack_detail``.
    """
    pack_ids: list[UUID] = [pack.id for pack in packs]
    families = _families_counts(db, pack_ids)
    lessons, exercises, icons = _content_counts(db, pack_ids)
    return [
        PackSummary.model_validate(pack).model_copy(
            update={
                "lesson_count": lessons.get(pack.id, 0),
                "exercise_count": exercises.get(pack.id, 0),
                "subject_icons": icons.get(pack.id, []),
                "families_count": families.get(pack.id, 0),
            }
        )
        for pack in packs
    ]


# --------------------------------------------------------------------------- #
# Catalogue
# --------------------------------------------------------------------------- #
def catalogue(
    db: Session,
    *,
    level: LevelEnum | None = None,
    subject_slug: str | None = None,
    tag: str | None = None,
    sort: str = "newest",
    limit: int = 50,
    offset: int = 0,
) -> list[PackSummary]:
    """Catalogue parent : packs officiels (non bloqués) et communautaires approuvés.

    Args:
        db: Session de base de données.
        level: Ne garde que les packs dont l'intervalle de niveaux couvre ``level``.
        subject_slug: Ne garde que les packs contenant une leçon de cette matière.
        tag: Ne garde que les packs portant cette étiquette.
        sort: ``'newest'`` (par date d'approbation, à défaut de création) ou
            ``'most_enabled'`` (signal social : nombre de familles).
        limit: Taille de page.
        offset: Décalage de page.

    Returns:
        Les cartes de packs de la page demandée.
    """
    enabled_counts = (
        db.query(
            ChildPackAccess.pack_id.label("pack_id"),
            func.count(distinct(ChildPackAccess.child_id)).label("families"),
        )
        .filter(ChildPackAccess.enabled.is_(True))
        .group_by(ChildPackAccess.pack_id)
        .subquery()
    )

    query = db.query(Pack).outerjoin(enabled_counts, enabled_counts.c.pack_id == Pack.id).filter(_catalogue_visible())

    if level is not None:
        query = query.filter(_level_covered(level))
    if subject_slug:
        query = query.filter(_subject_exists(subject_slug))
    if tag:
        # ``tags`` est une colonne JSON : aucun opérateur de conteneur n'est
        # portable entre SQLite (tests) et Postgres (production). Le rendu texte
        # d'une liste JSON encadre chaque élément de guillemets, donc chercher
        # ``"tag"`` cible bien un élément entier et non un préfixe.
        query = query.filter(cast(Pack.tags, Text).like(f'%"{tag}"%'))

    if sort == "most_enabled":
        query = query.order_by(func.coalesce(enabled_counts.c.families, 0).desc(), Pack.title.asc())
    else:
        # ``coalesce`` plutôt que ``nullslast`` : le tri des NULL en DESC diffère
        # entre SQLite et Postgres, et un pack officiel n'a pas de ``reviewed_at``.
        query = query.order_by(func.coalesce(Pack.reviewed_at, Pack.created_at).desc(), Pack.title.asc())

    packs = query.limit(limit).offset(offset).all()
    return summaries(db, packs)


def catalogue_pack(db: Session, pack_id: UUID) -> Pack | None:
    """Pack du catalogue (aperçu avant activation), ou ``None`` s'il n'y est pas."""
    return db.query(Pack).filter(Pack.id == pack_id).filter(_catalogue_visible()).first()


# --------------------------------------------------------------------------- #
# Liste blanche par enfant
# --------------------------------------------------------------------------- #
def access_entries(db: Session, child_id: UUID) -> list[AccessEntry]:
    """Lignes d'accès explicites d'un enfant, packs joints.

    Les packs ``official`` en sont absents par construction : ils n'ont pas de
    ligne d'accès (invariant 2 du module).
    """
    rows = (
        db.query(ChildPackAccess)
        .filter(ChildPackAccess.child_id == child_id)
        .order_by(ChildPackAccess.enabled_at.desc())
        .all()
    )
    if not rows:
        return []
    packs = db.query(Pack).filter(Pack.id.in_([r.pack_id for r in rows])).all()
    cards = {card.id: card for card in summaries(db, packs)}
    return [
        AccessEntry(
            pack_id=row.pack_id,
            enabled=bool(row.enabled),
            enabled_by=row.enabled_by,
            enabled_at=row.enabled_at,
            updated_at=row.updated_at,
            pack=cards[row.pack_id],
        )
        for row in rows
        if row.pack_id in cards
    ]


def set_access(
    db: Session,
    *,
    child_id: UUID,
    pack_id: UUID,
    enabled: bool,
    guardian: User,
) -> ChildPackAccess:
    """Active ou désactive un pack pour un enfant, et journalise le garde acteur.

    Gardes concurrents : le dernier écrit gagne, et ``enabled_by`` plus le
    journal d'audit disent lequel. Une désactivation **conserve** la ligne et ne
    touche à aucune ligne de progression : l'enfant qui retrouve le pack
    retrouve son avancement.

    Raises:
        HTTPException: 404 si le pack n'existe pas.
    """
    pack = db.query(Pack).filter(Pack.id == pack_id).first()
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pack non trouvé.")

    row = (
        db.query(ChildPackAccess)
        .filter(ChildPackAccess.child_id == child_id, ChildPackAccess.pack_id == pack_id)
        .first()
    )
    if row is None:
        row = ChildPackAccess(child_id=child_id, pack_id=pack_id)
        db.add(row)
    row.enabled = enabled
    row.enabled_by = guardian.id
    if enabled:
        # Sert d'horodatage « depuis quand ce pack est-il disponible » : remis à
        # jour à chaque réactivation, laissé intact par une désactivation.
        row.enabled_at = datetime.utcnow()

    log_pack_action(
        db,
        pack_id=pack_id,
        actor_id=guardian.id,
        action="access_enabled" if enabled else "access_disabled",
        detail={"child_id": str(child_id)},
    )
    db.commit()
    db.refresh(row)
    return row


def set_auto_enable(db: Session, *, child_id: UUID, enabled: bool, guardian: User) -> Profile:
    """Écrit l'interrupteur d'auto-activation du profil de l'enfant.

    Par enfant, désactivé par défaut : c'est l'opt-in explicite qui garde deux
    adultes dans la chaîne. Le parent qui fait confiance à la revue peut ouvrir
    le robinet, mais il doit le faire pour chaque enfant.

    Raises:
        HTTPException: 404 si l'enfant n'a pas de profil.
    """
    profile = db.query(Profile).filter(Profile.user_id == child_id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enfant non trouvé.")
    profile.auto_enable_approved_packs = enabled
    log_pack_action(
        db,
        pack_id=None,
        actor_id=guardian.id,
        action="auto_enable_on" if enabled else "auto_enable_off",
        detail={"child_id": str(child_id)},
    )
    db.commit()
    db.refresh(profile)
    return profile


# --------------------------------------------------------------------------- #
# Statistiques d'auteur
# --------------------------------------------------------------------------- #
def contributor_stats(db: Session, user_id: UUID) -> dict[str, Any]:
    """Compte ce qu'un auteur a produit et l'usage réel qui en est fait.

    La reconnaissance est la seule récompense offerte : ces nombres sont donc
    calculés sur les lignes d'accès réelles, jamais estimés.
    """
    profile = db.query(ContributorProfile).filter(ContributorProfile.user_id == user_id).first()

    approved_ids = [
        row[0]
        for row in db.query(Pack.id).filter(
            Pack.author_id == user_id,
            Pack.community_status == CommunityStatus.APPROVED.value,
        )
    ]
    pending = (
        db.query(func.count(Pack.id))
        .filter(Pack.author_id == user_id, Pack.community_status == CommunityStatus.PENDING.value)
        .scalar()
        or 0
    )

    times_enabled = 0
    families_reached = 0
    if approved_ids:
        times_enabled = (
            db.query(func.count(ChildPackAccess.id))
            .filter(ChildPackAccess.pack_id.in_(approved_ids), ChildPackAccess.enabled.is_(True))
            .scalar()
            or 0
        )
        families_reached = (
            db.query(func.count(distinct(ChildPackAccess.child_id)))
            .filter(ChildPackAccess.pack_id.in_(approved_ids), ChildPackAccess.enabled.is_(True))
            .scalar()
            or 0
        )

    return {
        "handle": profile.handle if profile else None,
        "trusted": bool(profile.trusted) if profile else False,
        "packs_approved": len(approved_ids),
        "packs_pending": int(pending),
        "times_enabled": int(times_enabled),
        "families_reached": int(families_reached),
    }


# --------------------------------------------------------------------------- #
# Découvrir : demandes de l'enfant
# --------------------------------------------------------------------------- #
def discoverable(db: Session, *, child_id: UUID, level: LevelEnum, limit: int = 50) -> list[DiscoverPack]:
    """Packs communautaires approuvés au niveau de l'enfant, hors déjà accessibles.

    Ne renvoie **que** des métadonnées adaptées à l'enfant : aucun statut de
    modération, aucun score qualité, aucune note de revue.
    """
    already = accessible_pack_ids(child_id, level, db) or set()
    query = db.query(Pack).filter(
        Pack.origin == PackOrigin.COMMUNITY.value,
        Pack.community_status == CommunityStatus.APPROVED.value,
        _level_covered(level),
    )
    if already:
        query = query.filter(Pack.id.notin_(already))
    packs = query.order_by(func.coalesce(Pack.reviewed_at, Pack.created_at).desc(), Pack.title.asc()).limit(limit).all()

    pending = {
        row[0]
        for row in db.query(PackRequest.pack_id).filter(
            PackRequest.child_id == child_id,
            PackRequest.status == PackRequestStatus.PENDING.value,
        )
    }
    pack_ids: list[UUID] = [pack.id for pack in packs]
    lesson_counts, _, icon_map = _content_counts(db, pack_ids)
    families = _families_counts(db, pack_ids)
    return [
        DiscoverPack(
            id=pack.id,
            title=pack.title,
            emoji=pack.emoji,
            description=pack.description,
            subject_icons=icon_map.get(pack.id, []),
            lesson_count=lesson_counts.get(pack.id, 0),
            families_count=families.get(pack.id, 0),
            author_handle=pack.author_handle,
            requested=pack.id in pending,
        )
        for pack in packs
    ]


def _requests_today(db: Session, child_id: UUID) -> int:
    """Demandes émises par l'enfant depuis minuit (heure serveur, UTC)."""
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(func.count(PackRequest.id))
        .filter(PackRequest.child_id == child_id, PackRequest.created_at >= start)
        .scalar()
        or 0
    )


def request_pack(db: Session, *, child_id: UUID, pack_id: UUID) -> PackRequest:
    """Enregistre un « Je veux ça ! ». N'accorde **jamais** l'accès.

    Une demande déjà en attente est renvoyée telle quelle (l'enfant qui tape
    deux fois ne doit pas consommer deux fois son quota).

    Raises:
        HTTPException: 404 si le pack n'est pas demandable, 409 s'il est déjà
            activé, 429 si le quota journalier de l'enfant est atteint.
    """
    pack = (
        db.query(Pack)
        .filter(
            Pack.id == pack_id,
            Pack.origin == PackOrigin.COMMUNITY.value,
            Pack.community_status == CommunityStatus.APPROVED.value,
        )
        .first()
    )
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pack non trouvé.")

    existing = (
        db.query(PackRequest)
        .filter(
            PackRequest.child_id == child_id,
            PackRequest.pack_id == pack_id,
            PackRequest.status == PackRequestStatus.PENDING.value,
        )
        .first()
    )
    if existing is not None:
        return existing

    enabled = (
        db.query(ChildPackAccess)
        .filter(
            ChildPackAccess.child_id == child_id,
            ChildPackAccess.pack_id == pack_id,
            ChildPackAccess.enabled.is_(True),
        )
        .first()
    )
    if enabled is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce pack est déjà activé.")

    if _requests_today(db, child_id) >= settings.PACK_MAX_REQUESTS_PER_CHILD_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de demandes aujourd'hui. Réessaie demain !",
        )

    request = PackRequest(child_id=child_id, pack_id=pack_id, status=PackRequestStatus.PENDING.value)
    db.add(request)
    log_pack_action(
        db, pack_id=pack_id, actor_id=child_id, action="request_created", detail={"child_id": str(child_id)}
    )
    db.commit()
    db.refresh(request)
    return request


def decide_request(db: Session, *, request: PackRequest, approve: bool, guardian: User) -> PackRequest:
    """Tranche une demande. L'approbation écrit la ligne d'accès et l'audite.

    Raises:
        HTTPException: 409 si la demande a déjà été tranchée.
    """
    if request.status != PackRequestStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cette demande a déjà été traitée.")

    request.status = PackRequestStatus.APPROVED.value if approve else PackRequestStatus.DECLINED.value
    request.decided_at = datetime.utcnow()
    request.decided_by = guardian.id
    log_pack_action(
        db,
        pack_id=request.pack_id,
        actor_id=guardian.id,
        action="request_approved" if approve else "request_declined",
        detail={"child_id": str(request.child_id), "request_id": str(request.id)},
    )
    db.commit()

    if approve:
        # ``set_access`` commite : l'ordre importe peu, mais passer par lui garde
        # une seule écriture possible de la liste blanche (et un seul audit).
        set_access(db, child_id=request.child_id, pack_id=request.pack_id, enabled=True, guardian=guardian)

    db.refresh(request)
    return request


def request_response(db: Session, request: PackRequest) -> PackRequestResponse:
    """DTO d'une demande, avec le titre du pack et le prénom de l'enfant."""
    pack = db.query(Pack).filter(Pack.id == request.pack_id).first()
    profile = db.query(Profile).filter(Profile.user_id == request.child_id).first()
    return PackRequestResponse(
        id=request.id,
        child_id=request.child_id,
        child_name=profile.display_name if profile else None,
        pack_id=request.pack_id,
        pack_title=pack.title if pack else "",
        pack_emoji=pack.emoji if pack else None,
        status=request.status,
        created_at=request.created_at,
        decided_at=request.decided_at,
        decided_by=request.decided_by,
    )


def pending_requests_for_guardian(db: Session, child_ids: list[UUID]) -> list[PackRequest]:
    """Demandes en attente de tous les enfants dont l'appelant est responsable."""
    if not child_ids:
        return []
    return (
        db.query(PackRequest)
        .filter(
            PackRequest.child_id.in_(child_ids),
            PackRequest.status == PackRequestStatus.PENDING.value,
        )
        .order_by(PackRequest.created_at.asc())
        .all()
    )


def child_requests(db: Session, child_id: UUID) -> list[PackRequest]:
    """Demandes en attente d'un enfant (sa propre vue « Découvrir »)."""
    return (
        db.query(PackRequest)
        .filter(PackRequest.child_id == child_id, PackRequest.status == PackRequestStatus.PENDING.value)
        .order_by(PackRequest.created_at.asc())
        .all()
    )


# --------------------------------------------------------------------------- #
# Signalements
# --------------------------------------------------------------------------- #
def report_pack(
    db: Session,
    *,
    pack_id: UUID,
    reporter_id: UUID,
    reason: ReportReason,
    details: str | None = None,
) -> PackReport:
    """Enregistre un signalement ``open``, repris par la file de modération.

    C'est le filet de sécurité des auteurs « de confiance » : leur contenu
    publie sans revue préalable, donc le signalement est la seule voie de
    recours d'un parent qui découvre un problème.

    Raises:
        HTTPException: 404 si le pack n'existe pas.
    """
    pack = db.query(Pack).filter(Pack.id == pack_id).first()
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pack non trouvé.")

    report = PackReport(
        pack_id=pack_id,
        reporter_id=reporter_id,
        reason=ReportReason(reason).value,
        details=details,
        status=ReportStatus.OPEN.value,
    )
    db.add(report)
    log_pack_action(db, pack_id=pack_id, actor_id=reporter_id, action="report", detail={"reason": str(reason)})
    db.commit()
    db.refresh(report)
    return report


__all__ = [
    "access_entries",
    "catalogue",
    "catalogue_pack",
    "child_requests",
    "contributor_stats",
    "decide_request",
    "discoverable",
    "pending_requests_for_guardian",
    "report_pack",
    "request_pack",
    "request_response",
    "set_access",
    "set_auto_enable",
    "summaries",
]
