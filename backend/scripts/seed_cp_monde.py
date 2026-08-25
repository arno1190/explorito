"""Seed CP Questionner le monde — le vivant, la matière, les objets (programme officiel).

15 leçons (paliers 1..15), 4 exercices chacune. Contenu simple et concret pour
des enfants de CP (~6 ans). Réponses scientifiquement correctes par construction.

Idempotent par (parcours, nom de leçon).

Usage:
    DATABASE_URL=... uv run python scripts/seed_cp_monde.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, shuffle_options, theme

from app.core.database import SessionLocal

LEVEL = "cp"
SLUG = "monde"


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
        # 1. Le vivant et le non-vivant
        L(
            1,
            1,
            "CP — Le vivant et le non-vivant 🌱",
            "Reconnaître ce qui est vivant.",
            [
                mcq("Lequel est vivant ?", ["Un chien", "Un caillou", "Une table"], 0, emoji="🐶"),
                mcq("Lequel n'est PAS vivant ?", ["Une fleur", "Un vélo", "Un oiseau"], 1, emoji="🚲"),
                mcq(
                    "Que font tous les êtres vivants ?",
                    ["Ils grandissent", "Ils restent toujours pareils", "Ils sont fabriqués en usine"],
                    0,
                ),
                mcq("Un arbre est…", ["vivant", "non-vivant", "un objet"], 0, emoji="🌳"),
            ],
        ),
        # 2. Où vivent les animaux
        L(
            2,
            1,
            "CP — Où vivent les animaux 🐄",
            "La ferme, la forêt et la mer.",
            [
                mcq("Où vit la vache ?", ["à la ferme", "dans la mer", "dans le désert"], 0, emoji="🐄"),
                mcq("Quel animal vit dans la mer ?", ["le poisson", "la poule", "le lapin"], 0, emoji="🐟"),
                mcq("Où vit l'écureuil ?", ["dans la forêt", "dans la mer", "sous l'eau"], 0, emoji="🐿️"),
                mcq("Quel animal vit à la ferme ?", ["le cochon", "le requin", "le lion"], 0, emoji="🐷"),
            ],
        ),
        # 3. Ce que mangent les animaux
        L(
            3,
            1,
            "CP — Ce que mangent les animaux 🍖",
            "Herbivore ou carnivore.",
            [
                mcq("La vache mange surtout…", ["de l'herbe", "de la viande", "des cailloux"], 0, emoji="🌿"),
                mcq("Un animal qui mange de l'herbe est…", ["herbivore", "carnivore", "un légume"], 0),
                mcq("Le lion mange de la viande, il est…", ["carnivore", "herbivore", "une plante"], 0, emoji="🦁"),
                mcq("Que mange le lapin ?", ["des carottes et de l'herbe", "de la viande", "du métal"], 0, emoji="🐰"),
            ],
        ),
        # 4. Les parties du corps
        L(
            4,
            1,
            "CP — Les parties du corps 🧍",
            "Connaître son corps.",
            [
                mcq("Avec quoi marche-t-on ?", ["les jambes", "les oreilles", "le nez"], 0, emoji="🦵"),
                mcq("Combien de mains as-tu ?", ["2", "1", "3"], 0, emoji="✋"),
                mcq("Où se trouvent les doigts ?", ["au bout des mains", "sur la tête", "dans le dos"], 0),
                mcq("Avec quoi attrape-t-on un objet ?", ["les mains", "les pieds", "les genoux"], 0, emoji="🤲"),
            ],
        ),
        # 5. Les cinq sens
        L(
            5,
            1,
            "CP — Les cinq sens 👀",
            "La vue, l'ouïe, l'odorat, le goût et le toucher.",
            [
                mcq("Combien avons-nous de sens ?", ["5", "3", "10"], 0),
                mcq("Avec quoi voit-on ?", ["les yeux", "les oreilles", "le nez"], 0, emoji="👀"),
                mcq("Avec quoi entend-on ?", ["les oreilles", "les yeux", "les pieds"], 0, emoji="👂"),
                mcq("Avec quoi sent-on les odeurs ?", ["le nez", "la langue", "les mains"], 0, emoji="👃"),
            ],
        ),
        # 6. De la graine à la fleur
        L(
            6,
            1,
            "CP — De la graine à la fleur 🌻",
            "Comment pousse une plante.",
            [
                mcq(
                    "Que met-on dans la terre pour faire pousser une plante ?",
                    ["une graine", "un caillou", "un jouet"],
                    0,
                    emoji="🌰",
                ),
                mcq("D'une graine, il pousse d'abord…", ["une petite tige verte", "une voiture", "un animal"], 0),
                mcq(
                    "Qu'est-ce qui apparaît sur la plante à la fin ?",
                    ["une fleur", "une pierre", "du plastique"],
                    0,
                    emoji="🌼",
                ),
                mcq(
                    "Pour pousser, la graine doit être…",
                    ["dans la terre", "dans une boîte fermée", "au congélateur"],
                    0,
                ),
            ],
        ),
        # 7. Les besoins des plantes
        L(
            7,
            1,
            "CP — Les besoins des plantes 💧",
            "L'eau et la lumière.",
            [
                mcq(
                    "De quoi une plante a-t-elle besoin pour vivre ?",
                    ["d'eau et de lumière", "de bonbons", "de télévision"],
                    0,
                ),
                mcq(
                    "Que se passe-t-il si on n'arrose jamais une plante ?",
                    ["elle sèche et meurt", "elle grandit plus vite", "elle devient bleue"],
                    0,
                ),
                mcq("Les plantes ont besoin de la lumière du…", ["soleil", "réfrigérateur", "téléphone"], 0, emoji="☀️"),
                mcq("Pour arroser une plante, on lui donne…", ["de l'eau", "du sable", "du sel"], 0, emoji="💧"),
            ],
        ),
        # 8. Bien manger
        L(
            8,
            1,
            "CP — Bien manger 🍎",
            "Une alimentation équilibrée.",
            [
                mcq(
                    "Quel aliment est bon pour la santé ?",
                    ["les fruits et les légumes", "les bonbons à tous les repas", "les chips seulement"],
                    0,
                    emoji="🍎",
                ),
                mcq(
                    "Que faut-il boire chaque jour pour être en forme ?",
                    ["de l'eau", "du soda à volonté", "rien"],
                    0,
                    emoji="🥤",
                ),
                mcq("Le fromage et le yaourt sont faits avec…", ["du lait", "du sable", "du bois"], 0, emoji="🧀"),
                mcq(
                    "Combien de repas prend-on en général par jour ?",
                    ["environ 3 ou 4", "un seul par semaine", "vingt"],
                    0,
                ),
            ],
        ),
        # 9. L'hygiène et la santé
        L(
            9,
            1,
            "CP — L'hygiène et la santé 🪥",
            "Se laver, les dents, le sommeil.",
            [
                mcq(
                    "Que faut-il faire avant de manger ?",
                    ["se laver les mains", "se salir les mains", "rien"],
                    0,
                    emoji="🧼",
                ),
                mcq(
                    "Combien de fois par jour faut-il se brosser les dents ?",
                    ["au moins 2 fois", "jamais", "une fois par mois"],
                    0,
                    emoji="🪥",
                ),
                mcq(
                    "Pour être en forme, il faut bien…",
                    ["dormir la nuit", "rester debout toute la nuit", "ne jamais bouger"],
                    0,
                    emoji="😴",
                ),
                mcq(
                    "Qu'est-ce qui abîme les dents ?", ["manger trop de sucre", "boire de l'eau", "manger une pomme"], 0
                ),
            ],
        ),
        # 10. Le jour, la nuit et le Soleil
        L(
            10,
            1,
            "CP — Le jour, la nuit et le Soleil ☀️",
            "Quand il fait jour et quand il fait nuit.",
            [
                mcq(
                    "Quand fait-il jour ?",
                    ["quand le soleil brille", "au milieu de la nuit", "quand on dort la nuit"],
                    0,
                ),
                mcq(
                    "Qu'est-ce qui éclaire la Terre le jour ?",
                    ["le Soleil", "la Lune", "une lampe de poche"],
                    0,
                    emoji="☀️",
                ),
                mcq(
                    "La nuit, dans le ciel, on peut voir…",
                    ["la Lune et les étoiles", "le Soleil", "un arc-en-ciel"],
                    0,
                    emoji="🌙",
                ),
                mcq("Le matin, le soleil…", ["se lève", "disparaît pour toujours", "devient bleu"], 0),
            ],
        ),
        # 11. La météo et les saisons
        L(
            11,
            2,
            "CP — La météo et les saisons 🌦️",
            "Soleil, pluie, neige et vent.",
            [
                mcq(
                    "Quel temps fait-il quand des gouttes tombent du ciel ?",
                    ["il pleut", "il neige", "il fait beau"],
                    0,
                    emoji="🌧️",
                ),
                mcq("En hiver, il peut tomber…", ["de la neige", "du sable", "des feuilles vertes"], 0, emoji="❄️"),
                mcq("Combien y a-t-il de saisons dans l'année ?", ["4", "2", "12"], 0),
                mcq(
                    "Quand le soleil brille et qu'il fait chaud, c'est souvent…",
                    ["l'été", "l'hiver", "la nuit"],
                    0,
                    emoji="🌞",
                ),
            ],
        ),
        # 12. L'eau : liquide et glace
        L(
            12,
            2,
            "CP — L'eau : liquide et glace 💧",
            "L'eau peut geler et fondre.",
            [
                mcq(
                    "Quand on met de l'eau au congélateur, elle devient…",
                    ["de la glace", "du sable", "du feu"],
                    0,
                    emoji="🧊",
                ),
                mcq("La glace, c'est de l'eau…", ["gelée (très froide)", "bouillante", "sucrée"], 0),
                mcq(
                    "Que devient un glaçon qu'on laisse au soleil ?",
                    ["il fond et redevient de l'eau", "il grossit", "il devient une pierre"],
                    0,
                ),
                mcq("L'eau qui coule du robinet est…", ["liquide", "solide", "en bois"], 0, emoji="🚰"),
            ],
        ),
        # 13. Les matériaux
        L(
            13,
            2,
            "CP — Les matériaux 🪵",
            "Le bois, le verre, le métal et le plastique.",
            [
                mcq("Une fenêtre est faite en…", ["verre", "chocolat", "eau"], 0, emoji="🪟"),
                mcq("Un tronc d'arbre donne le…", ["bois", "métal", "verre"], 0, emoji="🪵"),
                mcq(
                    "Quel matériau est dur et brille, comme une cuillère ?",
                    ["le métal", "le papier", "le tissu"],
                    0,
                    emoji="🥄",
                ),
                mcq(
                    "Une bouteille légère qui ne se casse pas facilement est souvent en…",
                    ["plastique", "verre", "bois"],
                    0,
                ),
            ],
        ),
        # 14. Les objets techniques et la sécurité
        L(
            14,
            2,
            "CP — Les objets et la sécurité ⚡",
            "L'électricité et les dangers.",
            [
                mcq(
                    "Peut-on toucher une prise électrique avec les doigts ?",
                    ["non, c'est dangereux", "oui, c'est amusant", "oui, avec de l'eau"],
                    0,
                    emoji="⚡",
                ),
                mcq(
                    "Près d'une plaque chaude, il faut…",
                    ["faire très attention", "y mettre les mains", "jouer avec"],
                    0,
                    emoji="🔥",
                ),
                mcq(
                    "Les ciseaux doivent être utilisés…",
                    ["avec précaution", "en courant", "les yeux fermés"],
                    0,
                    emoji="✂️",
                ),
                mcq(
                    "Si un appareil électrique tombe dans l'eau, il faut…",
                    ["prévenir un adulte", "le prendre avec les mains mouillées", "sauter dans l'eau"],
                    0,
                ),
            ],
        ),
        # 15. Protéger la nature
        L(
            15,
            2,
            "CP — Protéger la nature ♻️",
            "Trier ses déchets et ne pas gaspiller.",
            [
                mcq(
                    "Où jette-t-on ses déchets ?",
                    ["à la poubelle", "par terre dans la rue", "dans la rivière"],
                    0,
                    emoji="🗑️",
                ),
                mcq(
                    "Trier les déchets permet de…",
                    ["recycler et protéger la nature", "salir la planète", "gaspiller"],
                    0,
                    emoji="♻️",
                ),
                mcq(
                    "Pour économiser l'eau, il faut…",
                    ["fermer le robinet quand on se brosse les dents", "laisser couler l'eau", "gaspiller l'eau"],
                    0,
                    emoji="💧",
                ),
                mcq(
                    "Quand on quitte une pièce, on peut…",
                    ["éteindre la lumière", "tout laisser allumé", "casser la lampe"],
                    0,
                    emoji="💡",
                ),
            ],
        ),
    ]


def main(dry_run: bool = False) -> int:
    themes = shuffle_options(curriculum(), salt="cp-monde")
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CP Monde "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
