"""Seed CM1 Logique — raisonnement avancé (suites, énigmes, déduction).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_cm1_logique.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, theme

from app.core.database import SessionLocal

LEVEL = "cm1"
SLUG = "logique"


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
        # ------------------------------------------------------------------ #
        # 1 — Suites arithmétiques
        # ------------------------------------------------------------------ #
        L(
            10,
            4,
            "CM1 — Suites arithmétiques 🔢",
            "Trouver le nombre suivant en repérant le pas d'addition ou de soustraction.",
            [
                mcq("Quelle est la suite ? 3, 7, 11, 15, ...", ["18", "19", "20"], 1),
                mcq("Quelle est la suite ? 5, 12, 19, 26, ...", ["31", "32", "33"], 2),
                mcq("Quelle est la suite ? 100, 91, 82, 73, ...", ["64", "65", "63"], 0),
                mcq(
                    "Le pas augmente : 2, 5, 9, 14, 20, ... (on ajoute +3, +4, +5, +6...)",
                    ["26", "27", "28"],
                    1,
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 2 — Suites multiplicatives
        # ------------------------------------------------------------------ #
        L(
            11,
            4,
            "CM1 — Suites multiplicatives ✖️",
            "Reconnaître un pas de multiplication ou un doublage.",
            [
                mcq("Quelle est la suite ? 2, 4, 8, 16, ... (on multiplie par 2)", ["24", "32", "30"], 1),
                mcq("Quelle est la suite ? 3, 9, 27, ... (on multiplie par 3)", ["54", "72", "81"], 2),
                mcq("On double à chaque fois : 1, 2, 4, 8, 16, ...", ["32", "24", "30"], 0),
                mcq("Quelle est la suite ? 5, 10, 20, 40, ...", ["60", "80", "70"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 3 — Suites de figures et de couleurs
        # ------------------------------------------------------------------ #
        L(
            12,
            4,
            "CM1 — Figures et couleurs 🔴",
            "Repérer le motif qui se répète pour deviner l'élément suivant.",
            [
                mcq("Que vient-il après ? 🔴🔵🔴🔵🔴 ...", ["🔴", "🔵", "🟢"], 1),
                mcq("Motif 🔺🔺🔵 qui se répète : 🔺🔺🔵 🔺🔺🔵 🔺🔺 ...", ["🔺", "🔵", "🟢"], 1),
                mcq("Que vient-il après ? 🟩🟨🟩🟨🟩🟨 ...", ["🟩", "🟨", "🟦"], 0),
                mcq("La figure grandit : ⭐, ⭐⭐, ⭐⭐⭐, ...", ["3 étoiles", "4 étoiles", "5 étoiles"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 4 — Trouver l'intrus
        # ------------------------------------------------------------------ #
        L(
            13,
            4,
            "CM1 — Trouver l'intrus 🕵️",
            "Repérer l'élément qui ne suit pas la même règle que les autres.",
            [
                mcq("Quel est l'intrus ? 2, 4, 6, 7, 8 (les nombres pairs)", ["4", "7", "8"], 1),
                mcq("Quel est l'intrus ? 10, 20, 25, 30, 40 (les multiples de 10)", ["20", "25", "40"], 1),
                mcq("Quel est l'intrus ? chien, chat, rose, cheval, lapin", ["chat", "rose", "lapin"], 1),
                mcq("Quel est l'intrus ? 9, 16, 25, 30, 36 (les carrés parfaits)", ["25", "30", "36"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 5 — Tableaux à double entrée
        # ------------------------------------------------------------------ #
        L(
            14,
            5,
            "CM1 — Tableaux à double entrée 📊",
            "Lire un tableau : Léa a 3 pommes et 3 poires, Tom a 1 pomme et 4 poires.",
            [
                mcq(
                    "Combien de fruits en tout ? (Léa : 3 pommes, 3 poires ; Tom : 1 pomme, 4 poires)",
                    ["10", "11", "12"],
                    1,
                ),
                mcq("Combien de poires en tout ?", ["6", "7", "8"], 1),
                mcq("Qui a le plus de fruits ?", ["Léa", "Tom", "Égalité"], 0),
                mcq("Combien Tom a-t-il de pommes de moins que Léa ?", ["1", "2", "3"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 6 — Raisonnement « si… alors »
        # ------------------------------------------------------------------ #
        L(
            15,
            5,
            "CM1 — Si… alors 🧩",
            "Tirer la bonne conclusion d'une règle logique, sans se tromper de sens.",
            [
                mcq(
                    "Tous les chats ont des moustaches. Filou est un chat. Alors...",
                    ["Filou a des moustaches", "Filou n'a pas de moustaches", "On ne sait pas"],
                    0,
                ),
                mcq(
                    "S'il pleut, Marie prend son parapluie. Marie n'a pas son parapluie. Donc...",
                    ["Il pleut", "Il ne pleut pas", "On ne peut rien dire"],
                    1,
                ),
                mcq(
                    "Un nombre pair se termine par 0, 2, 4, 6 ou 8. Le nombre 37 est-il pair ?",
                    ["Oui", "Non", "On ne sait pas"],
                    1,
                ),
                mcq(
                    "Si un animal est un poisson, il vit dans l'eau. Un dauphin vit dans l'eau. Est-il forcément un poisson ?",
                    ["Oui", "Non", "Oui, toujours"],
                    1,
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 7 — Déductions (qui possède quoi)
        # ------------------------------------------------------------------ #
        L(
            16,
            5,
            "CM1 — Qui aime quoi ? 🎨",
            "Emma, Louis et Sara aiment le rouge, le bleu ou le vert (une couleur chacun).",
            [
                mcq(
                    "Emma n'aime ni le rouge ni le vert. Quelle couleur aime-t-elle ?",
                    ["rouge", "bleu", "vert"],
                    1,
                ),
                mcq(
                    "Emma aime le bleu. Louis n'aime pas le vert. Quelle couleur aime Louis ?",
                    ["rouge", "bleu", "vert"],
                    0,
                ),
                mcq(
                    "Emma aime le bleu et Louis le rouge. Quelle couleur reste pour Sara ?",
                    ["rouge", "bleu", "vert"],
                    2,
                ),
                mcq(
                    "Trois amis font foot, judo ou tennis. Marc fait du tennis. Paul ne joue pas au ballon. Que fait Zoé ?",
                    ["foot", "judo", "tennis"],
                    0,
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 8 — Comparaisons et rangements (transitivité)
        # ------------------------------------------------------------------ #
        L(
            17,
            5,
            "CM1 — Rangements logiques 📏",
            "Enchaîner des comparaisons pour ranger du plus petit au plus grand.",
            [
                mcq(
                    "Anna est plus grande que Bob. Bob est plus grand que Chloé. Qui est le plus petit ?",
                    ["Anna", "Bob", "Chloé"],
                    2,
                ),
                mcq(
                    "Le train est plus rapide que le vélo. La voiture est plus rapide que le train. Le plus rapide ?",
                    ["le vélo", "le train", "la voiture"],
                    2,
                ),
                mcq(
                    "Tom pèse plus que Léa. Léa pèse plus que Sam. Qui est le plus léger ?",
                    ["Tom", "Léa", "Sam"],
                    2,
                ),
                mcq(
                    "P est plus âgé que Q, Q que R, et R que S. Qui est le plus jeune ?",
                    ["P", "R", "S"],
                    2,
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 9 — Carrés magiques (simples)
        # ------------------------------------------------------------------ #
        L(
            18,
            5,
            "CM1 — Carrés magiques ✨",
            "Chaque ligne, colonne et diagonale a la même somme, avec les nombres de 1 à 9.",
            [
                mcq("Avec les nombres de 1 à 9, quelle est la somme magique de chaque ligne ?", ["12", "15", "18"], 1),
                mcq("Une ligne contient déjà 8 et 3. Quel nombre la complète pour faire 15 ?", ["3", "4", "5"], 1),
                mcq("Une ligne contient 2 et 7. Quel est le troisième nombre pour faire 15 ?", ["5", "6", "7"], 1),
                mcq("Dans un carré magique 3×3 (1 à 9), quel nombre est toujours au centre ?", ["4", "5", "6"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 10 — Codage et décodage
        # ------------------------------------------------------------------ #
        L(
            19,
            5,
            "CM1 — Codage secret 🔐",
            "Coder et décoder des mots avec A=1, B=2, C=3... ou un décalage de lettres.",
            [
                mcq("Avec A=1, B=2, C=3..., comment code-t-on le mot « CAB » ?", ["312", "321", "123"], 0),
                mcq("Avec A=1, B=2, C=3..., que veut dire le code « 4-1-4-1 » ?", ["DADA", "BABA", "CACA"], 0),
                mcq(
                    "Chaque lettre est remplacée par la suivante (A→B, U→V...). Comment code-t-on « OUI » ?",
                    ["PVJ", "NTH", "PWK"],
                    0,
                ),
                mcq(
                    "On écrit le mot à l'envers. Que donne « RADAR » écrit à l'envers ?", ["RADAR", "RADRA", "ROTOR"], 0
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 11 — Énigmes d'âge
        # ------------------------------------------------------------------ #
        L(
            20,
            5,
            "CM1 — Énigmes d'âge 🎂",
            "Résoudre des problèmes d'âges avec des écarts qui restent constants.",
            [
                mcq("Lucie a 8 ans. Son frère a 3 ans de plus. Quel âge a le frère ?", ["5", "11", "12"], 1),
                mcq("Dans 5 ans, Marie aura 14 ans. Quel âge a-t-elle aujourd'hui ?", ["8", "9", "10"], 1),
                mcq(
                    "Deux frères ont ensemble 20 ans. L'aîné a 4 ans de plus que le cadet. Quel âge a l'aîné ?",
                    ["10", "12", "14"],
                    1,
                ),
                mcq(
                    "Papa a 40 ans, sa fille 10 ans. Dans combien d'années papa aura-t-il le double de l'âge de sa fille ?",
                    ["15", "20", "30"],
                    1,
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 12 — Problèmes de dénombrement (pattes, roues…)
        # ------------------------------------------------------------------ #
        L(
            21,
            4,
            "CM1 — Pattes et roues 🐾",
            "Compter en tenant compte du nombre de pattes ou de roues de chacun.",
            [
                mcq("Dans une ferme, il y a 4 poules. Combien de pattes en tout ?", ["6", "8", "10"], 1),
                mcq("Il y a 3 vaches et 2 canards. Combien de pattes en tout ?", ["14", "16", "18"], 1),
                mcq(
                    "Sur un parking, 3 vélos (2 roues) et 2 voitures (4 roues). Combien de roues ?",
                    ["12", "14", "16"],
                    1,
                ),
                mcq("5 motos (2 roues) et 3 tricycles (3 roues). Combien de roues en tout ?", ["18", "19", "20"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 13 — Proportionnalité (notions simples)
        # ------------------------------------------------------------------ #
        L(
            22,
            5,
            "CM1 — Proportionnalité 🍰",
            "Passer d'une quantité à une autre en gardant le même rapport.",
            [
                mcq("3 stylos coûtent 6 €. Combien coûtent 6 stylos ?", ["9 €", "12 €", "15 €"], 1),
                mcq("2 gâteaux nécessitent 4 œufs. Combien d'œufs pour 5 gâteaux ?", ["8", "10", "12"], 1),
                mcq(
                    "Une voiture roule à 60 km en 1 heure. Combien de km en 3 heures (même vitesse) ?",
                    ["120", "180", "200"],
                    1,
                ),
                mcq("4 places de cinéma coûtent 32 €. Combien coûte 1 place ?", ["6 €", "8 €", "9 €"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 14 — Symétrie et transformations
        # ------------------------------------------------------------------ #
        L(
            23,
            4,
            "CM1 — Symétrie et miroirs 🪞",
            "Reconnaître les axes de symétrie et les images dans un miroir.",
            [
                mcq("Combien d'axes de symétrie a un carré ?", ["2", "4", "6"], 1),
                mcq("La lettre « A » majuscule a un axe de symétrie...", ["vertical", "horizontal", "aucun"], 0),
                mcq("Dans un miroir vertical, la lettre « b » devient...", ["d", "p", "q"], 0),
                mcq("Combien d'axes de symétrie a un cercle ?", ["1", "4", "une infinité"], 2),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 15 — Analogies
        # ------------------------------------------------------------------ #
        L(
            24,
            4,
            "CM1 — Analogies 🔗",
            "Compléter « A est à B ce que C est à... » en trouvant la même relation.",
            [
                mcq("Chaton est à chat ce que chiot est à...", ["chien", "loup", "lapin"], 0),
                mcq("Main est à gant ce que pied est à...", ["chaussure", "chapeau", "écharpe"], 0),
                mcq("2 est à 4 ce que 3 est à... (on multiplie par 2)", ["5", "6", "9"], 1),
                mcq("Oiseau est à voler ce que poisson est à...", ["nager", "marcher", "sauter"], 0),
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CM1 Logique "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
