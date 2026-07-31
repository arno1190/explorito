"""
Endpoints d'authentification JWT
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import Profile, User
from app.schemas.auth import (
    ProfileUpdate,
    RefreshTokenRequest,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.uploads import save_avatar

router = APIRouter()

# OAuth2 scheme pour l'extraction du token depuis les headers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


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


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """
    Authentifie un utilisateur avec email et mot de passe

    Args:
        db: Session de base de données
        email: Email de l'utilisateur
        password: Mot de passe en clair

    Returns:
        Utilisateur si authentification réussie, None sinon
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
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


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Annotated[Session, Depends(get_db)]) -> User:
    """
    Inscrit un nouvel utilisateur (parent ou enfant)

    Args:
        user_data: Données d'inscription
        db: Session de base de données

    Returns:
        Utilisateur créé avec son profil

    Raises:
        HTTPException: Si l'email existe déjà ou si des validations échouent
    """
    # Vérifier si l'email existe déjà
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà",
        )

    # Vérifier le parent pour les enfants
    parent_user = None
    if user_data.role.value == "child" and user_data.parent_email:
        parent_user = get_user_by_email(db, user_data.parent_email)
        if not parent_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent non trouvé avec cet email",
            )
        if parent_user.role.value != "parent":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'email parent doit correspondre à un compte parent",
            )

    # Créer l'utilisateur
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role,
        is_active=True,
    )
    db.add(new_user)
    db.flush()  # Pour obtenir l'ID de l'utilisateur

    # Créer le profil
    profile = Profile(
        user_id=new_user.id,
        display_name=user_data.display_name,
        date_of_birth=user_data.date_of_birth,
        is_child=(user_data.role.value == "child"),
        parent_id=parent_user.id if parent_user else None,
        settings={},
    )
    db.add(profile)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Annotated[Session, Depends(get_db)]) -> Token:
    """
    Connecte un utilisateur et retourne un token JWT

    Args:
        user_credentials: Email et mot de passe
        db: Session de base de données

    Returns:
        Token JWT avec durée de validité

    Raises:
        HTTPException: Si les identifiants sont incorrects
    """
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte utilisateur inactif")

    # Créer le token d'accès
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value, "user_id": str(user.id)},
        expires_delta=access_token_expires,
    )

    # Créer le token de rafraîchissement (durée plus longue)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_access_token(
        data={"sub": user.email, "type": "refresh"}, expires_delta=refresh_token_expires
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # en secondes
    )


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """
    Endpoint de connexion compatible OAuth2 pour la documentation interactive

    Args:
        form_data: Formulaire OAuth2 (username = email, password)
        db: Session de base de données

    Returns:
        Token JWT

    Raises:
        HTTPException: Si les identifiants sont incorrects
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte utilisateur inactif")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value, "user_id": str(user.id)},
        expires_delta=access_token_expires,
    )

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_access_token(
        data={"sub": user.email, "type": "refresh"}, expires_delta=refresh_token_expires
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


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
