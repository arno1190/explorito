"""Seed CM1 Sciences — programme avancé (niveau élevé).

Idempotent par (parcours, nom de leçon). Faits établis.

Usage:
    DATABASE_URL=... uv run python scripts/seed_cm1_monde.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, reading, theme

from app.core.database import SessionLocal

LEVEL = "cm1"
SLUG = "monde"


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
        # 1. Les états de la matière et leurs changements
        L(
            10,
            4,
            "CM1 — Les états de la matière 🧊",
            "Solide, liquide, gaz et les changements d'état.",
            [
                reading(
                    "Les trois états de la matière",
                    "La matière existe sous trois états : solide (la glace), liquide (l'eau) et "
                    "gazeux (la vapeur d'eau). L'eau change d'état selon la température : elle gèle "
                    "à 0 °C et bout à 100 °C. Quand un solide devient liquide, on parle de fusion ; "
                    "quand un liquide devient gaz, c'est l'évaporation ou l'ébullition.",
                ),
                mcq(
                    "À quelle température l'eau bout-elle (au niveau de la mer) ?",
                    ["100 °C", "50 °C", "0 °C"],
                    0,
                ),
                mcq(
                    "Quand la glace fond et devient de l'eau liquide, ce changement s'appelle…",
                    ["la fusion", "la solidification", "l'évaporation"],
                    0,
                ),
                mcq(
                    "Quand un liquide se transforme en solide (l'eau qui gèle), c'est…",
                    ["la solidification", "la fusion", "la condensation"],
                    0,
                ),
            ],
        ),
        # 2. Les mélanges (solubles ou non ; séparer)
        L(
            11,
            5,
            "CM1 — Les mélanges et les séparations 🧂",
            "Ce qui se dissout ou non, et comment séparer.",
            [
                reading(
                    "Mélanges et solubilité",
                    "Certaines substances se dissolvent dans l'eau : le sel et le sucre sont "
                    "solubles. D'autres ne se dissolvent pas : le sable et l'huile sont insolubles. "
                    "Pour séparer un mélange, on peut filtrer (retenir le sable), décanter (laisser "
                    "reposer) ou faire s'évaporer l'eau pour récupérer le sel.",
                ),
                mcq(
                    "Parmi ces produits, lequel N'EST PAS soluble dans l'eau ?",
                    ["le sable", "le sel", "le sucre"],
                    0,
                ),
                mcq(
                    "L'huile versée dans l'eau…",
                    ["ne se mélange pas et flotte au-dessus", "se dissout complètement", "coule au fond et disparaît"],
                    0,
                ),
                mcq(
                    "Pour récupérer le sel dissous dans de l'eau salée, on peut…",
                    ["faire s'évaporer l'eau", "filtrer avec un papier", "ajouter du sable"],
                    0,
                ),
            ],
        ),
        # 3. Le cycle de l'eau
        L(
            12,
            4,
            "CM1 — Le cycle de l'eau 🌧️",
            "Évaporation, condensation, précipitations.",
            [
                reading(
                    "Le cycle de l'eau",
                    "Sous l'effet de la chaleur du Soleil, l'eau des mers et des rivières s'évapore "
                    "et monte dans l'air sous forme de vapeur. En altitude, la vapeur se refroidit et "
                    "se condense en fines gouttelettes qui forment les nuages. L'eau retombe ensuite "
                    "en pluie, en neige ou en grêle : ce sont les précipitations. Elle rejoint les "
                    "rivières et la mer, et le cycle recommence.",
                ),
                mcq(
                    "Le passage de la vapeur d'eau à de fines gouttelettes (les nuages) s'appelle…",
                    ["la condensation", "l'évaporation", "la fusion"],
                    0,
                ),
                mcq(
                    "Qu'est-ce qui fournit l'énergie qui fait s'évaporer l'eau ?",
                    ["le Soleil", "la Lune", "le vent froid"],
                    0,
                ),
                mcq(
                    "La pluie, la neige et la grêle sont des…",
                    ["précipitations", "évaporations", "condensations"],
                    0,
                ),
            ],
        ),
        # 4. Classer les êtres vivants
        L(
            13,
            5,
            "CM1 — Classer les êtres vivants 🦉",
            "Grandes familles : vertébrés et invertébrés.",
            [
                reading(
                    "Classer les animaux",
                    "Les scientifiques classent les êtres vivants selon leurs caractères communs. "
                    "Les animaux qui possèdent une colonne vertébrale sont des vertébrés : ils forment "
                    "cinq groupes (mammifères, oiseaux, poissons, reptiles, amphibiens). Ceux qui n'ont "
                    "pas de squelette interne sont des invertébrés, comme les insectes, les araignées "
                    "ou les vers.",
                ),
                mcq(
                    "Un animal qui possède une colonne vertébrale est un…",
                    ["vertébré", "invertébré", "végétal"],
                    0,
                ),
                mcq(
                    "Parmi ces animaux, lequel est un invertébré ?",
                    ["l'escargot", "le chat", "l'aigle"],
                    0,
                ),
                mcq(
                    "La grenouille, qui vit dans l'eau puis sur terre, appartient aux…",
                    ["amphibiens", "reptiles", "poissons"],
                    0,
                ),
            ],
        ),
        # 5. Régimes alimentaires et chaînes alimentaires
        L(
            14,
            5,
            "CM1 — Chaînes et réseaux alimentaires 🦊",
            "Qui mange qui, des plantes aux prédateurs.",
            [
                reading(
                    "La chaîne alimentaire",
                    "Une chaîne alimentaire montre qui mange qui. Elle commence toujours par un "
                    "végétal, car les plantes fabriquent leur propre nourriture. Les herbivores "
                    "mangent les plantes, puis les carnivores mangent d'autres animaux. La flèche "
                    "d'une chaîne (herbe → lapin → renard) signifie « est mangé par ».",
                ),
                mcq(
                    "Une chaîne alimentaire commence toujours par…",
                    ["un végétal", "un carnivore", "un prédateur"],
                    0,
                ),
                mcq(
                    "Dans « herbe → sauterelle → grenouille → héron », que mange la grenouille ?",
                    ["la sauterelle", "le héron", "l'herbe"],
                    0,
                ),
                mcq(
                    "Un animal qui mange à la fois des plantes et de la viande est…",
                    ["omnivore", "herbivore", "carnivore"],
                    0,
                ),
            ],
        ),
        # 6. La reproduction des animaux
        L(
            15,
            4,
            "CM1 — La reproduction des animaux 🐣",
            "Ovipares, vivipares et développement.",
            [
                reading(
                    "Comment naissent les animaux ?",
                    "Certains animaux pondent des œufs d'où sortent les petits : ce sont les ovipares, "
                    "comme la poule, la grenouille ou le poisson. D'autres donnent naissance à des "
                    "petits déjà formés : ce sont les vivipares, comme le chat, la vache ou l'être "
                    "humain. Pour qu'il y ait reproduction, il faut en général un mâle et une femelle.",
                ),
                mcq(
                    "Un animal qui pond des œufs est…",
                    ["ovipare", "vivipare", "herbivore"],
                    0,
                ),
                mcq(
                    "Parmi ces animaux, lequel est vivipare ?",
                    ["le chien", "la poule", "la grenouille"],
                    0,
                ),
                mcq(
                    "Pour se reproduire, la plupart des animaux ont besoin…",
                    ["d'un mâle et d'une femelle", "d'un seul individu toujours", "de beaucoup de soleil"],
                    0,
                ),
            ],
        ),
        # 7. Le cycle de vie des plantes
        L(
            16,
            4,
            "CM1 — Le cycle de vie des plantes 🌱",
            "De la graine à la fleur et aux graines.",
            [
                reading(
                    "Le cycle de vie d'une plante",
                    "Une plante à fleurs naît d'une graine : c'est la germination. La jeune plante "
                    "grandit, développe des racines, une tige et des feuilles. Elle produit ensuite "
                    "des fleurs qui, une fois pollinisées, donnent des fruits contenant de nouvelles "
                    "graines. Ces graines pourront germer à leur tour : le cycle recommence.",
                ),
                mcq(
                    "Le moment où la graine commence à pousser s'appelle…",
                    ["la germination", "la floraison", "la digestion"],
                    0,
                ),
                mcq(
                    "Pour germer et grandir, une graine a besoin surtout…",
                    ["d'eau, de chaleur et d'air", "d'obscurité totale et de froid", "de sel et de sable"],
                    0,
                ),
                mcq(
                    "Où trouve-t-on les nouvelles graines d'une plante à fleurs ?",
                    ["dans le fruit", "dans les racines", "dans la tige"],
                    0,
                ),
            ],
        ),
        # 8. La digestion
        L(
            17,
            5,
            "CM1 — La digestion 🍽️",
            "Le trajet des aliments dans le corps.",
            [
                reading(
                    "Le trajet des aliments",
                    "La digestion transforme les aliments en petits morceaux que le corps peut "
                    "utiliser. Les aliments entrent par la bouche, où ils sont mâchés, puis descendent "
                    "par l'œsophage jusqu'à l'estomac. Ils passent ensuite dans l'intestin, où les "
                    "nutriments passent dans le sang. Ce qui n'est pas utilisé est rejeté sous forme "
                    "de déchets.",
                ),
                mcq(
                    "Par où commence la digestion ?",
                    ["la bouche", "l'estomac", "l'intestin"],
                    0,
                ),
                mcq(
                    "Le tube qui relie la bouche à l'estomac est…",
                    ["l'œsophage", "la trachée", "l'artère"],
                    0,
                ),
                mcq(
                    "Où les nutriments passent-ils surtout dans le sang ?",
                    ["dans l'intestin", "dans la bouche", "dans les poumons"],
                    0,
                ),
            ],
        ),
        # 9. La respiration
        L(
            18,
            4,
            "CM1 — La respiration 🫁",
            "Les poumons, l'oxygène et le dioxyde de carbone.",
            [
                reading(
                    "Comment respire-t-on ?",
                    "Quand on inspire, l'air entre par le nez ou la bouche, passe par la trachée et "
                    "descend jusqu'aux poumons. Là, le corps prélève l'oxygène de l'air et le fait "
                    "passer dans le sang. Quand on expire, on rejette du dioxyde de carbone, un gaz "
                    "dont le corps n'a plus besoin.",
                ),
                mcq(
                    "Quel organe permet la respiration ?",
                    ["les poumons", "l'estomac", "le cœur"],
                    0,
                ),
                mcq(
                    "Quel gaz de l'air le corps prélève-t-il pour vivre ?",
                    ["l'oxygène", "le dioxyde de carbone", "l'hélium"],
                    0,
                ),
                mcq(
                    "Quand on expire, on rejette surtout…",
                    ["du dioxyde de carbone", "de l'oxygène pur", "de l'azote liquide"],
                    0,
                ),
            ],
        ),
        # 10. La circulation du sang
        L(
            19,
            5,
            "CM1 — La circulation du sang ❤️",
            "Le cœur, les vaisseaux et le rôle du sang.",
            [
                reading(
                    "Le cœur et le sang",
                    "Le cœur est un muscle qui bat sans arrêt : il pompe le sang et le fait circuler "
                    "dans tout le corps grâce aux vaisseaux sanguins (artères et veines). Le sang "
                    "transporte l'oxygène et les nutriments jusqu'aux organes, et emporte les déchets. "
                    "On peut sentir le cœur travailler en prenant son pouls.",
                ),
                mcq(
                    "Quel organe pompe le sang dans le corps ?",
                    ["le cœur", "le foie", "les poumons"],
                    0,
                ),
                mcq(
                    "Le sang circule dans le corps grâce…",
                    ["aux vaisseaux sanguins", "aux os", "aux nerfs"],
                    0,
                ),
                mcq(
                    "Le sang transporte notamment…",
                    ["l'oxygène et les nutriments", "de l'air pur seulement", "de la lumière"],
                    0,
                ),
            ],
        ),
        # 11. Le squelette et les muscles (le mouvement)
        L(
            20,
            4,
            "CM1 — Le mouvement : os et muscles 🦴",
            "Squelette, articulations et muscles.",
            [
                reading(
                    "Comment bouge le corps ?",
                    "Le squelette d'un adulte compte environ 200 os. Il soutient le corps et protège "
                    "les organes fragiles : le crâne protège le cerveau, les côtes protègent le cœur "
                    "et les poumons. Les os se rejoignent au niveau des articulations, comme le genou "
                    "ou le coude. Ce sont les muscles, attachés aux os, qui les tirent pour produire "
                    "le mouvement.",
                ),
                mcq(
                    "Qu'est-ce qui fait bouger les os ?",
                    ["les muscles", "les cheveux", "la peau"],
                    0,
                ),
                mcq(
                    "L'endroit où deux os se rejoignent et permettent de plier s'appelle…",
                    ["une articulation", "un muscle", "un nerf"],
                    0,
                ),
                mcq(
                    "Quels os protègent le cœur et les poumons ?",
                    ["les côtes", "le crâne", "le fémur"],
                    0,
                ),
            ],
        ),
        # 12. Les sources d'énergie
        L(
            21,
            5,
            "CM1 — Les sources d'énergie ⚡",
            "Énergies renouvelables et non renouvelables.",
            [
                reading(
                    "D'où vient l'énergie ?",
                    "Nous utilisons de l'énergie pour nous chauffer, nous déplacer et faire "
                    "fonctionner les appareils. Certaines sources sont renouvelables : le Soleil, le "
                    "vent, l'eau des rivières se reconstituent sans s'épuiser. D'autres sont non "
                    "renouvelables : le pétrole, le charbon et le gaz mettent des millions d'années à "
                    "se former et finiront par manquer. Leur combustion pollue l'air.",
                ),
                mcq(
                    "Parmi ces sources d'énergie, laquelle est renouvelable ?",
                    ["le vent", "le pétrole", "le charbon"],
                    0,
                ),
                mcq(
                    "Une source d'énergie non renouvelable est…",
                    ["le pétrole", "le Soleil", "l'eau des rivières"],
                    0,
                ),
                mcq(
                    "L'énergie du Soleil peut être captée par…",
                    ["des panneaux solaires", "des éoliennes qui brûlent du gaz", "des mines de charbon"],
                    0,
                ),
            ],
        ),
        # 13. Le système solaire
        L(
            22,
            5,
            "CM1 — Le système solaire 🪐",
            "Le Soleil, les 8 planètes et la place de la Terre.",
            [
                reading(
                    "Le système solaire",
                    "Le système solaire est formé du Soleil, une étoile, et de huit planètes qui "
                    "tournent autour de lui. En partant du Soleil, ce sont : Mercure, Vénus, la Terre, "
                    "Mars, Jupiter, Saturne, Uranus et Neptune. La Terre est la troisième planète. Le "
                    "Soleil ne tourne pas : ce sont les planètes qui tournent autour de lui.",
                ),
                mcq(
                    "Combien y a-t-il de planètes dans le système solaire ?",
                    ["8", "9", "12"],
                    0,
                ),
                mcq(
                    "La Terre est la… planète en partant du Soleil.",
                    ["troisième", "première", "cinquième"],
                    0,
                ),
                mcq(
                    "Au centre du système solaire se trouve…",
                    ["le Soleil, une étoile", "la Terre", "la Lune"],
                    0,
                ),
            ],
        ),
        # 14. Jour/nuit, saisons et phases de la Lune
        L(
            23,
            5,
            "CM1 — Jour, saisons et phases de la Lune 🌙",
            "Rotation de la Terre, orbites et Lune.",
            [
                reading(
                    "La Terre et la Lune en mouvement",
                    "La Terre tourne sur elle-même en 24 heures : c'est ce qui explique le jour et la "
                    "nuit. Elle tourne aussi autour du Soleil en un an, et son axe incliné explique les "
                    "saisons. La Lune, elle, tourne autour de la Terre. Selon sa position, on n'en voit "
                    "qu'une partie éclairée par le Soleil : ce sont les phases de la Lune (nouvelle "
                    "lune, premier quartier, pleine lune…).",
                ),
                mcq(
                    "Pourquoi y a-t-il le jour et la nuit ?",
                    [
                        "parce que la Terre tourne sur elle-même",
                        "parce que le Soleil s'éteint",
                        "parce que la Lune bouge",
                    ],
                    0,
                ),
                mcq(
                    "En combien de temps la Terre fait-elle un tour autour du Soleil ?",
                    ["un an", "24 heures", "un mois"],
                    0,
                ),
                mcq(
                    "Les phases de la Lune s'expliquent parce que la Lune…",
                    ["tourne autour de la Terre", "change de taille", "produit sa propre lumière"],
                    0,
                ),
            ],
        ),
        # 15. Protéger l'environnement
        L(
            24,
            4,
            "CM1 — Protéger l'environnement 🌍",
            "Réduire, réutiliser, recycler et économiser.",
            [
                reading(
                    "Prendre soin de la planète",
                    "Nos activités produisent des déchets et de la pollution. Pour protéger "
                    "l'environnement, on peut appliquer la règle des « 3 R » : réduire ce qu'on "
                    "consomme, réutiliser les objets et recycler les déchets en les triant. Économiser "
                    "l'eau et l'électricité, et préférer les énergies renouvelables, aident aussi à "
                    "préserver la nature et le climat.",
                ),
                mcq(
                    "Recycler un déchet, c'est…",
                    [
                        "l'utiliser pour fabriquer un nouvel objet",
                        "le brûler dans le jardin",
                        "le jeter dans la nature",
                    ],
                    0,
                ),
                mcq(
                    "Les épluchures de légumes peuvent servir à fabriquer…",
                    ["du compost", "du plastique", "du verre"],
                    0,
                ),
                mcq(
                    "Quel geste aide à protéger l'environnement ?",
                    ["économiser l'eau et l'électricité", "gaspiller la nourriture", "laisser couler le robinet"],
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CM1 Sciences "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
