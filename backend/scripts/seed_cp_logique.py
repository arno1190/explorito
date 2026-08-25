"""Seed CP Logique — motifs, tri, déduction (raisonnement).

15 leçons (tiers 1..15), 4 exercices chacune. Réponses correctes par
construction. Idempotent par (parcours, nom de leçon).

Usage:
    DATABASE_URL=... uv run python scripts/seed_cp_logique.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, math_problem, mcq, shuffle_options, theme

from app.core.database import SessionLocal

LEVEL = "cp"
SLUG = "logique"


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
        # 1. Rythme / motif AB qui se répète — tier 1, level 1
        L(
            1,
            1,
            "CP — Le rythme qui se répète 🔴",
            "Reconnaître un motif AB qui se répète et trouver la suite.",
            [
                # 🔴🔵🔴🔵🔴 -> 🔵
                mcq("Que vient-il après ? 🔴 🔵 🔴 🔵 🔴 …", ["🔴", "🔵", "🟢"], 1),
                # 🌞🌙🌞🌙🌞🌙 -> 🌞
                mcq("Que vient-il après ? 🌞 🌙 🌞 🌙 🌞 🌙 …", ["🌞", "🌙", "⭐"], 0),
                # 🐶🐱🐶🐱 -> 🐶
                mcq("Que vient-il après ? 🐶 🐱 🐶 🐱 …", ["🐱", "🐶", "🐰"], 1),
                # 🍎🍌🍎🍌🍎 -> 🍌
                mcq("Que vient-il après ? 🍎 🍌 🍎 🍌 🍎 …", ["🍎", "🍌", "🍇"], 1),
            ],
        ),
        # 2. Compléter une suite ABB / ABC — tier 2, level 1
        L(
            2,
            1,
            "CP — Des motifs plus longs 🔺",
            "Continuer une suite de motifs ABB ou ABC.",
            [
                # motif 🔴🔵🔵 : 🔴🔵🔵 🔴🔵🔵 🔴 -> 🔵
                mcq("Que vient-il après ? 🔴 🔵 🔵 🔴 🔵 🔵 🔴 …", ["🔴", "🔵", "🟢"], 1),
                # motif 🔺🟦⭕ : 🔺🟦⭕ 🔺🟦⭕ 🔺 -> 🟦
                mcq("Que vient-il après ? 🔺 🟦 ⭕ 🔺 🟦 ⭕ 🔺 …", ["⭕", "🟦", "🔺"], 1),
                # motif 🐶🐱🐱 : 🐶🐱🐱 🐶🐱🐱 -> 🐶
                mcq("Que vient-il après ? 🐶 🐱 🐱 🐶 🐱 🐱 …", ["🐱", "🐶", "🐰"], 1),
                # motif 🍎🍌🍇 : 🍎🍌🍇 🍎🍌🍇 🍎🍌 -> 🍇
                mcq("Que vient-il après ? 🍎 🍌 🍇 🍎 🍌 🍇 🍎 🍌 …", ["🍎", "🍌", "🍇"], 2),
            ],
        ),
        # 3. Suites de nombres (1 en 1, 2 en 2) — tier 3, level 1
        L(
            3,
            1,
            "CP — Les suites de nombres 🔢",
            "Compter de 1 en 1 et de 2 en 2 pour continuer une suite.",
            [
                # 1,2,3,4 -> 5
                mcq("Continue la suite : 1, 2, 3, 4, …", ["5", "6", "4"], 0),
                # de 2 en 2 : 2,4,6,8 -> 10
                math_problem("Compte de 2 en 2 : 2, 4, 6, 8, … Quel nombre vient après ?", 10),
                # 5,6,7,8 -> 9
                mcq("Continue la suite : 5, 6, 7, 8, …", ["10", "9", "7"], 1),
                # de 2 en 2 : 10,12,14,16 -> 18
                math_problem("Compte de 2 en 2 : 10, 12, 14, 16, … Quel nombre vient après ?", 18),
            ],
        ),
        # 4. Ranger du plus petit au plus grand — tier 4, level 1
        L(
            4,
            1,
            "CP — Du plus petit au plus grand 📏",
            "Ranger des nombres du plus petit au plus grand.",
            [
                mcq("Range du plus petit au plus grand : 3, 1, 2", ["1, 2, 3", "3, 2, 1", "2, 1, 3"], 0),
                mcq("Range du plus petit au plus grand : 5, 2, 8", ["2, 5, 8", "8, 5, 2", "5, 2, 8"], 0),
                mcq("Quel est le plus PETIT nombre ?", ["7", "4", "9"], 1),
                mcq("Quel est le plus GRAND nombre ?", ["6", "3", "8"], 2),
            ],
        ),
        # 5. Trier selon un critère (couleur, forme, taille) — tier 5, level 1
        L(
            5,
            1,
            "CP — Je trie et je range 🗂️",
            "Trier selon la couleur, la forme ou la taille.",
            [
                # 🍎 rouge, 🫐 bleu, 🍏 vert -> rouge = 🍎
                mcq("Lequel est ROUGE ?", ["🍎", "🫐", "🍏"], 0),
                # le plus gros -> 🐘
                mcq("Quel animal est le plus GROS ?", ["🐘", "🐭", "🐈"], 0),
                # rond -> ⭕
                mcq("Quelle forme est un ROND ?", ["🔺", "⭕", "🟦"], 1),
                # qui va avec les fruits -> 🍌
                mcq("Lequel va avec les FRUITS ?", ["🍌", "🚗", "👟"], 0),
            ],
        ),
        # 6. Trouver l'intrus — tier 6, level 1
        L(
            6,
            1,
            "CP — Trouve l'intrus 🔍",
            "Repérer celui qui ne va pas avec les autres.",
            [
                # fruits vs voiture -> 🚗
                mcq("Quel est l'intrus ?", ["🍎", "🍌", "🚗", "🍇"], 2),
                # animaux vs arbre -> 🌳
                mcq("Quel est l'intrus ?", ["🐶", "🐱", "🐴", "🌳"], 3),
                # ronds vs triangle -> 🔺
                mcq("Quel est l'intrus ?", ["🔴", "🔵", "🟢", "🔺"], 3),
                # nombres pairs vs 5 (impair) -> 5
                mcq("Quel est l'intrus ?", ["2", "4", "5", "6"], 2),
            ],
        ),
        # 7. Comparer : grand/petit, lourd/léger — tier 7, level 1
        L(
            7,
            1,
            "CP — Plus grand ou plus lourd ? ⚖️",
            "Comparer les tailles et les poids.",
            [
                mcq("Qui est le plus GRAND ?", ["🐘", "🐁"], 0),
                mcq("Qu'est-ce qui est le plus LOURD ?", ["Une plume 🪶", "Un rocher 🪨"], 1),
                mcq("Quel nombre est le plus GRAND : 8 ou 5 ?", ["8", "5"], 0),
                mcq("Qu'est-ce qui est le plus LÉGER ?", ["Un éléphant 🐘", "Un papillon 🦋"], 1),
            ],
        ),
        # 8. Tableaux à double entrée simples — tier 8, level 1
        L(
            8,
            1,
            "CP — Je lis un tableau 📋",
            "Trouver une information dans un petit tableau.",
            [
                mcq("Léa aime 🍎, Tom aime 🍌. Qu'aime Léa ?", ["🍎", "🍌"], 0),
                mcq("Léa aime 🍎, Tom aime 🍌. Qui aime la banane 🍌 ?", ["Léa", "Tom"], 1),
                mcq("Lundi il fait ☀️, mardi il pleut 🌧️. Quel temps fait-il mardi ?", ["☀️", "🌧️"], 1),
                mcq("Max a un 🐶, Zoé a un 🐱. Qui a un chat 🐱 ?", ["Max", "Zoé"], 1),
            ],
        ),
        # 9. La symétrie simple — tier 9, level 1
        L(
            9,
            1,
            "CP — Les deux moitiés pareilles 🦋",
            "Reconnaître la symétrie : une moitié pareille à l'autre.",
            [
                # papillon symétrique, lune non
                mcq("Quelle image a ses deux moitiés PAREILLES ?", ["🦋", "🌙"], 0),
                mcq("Le papillon 🦋 a ses deux ailes pareilles. On dit qu'il est…", ["symétrique", "tout mélangé"], 0),
                mcq("Quelle paire est PAREILLE ?", ["🔵 et 🔵", "🔵 et 🔺"], 0),
                # A : symétrique gauche/droite ; J : non
                mcq("Quelle lettre a ses deux moitiés pareilles (comme dans un miroir) ?", ["A", "J"], 0),
            ],
        ),
        # 10. Se repérer dans un quadrillage — tier 10, level 1
        L(
            10,
            1,
            "CP — Je me repère dans la grille 🗺️",
            "Se repérer : gauche/droite, haut/bas, lignes et colonnes.",
            [
                # 🟥 à gauche de 🟦 -> à droite = 🟦
                mcq("🟥 est à gauche de 🟦. Qui est à DROITE ?", ["🟥", "🟦"], 1),
                mcq("Dans la grille, 🐱 est en haut, 🐶 est en bas. Qui est EN HAUT ?", ["🐱", "🐶"], 0),
                # ⭐ 1re ligne, 🌙 2e ligne -> plus haut = ⭐
                mcq("⭐ est sur la 1re ligne, 🌙 est sur la 2e ligne. Qui est le plus HAUT ?", ["⭐", "🌙"], 0),
                mcq("Le trésor 💎 est à droite de la porte 🚪. Où le cherches-tu ?", ["À gauche", "À droite"], 1),
            ],
        ),
        # 11. Raisonnement « si… alors » — tier 11, level 2
        L(
            11,
            2,
            "CP — Si… alors 🧠",
            "Tirer une conclusion à partir d'une règle simple.",
            [
                mcq(
                    "S'il pleut, Léo prend son parapluie ☂️. Il pleut. Que fait Léo ?",
                    ["Il prend son parapluie", "Il met des lunettes de soleil"],
                    0,
                ),
                mcq(
                    "Tous les chats ont des moustaches. Minou est un chat. Alors Minou…",
                    ["a des moustaches", "n'a pas de moustaches"],
                    0,
                ),
                mcq(
                    "Quand il fait nuit 🌙, le ciel est noir. Il fait nuit. Le ciel est…",
                    ["noir", "tout bleu"],
                    0,
                ),
                mcq(
                    "Tous les poissons vivent dans l'eau. Némo est un poisson. Alors Némo vit…",
                    ["dans l'eau", "dans un arbre"],
                    0,
                ),
            ],
        ),
        # 12. Remettre une histoire dans l'ordre — tier 12, level 2
        L(
            12,
            2,
            "CP — Dans le bon ordre 🎬",
            "Remettre les étapes d'une histoire dans l'ordre.",
            [
                mcq(
                    "On plante une graine 🌱. Que se passe-t-il APRÈS ?",
                    ["Une fleur pousse 🌸", "La graine disparaît"],
                    0,
                ),
                mcq("Qui vient en PREMIER ?", ["La graine 🌰", "L'arbre 🌳"], 0),
                mcq("Pour manger une banane, que fait-on d'ABORD ?", ["On l'épluche 🍌", "On la mange"], 0),
                mcq("Le matin on se réveille ☀️. Le soir, on…", ["se couche 🌙", "se réveille encore"], 0),
            ],
        ),
        # 13. Coder / décoder un déplacement (flèches) — tier 13, level 2
        L(
            13,
            2,
            "CP — Le code des flèches 🧭",
            "Suivre et comprendre des déplacements avec des flèches.",
            [
                mcq("➡️ veut dire aller à droite. Où va-t-on avec ➡️ ?", ["À droite", "À gauche"], 0),
                mcq("Je suis les flèches ⬆️ ⬆️. De combien de cases est-ce que je monte ?", ["2", "3"], 0),
                # case 3, +2 -> 5
                math_problem("Je suis sur la case 3. Je suis la flèche ➡️ deux fois (j'avance de 2). Où suis-je ?", 5),
                mcq("⬅️ va à gauche, ➡️ va à droite. Pour revenir en arrière après ➡️, je fais…", ["⬅️", "⬆️"], 0),
            ],
        ),
        # 14. Énigmes de logique simples — tier 14, level 2
        L(
            14,
            2,
            "CP — Devine qui je suis 🔮",
            "Résoudre de petites énigmes avec des indices.",
            [
                mcq("J'ai 4 pattes et je fais « miaou ». Qui suis-je ?", ["Un chat 🐱", "Un oiseau 🐦"], 0),
                mcq(
                    "Je suis jaune, je brille dans le ciel le jour et je réchauffe. Qui suis-je ?",
                    ["Le soleil ☀️", "La lune 🌙"],
                    0,
                ),
                # 2 - 1 = 1
                math_problem("Léa a 2 pommes 🍎. Elle en mange 1. Combien lui en reste-t-il ?", 2 - 1),
                # 3 + 1 = 4
                math_problem("Dans un panier il y a 3 œufs 🥚. J'en ajoute 1. Combien y a-t-il d'œufs ?", 3 + 1),
            ],
        ),
        # 15. Puzzles et assemblages — tier 15, level 2
        L(
            15,
            2,
            "CP — Quelle pièce complète ? 🧩",
            "Trouver la pièce qui complète un puzzle ou un assemblage.",
            [
                mcq(
                    "Un puzzle montre la moitié d'un cœur ❤️. Quelle pièce le complète ?",
                    ["L'autre moitié du cœur", "Un morceau d'étoile"],
                    0,
                ),
                mcq(
                    "Il manque une roue au puzzle de la voiture 🚗. Quelle pièce prends-tu ?",
                    ["Une roue ⚫", "Une fleur 🌸"],
                    0,
                ),
                mcq("Deux carrés identiques mis côte à côte forment un…", ["rectangle", "rond"], 0),
                # 🟨🟥🟨🟥 -> 🟨
                mcq("La suite du puzzle est 🟨 🟥 🟨 🟥. Quelle pièce vient juste après ?", ["🟨", "🟩"], 0),
            ],
        ),
    ]


def main(dry_run: bool = False) -> int:
    themes = shuffle_options(curriculum(), salt="cp-logique")
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CP Logique "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
