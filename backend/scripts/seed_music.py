"""
Seed des leçons de lecture de notes — Musique CE1, clé de sol et clé d'ut 3e ligne.

La clé d'ut 3e ligne est celle de l'alto. Progression : la portée et le sol,
puis do-ré-mi sous la portée, le haut de la portée en clé de sol ; en parallèle
la clé d'ut 3 (le do sur la ligne du milieu) puis les cordes à vide de l'alto
(do, sol, ré, la) ; un défi final mélange les deux clés. Chaque note
s'écoute (synthèse Web Audio côté navigateur, aucun fichier son).

Matière « Musique » à part (et non dans Arts) : les paliers se débloquent par
pack, ces leçons seraient sinon verrouillées derrière toutes celles d'Arts CE1.
Les deux clés s'ouvrent ensemble au palier 1, le défi mélangé arrive en dernier.

Réutilise les constructeurs et l'insertion idempotente de ``seed_curriculum``.

Usage:
    # dev
    DATABASE_URL=postgresql://user@localhost:5432/explorito_dev \\
        uv run python scripts/seed_music.py [--dry-run]
    # prod (dans le conteneur backend)
    uv run python scripts/seed_music.py
"""

import sys
from typing import Any

# ``seed_curriculum`` est dans le même dossier ``scripts/`` (présent dans l'image).
from seed_curriculum import _seed_one, mcq, music_note, reading, theme

from app.core.database import SessionLocal

NAME_Q = "Quelle est cette note ? 🎵"
DO_RE_MI = ["do", "ré", "mi"]
ALTO = "ut3"
STRINGS = ["do", "sol", "ré", "la"]  # cordes à vide de l'alto, du grave à l'aigu


def curriculum() -> list[dict[str, Any]]:
    return [
        # ------------------------------------------------------- clé de sol
        theme(
            "musique",
            "ce1",
            1,
            "La clé de sol 🎼",
            "Découvrir la portée et trouver le sol.",
            40,
            [
                reading(
                    "La maison des notes",
                    "La musique s'écrit sur une PORTÉE : 5 lignes que l'on compte de bas en haut. "
                    "Au début, il y a une clé. La clé de sol s'enroule autour de la 2e ligne : "
                    "toute note posée sur cette ligne s'appelle SOL ! "
                    "Appuie sur 🔊 pour écouter chaque note.",
                ),
                mcq("Combien de lignes a une portée ?", ["4", "5", "6"], 1, emoji="🎼", level=1),
                music_note(NAME_Q, "G4", choices=["fa", "sol", "la"], level=1),
                music_note("Pose un sol sur la portée.", "G4", mode="place", level=1),
                music_note(
                    NAME_Q,
                    "A4",
                    choices=["sol", "la", "si"],
                    explanation="Juste au-dessus du sol, entre deux lignes, c'est LA.",
                    level=1,
                ),
                music_note(
                    NAME_Q,
                    "F4",
                    choices=["fa", "sol", "la"],
                    explanation="Juste en dessous du sol, entre deux lignes, c'est FA.",
                    level=1,
                ),
                music_note(NAME_Q, "B4", choices=["sol", "la", "si"], level=2),
            ],
        ),
        theme(
            "musique",
            "ce1",
            2,
            "Clé de sol : do, ré, mi 🎹",
            "Lire les notes du bas de la portée.",
            45,
            [
                reading(
                    "On monte l'escalier !",
                    "Sous la portée, le DO a besoin d'une petite ligne rien qu'à lui : "
                    "une ligne supplémentaire. Juste au-dessus, collé sous la 1re ligne, c'est RÉ. "
                    "Sur la 1re ligne, c'est MI. Do, ré, mi : chaque note monte d'une marche !",
                ),
                music_note(NAME_Q, "C4", choices=DO_RE_MI, level=1),
                music_note(NAME_Q, "E4", choices=DO_RE_MI, level=1),
                music_note(NAME_Q, "D4", choices=DO_RE_MI, level=2),
                music_note("Pose un do sur sa petite ligne.", "C4", mode="place", level=2),
                music_note("Pose un mi sur la portée.", "E4", mode="place", level=2),
                music_note(
                    NAME_Q,
                    "F4",
                    explanation="Après do, ré, mi vient FA, juste au-dessus de la 1re ligne.",
                    level=2,
                ),
            ],
        ),
        theme(
            "musique",
            "ce1",
            3,
            "Clé de sol : en haut de l'échelle 🪜",
            "Lire les notes du haut de la portée.",
            50,
            [
                reading(
                    "Toujours dans l'ordre",
                    "Les notes se suivent toujours dans le même ordre : do, ré, mi, fa, sol, la, si… "
                    "puis on recommence avec DO ! Sur la 3e ligne, c'est si. Au-dessus viennent do, "
                    "ré sur la 4e ligne, mi, puis fa sur la 5e ligne, tout en haut.",
                ),
                mcq("Quelle note vient après si ?", ["la", "do", "ré"], 1, emoji="🪜", level=1),
                music_note(NAME_Q, "C5", choices=["si", "do", "ré"], level=2),
                music_note(NAME_Q, "D5", choices=["do", "ré", "mi"], level=2),
                music_note(NAME_Q, "F5", level=3),
                music_note(NAME_Q, "E5", level=3),
                music_note("Pose un ré sur la portée.", "D5", mode="place", level=2),
            ],
        ),
        # ------------------------------------------- clé d'ut 3e ligne (alto)
        theme(
            "musique",
            "ce1",
            1,
            "La clé de l'alto 🎻",
            "Découvrir la clé d'ut 3e ligne et trouver le do.",
            45,
            [
                reading(
                    "La clé de l'alto",
                    "Voici la clé d'UT 3e ligne : c'est la clé de l'ALTO ! Ut, c'est l'ancien nom "
                    "du DO. Le milieu de la clé pointe la 3e ligne, celle du milieu : toute note "
                    "posée sur cette ligne s'appelle DO. Écoute-la avec 🔊 !",
                ),
                mcq(
                    "Quel instrument lit la clé d'ut 3e ligne ?",
                    ["La flûte", "L'alto", "La trompette"],
                    1,
                    emoji="🎻",
                    level=1,
                ),
                mcq("Comment appelait-on le do autrefois ?", ["Ré", "Ut", "La"], 1, emoji="🔑", level=1),
                music_note(NAME_Q, "C4", clef=ALTO, choices=["si", "do", "ré"], level=1),
                music_note("Pose un do sur la portée.", "C4", clef=ALTO, mode="place", level=2),
                music_note(
                    NAME_Q,
                    "D4",
                    clef=ALTO,
                    choices=DO_RE_MI,
                    explanation="Juste au-dessus du do, entre deux lignes, c'est RÉ.",
                    level=2,
                ),
                music_note(
                    NAME_Q,
                    "B3",
                    clef=ALTO,
                    choices=["la", "si", "do"],
                    explanation="Juste en dessous du do, on recule d'une marche : c'est SI.",
                    level=2,
                ),
            ],
        ),
        theme(
            "musique",
            "ce1",
            2,
            "Les cordes à vide de l'alto 🎻",
            "Lire do, sol, ré, la : les quatre cordes de l'alto.",
            50,
            [
                reading(
                    "Quatre cordes, quatre notes",
                    "L'alto a 4 cordes : DO, SOL, RÉ et LA. La corde de do est la plus grave : "
                    "elle est sous la portée, accrochée sous une petite ligne. SOL est dans le "
                    "2e interligne, RÉ dans le 4e interligne, et LA se pose juste au-dessus de la portée.",
                ),
                music_note(NAME_Q, "G3", clef=ALTO, choices=STRINGS, level=2),
                music_note(NAME_Q, "D4", clef=ALTO, choices=STRINGS, level=2),
                music_note(
                    NAME_Q,
                    "C3",
                    clef=ALTO,
                    choices=STRINGS,
                    explanation="La plus grosse corde, la plus grave : le DO, sous la portée.",
                    level=2,
                ),
                music_note(NAME_Q, "A4", clef=ALTO, choices=STRINGS, level=2),
                music_note("Pose la corde de sol sur la portée.", "G3", clef=ALTO, mode="place", level=3),
                music_note(NAME_Q, "F3", clef=ALTO, level=3),
                music_note(NAME_Q, "E4", clef=ALTO, level=3),
            ],
        ),
        theme(
            "musique",
            "ce1",
            4,
            "Défi des deux clés 🏆",
            "Ne pas se laisser piéger par la clé !",
            55,
            [
                mcq(
                    "En clé de sol, quelle note est sur la 2e ligne ?",
                    ["fa", "sol", "do"],
                    1,
                    emoji="🎼",
                    level=2,
                ),
                mcq(
                    "En clé d'ut 3, quelle note est sur la 3e ligne ?",
                    ["la", "do", "mi"],
                    1,
                    emoji="🎻",
                    level=2,
                ),
                music_note(NAME_Q, "B4", level=3),
                music_note(
                    NAME_Q,
                    "C4",
                    clef=ALTO,
                    explanation="Même ligne du milieu qu'avant, mais pas la même clé : en clé d'ut 3, c'est DO !",
                    level=3,
                ),
                music_note(NAME_Q, "D5", level=3),
                music_note(NAME_Q, "A3", clef=ALTO, level=3),
                music_note("Pose un mi sur la portée.", "E4", clef=ALTO, mode="place", level=3),
                mcq(
                    "Le do sous la portée en clé de sol et le do de la 3e ligne en clé d'ut 3 ont-ils le même son ?",
                    ["Oui, c'est le même do !", "Non, ils sont différents"],
                    0,
                    emoji="👂",
                    explanation="C'est le même do, celui du milieu du piano : seule la clé change sa place.",
                    level=3,
                ),
            ],
        ),
    ]


def main(dry_run: bool = False) -> int:
    themes = curriculum()
    db = SessionLocal()
    created = skipped = 0
    try:
        for data in themes:
            status = _seed_one(data, db, dry_run=dry_run)
            print(status)
            if status.startswith("+"):
                created += 1
            elif status.startswith("="):
                skipped += 1
        total_ex = sum(len(t["exercises"]) for t in themes)
        print(
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons de lecture de notes "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
