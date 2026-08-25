"""Seed CP Arts — couleurs, formes, œuvres et musique (programme officiel).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction ;
œuvres/artistes du domaine public ou faits établis, formulés simplement pour
des enfants de CP (première année, ~6 ans).

Usage:
    DATABASE_URL=... uv run python scripts/seed_cp_arts.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, shuffle_options, theme

from app.core.database import SessionLocal

LEVEL = "cp"
SLUG = "arts"


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
        # 1. Les couleurs primaires — tier 1, niveau 1
        L(
            1,
            1,
            "CP — Les couleurs primaires 🎨",
            "Rouge, jaune et bleu : les trois couleurs de base.",
            [
                mcq(
                    "Quelles sont les trois couleurs primaires ?",
                    ["Rouge, jaune, bleu", "Vert, orange, violet", "Noir, blanc, gris"],
                    0,
                ),
                mcq(
                    "Le rouge est-il une couleur primaire ?",
                    ["Oui", "Non"],
                    0,
                    emoji="🔴",
                ),
                mcq(
                    "Laquelle de ces couleurs est primaire ?",
                    ["Le vert", "Le bleu", "L'orange"],
                    1,
                    emoji="🔵",
                ),
                mcq(
                    "Combien y a-t-il de couleurs primaires ?",
                    ["Deux", "Trois", "Cinq"],
                    1,
                ),
            ],
        ),
        # 2. Mélanger les couleurs — tier 2, niveau 1
        L(
            2,
            1,
            "CP — Mélanger les couleurs 🖌️",
            "Deux couleurs primaires mélangées donnent une nouvelle couleur.",
            [
                mcq(
                    "Bleu + jaune, ça donne quelle couleur ?",
                    ["Du vert", "Du violet", "De l'orange"],
                    0,
                    emoji="🟢",
                ),
                mcq(
                    "Rouge + jaune, ça donne quelle couleur ?",
                    ["Du vert", "De l'orange", "Du violet"],
                    1,
                    emoji="🟠",
                ),
                mcq(
                    "Rouge + bleu, ça donne quelle couleur ?",
                    ["Du vert", "De l'orange", "Du violet"],
                    2,
                    emoji="🟣",
                ),
                mcq(
                    "Pour faire du vert, je mélange…",
                    ["Bleu et jaune", "Rouge et bleu", "Rouge et jaune"],
                    0,
                ),
            ],
        ),
        # 3. Couleurs chaudes et froides — tier 3, niveau 1
        L(
            3,
            1,
            "CP — Couleurs chaudes et froides 🔥",
            "Les couleurs qui réchauffent et celles qui rafraîchissent.",
            [
                mcq(
                    "Le rouge est une couleur…",
                    ["Chaude", "Froide"],
                    0,
                    emoji="🔥",
                ),
                mcq(
                    "Le bleu est une couleur…",
                    ["Chaude", "Froide"],
                    1,
                    emoji="❄️",
                ),
                mcq(
                    "Quelle couleur fait penser au soleil et au feu ?",
                    ["Le bleu", "L'orange", "Le vert"],
                    1,
                    emoji="☀️",
                ),
                mcq(
                    "Quelle couleur fait penser à la mer et à la glace ?",
                    ["Le rouge", "Le bleu", "L'orange"],
                    1,
                ),
            ],
        ),
        # 4. Les nuances : clair et foncé — tier 4, niveau 1
        L(
            4,
            1,
            "CP — Clair et foncé 🌗",
            "Éclaircir ou foncer une couleur.",
            [
                mcq(
                    "Pour éclaircir une couleur, on ajoute…",
                    ["Du blanc", "Du noir", "Du rouge"],
                    0,
                    emoji="⚪",
                ),
                mcq(
                    "Pour foncer une couleur, on ajoute…",
                    ["Du blanc", "Du noir", "Du jaune"],
                    1,
                    emoji="⚫",
                ),
                mcq(
                    "Le bleu ciel est un bleu…",
                    ["Clair", "Foncé"],
                    0,
                ),
                mcq(
                    "Le bleu marine est un bleu…",
                    ["Clair", "Foncé"],
                    1,
                ),
            ],
        ),
        # 5. Les formes et les lignes — tier 5, niveau 1
        L(
            5,
            1,
            "CP — Les formes et les lignes ✏️",
            "Lignes droites, courbes, zigzag et formes simples.",
            [
                mcq(
                    "Comment appelle-t-on une ligne qui ne tourne pas ?",
                    ["Une ligne droite", "Une ligne courbe", "Un zigzag"],
                    0,
                    emoji="📏",
                ),
                mcq(
                    "Une ligne qui tourne en rond est une ligne…",
                    ["Droite", "Courbe", "En zigzag"],
                    1,
                ),
                mcq(
                    "Combien de côtés a un triangle ?",
                    ["Trois", "Quatre", "Cinq"],
                    0,
                    emoji="🔺",
                ),
                mcq(
                    "Quelle forme est toute ronde, sans coins ?",
                    ["Le carré", "Le cercle", "Le triangle"],
                    1,
                    emoji="⭕",
                ),
            ],
        ),
        # 6. Le point, la ligne, la tache — tier 6, niveau 1
        L(
            6,
            1,
            "CP — Le point, la ligne, la tache 🎯",
            "Les traces que laisse le geste de l'artiste.",
            [
                mcq(
                    "Quand j'appuie une seule fois avec mon crayon, je fais un…",
                    ["Point", "Trait long", "Cercle"],
                    0,
                    emoji="⚫",
                ),
                mcq(
                    "Quand je tire mon crayon sans lever la main, je trace une…",
                    ["Ligne", "Tache", "Point"],
                    0,
                ),
                mcq(
                    "Quand je pose beaucoup de peinture d'un coup, je fais une…",
                    ["Ligne fine", "Tache", "Point tout petit"],
                    1,
                ),
                mcq(
                    "Avec quoi peut-on faire des points de peinture ?",
                    ["Le bout du doigt", "Une règle", "Une gomme"],
                    0,
                    emoji="👆",
                ),
            ],
        ),
        # 7. Portrait, paysage, nature morte — tier 7, niveau 1
        L(
            7,
            1,
            "CP — Portrait, paysage, nature morte 🖼️",
            "Reconnaître les différents types d'images.",
            [
                mcq(
                    "Un portrait, c'est le dessin d'…",
                    ["Une personne", "Une montagne", "Un panier de fruits"],
                    0,
                    emoji="🧑",
                ),
                mcq(
                    "Un paysage, c'est le dessin d'…",
                    ["Un visage", "Un lieu, la nature", "Une seule pomme"],
                    1,
                    emoji="🏞️",
                ),
                mcq(
                    "Une nature morte, c'est surtout le dessin d'…",
                    ["Objets et fruits posés", "Un roi", "Une forêt"],
                    0,
                    emoji="🍎",
                ),
                mcq(
                    "Comment appelle-t-on le portrait de soi-même ?",
                    ["Un paysage", "Un autoportrait", "Une nature morte"],
                    1,
                ),
            ],
        ),
        # 8. La Joconde — tier 8, niveau 1
        L(
            8,
            1,
            "CP — La Joconde 🖼️",
            "Un tableau très célèbre de Léonard de Vinci.",
            [
                mcq(
                    "Qui a peint La Joconde ?",
                    ["Léonard de Vinci", "Vincent van Gogh", "Claude Monet"],
                    0,
                ),
                mcq(
                    "La Joconde est le portrait d'…",
                    ["Un roi", "Une femme qui sourit", "Un chevalier"],
                    1,
                    emoji="🙂",
                ),
                mcq(
                    "La Joconde est un…",
                    ["Portrait", "Paysage de mer", "Dessin d'animal"],
                    0,
                ),
                mcq(
                    "Dans quel grand musée peut-on voir La Joconde ?",
                    ["Le Louvre, à Paris", "La tour Eiffel", "Le zoo"],
                    0,
                    emoji="🏛️",
                ),
            ],
        ),
        # 9. Les Tournesols — tier 9, niveau 1
        L(
            9,
            1,
            "CP — Les Tournesols 🌻",
            "Un tableau plein de jaune peint par Van Gogh.",
            [
                mcq(
                    "Qui a peint Les Tournesols ?",
                    ["Vincent van Gogh", "Léonard de Vinci", "Pablo Picasso"],
                    0,
                    emoji="🌻",
                ),
                mcq(
                    "Que voit-on sur ce tableau ?",
                    ["Des fleurs jaunes", "Un château", "La mer"],
                    0,
                ),
                mcq(
                    "Quelle couleur domine dans Les Tournesols ?",
                    ["Le jaune", "Le bleu", "Le noir"],
                    0,
                    emoji="🟡",
                ),
                mcq(
                    "Les tournesols sont posés dans un…",
                    ["Vase", "Panier de pommes", "Sac"],
                    0,
                ),
            ],
        ),
        # 10. Les outils du peintre — tier 10, niveau 1
        L(
            10,
            1,
            "CP — Les outils du peintre 🖌️",
            "Pinceau, crayon, éponge : les outils pour créer.",
            [
                mcq(
                    "Avec quel outil étale-t-on la peinture ?",
                    ["Un pinceau", "Une cuillère", "Une gomme"],
                    0,
                    emoji="🖌️",
                ),
                mcq(
                    "Avec quel outil dessine-t-on des traits fins ?",
                    ["Un crayon", "Un balai", "Un marteau"],
                    0,
                    emoji="✏️",
                ),
                mcq(
                    "Avec quoi peut-on tamponner de grandes taches de couleur ?",
                    ["Une éponge", "Une règle", "Des ciseaux"],
                    0,
                    emoji="🧽",
                ),
                mcq(
                    "Dans quoi mélange-t-on ses couleurs de peinture ?",
                    ["Une palette", "Un cartable", "Une trousse"],
                    0,
                ),
            ],
        ),
        # 11. Le collage et les matières — tier 11, niveau 2
        L(
            11,
            2,
            "CP — Le collage et les matières ✂️",
            "Coller du papier et sentir les différentes matières.",
            [
                mcq(
                    "Coller des morceaux de papier pour faire une image, c'est le…",
                    ["Collage", "Modelage", "Coloriage"],
                    0,
                    emoji="✂️",
                ),
                mcq(
                    "Avec quoi colle-t-on les morceaux de papier ?",
                    ["De la colle", "De l'eau seule", "Du sel"],
                    0,
                ),
                mcq(
                    "Le coton est une matière…",
                    ["Douce", "Piquante", "Dure comme la pierre"],
                    0,
                    emoji="☁️",
                ),
                mcq(
                    "Quel outil sert à découper le papier ?",
                    ["Des ciseaux", "Un pinceau", "Une gomme"],
                    0,
                ),
            ],
        ),
        # 12. Les instruments de musique — tier 12, niveau 2
        L(
            12,
            2,
            "CP — Les instruments de musique 🎵",
            "Reconnaître le piano, la guitare, le tambour et la flûte.",
            [
                mcq(
                    "Sur quel instrument appuie-t-on sur des touches noires et blanches ?",
                    ["Le piano", "Le tambour", "La flûte"],
                    0,
                    emoji="🎹",
                ),
                mcq(
                    "Quel instrument a des cordes que l'on pince ?",
                    ["La guitare", "Le tambour", "La flûte"],
                    0,
                    emoji="🎸",
                ),
                mcq(
                    "Sur quel instrument tape-t-on pour faire du son ?",
                    ["Le tambour", "Le piano", "La flûte"],
                    0,
                    emoji="🥁",
                ),
                mcq(
                    "Dans quel instrument souffle-t-on pour jouer ?",
                    ["La flûte", "La guitare", "Le tambour"],
                    0,
                    emoji="🎶",
                ),
            ],
        ),
        # 13. Les familles d'instruments — tier 13, niveau 2
        L(
            13,
            2,
            "CP — Les familles d'instruments 🎻",
            "Cordes, vents et percussions.",
            [
                mcq(
                    "La guitare est un instrument à…",
                    ["Cordes", "Vent", "Percussion"],
                    0,
                    emoji="🎸",
                ),
                mcq(
                    "La flûte est un instrument à…",
                    ["Cordes", "Vent", "Percussion"],
                    1,
                    emoji="🎶",
                ),
                mcq(
                    "Le tambour est un instrument à…",
                    ["Cordes", "Vent", "Percussion"],
                    2,
                    emoji="🥁",
                ),
                mcq(
                    "Pour jouer d'un instrument à vent, il faut…",
                    ["Souffler dedans", "Taper dessus", "Pincer des cordes"],
                    0,
                ),
            ],
        ),
        # 14. Le rythme et le son — tier 14, niveau 2
        L(
            14,
            2,
            "CP — Le rythme et le son 🔊",
            "Fort ou doux, vite ou lent, aigu ou grave.",
            [
                mcq(
                    "Un son très puissant est un son…",
                    ["Fort", "Doux"],
                    0,
                    emoji="🔊",
                ),
                mcq(
                    "Une musique qui va très vite est…",
                    ["Rapide", "Lente"],
                    0,
                ),
                mcq(
                    "Le petit oiseau qui chante fait un son…",
                    ["Aigu", "Grave"],
                    0,
                    emoji="🐦",
                ),
                mcq(
                    "Le gros tambour fait un son…",
                    ["Aigu", "Grave"],
                    1,
                    emoji="🥁",
                ),
            ],
        ),
        # 15. Chanter et écouter — tier 15, niveau 2
        L(
            15,
            2,
            "CP — Chanter et écouter 🎤",
            "Les comptines et la voix.",
            [
                mcq(
                    "Avec quelle partie de ton corps chantes-tu ?",
                    ["La voix", "Les pieds", "Les mains"],
                    0,
                    emoji="🎤",
                ),
                mcq(
                    "Une petite chanson pour les enfants s'appelle une…",
                    ["Comptine", "Recette", "Photo"],
                    0,
                ),
                mcq(
                    "« Frère Jacques » est une…",
                    ["Comptine", "Peinture", "Sculpture"],
                    0,
                    emoji="🎵",
                ),
                mcq(
                    "Pour bien chanter tous ensemble, il faut…",
                    ["Écouter les autres", "Crier le plus fort", "Fermer les oreilles"],
                    0,
                    emoji="👂",
                ),
            ],
        ),
    ]


def main(dry_run: bool = False) -> int:
    themes = shuffle_options(curriculum(), salt="cp-arts")
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CP Arts "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
