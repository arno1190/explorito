"""Seed CP Mathématiques — couverture du programme officiel (fondamentaux).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_cp_maths.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, math_problem, mcq, shuffle_options, theme

from app.core.database import SessionLocal

LEVEL = "cp"
SLUG = "maths"


def _lvl(exercises: list[dict[str, Any]], level: int) -> list[dict[str, Any]]:
    for ex in exercises:
        if ex.get("type") != "reading":
            ex["level"] = level
    return exercises


def L(tier: int, level: int, name: str, desc: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
    xp = 30 if level == 1 else 35
    return theme(SLUG, LEVEL, tier, name, desc, xp, _lvl(exercises, level))


def curriculum() -> list[dict[str, Any]]:
    return [
        # 1 — Les nombres jusqu'à 10
        L(
            1,
            1,
            "CP — Les nombres jusqu'à 10 🔟",
            "Dénombrer et écrire les nombres de 0 à 10.",
            [
                mcq("Combien de pommes ? 🍎🍎🍎", ["2", "3", "4"], 1, emoji="🍎"),
                mcq("Combien d'étoiles ? ⭐⭐⭐⭐⭐⭐", ["5", "6", "7"], 1, emoji="⭐"),
                math_problem("Compte les doigts d'une main : combien y en a-t-il ? ✋", 5, emoji="✋"),
                mcq("Comment s'écrit le nombre « huit » en chiffres ?", ["6", "8", "10"], 1),
            ],
        ),
        # 2 — Les nombres jusqu'à 20
        L(
            2,
            1,
            "CP — Les nombres jusqu'à 20 🎈",
            "Compter et reconnaître les nombres de 10 à 20.",
            [
                mcq("Quel nombre vient juste après 12 ?", ["11", "13", "20"], 1),
                mcq("Comment s'écrit le nombre « quinze » en chiffres ?", ["5", "15", "50"], 1),
                math_problem("Il y a 10 billes bleues et 4 billes rouges. Combien de billes ? 🔵", 10 + 4, emoji="🔵"),
                mcq("Quel nombre vient juste avant 20 ?", ["18", "19", "21"], 1),
            ],
        ),
        # 3 — Les nombres jusqu'à 100 (dizaines et unités)
        L(
            3,
            1,
            "CP — Les nombres jusqu'à 100 💯",
            "Comprendre les dizaines et les unités.",
            [
                math_problem("Combien font 3 dizaines ? (3 paquets de 10)", 3 * 10),
                mcq("Dans le nombre 24, quel est le chiffre des dizaines ?", ["2", "4", "24"], 0),
                math_problem("2 dizaines et 5 unités, ça fait quel nombre ?", 2 * 10 + 5),
                mcq("Comment s'écrit « soixante » en chiffres ?", ["16", "60", "66"], 1),
            ],
        ),
        # 4 — Comparer et ranger (<, >, =)
        L(
            4,
            1,
            "CP — Comparer et ranger 📊",
            "Utiliser les signes plus petit, plus grand et égal.",
            [
                mcq("Quel nombre est le plus grand ?", ["7", "9", "5"], 1),
                mcq("Quel signe va entre 8 et 3 ? (8 … 3)", [">", "<", "="], 0),
                mcq("Quel nombre est le plus petit ?", ["14", "11", "17"], 1),
                mcq("Quel signe va entre 6 et 6 ? (6 … 6)", [">", "<", "="], 2),
            ],
        ),
        # 5 — Avant / après, suites de nombres
        L(
            5,
            1,
            "CP — Avant, après et les suites ➡️",
            "Trouver le nombre suivant, le précédent et continuer une suite.",
            [
                math_problem("Quel est le nombre juste après 6 ?", 6 + 1),
                math_problem("Quel est le nombre juste avant 10 ?", 10 - 1),
                mcq("Continue la suite : 2, 4, 6, 8, … ?", ["9", "10", "12"], 1),
                math_problem("Quel nombre est entre 7 et 9 ?", 8),
            ],
        ),
        # 6 — Les compléments à 10
        L(
            6,
            1,
            "CP — Les compléments à 10 🤝",
            "Trouver ce qu'il manque pour aller jusqu'à 10.",
            [
                math_problem("7 + ? = 10", 10 - 7),
                math_problem("Il faut 10 bougies. J'en ai 4. Combien en manque-t-il ? 🕯️", 10 - 4, emoji="🕯️"),
                math_problem("6 + ? = 10", 10 - 6),
                mcq("Quel nombre complète 3 pour faire 10 ?", ["6", "7", "8"], 1),
            ],
        ),
        # 7 — L'addition sans retenue (≤ 20)
        L(
            7,
            1,
            "CP — L'addition ➕",
            "Additionner de petits nombres jusqu'à 20.",
            [
                math_problem("3 + 4 = ?", 3 + 4),
                math_problem("Il y a 5 canards, 3 arrivent. Combien de canards ? 🦆", 5 + 3, emoji="🦆"),
                math_problem("10 + 6 = ?", 10 + 6),
                mcq("Combien font 8 + 5 ?", ["12", "13", "14"], 1),
            ],
        ),
        # 8 — L'addition jusqu'à 100 (dizaines)
        L(
            8,
            1,
            "CP — Additionner les dizaines 🔢",
            "Additionner des dizaines jusqu'à 100.",
            [
                math_problem("20 + 30 = ?", 20 + 30),
                math_problem("40 + 10 = ?", 40 + 10),
                math_problem("J'ai 50 €, je gagne 20 €. Combien en tout ? 💶", 50 + 20, unit="€", emoji="💶"),
                mcq("Combien font 60 + 40 ?", ["90", "100", "110"], 1),
            ],
        ),
        # 9 — La soustraction simple (≤ 20)
        L(
            9,
            1,
            "CP — La soustraction ➖",
            "Enlever et retirer de petits nombres.",
            [
                math_problem("7 - 2 = ?", 7 - 2),
                math_problem("Il y a 9 oiseaux, 4 s'envolent. Combien reste-t-il ? 🐦", 9 - 4, emoji="🐦"),
                math_problem("10 - 6 = ?", 10 - 6),
                mcq("Combien font 15 - 5 ?", ["5", "10", "15"], 1),
            ],
        ),
        # 10 — Les doubles et les moitiés
        L(
            10,
            1,
            "CP — Les doubles et les moitiés ✌️",
            "Calculer le double et la moitié de petits nombres.",
            [
                math_problem("Quel est le double de 3 ?", 3 * 2),
                math_problem("Quel est le double de 5 ?", 5 * 2),
                math_problem("Quelle est la moitié de 8 ?", 8 // 2),
                mcq("Quelle est la moitié de 10 ?", ["4", "5", "6"], 1),
            ],
        ),
        # 11 — Les formes planes
        L(
            11,
            2,
            "CP — Les formes planes 🔷",
            "Reconnaître le carré, le rond, le triangle et le rectangle.",
            [
                mcq("Quelle forme a 3 côtés ? 🔺", ["Le carré", "Le triangle", "Le rond"], 1, emoji="🔺"),
                math_problem("Combien de côtés a un carré ? 🟦", 4, emoji="🟦"),
                mcq("Quelle forme n'a aucun coin ? ⭕", ["Le rond", "Le carré", "Le triangle"], 0, emoji="⭕"),
                mcq(
                    "Quelle forme a 4 côtés, deux longs et deux courts ?",
                    ["Le triangle", "Le rectangle", "Le rond"],
                    1,
                ),
            ],
        ),
        # 12 — Se repérer : gauche / droite, quadrillage
        L(
            12,
            2,
            "CP — Gauche, droite et quadrillage 🧭",
            "Se repérer dans l'espace et sur un quadrillage.",
            [
                mcq("De quel côté est ta main qui écrit (pour la plupart) ?", ["La gauche", "La droite"], 1),
                mcq("Si tu lèves la main droite, l'autre main est à…", ["gauche", "droite"], 0),
                mcq("Sur un quadrillage, une case est un…", ["carreau", "cercle", "triangle"], 0),
                math_problem("Une ligne du quadrillage a 5 cases. Combien de cases sur 2 lignes ?", 5 * 2),
            ],
        ),
        # 13 — La monnaie : les euros
        L(
            13,
            2,
            "CP — La monnaie : les euros 💶",
            "Reconnaître et compter des pièces en euros.",
            [
                math_problem(
                    "J'ai une pièce de 2 € et une pièce de 1 €. Combien en tout ? 🪙", 2 + 1, unit="€", emoji="🪙"
                ),
                math_problem("Deux pièces de 5 €, ça fait combien d'euros ?", 5 + 5, unit="€"),
                math_problem(
                    "Un gâteau coûte 3 €, je paie avec 5 €. Combien me rend-on ? 🍰", 5 - 3, unit="€", emoji="🍰"
                ),
                mcq("Avec une pièce de 2 €, puis-je acheter un ballon à 2 € ?", ["Oui", "Non"], 0),
            ],
        ),
        # 14 — Lire l'heure : les heures pile
        L(
            14,
            2,
            "CP — Lire l'heure ⏰",
            "Lire les heures pile sur une horloge.",
            [
                mcq(
                    "Quand la grande aiguille est sur le 12, il est une heure…",
                    ["pile", "et quart", "et demie"],
                    0,
                ),
                math_problem("Il est 3 heures. Dans 1 heure, il sera quelle heure ?", 3 + 1),
                math_problem("Combien y a-t-il d'heures dans une journée ?", 24),
                mcq("À midi, la petite aiguille est sur le…", ["6", "12", "3"], 1),
            ],
        ),
        # 15 — Les longueurs : comparer les tailles
        L(
            15,
            2,
            "CP — Comparer les longueurs 📏",
            "Comparer les tailles et mesurer en pas ou en cubes.",
            [
                mcq("Qui est le plus grand : un adulte ou un bébé ? 👶", ["L'adulte", "Le bébé"], 0, emoji="👶"),
                mcq("Lequel est le plus long ?", ["Un crayon", "Une règle", "Une gomme"], 1),
                math_problem("Une tour fait 4 cubes, j'en ajoute 3. Combien de cubes ? 🧱", 4 + 3, emoji="🧱"),
                mcq("Pour mesurer la longueur d'une table, j'utilise…", ["une règle", "une balance", "une horloge"], 0),
            ],
        ),
    ]


def main(dry_run: bool = False) -> int:
    themes = shuffle_options(curriculum(), salt="cp-maths")
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CP Maths "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
