"""Seed CM1 Mathématiques — programme avancé (niveau élevé).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_cm1_maths.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, math_problem, mcq, theme

from app.core.database import SessionLocal

LEVEL = "cm1"
SLUG = "maths"


def _lvl(exercises: list[dict[str, Any]], level: int) -> list[dict[str, Any]]:
    for ex in exercises:
        if ex.get("type") != "reading":
            ex["level"] = level
    return exercises


def L(tier: int, level: int, name: str, desc: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
    xp = 60 if level == 4 else 70
    return theme(SLUG, LEVEL, tier, name, desc, xp, _lvl(exercises, level))


def curriculum() -> list[dict[str, Any]]:
    return [
        # --- 1. Tables 2 à 5 ---------------------------------------------- #
        L(
            10,
            4,
            "CM1 — Tables de 2 à 5 🔢",
            "Réviser les tables de multiplication de 2 à 5.",
            [
                math_problem("Combien font 4 × 7 ?", 4 * 7),
                math_problem("Combien font 3 × 9 ?", 3 * 9),
                math_problem("Combien font 5 × 8 ?", 5 * 8),
                mcq("Combien font 4 × 6 ?", ["22", "24", "26"], 1),
            ],
        ),
        # --- 2. Tables 6 à 9 ---------------------------------------------- #
        L(
            11,
            4,
            "CM1 — Tables de 6 à 9 ✖️",
            "Maîtriser les tables les plus difficiles : 6, 7, 8 et 9.",
            [
                math_problem("Combien font 7 × 8 ?", 7 * 8),
                math_problem("Combien font 9 × 6 ?", 9 * 6),
                math_problem("Combien font 6 × 8 ?", 6 * 8),
                mcq("Combien font 9 × 7 ?", ["56", "63", "72"], 1),
            ],
        ),
        # --- 3. Calcul rapide (mélange 2 à 9) ----------------------------- #
        L(
            12,
            5,
            "CM1 — Calcul rapide des tables ⚡",
            "Répondre vite en mélangeant toutes les tables de 2 à 9.",
            [
                math_problem("Combien font 9 × 8 ?", 9 * 8),
                math_problem("Combien font 7 × 7 ?", 7 * 7),
                math_problem("Combien font 6 × 9 ?", 6 * 9),
                mcq("Quel produit est égal à 48 ?", ["6 × 7", "6 × 8", "7 × 8"], 1),
            ],
        ),
        # --- 4. Multiplier par 10, 100, 1000 ------------------------------ #
        L(
            13,
            4,
            "CM1 — Multiplier par 10, 100, 1000 🎯",
            "Ajouter les bons zéros pour multiplier par 10, 100 ou 1000.",
            [
                math_problem("Calcule : 45 × 10", 45 * 10),
                math_problem("Calcule : 38 × 100", 38 * 100),
                math_problem("Calcule : 26 × 1000", 26 * 1000),
                mcq("Combien font 700 × 100 ?", ["7 000", "70 000", "700 000"], 1),
            ],
        ),
        # --- 5. Multiplication posée (2 chiffres) ------------------------- #
        L(
            14,
            5,
            "CM1 — La multiplication posée 📝",
            "Multiplier par un nombre à deux chiffres.",
            [
                math_problem("Calcule : 34 × 26", 34 * 26),
                math_problem("Calcule : 57 × 43", 57 * 43),
                math_problem("Calcule : 128 × 24", 128 * 24),
                math_problem("Un cinéma a 48 rangées de 36 sièges. Combien de sièges ?", 48 * 36, emoji="🎬"),
            ],
        ),
        # --- 6. Nombres jusqu'à 1 000 000 --------------------------------- #
        L(
            15,
            4,
            "CM1 — Les grands nombres 🔭",
            "Lire et décomposer les nombres jusqu'à 1 000 000.",
            [
                mcq("Comment s'écrit « trois cent mille quarante » ?", ["300 040", "30 040", "300 400"], 0),
                math_problem("Dans 458 763, quel est le chiffre des milliers ?", 8),
                math_problem("Calcule : 400 000 + 50 000 + 6 000 + 700 + 20 + 3", 400000 + 50000 + 6000 + 700 + 20 + 3),
                mcq("Quel nombre vient juste après 199 999 ?", ["200 000", "100 000", "199 990"], 0),
            ],
        ),
        # --- 7. La division posée (quotient et reste) --------------------- #
        L(
            16,
            5,
            "CM1 — La division posée ➗",
            "Trouver le quotient et le reste d'une division.",
            [
                math_problem("Dans 47 ÷ 5, quel est le quotient ?", 47 // 5),
                math_problem("Dans 47 ÷ 5, quel est le reste ?", 47 % 5),
                math_problem("Quel est le reste de 100 ÷ 7 ?", 100 % 7),
                math_problem("On range 253 images en paquets de 8. Combien de paquets complets ?", 253 // 8, emoji="🖼️"),
            ],
        ),
        # --- 8. Multiples et calcul mental -------------------------------- #
        L(
            17,
            4,
            "CM1 — Multiples et calcul mental 🧠",
            "Reconnaître les multiples et calculer de tête.",
            [
                mcq("Lequel est un multiple de 9 ?", ["56", "63", "70"], 1),
                math_problem("Quel est le plus grand multiple de 6 inférieur à 50 ?", 48),
                math_problem("Calcule de tête : 25 × 4", 25 * 4),
                mcq("Lequel N'EST PAS un multiple de 3 ?", ["27", "34", "45"], 1),
            ],
        ),
        # --- 9. Les fractions simples ------------------------------------- #
        L(
            18,
            4,
            "CM1 — Les fractions simples 🍕",
            "Prendre une fraction d'une quantité.",
            [
                math_problem("Combien fait 3/4 de 20 ?", 20 * 3 // 4),
                math_problem("Combien fait 2/5 de 30 ?", 30 * 2 // 5),
                math_problem("Combien fait 5/6 de 24 ?", 24 * 5 // 6),
                mcq("Quelle fraction est égale à un demi ?", ["3/6", "2/5", "4/9"], 0),
            ],
        ),
        # --- 10. Comparer et placer des fractions ------------------------- #
        L(
            19,
            5,
            "CM1 — Comparer les fractions ⚖️",
            "Comparer, ranger et placer des fractions.",
            [
                mcq("Quelle fraction est la plus grande ?", ["3/4", "2/4", "1/4"], 0),
                mcq("Quelle fraction est plus grande que 1 ?", ["3/4", "5/4", "2/3"], 1),
                mcq("Laquelle est la plus petite ?", ["1/2", "1/3", "1/5"], 2),
                math_problem("Combien de quarts (1/4) faut-il pour faire un entier ?", 4),
            ],
        ),
        # --- 11. Les nombres décimaux ------------------------------------- #
        L(
            20,
            5,
            "CM1 — Les nombres décimaux 🔟",
            "Comprendre les dixièmes et les centièmes.",
            [
                math_problem("Écris en nombre décimal : 3 unités et 7 dixièmes.", 3.7, tolerance=0.01),
                math_problem("Combien de centièmes y a-t-il dans 1 dixième ?", 10),
                mcq("Comment lit-on 0,25 ?", ["vingt-cinq centièmes", "vingt-cinq dixièmes", "deux virgule cinq"], 0),
                math_problem("Calcule : 2,5 + 1,75", round(2.5 + 1.75, 2), tolerance=0.01),
            ],
        ),
        # --- 12. Périmètre du carré et du rectangle ----------------------- #
        L(
            21,
            4,
            "CM1 — Le périmètre 📏",
            "Calculer le périmètre du carré et du rectangle.",
            [
                math_problem("Périmètre d'un carré de côté 7 cm ?", 4 * 7, unit="cm"),
                math_problem("Périmètre d'un rectangle de 12 cm sur 5 cm ?", 2 * (12 + 5), unit="cm"),
                math_problem("Un carré a un périmètre de 36 cm. Combien mesure un côté ?", 36 // 4, unit="cm"),
                mcq("Formule du périmètre d'un rectangle ?", ["L + l", "2 × (L + l)", "L × l"], 1),
            ],
        ),
        # --- 13. L'aire du carré et du rectangle -------------------------- #
        L(
            22,
            5,
            "CM1 — L'aire 🟩",
            "Calculer l'aire du carré et du rectangle.",
            [
                math_problem("Aire d'un carré de côté 8 cm ?", 8 * 8, unit="cm²"),
                math_problem("Aire d'un rectangle de 15 cm sur 6 cm ?", 15 * 6, unit="cm²"),
                math_problem(
                    "Un rectangle a une aire de 48 cm² et une longueur de 8 cm. Quelle largeur ?", 48 // 8, unit="cm"
                ),
                mcq("Quelle est l'unité d'une aire ?", ["le cm", "le cm²", "le cm³"], 1),
            ],
        ),
        # --- 14. Les durées ----------------------------------------------- #
        L(
            23,
            5,
            "CM1 — Les durées ⏱️",
            "Convertir et calculer des heures, minutes et secondes.",
            [
                math_problem("Combien de minutes dans 3 heures ?", 3 * 60, unit="min"),
                math_problem("Combien de secondes dans 5 minutes ?", 5 * 60, unit="s"),
                math_problem(
                    "Un film dure 2 h 15 min. Combien de minutes en tout ?", 2 * 60 + 15, unit="min", emoji="🎥"
                ),
                math_problem("Il est 9 h 50. Combien de minutes avant 11 h ?", 70, unit="min"),
            ],
        ),
        # --- 15. Problèmes à plusieurs étapes ----------------------------- #
        L(
            24,
            5,
            "CM1 — Problèmes à étapes 🧩",
            "Résoudre des problèmes en plusieurs calculs.",
            [
                math_problem(
                    "3 cahiers à 4 € et 2 stylos à 3 €. Combien en tout ?", 3 * 4 + 2 * 3, unit="€", emoji="🛒"
                ),
                math_problem(
                    "28 élèves montent dans un bus de 45 places. Combien de places libres ?", 45 - 28, emoji="🚌"
                ),
                math_problem(
                    "Un fermier a 1 250 pommes, en vend 780 et range le reste en 5 caisses égales. Combien par caisse ?",
                    (1250 - 780) // 5,
                    emoji="🍎",
                ),
                math_problem(
                    "Un livre de 240 pages. Léa lit 35 pages par jour pendant 6 jours. Combien de pages restantes ?",
                    240 - 35 * 6,
                    emoji="📖",
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
            created += status.startswith("+")
            skipped += status.startswith("=")
        total_ex = sum(len(t["exercises"]) for t in themes)
        print(
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CM1 Maths "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
