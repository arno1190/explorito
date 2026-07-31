"""
Enregistrement des fichiers uploadés (avatars).

Les images sont écrites dans ``UPLOAD_DIR/avatars`` et servies par le montage
statique ``/uploads`` de l'application. On stocke un chemin relatif
(``/uploads/avatars/<nom>``) ; le frontend le résout contre l'URL de l'API.
"""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

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
