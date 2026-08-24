"""Seed CM1 Arts — programme avancé (arts plastiques & musique).

Idempotent par (parcours, nom de leçon). Faits établis / domaine public.

Usage:
    DATABASE_URL=... uv run python scripts/seed_cm1_arts.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, theme

from app.core.database import SessionLocal

LEVEL = "cm1"
SLUG = "arts"


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
        # 1. Les couleurs primaires et secondaires — tier 10, niveau 4
        L(
            10,
            4,
            "CM1 — Couleurs primaires et secondaires 🎨",
            "Les trois primaires et les couleurs qu'elles fabriquent.",
            [
                mcq(
                    "Quelles sont les trois couleurs primaires ?",
                    ["Rouge, jaune, bleu", "Vert, orange, violet", "Noir, blanc, gris", "Rose, marron, beige"],
                    0,
                ),
                mcq(
                    "Quelle couleur obtient-on en mélangeant du jaune et du bleu ?",
                    ["Le vert", "Le violet", "L'orange", "Le marron"],
                    0,
                ),
                mcq(
                    "Quelle couleur obtient-on en mélangeant du rouge et du jaune ?",
                    ["L'orange", "Le vert", "Le violet", "Le gris"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on une couleur faite en mélangeant deux primaires ?",
                    ["Une couleur secondaire", "Une couleur primaire", "Une couleur blanche", "Une couleur neutre"],
                    0,
                ),
            ],
        ),
        # 2. Couleurs chaudes, froides et complémentaires — tier 11, niveau 4
        L(
            11,
            4,
            "CM1 — Chaudes, froides et complémentaires 🔥",
            "Ranger les couleurs et trouver leurs complémentaires.",
            [
                mcq(
                    "Laquelle de ces couleurs est une couleur chaude ?",
                    ["Le rouge", "Le bleu", "Le vert", "Le violet"],
                    0,
                ),
                mcq(
                    "Laquelle de ces couleurs est une couleur froide ?",
                    ["Le bleu", "L'orange", "Le rouge", "Le jaune"],
                    0,
                ),
                mcq(
                    "Quelle est la couleur complémentaire du rouge ?",
                    ["Le vert", "Le jaune", "Le bleu", "Le marron"],
                    0,
                ),
                mcq(
                    "À quoi servent deux couleurs complémentaires côte à côte ?",
                    [
                        "Elles se mettent en valeur et créent un contraste",
                        "Elles deviennent invisibles",
                        "Elles se mélangent toujours en blanc",
                        "Elles font toujours du noir sur la feuille",
                    ],
                    0,
                ),
            ],
        ),
        # 3. Les nuances et le camaïeu — tier 12, niveau 4
        L(
            12,
            4,
            "CM1 — Les nuances et le camaïeu 🌗",
            "Éclaircir, foncer et jouer avec une seule couleur.",
            [
                mcq(
                    "Comment appelle-t-on un dégradé de tons d'une seule couleur ?",
                    ["Un camaïeu", "Un arc-en-ciel", "Un contraste", "Un aplat"],
                    0,
                ),
                mcq(
                    "Que faut-il ajouter à une couleur pour l'éclaircir ?",
                    ["Du blanc", "Du noir", "Du rouge", "Du bleu"],
                    0,
                ),
                mcq(
                    "Que faut-il ajouter à une couleur pour la foncer ?",
                    ["Du noir", "Du blanc", "Du jaune", "De l'eau claire"],
                    0,
                ),
                mcq(
                    "Une « nuance », c'est :",
                    [
                        "une petite différence entre deux tons proches",
                        "une couleur primaire",
                        "un pinceau spécial",
                        "le nom d'un tableau",
                    ],
                    0,
                ),
            ],
        ),
        # 4. La perspective (notions simples) — tier 13, niveau 5
        L(
            13,
            5,
            "CM1 — La perspective 🛤️",
            "Donner l'impression de profondeur dans un dessin.",
            [
                mcq(
                    "À quoi sert la perspective dans un dessin ?",
                    [
                        "À donner une impression de profondeur",
                        "À rendre les couleurs plus vives",
                        "À dessiner plus vite",
                        "À effacer les traits",
                    ],
                    0,
                ),
                mcq(
                    "Un objet éloigné se dessine généralement :",
                    ["Plus petit", "Plus grand", "Toujours en rouge", "Sans le dessiner"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on la ligne où le ciel semble toucher la terre ?",
                    ["La ligne d'horizon", "La ligne de fuite", "La diagonale", "Le contour"],
                    0,
                ),
                mcq(
                    "Vers quel point les lignes semblent-elles se rejoindre au loin ?",
                    ["Le point de fuite", "Le point central", "Le point de départ", "Le point noir"],
                    0,
                ),
            ],
        ),
        # 5. Le portrait et l'autoportrait — tier 14, niveau 5
        L(
            14,
            5,
            "CM1 — Portrait et autoportrait 🖼️",
            "Représenter un visage, et se représenter soi-même.",
            [
                mcq(
                    "Qu'est-ce qu'un portrait ?",
                    [
                        "La représentation d'une personne",
                        "La représentation d'un paysage",
                        "La représentation de fruits",
                        "La représentation d'un bâtiment",
                    ],
                    0,
                ),
                mcq(
                    "Qu'est-ce qu'un autoportrait ?",
                    [
                        "Un portrait de soi-même par l'artiste",
                        "Le portrait d'un roi",
                        "Le portrait d'un animal",
                        "Un portrait de groupe",
                    ],
                    0,
                ),
                mcq(
                    "Quel tableau célèbre de Léonard de Vinci est un portrait de femme ?",
                    ["La Joconde", "La Nuit étoilée", "Les Nymphéas", "Le Cri"],
                    0,
                ),
                mcq(
                    "Sur un portrait, où se trouvent les yeux dans un visage bien proportionné ?",
                    [
                        "À peu près au milieu de la hauteur du visage",
                        "Tout en haut du front",
                        "Sur le menton",
                        "En dehors du visage",
                    ],
                    0,
                ),
            ],
        ),
        # 6. Le paysage en peinture — tier 15, niveau 4
        L(
            15,
            4,
            "CM1 — Le paysage en peinture 🏞️",
            "Peindre la nature : ciel, terre et profondeur.",
            [
                mcq(
                    "Qu'est-ce qu'un paysage en peinture ?",
                    [
                        "La représentation d'un lieu et de la nature",
                        "La représentation d'un visage",
                        "La représentation de fruits sur une table",
                        "La représentation d'une statue",
                    ],
                    0,
                ),
                mcq(
                    "Dans un paysage, où se trouve souvent le ciel ?",
                    [
                        "Dans la partie haute du tableau",
                        "Dans la partie basse",
                        "Au centre uniquement",
                        "On ne le peint jamais",
                    ],
                    0,
                ),
                mcq(
                    "Quel peintre est célèbre pour ses paysages et ses nénuphars ?",
                    ["Claude Monet", "Pablo Picasso", "Michel-Ange", "Auguste Rodin"],
                    0,
                ),
                mcq(
                    "Pour montrer la profondeur d'un paysage, les collines lointaines sont souvent peintes :",
                    [
                        "Plus claires et plus floues",
                        "En noir vif",
                        "Plus grandes qu'au premier plan",
                        "Sans aucune couleur",
                    ],
                    0,
                ),
            ],
        ),
        # 7. La nature morte — tier 16, niveau 4
        L(
            16,
            4,
            "CM1 — La nature morte 🍎",
            "Peindre des objets et des fruits posés.",
            [
                mcq(
                    "Qu'est-ce qu'une nature morte ?",
                    [
                        "La représentation d'objets ou de fruits immobiles",
                        "La représentation d'une personne en mouvement",
                        "Un paysage de montagne",
                        "Un portrait de famille",
                    ],
                    0,
                ),
                mcq(
                    "Lequel de ces sujets est typique d'une nature morte ?",
                    [
                        "Une corbeille de fruits sur une table",
                        "Un enfant qui court",
                        "Une rivière qui coule",
                        "Un cheval au galop",
                    ],
                    0,
                ),
                mcq(
                    "Dans une nature morte, les objets sont :",
                    ["Immobiles et posés", "En train de bouger", "Toujours vivants", "Invisibles"],
                    0,
                ),
                mcq(
                    "Que doit bien observer l'artiste pour peindre une nature morte réaliste ?",
                    [
                        "La lumière et les ombres sur les objets",
                        "Le bruit des objets",
                        "La vitesse des objets",
                        "Le goût des fruits",
                    ],
                    0,
                ),
            ],
        ),
        # 8. La sculpture — tier 17, niveau 5
        L(
            17,
            5,
            "CM1 — La sculpture 🗿",
            "Un art en volume, que l'on peut voir de tous les côtés.",
            [
                mcq(
                    "Qu'est-ce qu'une sculpture ?",
                    [
                        "Une œuvre d'art en volume, en trois dimensions",
                        "Un dessin sur une feuille plate",
                        "Une chanson",
                        "Une photographie",
                    ],
                    0,
                ),
                mcq(
                    "Quel matériau est souvent utilisé pour sculpter ?",
                    ["Le marbre", "L'eau", "Le papier journal seul", "Le sable sec"],
                    0,
                ),
                mcq(
                    "Quel célèbre sculpteur a réalisé « Le Penseur » ?",
                    ["Auguste Rodin", "Claude Monet", "Vincent van Gogh", "Léonard de Vinci"],
                    0,
                ),
                mcq(
                    "Contrairement à un tableau, une sculpture peut être :",
                    [
                        "regardée de tous les côtés, en tournant autour",
                        "regardée seulement de face",
                        "seulement écoutée",
                        "seulement lue",
                    ],
                    0,
                ),
            ],
        ),
        # 9. Léonard de Vinci et la Renaissance — tier 18, niveau 5
        L(
            18,
            5,
            "CM1 — Léonard de Vinci et la Renaissance 🎭",
            "Un génie de la Renaissance, peintre et inventeur.",
            [
                mcq(
                    "Quel tableau très célèbre a peint Léonard de Vinci ?",
                    ["La Joconde", "La Nuit étoilée", "Le Cri", "Les Tournesols"],
                    0,
                ),
                mcq(
                    "À quelle grande période artistique appartient Léonard de Vinci ?",
                    ["La Renaissance", "La Préhistoire", "Le XXe siècle", "L'époque moderne"],
                    0,
                ),
                mcq(
                    "Léonard de Vinci était seulement peintre. Vrai ou faux ?",
                    [
                        "Faux, il était aussi inventeur et savant",
                        "Vrai, uniquement peintre",
                        "Vrai, uniquement musicien",
                        "Faux, il n'a jamais peint",
                    ],
                    0,
                ),
                mcq(
                    "Dans quel musée peut-on admirer aujourd'hui La Joconde ?",
                    [
                        "Le musée du Louvre, à Paris",
                        "La tour Eiffel",
                        "Le château de Versailles",
                        "Le musée d'Orsay uniquement",
                    ],
                    0,
                ),
            ],
        ),
        # 10. L'impressionnisme (Claude Monet) — tier 19, niveau 5
        L(
            19,
            5,
            "CM1 — L'impressionnisme et Monet 🌸",
            "Peindre la lumière et l'instant, à petites touches.",
            [
                mcq(
                    "Quel peintre est un grand maître de l'impressionnisme ?",
                    ["Claude Monet", "Michel-Ange", "Auguste Rodin", "Léonard de Vinci"],
                    0,
                ),
                mcq(
                    "Quelle célèbre série de tableaux de Monet représente des fleurs d'eau ?",
                    ["Les Nymphéas", "La Joconde", "Le Penseur", "La Nuit étoilée"],
                    0,
                ),
                mcq(
                    "Que cherchent surtout à peindre les impressionnistes ?",
                    [
                        "La lumière et les impressions du moment",
                        "Uniquement des lignes noires",
                        "Seulement des portraits de rois",
                        "Uniquement des statues",
                    ],
                    0,
                ),
                mcq(
                    "Les impressionnistes peignent souvent :",
                    [
                        "En plein air, dehors, dans la nature",
                        "Seulement la nuit",
                        "Uniquement dans une cave",
                        "Sans jamais regarder le sujet",
                    ],
                    0,
                ),
            ],
        ),
        # 11. Les familles d'instruments — tier 20, niveau 4
        L(
            20,
            4,
            "CM1 — Les familles d'instruments 🎻",
            "Cordes, vents et percussions dans l'orchestre.",
            [
                mcq(
                    "À quelle famille appartient le violon ?",
                    ["Les cordes", "Les vents", "Les percussions", "Les claviers électriques"],
                    0,
                ),
                mcq(
                    "À quelle famille appartient la flûte ?",
                    ["Les vents", "Les cordes", "Les percussions", "Les cuivres frottés"],
                    0,
                ),
                mcq(
                    "À quelle famille appartient le tambour ?",
                    ["Les percussions", "Les cordes", "Les vents", "Les claviers"],
                    0,
                ),
                mcq(
                    "Comment produit-on le son d'un instrument à vent ?",
                    [
                        "En soufflant de l'air dedans",
                        "En frottant des cordes",
                        "En le frappant seulement",
                        "En le posant par terre",
                    ],
                    0,
                ),
            ],
        ),
        # 12. Le rythme et le tempo — tier 21, niveau 5
        L(
            21,
            5,
            "CM1 — Le rythme et le tempo 🥁",
            "La pulsation de la musique : vite ou lentement.",
            [
                mcq(
                    "Que désigne le tempo en musique ?",
                    [
                        "La vitesse de la musique",
                        "La couleur des notes",
                        "Le nom du chanteur",
                        "La taille de l'instrument",
                    ],
                    0,
                ),
                mcq(
                    "Un morceau au tempo rapide est :",
                    ["Joué vite", "Joué très lentement", "Toujours silencieux", "Toujours triste"],
                    0,
                ),
                mcq(
                    "Le rythme, c'est :",
                    [
                        "l'organisation des sons courts et longs dans le temps",
                        "la couleur du piano",
                        "le prix d'un instrument",
                        "le nombre de musiciens",
                    ],
                    0,
                ),
                mcq(
                    "Que fait-on souvent avec le pied ou les mains pour suivre le rythme ?",
                    [
                        "On bat la pulsation (on tape en mesure)",
                        "On ferme les yeux sans bouger",
                        "On chante à l'envers",
                        "On arrête la musique",
                    ],
                    0,
                ),
            ],
        ),
        # 13. Les nuances musicales (fort / doux) — tier 22, niveau 4
        L(
            22,
            4,
            "CM1 — Les nuances musicales 🔊",
            "Jouer fort ou doucement : forte et piano.",
            [
                mcq(
                    "Que veut dire jouer « forte » en musique ?",
                    ["Jouer fort", "Jouer doucement", "Jouer très vite", "Arrêter de jouer"],
                    0,
                ),
                mcq(
                    "Que veut dire jouer « piano » comme nuance en musique ?",
                    ["Jouer doucement", "Jouer très fort", "Jouer très vite", "Jouer faux"],
                    0,
                ),
                mcq(
                    "Les nuances en musique servent à régler :",
                    [
                        "l'intensité du son (fort ou doux)",
                        "la couleur du papier",
                        "le nombre de musiciens",
                        "la longueur du concert",
                    ],
                    0,
                ),
                mcq(
                    "Passer petit à petit de doux à fort s'appelle un :",
                    ["crescendo", "silence", "refrain", "tempo lent"],
                    0,
                ),
            ],
        ),
        # 14. Lire les notes (do, ré, mi…) — tier 23, niveau 5
        L(
            23,
            5,
            "CM1 — Lire les notes de musique 🎵",
            "La gamme do ré mi fa sol la si do.",
            [
                mcq(
                    "Combien y a-t-il de notes différentes dans la gamme de base ?",
                    ["Sept", "Cinq", "Huit sans répétition", "Douze"],
                    0,
                ),
                mcq(
                    "Quelle note vient juste après « do » dans la gamme ?",
                    ["Ré", "Mi", "Sol", "Si"],
                    0,
                ),
                mcq(
                    "Quelle est la dernière note de la gamme do ré mi fa sol la si… ?",
                    ["Do", "Fa", "Ré", "La"],
                    0,
                ),
                mcq(
                    "Sur quoi écrit-on les notes de musique ?",
                    ["Sur une portée (cinq lignes)", "Sur une seule ligne", "Sur un cercle", "Sur une grille de mots"],
                    0,
                ),
            ],
        ),
        # 15. L'art à travers l'histoire — tier 24, niveau 5
        L(
            24,
            5,
            "CM1 — L'art à travers l'histoire ⏳",
            "Des grottes préhistoriques aux grands musées.",
            [
                mcq(
                    "Où les hommes préhistoriques peignaient-ils souvent des animaux ?",
                    [
                        "Sur les parois des grottes",
                        "Sur des toiles vendues au marché",
                        "Sur des écrans",
                        "Sur du papier imprimé",
                    ],
                    0,
                ),
                mcq(
                    "Quelle célèbre grotte française contient des peintures préhistoriques ?",
                    ["La grotte de Lascaux", "La grotte de Monet", "La grotte du Louvre", "La grotte de Vinci"],
                    0,
                ),
                mcq(
                    "À la Renaissance, l'art s'est surtout développé :",
                    ["en Italie", "au pôle Nord", "dans le désert du Sahara", "sur la Lune"],
                    0,
                ),
                mcq(
                    "Où peut-on aujourd'hui admirer et conserver de nombreuses œuvres d'art ?",
                    [
                        "Dans les musées",
                        "Uniquement dans la rue",
                        "Seulement à la télévision",
                        "Seulement dans les livres d'école",
                    ],
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CM1 Arts "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
