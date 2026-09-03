"""Appareil juridique de la contribution : conditions, pseudonyme, signalements.

Ce module rassemble ce qui doit être **identique** sur toutes les surfaces qui
touchent au contenu venu d'inconnus : le texte des conditions accepté au premier
envoi, les règles du pseudonyme publié, la règle « aucune donnée personnelle »
récitée par le rubric d'écriture *et* par la checklist de revue, et la liste des
motifs de signalement. Dupliquer l'un de ces quatre éléments garantirait qu'une
surface finisse par autoriser ce qu'une autre refuse.

Il est volontairement sans dépendance sur la modération : la contribution
(``services/contribution.py``) et la bibliothèque (``services/library.py``)
l'importent sans tirer la file d'attente admin avec elles.
"""

import enum
import re
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.contribution import ContributorProfile
from app.models.user import Profile, User
from app.services.packs import OFFICIAL_AUTHOR_HANDLE

#: Version des conditions en vigueur. Miroir de la configuration : le stockage
#: de la version acceptée n'a d'intérêt que si un changement de texte change la
#: version, donc la source unique reste ``settings``.
CONTRIBUTOR_TERMS_VERSION = settings.CONTRIBUTOR_TERMS_VERSION

#: Pseudonyme réservé à l'équipe : un contributeur ne peut pas s'en emparer.
RESERVED_HANDLES = (OFFICIAL_AUTHOR_HANDLE, "Explorito Officiel", "Admin", "Modération")

#: Pseudonyme de repli lorsqu'un pack est anonymisé et n'avait aucun pseudonyme.
#: Jamais l'email ni le nom Google : l'anonymisation ne doit pas publier ce que
#: le pseudonymat protégeait.
ANONYMOUS_AUTHOR_HANDLE = "Parent Explorito"

HANDLE_MIN_LENGTH = 3
HANDLE_MAX_LENGTH = 24

#: Caractères autorisés dans un pseudonyme. Pas de « @ » ni de « . » : cela
#: exclut mécaniquement les pseudonymes en forme d'adresse email.
_HANDLE_ALLOWED = re.compile(r"^[a-zA-Z0-9_\- ]+$")

#: Règle « aucune donnée personnelle », citée telle quelle par le rubric
#: d'écriture et par la checklist de revue. L'échec réaliste n'est pas la
#: malveillance : c'est « Les vacances d'Arthur à Biarritz », soit le prénom d'un
#: enfant réel et sa localisation, publiés à des inconnus.
NO_PERSONAL_DATA_RULE = (
    "Aucune donnée personnelle. Un pack est publié à des familles inconnues : "
    "il ne doit contenir ni prénom ou nom d'une personne réelle, ni école, ni "
    "ville de résidence, ni date de naissance, ni photo, ni adresse, ni email, "
    "ni numéro de téléphone, ni lien vers un réseau social. Les prénoms de "
    "personnages inventés ou de figures historiques sont autorisés. Cette règle "
    "s'applique au titre, à la description, aux tags, aux énoncés, aux réponses "
    "et aux explications."
)

#: Conditions de contribution, acceptées une fois (version + horodatage) avant
#: le premier envoi. La licence « distribuer **et modifier** » est porteuse :
#: c'est elle qui autorise l'admin à corriger un pack à la revue, et la clause
#: de survie est ce qui rend une suppression RGPD honorable sans détruire la
#: progression des enfants d'autres familles.
CONTRIBUTOR_TERMS = f"""\
Conditions de contribution — version {CONTRIBUTOR_TERMS_VERSION}

En envoyant un pack à Explorito, vous déclarez et acceptez ce qui suit.

1. Vous êtes l'auteur du contenu. Le contenu que vous envoyez est le vôtre, ou
   vous disposez des droits nécessaires pour le partager. Vous n'y avez pas
   recopié de manuel, de fichier d'éditeur, d'image ni de texte protégé.

2. Vous accordez à Explorito une licence gratuite, mondiale et non exclusive de
   **stocker, reproduire, distribuer, adapter et modifier** votre pack pour le
   proposer aux familles utilisatrices. Le droit de modification est nécessaire :
   à la revue, l'équipe corrige les erreurs de contenu, de niveau, de langue et
   les métadonnées visibles par les enfants (titre, emoji, description).

3. Votre pack peut être publié à d'autres familles. Une fois approuvé, il peut
   être activé par n'importe quel adulte responsable pour son enfant. Vous ne
   choisissez pas qui l'utilise et vous n'en tirez aucune rémunération.

4. Vous êtes publié sous pseudonyme. Seul le pseudonyme que vous choisissez est
   affiché. Ni votre nom, ni votre email, ni votre photo Google n'apparaissent
   sur une surface communautaire. Aucune messagerie et aucun abonnement
   n'existent : les familles ne peuvent pas vous contacter via l'application.

5. Aucune donnée personnelle dans le contenu. {NO_PERSONAL_DATA_RULE}

6. Vos packs survivent à la suppression de votre compte, anonymisés. Si vous
   supprimez votre compte, votre identité est effacée (le pack n'est plus relié
   à votre compte, seul le pseudonyme subsiste), mais les packs approuvés
   restent en place : des enfants d'autres familles y ont une progression
   attachée, et la supprimer effacerait leur travail. Cette conservation, sans
   lien avec votre compte, est la condition pour honorer votre demande de
   suppression sans détruire les données d'autrui.

7. L'équipe peut refuser, corriger ou bloquer un pack. Un refus n'a aucun effet
   sur votre propre famille : votre pack et l'XP déjà gagnée par votre enfant
   restent intacts. Un blocage, réservé au contenu réellement nuisible, masque
   le pack pour tout le monde sans rien supprimer.
"""


class ReportReason(str, enum.Enum):
    """Motif d'un signalement de pack par un parent.

    Liste courte et fermée : un champ libre produit des signalements
    intriables, et le motif détermine l'urgence du traitement (``PERSONAL_DATA``
    et ``INAPPROPRIATE`` peuvent mener à ``blocked``).
    """

    INAPPROPRIATE = "inappropriate"
    WRONG_CONTENT = "wrong_content"
    PERSONAL_DATA = "personal_data"
    DUPLICATE = "duplicate"
    OTHER = "other"


#: Motifs qui justifient un blocage immédiat plutôt qu'un simple refus : le
#: contenu est déjà chez des enfants, l'attente n'est pas neutre.
URGENT_REPORT_REASONS = (ReportReason.INAPPROPRIATE, ReportReason.PERSONAL_DATA)


def normalise_handle(raw: str) -> str:
    """Nettoie un pseudonyme saisi : espaces de bord et espaces internes répétés."""
    return re.sub(r"\s+", " ", (raw or "").strip())


def _identity_key(value: str | None) -> str:
    """Clé de comparaison « même identité » : minuscules, alphanumérique seul.

    Sert à repérer un pseudonyme qui n'en est pas un (« jean.dupont » →
    « jeandupont » → identique à la partie locale de l'email).
    """
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def validate_handle(db: Session, raw: str, *, user: User) -> str:
    """Valide un pseudonyme public et le renvoie normalisé.

    Le pseudonyme est la **seule** chose publiée d'un contributeur : il doit
    donc être unique, lisible, et ne pas reconstituer l'identité réelle que le
    pseudonymat protège (partie locale de l'email, nom Google).

    Args:
        db: Session de base de données.
        raw: Pseudonyme saisi.
        user: Compte auteur (sert aux contrôles anti-identité et à
            l'idempotence : réenvoyer son propre pseudonyme est licite).

    Returns:
        Le pseudonyme normalisé.

    Raises:
        HTTPException: 422 si le pseudonyme est mal formé, réservé ou révèle
            l'identité réelle ; 409 s'il est déjà pris par quelqu'un d'autre.
    """
    handle = normalise_handle(raw)
    if not (HANDLE_MIN_LENGTH <= len(handle) <= HANDLE_MAX_LENGTH):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Le pseudonyme doit faire entre {HANDLE_MIN_LENGTH} et {HANDLE_MAX_LENGTH} caractères.",
        )
    if not _HANDLE_ALLOWED.match(handle):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le pseudonyme n'accepte que lettres, chiffres, tiret, tiret bas et espace.",
        )

    key = _identity_key(handle)
    if any(key == _identity_key(reserved) for reserved in (*RESERVED_HANDLES, ANONYMOUS_AUTHOR_HANDLE)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ce pseudonyme est réservé.",
        )

    local_part = (user.email or "").split("@")[0]
    if key and key == _identity_key(local_part):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Choisissez un pseudonyme qui ne reprend pas votre adresse email.",
        )
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if profile is not None and key and key == _identity_key(profile.display_name):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Choisissez un pseudonyme qui ne reprend pas votre nom réel.",
        )

    # Unicité insensible à la casse : deux pseudonymes ne différant que par la
    # casse seraient indiscernables sur une carte de pack.
    taken = db.query(ContributorProfile).filter(func.lower(ContributorProfile.handle) == handle.lower()).first()
    if taken is not None and taken.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce pseudonyme est déjà pris.")
    return handle


def record_terms_acceptance(profile: ContributorProfile) -> None:
    """Inscrit l'acceptation des conditions (version + horodatage), sans commit."""
    profile.terms_version = CONTRIBUTOR_TERMS_VERSION
    profile.terms_accepted_at = datetime.utcnow()


def terms_accepted(profile: ContributorProfile | None) -> bool:
    """Vrai si le contributeur a accepté la **version en vigueur** des conditions.

    Une version périmée vaut refus : le texte a changé, notamment la clause de
    licence, et l'ancien consentement ne couvre pas le nouveau texte.
    """
    if profile is None:
        return False
    return bool(profile.terms_accepted_at) and profile.terms_version == CONTRIBUTOR_TERMS_VERSION
