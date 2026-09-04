"""Contribution de packs par les parents : envoi de brouillon, aperçu, édition rapide, soumission.

Un seul point d'entrée pour deux transports (navigateur authentifié par session,
ou compétence d'écriture munie d'un jeton d'envoi restreint) et un seul
validateur. Un jeton d'envoi ne peut jamais publier : il crée des brouillons.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user, get_user_by_email
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.content import Exercise, Lesson
from app.models.contribution import UploadToken
from app.models.pack import CommunityStatus, Pack
from app.models.user import User, UserRole
from app.schemas.contribution import (
    ContributorTerms,
    ContributorTermsAccept,
    PackQuickEdit,
    PairingClaim,
    PairingCode,
    PairingResult,
    UploadResult,
    UploadTokenCreate,
    UploadTokenCreated,
    UploadTokenResponse,
)
from app.schemas.pack import PackDetail, PackSummary, ValidationIssue
from app.services.contribution import (
    PAIRING_TTL_SECONDS,
    assert_can_upload,
    assert_pack_mutable,
    claim_pairing,
    clone_pack,
    contributor_terms_state,
    create_pairing,
    ensure_contributor,
    ingest_pack,
    issue_upload_token,
    known_subject_slugs,
    near_duplicate_flags,
    pack_detail,
    pack_summary,
    resolve_upload_token,
    submit_pack,
)
from app.services.contributor_legal import CONTRIBUTOR_TERMS, CONTRIBUTOR_TERMS_VERSION
from app.services.pack_format import PackRejected, validate_pack
from app.services.packs import log_pack_action, refresh_lesson_xp

router = APIRouter()

#: Extraction du porteur JWT **sans** échec automatique : cet endpoint accepte
#: aussi un jeton d'envoi, donc l'absence d'``Authorization`` n'est pas une
#: erreur en soi. La dépendance de session standard, elle, répond 401 d'office.
_optional_bearer = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/dev-login", auto_error=False)


@dataclass(frozen=True)
class ContributionActor:
    """Auteur d'une requête de contribution et **transport** utilisé.

    Le transport est porté jusqu'aux handlers parce qu'il est décisif : un jeton
    long-terme ne doit pouvoir que déposer un brouillon (décision 16). Confondre
    les deux reviendrait à donner à un fichier de configuration le pouvoir de
    publier chez d'autres familles.
    """

    user: User
    via_token: bool


def contribution_actor(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Depends(_optional_bearer)] = None,
    x_upload_token: Annotated[str | None, Header()] = None,
) -> ContributionActor:
    """Authentifie par session **ou** par jeton d'envoi.

    Args:
        db: Session de base de données.
        token: Jeton JWT de session, s'il est présent.
        x_upload_token: Secret du jeton d'envoi, s'il est présent.

    Returns:
        L'auteur et le transport employé.

    Raises:
        HTTPException: 401 si aucune identité valide, 403 si le compte est inactif.
    """
    if x_upload_token:
        user = resolve_upload_token(db, x_upload_token)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Jeton d'envoi inconnu ou révoqué",
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Utilisateur inactif")
        return ContributionActor(user=user, via_token=True)

    if token:
        payload = decode_access_token(token)
        email = payload.get("sub") if payload else None
        user = get_user_by_email(db, email=email) if email else None
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Impossible de valider les informations d'identification",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Utilisateur inactif")
        return ContributionActor(user=user, via_token=False)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise (session ou en-tête X-Upload-Token)",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _require_session(actor: ContributionActor) -> User:
    """Exige une session : un jeton d'envoi ne peut que créer des brouillons."""
    if actor.via_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "token_scope",
                "message": (
                    "Un jeton d'envoi ne permet que de créer un brouillon. Ouvrez l'aperçu dans "
                    "l'application pour relire, corriger puis soumettre le pack."
                ),
            },
        )
    return actor.user


def _owned_pack(db: Session, pack_id: UUID, user: User) -> Pack:
    """Pack du parent (ou n'importe lequel pour un admin), sinon 404.

    Volontairement 404 et non 403 : répondre « interdit » confirmerait
    l'existence du pack d'une autre famille.
    """
    pack = db.query(Pack).filter(Pack.id == pack_id).first()
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pack non trouvé")
    if user.role != UserRole.ADMIN and pack.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pack non trouvé")
    return pack


def _rejected(issues: list[ValidationIssue]) -> HTTPException:
    """Traduit un refus du validateur en 422 lisible **par une machine**.

    Le corps est la liste complète des constats : c'est ce que l'IA du parent
    relit pour corriger son fichier, la boucle de rétroaction du format.
    """
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "code": "pack_invalid",
            "message": f"{len(issues)} erreur(s) à corriger avant l'envoi.",
            "issues": [issue.model_dump() for issue in issues],
        },
    )


async def _read_document(request: Request) -> tuple[dict[str, Any], bool, str | None]:
    """Lit le document `.explorito` (corps JSON ou fichier multipart).

    Args:
        request: Requête entrante.

    Returns:
        Le document désérialisé, l'acceptation des conditions et le pseudonyme
        éventuellement transmis.

    Raises:
        HTTPException: 413 si le fichier dépasse le plafond, 400 s'il n'est pas
            du JSON exploitable.
    """
    accept_terms = str(request.query_params.get("accept_terms", "")).lower() in ("1", "true", "yes", "on")
    handle = request.query_params.get("handle")

    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None or isinstance(upload, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Champ « file » manquant : joignez le fichier .explorito.",
            )
        raw = await upload.read()
        accept_terms = accept_terms or str(form.get("accept_terms", "")).lower() in ("1", "true", "yes", "on")
        form_handle = form.get("handle")
        handle = handle or (form_handle if isinstance(form_handle, str) else None)
    else:
        raw = await request.body()

    if len(raw) > settings.PACK_MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "file_too_large",
                "message": (
                    f"Fichier de {len(raw)} octets pour un maximum de {settings.PACK_MAX_FILE_SIZE}. "
                    "Découpez le contenu en plusieurs packs."
                ),
            },
        )
    try:
        document = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fichier .explorito illisible : JSON invalide ({exc}).",
        ) from exc
    if not isinstance(document, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier .explorito doit contenir un objet JSON à la racine.",
        )
    return document, accept_terms, handle


def _preview_url(pack: Pack) -> str:
    """URL de l'écran d'aperçu du pack (relecture puis soumission)."""
    return f"{settings.PUBLIC_APP_URL.rstrip('/')}/contributions/{pack.id}"


# --------------------------------------------------------------------------- #
# Conditions et jetons — déclarés avant /{pack_id} pour éviter la collision
# --------------------------------------------------------------------------- #
@router.get("/terms", response_model=ContributorTerms)
async def get_terms(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Depends(_optional_bearer)] = None,
) -> ContributorTerms:
    """Conditions de contribution en vigueur, et leur acceptation par le compte.

    Lisible sans session : le texte doit pouvoir être affiché *avant* l'envoi,
    et c'est aussi ce que renvoie le 428 du premier envoi.
    """
    accepted = False
    handle: str | None = None
    trusted = False
    payload = decode_access_token(token) if token else None
    email = payload.get("sub") if payload else None
    user = get_user_by_email(db, email=email) if email else None
    if user is not None:
        profile, accepted = contributor_terms_state(db, user)
        handle = profile.handle if profile is not None else None
        trusted = bool(profile.trusted) if profile is not None else False
    return ContributorTerms(
        version=CONTRIBUTOR_TERMS_VERSION,
        text=CONTRIBUTOR_TERMS,
        accepted=accepted,
        handle=handle,
        trusted=trusted,
    )


@router.post("/terms/accept", response_model=ContributorTerms)
async def accept_terms(
    body: ContributorTermsAccept,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ContributorTerms:
    """Enregistre l'acceptation des conditions et le pseudonyme public.

    Séparé de l'envoi à dessein : le parent doit pouvoir accepter **avant**
    d'avoir un pack sous la main. Tant que cette route n'a pas été appelée, la
    page de contribution reste inactive côté client — c'était sinon un 428
    surgissant au premier envoi, c'est-à-dire au pire moment.

    Session obligatoire : un jeton d'envoi ne peut pas accepter des conditions
    juridiques au nom d'une personne.
    """
    profile = ensure_contributor(db, current_user, handle=body.handle, accept_terms=True)
    db.commit()
    db.refresh(profile)
    return ContributorTerms(
        version=CONTRIBUTOR_TERMS_VERSION,
        text=CONTRIBUTOR_TERMS,
        accepted=True,
        handle=profile.handle,
        trusted=bool(profile.trusted),
    )


@router.post("/pairing", response_model=PairingCode, status_code=status.HTTP_201_CREATED)
async def start_pairing(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PairingCode:
    """Affiche un code court à dicter à son assistant.

    Remplace la mise en place d'une variable d'environnement, qui perdait la
    quasi-totalité des parents : huit caractères lus à voix haute, et
    l'assistant va chercher le jeton lui-même.
    """
    code, expires_at = create_pairing(db, current_user)
    db.commit()
    return PairingCode(
        code=code,
        expires_at=expires_at,
        expires_in_seconds=PAIRING_TTL_SECONDS,
    )


@router.post("/pairing/claim", response_model=PairingResult)
async def claim_pairing_code(
    body: PairingClaim,
    db: Annotated[Session, Depends(get_db)],
) -> PairingResult:
    """Échange un code d'appariement contre un jeton d'envoi (sans session).

    Volontairement non authentifié : c'est tout l'intérêt, l'assistant n'a rien
    à configurer. Le code est la preuve, donc il est à usage unique, expire en
    quinze minutes et ne débloque qu'un jeton de **brouillon**.
    """
    user, token, secret = claim_pairing(db, body.code)
    profile, accepted = contributor_terms_state(db, user)
    db.commit()
    return PairingResult(
        token=secret,
        prefix=token.prefix,
        handle=profile.handle if profile is not None else None,
        terms_accepted=accepted,
        terms_version=CONTRIBUTOR_TERMS_VERSION,
        app_url=settings.PUBLIC_APP_URL,
    )


@router.get("/tokens", response_model=list[UploadTokenResponse])
async def list_tokens(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UploadTokenResponse]:
    """Jetons d'envoi du compte (préfixe et usage seulement, jamais le secret)."""
    tokens = (
        db.query(UploadToken)
        .filter(UploadToken.user_id == current_user.id)
        .order_by(UploadToken.created_at.desc())
        .all()
    )
    return [
        UploadTokenResponse(
            id=token.id,
            prefix=token.prefix,
            label=token.label,
            created_at=token.created_at,
            last_used_at=token.last_used_at,
            revoked_at=token.revoked_at,
            active=token.is_active,
        )
        for token in tokens
    ]


@router.post("/tokens", response_model=UploadTokenCreated, status_code=status.HTTP_201_CREATED)
async def create_token(
    body: UploadTokenCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UploadTokenCreated:
    """Émet un jeton d'envoi. Le secret n'est affiché qu'ici, une seule fois."""
    token, secret = issue_upload_token(db, current_user, body.label)
    db.commit()
    db.refresh(token)
    return UploadTokenCreated(
        id=token.id,
        prefix=token.prefix,
        label=token.label,
        created_at=token.created_at,
        last_used_at=token.last_used_at,
        revoked_at=token.revoked_at,
        active=token.is_active,
        token=secret,
    )


@router.delete("/tokens", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_tokens(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Révoque tous les jetons actifs du compte (bouton « je ne sais plus lequel »)."""
    tokens = (
        db.query(UploadToken).filter(UploadToken.user_id == current_user.id, UploadToken.revoked_at.is_(None)).all()
    )
    for token in tokens:
        token.revoked_at = datetime.utcnow()
    db.commit()


@router.delete("/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_token(
    token_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Révoque un jeton précis ; la révocation prend effet immédiatement."""
    token = db.query(UploadToken).filter(UploadToken.id == token_id, UploadToken.user_id == current_user.id).first()
    if token is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jeton non trouvé")
    if token.revoked_at is None:
        token.revoked_at = datetime.utcnow()
        db.commit()


# --------------------------------------------------------------------------- #
# Envoi et aperçu
# --------------------------------------------------------------------------- #
@router.post("", response_model=UploadResult, status_code=status.HTTP_201_CREATED)
async def upload_pack(
    request: Request,
    actor: Annotated[ContributionActor, Depends(contribution_actor)],
    db: Annotated[Session, Depends(get_db)],
) -> UploadResult:
    """Dépose un pack en **brouillon** depuis un fichier `.explorito`.

    Deux transports (session du navigateur, jeton d'envoi de la compétence
    d'écriture) et un seul validateur. Rien n'est publié ici : la soumission est
    un geste explicite et distinct.

    Args:
        request: Requête portant le document (corps JSON ou multipart).
        actor: Auteur et transport.
        db: Session de base de données.

    Returns:
        L'identifiant du brouillon, son URL d'aperçu, ses constats et son score.

    Raises:
        HTTPException: 428 si les conditions ne sont pas acceptées, 429 sur
            quota, 413 sur fichier trop gros, 422 si le pack est invalide.
    """
    document, accept_terms, handle = await _read_document(request)
    user = actor.user

    _, accepted = contributor_terms_state(db, user)
    if not accepted and not accept_terms:
        # 428 « Precondition Required » : la requête est correcte, mais elle
        # exige un acte préalable dont on renvoie le texte pour l'afficher.
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail={
                "code": "terms_required",
                "message": (
                    "Acceptez les conditions de contribution pour votre premier envoi "
                    "(accept_terms=true), et choisissez un pseudonyme public."
                ),
                "terms_version": CONTRIBUTOR_TERMS_VERSION,
                "terms": CONTRIBUTOR_TERMS,
            },
        )

    assert_can_upload(db, user)
    ensure_contributor(db, user, handle=handle, accept_terms=accept_terms)
    # Commit avant validation : un pack refusé ne doit pas annuler l'acceptation
    # des conditions ni le pseudonyme, sinon le parent les ressaisirait à chaque
    # aller-retour de correction.
    db.commit()

    try:
        payload, issues, score = validate_pack(document, known_subject_slugs=known_subject_slugs(db))
    except PackRejected as rejected:
        raise _rejected(rejected.issues) from rejected

    pack = ingest_pack(db, payload=payload, author=user, issues=issues, quality_score=score)
    duplicates = near_duplicate_flags(db, pack)
    if duplicates:
        # Réassignation (et non mutation) : la colonne est du JSON, SQLAlchemy ne
        # détecte pas une modification en place.
        pack.warnings = list(pack.warnings or []) + [issue.model_dump() for issue in duplicates]
        issues = issues + duplicates
    db.commit()
    db.refresh(pack)

    return UploadResult(
        pack_id=pack.id,
        preview_url=_preview_url(pack),
        community_status=CommunityStatus(pack.community_status),
        quality_score=score,
        warnings=[issue for issue in issues if issue.severity == "warning"],
        flags=[issue for issue in issues if issue.severity == "flag"],
    )


@router.get("", response_model=list[PackSummary])
async def list_my_packs(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PackSummary]:
    """Packs rédigés par le parent connecté, du plus récent au plus ancien."""
    packs = db.query(Pack).filter(Pack.author_id == current_user.id).order_by(Pack.created_at.desc()).all()
    return [pack_summary(db, pack) for pack in packs]


@router.get("/{pack_id}", response_model=PackDetail)
async def get_my_pack(
    pack_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PackDetail:
    """Aperçu complet d'un pack : toutes les leçons, tous les exercices."""
    pack = _owned_pack(db, pack_id, current_user)
    return pack_detail(db, pack)


# --------------------------------------------------------------------------- #
# Édition rapide et cycle de vie
# --------------------------------------------------------------------------- #
def _pack_document(db: Session, pack: Pack) -> dict[str, Any]:
    """Reconstruit un document `.explorito` depuis l'état en base du pack.

    Permet de faire relire au **même** validateur le résultat d'une retouche :
    une correction ne peut donc pas rendre un pack invalide.
    """
    detail = pack_detail(db, pack)
    # Le bloc self_check n'a pas de colonne : on se souvient de sa présence via
    # l'avertissement produit au premier envoi, sinon chaque retouche ferait
    # baisser le score d'un pack qui, lui, n'a pas changé sur ce point.
    had_self_check = not any(issue.code == "self_check_missing" for issue in detail.warnings)
    return {
        "format_version": settings.PACK_FORMAT_VERSION,
        "pack": {
            "title": pack.title,
            "emoji": pack.emoji,
            "description": pack.description,
            "tags": list(pack.tags or []),
        },
        "lessons": [
            {
                "subject_slug": lesson.subject_slug,
                "level": lesson.level.value,
                "tier": lesson.tier,
                "name": lesson.name,
                "description": lesson.description,
                "exercises": [
                    {
                        "type": exercise.type,
                        "question": exercise.question,
                        "content": exercise.content,
                        "correct_answer": exercise.correct_answer,
                        "explanation": exercise.explanation,
                        "difficulty_level": exercise.difficulty_level,
                    }
                    for exercise in lesson.exercises
                ],
            }
            for lesson in detail.lessons
        ],
        "self_check": {"source": "envoi initial"} if had_self_check else None,
    }


@router.patch("/{pack_id}", response_model=PackDetail)
async def quick_edit_pack(
    pack_id: UUID,
    body: PackQuickEdit,
    actor: Annotated[ContributionActor, Depends(contribution_actor)],
    db: Annotated[Session, Depends(get_db)],
) -> PackDetail:
    """Applique les corrections de l'écran d'aperçu, puis **revalide** le pack.

    Args:
        pack_id: Pack à corriger.
        body: Corrections partielles (pack, leçons, exercices).
        actor: Auteur et transport.
        db: Session de base de données.

    Returns:
        Le pack corrigé, tel qu'il sera joué.

    Raises:
        HTTPException: 403 via jeton d'envoi, 404 si le pack n'est pas le sien,
            409 si le pack est verrouillé, 422 si la correction le rendrait invalide.
    """
    user = _require_session(actor)
    pack = _owned_pack(db, pack_id, user)
    is_admin = user.role == UserRole.ADMIN
    assert_pack_mutable(pack, is_admin=is_admin)

    if body.title is not None:
        pack.title = body.title
    if body.emoji is not None:
        pack.emoji = body.emoji or None
    if body.description is not None:
        pack.description = body.description or None
    if body.tags is not None:
        pack.tags = [tag.strip() for tag in body.tags if tag.strip()]

    touched_lessons: set[UUID] = set()
    for lesson_edit in body.lessons:
        lesson = db.query(Lesson).filter(Lesson.id == lesson_edit.id, Lesson.pack_id == pack.id).first()
        if lesson is None:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Leçon {lesson_edit.id} absente de ce pack",
            )
        if lesson_edit.name is not None:
            lesson.name = lesson_edit.name
        if lesson_edit.description is not None:
            lesson.description = lesson_edit.description or None
        if lesson_edit.tier is not None:
            lesson.order_index = lesson_edit.tier
        touched_lessons.add(lesson.id)

        for exercise_edit in lesson_edit.exercises:
            exercise = (
                db.query(Exercise).filter(Exercise.id == exercise_edit.id, Exercise.lesson_id == lesson.id).first()
            )
            if exercise is None:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exercice {exercise_edit.id} absent de la leçon {lesson.id}",
                )
            if exercise_edit.question is not None:
                exercise.question = exercise_edit.question
            if exercise_edit.content is not None:
                exercise.content = exercise_edit.content
            if exercise_edit.correct_answer is not None:
                exercise.correct_answer = exercise_edit.correct_answer
            if exercise_edit.difficulty_level is not None:
                exercise.difficulty_level = exercise_edit.difficulty_level
            if exercise_edit.order_index is not None:
                exercise.order_index = exercise_edit.order_index
    db.flush()

    try:
        _, issues, score = validate_pack(_pack_document(db, pack), known_subject_slugs=known_subject_slugs(db))
    except PackRejected as rejected:
        # Rien n'a été commité : le rollback rétablit exactement l'état d'avant.
        db.rollback()
        raise _rejected(rejected.issues) from rejected

    pack.warnings = [issue.model_dump() for issue in issues]
    pack.quality_score = score
    for lesson_id in touched_lessons:
        # L'XP suit le contenu : changer une difficulté change l'XP de la leçon.
        refresh_lesson_xp(db, lesson_id)
    if is_admin and pack.author_id != user.id:
        log_pack_action(db, pack_id=pack.id, actor_id=user.id, action="admin_edit", detail={"quality_score": score})
    db.commit()
    db.refresh(pack)
    return pack_detail(db, pack)


@router.post("/{pack_id}/submit", response_model=PackDetail)
async def submit_my_pack(
    pack_id: UUID,
    actor: Annotated[ContributionActor, Depends(contribution_actor)],
    db: Annotated[Session, Depends(get_db)],
) -> PackDetail:
    """Soumet un brouillon à la revue (et le rend visible à ses propres enfants)."""
    user = _require_session(actor)
    pack = _owned_pack(db, pack_id, user)
    submit_pack(db, pack, user)
    db.commit()
    db.refresh(pack)
    return pack_detail(db, pack)


@router.post("/{pack_id}/clone", response_model=PackDetail, status_code=status.HTTP_201_CREATED)
async def clone_my_pack(
    pack_id: UUID,
    actor: Annotated[ContributionActor, Depends(contribution_actor)],
    db: Annotated[Session, Depends(get_db)],
) -> PackDetail:
    """Clone un pack en nouveau brouillon : c'est ainsi qu'on révise un pack verrouillé."""
    user = _require_session(actor)
    pack = _owned_pack(db, pack_id, user)
    clone = clone_pack(db, pack=pack, author=user)
    db.commit()
    db.refresh(clone)
    return pack_detail(db, clone)
