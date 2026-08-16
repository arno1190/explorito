"""Seed CE2 Questionner le monde — couverture du programme (leçons avancées).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce2_monde.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, reading, theme

from app.core.database import SessionLocal

LEVEL = "ce2"
SLUG = "monde"


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
        # 1. Le vivant et le non-vivant
        L(
            10,
            3,
            "CE2 — Le vivant et le non-vivant 🌱",
            "Distinguer ce qui est vivant de ce qui ne l'est pas.",
            [
                reading(
                    "Vivant ou non-vivant ?",
                    "Un être vivant naît, grandit, se nourrit, se reproduit puis meurt. "
                    "Une plante, un animal ou un champignon sont vivants. Un caillou, "
                    "l'eau ou une voiture ne sont pas vivants.",
                ),
                mcq("Parmi ces éléments, lequel est vivant ?", ["Un rocher", "Un arbre", "Une voiture"], 1),
                mcq(
                    "Qu'est-ce que tous les êtres vivants font ?",
                    [
                        "Ils grandissent et se reproduisent",
                        "Ils restent toujours identiques",
                        "Ils sont fabriqués en usine",
                    ],
                    0,
                ),
                mcq("Lequel n'est PAS vivant ?", ["Un champignon", "Un caillou", "Une fleur"], 1),
            ],
        ),
        # 2. Classer les animaux
        L(
            11,
            3,
            "CE2 — Classer les animaux 🦉",
            "Reconnaître mammifères, oiseaux, poissons et insectes.",
            [
                mcq("Le chat est un…", ["mammifère", "oiseau", "poisson"], 0),
                mcq("Quel animal est un oiseau ?", ["la chauve-souris", "l'aigle", "le dauphin"], 1),
                mcq("Combien de pattes a un insecte ?", ["6", "8", "4"], 0),
                mcq("Le saumon est un…", ["poisson", "reptile", "mammifère"], 0),
            ],
        ),
        # 3. Les régimes alimentaires
        L(
            12,
            3,
            "CE2 — Les régimes alimentaires 🍽️",
            "Herbivore, carnivore ou omnivore.",
            [
                mcq(
                    "Un animal qui mange seulement des plantes est…",
                    ["herbivore", "carnivore", "omnivore"],
                    0,
                ),
                mcq("Le lion mange de la viande, il est donc…", ["carnivore", "herbivore", "omnivore"], 0),
                mcq(
                    "Un animal omnivore mange…",
                    ["des plantes et de la viande", "seulement des plantes", "seulement de la viande"],
                    0,
                ),
                mcq("La vache mange de l'herbe, elle est…", ["herbivore", "carnivore", "omnivore"], 0),
            ],
        ),
        # 4. La chaîne alimentaire
        L(
            13,
            4,
            "CE2 — La chaîne alimentaire 🦊",
            "Comprendre qui mange qui dans la nature.",
            [
                reading(
                    "La chaîne alimentaire",
                    "Dans une chaîne alimentaire, chaque être vivant sert de nourriture à un autre. "
                    "Elle commence toujours par une plante. Par exemple : l'herbe est mangée par la "
                    "sauterelle, la sauterelle est mangée par la grenouille, et la grenouille est "
                    "mangée par le héron.",
                ),
                mcq("Une chaîne alimentaire commence toujours par…", ["une plante", "un carnivore", "un rocher"], 0),
                mcq("Dans « herbe → lapin → renard », qui mange le lapin ?", ["le renard", "l'herbe", "personne"], 0),
                mcq(
                    "Un « prédateur » est un animal qui…",
                    ["chasse et mange d'autres animaux", "mange seulement de l'herbe", "se fait toujours manger"],
                    0,
                ),
            ],
        ),
        # 5. Le squelette et les muscles
        L(
            14,
            4,
            "CE2 — Le squelette et les muscles 🦴",
            "Comment le corps tient debout et bouge.",
            [
                mcq(
                    "À quoi sert le squelette ?",
                    ["à soutenir le corps et protéger les organes", "à digérer les aliments", "à respirer"],
                    0,
                ),
                mcq(
                    "Combien d'os compte environ le squelette d'un adulte ?",
                    ["environ 200", "environ 20", "environ 2000"],
                    0,
                ),
                mcq("Qu'est-ce qui permet de faire bouger les os ?", ["les muscles", "les cheveux", "la peau"], 0),
                mcq("Quel os protège le cerveau ?", ["le crâne", "le fémur (la jambe)", "les côtes"], 0),
            ],
        ),
        # 6. Les dents et l'hygiène bucco-dentaire
        L(
            15,
            3,
            "CE2 — Les dents et l'hygiène 🦷",
            "Prendre soin de ses dents.",
            [
                mcq(
                    "Combien de fois par jour faut-il se brosser les dents ?",
                    ["au moins 2 fois", "jamais", "une fois par semaine"],
                    0,
                ),
                mcq(
                    "Les dents pointues qui servent à déchirer sont…",
                    ["les canines", "les molaires", "les incisives"],
                    0,
                ),
                mcq("Qu'est-ce qui abîme les dents et provoque les caries ?", ["le sucre", "l'eau", "les légumes"], 0),
                mcq(
                    "Les dents de lait sont ensuite remplacées par…",
                    ["les dents définitives", "rien du tout", "des dents en plastique"],
                    0,
                ),
            ],
        ),
        # 7. La respiration
        L(
            16,
            4,
            "CE2 — La respiration 🫁",
            "Comprendre comment le corps respire.",
            [
                reading(
                    "Comment respire-t-on ?",
                    "Quand on inspire, l'air entre par le nez ou la bouche et descend jusqu'aux poumons. "
                    "Le corps prend alors l'oxygène contenu dans l'air. Quand on expire, on rejette du "
                    "dioxyde de carbone.",
                ),
                mcq("Quel organe permet de respirer ?", ["les poumons", "l'estomac", "le foie"], 0),
                mcq(
                    "Quel gaz de l'air notre corps utilise-t-il pour vivre ?", ["l'oxygène", "l'hélium", "la fumée"], 0
                ),
                mcq(
                    "Quand on expire (souffle), on rejette surtout…",
                    ["du dioxyde de carbone", "de l'oxygène pur", "de l'eau"],
                    0,
                ),
            ],
        ),
        # 8. Les cinq sens
        L(
            17,
            3,
            "CE2 — Les cinq sens 👀",
            "La vue, l'ouïe, le goût, l'odorat et le toucher.",
            [
                mcq("Avec quel organe voit-on ?", ["les yeux", "les oreilles", "le nez"], 0),
                mcq("On perçoit le goût grâce à…", ["la langue", "la peau", "les yeux"], 0),
                mcq("On entend grâce…", ["aux oreilles", "au nez", "aux mains"], 0),
                mcq("Le toucher se fait surtout grâce à…", ["la peau", "la langue", "les oreilles"], 0),
            ],
        ),
        # 9. Les états de l'eau
        L(
            18,
            3,
            "CE2 — Les états de l'eau 💧",
            "Solide, liquide et gazeux.",
            [
                mcq("La glace est de l'eau à l'état…", ["solide", "liquide", "gazeux"], 0),
                mcq("La vapeur d'eau est de l'eau à l'état…", ["gazeux", "solide", "liquide"], 0),
                mcq("À quelle température l'eau gèle-t-elle ?", ["0 °C", "100 °C", "50 °C"], 0),
                mcq("Quand la glace fond, elle devient…", ["liquide", "gazeuse", "encore plus solide"], 0),
            ],
        ),
        # 10. Le cycle de l'eau
        L(
            19,
            4,
            "CE2 — Le cycle de l'eau 🌧️",
            "Le voyage de l'eau dans la nature.",
            [
                reading(
                    "Le cycle de l'eau",
                    "Sous l'effet du soleil, l'eau des mers et des rivières s'évapore et monte dans le ciel. "
                    "Là-haut, la vapeur se refroidit et forme les nuages. L'eau retombe ensuite en pluie ou "
                    "en neige, puis rejoint les rivières et la mer. C'est le cycle de l'eau.",
                ),
                mcq("Qu'est-ce qui fait s'évaporer l'eau ?", ["la chaleur du soleil", "la lune", "le vent froid"], 0),
                mcq("Les nuages sont formés de…", ["gouttelettes d'eau", "de fumée", "de coton"], 0),
                mcq(
                    "Quand la vapeur d'eau se refroidit, elle…",
                    ["se transforme en gouttes (elle se condense)", "disparaît pour toujours", "devient du sable"],
                    0,
                ),
            ],
        ),
        # 11. Les mélanges
        L(
            20,
            4,
            "CE2 — Les mélanges avec l'eau 🧂",
            "Ce qui se dissout ou non dans l'eau.",
            [
                mcq(
                    "Que se passe-t-il quand on met du sel dans l'eau et qu'on remue ?",
                    ["il se dissout (on ne le voit plus)", "il flotte à la surface", "il devient rouge"],
                    0,
                ),
                mcq("Lequel NE se dissout PAS dans l'eau ?", ["le sable", "le sucre", "le sel"], 0),
                mcq("Un produit qui se dissout dans l'eau est dit…", ["soluble", "insoluble", "liquide"], 0),
                mcq(
                    "Comment séparer le sable de l'eau ?",
                    ["en filtrant le mélange", "en le buvant", "c'est impossible"],
                    0,
                ),
            ],
        ),
        # 12. L'air
        L(
            21,
            3,
            "CE2 — L'air qui nous entoure 🎐",
            "L'air existe, il pèse, et il peut se déplacer.",
            [
                mcq("L'air…", ["existe partout autour de nous", "n'existe pas vraiment", "se voit très facilement"], 0),
                mcq("Le vent, c'est…", ["de l'air qui se déplace", "de l'eau qui coule", "de la lumière"], 0),
                mcq(
                    "Comment peut-on montrer que l'air existe ?",
                    ["en gonflant un ballon", "en le mangeant", "on ne peut pas"],
                    0,
                ),
                mcq("L'air…", ["a un poids (il pèse un peu)", "ne pèse rien du tout", "est plus lourd que l'eau"], 0),
            ],
        ),
        # 13. Les matériaux et les objets techniques
        L(
            22,
            4,
            "CE2 — Les matériaux et les objets 🔧",
            "D'où viennent les matériaux et leurs propriétés.",
            [
                mcq("Le verre est fabriqué surtout à partir de…", ["sable", "bois", "plastique"], 0),
                mcq("Parmi ces matériaux, lequel est transparent ?", ["le verre", "le bois", "le métal"], 0),
                mcq("Le papier est fabriqué à partir de…", ["bois", "pierre", "verre"], 0),
                mcq("Quel matériau conduit bien l'électricité ?", ["le métal", "le plastique", "le bois"], 0),
            ],
        ),
        # 14. Protéger l'environnement (le tri des déchets)
        L(
            23,
            3,
            "CE2 — Protéger l'environnement 🗑️",
            "Trier ses déchets et respecter la planète.",
            [
                mcq(
                    "Recycler, c'est…",
                    [
                        "réutiliser les déchets pour fabriquer de nouveaux objets",
                        "tout jeter à la poubelle",
                        "brûler les jardins",
                    ],
                    0,
                ),
                mcq(
                    "Où jette-t-on une bouteille en plastique vide ?",
                    ["dans le bac de tri", "par terre", "dans l'évier"],
                    0,
                ),
                mcq("Les épluchures de légumes peuvent servir à faire…", ["du compost", "du verre", "du métal"], 0),
                mcq(
                    "Pour protéger la planète, il vaut mieux…",
                    ["économiser l'eau et l'électricité", "gaspiller l'eau", "laisser toutes les lumières allumées"],
                    0,
                ),
            ],
        ),
        # 15. Le jour et la nuit
        L(
            24,
            4,
            "CE2 — Le jour et la nuit 🌍",
            "La Terre tourne sur elle-même.",
            [
                reading(
                    "Pourquoi le jour et la nuit ?",
                    "La Terre tourne sur elle-même en 24 heures. Le côté de la Terre tourné vers le Soleil "
                    "est éclairé : c'est le jour. Le côté opposé est dans l'ombre : c'est la nuit. Ce n'est "
                    "pas le Soleil qui tourne autour de la Terre.",
                ),
                mcq(
                    "Pourquoi y a-t-il le jour et la nuit ?",
                    [
                        "parce que la Terre tourne sur elle-même",
                        "parce que le Soleil s'éteint",
                        "parce que la Lune s'en va",
                    ],
                    0,
                ),
                mcq(
                    "En combien de temps la Terre fait-elle un tour sur elle-même ?",
                    ["24 heures", "1 heure", "un an"],
                    0,
                ),
                mcq(
                    "C'est le jour quand notre côté de la Terre est…",
                    ["tourné vers le Soleil", "dans l'ombre", "couvert de nuages"],
                    0,
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE2 Monde "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
