"""
Endpoints d'authentification JWT
"""

import logging
from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_google_id_token,
    verify_password,
)
from app.models.guardianship import INVITE_SIGNUP
from app.models.user import Profile, User, UserRole
from app.schemas.auth import (
    DevLoginRequest,
    GoogleAuthRequest,
    PinRequest,
    ProfileUpdate,
    RefreshTokenRequest,
    Token,
    UserResponse,
)
from app.services.admin import record_login
from app.services.guardianship import consume_signup_invitation, get_usable_invitation
from app.services.uploads import save_avatar

logger = logging.getLogger("explorito.admin")
router = APIRouter()

# OAuth2 scheme pour l'extraction du token depuis les headers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/dev-login", auto_error=True)


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Récupère un utilisateur par son email

    Args:
        db: Session de base de données
        email: Email de l'utilisateur

    Returns:
        Utilisateur ou None si non trouvé
    """
    return db.query(User).filter(User.email == email).first()


def _role_for_email(email: str) -> UserRole:
    """Rôle attribué à la connexion : admin si l'email est sur l'allowlist."""
    return UserRole.ADMIN if email.lower() in settings.admin_emails_set else UserRole.PARENT


def _issue_token(user: User, db: Session) -> Token:
    """Émet les jetons applicatifs (accès + rafraîchissement) et journalise la connexion."""
    record_login(db, user)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value, "user_id": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_access_token(
        data={"sub": user.email, "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


SIGNUP_INVITE_REQUIRED_MESSAGE = (
    "Explorito est en accès sur invitation. Demandez un code d'invitation à la "
    "personne qui vous a parlé de l'application, puis réessayez."
)

SIGNUP_INVITE_INVALID_MESSAGE = (
    "Ce code d'invitation est invalide, expiré, ou a déjà servi à créer un compte. Demandez-en un nouveau."
)


def _upsert_parent(
    db: Session,
    email: str,
    *,
    display_name: str | None = None,
    google_sub: str | None = None,
    avatar_url: str | None = None,
    invite_token: str | None = None,
) -> User:
    """Récupère ou crée le compte parent associé à un email.

    Le rôle est (re)calculé à chaque connexion depuis l'allowlist admin. Un profil
    parent est créé au premier accès. ``google_sub`` est lié s'il est fourni.

    La porte d'entrée ne se referme que sur la **création** : quand
    ``SIGNUP_INVITE_REQUIRED`` est actif, un compte inconnu exige une invitation
    encore utilisable, tandis qu'un compte existant se connecte toujours sans
    code. Activer le réglage ne doit jamais verrouiller dehors une famille déjà
    installée.

    Deux jetons ouvrent la porte, et ils ne se comportent pas pareil :

    - un code ``signup`` est **brûlé** ici même (un code = une famille) ;
    - un partage de garde (``child`` / ``all``) autorise la création du compte
      sans être consommé : être invité à co-parenter un enfant n'est pas être un
      inconnu, et le jeton reste nécessaire à ``/invitations/{token}/accept``
      pour accorder la garde juste après.

    Args:
        db: Session de base de données.
        email: Email du parent (déjà normalisé en minuscules).
        display_name: Nom d'affichage, à la création seulement.
        google_sub: Identifiant stable Google, lié s'il est fourni.
        avatar_url: Photo de profil, à la création seulement.
        invite_token: Code d'invitation présenté à l'inscription.

    Returns:
        Le compte parent, créé ou récupéré.

    Raises:
        HTTPException: 403 si la création exige un code et qu'aucun code
            valide n'est présenté, ou si le code a été consommé entre-temps.
    """
    user = get_user_by_email(db, email)
    if user is None:
        invitation = None
        if settings.SIGNUP_INVITE_REQUIRED:
            # Un jeton collé depuis un email arrive parfois avec un retour à la
            # ligne : on ne refuse pas une famille pour un espace.
            token = (invite_token or "").strip()
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=SIGNUP_INVITE_REQUIRED_MESSAGE,
                )
            # N'importe quelle invitation encore utilisable ouvre la porte, pas
            # seulement un code ``signup`` : être explicitement invité à
            # co-parenter un enfant, c'est déjà ne pas être un inconnu. Sans
            # cela, activer le réglage condamnerait tout le parcours de partage.
            invitation = get_usable_invitation(token, db)
            if invitation is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=SIGNUP_INVITE_INVALID_MESSAGE,
                )

        user = User(email=email, role=_role_for_email(email), is_active=True, google_sub=google_sub)
        db.add(user)
        db.flush()
        db.add(
            Profile(
                user_id=user.id,
                display_name=display_name or email.split("@")[0],
                avatar_url=avatar_url,
                is_child=False,
                settings={},
            )
        )
        if invitation is not None and invitation.kind == INVITE_SIGNUP:
            # Consommé après la création pour pouvoir enregistrer qui l'a
            # utilisé ; un code = une famille. La consommation est conditionnelle :
            # si une inscription concurrente a gagné la course, ce compte-ci est
            # annulé plutôt que de partager le code à deux.
            if not consume_signup_invitation(invitation, user.id, db):
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=SIGNUP_INVITE_INVALID_MESSAGE,
                )
    else:
        # Synchronise le rôle avec l'allowlist et lie l'identité Google.
        user.role = _role_for_email(email)
        if google_sub and not user.google_sub:
            user.google_sub = google_sub
    db.commit()
    db.refresh(user)
    return user


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
    x_impersonate_user_id: Annotated[str | None, Header()] = None,
) -> User:
    """
    Récupère l'utilisateur actuel à partir du token JWT

    Args:
        token: Token JWT extrait du header Authorization
        db: Session de base de données

    Returns:
        Utilisateur authentifié

    Raises:
        HTTPException: Si le token est invalide ou l'utilisateur n'existe pas
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les informations d'identification",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    email: str | None = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception

    # Impersonation admin — « voir en tant que » un autre compte via l'en-tête
    # X-Impersonate-User-Id. Volontairement restreint pour limiter la surface :
    #   - réservé aux administrateurs ;
    #   - LECTURE SEULE : ignoré sur les requêtes qui modifient l'état
    #     (seules GET/HEAD/OPTIONS sont honorées) — pas d'écriture « en tant que » ;
    #   - cible non-admin uniquement (pas d'impersonation admin → admin) ;
    #   - chaque usage est journalisé (audit).
    if x_impersonate_user_id and user.role == UserRole.ADMIN and request.method in ("GET", "HEAD", "OPTIONS"):
        try:
            target_id = UUID(x_impersonate_user_id)
        except ValueError:
            return user
        target = db.query(User).filter(User.id == target_id).first()
        if target is not None and target.role != UserRole.ADMIN:
            logger.info(
                "admin_impersonation admin=%s target=%s method=%s path=%s",
                user.email,
                target_id,
                request.method,
                request.url.path,
            )
            return target

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Vérifie que l'utilisateur actuel est actif

    Args:
        current_user: Utilisateur authentifié

    Returns:
        Utilisateur actif

    Raises:
        HTTPException: Si l'utilisateur est inactif
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Utilisateur inactif")
    return current_user


@router.post("/google", response_model=Token)
async def google_login(payload: GoogleAuthRequest, db: Annotated[Session, Depends(get_db)]) -> Token:
    """Connexion via Google (flux id_token). Inscription libre des parents.

    Vérifie l'``id_token`` Google, exige un email vérifié, puis crée ou récupère
    le compte parent correspondant et émet un jeton applicatif.

    Raises:
        HTTPException: 401 si le token Google est invalide ou l'email non vérifié.
    """
    try:
        info = verify_google_id_token(payload.credential)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton Google invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    email = info.get("email")
    if not email or not info.get("email_verified"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email Google non vérifié.")

    user = _upsert_parent(
        db,
        email.lower(),
        display_name=info.get("name"),
        google_sub=info.get("sub"),
        avatar_url=info.get("picture"),
        invite_token=payload.invite,
    )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé.")
    return _issue_token(user, db)


if settings.DEBUG:
    # Connexion de développement/tests uniquement (jamais montée en production).
    @router.post("/dev-login", response_model=Token)
    async def dev_login(payload: DevLoginRequest, db: Annotated[Session, Depends(get_db)]) -> Token:
        """Connexion sans Google pour le dev et les tests (email → jeton parent)."""
        user = _upsert_parent(
            db,
            payload.email.lower(),
            display_name=payload.display_name,
            invite_token=payload.invite,
        )
        return _issue_token(user, db)


@router.post("/pin", response_model=UserResponse)
async def set_pin(
    payload: PinRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Définit (ou remplace) le code PIN parent à 4 chiffres."""
    current_user.pin_hash = get_password_hash(payload.pin)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/verify-pin", status_code=status.HTTP_204_NO_CONTENT)
async def verify_pin(
    payload: PinRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """Vérifie le code PIN parent (retour à la vue parent depuis le mode enfant).

    Raises:
        HTTPException: 400 si aucun PIN n'est défini, 401 si le PIN est erroné.
    """
    if not current_user.pin_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucun code PIN défini.")
    if not verify_password(payload.pin, current_user.pin_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Code PIN incorrect.")


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest, db: Annotated[Session, Depends(get_db)]) -> Token:
    """
    Rafraîchit un token d'accès expiré

    Args:
        refresh_data: Token de rafraîchissement
        db: Session de base de données

    Returns:
        Nouveau token d'accès

    Raises:
        HTTPException: Si le refresh token est invalide
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de rafraîchissement invalide",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(refresh_data.refresh_token)
    if payload is None:
        raise credentials_exception

    token_type = payload.get("type")
    if token_type != "refresh":
        raise credentials_exception

    email: str | None = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if user is None or not user.is_active:
        raise credentials_exception

    # Créer un nouveau token d'accès
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value, "user_id": str(user.id)},
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_data.refresh_token,  # Garder le même refresh token
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Récupère les informations de l'utilisateur actuellement connecté

    Args:
        current_user: Utilisateur authentifié et actif

    Returns:
        Informations complètes de l'utilisateur avec son profil
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Met à jour son propre profil (avatar, nom d'affichage).

    Args:
        data: Champs à modifier (seuls ceux fournis sont appliqués).
        current_user: Utilisateur authentifié.
        db: Session de base de données.

    Returns:
        L'utilisateur avec son profil mis à jour.
    """
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil non trouvé")
    if data.display_name is not None:
        profile.display_name = data.display_name
    if data.avatar_url is not None:
        profile.avatar_url = data.avatar_url or None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/avatar", response_model=UserResponse)
async def upload_my_avatar(
    file: Annotated[UploadFile, File(description="Image d'avatar (PNG, JPEG, WebP, GIF)")],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Téléverse une image comme avatar de son propre profil.

    Args:
        file: Fichier image (multipart).
        current_user: Utilisateur authentifié.
        db: Session de base de données.

    Returns:
        L'utilisateur avec l'avatar mis à jour.
    """
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil non trouvé")
    profile.avatar_url = save_avatar(file)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """
    Déconnexion de l'utilisateur

    Note: Avec JWT, la déconnexion est principalement gérée côté client
    en supprimant le token. Cet endpoint peut être utilisé pour des logs
    ou pour invalider des tokens dans une liste noire (non implémenté ici).

    Args:
        current_user: Utilisateur authentifié et actif

    Returns:
        None (204 No Content)
    """
    # Dans une implémentation complète, on pourrait:
    # - Logger la déconnexion
    # - Ajouter le token à une liste noire (blacklist)
    # - Invalider les refresh tokens en base de données
    pass
