"""Modération des packs communautaires : file d'attente, verdicts, audit, confiance.

Trois invariants portent tout ce module, et chacun existe parce que le contenu
est déjà chez des enfants au moment où l'admin décide :

1. **Un verdict ne supprime jamais rien.** ``rejected`` retire seulement le pack
   du catalogue communautaire ; ``blocked`` le masque pour tout le monde. Dans
   les deux cas les leçons, les exercices, ``user_progress`` et
   ``exercise_results`` restent en base : effacer priverait un enfant d'un
   travail déjà fait pour une décision qui ne le concerne pas.
2. **La famille de l'auteur est hors de portée d'un refus.** L'accès de sa
   famille vient de :func:`app.services.packs.author_family_pack_ids`, qui
   n'exclut que ``blocked`` : un refus communautaire ne touche donc ni l'XP, ni
   la progression, ni les lignes d'accès. Rien à faire ici — sauf ne rien faire.
3. **Tout ce qu'un admin change est journalisé.** Un pack approuvé est
   verrouillé : l'auteur n'a plus la main, donc « qui a changé quoi » doit être
   reconstituable (:class:`app.models.contribution.PackAuditLog`).
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Exercise, LearningPath, Lesson, LevelEnum, Subject, level_rank
from app.models.contribution import ContributorProfile, PackAuditLog, PackReport, ReportStatus
from app.models.pack import ChildPackAccess, CommunityStatus, Pack, PackOrigin
from app.models.user import User
from app.services.contributor_legal import ANONYMOUS_AUTHOR_HANDLE
from app.services.packs import log_pack_action, mark_reviewed, refresh_pack_lesson_xp

#: Verdicts qu'un humain peut rendre. ``draft`` et ``pending`` sont des états du
#: cycle de vie, pas des décisions : les accepter comme verdict permettrait de
#: « dé-décider » un pack sans trace lisible.
VERDICTS = (CommunityStatus.APPROVED, CommunityStatus.REJECTED, CommunityStatus.BLOCKED)

#: Champs qu'un admin peut corriger à la revue, y compris sur un pack verrouillé.
#: Le titre, l'emoji et la description en font partie parce qu'ils sont visibles
#: par l'enfant **avant** activation : un pack propre au titre grossier atteint
#: quand même son regard.
EDITABLE_FIELDS = ("title", "emoji", "description", "tags", "level_min", "level_max")


def _jsonable(value: Any) -> Any:
    """Valeur stockable dans ``PackAuditLog.detail`` (colonne JSON)."""
    if isinstance(value, LevelEnum):
        return value.value
    if isinstance(value, UUID | datetime):
        return str(value)
    return value


def _counts_by_pack(db: Session, pack_ids: list[UUID]) -> dict[str, dict[UUID, Any]]:
    """Agrégats de la file, en requêtes groupées (jamais une requête par pack)."""
    if not pack_ids:
        return {"lessons": {}, "exercises": {}, "icons": {}, "families": {}, "reports": {}}

    lessons = dict(
        db.query(Lesson.pack_id, func.count(Lesson.id)).filter(Lesson.pack_id.in_(pack_ids)).group_by(Lesson.pack_id)
    )
    exercises = dict(
        db.query(Lesson.pack_id, func.count(Exercise.id))
        .join(Exercise, Exercise.lesson_id == Lesson.id)
        .filter(Lesson.pack_id.in_(pack_ids))
        .group_by(Lesson.pack_id)
    )
    icons: dict[UUID, list[str]] = {}
    icon_rows = (
        db.query(Lesson.pack_id, Subject.icon)
        .join(LearningPath, LearningPath.id == Lesson.path_id)
        .join(Subject, Subject.id == LearningPath.subject_id)
        .filter(Lesson.pack_id.in_(pack_ids))
        .distinct()
    )
    for pack_id, icon in icon_rows:
        if icon and icon not in icons.setdefault(pack_id, []):
            icons[pack_id].append(icon)
    families = dict(
        db.query(ChildPackAccess.pack_id, func.count(func.distinct(ChildPackAccess.child_id)))
        .filter(ChildPackAccess.pack_id.in_(pack_ids), ChildPackAccess.enabled.is_(True))
        .group_by(ChildPackAccess.pack_id)
    )
    reports = dict(
        db.query(PackReport.pack_id, func.count(PackReport.id))
        .filter(PackReport.pack_id.in_(pack_ids), PackReport.status == ReportStatus.OPEN.value)
        .group_by(PackReport.pack_id)
    )
    return {
        "lessons": lessons,
        "exercises": exercises,
        "icons": icons,
        "families": families,
        "reports": reports,
    }


def queue(db: Session, *, status: CommunityStatus = CommunityStatus.PENDING, limit: int = 50) -> list[dict]:
    """Packs en attente de décision, du plus récemment soumis au plus ancien.

    Chaque entrée porte de quoi décider sans ouvrir le pack (volumétrie, score
    qualité, avertissements du validateur, signalements ouverts) **et** sa
    lignée : un pack cloné d'un pack approuvé se revoit en le comparant à son
    parent, pas en le relisant de zéro.

    Args:
        db: Session de base de données.
        status: Statut communautaire filtré (``pending`` par défaut).
        limit: Nombre maximum d'entrées renvoyées.

    Returns:
        Entrées de file, prêtes à alimenter ``ModerationQueueEntry``.
    """
    packs = (
        db.query(Pack)
        .filter(Pack.community_status == status.value)
        .order_by(func.coalesce(Pack.submitted_at, Pack.created_at).desc())
        .limit(limit)
        .all()
    )
    if not packs:
        return []

    agg = _counts_by_pack(db, [pack.id for pack in packs])
    parent_ids = [pack.cloned_from_pack_id for pack in packs if pack.cloned_from_pack_id]
    parent_titles = dict(db.query(Pack.id, Pack.title).filter(Pack.id.in_(parent_ids)).all()) if parent_ids else {}

    return [
        {
            "id": pack.id,
            "title": pack.title,
            "emoji": pack.emoji,
            "description": pack.description,
            "origin": pack.origin,
            "community_status": pack.community_status,
            "author_id": pack.author_id,
            "author_handle": pack.author_handle,
            "tags": list(pack.tags or []),
            "quality_score": pack.quality_score,
            "warnings": list(pack.warnings or []),
            "difficulty_ratified": bool(pack.difficulty_ratified),
            "locked": bool(pack.locked),
            "level_min": pack.level_min,
            "level_max": pack.level_max,
            "lesson_count": agg["lessons"].get(pack.id, 0),
            "exercise_count": agg["exercises"].get(pack.id, 0),
            "subject_icons": agg["icons"].get(pack.id, []),
            "families_count": agg["families"].get(pack.id, 0),
            "open_reports": agg["reports"].get(pack.id, 0),
            "cloned_from_pack_id": pack.cloned_from_pack_id,
            "cloned_from_title": parent_titles.get(pack.cloned_from_pack_id),
            "created_at": pack.created_at,
            "submitted_at": pack.submitted_at,
            "reviewed_at": pack.reviewed_at,
            "review_notes": pack.review_notes,
        }
        for pack in packs
    ]


def apply_verdict(
    db: Session,
    *,
    pack: Pack,
    verdict: CommunityStatus,
    actor_id: UUID | None,
    notes: str | None = None,
    quality_score: int | None = None,
    ratify_difficulty: bool | None = None,
) -> Pack:
    """Écrit la décision humaine sur un pack et la journalise.

    ``approved`` ratifie la difficulté (donc l'XP graduée) et verrouille le pack
    — l'auteur révise ensuite en clonant. ``rejected`` et ``blocked`` ne
    touchent **aucune** ligne d'accès ni de progression : la visibilité est
    entièrement dérivée du statut du pack
    (cf. :func:`app.services.packs.accessible_pack_ids`), donc supprimer des
    lignes n'apporterait rien et détruirait l'historique.

    Args:
        db: Session de base de données.
        pack: Pack décidé.
        verdict: ``approved``, ``rejected`` ou ``blocked``.
        actor_id: Admin auteur de la décision (``None`` si jeton de modération).
        notes: Motivation, renvoyée à l'auteur.
        quality_score: Score 0–100 attribué à la revue.
        ratify_difficulty: Force la ratification (``None`` = comportement par
            défaut du verdict). Un ``False`` explicite à l'approbation dit « le
            contenu passe, mais les étiquettes de difficulté ne sont pas fiables ».

    Returns:
        Le pack rafraîchi.

    Raises:
        HTTPException: 400 si le verdict n'est pas une décision, 409 sur un pack officiel.
    """
    if verdict not in VERDICTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verdict invalide : attendu approved, rejected ou blocked.",
        )
    if pack.origin == PackOrigin.OFFICIAL.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un pack officiel ne passe pas par la modération communautaire.",
        )

    previous = pack.community_status
    was_ratified = bool(pack.difficulty_ratified)
    mark_reviewed(pack, actor_id, verdict)
    if notes is not None:
        pack.review_notes = notes
    if quality_score is not None:
        pack.quality_score = quality_score
    if ratify_difficulty is not None:
        pack.difficulty_ratified = ratify_difficulty
    if bool(pack.difficulty_ratified) != was_ratified:
        # La ratification fait passer le pack du tarif forfaitaire au tarif
        # gradué : la récompense **annoncée** des leçons doit suivre, sinon
        # l'écran promet une XP que l'enfant ne gagnera pas (ou l'inverse).
        # L'XP déjà attribuée n'est jamais recalculée.
        refresh_pack_lesson_xp(db, pack)

    log_pack_action(
        db,
        pack_id=pack.id,
        actor_id=actor_id,
        action="verdict",
        detail={
            "from": previous,
            "verdict": verdict.value,
            "notes": notes,
            "quality_score": pack.quality_score,
            "difficulty_ratified": bool(pack.difficulty_ratified),
            "locked": bool(pack.locked),
        },
    )
    db.commit()
    db.refresh(pack)
    return pack


def admin_edit(db: Session, *, pack: Pack, actor_id: UUID | None, changes: dict[str, Any]) -> dict[str, dict]:
    """Corrige un pack à la revue, verrou compris, en journalisant chaque champ.

    Le verrou protège le pack de son **auteur** (anti bait-and-switch), pas de
    l'admin : la licence de contribution accorde explicitement le droit de
    modifier, et corriger la ligne d'origine profite aussi à l'enfant de
    l'auteur, puisqu'il n'y a qu'une seule ligne.

    Args:
        db: Session de base de données.
        pack: Pack corrigé.
        actor_id: Admin auteur de la correction.
        changes: Champs à écrire, restreints à :data:`EDITABLE_FIELDS`.

    Returns:
        Différentiel ``{champ: {"before": ..., "after": ...}}``, limité aux
        champs réellement modifiés (un différentiel vide n'est pas journalisé).

    Raises:
        HTTPException: 400 sur un champ non éditable ou un intervalle de niveaux inversé.
    """
    unknown = sorted(set(changes) - set(EDITABLE_FIELDS))
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Champs non éditables : {', '.join(unknown)}.",
        )

    level_min = changes.get("level_min", pack.level_min)
    level_max = changes.get("level_max", pack.level_max)
    if level_rank(level_min) > level_rank(level_max):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Intervalle de niveaux inversé (level_min > level_max).",
        )

    diff: dict[str, dict] = {}
    for field, after in changes.items():
        before = getattr(pack, field)
        if before == after:
            continue
        setattr(pack, field, after)
        diff[field] = {"before": _jsonable(before), "after": _jsonable(after)}

    if diff:
        log_pack_action(
            db,
            pack_id=pack.id,
            actor_id=actor_id,
            action="admin_edit",
            detail={"locked": bool(pack.locked), "fields": diff},
        )
    db.commit()
    db.refresh(pack)
    return diff


def _report_dict(report: PackReport, pack_title: str) -> dict:
    return {
        "id": report.id,
        "pack_id": report.pack_id,
        "pack_title": pack_title,
        "reason": report.reason,
        "details": report.details,
        "status": report.status,
        "created_at": report.created_at,
        "resolved_at": report.resolved_at,
    }


def reports(
    db: Session,
    *,
    status: ReportStatus | None = ReportStatus.OPEN,
    pack_id: UUID | None = None,
    limit: int = 50,
) -> list[dict]:
    """Signalements de parents, du plus récent au plus ancien.

    ``status=None`` renvoie tous les statuts ; ``pack_id`` restreint à un pack
    (écran de revue), sans quoi la limite globale pourrait masquer justement
    les signalements du pack qu'on est en train de relire.
    """
    query = db.query(PackReport, Pack.title).join(Pack, Pack.id == PackReport.pack_id)
    if status is not None:
        query = query.filter(PackReport.status == status.value)
    if pack_id is not None:
        query = query.filter(PackReport.pack_id == pack_id)
    rows = query.order_by(PackReport.created_at.desc()).limit(limit).all()
    return [_report_dict(report, title) for report, title in rows]


def report_row(db: Session, report: PackReport) -> dict:
    """Un signalement précis, avec le titre du pack visé."""
    title = db.query(Pack.title).filter(Pack.id == report.pack_id).scalar()
    return _report_dict(report, title or "—")


def resolve_report(
    db: Session,
    *,
    report: PackReport,
    actor_id: UUID | None,
    decision: ReportStatus,
    block_pack: bool = False,
) -> PackReport:
    """Clôt un signalement, en bloquant le pack si le signalement est fondé.

    C'est le chemin « le signalement pilote le blocage » : un parent signale, un
    humain confirme, le pack disparaît de toutes les surfaces sans qu'aucune
    progression ne soit supprimée.

    Args:
        db: Session de base de données.
        report: Signalement traité.
        actor_id: Admin traitant.
        decision: ``actioned`` (fondé) ou ``dismissed`` (sans suite).
        block_pack: Bloque le pack signalé (implique ``actioned``).

    Returns:
        Le signalement rafraîchi.

    Raises:
        HTTPException: 400 si la décision n'est pas une clôture.
    """
    if decision not in (ReportStatus.ACTIONED, ReportStatus.DISMISSED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Décision invalide : attendu actioned ou dismissed.",
        )
    report.status = (ReportStatus.ACTIONED if block_pack else decision).value
    report.resolved_at = datetime.utcnow()
    report.resolved_by = actor_id
    log_pack_action(
        db,
        pack_id=report.pack_id,
        actor_id=actor_id,
        action="report_resolved",
        detail={"report_id": str(report.id), "decision": report.status, "reason": report.reason},
    )
    db.commit()

    if block_pack:
        pack = db.query(Pack).filter(Pack.id == report.pack_id).first()
        if pack is not None:
            apply_verdict(
                db,
                pack=pack,
                verdict=CommunityStatus.BLOCKED,
                actor_id=actor_id,
                notes=f"Bloqué après signalement ({report.reason}).",
            )
    db.refresh(report)
    return report


def trust_eligibility(db: Session, user_id: UUID) -> dict:
    """État du palier de confiance d'un contributeur, **sans jamais le promouvoir**.

    Le seuil (:data:`app.core.config.Settings.PACK_TRUST_THRESHOLD`) est un
    indicateur affiché à l'admin, pas un automate : promouvoir en silence
    supprimerait la seule barrière du dispositif au moment où elle compte.
    """
    approved = (
        db.query(func.count(Pack.id))
        .filter(Pack.author_id == user_id, Pack.community_status == CommunityStatus.APPROVED.value)
        .scalar()
        or 0
    )
    pending = (
        db.query(func.count(Pack.id))
        .filter(Pack.author_id == user_id, Pack.community_status == CommunityStatus.PENDING.value)
        .scalar()
        or 0
    )
    profile = db.query(ContributorProfile).filter(ContributorProfile.user_id == user_id).first()
    trusted = bool(profile and profile.trusted)
    return {
        "approved_packs": approved,
        "pending_packs": pending,
        "trust_threshold": settings.PACK_TRUST_THRESHOLD,
        "trust_eligible": approved >= settings.PACK_TRUST_THRESHOLD and not trusted,
        "trusted": trusted,
    }


def grant_trust(db: Session, *, user: User, actor_id: UUID | None, trusted: bool) -> ContributorProfile:
    """Accorde ou retire le palier de confiance d'un contributeur (audité).

    Révocable : ``trusted=False`` remet les envois suivants dans la file.

    Raises:
        HTTPException: 404 si le compte n'a pas de profil de contributeur.
    """
    profile = db.query(ContributorProfile).filter(ContributorProfile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ce compte n'est pas contributeur.")

    profile.trusted = trusted
    profile.trusted_at = datetime.utcnow() if trusted else None
    profile.trusted_by = actor_id if trusted else None
    log_pack_action(
        db,
        pack_id=None,
        actor_id=actor_id,
        action="trust_granted" if trusted else "trust_revoked",
        detail={"user_id": str(user.id), "handle": profile.handle, "trusted": trusted},
    )
    db.commit()
    db.refresh(profile)
    return profile


def contributor_row(db: Session, profile: ContributorProfile) -> dict:
    """Un contributeur : reconnaissance mesurée, conditions acceptées, éligibilité.

    ``families_reached`` compte les enfants distincts ayant un accès actif à un
    pack de l'auteur : la reconnaissance est la seule contrepartie offerte, donc
    elle doit être mesurée, pas suggérée.
    """
    families = (
        db.query(func.count(func.distinct(ChildPackAccess.child_id)))
        .join(Pack, Pack.id == ChildPackAccess.pack_id)
        .filter(Pack.author_id == profile.user_id, ChildPackAccess.enabled.is_(True))
        .scalar()
        or 0
    )
    return {
        "user_id": profile.user_id,
        "handle": profile.handle,
        "terms_version": profile.terms_version,
        "terms_accepted_at": profile.terms_accepted_at,
        "trusted_at": profile.trusted_at,
        "families_reached": families,
        **trust_eligibility(db, profile.user_id),
    }


def contributors(db: Session, *, limit: int = 100) -> list[dict]:
    """Tous les contributeurs, du plus récent au plus ancien."""
    profiles = db.query(ContributorProfile).order_by(ContributorProfile.created_at.desc()).limit(limit).all()
    return [contributor_row(db, profile) for profile in profiles]


def anonymise_author(db: Session, *, user_id: UUID) -> int:
    """Détache les packs d'un auteur de son compte, sans rien supprimer (RGPD).

    Appelé **avant** la suppression du compte
    (:func:`app.services.admin.delete_user`) : le ``ON DELETE SET NULL`` de la
    base détacherait bien le pack, mais perdrait l'attribution des packs sans
    pseudonyme dénormalisé. Supprimer les packs, à l'inverse, effacerait la
    progression d'enfants d'autres familles — ce que les conditions de
    contribution annoncent explicitement à l'auteur.

    Ne commite pas : la suppression du compte reste une transaction unique.

    Args:
        db: Session de base de données.
        user_id: Compte auteur en cours de suppression.

    Returns:
        Nombre de packs anonymisés.
    """
    packs = db.query(Pack).filter(Pack.author_id == user_id).all()
    if not packs:
        return 0

    profile = db.query(ContributorProfile).filter(ContributorProfile.user_id == user_id).first()
    fallback = (profile.handle if profile else None) or ANONYMOUS_AUTHOR_HANDLE
    for pack in packs:
        if not pack.author_handle:
            pack.author_handle = fallback
        pack.author_id = None
        log_pack_action(
            db,
            pack_id=pack.id,
            actor_id=None,
            action="author_anonymised",
            detail={"handle": pack.author_handle},
        )
    db.flush()
    return len(packs)


def audit_trail(db: Session, *, pack_id: UUID, limit: int = 50) -> list[PackAuditLog]:
    """Journal d'un pack, du plus récent au plus ancien (écran de revue)."""
    return (
        db.query(PackAuditLog)
        .filter(PackAuditLog.pack_id == pack_id)
        .order_by(PackAuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
