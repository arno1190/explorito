"""Seed CE2 Mathématiques — couverture du programme (leçons avancées).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce2_maths.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, math_problem, mcq, theme

from app.core.database import SessionLocal

LEVEL = "ce2"
SLUG = "maths"


def _lvl(exercises: list[dict[str, Any]], level: int) -> list[dict[str, Any]]:
    for ex in exercises:
        if ex.get("type") != "reading":
            ex["level"] = level
    return exercises


def L(tier: int, level: int, name: str, desc: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
    xp = 55 if level == 3 else 60
    return theme(SLUG, LEVEL, tier, name, desc, xp, _lvl(exercises, level))


def curriculum() -> list[dict[str, Any]]:
    return [
        # 1 — Les nombres jusqu'à 10 000
        L(
            10,
            3,
            "CE2 — Les nombres jusqu'à 10 000 🔢",
            "Lire, écrire et décomposer les grands nombres.",
            [
                mcq(
                    "Comment s'écrit en chiffres « sept mille cinq cents » ?",
                    ["7 500", "7 050", "750"],
                    0,
                ),
                math_problem("Dans le nombre 8 246, quel est le chiffre des milliers ?", 8),
                math_problem("Quel est le nombre juste après 9 999 ?", 10000),
                mcq(
                    "Dans 3 608, que représente le chiffre 6 ?",
                    ["6 centaines", "6 dizaines", "6 unités"],
                    0,
                ),
            ],
        ),
        # 2 — Comparer et ranger les nombres
        L(
            11,
            3,
            "CE2 — Comparer et ranger les nombres 📊",
            "Utiliser les signes < et > et ranger les nombres.",
            [
                mcq("Quel signe entre 4 532 et 4 523 ?", [">", "<", "="], 0),
                math_problem("Quel est le plus grand : 2 999, 3 001 ou 2 990 ?", 3001),
                mcq(
                    "Quel est le plus petit nombre ?",
                    ["5 678", "5 687", "5 768"],
                    0,
                ),
                math_problem("Quel est le plus petit : 1 234, 1 243 ou 1 224 ?", 1224),
            ],
        ),
        # 3 — L'addition posée avec retenue
        L(
            12,
            3,
            "CE2 — L'addition posée avec retenue ➕",
            "Additionner en posant l'opération et en gérant les retenues.",
            [
                math_problem("247 + 158 = ?", 247 + 158),
                math_problem("365 + 276 = ?", 365 + 276),
                math_problem("1 456 + 289 = ?", 1456 + 289),
                mcq(
                    "Pourquoi pose-t-on une retenue dans 47 + 38 ?",
                    ["Car 7 + 8 = 15, plus grand que 9", "Car 4 + 3 = 7", "Car le résultat est pair"],
                    0,
                ),
            ],
        ),
        # 4 — La soustraction posée avec retenue
        L(
            13,
            4,
            "CE2 — La soustraction posée avec retenue ➖",
            "Soustraire en posant l'opération avec des retenues.",
            [
                math_problem("523 - 187 = ?", 523 - 187),
                math_problem("600 - 245 = ?", 600 - 245),
                math_problem("1 302 - 458 = ?", 1302 - 458),
                mcq("Combien vaut 500 - 236 ?", ["264", "274", "364"], 0),
            ],
        ),
        # 5 — Les tables de multiplication (2 à 5)
        L(
            14,
            3,
            "CE2 — Les tables de multiplication (2 à 5) ✖️",
            "Mémoriser et utiliser les tables de 2, 3, 4 et 5.",
            [
                math_problem("4 × 6 = ?", 4 * 6),
                math_problem("5 × 7 = ?", 5 * 7),
                math_problem("3 × 8 = ?", 3 * 8),
                mcq("Combien font 2 × 9 ?", ["16", "18", "20"], 1),
            ],
        ),
        # 6 — Les tables de multiplication (6 à 9)
        L(
            15,
            4,
            "CE2 — Les tables de multiplication (6 à 9) 🧮",
            "Mémoriser et utiliser les tables de 6, 7, 8 et 9.",
            [
                math_problem("7 × 8 = ?", 7 * 8),
                math_problem("6 × 9 = ?", 6 * 9),
                math_problem("8 × 8 = ?", 8 * 8),
                mcq("Combien font 9 × 7 ?", ["56", "63", "72"], 1),
            ],
        ),
        # 7 — La multiplication posée (par un chiffre)
        L(
            16,
            4,
            "CE2 — La multiplication posée par un chiffre 🔢",
            "Multiplier un nombre par un chiffre en posant l'opération.",
            [
                math_problem("24 × 3 = ?", 24 * 3),
                math_problem("36 × 4 = ?", 36 * 4),
                math_problem("125 × 6 = ?", 125 * 6),
                mcq("Combien font 48 × 5 ?", ["230", "240", "250"], 1),
            ],
        ),
        # 8 — La division et le partage
        L(
            17,
            4,
            "CE2 — La division et le partage 🍰",
            "Partager en parts égales et calculer des divisions simples.",
            [
                math_problem("On partage 24 bonbons entre 4 enfants. Combien chacun ?", 24 // 4),
                math_problem("36 ÷ 6 = ?", 36 // 6),
                math_problem("On range 30 livres par étagères de 5. Combien d'étagères ?", 30 // 5),
                mcq("Combien font 45 ÷ 9 ?", ["4", "5", "6"], 1),
            ],
        ),
        # 9 — Le double et la moitié
        L(
            18,
            3,
            "CE2 — Le double et la moitié ✌️",
            "Calculer le double et la moitié d'un nombre.",
            [
                math_problem("Quel est le double de 8 ?", 8 * 2),
                math_problem("Quelle est la moitié de 20 ?", 20 // 2),
                math_problem("Quel est le double de 25 ?", 25 * 2),
                mcq("Quelle est la moitié de 14 ?", ["6", "7", "8"], 1),
            ],
        ),
        # 10 — Les mesures de longueur (m, cm, km)
        L(
            19,
            3,
            "CE2 — Les mesures de longueur (m, cm, km) 📏",
            "Connaître et convertir les unités de longueur.",
            [
                math_problem("Combien y a-t-il de centimètres dans 1 mètre ?", 100),
                math_problem("Combien y a-t-il de mètres dans 1 kilomètre ?", 1000),
                math_problem("2 m + 50 cm = ? cm", 250),
                mcq(
                    "Quelle unité pour mesurer la distance entre deux villes ?",
                    ["le centimètre", "le mètre", "le kilomètre"],
                    2,
                ),
            ],
        ),
        # 11 — Les masses (kg, g)
        L(
            20,
            3,
            "CE2 — Les masses (kg, g) ⚖️",
            "Connaître et convertir les unités de masse.",
            [
                math_problem("Combien y a-t-il de grammes dans 1 kilogramme ?", 1000),
                math_problem("2 kg = ? g", 2000),
                math_problem("1 kg et 500 g = ? g", 1500),
                mcq("Avec quelle unité pèse-t-on une plume ?", ["le gramme", "le kilogramme", "le mètre"], 0),
            ],
        ),
        # 12 — Les contenances (le litre)
        L(
            21,
            3,
            "CE2 — Les contenances : le litre 🥤",
            "Mesurer des contenances en litres et centilitres.",
            [
                math_problem("Combien y a-t-il de centilitres dans 1 litre ?", 100),
                math_problem("3 litres = ? cL", 300),
                math_problem("Une bouteille de 2 L contient combien de cL ?", 200),
                mcq(
                    "Quelle unité pour mesurer l'eau d'une piscine ?",
                    ["le gramme", "le litre", "le mètre"],
                    1,
                ),
            ],
        ),
        # 13 — Lire l'heure (heures et minutes)
        L(
            22,
            4,
            "CE2 — Lire l'heure : heures et minutes ⏰",
            "Lire les heures et les minutes sur une horloge.",
            [
                math_problem("Combien y a-t-il de minutes dans 1 heure ?", 60),
                math_problem("Combien y a-t-il de minutes dans 2 heures et demie ?", 150),
                mcq(
                    "Quand la grande aiguille est sur le 6, il est...",
                    ["et quart", "et demie", "moins le quart"],
                    1,
                ),
                math_problem("Il est 8 h 15. Dans 30 minutes, il sera 8 h combien ?", 45),
            ],
        ),
        # 14 — La monnaie (euros et centimes)
        L(
            23,
            4,
            "CE2 — La monnaie : euros et centimes 💶",
            "Compter et rendre la monnaie en euros et centimes.",
            [
                math_problem("Combien y a-t-il de centimes dans 1 euro ?", 100),
                math_problem("J'ai 2 € et 50 centimes. Combien de centimes en tout ?", 250),
                math_problem("Un jouet coûte 7 €. Je paie avec 10 €. Combien me rend-on ?", 10 - 7),
                mcq("Avec 5 €, puis-je acheter un livre à 4 € 50 ?", ["Oui", "Non"], 0),
            ],
        ),
        # 15 — Géométrie : carré, rectangle, triangle, angle droit
        L(
            24,
            4,
            "CE2 — Géométrie : carré, rectangle, triangle 📐",
            "Reconnaître les figures planes et l'angle droit.",
            [
                math_problem("Combien de côtés a un carré ?", 4),
                mcq(
                    "Quelle figure a 4 côtés égaux et 4 angles droits ?",
                    ["le rectangle", "le carré", "le triangle"],
                    1,
                ),
                math_problem("Combien de côtés a un triangle ?", 3),
                mcq("Combien d'angles droits a un rectangle ?", ["2", "3", "4"], 2),
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
            created += status.startswith("+")
            skipped += status.startswith("=")
        total_ex = sum(len(t["exercises"]) for t in themes)
        print(
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE2 Maths "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
