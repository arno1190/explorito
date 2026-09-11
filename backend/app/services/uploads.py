"""
Enregistrement et suppression des fichiers uploadés (avatars).

Les images sont écrites dans ``UPLOAD_DIR/avatars`` et servies par le montage
statique ``/uploads`` de l'application. On stocke un chemin relatif
(``/uploads/avatars/<nom>``) ; le frontend le résout contre l'URL de l'API.

Ce montage statique sert le disque, pas la base : effacer la ligne d'un enfant
laisserait son image accessible à quiconque connaît l'URL. La politique de
confidentialité promet l'inverse, d'où :func:`delete_upload`, appelée par le
chemin de suppression d'un compte.
"""

import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

logger = logging.getLogger("explorito.uploads")

# Préfixe des chemins relatifs servis par le montage statique.
UPLOAD_URL_PREFIX = "/uploads/"

# Types MIME image autorisés -> extension de fichier.
ALLOWED_IMAGE_TYPES: dict[str, str] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def save_avatar(file: UploadFile) -> str:
    """
    Valide et enregistre une image d'avatar.

    Args:
        file: Fichier uploadé (multipart).

    Returns:
        Le chemin relatif servi (``/uploads/avatars/<nom>``).

    Raises:
        HTTPException: 400 (format/fichier invalide) ou 413 (trop volumineux).
    """
    ext = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if ext is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format d'image non supporté (PNG, JPEG, WebP ou GIF).",
        )
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier vide.")
    if len(data) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image trop volumineuse (max {settings.MAX_UPLOAD_SIZE // (1024 * 1024)} Mo).",
        )

    avatars_dir = Path(settings.UPLOAD_DIR) / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    (avatars_dir / filename).write_bytes(data)
    return f"/uploads/avatars/{filename}"


def delete_upload(relative_url: str | None) -> bool:
    """Supprime du disque un fichier précédemment téléversé.

    Silencieuse et idempotente : un avatar déjà absent, un emoji stocké dans le
    même champ (``avatar_url`` accepte aussi un caractère) ou une URL externe ne
    sont pas des erreurs — la suppression du compte ne doit jamais échouer pour
    un fichier manquant.

    Args:
        relative_url: Valeur de ``avatar_url``, telle que stockée. Seuls les
            chemins servis par ce module (``/uploads/...``) sont traités.

    Returns:
        ``True`` si un fichier a bien été supprimé du disque.
    """
    if not relative_url or not relative_url.startswith(UPLOAD_URL_PREFIX):
        return False

    root = Path(settings.UPLOAD_DIR).resolve()
    target = (root / relative_url[len(UPLOAD_URL_PREFIX) :]).resolve()
    # Garde-fou : une valeur forgée (``/uploads/../../etc/passwd``) ne doit pas
    # faire sortir la suppression du répertoire d'uploads.
    if not target.is_relative_to(root):
        logger.warning("Chemin d'upload hors du répertoire, suppression ignorée: %s", relative_url)
        return False
    try:
        target.unlink()
    except FileNotFoundError:
        return False
    except OSError as exc:
        logger.warning("Suppression du fichier %s impossible: %s", target, exc)
        return False
    return True
