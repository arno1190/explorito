"""Seed CM1 Orthographe — programme avancé (niveau élevé).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_cm1_orthographe.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, theme

from app.core.database import SessionLocal

LEVEL = "cm1"
SLUG = "orthographe"


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
        # --- Tier 10 — Accord sujet-verbe : cas difficiles (niveau 5) --------- #
        L(
            10,
            5,
            "CM1 — Accord sujet-verbe : cas difficiles 🔗",
            "Accorder le verbe même quand le sujet est inversé, éloigné ou composé.",
            [
                mcq(
                    "« Que ___ tes parents le dimanche ? » Choisis la bonne forme du verbe faire.",
                    ["font", "fait", "fais"],
                    0,
                    explanation="Sujet inversé « tes parents » (pluriel) → font.",
                ),
                fill_blanks(
                    "Le sujet est éloigné du verbe. Écris jouer au présent.",
                    "Les élèves de la classe de madame Martin ___ dans la grande cour.",
                    ["jouent"],
                    explanation="Le sujet est « les élèves » (pluriel), pas « la classe ».",
                ),
                mcq(
                    "« Sur les branches ___ les oiseaux. » Choisis le verbe chanter.",
                    ["chante", "chantent", "chantes"],
                    1,
                    explanation="Sujet inversé « les oiseaux » (pluriel) → chantent.",
                ),
                mcq(
                    "« Toi et moi ___ au cinéma. » Choisis le verbe aller.",
                    ["va", "vont", "allons"],
                    2,
                    explanation="« Toi et moi » = nous → allons.",
                ),
            ],
        ),
        # --- Tier 11 — L'accord de l'adjectif (niveau 4) --------------------- #
        L(
            11,
            4,
            "CM1 — L'accord de l'adjectif 🎨",
            "Accorder l'adjectif en genre et en nombre avec le nom.",
            [
                mcq(
                    "« des fleurs ___ » — accorde l'adjectif blanc.",
                    ["blanc", "blanche", "blanches"],
                    2,
                    explanation="« fleurs » est féminin pluriel → blanches.",
                ),
                fill_blanks(
                    "Accorde l'adjectif rapide.",
                    "Les deux chevaux sont très ___.",
                    ["rapides"],
                    explanation="« chevaux » est pluriel → rapides.",
                ),
                mcq(
                    "« une veste ___ » — accorde l'adjectif neuf.",
                    ["neuf", "neuve", "neufs"],
                    1,
                    explanation="Féminin singulier : neuf → neuve.",
                ),
                mcq(
                    "« un manteau et une écharpe ___ » — accorde l'adjectif gris.",
                    ["gris", "grise", "grises"],
                    0,
                    explanation="Genres mélangés (masculin + féminin) → masculin pluriel : gris.",
                ),
            ],
        ),
        # --- Tier 12 — Le participe passé avec être (niveau 5) --------------- #
        L(
            12,
            5,
            "CM1 — Le participe passé avec être 🚪",
            "Avec être, le participe passé s'accorde avec le sujet.",
            [
                mcq(
                    "« Elle est ___ tôt ce matin. » Accorde le participe passé de partir.",
                    ["parti", "partie", "partis"],
                    1,
                    explanation="Avec être, on accorde avec le sujet « elle » → partie.",
                ),
                mcq(
                    "« Les filles sont ___ à la fête. » Accorde le participe passé de venir.",
                    ["venu", "venus", "venues"],
                    2,
                    explanation="Sujet féminin pluriel → venues.",
                ),
                fill_blanks(
                    "Accorde le participe passé de descendre (avec être).",
                    "Les voyageurs sont ___ du train à l'heure.",
                    ["descendus"],
                    explanation="Sujet masculin pluriel « les voyageurs » → descendus.",
                ),
                mcq(
                    "« Ma sœur et ma mère sont ___ à la maison. » Accorde rentrer.",
                    ["rentré", "rentrés", "rentrées"],
                    2,
                    explanation="Deux sujets féminins → féminin pluriel : rentrées.",
                ),
            ],
        ),
        # --- Tier 13 — Le participe passé avec avoir (niveau 5) -------------- #
        L(
            13,
            5,
            "CM1 — Le participe passé avec avoir 🤝",
            "Avec avoir, le participe passé ne s'accorde pas avec le sujet.",
            [
                mcq(
                    "« Elles ont ___ une pomme. » Accorde le participe passé de manger.",
                    ["mangé", "mangés", "mangées"],
                    0,
                    explanation="Avec avoir, pas d'accord avec le sujet : mangé.",
                ),
                mcq(
                    "« Les enfants ont ___ leurs devoirs. » Accorde finir.",
                    ["fini", "finis", "finies"],
                    0,
                    explanation="Avec avoir et le COD placé après, le participe reste invariable : fini.",
                ),
                mcq(
                    "Avec l'auxiliaire avoir, le participe passé s'accorde-t-il avec le sujet ?",
                    [
                        "Oui, toujours avec le sujet",
                        "Non, il reste invariable (sans COD placé avant)",
                        "Seulement au féminin",
                    ],
                    1,
                    explanation="Avec avoir, on n'accorde jamais avec le sujet.",
                ),
                fill_blanks(
                    "Accorde le participe passé de perdre (avec avoir).",
                    "Les filles ont ___ leurs clés dans le jardin.",
                    ["perdu"],
                    explanation="Avec avoir et le COD après le verbe, le participe reste invariable : perdu.",
                ),
            ],
        ),
        # --- Tier 14 — Le pluriel des noms (niveau 4) ------------------------ #
        L(
            14,
            4,
            "CM1 — Le pluriel des noms 📚",
            "Pluriels en -s, -x, -aux et les exceptions à connaître.",
            [
                mcq(
                    "Quel est le pluriel de « cheval » ?",
                    ["chevals", "chevaux", "chevales"],
                    1,
                    explanation="Les noms en -al font -aux : chevaux.",
                ),
                mcq(
                    "Quel est le pluriel de « carnaval » ?",
                    ["carnavaux", "carnavals", "carnaval"],
                    1,
                    explanation="Exception : carnaval → carnavals (comme bal, festival, récital).",
                ),
                fill_blanks(
                    "Écris le pluriel du nom bal (c'est une exception !).",
                    "On adore danser : un bal, deux ___.",
                    ["bals"],
                    explanation="Exception : bal → bals (et non « baux »).",
                ),
                mcq(
                    "Quel est le pluriel de « bijou » ?",
                    ["bijous", "bijoux", "bijoues"],
                    1,
                    explanation="Bijou fait partie des noms en -ou qui prennent -x : bijoux.",
                ),
            ],
        ),
        # --- Tier 15 — Le pluriel des noms composés (niveau 5) --------------- #
        L(
            15,
            5,
            "CM1 — Le pluriel des noms composés 🔧",
            "Accorder les noms composés selon la nature de leurs mots.",
            [
                mcq(
                    "Quel est le pluriel de « un chou-fleur » ?",
                    ["des chou-fleurs", "des choux-fleurs", "des choux-fleur"],
                    1,
                    explanation="Nom + nom : les deux s'accordent → choux-fleurs.",
                ),
                mcq(
                    "Quel est le pluriel de « un grand-père » ?",
                    ["des grand-pères", "des grands-pères", "des grands-pere"],
                    1,
                    explanation="Adjectif + nom : les deux s'accordent → grands-pères.",
                ),
                mcq(
                    "Quel est le pluriel de « un coffre-fort » ?",
                    ["des coffres-forts", "des coffre-forts", "des coffres-fort"],
                    0,
                    explanation="Nom + adjectif : les deux s'accordent → coffres-forts.",
                ),
                mcq(
                    "Quel est le pluriel de « un tire-bouchon » (verbe + nom) ?",
                    ["des tires-bouchons", "des tire-bouchons", "des tire-bouchon"],
                    1,
                    explanation="Le verbe reste invariable, seul le nom s'accorde → tire-bouchons.",
                ),
            ],
        ),
        # --- Tier 16 — m devant m, b, p (niveau 4) --------------------------- #
        L(
            16,
            4,
            "CM1 — m devant m, b, p ✍️",
            "Devant m, b, p, la lettre n devient m (sauf exceptions).",
            [
                fill_blanks(
                    "Complète la règle avec une seule lettre.",
                    "Devant les lettres m, b et p, on écrit ___ au lieu de n.",
                    ["m"],
                    explanation="On écrit em-, om-, im- devant m, b, p.",
                ),
                mcq(
                    "Quelle est la bonne orthographe ?",
                    ["tanbour", "tambour", "tammbour"],
                    1,
                    explanation="n devient m devant b : tambour.",
                ),
                mcq(
                    "Quelle est la bonne orthographe ?",
                    ["enporter", "emporter", "emmporter"],
                    1,
                    explanation="n devient m devant p : emporter.",
                ),
                mcq(
                    "Quel mot est une exception (il garde le n devant b) ?",
                    ["chambre", "bonbon", "tempête"],
                    1,
                    explanation="Exceptions : bonbon, bonbonne, embonpoint, néanmoins.",
                ),
            ],
        ),
        # --- Tier 17 — Le son [s] (niveau 4) --------------------------------- #
        L(
            17,
            4,
            "CM1 — Le son [s] 🐍",
            "Écrire le son [s] : s, ss, c, ç, sc et t.",
            [
                mcq(
                    "Comment écrit-on le son [s] dans « gar___on » ?",
                    ["c", "ç", "ss"],
                    1,
                    explanation="Devant a, o, u, le c prend une cédille : garçon.",
                ),
                mcq(
                    "Entre deux voyelles, comment écrit-on le son [s] dans « poi___on » ?",
                    ["s", "ss", "c"],
                    1,
                    explanation="Un seul s entre deux voyelles ferait [z], on double : poisson.",
                ),
                fill_blanks(
                    "Complète la règle (deux lettres).",
                    "Pour faire le son [s] entre deux voyelles, on écrit ___.",
                    ["ss"],
                    explanation="Exemples : poisson, tasse, dessin.",
                ),
                mcq(
                    "Dans le mot « nation », le son [s] s'écrit avec la lettre...",
                    ["s", "t", "c"],
                    1,
                    explanation="Dans -tion, le t se prononce [s] : nation, addition.",
                ),
            ],
        ),
        # --- Tier 18 — Les sons [g] et [j] (niveau 4) ------------------------ #
        L(
            18,
            4,
            "CM1 — Les sons [g] et [j] 🐊",
            "Écrire le son [g] dur et le son [j] : g, ge, gu.",
            [
                mcq(
                    "Pour faire le son [g] dur devant e ou i, on écrit...",
                    ["g", "gu", "ge"],
                    1,
                    explanation="On ajoute un u : guitare, guerre, guirlande.",
                ),
                mcq(
                    "« nous man___ons » — pour garder le son [j] devant o, on écrit...",
                    ["g", "ge", "gu"],
                    1,
                    explanation="On ajoute un e après le g : nous mangeons.",
                ),
                mcq(
                    "Dans le mot « guitare », le son [g] dur s'écrit...",
                    ["g", "gu", "gh"],
                    1,
                    explanation="Devant i, il faut gu pour garder le son [g] : guitare.",
                ),
                fill_blanks(
                    "Complète (deux lettres) pour garder le son [j] devant o.",
                    "Nous plon___ons dans la piscine.",
                    ["ge"],
                    explanation="On ajoute un e : nous plongeons.",
                ),
            ],
        ),
        # --- Tier 19 — Les consonnes doubles (niveau 5) ---------------------- #
        L(
            19,
            5,
            "CM1 — Les consonnes doubles 🔁",
            "Repérer les mots avec une consonne double.",
            [
                mcq(
                    "Quelle est la bonne orthographe ?",
                    ["apeler", "appeler", "appeller"],
                    1,
                    explanation="Deux p et un seul l : appeler.",
                ),
                mcq(
                    "Quelle est la bonne orthographe ?",
                    ["doner", "donner", "donnner"],
                    1,
                    explanation="On double le n : donner.",
                ),
                mcq(
                    "Combien de « l » dans le mot « tranquille » ?",
                    ["un l", "deux l", "trois l"],
                    1,
                    explanation="tranquille s'écrit avec deux l.",
                ),
                fill_blanks(
                    "Complète (deux lettres) le mot ballon.",
                    "On gonfle un ba___on pour la fête.",
                    ["ll"],
                    explanation="ballon s'écrit avec deux l.",
                ),
            ],
        ),
        # --- Tier 20 — a / à / as (niveau 4) --------------------------------- #
        L(
            20,
            4,
            "CM1 — a, à ou as ? 🅰️",
            "Distinguer le verbe avoir (a, as) et la préposition à.",
            [
                fill_blanks(
                    "Complète avec le verbe avoir (3e personne).",
                    "Léa ___ un joli vélo rouge.",
                    ["a"],
                    explanation="« a » = verbe avoir, on peut dire « avait ».",
                ),
                fill_blanks(
                    "Complète avec le verbe avoir (2e personne).",
                    "Tu ___ complètement raison !",
                    ["as"],
                    explanation="« as » = verbe avoir, on peut dire « avais ».",
                ),
                mcq(
                    "« Il va ___ Paris demain. » Choisis le bon mot.",
                    ["a", "à", "as"],
                    1,
                    explanation="Ici c'est la préposition à (on ne peut pas dire « avait »).",
                ),
                mcq(
                    "Pour reconnaître le verbe « a », on peut le remplacer par...",
                    ["avait", "et", "ou"],
                    0,
                    explanation="Si on peut dire « avait », c'est le verbe a (sans accent).",
                ),
            ],
        ),
        # --- Tier 21 — et / est / es (niveau 4) ------------------------------ #
        L(
            21,
            4,
            "CM1 — et, est ou es ? ➕",
            "Distinguer et (addition) du verbe être (est, es).",
            [
                fill_blanks(
                    "Complète avec le petit mot qui relie deux mots.",
                    "Paul ___ Marie jouent ensemble.",
                    ["et"],
                    explanation="« et » relie deux mots, on peut dire « et puis ».",
                ),
                fill_blanks(
                    "Complète avec le verbe être (3e personne).",
                    "Le chat ___ tout noir.",
                    ["est"],
                    explanation="« est » = verbe être, on peut dire « était ».",
                ),
                fill_blanks(
                    "Complète avec le verbe être (2e personne).",
                    "Tu ___ mon meilleur ami.",
                    ["es"],
                    explanation="« es » = verbe être, on peut dire « étais ».",
                ),
                mcq(
                    "Pour reconnaître « est », on peut le remplacer par...",
                    ["était", "et puis", "et"],
                    0,
                    explanation="Si on peut dire « était », c'est le verbe est.",
                ),
            ],
        ),
        # --- Tier 22 — son / sont, on / ont (niveau 5) ---------------------- #
        L(
            22,
            5,
            "CM1 — son/sont, on/ont 👥",
            "Distinguer les homophones son/sont et on/ont.",
            [
                fill_blanks(
                    "Complète avec le verbe être (3e personne du pluriel).",
                    "Les enfants ___ très contents.",
                    ["sont"],
                    explanation="« sont » = verbe être, on peut dire « étaient ».",
                ),
                fill_blanks(
                    "Complète avec le petit mot qui montre l'appartenance.",
                    "Il enfile ___ manteau bleu.",
                    ["son"],
                    explanation="« son » = le sien (son manteau à lui).",
                ),
                fill_blanks(
                    "Complète avec le pronom (comme « quelqu'un »).",
                    "___ va tous au parc cet après-midi.",
                    ["on"],
                    explanation="« on » est un pronom sujet, on peut dire « il ».",
                ),
                mcq(
                    "« Elles ___ un chien. » Choisis le verbe avoir (3e pers. pluriel).",
                    ["ont", "on", "son"],
                    0,
                    explanation="« ont » = verbe avoir, on peut dire « avaient ».",
                ),
            ],
        ),
        # --- Tier 23 — ces / ses / c'est / s'est (niveau 5) ------------------ #
        L(
            23,
            5,
            "CM1 — ces, ses, c'est, s'est 🔍",
            "Distinguer ces, ses, c'est et s'est.",
            [
                mcq(
                    "« ___ un très beau jour. » Choisis le bon mot.",
                    ["Ces", "Ses", "C'est"],
                    2,
                    explanation="« c'est » = cela est (« c'est un beau jour »).",
                ),
                mcq(
                    "« Il ___ lavé les mains. » Choisis le bon mot.",
                    ["c'est", "s'est", "ses"],
                    1,
                    explanation="« s'est » vient du verbe se laver (il s'est lavé).",
                ),
                fill_blanks(
                    "Complète avec le mot qui montre l'appartenance (les siennes).",
                    "Sofia range ___ affaires dans le sac.",
                    ["ses"],
                    explanation="« ses » = les siennes (ses affaires à elle).",
                ),
                fill_blanks(
                    "Complète avec le mot qui montre du doigt (celles-là).",
                    "Regarde ___ montagnes tout au loin !",
                    ["ces"],
                    explanation="« ces » désigne les montagnes que l'on montre.",
                ),
            ],
        ),
        # --- Tier 24 — la / là / l'a et ou / où (niveau 5) ------------------- #
        L(
            24,
            5,
            "CM1 — la, là, l'a / ou, où 📍",
            "Distinguer la, là, l'a et les homophones ou/où.",
            [
                mcq(
                    "« Tu veux du thé ___ du café ? » Choisis le bon mot.",
                    ["ou", "où", "houx"],
                    0,
                    explanation="« ou » propose un choix, on peut dire « ou bien ».",
                ),
                mcq(
                    "« ___ est la gare, s'il vous plaît ? » Choisis le bon mot.",
                    ["Ou", "Où", "Hou"],
                    1,
                    explanation="« où » (avec accent) indique le lieu.",
                ),
                mcq(
                    "« Il ___ appelé au téléphone. » Choisis le bon mot (le + a).",
                    ["la", "là", "l'a"],
                    2,
                    explanation="« l'a » = le/la + verbe avoir (il l'a appelé).",
                ),
                mcq(
                    "« Viens ___, tout près de moi ! » Choisis le bon mot.",
                    ["la", "là", "l'a"],
                    1,
                    explanation="« là » (avec accent) indique le lieu.",
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CM1 Orthographe "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
