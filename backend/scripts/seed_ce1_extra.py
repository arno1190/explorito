"""
Seed complémentaire CE1 : lecture-compréhension, langue/orthographe et
questionner-le-monde. Contenu rédigé (faits simples, grand public) ; les
réponses de compréhension sont tirées des textes fournis (correctes par
construction). Complète la progression maths (seed_ce1_maths.py).

Idempotent par (parcours, nom de leçon).

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce1_extra.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, reading, theme

from app.core.database import SessionLocal

LEVEL = "ce1"
LIRE = "Lis le texte, puis réponds aux questions."


def _read_lesson(slug, tier, name, desc, xp, text, qcm):
    return theme("francais", LEVEL, tier, name, desc, xp, [reading(LIRE, text), *qcm])


def curriculum() -> list[dict[str, Any]]:
    themes: list[dict[str, Any]] = []

    # ------------------------------------------------------ Français : lecture
    themes.append(
        _read_lesson(
            "francais",
            4,
            "Lecture — La ferme 🐄",
            "Comprendre un court texte.",
            45,
            "À la ferme, le fermier se lève très tôt. Il donne du foin aux vaches et "
            "du grain aux poules. Les poules pondent des œufs dans le poulailler. "
            "Le chien garde le troupeau de moutons dans le pré.",
            [
                mcq("Que donne le fermier aux vaches ?", ["Du foin", "Du grain", "Des œufs"], 0),
                mcq("Où les poules pondent-elles ?", ["Dans le pré", "Dans le poulailler", "Dans la mare"], 1),
                mcq("Qui garde les moutons ?", ["Le chat", "Le chien", "Le fermier"], 1),
            ],
        )
    )
    themes.append(
        _read_lesson(
            "francais",
            4,
            "Lecture — La mer 🌊",
            "Comprendre un court texte.",
            45,
            "Sur la plage, les enfants construisent un château de sable. Les vagues "
            "arrivent et repartent. On voit des mouettes voler dans le ciel et des "
            "coquillages sur le sable. Papa nage dans l'eau salée.",
            [
                mcq("Que construisent les enfants ?", ["Un bateau", "Un château de sable", "Une cabane"], 1),
                mcq("Quels oiseaux volent dans le ciel ?", ["Des mouettes", "Des pigeons", "Des aigles"], 0),
                mcq("Comment est l'eau de la mer ?", ["Sucrée", "Salée", "Chaude"], 1),
            ],
        )
    )
    themes.append(
        _read_lesson(
            "francais",
            5,
            "Lecture — L'automne 🍂",
            "Comprendre un court texte.",
            50,
            "En automne, les feuilles des arbres deviennent jaunes, oranges et "
            "rouges, puis elles tombent. Les écureuils font des réserves de noisettes "
            "pour l'hiver. Le vent souffle et il pleut souvent.",
            [
                mcq(
                    "De quelle couleur deviennent les feuilles ?", ["Vertes", "Jaunes, oranges et rouges", "Bleues"], 1
                ),
                mcq("Que font les écureuils ?", ["Ils dorment", "Ils font des réserves de noisettes", "Ils volent"], 1),
                mcq("Quel temps fait-il souvent en automne ?", ["Il neige", "Il pleut", "Il fait très chaud"], 1),
            ],
        )
    )
    themes.append(
        _read_lesson(
            "francais",
            5,
            "Lecture — L'anniversaire 🎂",
            "Comprendre un court texte.",
            50,
            "Aujourd'hui, c'est l'anniversaire de Lucie. Elle a sept ans. Ses amis "
            "sont venus avec des cadeaux. Maman a préparé un gâteau au chocolat avec "
            "sept bougies. Lucie souffle les bougies et fait un vœu.",
            [
                mcq("Quel âge a Lucie ?", ["Six ans", "Sept ans", "Huit ans"], 1),
                mcq("Quel gâteau a préparé maman ?", ["Un gâteau au chocolat", "Une tarte", "Des crêpes"], 0),
                mcq("Que fait Lucie en soufflant les bougies ?", ["Un vœu", "Un dessin", "Une sieste"], 0),
            ],
        )
    )
    themes.append(
        _read_lesson(
            "francais",
            6,
            "Lecture — Le jardin 🌻",
            "Comprendre un court texte.",
            55,
            "Papi plante des graines dans son jardin. Il les arrose tous les jours. "
            "Avec le soleil et l'eau, les graines deviennent des plantes. Bientôt, il "
            "y aura des tomates rouges et de grands tournesols jaunes.",
            [
                mcq("Que plante Papi ?", ["Des graines", "Des cailloux", "Des jouets"], 0),
                mcq(
                    "De quoi les graines ont-elles besoin pour pousser ?",
                    ["De soleil et d'eau", "De neige", "De bruit"],
                    0,
                ),
                mcq("Quelle fleur va pousser ?", ["Des roses", "Des tournesols", "Des tulipes"], 1),
            ],
        )
    )
    themes.append(
        _read_lesson(
            "francais",
            6,
            "Lecture — Les pompiers 🚒",
            "Comprendre un court texte.",
            55,
            "Les pompiers travaillent dans une caserne. Quand il y a un incendie, "
            "l'alarme sonne. Ils montent vite dans le grand camion rouge et foncent, "
            "sirène allumée. Avec leur lance à eau, ils éteignent le feu.",
            [
                mcq("Où travaillent les pompiers ?", ["Dans une caserne", "Dans une école", "Dans un magasin"], 0),
                mcq("De quelle couleur est leur camion ?", ["Bleu", "Rouge", "Vert"], 1),
                mcq("Avec quoi éteignent-ils le feu ?", ["Une lance à eau", "Un balai", "Du sable"], 0),
            ],
        )
    )
    themes.append(
        _read_lesson(
            "francais",
            7,
            "Lecture — Les trois petits cochons 🐷",
            "Comprendre un conte.",
            55,
            "Trois petits cochons construisent chacun une maison : une en paille, une "
            "en bois et une en briques. Le loup souffle et détruit la maison de paille "
            "et celle de bois. Mais il ne réussit pas à détruire la maison de briques, "
            "la plus solide. Les trois cochons y sont sauvés.",
            [
                mcq("Combien y a-t-il de petits cochons ?", ["Deux", "Trois", "Quatre"], 1),
                mcq(
                    "Quelle maison résiste au loup ?",
                    ["La maison de paille", "La maison de bois", "La maison de briques"],
                    2,
                ),
                mcq(
                    "Pourquoi cette maison résiste-t-elle ?",
                    ["Elle est la plus solide", "Elle est jolie", "Elle est petite"],
                    0,
                ),
            ],
        )
    )
    themes.append(
        _read_lesson(
            "francais",
            7,
            "Lecture — La petite poule rousse 🐔",
            "Comprendre un conte.",
            55,
            "La petite poule rousse trouve des grains de blé. Elle demande de l'aide "
            "pour les planter, mais le chat, le chien et le canard refusent. Elle fait "
            "tout toute seule et prépare du bon pain. Quand le pain est prêt, tous "
            "veulent en manger, mais la poule le partage seulement avec ses poussins.",
            [
                mcq("Que trouve la petite poule ?", ["Des grains de blé", "Un trésor", "Un œuf"], 0),
                mcq("Qui l'aide à planter le blé ?", ["Le chat", "Personne", "Le canard"], 1),
                mcq("Avec qui partage-t-elle le pain ?", ["Ses poussins", "Le chien", "Tout le monde"], 0),
            ],
        )
    )

    # ------------------------------------------------------ Français : langue
    themes.append(
        theme(
            "francais",
            LEVEL,
            8,
            "Le son [ch] 🐑",
            "Écrire des mots avec le son [ch].",
            45,
            [
                fill_blanks("Complète : le mouton dit…", "Le mouton porte de la laine : c'est un ___", ["mouton"]),
                fill_blanks("Complète le mot : un ___val (l'animal).", "un ___eval", ["ch"]),
                fill_blanks("Complète le mot : un ___apeau sur la tête.", "un ___apeau", ["ch"]),
                mcq("Quel mot contient le son [ch] ?", ["chat", "table", "lune"], 0),
            ],
        )
    )
    themes.append(
        theme(
            "francais",
            LEVEL,
            8,
            "Les majuscules 🔠",
            "Savoir quand mettre une majuscule.",
            45,
            [
                mcq(
                    "Où met-on une majuscule ?",
                    ["Au début d'une phrase", "Au milieu d'un mot", "À la fin d'une phrase"],
                    0,
                ),
                mcq("Quel mot prend toujours une majuscule ?", ["chat", "Paris", "table"], 1),
                mcq("Quelle phrase est bien écrite ?", ["le chien court.", "Le chien court.", "le Chien court."], 1),
                mcq(
                    "Après un point, le mot suivant commence par…", ["une minuscule", "une majuscule", "un chiffre"], 1
                ),
            ],
        )
    )

    # ------------------------------------------------------ Orthographe
    themes.append(
        theme(
            "orthographe",
            LEVEL,
            3,
            "Le pluriel des noms 🐈",
            "Mettre les noms au pluriel.",
            45,
            [
                fill_blanks("Un chat → deux…", "deux ___", ["chats"]),
                fill_blanks("Une fleur → des…", "des ___", ["fleurs"]),
                fill_blanks("Un ami → des…", "des ___", ["amis"]),
                mcq("Quel est le pluriel de « livre » ?", ["livre", "livres", "livrs"], 1),
            ],
        )
    )
    themes.append(
        theme(
            "orthographe",
            LEVEL,
            4,
            "a ou à",
            "Distinguer « a » et « à ».",
            50,
            [
                mcq("Il ___ un vélo.", ["a", "à"], 0),
                mcq("Je vais ___ la piscine.", ["a", "à"], 1),
                mcq("Elle ___ faim.", ["a", "à"], 0),
                mcq("On joue ___ cache-cache.", ["a", "à"], 1),
            ],
        )
    )
    themes.append(
        theme(
            "orthographe",
            LEVEL,
            4,
            "et ou est",
            "Distinguer « et » et « est ».",
            50,
            [
                mcq("Papa ___ maman.", ["et", "est"], 0),
                mcq("Le ciel ___ bleu.", ["et", "est"], 1),
                mcq("Un chien ___ un chat.", ["et", "est"], 0),
                mcq("Le chat ___ noir.", ["et", "est"], 1),
            ],
        )
    )
    themes.append(
        theme(
            "orthographe",
            LEVEL,
            5,
            "on ou ont",
            "Distinguer « on » et « ont ».",
            50,
            [
                mcq("___ joue dans la cour.", ["On", "Ont"], 0),
                mcq("Les enfants ___ des jouets.", ["on", "ont"], 1),
                mcq("___ mange à midi.", ["On", "Ont"], 0),
                mcq("Ils ___ un chien.", ["on", "ont"], 1),
            ],
        )
    )
    themes.append(
        theme(
            "orthographe",
            LEVEL,
            5,
            "son ou sont",
            "Distinguer « son » et « sont ».",
            55,
            [
                mcq("___ vélo est rouge.", ["Son", "Sont"], 0),
                mcq("Les fleurs ___ belles.", ["son", "sont"], 1),
                mcq("Il joue avec ___ ballon.", ["son", "sont"], 0),
                mcq("Ils ___ contents.", ["son", "sont"], 1),
            ],
        )
    )
    themes.append(
        theme(
            "orthographe",
            LEVEL,
            6,
            "m devant m, b, p",
            "Écrire « m » devant m, b, p.",
            55,
            [
                fill_blanks("Devant b : un ti___bre.", "un ti___bre", ["m"]),
                fill_blanks("Devant p : une la___pe.", "une la___pe", ["m"]),
                mcq("Quel mot est bien écrit ?", ["un tanbour", "un tambour", "un tambur"], 1),
                mcq("Devant « m », « b » et « p », on écrit…", ["n", "m", "rien"], 1),
            ],
        )
    )

    # ------------------------------------------------ Questionner le monde
    themes.append(
        theme(
            "monde",
            LEVEL,
            2,
            "Le vivant et le non-vivant 🌱",
            "Distinguer le vivant du non-vivant.",
            45,
            [
                mcq("Lequel est vivant ?", ["Un caillou", "Un arbre", "Une table"], 1),
                mcq("Lequel n'est pas vivant ?", ["Un chat", "Une voiture", "Une fleur"], 1),
                mcq(
                    "Un être vivant peut…",
                    ["grandir et se nourrir", "rester toujours pareil", "être fabriqué en usine"],
                    0,
                ),
                mcq("Lequel est vivant ?", ["Le vent", "Un poisson", "Un ballon"], 1),
            ],
        )
    )
    themes.append(
        theme(
            "monde",
            LEVEL,
            3,
            "Les cinq sens 👀",
            "Découvrir les cinq sens.",
            45,
            [
                mcq("Avec quoi voit-on ?", ["Les yeux", "Le nez", "Les oreilles"], 0),
                mcq("Avec quoi entend-on ?", ["Les mains", "Les oreilles", "La langue"], 1),
                mcq("Avec quoi sent-on les odeurs ?", ["Le nez", "Les yeux", "Les pieds"], 0),
                mcq("Avec la langue, on utilise le sens du…", ["goût", "toucher", "vue"], 0),
            ],
        )
    )
    themes.append(
        theme(
            "monde",
            LEVEL,
            4,
            "Les animaux 🦁",
            "Classer les animaux.",
            50,
            [
                mcq("Lequel est un oiseau ?", ["Le chat", "La poule", "Le poisson"], 1),
                mcq("Où vit le poisson ?", ["Dans l'eau", "Dans les arbres", "Sous la terre"], 0),
                mcq("Lequel vole ?", ["Le lapin", "L'oiseau", "La vache"], 1),
                mcq("La vache est un…", ["oiseau", "mammifère", "poisson"], 1),
            ],
        )
    )
    themes.append(
        theme(
            "monde",
            LEVEL,
            5,
            "Les plantes 🌻",
            "Connaître les parties d'une plante.",
            50,
            [
                mcq("Quelle partie est sous la terre ?", ["La fleur", "Les racines", "Les feuilles"], 1),
                mcq(
                    "De quoi la plante a-t-elle besoin pour pousser ?",
                    ["De l'eau et du soleil", "Du bruit", "Du froid"],
                    0,
                ),
                mcq("La partie colorée qui attire les abeilles est…", ["la racine", "la fleur", "la tige"], 1),
                mcq("Les feuilles sont souvent de couleur…", ["verte", "bleue", "noire"], 0),
            ],
        )
    )
    themes.append(
        theme(
            "monde",
            LEVEL,
            5,
            "Le jour et la nuit 🌙",
            "Comprendre le jour et la nuit.",
            50,
            [
                mcq("Le jour, on voit…", ["le Soleil", "la Lune et les étoiles", "rien"], 0),
                mcq("La nuit, dans le ciel, on voit…", ["le Soleil", "la Lune et les étoiles", "un arc-en-ciel"], 1),
                mcq("Quand se couche-t-on pour dormir ?", ["Le jour", "La nuit", "À midi"], 1),
                mcq("Le matin, le Soleil se…", ["lève", "couche", "cache pour toujours"], 0),
            ],
        )
    )
    themes.append(
        theme(
            "monde",
            LEVEL,
            6,
            "Les saisons 🍂",
            "Connaître les quatre saisons.",
            55,
            [
                mcq("Combien y a-t-il de saisons ?", ["Deux", "Quatre", "Six"], 1),
                mcq("En quelle saison neige-t-il souvent ?", ["L'été", "L'hiver", "Le printemps"], 1),
                mcq("En quelle saison les fleurs poussent-elles ?", ["Le printemps", "L'hiver", "L'automne"], 0),
                mcq("Quelle saison est la plus chaude ?", ["L'automne", "L'été", "L'hiver"], 1),
            ],
        )
    )
    themes.append(
        theme(
            "monde",
            LEVEL,
            6,
            "L'eau 💧",
            "Découvrir l'eau et ses états.",
            55,
            [
                mcq("Quand l'eau gèle, elle devient…", ["de la glace", "de la vapeur", "du sable"], 0),
                mcq("Que boit-on pour vivre ?", ["De l'eau", "Du sable", "De l'air"], 0),
                mcq("L'eau très chaude se transforme en…", ["glace", "vapeur", "pierre"], 1),
                mcq("La pluie tombe depuis…", ["les nuages", "le sol", "les arbres"], 0),
            ],
        )
    )
    themes.append(
        theme(
            "monde",
            LEVEL,
            2,
            "L'hygiène 🪥",
            "Prendre soin de soi.",
            45,
            [
                mcq(
                    "Combien de fois par jour se brosse-t-on les dents ?",
                    ["Jamais", "Deux fois", "Une fois par mois"],
                    1,
                ),
                mcq("Quand faut-il se laver les mains ?", ["Avant de manger", "Jamais", "Une fois par an"], 0),
                mcq("Avec quoi se lave-t-on les mains ?", ["De l'eau et du savon", "Du sable", "De la peinture"], 0),
                mcq("Pour être en forme, il faut aussi…", ["bien dormir", "veiller très tard", "ne jamais bouger"], 0),
            ],
        )
    )

    # ------------------------------------------------------- Géo & Histoire
    themes.append(
        theme(
            "geo",
            LEVEL,
            2,
            "La France 🇫🇷",
            "Découvrir la France.",
            45,
            [
                mcq("Quelle est la capitale de la France ?", ["Lyon", "Paris", "Nice"], 1),
                mcq(
                    "Quel monument célèbre est à Paris ?", ["La tour Eiffel", "La Grande Muraille", "Les pyramides"], 0
                ),
                mcq(
                    "De quelles couleurs est le drapeau français ?",
                    ["Bleu, blanc, rouge", "Vert, blanc, rouge", "Bleu, jaune, rouge"],
                    0,
                ),
                mcq("La France est un…", ["pays", "océan", "animal"], 0),
            ],
        )
    )
    themes.append(
        theme(
            "histoire",
            LEVEL,
            2,
            "Hier, aujourd'hui, demain ⏳",
            "Se repérer dans le temps.",
            45,
            [
                mcq("Le jour qui vient après aujourd'hui s'appelle…", ["hier", "demain", "avant"], 1),
                mcq("Le jour qui était avant aujourd'hui s'appelle…", ["hier", "demain", "bientôt"], 0),
                mcq("Combien de jours dans une semaine ?", ["Cinq", "Sept", "Dix"], 1),
                mcq("Quel est le premier repas de la journée ?", ["Le dîner", "Le petit-déjeuner", "Le goûter"], 1),
            ],
        )
    )

    return themes


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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE1 (extra) "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
