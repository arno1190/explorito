"""Schémas du chemin d'accueil de l'enfant (lentilles Thèmes / Matières).

Ces DTO décrivent **un seul jeu de données vu de deux façons** (décision 8 de
l'épopée) : la lentille ne change pas la charge utile, seulement le regroupement
appliqué par le client. Le serveur y met tout ce qu'il faut pour trancher sans
second aller-retour : le verrou, la progression, et le cumul par pack qui permet
de replier un pack terminé en une ligne trophée (décision 17).
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.content import LevelEnum
from app.models.progress import ProgressStatus
from app.schemas.pack import PackSummary

#: Lentille d'accueil. « themes » est le défaut (décision 8) : c'est la seule
#: lecture qui rende un pack transversal (« Coupe du Monde ⚽ ») intelligible.
PackLens = Literal["themes", "matieres"]


class PackPathLesson(BaseModel):
    """Une leçon telle qu'elle apparaît sur le chemin, verrou et progression compris.

    Les noms de champs communs sont alignés sur
    :class:`app.schemas.pack.PackLessonPreview` pour que le frontend manipule la
    même forme de leçon partout. Ce n'est volontairement **pas** une sous-classe :
    l'aperçu embarque ``exercises``, or le chemin d'accueil liste des dizaines de
    leçons et n'en affiche aucun exercice — hériter multiplierait la charge utile
    de l'écran le plus consulté de l'application.
    """

    id: UUID
    name: str
    description: str | None = None
    subject_id: UUID
    subject_slug: str
    subject_name: str | None = None
    subject_icon: str | None = None
    level: LevelEnum
    tier: int
    xp_reward: int = 0
    exercise_count: int = 0
    # Verrou calculé par app.services.progression.lesson_locked : le client
    # l'affiche, ne le recalcule jamais (critère d'acceptation de l'issue #11).
    locked: bool = False
    status: ProgressStatus = ProgressStatus.AVAILABLE
    stars: int = 0
    score: int = 0
    attempts: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    # XP réellement acquis sur cette leçon (0 si non terminée).
    xp_earned: int = 0


class PackPathRollup(BaseModel):
    """Cumul de progression d'un pack : ce que la ligne trophée doit pouvoir dire.

    ``stars_earned``, ``xp_banked`` et ``completed_at`` sont obligatoires dans la
    charge utile : un pack replié sans eux se lirait comme du contenu *retiré* à
    l'enfant, alors qu'il s'agit de contenu *capitalisé* (décision 17).
    """

    lessons_total: int = 0
    lessons_completed: int = 0
    stars_earned: int = 0
    stars_total: int = 0
    xp_banked: int = 0
    xp_total: int = 0
    completed_at: datetime | None = None
    complete: bool = False


class PackPathEntry(BaseModel):
    """Un pack du chemin : sa carte, ses leçons ordonnées par palier, son cumul."""

    pack: PackSummary
    lessons: list[PackPathLesson] = Field(default_factory=list)
    rollup: PackPathRollup


class ContinuerCard(BaseModel):
    """La leçon recommandée, résolue côté serveur.

    Une seule, pour que toutes les surfaces (les deux lentilles, et tout écran
    futur) désignent la même action suivante. ``reason`` distingue la reprise
    d'un pack entamé du démarrage du pack le moins avancé, ce qui suffit au
    client pour choisir son libellé (« Continuer » vs « Commencer »).
    """

    pack_id: UUID
    pack_title: str
    pack_emoji: str | None = None
    reason: Literal["resume", "start"]
    lesson: PackPathLesson


class PackPathResponse(BaseModel):
    """Chemin complet : lentille active, packs, et carte « Continuer ».

    ``continuer`` à ``None`` n'est pas une erreur : c'est l'état vide honnête
    (tout est terminé, ou aucun pack n'est activé pour cet enfant).
    """

    lens: PackLens = "themes"
    entries: list[PackPathEntry] = Field(default_factory=list)
    continuer: ContinuerCard | None = None


class PackLensUpdate(BaseModel):
    """Bascule de lentille, persistée par enfant (``Profile.pack_lens``)."""

    lens: PackLens


class PackLensResponse(BaseModel):
    """Lentille effective après enregistrement."""

    lens: PackLens
