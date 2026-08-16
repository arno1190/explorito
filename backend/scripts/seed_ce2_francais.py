"""Seed CE2 Français — couverture du programme (leçons avancées).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce2_francais.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, reading, theme

from app.core.database import SessionLocal

LEVEL = "ce2"
SLUG = "francais"


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
        # 1. Le nom : commun et propre
        L(
            10,
            3,
            "CE2 — Nom commun et nom propre 🏷️",
            "Distinguer le nom commun du nom propre.",
            [
                mcq("Quel mot est un nom propre ?", ["chien", "Paris", "table"], 1),
                mcq("Quel mot est un nom commun ?", ["Lucie", "Lyon", "voiture"], 2),
                mcq(
                    "Un nom propre commence toujours par...",
                    ["une lettre minuscule", "une majuscule", "un chiffre"],
                    1,
                ),
                mcq("Dans « Le chat de Léa dort », quel est le nom propre ?", ["chat", "Léa", "dort"], 1),
            ],
        ),
        # 2. Le verbe et son infinitif
        L(
            11,
            3,
            "CE2 — Le verbe et son infinitif 🏃",
            "Reconnaître le verbe et trouver son infinitif.",
            [
                mcq("Quel est l'infinitif de « il mange » ?", ["manger", "mangé", "mangeait"], 0),
                mcq("Quel est l'infinitif de « nous finissons » ?", ["finir", "finissons", "fini"], 0),
                mcq("Quel mot est un verbe ?", ["rapide", "courir", "table"], 1),
                mcq("Quel est l'infinitif de « elles vont » ?", ["aller", "allé", "vont"], 0),
            ],
        ),
        # 3. L'adjectif qualificatif
        L(
            12,
            3,
            "CE2 — L'adjectif qualificatif ✨",
            "Repérer l'adjectif qui décrit le nom.",
            [
                mcq("Dans « une grande maison », quel est l'adjectif ?", ["une", "grande", "maison"], 1),
                mcq("Quel mot est un adjectif ?", ["rouge", "manger", "chat"], 0),
                mcq("Dans « un petit chien noir », combien y a-t-il d'adjectifs ?", ["1", "2", "3"], 1),
                mcq("L'adjectif s'accorde avec...", ["le verbe", "le nom", "l'adverbe"], 1),
            ],
        ),
        # 4. Les déterminants
        L(
            13,
            3,
            "CE2 — Les déterminants 🔑",
            "Reconnaître le, la, un, des, mon devant le nom.",
            [
                mcq("Quel mot est un déterminant ?", ["chien", "le", "court"], 1),
                mcq("Complète : « ___ voiture est rouge ».", ["La", "Manger", "Vite"], 0),
                mcq("Dans « mes amis jouent », quel est le déterminant ?", ["mes", "amis", "jouent"], 0),
                mcq("Quel est le déterminant dans « des fleurs poussent » ?", ["des", "fleurs", "poussent"], 0),
            ],
        ),
        # 5. Le sujet du verbe
        L(
            14,
            4,
            "CE2 — Le sujet du verbe 🎯",
            "Trouver qui fait l'action dans la phrase.",
            [
                mcq("Dans « Le chien aboie », quel est le sujet ?", ["Le chien", "aboie", "chien aboie"], 0),
                mcq("Dans « Marie et Paul chantent », quel est le sujet ?", ["chantent", "Marie et Paul", "Marie"], 1),
                mcq("Pour trouver le sujet, on pose la question...", ["Qui est-ce qui ?", "Quand ?", "Où ?"], 0),
                mcq("Dans « Demain, nous partirons », quel est le sujet ?", ["Demain", "nous", "partirons"], 1),
            ],
        ),
        # 6. Le futur simple
        L(
            15,
            4,
            "CE2 — Le futur simple 🚀",
            "Conjuguer les verbes courants au futur.",
            [
                mcq("Conjugue « chanter » au futur avec « je ».", ["je chante", "je chanterai", "je chantais"], 1),
                mcq("« Nous ___ notre travail demain » (finir).", ["finirons", "finissons", "finirions"], 0),
                fill_blanks(
                    "Écris les verbes au futur.",
                    "Demain, tu ___ (jouer) et nous ___ (manger).",
                    ["joueras", "mangerons"],
                ),
                mcq("« Ils ___ bientôt là » (être, futur).", ["seront", "étaient", "sont"], 0),
            ],
        ),
        # 7. L'imparfait
        L(
            16,
            4,
            "CE2 — L'imparfait ⏪",
            "Conjuguer les verbes courants à l'imparfait.",
            [
                mcq("Conjugue « jouer » à l'imparfait avec « je ».", ["je jouais", "je jouerai", "je joue"], 0),
                mcq("« Nous ___ à la balle » (jouer, imparfait).", ["jouions", "jouons", "jouerons"], 0),
                fill_blanks(
                    "Écris les verbes à l'imparfait.",
                    "Avant, tu ___ (chanter) et il ___ (regarder) la télé.",
                    ["chantais", "regardait"],
                ),
                mcq("« Ils ___ contents » (être, imparfait).", ["étaient", "sont", "seront"], 0),
            ],
        ),
        # 8. Le passé composé (avec avoir)
        L(
            17,
            4,
            "CE2 — Le passé composé avec avoir ✅",
            "Former le passé composé avec l'auxiliaire avoir.",
            [
                mcq(
                    "Le passé composé se forme avec un auxiliaire + ...",
                    ["l'infinitif", "le participe passé", "le futur"],
                    1,
                ),
                mcq("« J'ai ___ une pomme » (manger).", ["mangé", "manger", "mangeais"], 0),
                mcq("« Nous avons ___ un film » (regarder).", ["regardé", "regarder", "regardions"], 0),
                mcq("Quel est l'auxiliaire dans « elle a fini » ?", ["avoir", "être", "aller"], 0),
            ],
        ),
        # 9. Les types de phrases
        L(
            18,
            3,
            "CE2 — Les types de phrases 💬",
            "Phrase déclarative, interrogative ou exclamative.",
            [
                mcq("« Tu viens ? » est une phrase...", ["déclarative", "interrogative", "exclamative"], 1),
                mcq("« Quelle belle journée ! » est une phrase...", ["interrogative", "exclamative", "déclarative"], 1),
                mcq("« Le chat dort. » est une phrase...", ["déclarative", "interrogative", "exclamative"], 0),
                mcq(
                    "Une phrase interrogative se termine par...",
                    ["un point", "un point d'interrogation", "un point d'exclamation"],
                    1,
                ),
            ],
        ),
        # 10. La ponctuation
        L(
            19,
            3,
            "CE2 — La ponctuation 🔤",
            "Utiliser le point, la virgule, le ? et le !",
            [
                mcq("Quel signe termine une question ?", [".", "?", "!"], 1),
                mcq("Quel signe marque une émotion forte ?", ["!", ",", "."], 0),
                mcq(
                    "À la fin d'une phrase déclarative, on met...",
                    ["un point", "une virgule", "un point d'interrogation"],
                    0,
                ),
                mcq("La virgule sert à...", ["terminer la phrase", "faire une petite pause", "poser une question"], 1),
            ],
        ),
        # 11. Synonymes et contraires
        L(
            20,
            3,
            "CE2 — Synonymes et contraires 🔁",
            "Trouver un mot de même sens ou de sens opposé.",
            [
                mcq("Quel est un synonyme de « content » ?", ["heureux", "triste", "fatigué"], 0),
                mcq("Quel est le contraire de « grand » ?", ["petit", "haut", "large"], 0),
                mcq("Quel est le contraire de « chaud » ?", ["froid", "tiède", "brûlant"], 0),
                mcq("Quel est un synonyme de « joli » ?", ["beau", "laid", "vieux"], 0),
            ],
        ),
        # 12. Les familles de mots
        L(
            21,
            4,
            "CE2 — Les familles de mots 🌳",
            "Préfixes, suffixes et mots de la même famille.",
            [
                mcq("Quel mot appartient à la famille de « dent » ?", ["dentiste", "danser", "donner"], 0),
                mcq("Dans « refaire », quel est le préfixe ?", ["re", "faire", "aire"], 0),
                mcq(
                    "Le suffixe « -eur » dans « chanteur » désigne...",
                    ["celui qui fait l'action", "un lieu", "un contraire"],
                    0,
                ),
                mcq("Quel mot n'est PAS de la famille de « terre » ?", ["terrain", "terrasse", "tortue"], 2),
            ],
        ),
        # 13. L'ordre alphabétique et le dictionnaire
        L(
            22,
            3,
            "CE2 — L'ordre alphabétique 📖",
            "Ranger les mots et se repérer dans le dictionnaire.",
            [
                mcq("Quelle lettre vient juste après « m » ?", ["l", "n", "o"], 1),
                mcq("Quel mot vient en premier dans le dictionnaire ?", ["banane", "abricot", "cerise"], 1),
                mcq(
                    "Entre « chat », « cheval » et « chien », lequel vient en premier ?",
                    ["chat", "cheval", "chien"],
                    0,
                ),
                mcq(
                    "Dans le dictionnaire, les mots sont rangés...",
                    ["par ordre alphabétique", "par taille", "au hasard"],
                    0,
                ),
            ],
        ),
        # 14. Le féminin des noms et adjectifs
        L(
            23,
            4,
            "CE2 — Le féminin des mots 🌸",
            "Former le féminin des noms et des adjectifs.",
            [
                mcq("Quel est le féminin de « un ami » ?", ["une amie", "une ami", "une amis"], 0),
                mcq("Quel est le féminin de « grand » ?", ["grande", "grandes", "grant"], 0),
                fill_blanks(
                    "Écris au féminin (sans accent).",
                    "Un chat noir devient une ___ ___.",
                    ["chatte", "noire"],
                ),
                mcq(
                    "Quel est le féminin de « le boulanger » ?",
                    ["la boulangère", "la boulanger", "la boulangerie"],
                    0,
                ),
            ],
        ),
        # 15. Lecture — compréhension
        L(
            24,
            4,
            "CE2 — Lecture : le petit renard 🦊",
            "Lire un texte et répondre aux questions.",
            [
                reading(
                    "Lis bien ce texte.",
                    "Léa et son petit frère Tom se promènent dans la forêt. Soudain, ils entendent un "
                    "bruit derrière un buisson. C'est un jeune renard roux, blessé à la patte. Léa "
                    "décide de l'aider : elle enroule doucement un mouchoir autour de sa patte. Le "
                    "renard les regarde, puis s'enfuit en boitant vers les arbres. Le soir, Léa "
                    "raconte tout à ses parents, très fière de sa bonne action.",
                ),
                mcq("Où se promènent Léa et Tom ?", ["Dans la forêt", "À la plage", "En ville"], 0),
                mcq("Quel animal trouvent-ils ?", ["Un lapin", "Un renard", "Un loup"], 1),
                mcq(
                    "Que fait Léa pour aider le renard ?",
                    [
                        "Elle lui donne à manger",
                        "Elle enroule un mouchoir autour de sa patte",
                        "Elle l'emmène chez le vétérinaire",
                    ],
                    1,
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE2 Français "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
