"""
Frontière des journées civiles pour les compteurs quotidiens.

Les horodatages sont stockés en UTC naïf : ``datetime.utcnow()`` côté
application, ``func.now()`` côté base. Les compteurs quotidiens — plafond
anti-farm du défi Pythagore, leçons du jour, objectif quotidien — doivent en
revanche se réinitialiser à minuit chez la famille.

Comparer ``func.date(colonne)`` à ``date.today()`` mélange les deux notions : la
première donne une date UTC, la seconde la date du fuseau du processus. Le
résultat ne tombe juste que si le conteneur tourne en UTC, ce qui fait dépendre
l'anti-farm d'une variable d'environnement que personne ne déclare — poser
``TZ=Europe/Paris`` ouvrait deux heures de plafond inopérant chaque nuit.

Ce module traduit « aujourd'hui, chez la famille » en un intervalle UTC
semi-ouvert, comparable directement aux colonnes stockées. Avantage accessoire :
un intervalle sur la colonne nue reste utilisable par un index, là où
``func.date(colonne)`` l'écarte.
"""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings


def local_day_bounds_utc(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Bornes UTC naïves ``[début, fin)`` du jour courant dans le fuseau applicatif.

    Args:
        now: Instant de référence. Un datetime naïf est lu comme de l'UTC, afin
            qu'une valeur relue d'une colonne du modèle soit acceptée telle
            quelle. ``None`` prend l'heure courante.

    Returns:
        Couple ``(début, fin)`` d'horodatages UTC naïfs encadrant la journée
        civile locale. L'intervalle est semi-ouvert : ``début <= t < fin``.
    """
    reference = datetime.now(UTC) if now is None else now
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)

    tz = ZoneInfo(settings.APP_TIMEZONE)
    local_midnight = reference.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    # Arithmétique en heure murale, puis conversion : ``astimezone`` recalcule le
    # décalage réel de la date locale d'arrivée, si bien qu'un jour de changement
    # d'heure dure correctement 23 ou 25 heures.
    next_local_midnight = local_midnight + timedelta(days=1)

    return (
        local_midnight.astimezone(UTC).replace(tzinfo=None),
        next_local_midnight.astimezone(UTC).replace(tzinfo=None),
    )
