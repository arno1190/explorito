import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.services.narration import instruction_audio, narrate_pack


def test_audio_is_cached_and_cleaned(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    calls = []

    async def save(self, path):
        calls.append(path)
        Path(path).write_bytes(b"mp3")

    monkeypatch.setattr("edge_tts.Communicate.save", save)
    first = asyncio.run(instruction_audio("Touche 🐱 le chat."))
    assert asyncio.run(instruction_audio("Touche le chat.")) == first
    assert len(calls) == 1
    assert (tmp_path / first.removeprefix("/uploads/")).read_bytes() == b"mp3"


def test_failed_synthesis_does_not_leave_a_cached_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    async def save(self, path):
        Path(path).write_bytes(b"partial")
        raise RuntimeError("unavailable")

    monkeypatch.setattr("edge_tts.Communicate.save", save)
    with pytest.raises(RuntimeError):
        asyncio.run(instruction_audio("Touche le chat."))
    assert list((tmp_path / "audio").iterdir()) == []


def test_young_levels_are_narrated_and_existing_audio_is_retained(monkeypatch):
    synthesize = AsyncMock(return_value="/uploads/audio/test.mp3")
    monkeypatch.setattr("app.services.narration.instruction_audio", synthesize)
    payload = {
        "lessons": [
            {"level": level, "exercises": [{"question": "Touche le chat.", "media_urls": {"emoji": "🐱"}}]}
            for level in ["ps", "ms", "gs", "cp", "ce1"]
        ]
    }
    payload["lessons"][0]["exercises"].append({"question": "Écoute.", "media_urls": {"audio": "/existing.mp3"}})
    asyncio.run(narrate_pack(payload))
    assert synthesize.await_count == 4
    for item in payload["lessons"][:4]:
        assert item["exercises"][0]["media_urls"] == {"emoji": "🐱", "audio": "/uploads/audio/test.mp3"}
    assert payload["lessons"][0]["exercises"][1]["media_urls"]["audio"] == "/existing.mp3"
    assert "audio" not in payload["lessons"][4]["exercises"][0]["media_urls"]
