"""French instruction audio shared by contributions and curriculum seeders."""

import asyncio
import hashlib
import re
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import edge_tts

from app.core.config import settings

DEFAULT_VOICE = "fr-FR-EloiseNeural"
_EMOJI_RE = re.compile("[\U0001f000-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff⬀-⯿️‍]+")


def clean_for_tts(text: str) -> str:
    text = _EMOJI_RE.sub(" ", text).replace("_", " ").replace("…", ".")
    return re.sub(r"\s+", " ", text).strip()


async def instruction_audio(text: str, *, voice: str = DEFAULT_VOICE) -> str | None:
    """Cache MP3s atomically so failed or concurrent requests cannot corrupt them."""
    spoken = clean_for_tts(text)
    if not spoken:
        return None
    key = hashlib.sha1(f"{voice}:{spoken}".encode()).hexdigest()
    directory = Path(settings.UPLOAD_DIR) / "audio"
    out = directory / f"{key}.mp3"
    if out.exists() and out.stat().st_size > 0:
        return f"/uploads/audio/{key}.mp3"
    directory.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=directory, suffix=".mp3", delete=False) as temporary:
        temp_path = Path(temporary.name)
    try:
        await asyncio.wait_for(edge_tts.Communicate(spoken, voice).save(str(temp_path)), timeout=30)
        if not temp_path.stat().st_size:
            raise RuntimeError("Empty instruction audio")
        temp_path.replace(out)
    finally:
        temp_path.unlink(missing_ok=True)
    return f"/uploads/audio/{key}.mp3"


async def narrate_pack(payload: dict[str, Any]) -> None:
    """Narrate young children's lessons, retaining author-provided media."""
    semaphore = asyncio.Semaphore(4)

    async def narrate(exercise: dict[str, Any]) -> None:
        async with semaphore:
            media = dict(exercise.get("media_urls") or {})
            if not media.get("audio"):
                audio = await instruction_audio(exercise["question"])
                if audio:
                    exercise["media_urls"] = {**media, "audio": audio}

    # TaskGroup cancels outstanding work if any synthesis fails.
    async with asyncio.timeout(120), asyncio.TaskGroup() as group:
        for lesson in payload["lessons"]:
            if lesson["level"] in {"ps", "ms", "gs", "cp"}:
                for exercise in lesson["exercises"]:
                    group.create_task(narrate(exercise))
