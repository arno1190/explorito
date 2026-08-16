"""Seed CE2 Logique — raisonnement, suites, énigmes (leçons avancées).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce2_logique.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, theme

from app.core.database import SessionLocal

LEVEL = "ce2"
SLUG = "logique"


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
        # 1. Suites croissantes (+2, +5, +10…) — tier 10, level 3
        L(
            10,
            3,
            "CE2 — Les suites qui montent 📈",
            "Continuer une suite croissante (+2, +5, +10).",
            [
                # 2, 4, 6, 8, ? -> 10
                mcq("Continue la suite : 2, 4, 6, 8, … (+2)", ["9", "10", "12"], 1),
                # 5, 10, 15, 20, ? -> 25
                mcq("Continue la suite : 5, 10, 15, 20, … (+5)", ["24", "25", "30"], 1),
                # 10, 20, 30, 40, ? -> 50
                mcq("Continue la suite : 10, 20, 30, 40, … (+10)", ["45", "50", "60"], 1),
                # 3, 6, 9, 12, ? -> 15
                mcq("Continue la suite : 3, 6, 9, 12, … (+3)", ["13", "14", "15"], 2),
            ],
        ),
        # 2. Suites décroissantes (−n) — tier 11, level 3
        L(
            11,
            3,
            "CE2 — Les suites qui descendent 📉",
            "Continuer une suite décroissante.",
            [
                # 20, 18, 16, 14, ? -> 12
                mcq("Continue la suite : 20, 18, 16, 14, … (−2)", ["10", "12", "13"], 1),
                # 50, 45, 40, 35, ? -> 30
                mcq("Continue la suite : 50, 45, 40, 35, … (−5)", ["25", "30", "32"], 1),
                # 100, 90, 80, 70, ? -> 60
                mcq("Continue la suite : 100, 90, 80, 70, … (−10)", ["50", "60", "65"], 1),
                # 30, 27, 24, 21, ? -> 18
                mcq("Continue la suite : 30, 27, 24, 21, … (−3)", ["18", "19", "20"], 0),
            ],
        ),
        # 3. Suites multiplicatives (×2) — tier 12, level 4
        L(
            12,
            4,
            "CE2 — Les suites qui doublent ✖️",
            "Continuer une suite en multipliant (×2).",
            [
                # 1, 2, 4, 8, ? -> 16
                mcq("Continue la suite : 1, 2, 4, 8, … (×2)", ["10", "12", "16"], 2),
                # 3, 6, 12, 24, ? -> 48
                mcq("Continue la suite : 3, 6, 12, 24, … (×2)", ["36", "48", "26"], 1),
                # 5, 10, 20, 40, ? -> 80
                mcq("Continue la suite : 5, 10, 20, 40, … (×2)", ["60", "80", "45"], 1),
                # 2, 4, 8, 16, ? -> 32
                mcq("Continue la suite : 2, 4, 8, 16, … (×2)", ["24", "32", "18"], 1),
            ],
        ),
        # 4. Suites de formes et couleurs — tier 13, level 3
        L(
            13,
            3,
            "CE2 — Suites de formes et couleurs 🔺",
            "Trouver ce qui vient après dans une suite de formes ou de couleurs.",
            [
                # 🔴🔵🔴🔵🔴 ? -> 🔵
                mcq("Que vient-il après ? 🔴 🔵 🔴 🔵 🔴 …", ["🔴", "🔵", "🟢"], 1),
                # 🔺🔺🔵🔺🔺🔵 ? -> répète 🔺🔺🔵, après 🔵 vient 🔺
                mcq("Que vient-il après ? 🔺 🔺 🔵 🔺 🔺 🔵 …", ["🔺", "🔵", "🟢"], 0),
                # 🟡🟢🟡🟢🟡🟢 ? -> 🟡
                mcq("Que vient-il après ? 🟡 🟢 🟡 🟢 🟡 🟢 …", ["🟢", "🟡", "🔴"], 1),
                # ⬛⬛⬜⬛⬛⬜ ? -> motif ⬛⬛⬜, après ⬜ vient ⬛
                mcq("Que vient-il après ? ⬛ ⬛ ⬜ ⬛ ⬛ ⬜ …", ["⬜", "⬛", "🟥"], 1),
            ],
        ),
        # 5. Trouver l'intrus — tier 14, level 3
        L(
            14,
            3,
            "CE2 — Trouve l'intrus 🔍",
            "Repérer l'élément qui n'a pas sa place.",
            [
                # animaux vs objet -> chaise
                mcq("Quel est l'intrus ?", ["Chien", "Chat", "Chaise", "Cheval"], 2),
                # fruits vs légume -> carotte
                mcq("Quel est l'intrus ?", ["Pomme", "Banane", "Carotte", "Fraise"], 2),
                # nombres pairs vs impair -> 7
                mcq("Quel est l'intrus ?", ["2", "4", "7", "8"], 2),
                # couleurs vs forme -> Carré
                mcq("Quel est l'intrus ?", ["Rouge", "Bleu", "Carré", "Vert"], 2),
            ],
        ),
        # 6. Classer par catégories — tier 15, level 3
        L(
            15,
            3,
            "CE2 — Ranger par familles 🗂️",
            "Classer les mots dans la bonne catégorie.",
            [
                mcq("Dans quelle famille ranger la « rose » ? 🌹", ["Les fleurs", "Les animaux", "Les outils"], 0),
                mcq("Dans quelle famille ranger le « marteau » ? 🔨", ["Les fruits", "Les outils", "Les vêtements"], 1),
                mcq(
                    "Dans quelle famille ranger le « pantalon » ? 👖",
                    ["Les vêtements", "Les meubles", "Les légumes"],
                    0,
                ),
                mcq(
                    "Lequel n'est PAS un moyen de transport ?",
                    ["La voiture", "Le vélo", "La banane", "L'avion"],
                    2,
                ),
            ],
        ),
        # 7. Tableaux à double entrée — tier 16, level 4
        L(
            16,
            4,
            "CE2 — Les tableaux à deux entrées 📊",
            "Lire une information au croisement d'une ligne et d'une colonne.",
            [
                # Léa aime le rouge / Tom aime le bleu / Zoé aime le vert
                mcq(
                    "Tableau : Léa→rouge, Tom→bleu, Zoé→vert. Quelle couleur aime Tom ?",
                    ["Rouge", "Bleu", "Vert"],
                    1,
                ),
                mcq(
                    "Tableau : Léa→rouge, Tom→bleu, Zoé→vert. Qui aime le vert ?",
                    ["Léa", "Tom", "Zoé"],
                    2,
                ),
                # Fruits par jour : lundi pomme, mardi poire, mercredi kiwi
                mcq(
                    "Tableau : lundi→pomme, mardi→poire, mercredi→kiwi. Quel fruit mardi ?",
                    ["Pomme", "Poire", "Kiwi"],
                    1,
                ),
                mcq(
                    "Tableau : lundi→pomme, mardi→poire, mercredi→kiwi. Quel jour pour le kiwi ?",
                    ["Lundi", "Mardi", "Mercredi"],
                    2,
                ),
            ],
        ),
        # 8. Raisonnement « si… alors » — tier 17, level 4
        L(
            17,
            4,
            "CE2 — Le raisonnement « si… alors » 🧠",
            "Tirer une conclusion à partir d'une règle.",
            [
                mcq(
                    "Si tous les chats ont des moustaches, et Minou est un chat, alors Minou…",
                    ["a des moustaches", "n'a pas de moustaches", "est un chien"],
                    0,
                ),
                mcq(
                    "S'il pleut, alors Léo prend son parapluie. Il pleut. Que fait Léo ?",
                    ["Il prend son parapluie", "Il reste sans rien", "Il prend des lunettes"],
                    0,
                ),
                mcq(
                    "Si un nombre est pair, il se termine par 0, 2, 4, 6 ou 8. Le nombre 14 est-il pair ?",
                    ["Oui", "Non", "On ne peut pas savoir"],
                    0,
                ),
                mcq(
                    "Tous les oiseaux ont des plumes. Le pingouin est un oiseau. Donc le pingouin…",
                    ["a des plumes", "a des écailles", "n'est pas un animal"],
                    0,
                ),
            ],
        ),
        # 9. Comparer / transitivité — tier 18, level 4
        L(
            18,
            4,
            "CE2 — Plus grand, plus petit ⚖️",
            "Comparer et raisonner par transitivité.",
            [
                # Tom > Léa, Léa > Zoé => Tom le plus grand
                mcq(
                    "Tom est plus grand que Léa. Léa est plus grande que Zoé. Qui est le plus grand ?",
                    ["Tom", "Léa", "Zoé"],
                    0,
                ),
                # Même énoncé -> le plus petit = Zoé
                mcq(
                    "Tom est plus grand que Léa. Léa est plus grande que Zoé. Qui est le plus petit ?",
                    ["Tom", "Léa", "Zoé"],
                    2,
                ),
                # A < B, B < C => A le plus petit ; question plus grand nombre
                mcq(
                    "Le chat pèse moins que le chien. Le chien pèse moins que le cheval. Le plus lourd est…",
                    ["Le chat", "Le chien", "Le cheval"],
                    2,
                ),
                mcq(
                    "Range du plus petit au plus grand : 47, 74, 17.",
                    ["17, 47, 74", "17, 74, 47", "47, 17, 74"],
                    0,
                ),
            ],
        ),
        # 10. Symétrie / pareil-différent — tier 19, level 3
        L(
            19,
            3,
            "CE2 — Pareil ou différent ? 🪞",
            "Reconnaître la symétrie et ce qui est identique.",
            [
                mcq(
                    "Quelle lettre reste PAREILLE dans un miroir vertical ?",
                    ["A", "B", "F"],
                    0,
                ),
                mcq(
                    "Quelle forme a un axe de symétrie ?",
                    ["Le cœur ❤️", "La virgule", "Le zigzag"],
                    0,
                ),
                mcq(
                    "Quelle paire est PAREILLE ?",
                    ["🐶 et 🐶", "🐶 et 🐱", "🐶 et 🐰"],
                    0,
                ),
                mcq(
                    "Le papillon 🦋 a ses deux ailes identiques. On dit qu'il est…",
                    ["symétrique", "tout différent", "cassé"],
                    0,
                ),
            ],
        ),
        # 11. Codage par symboles — tier 20, level 4
        L(
            20,
            3,
            "CE2 — Le code des symboles ⭐",
            "Calculer avec un code : ⭐=1, 🌙=2, ☀️=5.",
            [
                # ⭐=1, 🌙=2 -> ⭐+🌙 = 3
                mcq("Si ⭐ = 1 et 🌙 = 2, combien font ⭐ + 🌙 ?", ["2", "3", "4"], 1),
                # 🌙+🌙 = 4
                mcq("Si 🌙 = 2, combien font 🌙 + 🌙 ?", ["3", "4", "5"], 1),
                # ☀️=5, ⭐=1 -> ☀️+⭐ = 6
                mcq("Si ☀️ = 5 et ⭐ = 1, combien font ☀️ + ⭐ ?", ["5", "6", "7"], 1),
                # ☀️+🌙 = 5+2 = 7
                mcq("Si ☀️ = 5 et 🌙 = 2, combien font ☀️ + 🌙 ?", ["6", "7", "8"], 1),
            ],
        ),
        # 12. Énigmes d'âge — tier 21, level 4
        L(
            21,
            3,
            "CE2 — Les énigmes d'âge 🎂",
            "Trouver un âge à partir d'indices.",
            [
                # Léa a 8 ans, son frère a 2 ans de plus -> 10
                mcq("Léa a 8 ans. Son frère a 2 ans de plus. Quel âge a le frère ?", ["6", "10", "12"], 1),
                # Tom a 7, sa soeur a 3 de moins -> 4
                mcq("Tom a 7 ans. Sa sœur a 3 ans de moins. Quel âge a la sœur ?", ["3", "4", "10"], 1),
                # Papa a 30, dans 5 ans -> 35
                mcq("Papa a 30 ans. Quel âge aura-t-il dans 5 ans ?", ["25", "35", "40"], 1),
                # Zoé a 9, il y a 2 ans elle avait -> 7
                mcq("Zoé a 9 ans. Quel âge avait-elle il y a 2 ans ?", ["7", "8", "11"], 0),
            ],
        ),
        # 13. Problèmes de dénombrement (pattes, roues) — tier 22, level 4
        L(
            22,
            4,
            "CE2 — Combien de pattes et de roues ? 🐾",
            "Compter en groupant (pattes, roues, doigts).",
            [
                # 3 chats × 4 pattes = 12
                mcq("Combien de pattes ont 3 chats ? (4 pattes chacun)", ["8", "12", "16"], 1),
                # 2 voitures × 4 roues = 8
                mcq("Combien de roues ont 2 voitures ? (4 roues chacune)", ["6", "8", "10"], 1),
                # 2 mains × 5 doigts = 10
                mcq("Combien de doigts sur 2 mains ? (5 doigts chacune)", ["8", "10", "12"], 1),
                # 3 vélos × 2 roues = 6
                mcq("Combien de roues ont 3 vélos ? (2 roues chacun)", ["5", "6", "8"], 1),
            ],
        ),
        # 14. Déplacements et chemins — tier 23, level 4
        L(
            23,
            4,
            "CE2 — Chemins et déplacements 🧭",
            "Suivre des déplacements gauche/droite, avancer/reculer.",
            [
                # Départ 5, avance 3 -> 8
                mcq("Je suis sur la case 5. J'avance de 3 cases. Où suis-je ?", ["7", "8", "9"], 1),
                # Case 10, recule 4 -> 6
                mcq("Je suis sur la case 10. Je recule de 4 cases. Où suis-je ?", ["5", "6", "7"], 1),
                # Face au nord, tourne à droite -> est
                mcq("Je regarde vers le Nord. Je tourne à droite. Je regarde vers…", ["l'Est", "l'Ouest", "le Sud"], 0),
                # Avance 2, recule 1, avance 3 depuis 0 -> 4
                mcq("Départ case 0 : j'avance de 2, je recule de 1, j'avance de 3. Où suis-je ?", ["3", "4", "5"], 1),
            ],
        ),
        # 15. Analogies — tier 24, level 4
        L(
            24,
            4,
            "CE2 — Les analogies 🔗",
            "A est à B ce que C est à… (trouver la relation).",
            [
                # chaton -> chat comme chiot -> chien
                mcq("Le chaton est au chat ce que le chiot est au…", ["chien", "lapin", "cheval"], 0),
                # main -> gant comme pied -> chaussure
                mcq("La main est au gant ce que le pied est à la…", ["chaussette", "chaussure", "casquette"], 1),
                # oiseau -> voler comme poisson -> nager
                mcq("L'oiseau est au vol ce que le poisson est à la…", ["marche", "nage", "course"], 1),
                # jour -> soleil comme nuit -> lune
                mcq("Le jour est au soleil ce que la nuit est à la…", ["lune", "étoile", "pluie"], 0),
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE2 Logique "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
