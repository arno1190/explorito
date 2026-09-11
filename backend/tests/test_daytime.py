"""
Frontière de journée des compteurs quotidiens.

Les horodatages sont stockés en UTC ; « aujourd'hui » doit se réinitialiser à
minuit chez la famille. Ces tests fixent la traduction entre les deux, et
notamment le fait qu'un jour de changement d'heure ne dure pas 24 heures.
"""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.daytime import local_day_bounds_utc


def test_the_window_starts_at_local_midnight_not_utc_midnight():
    # Paris est à UTC+2 en été : minuit local vaut 22h UTC la veille.
    start, end = local_day_bounds_utc(datetime(2026, 7, 15, 9, 0, tzinfo=UTC))
    assert start == datetime(2026, 7, 14, 22, 0)
    assert end == datetime(2026, 7, 15, 22, 0)


def test_the_window_follows_the_winter_offset():
    # UTC+1 en hiver : la même borne tombe à 23h UTC la veille.
    start, end = local_day_bounds_utc(datetime(2026, 1, 15, 9, 0, tzinfo=UTC))
    assert start == datetime(2026, 1, 14, 23, 0)
    assert end == datetime(2026, 1, 15, 23, 0)


def test_an_instant_just_after_local_midnight_belongs_to_the_local_day():
    # 00h30 à Paris le 15 juillet, c'est 22h30 UTC le 14 : la date UTC diffère de
    # la date locale, et c'est précisément là que le décompte se trompait.
    tz = ZoneInfo(settings.APP_TIMEZONE)
    local = datetime(2026, 7, 15, 0, 30, tzinfo=tz)
    as_utc = local.astimezone(UTC).replace(tzinfo=None)
    assert as_utc.date() != local.date()

    start, end = local_day_bounds_utc(local)
    assert start <= as_utc < end


def test_a_spring_forward_day_is_twenty_three_hours_long():
    # 29 mars 2026 : 2h -> 3h à Paris. Une journée civile de 23 heures.
    start, end = local_day_bounds_utc(datetime(2026, 3, 29, 12, 0, tzinfo=UTC))
    assert end - start == timedelta(hours=23)


def test_an_autumn_fallback_day_is_twenty_five_hours_long():
    # 25 octobre 2026 : 3h -> 2h à Paris.
    start, end = local_day_bounds_utc(datetime(2026, 10, 25, 12, 0, tzinfo=UTC))
    assert end - start == timedelta(hours=25)


def test_a_naive_reference_is_read_as_utc():
    # Les colonnes du modèle sont naïves-UTC : passer l'une d'elles directement
    # ne doit pas être interprété comme une heure locale.
    aware = local_day_bounds_utc(datetime(2026, 7, 15, 9, 0, tzinfo=UTC))
    naive = local_day_bounds_utc(datetime(2026, 7, 15, 9, 0))
    assert aware == naive
