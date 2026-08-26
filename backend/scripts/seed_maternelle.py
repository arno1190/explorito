"""Seed maternelle (PS / MS / GS) — exercices 100 % visuels pour non-lecteurs.

Les enfants de maternelle ne lisent pas : aucune option n'est du texte à lire.
Chaque option est soit un **pictogramme** (image ARASAAC via ``media_gen.picto``),
soit une **pastille de couleur**, soit un **groupe d'emojis** (quantités). Les
énoncés sont de courtes consignes lues à voix haute (audio TTS généré par
``scripts/backfill_audio.py``).

6 leçons par niveau (PS, MS, GS) = 18 leçons. Idempotent par (parcours, nom).

Usage:
    uv run python scripts/seed_maternelle.py [--dry-run] [--reset]

``--reset`` supprime d'abord les leçons de ce script (par nom) avant de les
recréer — utile quand on modifie le contenu (les leçons existantes seraient
sinon ignorées par l'idempotence).
"""

import sys
from typing import Any

from media_gen import picto
from seed_curriculum import _seed_one, shuffle_options, theme

from app.core.database import SessionLocal
from app.models.content import LearningPath, Lesson, LevelEnum, Subject

XP = 15

# Couleurs vives et lisibles (valeurs CSS) pour les pastilles.
COLORS: dict[str, str] = {
    "rouge": "#EF4444",
    "bleu": "#1CAFF6",
    "jaune": "#F4B400",
    "vert": "#22C55E",
    "orange": "#F97316",
    "violet": "#8B5CF6",
    "rose": "#EC4899",
    "marron": "#92400E",
    "noir": "#111827",
    "blanc": "#FFFFFF",
    "gris": "#9CA3AF",
}


def _base(consigne: str, opts: list[dict[str, Any]], correct: int, emoji: str | None) -> dict[str, Any]:
    return {
        "type": "multiple_choice",
        "question": consigne,
        "content": {"options": opts, "multiple": False},
        "correct_answer": {"option_ids": [str(correct + 1)]},
        "media_urls": {"emoji": emoji} if emoji else {},
        "level": 1,
    }


def pic(consigne: str, options: list[tuple[str, str]], correct: int, *, emoji: str | None = None) -> dict[str, Any]:
    """QCM à pictogrammes. ``options`` = ``(label, mot_picto)``."""
    opts: list[dict[str, Any]] = []
    for i, (text, word) in enumerate(options):
        opt: dict[str, Any] = {"id": str(i + 1), "text": text}
        img = picto(word)
        if img:
            opt["image"] = img
        opts.append(opt)
    return _base(consigne, opts, correct, emoji)


def col(consigne: str, options: list[str], correct: int, *, emoji: str | None = None) -> dict[str, Any]:
    """QCM à pastilles de couleur. ``options`` = noms de couleurs (cf. COLORS)."""
    opts = [{"id": str(i + 1), "text": name, "color": COLORS[name]} for i, name in enumerate(options)]
    return _base(consigne, opts, correct, emoji)


def count(consigne: str, glyph: str, counts: list[int], correct_count: int) -> dict[str, Any]:
    """QCM « appuie là où il y a N objets » : options = groupes d'emojis."""
    opts = [{"id": str(i + 1), "text": glyph * n} for i, n in enumerate(counts)]
    return _base(consigne, opts, counts.index(correct_count), glyph)


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
                pic("Appuie sur le chat.", [("le chat", "chat"), ("le chien", "chien"), ("le lapin", "lapin")], 0),
                pic("Appuie sur le chien.", [("le poisson", "poisson"), ("le chien", "chien"), ("le chat", "chat")], 1),
                pic(
                    "Appuie sur le poisson.",
                    [("le lapin", "lapin"), ("le poisson", "poisson"), ("le chien", "chien")],
                    1,
                ),
                pic("Appuie sur le lapin.", [("le lapin", "lapin"), ("le chat", "chat"), ("le poisson", "poisson")], 0),
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
                pic(
                    "Appuie sur la pomme.", [("la pomme", "pomme"), ("la banane", "banane"), ("la fraise", "fraise")], 0
                ),
                pic(
                    "Appuie sur la banane.",
                    [("la fraise", "fraise"), ("la banane", "banane"), ("la pomme", "pomme")],
                    1,
                ),
                pic(
                    "Appuie sur la fraise.", [("la fraise", "fraise"), ("la pomme", "pomme"), ("l'orange", "orange")], 0
                ),
                pic(
                    "Appuie sur l'orange.",
                    [("la banane", "banane"), ("l'orange", "orange"), ("la fraise", "fraise")],
                    1,
                ),
            ],
        )
    )
    lessons.append(
        L(
            "maths",
            "ps",
            3,
            "Compter jusqu'à 3 🔢",
            "Reconnaître les petites quantités.",
            [
                count("Appuie là où il y a deux ballons.", "🎈", [1, 2, 3], 2),
                count("Appuie là où il y a trois étoiles.", "⭐", [1, 2, 3], 3),
                count("Appuie là où il y a un chat.", "🐱", [1, 2, 3], 1),
                count("Appuie là où il y a deux pommes.", "🍎", [3, 2, 1], 2),
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
                    "Appuie sur le rond.",
                    [("le rond", "cercle"), ("le carré", "carré"), ("le triangle", "triangle")],
                    0,
                ),
                pic(
                    "Appuie sur le carré.",
                    [("le triangle", "triangle"), ("le carré", "carré"), ("le rond", "cercle")],
                    1,
                ),
                pic(
                    "Appuie sur le triangle.",
                    [("le triangle", "triangle"), ("le rond", "cercle"), ("le carré", "carré")],
                    0,
                ),
                pic("Appuie sur l'étoile.", [("l'étoile", "étoile"), ("le rond", "cercle"), ("le carré", "carré")], 0),
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
                col("De quelle couleur est la fraise ? 🍓", ["rouge", "bleu", "vert"], 0, emoji="🍓"),
                col("De quelle couleur est le ciel ? 🌤️", ["rouge", "bleu", "jaune"], 1, emoji="🌤️"),
                col("De quelle couleur est l'herbe ? 🌱", ["vert", "violet", "rouge"], 0, emoji="🌱"),
                col("De quelle couleur est le soleil ? ☀️", ["bleu", "jaune", "noir"], 1, emoji="☀️"),
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
                pic("Appuie sur le nez.", [("le nez", "nez"), ("la main", "main"), ("le pied", "pied")], 0),
                pic("Appuie sur la main.", [("le pied", "pied"), ("la main", "main"), ("la bouche", "bouche")], 1),
                pic("Appuie sur la bouche.", [("la bouche", "bouche"), ("le nez", "nez"), ("la main", "main")], 0),
                pic("Appuie sur le pied.", [("la main", "main"), ("le pied", "pied"), ("le nez", "nez")], 1),
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
            "Reconnaître les quantités jusqu'à cinq.",
            [
                count("Appuie là où il y a quatre fleurs.", "🌸", [3, 4, 5], 4),
                count("Appuie là où il y a cinq poissons.", "🐟", [3, 4, 5], 5),
                count("Appuie là où il y a trois pommes.", "🍎", [2, 3, 4], 3),
                count("Appuie là où il y a cinq étoiles.", "⭐", [4, 5, 3], 5),
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
                    "Appuie sur le chapeau.",
                    [("le chapeau", "chapeau"), ("la chaussure", "chaussure"), ("le pantalon", "pantalon")],
                    0,
                ),
                pic(
                    "Appuie sur la chaussure.",
                    [("le manteau", "manteau"), ("la chaussure", "chaussure"), ("le chapeau", "chapeau")],
                    1,
                ),
                pic(
                    "Appuie sur le pantalon.",
                    [("le pantalon", "pantalon"), ("le chapeau", "chapeau"), ("la chaussure", "chaussure")],
                    0,
                ),
                pic(
                    "Appuie sur le manteau.",
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
                pic("Appuie sur le pain.", [("le pain", "pain"), ("le lait", "lait"), ("le fromage", "fromage")], 0),
                pic("Appuie sur le lait.", [("le gâteau", "gâteau"), ("le lait", "lait"), ("le pain", "pain")], 1),
                pic("Appuie sur le fromage.", [("le fromage", "fromage"), ("le pain", "pain"), ("le lait", "lait")], 0),
                pic(
                    "Appuie sur le gâteau.",
                    [("le lait", "lait"), ("le gâteau", "gâteau"), ("le fromage", "fromage")],
                    1,
                ),
            ],
        )
    )
    lessons.append(
        L(
            "maths",
            "ms",
            10,
            "Grand et petit 📏",
            "Comparer les tailles.",
            [
                pic("Appuie sur le plus grand.", [("l'éléphant", "éléphant"), ("la souris", "souris")], 0),
                pic("Appuie sur le plus petit.", [("la fourmi", "fourmi"), ("le chien", "chien")], 0),
                pic("Appuie sur le plus grand.", [("le chat", "chat"), ("la girafe", "girafe")], 1),
                pic("Appuie sur le plus petit.", [("l'éléphant", "éléphant"), ("la souris", "souris")], 1),
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
                pic(
                    "Appuie sur la vache.", [("la vache", "vache"), ("le mouton", "mouton"), ("le cochon", "cochon")], 0
                ),
                pic(
                    "Appuie sur le mouton.", [("la poule", "poule"), ("le mouton", "mouton"), ("la vache", "vache")], 1
                ),
                pic(
                    "Appuie sur le cochon.",
                    [("le cochon", "cochon"), ("la vache", "vache"), ("le mouton", "mouton")],
                    0,
                ),
                pic(
                    "Appuie sur la poule.", [("le mouton", "mouton"), ("la poule", "poule"), ("le cochon", "cochon")], 1
                ),
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
                col("De quelle couleur est la banane ? 🍌", ["jaune", "bleu", "rouge"], 0, emoji="🍌"),
                col("De quelle couleur est une orange ? 🍊", ["vert", "orange", "violet"], 1, emoji="🍊"),
                col("De quelle couleur est le raisin ? 🍇", ["violet", "rouge", "jaune"], 0, emoji="🍇"),
                col("De quelle couleur est la neige ? ❄️", ["noir", "blanc", "vert"], 1, emoji="❄️"),
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
            "Reconnaître les quantités jusqu'à dix.",
            [
                count("Appuie là où il y a six ballons.", "🎈", [5, 6, 7], 6),
                count("Appuie là où il y a huit étoiles.", "⭐", [7, 8, 9], 8),
                count("Appuie là où il y a dix ronds.", "🔵", [8, 9, 10], 10),
                count("Appuie là où il y a sept cœurs.", "❤️", [6, 7, 8], 7),
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
                    "Appuie sur le mot qui commence comme « avion » : le son [a].",
                    [("ananas", "ananas"), ("bateau", "bateau"), ("moto", "moto")],
                    0,
                ),
                pic(
                    "Appuie sur le mot qui commence comme « lune » : le son [l].",
                    [("souris", "souris"), ("lapin", "lapin"), ("chat", "chat")],
                    1,
                ),
                pic(
                    "Appuie sur le mot qui commence comme « papa » : le son [p].",
                    [("pomme", "pomme"), ("tomate", "tomate"), ("orange", "orange")],
                    0,
                ),
                pic(
                    "Appuie sur le mot qui commence comme « moto » : le son [m].",
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
                count("Combien de syllabes dans « chat » ? Compte et appuie.", "🔵", [1, 2, 3], 1),
                count("Combien de syllabes dans « ba-teau » ? Compte et appuie.", "🔵", [1, 2, 3], 2),
                count("Combien de syllabes dans « cho-co-lat » ? Compte et appuie.", "🔵", [2, 3, 4], 3),
                count("Combien de syllabes dans « chien » ? Compte et appuie.", "🔵", [1, 2, 3], 1),
            ],
        )
    )
    lessons.append(
        L(
            "maths",
            "gs",
            16,
            "Les formes 🔺",
            "Reconnaître les formes.",
            [
                pic(
                    "Appuie sur le rectangle.",
                    [("le rectangle", "rectangle"), ("le rond", "cercle"), ("le triangle", "triangle")],
                    0,
                ),
                pic("Appuie sur l'étoile.", [("le rond", "cercle"), ("l'étoile", "étoile"), ("le carré", "carré")], 1),
                pic(
                    "Appuie sur le carré.",
                    [("le carré", "carré"), ("le triangle", "triangle"), ("le rond", "cercle")],
                    0,
                ),
                pic(
                    "Appuie sur le triangle.",
                    [("le rectangle", "rectangle"), ("le triangle", "triangle"), ("l'étoile", "étoile")],
                    1,
                ),
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
                    "Appuie sur le soleil.",
                    [("la pluie", "pluie"), ("le soleil", "soleil"), ("la neige", "neige")],
                    1,
                    emoji="☀️",
                ),
                pic(
                    "Appuie sur la pluie.",
                    [("la pluie", "pluie"), ("le soleil", "soleil"), ("le vent", "vent")],
                    0,
                    emoji="🌧️",
                ),
                pic(
                    "Appuie sur la saison où il neige.",
                    [("l'été", "été"), ("l'hiver", "hiver"), ("le printemps", "printemps")],
                    1,
                    emoji="❄️",
                ),
                pic(
                    "Appuie sur la saison où il fait très chaud.",
                    [("l'été", "été"), ("l'hiver", "hiver"), ("l'automne", "automne")],
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
                pic(
                    "Appuie sur le contraire de « grand ».", [("petit", "petit"), ("gros", "gros"), ("haut", "haut")], 0
                ),
                pic("Appuie sur le contraire de « chaud ».", [("doux", "doux"), ("froid", "froid"), ("mou", "mou")], 1),
                pic(
                    "Appuie sur le contraire de « jour ».", [("nuit", "nuit"), ("matin", "matin"), ("soir", "soir")], 0
                ),
                pic(
                    "Appuie sur le contraire de « content ».",
                    [("joyeux", "joyeux"), ("triste", "triste"), ("gentil", "gentil")],
                    1,
                ),
            ],
        )
    )

    return lessons


def _reset(themes: list[dict[str, Any]], db: Any) -> int:
    """Supprime les leçons de ce script (par niveau + nom) avant reseed."""
    removed = 0
    for data in themes:
        subject = db.query(Subject).filter(Subject.slug == data["subject_slug"]).first()
        if not subject:
            continue
        path = (
            db.query(LearningPath)
            .filter(LearningPath.subject_id == subject.id, LearningPath.level == LevelEnum(data["level"]))
            .first()
        )
        if not path:
            continue
        lesson = db.query(Lesson).filter(Lesson.path_id == path.id, Lesson.name == data["lesson"]["name"]).first()
        if lesson:
            db.delete(lesson)
            removed += 1
    db.commit()
    return removed


def main(dry_run: bool = False, reset: bool = False) -> int:
    themes = shuffle_options(curriculum(), salt="maternelle")
    db = SessionLocal()
    created = skipped = 0
    try:
        if reset and not dry_run:
            print(f"reset : {_reset(themes, db)} leçons supprimées.")
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
    raise SystemExit(main(dry_run="--dry-run" in sys.argv, reset="--reset" in sys.argv))
