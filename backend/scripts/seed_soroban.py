"""
Seed des leçons de boulier (soroban) — Maths CP & CE1, très didactiques.

Progression : CP (une tige, unités 0→9, boule du ciel = 5) puis CE1 (dizaines,
nombres à deux chiffres). Chaque leçon commence par un bloc d'explication
(``reading``), puis alterne « lis le boulier » (``soroban`` mode read) et
« construis le nombre » (``soroban`` mode build, interactif).

Réutilise les constructeurs et l'insertion idempotente de ``seed_curriculum``.

Usage:
    # dev
    DATABASE_URL=postgresql://devuser@localhost:5432/explorito_dev \\
        uv run python scripts/seed_soroban.py [--dry-run]
    # prod (dans le conteneur backend)
    uv run python scripts/seed_soroban.py
"""

import sys
from typing import Any

# ``seed_curriculum`` est dans le même dossier ``scripts/`` (présent dans l'image).
from seed_curriculum import _seed_one, reading, soroban, theme

from app.core.database import SessionLocal

READ_Q = "Quel nombre est représenté sur le boulier ?"


def curriculum() -> list[dict[str, Any]]:
    return [
        # ----------------------------------------------------------------- CP
        theme(
            "maths",
            "cp",
            1,
            "Le boulier — Découverte 🧮",
            "Découvrir le boulier et compter jusqu'à 4.",
            40,
            [
                reading(
                    "Regarde bien le boulier !",
                    "Le boulier a des tiges avec des boules et une barre au milieu. "
                    "En bas de la barre, chaque petite boule vaut 1. "
                    "Pour compter, on POUSSE les boules du bas vers la barre : "
                    "1 boule = 1, 2 boules = 2, 3 boules = 3. À toi de jouer !",
                ),
                soroban(READ_Q, 1, mode="read", columns=1),
                soroban(READ_Q, 3, mode="read", columns=1),
                soroban("Construis le nombre 2 sur le boulier.", 2, mode="build", columns=1),
                soroban("Construis le nombre 4 sur le boulier.", 4, mode="build", columns=1),
            ],
        ),
        theme(
            "maths",
            "cp",
            2,
            "La boule du ciel (5) ⭐",
            "Utiliser la boule du ciel qui vaut 5.",
            45,
            [
                reading(
                    "Une nouvelle boule !",
                    "Au-dessus de la barre, il y a une grosse boule : la BOULE DU CIEL. "
                    "Elle vaut 5 ! Pour faire 5, on pousse la boule du ciel vers la barre. "
                    "Pour faire 6, on met la boule du ciel (5) PLUS 1 boule du bas. "
                    "Pour faire 7, c'est 5 + 2 !",
                ),
                soroban(READ_Q, 5, mode="read", columns=1),
                soroban(READ_Q, 6, mode="read", columns=1),
                soroban(READ_Q, 7, mode="read", columns=1),
                soroban("Construis le nombre 5 sur le boulier.", 5, mode="build", columns=1),
                soroban("Construis le nombre 8 sur le boulier.", 8, mode="build", columns=1),
            ],
        ),
        theme(
            "maths",
            "cp",
            3,
            "Compter jusqu'à 9 🚀",
            "Faire tous les nombres de 0 à 9.",
            50,
            [
                reading(
                    "Le plus grand nombre sur une tige !",
                    "Avec la boule du ciel (5) et les 4 boules du bas, on peut faire tous "
                    "les nombres jusqu'à 9. En effet, 9 = 5 + 4 ! C'est le plus grand "
                    "nombre que l'on peut montrer sur une seule tige.",
                ),
                soroban(READ_Q, 9, mode="read", columns=1),
                soroban(READ_Q, 8, mode="read", columns=1),
                soroban("Construis le nombre 6 sur le boulier.", 6, mode="build", columns=1),
                soroban("Construis le nombre 9 sur le boulier.", 9, mode="build", columns=1),
            ],
        ),
        # ---------------------------------------------------------------- CE1
        theme(
            "maths",
            "ce1",
            1,
            "Le boulier — Les dizaines 🔟",
            "Découvrir la tige des dizaines.",
            45,
            [
                reading(
                    "Une deuxième tige !",
                    "Chaque tige est une colonne. La tige de DROITE, ce sont les unités. "
                    "La tige juste à GAUCHE, ce sont les DIZAINES. Une boule du bas sur la "
                    "tige des dizaines vaut 10 ! Pour faire 10, on pousse 1 boule du bas "
                    "sur la tige des dizaines (et rien sur les unités).",
                ),
                soroban(READ_Q, 10, mode="read", columns=2),
                soroban(READ_Q, 12, mode="read", columns=2),
                soroban("Construis le nombre 10 sur le boulier.", 10, mode="build", columns=2),
                soroban("Construis le nombre 14 sur le boulier.", 14, mode="build", columns=2),
            ],
        ),
        theme(
            "maths",
            "ce1",
            2,
            "Nombres à deux chiffres ✌️",
            "Lire et construire des nombres jusqu'à 99.",
            50,
            [
                reading(
                    "Lire un nombre à deux chiffres",
                    "On lit d'abord les DIZAINES (à gauche), puis les UNITÉS (à droite). "
                    "Par exemple, 23 = 2 dizaines et 3 unités. Sur la tige des dizaines, "
                    "on met 2 ; sur la tige des unités, on met 3.",
                ),
                soroban(READ_Q, 23, mode="read", columns=2),
                soroban(READ_Q, 34, mode="read", columns=2),
                soroban("Construis le nombre 20 sur le boulier.", 20, mode="build", columns=2),
                soroban("Construis le nombre 25 sur le boulier.", 25, mode="build", columns=2),
            ],
        ),
        theme(
            "maths",
            "ce1",
            3,
            "Défi boulier 🏆",
            "Lire et construire de plus grands nombres.",
            55,
            [
                soroban(READ_Q, 42, mode="read", columns=2),
                soroban(READ_Q, 56, mode="read", columns=2),
                soroban("Construis le nombre 37 sur le boulier.", 37, mode="build", columns=2),
                soroban("Construis le nombre 63 sur le boulier.", 63, mode="build", columns=2),
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons boulier "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
