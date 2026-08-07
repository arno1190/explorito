"""
Seed de leçons de compréhension de texte « Français » — univers Jules Verne.

Six leçons (CE1 et CE2, paliers 1 à 3) : chacune propose un court texte à lire
(bloc ``reading``) inspiré d'un roman de Jules Verne, suivi de questions de
compréhension en QCM (``multiple_choice``). Les réponses sont tirées du texte
fourni : elles sont donc correctes par construction.

Réutilise les constructeurs et l'insertion idempotente de ``seed_curriculum``.

Usage:
    # dev
    DATABASE_URL=postgresql://user@localhost:5432/explorito_dev \\
        uv run python scripts/seed_jules_verne.py [--dry-run]
    # prod (dans le conteneur backend)
    uv run python scripts/seed_jules_verne.py
"""

import sys
from typing import Any

# ``seed_curriculum`` est dans le même dossier ``scripts/`` (présent dans l'image).
from seed_curriculum import _seed_one, mcq, reading, theme

from app.core.database import SessionLocal

READING_INSTRUCTION = "Lis attentivement le texte, puis réponds aux questions."


def curriculum() -> list[dict[str, Any]]:
    return [
        # ------------------------------------------------------------------ CE1
        theme(
            "francais",
            "ce1",
            1,
            "Lecture — Le tour du monde en 80 jours 🎩",
            "Comprendre un court texte (univers Jules Verne).",
            45,
            [
                reading(
                    READING_INSTRUCTION,
                    "Phileas Fogg est un homme très ponctuel qui vit à Londres. "
                    "Un jour, il fait un pari fou avec ses amis : faire le tour du "
                    "monde en seulement quatre-vingts jours ! Il part aussitôt avec "
                    "son fidèle domestique, Passepartout. Ensemble, ils voyagent en "
                    "train et en bateau à travers de nombreux pays.",
                ),
                mcq("Dans quelle ville vit Phileas Fogg ?", ["Paris", "Londres", "Rome"], 1),
                mcq(
                    "Quel pari fait-il ?",
                    ["Faire le tour du monde en 80 jours", "Gagner une course à pied", "Construire un bateau"],
                    0,
                ),
                mcq("Comment s'appelle son domestique ?", ["Nemo", "Axel", "Passepartout"], 2),
                mcq("Comment voyagent-ils ?", ["En avion", "En train et en bateau", "À cheval"], 1),
            ],
        ),
        theme(
            "francais",
            "ce1",
            2,
            "Lecture — Vingt mille lieues sous les mers 🐙",
            "Comprendre un court texte (univers Jules Verne).",
            50,
            [
                reading(
                    READING_INSTRUCTION,
                    "Le professeur Aronnax explore les océans à bord d'un sous-marin "
                    "extraordinaire : le Nautilus. Ce bateau sous-marin est commandé "
                    "par le mystérieux capitaine Nemo. À travers les hublots, on peut "
                    "observer des poissons multicolores, des coraux et même des "
                    "épaves. Le Nautilus plonge très profond, là où la lumière du "
                    "soleil n'arrive plus.",
                ),
                mcq("Comment s'appelle le sous-marin ?", ["Le Nautilus", "Le Titanic", "L'Hispaniola"], 0),
                mcq("Qui commande le sous-marin ?", ["Le professeur Aronnax", "Le capitaine Nemo", "Passepartout"], 1),
                mcq(
                    "Que peut-on voir par les hublots ?",
                    ["Des étoiles", "Des dinosaures", "Des poissons et des coraux"],
                    2,
                ),
                mcq("Où plonge le Nautilus ?", ["Très profond", "Dans le ciel", "Sur la plage"], 0),
            ],
        ),
        theme(
            "francais",
            "ce1",
            3,
            "Lecture — Voyage au centre de la Terre 🌋",
            "Comprendre un court texte (univers Jules Verne).",
            55,
            [
                reading(
                    READING_INSTRUCTION,
                    "Le professeur Lidenbrock et son neveu Axel décident d'explorer "
                    "l'intérieur de la Terre. Ils descendent par le cratère d'un "
                    "volcan éteint, en Islande. Sous la terre, ils découvrent une "
                    "immense grotte, une mer souterraine et d'étranges créatures. Le "
                    "voyage est dangereux, mais les deux explorateurs sont très "
                    "courageux.",
                ),
                mcq(
                    "Qui accompagne le professeur Lidenbrock ?",
                    ["Le capitaine Nemo", "Son neveu Axel", "Phileas Fogg"],
                    1,
                ),
                mcq(
                    "Par où descendent-ils sous la Terre ?",
                    ["Le cratère d'un volcan", "Un puits de mine", "Une grotte au bord de la mer"],
                    0,
                ),
                mcq(
                    "Que découvrent-ils sous la terre ?",
                    ["Un désert de sable", "Une ville moderne", "Une mer souterraine"],
                    2,
                ),
                mcq("Comment sont les deux explorateurs ?", ["Peureux", "Courageux", "Paresseux"], 1),
            ],
        ),
        # ------------------------------------------------------------------ CE2
        theme(
            "francais",
            "ce2",
            1,
            "Lecture — Cinq semaines en ballon 🎈",
            "Comprendre un texte plus long (univers Jules Verne).",
            50,
            [
                reading(
                    READING_INSTRUCTION,
                    "Le docteur Samuel Fergusson est un explorateur passionné. Il a "
                    "une idée audacieuse : traverser l'Afrique à bord d'un ballon "
                    "rempli de gaz. Grâce au vent, son ballon survole des forêts, des "
                    "fleuves immenses et des troupeaux d'animaux sauvages. De là-haut, "
                    "il dessine des cartes des régions encore inconnues. Son voyage "
                    "dure cinq semaines.",
                ),
                mcq(
                    "Quel continent le docteur Fergusson veut-il traverser ?", ["L'Afrique", "L'Amérique", "L'Asie"], 0
                ),
                mcq("Avec quel moyen de transport voyage-t-il ?", ["Un sous-marin", "Un ballon", "Un train"], 1),
                mcq(
                    "Que fait-il depuis le ciel ?",
                    ["Il pêche des poissons", "Il plante des arbres", "Il dessine des cartes"],
                    2,
                ),
                mcq("Combien de temps dure son voyage ?", ["Cinq jours", "Cinq semaines", "Cinq ans"], 1),
            ],
        ),
        theme(
            "francais",
            "ce2",
            2,
            "Lecture — De la Terre à la Lune 🚀",
            "Comprendre un texte plus long (univers Jules Verne).",
            55,
            [
                reading(
                    READING_INSTRUCTION,
                    "Après une grande guerre, les membres du Gun-Club s'ennuient. Leur "
                    "président propose alors un projet incroyable : envoyer un obus "
                    "jusqu'à la Lune ! Pour cela, ils construisent un canon géant, "
                    "long de plusieurs centaines de mètres. Trois hommes courageux "
                    "acceptent de monter à l'intérieur de l'obus pour tenter le voyage "
                    "vers l'espace.",
                ),
                mcq(
                    "Quel projet propose le président du Gun-Club ?",
                    ["Envoyer un obus vers la Lune", "Construire un pont", "Creuser un tunnel"],
                    0,
                ),
                mcq(
                    "Que construisent-ils pour réaliser ce projet ?",
                    ["Une fusée moderne", "Un canon géant", "Un ballon"],
                    1,
                ),
                mcq("Combien d'hommes montent dans l'obus ?", ["Un", "Dix", "Trois"], 2),
                mcq(
                    "Vers où veulent-ils voyager ?",
                    ["Vers l'espace, la Lune", "Vers le fond des mers", "Vers le centre de la Terre"],
                    0,
                ),
            ],
        ),
        theme(
            "francais",
            "ce2",
            3,
            "Lecture — L'Île mystérieuse 🏝️",
            "Comprendre un texte plus long et déduire (univers Jules Verne).",
            60,
            [
                reading(
                    READING_INSTRUCTION,
                    "Emportés par une tempête à bord d'un ballon, cinq naufragés "
                    "atterrissent sur une île déserte au milieu de l'océan Pacifique. "
                    "Pour survivre, ils doivent se montrer astucieux : ils fabriquent "
                    "des outils, cultivent la terre et construisent un abri. "
                    "L'ingénieur Cyrus Smith, plein d'idées, dirige le petit groupe. "
                    "Mais l'île cache un mystère : quelqu'un semble les aider en "
                    "secret…",
                ),
                mcq("Comment les naufragés arrivent-ils sur l'île ?", ["En ballon", "En sous-marin", "À la nage"], 0),
                mcq(
                    "Sur quel océan se trouve l'île ?",
                    ["L'océan Atlantique", "L'océan Pacifique", "La mer Méditerranée"],
                    1,
                ),
                mcq(
                    "Que font-ils pour survivre ?",
                    [
                        "Ils attendent sans rien faire",
                        "Ils repartent aussitôt",
                        "Ils fabriquent des outils et cultivent la terre",
                    ],
                    2,
                ),
                mcq(
                    "Qui dirige le petit groupe ?", ["Le capitaine Nemo", "L'ingénieur Cyrus Smith", "Phileas Fogg"], 1
                ),
                mcq(
                    "Quel est le mystère de l'île ?",
                    ["Quelqu'un les aide en secret", "Il n'y a pas d'eau", "Elle est en feu"],
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
            if status.startswith("+"):
                created += 1
            elif status.startswith("="):
                skipped += 1
        total_ex = sum(len(t["exercises"]) for t in themes)
        print(
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons Jules Verne "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
