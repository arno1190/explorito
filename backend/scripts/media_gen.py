"""Génération d'assets média pour les exercices (audio TTS + pictogrammes).

Deux fonctions idempotentes, pensées pour être appelées au *seed* :

- :func:`tts` — synthèse vocale française via **edge-tts** (voix neuronale
  Microsoft, gratuite, sans clé). Le MP3 est écrit une seule fois sous
  ``UPLOAD_DIR/audio/<sha1>.mp3`` et servi par le montage ``/uploads``.
- :func:`picto` — pictogramme **ARASAAC** (gratuit, éducatif, français) :
  recherche le mot, télécharge le PNG 500px sous
  ``UPLOAD_DIR/img/arasaac/<id>.png``.

Les fichiers vivent dans le volume ``uploads_data`` en prod : générés une fois,
ils persistent d'un déploiement à l'autre. Regénération = supprimer le fichier.

Attribution requise pour ARASAAC (CC BY-NC-SA) : pictogrammes de Sergio Palao
pour ARASAAC (https://arasaac.org), Gouvernement d'Aragon (Espagne). Affichée
dans l'application.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from pathlib import Path

import edge_tts
import requests

from app.core.config import settings

# Voix par défaut : jeune et enjouée, adaptée aux jeunes enfants.
DEFAULT_VOICE = "fr-FR-EloiseNeural"

_UPLOAD = Path(settings.UPLOAD_DIR)
_AUDIO_DIR = _UPLOAD / "audio"
_PICTO_DIR = _UPLOAD / "img" / "arasaac"

_ARASAAC_SEARCH = "https://api.arasaac.org/api/pictograms/fr/search/{word}"
_ARASAAC_IMG = "https://static.arasaac.org/pictograms/{id}/{id}_500.png"

# Emoji / symboles à retirer avant la synthèse vocale (edge-tts les lirait mal).
_EMOJI_RE = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff⬀-⯿️‍]+",
    flags=re.UNICODE,
)

# Mots dont la recherche ARASAAC est ambiguë : on force le bon identifiant.
_PICTO_OVERRIDES: dict[str, int] = {}

# Cache mémoire mot -> id (évite de re-taper l'API dans une même exécution).
_picto_cache: dict[str, int | None] = {}


def clean_for_tts(text: str) -> str:
    """Nettoie un énoncé pour la synthèse : retire emojis et espaces superflus."""
    text = _EMOJI_RE.sub(" ", text)
    text = text.replace("_", " ").replace("…", ".")
    return re.sub(r"\s+", " ", text).strip()


async def _synthesize(text: str, voice: str, out: Path) -> None:
    await edge_tts.Communicate(text, voice).save(str(out))


def tts(text: str, *, voice: str = DEFAULT_VOICE) -> str | None:
    """Synthétise ``text`` en MP3 (idempotent) et renvoie l'URL ``/uploads/...``.

    Renvoie ``None`` si le texte nettoyé est vide (rien à dire).
    """
    spoken = clean_for_tts(text)
    if not spoken:
        return None
    key = hashlib.sha1(f"{voice}:{spoken}".encode()).hexdigest()
    out = _AUDIO_DIR / f"{key}.mp3"
    url = f"/uploads/audio/{key}.mp3"
    if out.exists() and out.stat().st_size > 0:
        return url
    _AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synthesize(spoken, voice, out))
    return url


def _resolve_picto_id(word: str) -> int | None:
    key = word.strip().lower()
    if key in _PICTO_OVERRIDES:
        return _PICTO_OVERRIDES[key]
    if key in _picto_cache:
        return _picto_cache[key]
    try:
        resp = requests.get(_ARASAAC_SEARCH.format(word=key), timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        _picto_cache[key] = None
        return None
    if not isinstance(data, list) or not data:
        _picto_cache[key] = None
        return None
    # Préférence : une entrée dont un mot-clé correspond exactement, sinon la 1re.
    best = next(
        (
            item
            for item in data
            if any((kw.get("keyword") or "").strip().lower() == key for kw in item.get("keywords", []))
        ),
        data[0],
    )
    pid = best.get("_id")
    pid = int(pid) if isinstance(pid, int) else None
    _picto_cache[key] = pid
    return pid


def picto(word: str) -> str | None:
    """Télécharge le pictogramme ARASAAC du ``word`` (idempotent).

    Renvoie l'URL ``/uploads/img/arasaac/<id>.png`` ou ``None`` si introuvable.
    """
    pid = _resolve_picto_id(word)
    if pid is None:
        return None
    out = _PICTO_DIR / f"{pid}.png"
    url = f"/uploads/img/arasaac/{pid}.png"
    if out.exists() and out.stat().st_size > 0:
        return url
    _PICTO_DIR.mkdir(parents=True, exist_ok=True)
    try:
        resp = requests.get(_ARASAAC_IMG.format(id=pid), timeout=30)
        resp.raise_for_status()
    except requests.RequestException:
        return None
    out.write_bytes(resp.content)
    return url
