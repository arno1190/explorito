"""Politique de confidentialité des familles : texte, version, acceptation.

Pendant du module ``contributor_legal`` — qui, lui, ne couvre que les **auteurs
de packs**. Celui-ci couvre l'autre moitié, la plus sensible : les familles, et
donc des données scolaires d'enfants qui ne sont pas ceux de l'hébergeur.

Le texte et la version vivent ici, en un seul endroit, et sont servis par
l'API : la page publique ``/confidentialite`` et la case à cocher de
l'inscription affichent donc forcément le même texte que celui dont la version
est horodatée en base. Recopier ce texte dans le frontend garantirait qu'un jour
un parent accepte une version qui n'est plus celle qui est affichée.

La version n'est **pas** figée à l'import : :func:`current_policy_version` est
la seule lecture de ``settings.PRIVACY_POLICY_VERSION`` de tout le backend.
Une constante de module et une lecture directe du réglage se contrediraient dès
que l'une des deux verrait une autre valeur (réglage modifié à chaud, test qui
monkeypatche) — et cette divergence rend la case à cocher **insatisfaisable** :
l'acceptation enregistrerait une version que ``User.privacy_accepted`` juge
périmée, donc le parent se verrait redemander son consentement à l'infini sans
aucun moyen de passer.

Chaque affirmation factuelle du texte ci-dessous doit être vérifiable dans le
code ; si un comportement change, c'est ce texte qu'il faut corriger avec lui.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.core.config import settings

if TYPE_CHECKING:  # évite le cycle d'imports avec ``app.models.user``, qui lit la version ici
    from app.models.user import User


def current_policy_version() -> str:
    """Version de la politique en vigueur.

    Source unique de vérité : le texte servi, le refus 409 d'une acceptation
    périmée et ``User.privacy_accepted`` passent tous par ici.

    Returns:
        L'identifiant de version (date ISO) de la politique en vigueur.
    """
    return settings.PRIVACY_POLICY_VERSION


def privacy_policy_text() -> str:
    """Texte intégral de la politique, version et mentions légales incluses.

    Returns:
        Le texte servi aux familles, rendu avec la version en vigueur et les
        mentions légales de l'exploitant (réglages ``PRIVACY_*``).
    """
    return f"""\
Politique de confidentialité — version {current_policy_version()}

Explorito est une application d'apprentissage utilisée en famille. Elle héberge
le travail scolaire d'enfants : ce texte dit exactement ce qui est collecté, ce
qui n'est pas collecté, et comment tout effacer.

1. Les enfants n'ont aucun compte.

   C'est le choix structurant. Un enfant ne se connecte pas, n'a ni identifiant,
   ni mot de passe, ni adresse email. C'est l'adulte responsable qui ouvre
   l'application pour lui depuis son propre compte. Il n'existe donc aucun moyen
   pour un enfant de se connecter seul, ni pour un tiers de se connecter à sa
   place.

2. Ce qui est collecté sur l'adulte responsable.

   L'adresse email de son compte Google, son nom d'affichage, sa photo de profil
   Google et l'identifiant technique stable fourni par Google (« sub »), obtenus
   à la connexion. S'il définit un code PIN parent, seule une empreinte
   chiffrée (bcrypt) en est conservée — jamais le code lui-même. Aucun mot de
   passe n'est collecté : Explorito n'en utilise pas.

3. Ce qui est collecté sur l'enfant.

   Son prénom ou surnom d'affichage, sa date de naissance et son niveau
   scolaire, tous trois saisis par l'adulte responsable. S'il le souhaite,
   l'adulte peut aussi choisir une image d'avatar pour l'enfant : elle est alors
   téléversée et stockée sur le serveur, en fichier, et elle est servie à
   l'adresse d'une URL non devinable (nom de fichier aléatoire). Cette image est
   facultative — aucun avatar n'est demandé ni créé par défaut, et une photo de
   l'enfant n'est jamais nécessaire au fonctionnement de l'application.
   Rien d'autre d'identifiant n'est collecté : ni nom de famille obligatoire,
   ni école, ni adresse, ni email, ni numéro de téléphone.

4. Ce qui est enregistré à l'usage.

   Les réponses aux exercices et leur exactitude, la progression dans les
   leçons, l'expérience (XP), les points attribués par le parent, les séries
   de jours consécutifs, et les objets de collection débloqués. Ces données
   n'existent que pour afficher la progression à la famille et pour proposer à
   l'enfant les exercices suivants.

5. Ce qui est enregistré techniquement.

   Le serveur qui reçoit les requêtes en tient un journal (adresse IP, date,
   page demandée), comme tout serveur web, pour la sécurité et le diagnostic de
   panne. L'application conserve en outre, pour chaque connexion d'adulte, la
   date de celle-ci et un compteur cumulé ; ce journal de connexion est purgé
   automatiquement au-delà de quatre-vingt-dix jours.

6. Ce qui n'est jamais fait.

   Aucune publicité. Aucun traceur publicitaire. Aucune revente ni partage des
   données à des tiers. Aucun profilage commercial. Aucune messagerie entre
   familles. Les données ne servent à rien d'autre qu'à faire fonctionner
   l'application pour la famille qui les a saisies.

7. Où les données sont hébergées.

   Sur un serveur unique, dans une base de données PostgreSQL, chez
   l'hébergeur indiqué au point « Mentions légales » ci-dessous. Le
   chiffrement du transport (HTTPS) est assuré par le serveur lui-même : le
   trafic ne passe par aucun intermédiaire technique, ni CDN, ni service de
   filtrage tiers. Aucune donnée n'est transférée hors de l'Union européenne, à
   l'exception de la vérification d'identité opérée par Google au moment de la
   connexion de l'adulte.

8. Combien de temps.

   Les données sont conservées tant que le compte existe. À la suppression,
   elles disparaissent immédiatement de la base de données vivante. Il reste
   les sauvegardes : le serveur en prend une copie compressée régulière, dont
   les exemplaires de plus de sept jours sont automatiquement détruits. Une
   donnée supprimée cesse donc d'exister partout au plus tard sept jours après
   la demande. Les journaux techniques du serveur sont conservés au plus douze
   mois.

9. Comment tout supprimer.

   L'adulte responsable peut supprimer un enfant depuis son tableau de bord :
   le profil de l'enfant, son image d'avatar sur le disque et **toute** sa
   progression (résultats d'exercices, XP, séries, collection) sont effacés
   définitivement de la base, en cascade, immédiatement.

   Il peut aussi demander la suppression de son propre compte en écrivant à
   l'adresse ci-dessous. Ses enfants sont alors supprimés avec lui, avec toutes
   leurs données — sauf si un autre adulte responsable leur est rattaché
   (garde partagée : co-parent, grand-parent, tiers de confiance). Dans ce cas
   l'enfant est conservé pour cet autre adulte, qui reste responsable de ses
   données, et le compte qui part perd simplement tout accès. Supprimer un
   enfant qu'aucun autre adulte ne suit l'efface donc entièrement, et personne
   ne peut faire disparaître l'enfant d'un autre responsable en effaçant son
   propre compte.

   Seule exception, si l'adulte a publié un pack de leçons à d'autres familles :
   le pack reste en ligne mais est détaché de son compte et anonymisé, car
   d'autres enfants y ont une progression rattachée. Cette règle est détaillée
   dans les conditions de contribution, acceptées séparément au premier envoi.

10. Vos droits.

   Vous pouvez demander l'accès, la rectification, l'export ou l'effacement des
   données de votre famille, et vous opposer à leur traitement, en écrivant à
   l'adresse de contact. La demande est traitée sous trente jours. Vous pouvez
   également introduire une réclamation auprès de la CNIL (www.cnil.fr).

11. Mentions légales.

   Éditeur et responsable de traitement : {settings.PRIVACY_PUBLISHER}.
   Contact : {settings.PRIVACY_CONTACT_EMAIL}.
   Hébergeur : {settings.PRIVACY_HOST}.

12. Modifications.

   Ce texte porte une version datée. S'il change sur un point qui vous engage,
   la nouvelle version vous est présentée à la connexion et votre acceptation
   est de nouveau demandée.
"""


def record_privacy_acceptance(user: User) -> None:
    """Inscrit l'acceptation de la politique (version + horodatage), sans commit.

    La lecture symétrique est ``User.privacy_accepted`` : elle vit sur le modèle
    pour être exposée par ``UserResponse`` sans cycle d'imports, mais elle lit
    la version par :func:`current_policy_version`, comme ici — c'est ce qui
    garantit qu'une acceptation enregistrée est bien reconnue comme valide.

    Args:
        user: Le compte adulte qui accepte la politique en vigueur.
    """
    user.privacy_version = current_policy_version()
    user.privacy_accepted_at = datetime.utcnow()
