"""Ingestion et cycle de vie d'un pack contribué : brouillon, jeton, soumission, clone.

Ce module est l'unique porte d'écriture du contenu contribué. Toutes ses
fonctions sont **sans commit** : l'endpoint (ou le script) qui appelle décide de
la transaction, ce qui permet d'enchaîner « valider, ingérer, journaliser » en
une seule unité atomique.

Trois invariants portés ici et nulle part ailleurs :

1. **L'XP n'est jamais celle de l'auteur.** :func:`ingest_pack` calcule
   ``Lesson.xp_reward`` avec :func:`app.services.packs.derive_lesson_xp` à partir
   des difficultés des exercices ; le format normalisé ne transporte même pas de
   champ ``xp_reward`` (cf. ``pack_format._EXERCISE_KEYS``).
2. **Un jeton d'envoi ne publie jamais.** :func:`resolve_upload_token` n'identifie
   qu'un auteur pour créer un brouillon ; la soumission exige une session.
3. **Un pack approuvé est immuable pour son auteur.** :func:`assert_pack_mutable`
   refuse la mutation et oriente vers :func:`clone_pack` (issue #17) : les lignes
   de leçon vivent pour toujours, donc la progression des enfants ne se détache
   jamais.
"""

import hashlib
import secrets
import uuid
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import (
    DifficultyEnum,
    Exercise,
    LearningPath,
    Lesson,
    LevelEnum,
    Subject,
    level_rank,
)
from app.models.contribution import (
    ContributionQuota,
    ContributorProfile,
    UploadPairing,
    UploadToken,
)
from app.models.pack import ChildPackAccess, CommunityStatus, Pack, PackOrigin
from app.models.progress import ExerciseResult, UserProgress
from app.models.user import User
from app.schemas.pack import (
    PackDetail,
    PackExercisePreview,
    PackLessonPreview,
    PackSummary,
    ValidationIssue,
)
from app.services.contributor_legal import (
    record_terms_acceptance,
    terms_accepted,
    validate_handle,
)
from app.services.pack_format import (
    CANONICAL_SUBJECT_SLUGS,
    CANONICAL_SUBJECTS,
    normalised_title,
    validate_pack,
)
from app.services.packs import (
    OFFICIAL_AUTHOR_HANDLE,
    derive_lesson_xp,
    log_pack_action,
    mark_reviewed,
    refresh_pack_lesson_xp,
)

#: Difficulté héritée (3 niveaux) déduite du palier, comme dans les seeders.
TIER_DIFFICULTY = {1: DifficultyEnum.EASY, 2: DifficultyEnum.MEDIUM, 3: DifficultyEnum.HARD}

#: Longueur du préfixe lisible conservé en clair pour qu'un parent reconnaisse
#: son jeton dans son profil sans que le secret soit récupérable.
TOKEN_PREFIX_LENGTH = 8


# --------------------------------------------------------------------------- #
# Contributeur : pseudonyme, conditions, quotas
# --------------------------------------------------------------------------- #
def ensure_contributor(
    db: Session,
    user: User,
    *,
    handle: str | None = None,
    accept_terms: bool = False,
) -> ContributorProfile:
    """Récupère (ou crée) le profil contributeur d'un parent.

    Args:
        db: Session de base de données.
        user: Parent auteur.
        handle: Pseudonyme souhaité ; généré s'il est absent à la création.
        accept_terms: Vrai si la requête porte l'acceptation des conditions.

    Returns:
        Le profil contributeur, créé si nécessaire (non commité).

    Raises:
        HTTPException: 422/409 si le pseudonyme est refusé (cf.
            :func:`app.services.contributor_legal.validate_handle`).
    """
    profile = db.query(ContributorProfile).filter(ContributorProfile.user_id == user.id).first()
    if profile is None:
        # Un pseudonyme est obligatoire dès la création : c'est la seule identité
        # publiée, et la dériver du nom Google exposerait un vrai nom.
        candidate = handle or f"Parent-{secrets.token_hex(3)}"
        profile = ContributorProfile(
            user_id=user.id,
            handle=validate_handle(db, candidate, user=user),
            trusted=False,
        )
        db.add(profile)
    elif handle:
        profile.handle = validate_handle(db, handle, user=user)

    if accept_terms:
        record_terms_acceptance(profile)
    db.flush()
    return profile


def assert_can_upload(db: Session, user: User) -> None:
    """Vérifie le quota journalier d'envois du compte.

    Args:
        db: Session de base de données.
        user: Parent auteur.

    Raises:
        HTTPException: 429 si le quota du jour est atteint.
    """
    quota = _today_quota(db, user)
    if quota.uploads >= settings.PACK_MAX_UPLOADS_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "quota_exceeded",
                "message": (
                    f"Limite de {settings.PACK_MAX_UPLOADS_PER_DAY} envois par jour atteinte. "
                    "Réessayez demain, ou complétez un brouillon existant."
                ),
                "uploads_today": quota.uploads,
                "limit": settings.PACK_MAX_UPLOADS_PER_DAY,
            },
        )


def _today_quota(db: Session, user: User) -> ContributionQuota:
    """Compteur d'envois du jour pour ce compte (créé au besoin)."""
    day = date.today().isoformat()
    quota = (
        db.query(ContributionQuota).filter(ContributionQuota.user_id == user.id, ContributionQuota.day == day).first()
    )
    if quota is None:
        quota = ContributionQuota(user_id=user.id, day=day, uploads=0)
        db.add(quota)
        db.flush()
    return quota


def _consume_quota(db: Session, user: User) -> None:
    """Incrémente le compteur d'envois du jour (un envoi accepté = un jeton consommé)."""
    quota = _today_quota(db, user)
    quota.uploads = int(quota.uploads) + 1
    db.flush()


# --------------------------------------------------------------------------- #
# Jetons d'envoi (brouillon uniquement)
# --------------------------------------------------------------------------- #
def _hash_token(raw_token: str) -> str:
    """Empreinte SHA-256 d'un jeton : seule forme jamais écrite en base."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def issue_upload_token(db: Session, user: User, label: str | None) -> tuple[UploadToken, str]:
    """Émet un jeton d'envoi personnel et renvoie son secret **une seule fois**.

    Args:
        db: Session de base de données.
        user: Propriétaire du jeton.
        label: Étiquette libre (« portable », « claude-cli »…).

    Returns:
        Le couple (ligne persistée, secret en clair). Le secret n'est plus
        récupérable ensuite : seule son empreinte est stockée.
    """
    raw_token = secrets.token_urlsafe(32)
    token = UploadToken(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        prefix=raw_token[:TOKEN_PREFIX_LENGTH],
        label=label,
    )
    db.add(token)
    db.flush()
    return token, raw_token


#: Alphabet sans caractère ambigu — ni ``O``/``0``, ni ``I``/``1``/``L``, ni
#: ``U``/``V`` — parce que ce code est **dicté à voix haute**. 29 symboles,
#: 8 tirés : environ 5·10¹¹ combinaisons, ce qui rend le tirage au hasard sans
#: intérêt sur une fenêtre de quinze minutes et un usage unique.
PAIRING_ALPHABET = "23456789ABCDEFGHJKMNPQRSTWXYZ"
PAIRING_LENGTH = 8
PAIRING_TTL_SECONDS = 15 * 60


def _normalise_pairing_code(raw: str) -> str:
    """Forme canonique d'un code dicté : majuscules, sans tirets ni espaces.

    Aucune correction de confusion n'est tentée : les caractères ambigus sont
    absents de l'alphabet, donc en rencontrer un signale une erreur de saisie.
    Deviner l'intention (``O`` → ``Q`` ?) transformerait une faute claire en
    échange silencieusement faux.
    """
    return "".join(char for char in raw.upper() if char.isalnum())


def create_pairing(db: Session, user: User) -> tuple[str, datetime]:
    """Émet un code d'appariement et périme les précédents du compte.

    Un seul code vivant par compte : sinon un code affiché puis abandonné sur un
    écran resterait échangeable, et le parent n'aurait aucun moyen de le savoir.

    Args:
        db: Session de base de données.
        user: Parent qui connecte son assistant.

    Returns:
        Le couple (code en clair, date d'expiration). Le code n'est plus
        récupérable ensuite : seule son empreinte est stockée.
    """
    now = datetime.utcnow()
    db.query(UploadPairing).filter(
        UploadPairing.user_id == user.id,
        UploadPairing.claimed_at.is_(None),
        UploadPairing.expires_at > now,
    ).update({"expires_at": now}, synchronize_session=False)

    code = "".join(secrets.choice(PAIRING_ALPHABET) for _ in range(PAIRING_LENGTH))
    expires_at = now + timedelta(seconds=PAIRING_TTL_SECONDS)
    db.add(
        UploadPairing(
            user_id=user.id,
            code_hash=_hash_token(code),
            expires_at=expires_at,
        )
    )
    db.flush()
    return code, expires_at


def claim_pairing(db: Session, raw_code: str) -> tuple[User, UploadToken, str]:
    """Échange un code d'appariement contre un jeton d'envoi.

    **Non authentifié** : le code est la preuve. C'est ce qui permet à
    l'assistant de se configurer seul, et c'est pourquoi le code est à usage
    unique, expire vite et n'ouvre que la création de brouillons.

    Args:
        db: Session de base de données.
        raw_code: Code dicté par le parent, sous n'importe quelle graphie.

    Returns:
        Le triplet (parent, ligne de jeton, secret en clair).

    Raises:
        HTTPException: 404 si le code est inconnu, expiré ou déjà utilisé — les
            trois cas sont indistinguables, pour ne pas confirmer l'existence
            d'un code à qui en essaie au hasard.
    """
    code = _normalise_pairing_code(raw_code)
    pairing = db.query(UploadPairing).filter(UploadPairing.code_hash == _hash_token(code)).first()
    now = datetime.utcnow()
    if pairing is None or pairing.claimed_at is not None or pairing.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "pairing_invalid",
                "message": (
                    "Ce code est inconnu, expiré ou déjà utilisé. Demandez au parent d'en "
                    "afficher un nouveau depuis « Connecter mon assistant »."
                ),
            },
        )

    user = db.query(User).filter(User.id == pairing.user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "pairing_invalid", "message": "Ce code n'est plus valide."},
        )

    token, secret = issue_upload_token(db, user, "Assistant IA")
    pairing.claimed_at = now
    pairing.token_id = token.id
    db.flush()
    return user, token, secret


def resolve_upload_token(db: Session, raw_token: str) -> User | None:
    """Identifie l'auteur derrière un jeton d'envoi, ou ``None``.

    Un jeton révoqué est indistinguable d'un jeton inexistant : la révocation
    prend donc effet immédiatement, sans cache ni délai.

    Args:
        db: Session de base de données.
        raw_token: Secret présenté par le client.

    Returns:
        L'utilisateur propriétaire du jeton actif, sinon ``None``.
    """
    if not raw_token:
        return None
    token = db.query(UploadToken).filter(UploadToken.token_hash == _hash_token(raw_token)).first()
    if token is None or not token.is_active:
        return None
    token.last_used_at = datetime.utcnow()
    db.flush()
    return db.query(User).filter(User.id == token.user_id).first()


# --------------------------------------------------------------------------- #
# Verrou d'édition
# --------------------------------------------------------------------------- #
def assert_pack_mutable(pack: Pack, *, is_admin: bool) -> None:
    """Refuse toute mutation d'un pack verrouillé par un non-admin.

    Args:
        pack: Pack visé.
        is_admin: Vrai si l'acteur est administrateur (édition auditée autorisée).

    Raises:
        HTTPException: 409 si le pack est verrouillé et l'acteur n'est pas admin.
    """
    if pack.locked and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "pack_locked",
                "message": (
                    "Ce pack est approuvé, donc verrouillé : d'autres familles l'utilisent et une "
                    "modification serait diffusée sans revue. Clonez-le pour en proposer une "
                    "révision (POST /api/v1/contributions/{pack_id}/clone), puis soumettez le clone."
                ),
                "pack_id": str(pack.id),
            },
        )


# --------------------------------------------------------------------------- #
# Ingestion
# --------------------------------------------------------------------------- #
def _ensure_subject(db: Session, slug: str) -> Subject:
    """Matière de ce slug (créée avec ses métadonnées canoniques au besoin)."""
    subject = db.query(Subject).filter(Subject.slug == slug).first()
    if subject is not None:
        return subject
    name, icon = CANONICAL_SUBJECTS.get(slug, (slug.replace("-", " ").title(), None))
    subject = Subject(name=name, slug=slug, icon=icon, is_active=True)
    db.add(subject)
    db.flush()
    return subject


def _ensure_path(db: Session, subject: Subject, level: LevelEnum) -> LearningPath:
    """Parcours (matière, niveau), find-or-create — même clé que les seeders.

    ``LearningPath`` reste l'index matière+niveau qui alimente ``SubjectProgress``,
    le classement et le tableau de bord (décision 15) ; seul le **verrou** de
    progression a migré vers le pack.
    """
    path = db.query(LearningPath).filter(LearningPath.subject_id == subject.id, LearningPath.level == level).first()
    if path is None:
        path = LearningPath(
            subject_id=subject.id,
            name=f"{subject.name} — {level.value.upper()}",
            level=level,
        )
        db.add(path)
        db.flush()
    return path


def ingest_pack(
    db: Session,
    *,
    payload: dict[str, Any],
    author: User | None,
    origin: PackOrigin = PackOrigin.COMMUNITY,
    issues: list[ValidationIssue] | None = None,
    quality_score: int | None = None,
) -> Pack:
    """Crée un pack complet (pack, leçons, exercices) depuis un document `.explorito`.

    Le document est **toujours** validé : si l'appelant n'a pas déjà fourni les
    constats de :func:`app.services.pack_format.validate_pack`, ils sont calculés
    ici. Aucun chemin d'ingestion ne peut donc contourner le validateur.

    Args:
        db: Session de base de données.
        payload: Document `.explorito` (brut ou déjà normalisé).
        author: Parent auteur ; ``None`` pour une ingestion « équipe ».
        origin: Provenance du pack.
        issues: Constats non bloquants déjà calculés, le cas échéant.
        quality_score: Score de qualité déjà calculé, le cas échéant.

    Returns:
        Le pack créé (non commité).

    Raises:
        PackRejected: Si le document est invalide et n'avait pas été validé avant.
    """
    if issues is None or quality_score is None:
        payload, issues, quality_score = validate_pack(payload, known_subject_slugs=known_subject_slugs(db))

    header = payload["pack"]
    lessons = payload["lessons"]
    ranks = [level_rank(lesson["level"]) for lesson in lessons]
    ordered = sorted(LevelEnum, key=level_rank)

    is_official = origin is PackOrigin.OFFICIAL
    profile = (
        db.query(ContributorProfile).filter(ContributorProfile.user_id == author.id).first()
        if author is not None
        else None
    )
    pack = Pack(
        title=header["title"],
        emoji=header.get("emoji"),
        description=header.get("description"),
        origin=origin.value,
        author_id=author.id if author is not None else None,
        author_handle=OFFICIAL_AUTHOR_HANDLE if is_official else (profile.handle if profile else None),
        community_status=(CommunityStatus.APPROVED if is_official else CommunityStatus.DRAFT).value,
        difficulty_ratified=is_official,
        locked=False,
        tags=header.get("tags") or [],
        quality_score=quality_score,
        warnings=[issue.model_dump() for issue in issues],
        level_min=ordered[min(ranks)],
        level_max=ordered[max(ranks)],
    )
    db.add(pack)
    db.flush()

    for lesson_spec in lessons:
        _ingest_lesson(db, pack, lesson_spec)

    if author is not None and not is_official:
        _consume_quota(db, author)
    log_pack_action(
        db,
        pack_id=pack.id,
        actor_id=author.id if author is not None else None,
        action="ingested",
        detail={
            "origin": origin.value,
            "lessons": len(lessons),
            "quality_score": quality_score,
            "flags": [issue.code for issue in issues if issue.severity == "flag"],
        },
    )
    db.flush()
    return pack


def _ingest_lesson(db: Session, pack: Pack, lesson_spec: dict[str, Any]) -> Lesson:
    """Crée une leçon publiée du pack, avec ses exercices et son XP dérivée."""
    level = LevelEnum(lesson_spec["level"])
    subject = _ensure_subject(db, lesson_spec["subject_slug"])
    path = _ensure_path(db, subject, level)
    tier = int(lesson_spec["tier"])
    exercises = lesson_spec["exercises"]

    lesson = Lesson(
        path_id=path.id,
        pack_id=pack.id,
        name=lesson_spec["name"],
        description=lesson_spec.get("description"),
        order_index=tier,
        # Source unique de l'XP : les difficultés des exercices, au tarif que
        # l'enfant gagnera vraiment (forfaitaire tant que le pack n'est pas
        # ratifié). Le document de l'auteur ne transporte aucun xp_reward.
        xp_reward=derive_lesson_xp(
            [exercise.get("difficulty_level") for exercise in exercises],
            ratified=bool(pack.difficulty_ratified),
        ),
        is_published=True,
    )
    db.add(lesson)
    db.flush()

    for index, exercise in enumerate(exercises):
        db.add(
            Exercise(
                lesson_id=lesson.id,
                type=exercise["type"],
                question=exercise["question"],
                content=exercise.get("content") or {},
                correct_answer=exercise.get("correct_answer") or {},
                hints=exercise.get("hints") or [],
                explanation=exercise.get("explanation"),
                order_index=exercise.get("order_index", index),
                difficulty=TIER_DIFFICULTY.get(tier, DifficultyEnum.EASY),
                difficulty_level=exercise.get("difficulty_level"),
                media_urls=exercise.get("media_urls") or {},
            )
        )
    db.flush()
    return lesson


def known_subject_slugs(db: Session) -> set[str]:
    """Matières acceptables : celles en base, plus les matières canoniques.

    Les canoniques sont admises même absentes de la base pour qu'un premier pack
    de « logique » sur une instance vierge ne soit pas refusé à tort.
    """
    return {row[0] for row in db.query(Subject.slug)} | set(CANONICAL_SUBJECT_SLUGS)


def near_duplicate_flags(db: Session, pack: Pack) -> list[ValidationIssue]:
    """Annote un pack dont le titre normalisé existe déjà (jamais un refus).

    Le clone d'un pack approuvé déclenchera nécessairement ce drapeau contre son
    propre parent : c'est voulu, la lignée (``cloned_from_pack_id``) permet à
    l'admin de le lire comme une révision et non comme un doublon.
    """
    key = normalised_title(pack.title)
    if not key:
        return []
    rows = db.query(Pack.id, Pack.title).filter(Pack.id != pack.id).all()
    matches = [str(row[0]) for row in rows if normalised_title(row[1]) == key]
    if not matches:
        return []
    return [
        ValidationIssue(
            severity="flag",
            code="near_duplicate",
            message=(
                f"Un pack porte déjà ce titre ({len(matches)} correspondance(s)). "
                "Aucun refus : ce peut être une révision volontaire."
            ),
            field="pack.title",
        )
    ]


# --------------------------------------------------------------------------- #
# Cycle de vie
# --------------------------------------------------------------------------- #
def submit_pack(db: Session, pack: Pack, actor: User) -> Pack:
    """Soumet un brouillon : ``DRAFT`` → ``PENDING`` (ou ``APPROVED`` si confiance).

    Le palier de confiance publie directement, avec contrôle a posteriori et
    bouton de signalement en filet (décision 5). L'approbation passe par
    :func:`app.services.packs.mark_reviewed`, qui verrouille le pack et ratifie
    sa difficulté — un auteur de confiance ne garde donc pas la main dessus.

    Args:
        db: Session de base de données.
        pack: Pack à soumettre.
        actor: Auteur qui soumet.

    Returns:
        Le pack soumis (non commité).

    Raises:
        HTTPException: 409 si le pack n'est pas un brouillon, 429 si trop de
            soumissions sont déjà en attente pour ce compte.
    """
    if pack.community_status != CommunityStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "not_a_draft",
                "message": f"Ce pack est déjà « {pack.community_status} » : seul un brouillon se soumet.",
            },
        )

    pending = (
        db.query(Pack)
        .filter(
            Pack.author_id == actor.id,
            Pack.community_status == CommunityStatus.PENDING.value,
        )
        .count()
    )
    if pending >= settings.PACK_MAX_PENDING:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "too_many_pending",
                "message": (
                    f"{pending} packs déjà en attente de revue (maximum {settings.PACK_MAX_PENDING}). "
                    "Attendez un verdict avant d'en soumettre un autre."
                ),
            },
        )

    profile = db.query(ContributorProfile).filter(ContributorProfile.user_id == actor.id).first()
    pack.submitted_at = datetime.utcnow()
    if profile is not None and bool(profile.trusted):
        mark_reviewed(pack, actor.id, CommunityStatus.APPROVED)
        # L'auto-approbation ratifie la difficulté : l'XP annoncée des leçons
        # passe du forfait au tarif gradué et doit être réécrite maintenant.
        refresh_pack_lesson_xp(db, pack)
        log_pack_action(
            db,
            pack_id=pack.id,
            actor_id=actor.id,
            action="submitted",
            detail={"auto_approved": True, "reason": "trusted_contributor"},
        )
    else:
        pack.community_status = CommunityStatus.PENDING.value
        log_pack_action(db, pack_id=pack.id, actor_id=actor.id, action="submitted", detail={"auto_approved": False})
    db.flush()
    return pack


#: Statuts qu'un auteur peut supprimer lui-même. Un pack approuvé n'en fait pas
#: partie : d'autres familles l'ont dans leur liste blanche, et il se retire par
#: un verdict de modération, pas par un geste unilatéral de l'auteur.
DELETABLE_STATUSES = (CommunityStatus.DRAFT, CommunityStatus.REJECTED)


def pack_progress_counts(db: Session, pack: Pack) -> tuple[int, int]:
    """Nombre de lignes de progression et de résultats attachées à un pack."""
    lesson_ids = [row[0] for row in db.query(Lesson.id).filter(Lesson.pack_id == pack.id)]
    if not lesson_ids:
        return 0, 0
    progress = db.query(UserProgress).filter(UserProgress.lesson_id.in_(lesson_ids)).count()
    results = (
        db.query(ExerciseResult)
        .join(Exercise, Exercise.id == ExerciseResult.exercise_id)
        .filter(Exercise.lesson_id.in_(lesson_ids))
        .count()
    )
    return progress, results


def delete_pack(db: Session, *, pack: Pack, actor: User, is_admin: bool) -> None:
    """Supprime définitivement un pack non publié et sans progression.

    C'est la seule suppression physique de contenu de l'application, et elle est
    étroitement gardée. ``user_progress.lesson_id`` et
    ``exercise_results.exercise_id`` sont en ``ON DELETE CASCADE`` : effacer un
    pack joué effacerait silencieusement les complétions d'un enfant et l'XP qui
    en découle. Le garde-fou n'est donc pas cosmétique — c'est lui qui rend la
    suppression acceptable.

    Quatre conditions :

    1. l'appelant est l'auteur (ou un admin) ;
    2. le pack est ``draft`` ou ``rejected`` — jamais publié à d'autres familles ;
    3. le pack n'est pas verrouillé ;
    4. **aucune ligne de progression ni de résultat** ne le référence.

    Args:
        db: Session de base de données.
        pack: Pack à supprimer.
        actor: Utilisateur à l'origine de la demande.
        is_admin: Vrai si l'appelant est administrateur.

    Raises:
        HTTPException: 409 si le statut, le verrou ou la progression l'interdit.
    """
    status_value = str(pack.community_status)
    if status_value not in {member.value for member in DELETABLE_STATUSES}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "pack_not_deletable",
                "message": (
                    "Seuls un brouillon et un pack refusé peuvent être supprimés. "
                    "Un pack publié se retire par la modération, car d'autres familles l'utilisent."
                ),
            },
        )
    if bool(pack.locked) and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "pack_locked", "message": "Ce pack est verrouillé : il ne peut plus être supprimé."},
        )

    progress, results = pack_progress_counts(db, pack)
    if progress or results:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "pack_has_progress",
                "message": (
                    f"Un enfant a déjà travaillé dans ce pack ({progress} leçon(s) commencée(s), "
                    f"{results} réponse(s) enregistrée(s)). Le supprimer effacerait sa progression "
                    "et l'XP gagnée, donc c'est refusé."
                ),
                "progress_rows": progress,
                "result_rows": results,
            },
        )

    title = str(pack.title)
    lesson_ids = [row[0] for row in db.query(Lesson.id).filter(Lesson.pack_id == pack.id)]
    if lesson_ids:
        db.query(Exercise).filter(Exercise.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        # Les leçons partent avant le pack : ``lessons.pack_id`` est en RESTRICT,
        # précisément pour qu'aucune suppression de pack ne cascade sur du contenu.
        db.query(Lesson).filter(Lesson.id.in_(lesson_ids)).delete(synchronize_session=False)
    db.delete(pack)
    # Trace posée avec ``pack_id`` à NULL : la ligne d'audit est en CASCADE sur le
    # pack, donc la rattacher la ferait disparaître avec lui.
    log_pack_action(
        db,
        pack_id=None,
        actor_id=actor.id,
        action="pack_deleted",
        detail={"pack_id": str(pack.id), "title": title, "status": status_value, "lessons": len(lesson_ids)},
    )
    db.flush()


def clone_pack(db: Session, *, pack: Pack, author: User) -> Pack:
    """Duplique un pack (leçons et exercices comprises) en un nouveau brouillon.

    Copie profonde vers de **nouvelles lignes** : les identifiants de leçon
    changent par construction. C'est le point de la décision 7 — l'original garde
    ses lignes, donc la progression et les résultats des enfants qui l'ont joué
    restent intacts, et le clone repasse en revue comme une soumission neuve.

    Args:
        db: Session de base de données.
        pack: Pack source (jamais modifié).
        author: Parent qui prend la main sur la révision.

    Returns:
        Le nouveau pack brouillon (non commité).
    """
    profile = db.query(ContributorProfile).filter(ContributorProfile.user_id == author.id).first()
    clone = Pack(
        title=f"{pack.title} (révision)",
        emoji=pack.emoji,
        description=pack.description,
        origin=PackOrigin.COMMUNITY.value,
        author_id=author.id,
        author_handle=profile.handle if profile is not None else None,
        community_status=CommunityStatus.DRAFT.value,
        difficulty_ratified=False,
        locked=False,
        tags=list(pack.tags or []),
        quality_score=pack.quality_score,
        warnings=list(pack.warnings or []),
        level_min=pack.level_min,
        level_max=pack.level_max,
        cloned_from_pack_id=pack.id,
    )
    db.add(clone)
    db.flush()

    source_lessons = db.query(Lesson).filter(Lesson.pack_id == pack.id).order_by(Lesson.order_index).all()
    for source in source_lessons:
        lesson = Lesson(
            path_id=source.path_id,
            pack_id=clone.id,
            name=source.name,
            description=source.description,
            order_index=source.order_index,
            unlock_criteria=dict(source.unlock_criteria or {}),
            xp_reward=source.xp_reward,
            estimated_duration=source.estimated_duration,
            cover_image=source.cover_image,
            is_published=source.is_published,
        )
        db.add(lesson)
        db.flush()
        exercises = db.query(Exercise).filter(Exercise.lesson_id == source.id).order_by(Exercise.order_index).all()
        for exercise in exercises:
            db.add(
                Exercise(
                    lesson_id=lesson.id,
                    type=exercise.type,
                    question=exercise.question,
                    content=dict(exercise.content or {}),
                    correct_answer=dict(exercise.correct_answer or {}),
                    hints=list(exercise.hints or []),
                    explanation=exercise.explanation,
                    order_index=exercise.order_index,
                    difficulty=exercise.difficulty,
                    difficulty_level=exercise.difficulty_level,
                    media_urls=dict(exercise.media_urls or {}),
                )
            )

    log_pack_action(
        db,
        pack_id=clone.id,
        actor_id=author.id,
        action="cloned",
        detail={"source_pack_id": str(pack.id), "lessons": len(source_lessons)},
    )
    db.flush()
    return clone


# --------------------------------------------------------------------------- #
# Vues (DTO partagés)
# --------------------------------------------------------------------------- #
def _pack_lessons(db: Session, pack_id: uuid.UUID) -> list[Any]:
    """Triplets ``(leçon, matière, parcours)`` du pack, dans l'ordre des paliers."""
    return (
        db.query(Lesson, Subject, LearningPath)
        .join(LearningPath, Lesson.path_id == LearningPath.id)
        .join(Subject, LearningPath.subject_id == Subject.id)
        .filter(Lesson.pack_id == pack_id)
        .order_by(Lesson.order_index, Lesson.name)
        .all()
    )


def pack_summary(db: Session, pack: Pack) -> PackSummary:
    """Carte d'un pack : compteurs, matières et nombre de familles utilisatrices."""
    rows = _pack_lessons(db, pack.id)
    lesson_ids = [lesson.id for lesson, _, _ in rows]
    exercise_count = db.query(Exercise).filter(Exercise.lesson_id.in_(lesson_ids)).count() if lesson_ids else 0
    icons: list[str] = []
    for _, subject, _ in rows:
        if subject.icon and subject.icon not in icons:
            icons.append(subject.icon)
    families = (
        db.query(ChildPackAccess.child_id)
        .filter(ChildPackAccess.pack_id == pack.id, ChildPackAccess.enabled.is_(True))
        .distinct()
        .count()
    )
    return PackSummary(
        id=pack.id,
        title=pack.title,
        emoji=pack.emoji,
        description=pack.description,
        origin=PackOrigin(pack.origin),
        community_status=CommunityStatus(pack.community_status),
        author_handle=pack.author_handle,
        tags=list(pack.tags or []),
        quality_score=pack.quality_score,
        difficulty_ratified=bool(pack.difficulty_ratified),
        locked=bool(pack.locked),
        level_min=pack.level_min,
        level_max=pack.level_max,
        lesson_count=len(rows),
        exercise_count=exercise_count,
        subject_icons=icons,
        families_count=families,
        created_at=pack.created_at,
        submitted_at=pack.submitted_at,
    )


def pack_detail(db: Session, pack: Pack) -> PackDetail:
    """Pack complet : leçons et exercices tels que l'enfant les verra.

    Sert l'aperçu de contribution, la file de modération et le catalogue parent :
    un adulte doit pouvoir lire **tout** le contenu avant de l'activer.
    """
    summary = pack_summary(db, pack)
    lessons: list[PackLessonPreview] = []
    for lesson, subject, path in _pack_lessons(db, pack.id):
        exercises = db.query(Exercise).filter(Exercise.lesson_id == lesson.id).order_by(Exercise.order_index).all()
        lessons.append(
            PackLessonPreview(
                id=lesson.id,
                name=lesson.name,
                description=lesson.description,
                subject_slug=subject.slug,
                subject_name=subject.name,
                subject_icon=subject.icon,
                level=path.level,
                tier=lesson.order_index or 1,
                xp_reward=lesson.xp_reward or 0,
                exercises=[
                    PackExercisePreview(
                        id=exercise.id,
                        order_index=exercise.order_index or 0,
                        type=exercise.type,
                        question=exercise.question,
                        content=exercise.content or {},
                        correct_answer=exercise.correct_answer or {},
                        explanation=exercise.explanation,
                        difficulty_level=exercise.difficulty_level,
                    )
                    for exercise in exercises
                ],
            )
        )
    return PackDetail(
        **summary.model_dump(),
        lessons=lessons,
        warnings=[ValidationIssue.model_validate(item) for item in (pack.warnings or [])],
        cloned_from_pack_id=pack.cloned_from_pack_id,
        review_notes=pack.review_notes,
        reviewed_at=pack.reviewed_at,
    )


def contributor_terms_state(db: Session, user: User) -> tuple[ContributorProfile | None, bool]:
    """Profil contributeur et acceptation à jour des conditions pour ce compte."""
    profile = db.query(ContributorProfile).filter(ContributorProfile.user_id == user.id).first()
    return profile, bool(profile is not None and terms_accepted(profile))
