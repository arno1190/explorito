"""Seed CE2 Arts — couverture du programme (arts plastiques & musique).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction ;
œuvres/artistes du domaine public ou faits établis.

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce2_arts.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, theme

from app.core.database import SessionLocal

LEVEL = "ce2"
SLUG = "arts"


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
        # 1. Les couleurs primaires — tier 10, niveau 3
        L(
            10,
            3,
            "CE2 — Les couleurs primaires 🎨",
            "Rouge, jaune, bleu : les trois couleurs de base.",
            [
                mcq(
                    "Quelles sont les trois couleurs primaires ?",
                    ["Rouge, jaune, bleu", "Vert, orange, violet", "Noir, blanc, gris", "Rose, marron, or"],
                    0,
                ),
                mcq(
                    "Combien y a-t-il de couleurs primaires ?",
                    ["Deux", "Trois", "Quatre", "Cinq"],
                    1,
                ),
                mcq(
                    "Peut-on fabriquer une couleur primaire en mélangeant d'autres couleurs ?",
                    [
                        "Non, on ne peut pas la fabriquer",
                        "Oui, avec du vert et du violet",
                        "Oui, avec du blanc",
                        "Oui, avec du noir",
                    ],
                    0,
                ),
                mcq(
                    "Parmi ces couleurs, laquelle est une couleur primaire ?",
                    ["Le vert", "L'orange", "Le bleu", "Le violet"],
                    2,
                ),
            ],
        ),
        # 2. Les couleurs secondaires — tier 11, niveau 3
        L(
            11,
            3,
            "CE2 — Les couleurs secondaires 🖌️",
            "Mélanger deux couleurs primaires pour en créer une nouvelle.",
            [
                mcq(
                    "Que donne le mélange du bleu et du jaune ?",
                    ["Du violet", "Du vert", "De l'orange", "Du marron"],
                    1,
                ),
                mcq(
                    "Que donne le mélange du rouge et du jaune ?",
                    ["De l'orange", "Du vert", "Du violet", "Du gris"],
                    0,
                ),
                mcq(
                    "Que donne le mélange du rouge et du bleu ?",
                    ["Du vert", "De l'orange", "Du violet", "Du jaune"],
                    2,
                ),
                mcq(
                    "Quelles sont les trois couleurs secondaires ?",
                    ["Rouge, jaune, bleu", "Orange, vert, violet", "Noir, blanc, gris", "Rose, or, argent"],
                    1,
                ),
            ],
        ),
        # 3. Les couleurs chaudes et froides — tier 12, niveau 3
        L(
            12,
            3,
            "CE2 — Couleurs chaudes et froides 🔥",
            "Reconnaître les couleurs qui réchauffent et celles qui rafraîchissent.",
            [
                mcq(
                    "Le bleu est une couleur…",
                    ["Chaude", "Froide", "Primaire uniquement", "Secondaire uniquement"],
                    1,
                ),
                mcq(
                    "Le rouge est une couleur…",
                    ["Froide", "Chaude", "Neutre", "Complémentaire"],
                    1,
                ),
                mcq(
                    "Quelle couleur fait penser au feu et au soleil ?",
                    ["Le bleu", "Le vert", "L'orange", "Le violet"],
                    2,
                ),
                mcq(
                    "Quelle couleur fait penser à la mer et à la glace ?",
                    ["Le rouge", "Le bleu", "L'orange", "Le jaune"],
                    1,
                ),
            ],
        ),
        # 4. Les couleurs complémentaires — tier 13, niveau 4
        L(
            13,
            4,
            "CE2 — Les couleurs complémentaires 🌈",
            "Les couleurs opposées sur le cercle chromatique.",
            [
                mcq(
                    "Quelle est la couleur complémentaire du rouge ?",
                    ["Le bleu", "Le vert", "Le jaune", "L'orange"],
                    1,
                ),
                mcq(
                    "Quelle est la couleur complémentaire du bleu ?",
                    ["L'orange", "Le vert", "Le violet", "Le rouge"],
                    0,
                ),
                mcq(
                    "Quelle est la couleur complémentaire du jaune ?",
                    ["Le rouge", "Le vert", "Le violet", "Le bleu"],
                    2,
                ),
                mcq(
                    "Sur le cercle chromatique, deux couleurs complémentaires sont…",
                    [
                        "Placées l'une à côté de l'autre",
                        "Placées l'une en face de l'autre",
                        "Toujours identiques",
                        "Toujours primaires",
                    ],
                    1,
                ),
            ],
        ),
        # 5. Les nuances (clair et foncé) — tier 14, niveau 3
        L(
            14,
            3,
            "CE2 — Les nuances : clair et foncé 🌗",
            "Éclaircir et foncer une couleur pour créer des nuances.",
            [
                mcq(
                    "Pour éclaircir une couleur, on ajoute…",
                    ["Du noir", "Du blanc", "Du rouge", "Du bleu"],
                    1,
                ),
                mcq(
                    "Pour foncer une couleur, on ajoute…",
                    ["Du blanc", "Du jaune", "Du noir", "De l'eau"],
                    2,
                ),
                mcq(
                    "Le bleu ciel et le bleu marine sont deux…",
                    [
                        "Couleurs primaires différentes",
                        "Nuances de bleu",
                        "Couleurs complémentaires",
                        "Couleurs chaudes",
                    ],
                    1,
                ),
                mcq(
                    "Un passage progressif du clair au foncé s'appelle un…",
                    ["Dégradé", "Contour", "Contraste", "Mélange primaire"],
                    0,
                ),
            ],
        ),
        # 6. Les lignes et les formes — tier 15, niveau 3
        L(
            15,
            3,
            "CE2 — Les lignes et les formes ✏️",
            "Lignes droites, courbes et formes géométriques.",
            [
                mcq(
                    "Combien de côtés a un triangle ?",
                    ["Deux", "Trois", "Quatre", "Cinq"],
                    1,
                ),
                mcq(
                    "Quelle forme n'a aucun angle ?",
                    ["Le carré", "Le triangle", "Le cercle", "Le rectangle"],
                    2,
                ),
                mcq(
                    "Une ligne qui tourne et n'est pas droite est une ligne…",
                    ["Droite", "Courbe", "Verticale", "Pointillée"],
                    1,
                ),
                mcq(
                    "Combien de côtés a un carré ?",
                    ["Trois", "Quatre", "Cinq", "Six"],
                    1,
                ),
            ],
        ),
        # 7. Le portrait — tier 16, niveau 4
        L(
            16,
            4,
            "CE2 — Le portrait 👩‍🎨",
            "Représenter le visage et une personne en peinture.",
            [
                mcq(
                    "Un portrait représente…",
                    ["Un paysage", "Une personne", "Un objet seul", "Une maison"],
                    1,
                ),
                mcq(
                    "Comment appelle-t-on un portrait de soi-même ?",
                    ["Un paysage", "Un autoportrait", "Une nature morte", "Une sculpture"],
                    1,
                ),
                mcq(
                    "Qui a peint le célèbre portrait de La Joconde ?",
                    ["Claude Monet", "Vincent van Gogh", "Léonard de Vinci", "Pablo Picasso"],
                    2,
                ),
                mcq(
                    "Vincent van Gogh est connu pour avoir peint de nombreux…",
                    ["Paysages de mer uniquement", "Autoportraits", "Portraits de rois", "Sculptures"],
                    1,
                ),
            ],
        ),
        # 8. Le paysage en peinture — tier 17, niveau 3
        L(
            17,
            3,
            "CE2 — Le paysage en peinture 🏞️",
            "Peindre la nature : ciel, terre et ligne d'horizon.",
            [
                mcq(
                    "Un paysage représente surtout…",
                    ["Un visage", "La nature ou un lieu", "Un seul objet", "Un animal en gros plan"],
                    1,
                ),
                mcq(
                    "La ligne qui sépare le ciel et la terre s'appelle la…",
                    ["Ligne d'horizon", "Ligne courbe", "Ligne brisée", "Ligne du milieu"],
                    0,
                ),
                mcq(
                    "Claude Monet était un peintre…",
                    ["De la Préhistoire", "Impressionniste", "Égyptien", "Sculpteur"],
                    1,
                ),
                mcq(
                    "Dans un paysage marin, on peint surtout…",
                    ["La montagne enneigée", "La mer", "Une forêt de sapins", "Un désert"],
                    1,
                ),
            ],
        ),
        # 9. La sculpture — tier 18, niveau 4
        L(
            18,
            4,
            "CE2 — La sculpture 🗿",
            "L'art en volume : matériaux et grands sculpteurs.",
            [
                mcq(
                    "Une sculpture est une œuvre…",
                    [
                        "Plate, en deux dimensions",
                        "En volume, en trois dimensions",
                        "Faite seulement de peinture",
                        "Faite seulement de papier",
                    ],
                    1,
                ),
                mcq(
                    "Quel matériau peut-on utiliser pour faire une sculpture ?",
                    ["Le marbre", "L'eau", "La lumière", "Le vent"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on l'artiste qui fait des sculptures ?",
                    ["Un peintre", "Un sculpteur", "Un musicien", "Un photographe"],
                    1,
                ),
                mcq(
                    "Qui a réalisé la célèbre sculpture « Le Penseur » ?",
                    ["Auguste Rodin", "Claude Monet", "Léonard de Vinci", "Vincent van Gogh"],
                    0,
                ),
            ],
        ),
        # 10. Léonard de Vinci et la Renaissance — tier 19, niveau 4
        L(
            19,
            4,
            "CE2 — Léonard de Vinci et la Renaissance 🖼️",
            "Un grand artiste italien et sa grande époque.",
            [
                mcq(
                    "Quelle célèbre œuvre a peint Léonard de Vinci ?",
                    ["La Nuit étoilée", "La Joconde", "Les Nymphéas", "Le Penseur"],
                    1,
                ),
                mcq(
                    "Léonard de Vinci était un artiste…",
                    ["Français", "Italien", "Égyptien", "Espagnol"],
                    1,
                ),
                mcq(
                    "Dans quel musée peut-on voir La Joconde aujourd'hui ?",
                    ["Le musée du Louvre, à Paris", "Le château de Versailles", "La tour Eiffel", "Le musée d'Orsay"],
                    0,
                ),
                mcq(
                    "La Renaissance est une grande période de l'histoire de…",
                    ["La musique seulement", "L'art", "La cuisine", "Le sport"],
                    1,
                ),
            ],
        ),
        # 11. Les familles d'instruments — tier 20, niveau 3
        L(
            20,
            3,
            "CE2 — Les familles d'instruments 🎻",
            "Cordes, vents et percussions : classer les instruments.",
            [
                mcq(
                    "À quelle famille appartient le violon ?",
                    ["Les percussions", "Les cordes", "Les vents", "Les claviers"],
                    1,
                ),
                mcq(
                    "La flûte est un instrument à…",
                    ["Cordes", "Vent", "Percussion", "Pédales"],
                    1,
                ),
                mcq(
                    "Le tambour fait partie de la famille des…",
                    ["Cordes", "Vents", "Percussions", "Cuivres"],
                    2,
                ),
                mcq(
                    "Quel instrument fait partie de la famille des cordes ?",
                    ["La trompette", "La guitare", "Le tambour", "La flûte"],
                    1,
                ),
            ],
        ),
        # 12. Le rythme et le tempo — tier 21, niveau 3
        L(
            21,
            3,
            "CE2 — Le rythme et le tempo ⏱️",
            "Musique rapide ou lente : découvrir le tempo.",
            [
                mcq(
                    "Le tempo, c'est la vitesse d'une musique. Un tempo rapide, c'est une musique…",
                    ["Très lente", "Rapide", "Silencieuse", "Très douce"],
                    1,
                ),
                mcq(
                    "Une musique jouée avec un tempo lent est…",
                    ["Rapide", "Lente", "Forte", "Aiguë"],
                    1,
                ),
                mcq(
                    "Le rythme, c'est l'organisation des sons dans…",
                    ["Le temps", "La couleur", "L'espace de la feuille", "Le silence total"],
                    0,
                ),
                mcq(
                    "Quand une musique accélère, son tempo devient de plus en plus…",
                    ["Lent", "Rapide", "Doux", "Grave"],
                    1,
                ),
            ],
        ),
        # 13. Les nuances en musique — tier 22, niveau 4
        L(
            22,
            4,
            "CE2 — Les nuances en musique 🔊",
            "Jouer fort ou doucement : forte, piano, crescendo.",
            [
                mcq(
                    "En musique, les nuances concernent surtout…",
                    ["La vitesse", "Le volume (fort ou doux)", "La couleur", "Le nombre de musiciens"],
                    1,
                ),
                mcq(
                    "Le mot « forte » veut dire qu'il faut jouer…",
                    ["Doucement", "Fort", "Lentement", "Vite"],
                    1,
                ),
                mcq(
                    "Le mot « piano », en musique, veut dire qu'il faut jouer…",
                    ["Fort", "Doucement", "Rapidement", "Faux"],
                    1,
                ),
                mcq(
                    "Un « crescendo », c'est quand la musique devient de plus en plus…",
                    ["Douce", "Forte", "Lente", "Rapide"],
                    1,
                ),
            ],
        ),
        # 14. Les techniques — tier 23, niveau 4
        L(
            23,
            4,
            "CE2 — Les techniques de l'artiste 🧵",
            "Collage, modelage, gravure et peinture.",
            [
                mcq(
                    "Coller des morceaux de papier pour faire une image, c'est le…",
                    ["Modelage", "Collage", "Dessin", "Tissage"],
                    1,
                ),
                mcq(
                    "Façonner de l'argile avec ses mains, c'est le…",
                    ["Collage", "Modelage", "Gravure", "Coloriage"],
                    1,
                ),
                mcq(
                    "Utiliser un pinceau et des couleurs, c'est la…",
                    ["Gravure", "Sculpture", "Peinture", "Photographie"],
                    2,
                ),
                mcq(
                    "Creuser une surface avec un outil pour ensuite l'imprimer, c'est la…",
                    ["Peinture", "Gravure", "Collage", "Modelage"],
                    1,
                ),
            ],
        ),
        # 15. L'art à travers l'histoire — tier 24, niveau 4
        L(
            24,
            4,
            "CE2 — L'art à travers l'histoire 🏛️",
            "De la Préhistoire à aujourd'hui, en passant par l'Égypte.",
            [
                mcq(
                    "Les peintures d'animaux de la grotte de Lascaux datent de la…",
                    ["Renaissance", "Préhistoire", "Époque des Égyptiens", "Époque d'aujourd'hui"],
                    1,
                ),
                mcq(
                    "Les anciens Égyptiens ont construit de grands monuments : les…",
                    ["Cathédrales", "Pyramides", "Gratte-ciel", "Châteaux forts"],
                    1,
                ),
                mcq(
                    "Dans quel pays se trouve la célèbre grotte de Lascaux ?",
                    ["En Italie", "En France", "En Égypte", "En Espagne"],
                    1,
                ),
                mcq(
                    "L'art réalisé de nos jours, à notre époque, s'appelle l'art…",
                    ["Préhistorique", "Contemporain", "Égyptien", "De la Renaissance"],
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE2 Arts "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
