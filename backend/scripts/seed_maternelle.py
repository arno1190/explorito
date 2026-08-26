"""Seed maternelle (PS / MS / GS) — exercices visuels pour non-lecteurs.

Les enfants de maternelle ne lisent pas : chaque exercice est un QCM dont
- l'énoncé est court (lu à voix haute par l'audio TTS, généré séparément par
  ``scripts/backfill_audio.py``),
- les options portent quand c'est possible un **pictogramme** (image ARASAAC via
  ``media_gen.picto``) plutôt que du texte, et les leçons de dénombrement
  affichent des emojis dans l'énoncé.

6 leçons par niveau (PS, MS, GS) = 18 leçons. Idempotent par (parcours, nom).

Usage:
    uv run python scripts/seed_maternelle.py [--dry-run]
"""

import sys
from typing import Any

from media_gen import picto
from seed_curriculum import _seed_one, shuffle_options, theme

from app.core.database import SessionLocal

XP = 15


def pic(
    consigne: str, options: list[tuple[str, str | None]], correct: int, *, emoji: str | None = None
) -> dict[str, Any]:
    """QCM à options illustrées.

    ``options`` = liste de ``(texte, mot_picto | None)``. Si un pictogramme
    ARASAAC existe pour le mot, il est attaché à l'option ; sinon on garde le
    texte seul. ``correct`` = index 0-based de la bonne option.
    """
    opts: list[dict[str, Any]] = []
    for i, (text, word) in enumerate(options):
        opt: dict[str, Any] = {"id": str(i + 1), "text": text}
        if word:
            img = picto(word)
            if img:
                opt["image"] = img
        opts.append(opt)
    ex: dict[str, Any] = {
        "type": "multiple_choice",
        "question": consigne,
        "content": {"options": opts, "multiple": False},
        "correct_answer": {"option_ids": [str(correct + 1)]},
        "media_urls": {"emoji": emoji} if emoji else {},
        "level": 1,
    }
    return ex


def L(slug: str, level: str, tier: int, name: str, desc: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
    return theme(slug, level, tier, name, desc, XP, exercises)


def curriculum() -> list[dict[str, Any]]:
    lessons: list[dict[str, Any]] = []

    # ---------------------------------------------------------------- PS (~3 ans)
    lessons.append(
        L(
            "francais",
            "ps",
            1,
            "Les animaux 🐾",
            "Reconnaître les animaux familiers.",
            [
                pic("Où est le chat ?", [("le chat", "chat"), ("le chien", "chien"), ("le lapin", "lapin")], 0),
                pic("Où est le chien ?", [("le poisson", "poisson"), ("le chien", "chien"), ("le chat", "chat")], 1),
                pic(
                    "Où est le poisson ?", [("le lapin", "lapin"), ("le poisson", "poisson"), ("le chien", "chien")], 1
                ),
                pic("Où est le lapin ?", [("le lapin", "lapin"), ("le chat", "chat"), ("le poisson", "poisson")], 0),
            ],
        )
    )
    lessons.append(
        L(
            "francais",
            "ps",
            2,
            "Les fruits 🍎",
            "Nommer les fruits du quotidien.",
            [
                pic("Où est la pomme ?", [("la pomme", "pomme"), ("la banane", "banane"), ("la fraise", "fraise")], 0),
                pic("Où est la banane ?", [("la fraise", "fraise"), ("la banane", "banane"), ("la pomme", "pomme")], 1),
                pic("Où est la fraise ?", [("la fraise", "fraise"), ("la pomme", "pomme"), ("l'orange", "orange")], 0),
                pic("Où est l'orange ?", [("la banane", "banane"), ("l'orange", "orange"), ("la fraise", "fraise")], 1),
            ],
        )
    )
    lessons.append(
        L(
            "maths",
            "ps",
            3,
            "Compter jusqu'à 3 🔢",
            "Dénombrer de petites quantités.",
            [
                pic("Combien de pommes ? 🍎", [("1", None), ("2", None), ("3", None)], 0, emoji="🍎"),
                pic("Combien de ballons ? 🎈🎈", [("1", None), ("2", None), ("3", None)], 1, emoji="🎈"),
                pic("Combien d'étoiles ? ⭐⭐⭐", [("1", None), ("2", None), ("3", None)], 2, emoji="⭐"),
                pic("Combien de chats ? 🐱🐱", [("2", None), ("3", None), ("1", None)], 0, emoji="🐱"),
            ],
        )
    )
    lessons.append(
        L(
            "maths",
            "ps",
            4,
            "Les formes 🔷",
            "Reconnaître le rond, le carré et le triangle.",
            [
                pic(
                    "Où est le rond ? ⭕",
                    [("le rond", "rond"), ("le carré", "carré"), ("le triangle", "triangle")],
                    0,
                    emoji="⭕",
                ),
                pic(
                    "Où est le carré ? 🟦",
                    [("le triangle", "triangle"), ("le carré", "carré"), ("le rond", "rond")],
                    1,
                    emoji="🟦",
                ),
                pic(
                    "Où est le triangle ? 🔺",
                    [("le triangle", "triangle"), ("le rond", "rond"), ("le carré", "carré")],
                    0,
                    emoji="🔺",
                ),
                pic("Combien de côtés a le triangle ? 🔺", [("2", None), ("3", None), ("4", None)], 1, emoji="🔺"),
            ],
        )
    )
    lessons.append(
        L(
            "arts",
            "ps",
            5,
            "Les couleurs 🎨",
            "Nommer les couleurs de base.",
            [
                pic(
                    "De quelle couleur est la fraise ? 🍓",
                    [("rouge", None), ("bleu", None), ("vert", None)],
                    0,
                    emoji="🍓",
                ),
                pic(
                    "De quelle couleur est le ciel ? ☀️",
                    [("rouge", None), ("bleu", None), ("jaune", None)],
                    1,
                    emoji="🌤️",
                ),
                pic(
                    "De quelle couleur est l'herbe ? 🌱",
                    [("vert", None), ("violet", None), ("rouge", None)],
                    0,
                    emoji="🌱",
                ),
                pic(
                    "De quelle couleur est le soleil ? ☀️",
                    [("bleu", None), ("jaune", None), ("noir", None)],
                    1,
                    emoji="☀️",
                ),
            ],
        )
    )
    lessons.append(
        L(
            "monde",
            "ps",
            6,
            "Mon corps 🧒",
            "Montrer les parties du visage et du corps.",
            [
                pic("Où est le nez ?", [("le nez", "nez"), ("la main", "main"), ("le pied", "pied")], 0),
                pic("Où est la main ?", [("le pied", "pied"), ("la main", "main"), ("la bouche", "bouche")], 1),
                pic("Où est la bouche ?", [("la bouche", "bouche"), ("le nez", "nez"), ("la main", "main")], 0),
                pic("Où est le pied ?", [("la main", "main"), ("le pied", "pied"), ("le nez", "nez")], 1),
            ],
        )
    )

    # ---------------------------------------------------------------- MS (~4 ans)
    lessons.append(
        L(
            "maths",
            "ms",
            7,
            "Compter jusqu'à 5 ✋",
            "Dénombrer jusqu'à cinq.",
            [
                pic("Combien de fleurs ? 🌸🌸🌸🌸", [("3", None), ("4", None), ("5", None)], 1, emoji="🌸"),
                pic("Combien de poissons ? 🐟🐟🐟🐟🐟", [("4", None), ("5", None), ("6", None)], 1, emoji="🐟"),
                pic("Combien de pommes ? 🍎🍎🍎", [("2", None), ("3", None), ("4", None)], 1, emoji="🍎"),
                pic("Combien d'étoiles ? ⭐⭐⭐⭐", [("5", None), ("4", None), ("3", None)], 1, emoji="⭐"),
            ],
        )
    )
    lessons.append(
        L(
            "francais",
            "ms",
            8,
            "Les vêtements 👕",
            "Nommer les vêtements.",
            [
                pic(
                    "Où est le chapeau ?",
                    [("le chapeau", "chapeau"), ("la chaussure", "chaussure"), ("le pantalon", "pantalon")],
                    0,
                ),
                pic(
                    "Où est la chaussure ?",
                    [("le manteau", "manteau"), ("la chaussure", "chaussure"), ("le chapeau", "chapeau")],
                    1,
                ),
                pic(
                    "Où est le pantalon ?",
                    [("le pantalon", "pantalon"), ("le chapeau", "chapeau"), ("la chaussure", "chaussure")],
                    0,
                ),
                pic(
                    "Où est le manteau ?",
                    [("la chaussure", "chaussure"), ("le manteau", "manteau"), ("le pantalon", "pantalon")],
                    1,
                ),
            ],
        )
    )
    lessons.append(
        L(
            "monde",
            "ms",
            9,
            "Les aliments 🍞",
            "Reconnaître ce que l'on mange.",
            [
                pic("Où est le pain ?", [("le pain", "pain"), ("le lait", "lait"), ("le fromage", "fromage")], 0),
                pic("Où est le lait ?", [("le gâteau", "gâteau"), ("le lait", "lait"), ("le pain", "pain")], 1),
                pic("Où est le fromage ?", [("le fromage", "fromage"), ("le pain", "pain"), ("le lait", "lait")], 0),
                pic("Où est le gâteau ?", [("le lait", "lait"), ("le gâteau", "gâteau"), ("le fromage", "fromage")], 1),
            ],
        )
    )
    lessons.append(
        L(
            "maths",
            "ms",
            10,
            "Grand et petit 📏",
            "Comparer les tailles et se repérer.",
            [
                pic("Quel est le plus grand ? 🐘 🐭", [("l'éléphant", "éléphant"), ("la souris", "souris")], 0),
                pic("Quel est le plus petit ? 🐜 🐕", [("le chien", "chien"), ("la fourmi", "fourmi")], 1),
                pic("Quel animal est le plus grand ? 🦒 🐈", [("la girafe", "girafe"), ("le chat", "chat")], 0),
                pic("Combien font 3 doigts et 1 doigt ? ✋", [("3", None), ("4", None), ("5", None)], 1, emoji="✋"),
            ],
        )
    )
    lessons.append(
        L(
            "monde",
            "ms",
            11,
            "Les animaux de la ferme 🐄",
            "Nommer les animaux de la ferme.",
            [
                pic("Où est la vache ?", [("la vache", "vache"), ("le mouton", "mouton"), ("le cochon", "cochon")], 0),
                pic("Où est le mouton ?", [("la poule", "poule"), ("le mouton", "mouton"), ("la vache", "vache")], 1),
                pic("Où est le cochon ?", [("le cochon", "cochon"), ("la vache", "vache"), ("le mouton", "mouton")], 0),
                pic("Où est la poule ?", [("le mouton", "mouton"), ("la poule", "poule"), ("le cochon", "cochon")], 1),
            ],
        )
    )
    lessons.append(
        L(
            "arts",
            "ms",
            12,
            "Encore des couleurs 🌈",
            "Enrichir le vocabulaire des couleurs.",
            [
                pic(
                    "De quelle couleur est la banane ? 🍌",
                    [("jaune", None), ("bleu", None), ("rouge", None)],
                    0,
                    emoji="🍌",
                ),
                pic(
                    "De quelle couleur est une orange ? 🍊",
                    [("vert", None), ("orange", None), ("violet", None)],
                    1,
                    emoji="🍊",
                ),
                pic(
                    "De quelle couleur est le raisin ? 🍇",
                    [("violet", None), ("rouge", None), ("jaune", None)],
                    0,
                    emoji="🍇",
                ),
                pic(
                    "De quelle couleur est la neige ? ❄️",
                    [("noir", None), ("blanc", None), ("vert", None)],
                    1,
                    emoji="❄️",
                ),
            ],
        )
    )

    # ---------------------------------------------------------------- GS (~5 ans)
    lessons.append(
        L(
            "maths",
            "gs",
            13,
            "Compter jusqu'à 10 🔟",
            "Dénombrer jusqu'à dix.",
            [
                pic("Combien de doigts ? ✋✋", [("8", None), ("10", None), ("9", None)], 1, emoji="✋"),
                pic("Combien d'étoiles ? ⭐⭐⭐⭐⭐⭐", [("5", None), ("6", None), ("7", None)], 1, emoji="⭐"),
                pic("Combien de ballons ? 🎈🎈🎈🎈🎈🎈🎈", [("6", None), ("7", None), ("8", None)], 1, emoji="🎈"),
                pic("Quel nombre vient après 8 ?", [("9", None), ("7", None), ("10", None)], 0),
            ],
        )
    )
    lessons.append(
        L(
            "francais",
            "gs",
            14,
            "Le son du début 👂",
            "Repérer le premier son d'un mot.",
            [
                pic(
                    "Quel mot commence comme « avion » ? [a]",
                    [("ananas", "ananas"), ("bateau", "bateau"), ("moto", "moto")],
                    0,
                ),
                pic(
                    "Quel mot commence comme « lune » ? [l]",
                    [("souris", "souris"), ("lapin", "lapin"), ("chat", "chat")],
                    1,
                ),
                pic(
                    "Quel mot commence comme « papa » ? [p]",
                    [("pomme", "pomme"), ("tomate", "tomate"), ("orange", "orange")],
                    0,
                ),
                pic(
                    "Quel mot commence comme « moto » ? [m]",
                    [("vache", "vache"), ("maison", "maison"), ("bateau", "bateau")],
                    1,
                ),
            ],
        )
    )
    lessons.append(
        L(
            "francais",
            "gs",
            15,
            "Les syllabes 👏",
            "Compter les syllabes en tapant dans les mains.",
            [
                pic("Combien de syllabes dans « chat » ?", [("1", None), ("2", None), ("3", None)], 0),
                pic("Combien de syllabes dans « ba-teau » ?", [("1", None), ("2", None), ("3", None)], 1),
                pic("Combien de syllabes dans « cho-co-lat » ?", [("2", None), ("3", None), ("4", None)], 1),
                pic("Combien de syllabes dans « chien » ?", [("1", None), ("2", None), ("3", None)], 0),
            ],
        )
    )
    lessons.append(
        L(
            "maths",
            "gs",
            16,
            "Formes et tailles 🔺",
            "Reconnaître les formes et comparer.",
            [
                pic(
                    "Où est le rectangle ?",
                    [("le rectangle", "rectangle"), ("le rond", "rond"), ("le triangle", "triangle")],
                    0,
                ),
                pic("Combien de côtés a un carré ? 🟦", [("3", None), ("4", None), ("5", None)], 1, emoji="🟦"),
                pic("Où est l'étoile ?", [("le rond", "rond"), ("l'étoile", "étoile"), ("le carré", "carré")], 1),
                pic("Combien de côtés a un triangle ? 🔺", [("3", None), ("4", None), ("2", None)], 0, emoji="🔺"),
            ],
        )
    )
    lessons.append(
        L(
            "monde",
            "gs",
            17,
            "Le temps qu'il fait 🌦️",
            "Reconnaître la météo et les saisons.",
            [
                pic(
                    "Quel temps fait-il ? ☀️",
                    [("il pleut", "pluie"), ("il y a du soleil", "soleil"), ("il neige", "neige")],
                    1,
                    emoji="☀️",
                ),
                pic(
                    "Quel temps fait-il ? 🌧️",
                    [("il pleut", "pluie"), ("il y a du soleil", "soleil"), ("il y a du vent", "vent")],
                    0,
                    emoji="🌧️",
                ),
                pic(
                    "En quelle saison tombe la neige ? ❄️",
                    [("l'été", None), ("l'hiver", None), ("le printemps", None)],
                    1,
                    emoji="❄️",
                ),
                pic(
                    "Quand fait-il très chaud ? 🏖️",
                    [("en été", None), ("en hiver", None), ("en automne", None)],
                    0,
                    emoji="🏖️",
                ),
            ],
        )
    )
    lessons.append(
        L(
            "francais",
            "gs",
            18,
            "Les contraires ↔️",
            "Trouver le contraire d'un mot.",
            [
                pic("Quel est le contraire de « grand » ?", [("petit", None), ("gros", None), ("haut", None)], 0),
                pic("Quel est le contraire de « chaud » ?", [("doux", None), ("froid", None), ("mou", None)], 1),
                pic("Quel est le contraire de « jour » ?", [("nuit", None), ("matin", None), ("soir", None)], 0),
                pic(
                    "Quel est le contraire de « content » ?", [("joyeux", None), ("triste", None), ("gentil", None)], 1
                ),
            ],
        )
    )

    return lessons


def main(dry_run: bool = False) -> int:
    themes = shuffle_options(curriculum(), salt="maternelle")
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons maternelle "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
