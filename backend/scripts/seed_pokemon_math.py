"""
Seed de problèmes de maths « Combats Pokémon » (PV / dégâts) — début de CE1.

Trois leçons (paliers 1 à 3) de problèmes à réponse numérique, sur le thème des
combats Pokémon : points de vie (PV), dégâts, Potions. Nombres adaptés au début
du CE1 (additions/soustractions, multi-étapes seulement au palier « Défi »).
Les réponses sont calculées en Python : correctes par construction.

Réutilise les constructeurs et l'insertion idempotente de ``seed_curriculum``.

Usage:
    # dev
    DATABASE_URL=postgresql://user@localhost:5432/explorito_dev \\
        uv run python scripts/seed_pokemon_math.py [--dry-run]
    # prod (dans le conteneur backend)
    uv run python scripts/seed_pokemon_math.py
"""

import sys
from typing import Any

# ``seed_curriculum`` est dans le même dossier ``scripts/`` (présent dans l'image).
from seed_curriculum import _seed_one, math_problem, theme

from app.core.database import SessionLocal


def curriculum() -> list[dict[str, Any]]:
    return [
        theme(
            "maths",
            "ce1",
            1,
            "Combats Pokémon — Les PV ⚡",
            "Additionner et soustraire des points de vie (début de CE1).",
            45,
            [
                math_problem(
                    "Pikachu a 25 PV. Il perd 10 PV à cause d'une attaque. Combien lui reste-t-il de PV ?",
                    25 - 10,
                    unit="PV",
                    emoji="⚡",
                ),
                math_problem(
                    "Salamèche a 18 PV. Une Potion lui rend 6 PV. Combien a-t-il de PV maintenant ?",
                    18 + 6,
                    unit="PV",
                    emoji="🔥",
                ),
                math_problem(
                    "Carapuce a 20 PV. Il perd 7 PV, puis encore 5 PV. Combien lui reste-t-il de PV ?",
                    20 - 7 - 5,
                    unit="PV",
                    emoji="💧",
                ),
                math_problem(
                    "Bulbizarre attaque deux fois : 4 dégâts puis 6 dégâts. Combien de dégâts en tout ?",
                    4 + 6,
                    unit="dégâts",
                    emoji="🌱",
                ),
                math_problem(
                    "Rondoudou a 30 PV. Après le combat, il lui reste 12 PV. Combien de PV a-t-il perdus ?",
                    30 - 12,
                    unit="PV",
                    emoji="🎤",
                ),
            ],
        ),
        theme(
            "maths",
            "ce1",
            2,
            "Combats Pokémon — Les dégâts 💥",
            "Calculer des PV et des dégâts jusqu'à 100 (début de CE1).",
            50,
            [
                math_problem(
                    "Dracaufeu a 78 PV. Il perd 25 PV. Combien lui reste-t-il de PV ?", 78 - 25, unit="PV", emoji="🔥"
                ),
                math_problem(
                    "Une Potion rend 20 PV et une Super Potion rend 50 PV. Combien de PV récupérés en tout ?",
                    20 + 50,
                    unit="PV",
                    emoji="🧪",
                ),
                math_problem(
                    "Pikachu inflige 15 dégâts, puis 20 dégâts. Combien de dégâts en tout ?",
                    15 + 20,
                    unit="dégâts",
                    emoji="⚡",
                ),
                math_problem(
                    "Ton Pokémon a 60 PV. Il perd 35 PV. Combien lui reste-t-il de PV ?", 60 - 35, unit="PV", emoji="🛡️"
                ),
                math_problem(
                    "Ronflex a 95 PV. Il perd 60 PV. Combien lui reste-t-il de PV ?", 95 - 60, unit="PV", emoji="😴"
                ),
            ],
        ),
        theme(
            "maths",
            "ce1",
            3,
            "Combats Pokémon — Défi Dresseur 🏆",
            "Résoudre des combats en plusieurs étapes (défi début de CE1).",
            55,
            [
                math_problem(
                    "Dracaufeu a 80 PV. Il perd 30 PV, puis 25 PV. Combien lui reste-t-il de PV ?",
                    80 - 30 - 25,
                    unit="PV",
                    emoji="🔥",
                ),
                math_problem(
                    "Ton Pokémon a 50 PV. Il perd 20 PV, puis une Potion lui rend 15 PV. Combien a-t-il de PV ?",
                    50 - 20 + 15,
                    unit="PV",
                    emoji="🧪",
                ),
                math_problem(
                    "L'adversaire a 40 PV. Pikachu inflige 12 dégâts, puis 18 dégâts. Combien lui reste-t-il de PV ?",
                    40 - 12 - 18,
                    unit="PV",
                    emoji="⚡",
                ),
                math_problem(
                    "Ton Pokémon a 100 PV. Il perd 45 PV, puis 30 PV. Combien lui reste-t-il de PV ?",
                    100 - 45 - 30,
                    unit="PV",
                    emoji="💥",
                ),
                math_problem(
                    "Ton Pokémon a 10 PV. Deux Potions lui rendent 25 PV chacune. Combien a-t-il de PV maintenant ?",
                    10 + 25 + 25,
                    unit="PV",
                    emoji="❤️",
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons Pokémon "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
