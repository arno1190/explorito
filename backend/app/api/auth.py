"""
Endpoints d'authentification JWT
"""

import logging
from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
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


def _upsert_parent(
    db: Session,
    email: str,
    *,
    display_name: str | None = None,
    google_sub: str | None = None,
    avatar_url: str | None = None,
) -> User:
    """Récupère ou crée le compte parent associé à un email (inscription libre).

    Le rôle est (re)calculé à chaque connexion depuis l'allowlist admin. Un profil
    parent est créé au premier accès. ``google_sub`` est lié s'il est fourni.
    """
    user = get_user_by_email(db, email)
    if user is None:
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
    else:
        # Synchronise le rôle avec l'allowlist et lie l'identité Google.
        user.role = _role_for_email(email)
        if google_sub and not user.google_sub:
            user.google_sub = google_sub
    db.commit()
    db.refresh(user)
    return user


async def get_current_user(
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

    # Impersonation admin : un administrateur peut « voir en tant que » un autre
    # compte via l'en-tête X-Impersonate-User-Id (audité). Réservé aux admins.
    if x_impersonate_user_id and user.role == UserRole.ADMIN:
        try:
            target_id = UUID(x_impersonate_user_id)
        except ValueError:
            return user
        target = db.query(User).filter(User.id == target_id).first()
        if target is not None:
            logger.info("admin_impersonation admin=%s target=%s", user.email, target_id)
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
    )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé.")
    return _issue_token(user, db)


if settings.DEBUG:
    # Connexion de développement/tests uniquement (jamais montée en production).
    @router.post("/dev-login", response_model=Token)
    async def dev_login(payload: DevLoginRequest, db: Annotated[Session, Depends(get_db)]) -> Token:
        """Connexion sans Google pour le dev et les tests (email → jeton parent)."""
        user = _upsert_parent(db, payload.email.lower(), display_name=payload.display_name)
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
