"""Contracts for first-cycle rhythm reading and short melodic dictation."""

from collections.abc import Sequence
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

# One beat is always a quarter note. Rests consume time without an attack.
RHYTHM_BEATS = {
    "ronde": 4.0,
    "blanche": 2.0,
    "noire": 1.0,
    "croche": 0.5,
    "demi_pause": 2.0,
    "soupir": 1.0,
    "demi_soupir": 0.5,
}
RhythmSymbol = Literal["ronde", "blanche", "noire", "croche", "demi_pause", "soupir", "demi_soupir"]


class RhythmChoice(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    events: list[RhythmSymbol] = Field(min_length=1, max_length=16)


def rhythm_beats(events: Sequence[str]) -> float:
    return sum(RHYTHM_BEATS[event] for event in events)


def rhythm_attacks(events: Sequence[str]) -> list[float]:
    position = 0.0
    attacks = []
    for event in events:
        if event in {"ronde", "blanche", "noire", "croche"}:
            attacks.append(position)
        position += RHYTHM_BEATS[event]
    return attacks


class MusicRhythmContent(BaseModel):
    mode: Literal["count", "listen", "tap"] = "count"
    events: list[RhythmSymbol] = Field(min_length=1, max_length=16)
    beats_per_bar: Literal[2, 3, 4] = 4
    bpm: int = Field(default=72, ge=50, le=120, strict=True)
    choices: list[RhythmChoice] | None = Field(default=None, min_length=2, max_length=4)

    @model_validator(mode="after")
    def check_patterns(self) -> "MusicRhythmContent":
        patterns = [self.events] + [choice.events for choice in self.choices or []]
        for events in patterns:
            position = 0.0
            for event in events:
                duration = RHYTHM_BEATS[event]
                if position % self.beats_per_bar + duration > self.beats_per_bar:
                    raise ValueError("Une figure ne peut pas traverser une barre de mesure sans liaison.")
                position += duration
            if position > 16:
                raise ValueError("Un rythme contient au plus 16 temps.")
            if not rhythm_attacks(events):
                raise ValueError("Un rythme doit contenir au moins une note.")
        if self.mode == "listen":
            if not self.choices:
                raise ValueError("Le mode listen exige 2 à 4 choix.")
            if len({choice.id for choice in self.choices}) != len(self.choices):
                raise ValueError("Les identifiants des choix doivent être uniques.")
            if len({tuple(choice.events) for choice in self.choices}) != len(self.choices):
                raise ValueError("Les rythmes proposés doivent être distincts.")
            if any(rhythm_beats(choice.events) != rhythm_beats(self.events) for choice in self.choices):
                raise ValueError("Tous les choix doivent avoir la même durée que le modèle.")
        elif self.choices is not None:
            raise ValueError("choices est réservé au mode listen.")
        if self.mode == "tap" and (
            self.events[0] not in {"ronde", "blanche", "noire", "croche"} or len(rhythm_attacks(self.events)) < 2
        ):
            raise ValueError("Le mode tap commence par une note et comporte au moins deux attaques.")
        return self


class MusicSequenceContent(BaseModel):
    clef: Literal["sol", "fa", "ut3"] = "sol"
    mode: Literal["read", "listen"] = "read"
    pitches: list[str] = Field(min_length=2, max_length=8)
    bpm: int = Field(default=72, ge=50, le=120, strict=True)

    @model_validator(mode="after")
    def check_pitches(self) -> "MusicSequenceContent":
        # Local import avoids a cycle with the existing single-note contract.
        from app.schemas.exercise import MusicNoteContent

        for pitch in self.pitches:
            MusicNoteContent(clef=self.clef, pitch=pitch)
        return self


class TapAnswer(BaseModel):
    taps: list[Annotated[float, Field(strict=True)]] = Field(min_length=2, max_length=16)

    @model_validator(mode="after")
    def check_times(self) -> "TapAnswer":
        import math

        if any(not math.isfinite(t) or t < 0 for t in self.taps):
            raise ValueError("Les frappes doivent être des temps finis et positifs.")
        if any(b <= a for a, b in zip(self.taps, self.taps[1:], strict=False)):
            raise ValueError("Les frappes doivent être strictement croissantes.")
        return self
