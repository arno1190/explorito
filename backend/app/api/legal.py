"""Surface publique des textes juridiques destinés aux familles.

Volontairement lisible **sans session** : une politique de confidentialité que
l'on ne peut consulter qu'après avoir créé un compte — et donc après avoir livré
ses données — ne remplit pas son office. La page ``/confidentialite`` du
frontend lit donc ces routes sans jeton.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user, get_user_by_email
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.legal import PrivacyAccept, PrivacyPolicy
from app.services.family_privacy import (
    current_policy_version,
    privacy_policy_text,
    record_privacy_acceptance,
)

router = APIRouter()

_optional_bearer = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/dev-login", auto_error=False)


@router.get("/privacy", response_model=PrivacyPolicy)
async def get_privacy_policy(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Depends(_optional_bearer)] = None,
) -> PrivacyPolicy:
    """Politique de confidentialité en vigueur, et son acceptation par le compte.

    Sans jeton, renvoie le texte et ``accepted=False`` : c'est ce que lit la
    page publique. Avec un jeton, renvoie en plus l'état d'acceptation, ce dont
    la case à cocher a besoin pour savoir si elle doit encore s'afficher.
    """
    user: User | None = None
    payload = decode_access_token(token) if token else None
    email = payload.get("sub") if payload else None
    if email:
        user = get_user_by_email(db, email=email)
    return PrivacyPolicy(
        version=current_policy_version(),
        text=privacy_policy_text(),
        accepted=user.privacy_accepted if user is not None else False,
        accepted_at=user.privacy_accepted_at if user is not None else None,
    )


@router.post("/privacy/accept", response_model=PrivacyPolicy)
async def accept_privacy_policy(
    body: PrivacyAccept,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PrivacyPolicy:
    """Enregistre l'acceptation de la politique (version acceptée + horodatage).

    Raises:
        HTTPException: 409 si la version envoyée n'est pas celle en vigueur —
            le parent a coché une case portant sur un texte périmé (onglet resté
            ouvert pendant une mise à jour), il doit relire le nouveau.
    """
    if body.version != current_policy_version():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La politique de confidentialité a changé depuis l'affichage. Merci de relire la nouvelle version.",
        )
    record_privacy_acceptance(current_user)
    db.commit()
    db.refresh(current_user)
    return PrivacyPolicy(
        version=current_policy_version(),
        text=privacy_policy_text(),
        accepted=True,
        accepted_at=current_user.privacy_accepted_at,
    )
