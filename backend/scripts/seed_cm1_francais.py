"""Seed CM1 Français — programme avancé (niveau élevé).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_cm1_francais.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, reading, theme

from app.core.database import SessionLocal

LEVEL = "cm1"
SLUG = "francais"


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
        # 1 — Les trois groupes de verbes
        L(
            10,
            4,
            "CM1 — Les trois groupes de verbes 🧩",
            "Classer les verbes selon leur groupe.",
            [
                mcq(
                    "À quel groupe appartient le verbe « chanter » ?",
                    ["1er groupe", "2e groupe", "3e groupe"],
                    0,
                    explanation="Les verbes en -er (sauf « aller ») forment le 1er groupe.",
                ),
                mcq(
                    "À quel groupe appartient le verbe « finir » (nous finissons) ?",
                    ["1er groupe", "2e groupe", "3e groupe"],
                    1,
                    explanation="Les verbes en -ir qui font « -issons » au présent sont du 2e groupe.",
                ),
                mcq(
                    "À quel groupe appartient le verbe « prendre » ?",
                    ["1er groupe", "2e groupe", "3e groupe"],
                    2,
                    explanation="Les verbes en -re, -oir et les -ir irréguliers sont du 3e groupe.",
                ),
                mcq(
                    "Le verbe « aller » se termine par -er : à quel groupe appartient-il ?",
                    ["1er groupe", "2e groupe", "3e groupe"],
                    2,
                    explanation="« aller » est un verbe irrégulier du 3e groupe, malgré sa terminaison en -er.",
                ),
            ],
        ),
        # 2 — Le présent (tous les groupes)
        L(
            11,
            4,
            "CM1 — Le présent de l'indicatif ✏️",
            "Conjuguer les trois groupes au présent.",
            [
                fill_blanks("Conjugue « manger » au présent : nous…", "Nous ___ à midi.", ["mangeons"]),
                fill_blanks("Conjugue « finir » au présent : ils…", "Ils ___ leurs devoirs.", ["finissent"]),
                fill_blanks("Conjugue « prendre » au présent : tu…", "Tu ___ le train.", ["prends"]),
                mcq(
                    "Conjugue « voir » au présent : nous…",
                    ["nous voyons", "nous voions", "nous voyions"],
                    0,
                    explanation="Au présent : nous voyons. « nous voyions » est de l'imparfait.",
                ),
            ],
        ),
        # 3 — L'imparfait
        L(
            12,
            4,
            "CM1 — L'imparfait ⏳",
            "Conjuguer à l'imparfait de l'indicatif.",
            [
                fill_blanks("« jouer » à l'imparfait : je…", "Quand j'étais petit, je ___ dans le jardin.", ["jouais"]),
                fill_blanks("« finir » à l'imparfait : nous…", "Nous ___ toujours à l'heure.", ["finissions"]),
                fill_blanks("« chanter » à l'imparfait : ils…", "Ils ___ en chœur.", ["chantaient"]),
                mcq(
                    "Quelle est la forme correcte de « être » à l'imparfait avec « il » ?",
                    ["il été", "il était", "il serait"],
                    1,
                    explanation="À l'imparfait : il était. « il serait » est du conditionnel.",
                ),
            ],
        ),
        # 4 — Le futur simple
        L(
            13,
            5,
            "CM1 — Le futur simple 🚀",
            "Conjuguer au futur simple, y compris les verbes irréguliers.",
            [
                fill_blanks("« manger » au futur : nous…", "Demain, nous ___ au restaurant.", ["mangerons"]),
                fill_blanks("« aller » au futur : je (j')…", "Demain, j'___ à la piscine.", ["irai"]),
                fill_blanks("« être » au futur : tu…", "Un jour, tu ___ grand.", ["seras"]),
                mcq(
                    "« voir » au futur simple : nous…",
                    ["nous verrons", "nous voirons", "nous verrions"],
                    0,
                    explanation="Le radical de « voir » au futur est « verr- » : nous verrons. « verrions » est du conditionnel.",
                ),
            ],
        ),
        # 5 — Le passé composé
        L(
            14,
            5,
            "CM1 — Le passé composé 🏝️",
            "Former le passé composé et accorder le participe passé.",
            [
                mcq(
                    "Comment se forme le passé composé ?",
                    [
                        "avec un seul verbe conjugué",
                        "avec l'auxiliaire « avoir » ou « être » au présent + le participe passé",
                        "avec le verbe au futur",
                    ],
                    1,
                ),
                mcq(
                    "Choisis la bonne forme : « Elle est ___ à la maison. » (rentrer)",
                    ["rentré", "rentrée", "rentrer"],
                    1,
                    explanation="Avec « être », le participe s'accorde avec le sujet : elle est rentrée.",
                ),
                mcq(
                    "Choisis la bonne forme : « J'ai ___ une pomme. » (manger)",
                    ["mangé", "mangée", "manger"],
                    0,
                    explanation="Avec « avoir », pas d'accord avec le sujet quand le COD suit : j'ai mangé.",
                ),
                mcq(
                    "Quel auxiliaire est utilisé dans « Nous sommes allés » ?",
                    ["avoir", "être", "aller"],
                    1,
                    explanation="Le verbe « aller » se conjugue avec l'auxiliaire « être ».",
                ),
            ],
        ),
        # 6 — Le passé simple (3e personne)
        L(
            15,
            5,
            "CM1 — Le passé simple 📜",
            "Reconnaître le passé simple à la 3e personne.",
            [
                mcq(
                    "« chanter » au passé simple, 3e personne du singulier : il…",
                    ["il chanta", "il chantait", "il chantera"],
                    0,
                    explanation="Passé simple : il chanta. « il chantait » est de l'imparfait.",
                ),
                mcq(
                    "« finir » au passé simple, 3e personne du pluriel : ils…",
                    ["ils finissaient", "ils finirent", "ils finiront"],
                    1,
                    explanation="Passé simple : ils finirent. « ils finiront » est du futur.",
                ),
                mcq(
                    "« être » au passé simple, 3e personne du singulier : il…",
                    ["il fut", "il était", "il fût"],
                    0,
                    explanation="Passé simple : il fut. « il était » est de l'imparfait.",
                ),
                mcq(
                    "« faire » au passé simple, 3e personne du singulier : il…",
                    ["il faisait", "il fit", "il fera"],
                    1,
                    explanation="Passé simple : il fit. « il faisait » est de l'imparfait.",
                ),
            ],
        ),
        # 7 — Nature et fonction des mots
        L(
            16,
            5,
            "CM1 — Nature et fonction des mots 🔍",
            "Distinguer la nature (classe) et la fonction (rôle) d'un mot.",
            [
                mcq(
                    "La « nature » d'un mot, c'est…",
                    [
                        "sa classe grammaticale (nom, verbe, adjectif…)",
                        "son rôle dans la phrase",
                        "son nombre de lettres",
                    ],
                    0,
                ),
                mcq(
                    "La « fonction » d'un mot, c'est…",
                    ["sa classe grammaticale", "son rôle dans la phrase (sujet, COD…)", "sa première lettre"],
                    1,
                ),
                mcq(
                    "Dans « Le chat dort », quelle est la fonction de « le chat » ?",
                    ["sujet", "complément d'objet", "verbe"],
                    0,
                ),
                mcq(
                    "Dans « Le chat dort », quelle est la nature du mot « dort » ?",
                    ["un nom", "un verbe", "un adjectif"],
                    1,
                ),
            ],
        ),
        # 8 — Le complément d'objet (COD / COI)
        L(
            17,
            5,
            "CM1 — Le complément d'objet 🎯",
            "Repérer le COD et le COI.",
            [
                mcq(
                    "Le COD répond à la question…",
                    ["qui ? quoi ?", "à qui ? à quoi ?", "quand ?"],
                    0,
                ),
                mcq(
                    "Le COI répond à la question…",
                    ["qui ? quoi ?", "à qui ? à quoi ? de qui ?", "où ?"],
                    1,
                ),
                mcq(
                    "Dans « Marie mange une pomme », « une pomme » est…",
                    ["un COD", "un COI", "un sujet"],
                    0,
                    explanation="Marie mange quoi ? une pomme → COD (pas de préposition).",
                ),
                mcq(
                    "Dans « Je parle à mon ami », « à mon ami » est…",
                    ["un COD", "un COI", "un adjectif"],
                    1,
                    explanation="Je parle à qui ? à mon ami → COI (préposition « à »).",
                ),
            ],
        ),
        # 9 — Les adverbes
        L(
            18,
            4,
            "CM1 — Les adverbes 💨",
            "Reconnaître et former des adverbes.",
            [
                mcq(
                    "Un adverbe est un mot…",
                    ["variable", "invariable", "toujours un nom"],
                    1,
                    explanation="L'adverbe est invariable : il ne change jamais d'orthographe.",
                ),
                mcq(
                    "Dans « Il court vite », quel est l'adverbe ?",
                    ["il", "court", "vite"],
                    2,
                ),
                mcq(
                    "Quel adverbe est formé à partir de l'adjectif « lent » ?",
                    ["lentement", "lenteur", "lentir"],
                    0,
                    explanation="« lenteur » est un nom ; « lentement » est l'adverbe.",
                ),
                mcq(
                    "Lequel de ces mots est un adverbe ?",
                    ["rapide", "rapidement", "rapidité"],
                    1,
                    explanation="« rapide » est un adjectif, « rapidité » un nom, « rapidement » l'adverbe.",
                ),
            ],
        ),
        # 10 — Sens propre et sens figuré
        L(
            19,
            4,
            "CM1 — Sens propre et sens figuré 🎨",
            "Distinguer le sens propre du sens figuré.",
            [
                mcq(
                    "« Il a mangé toute la tarte. » Le verbe « manger » est employé au sens…",
                    ["propre", "figuré", "interdit"],
                    0,
                ),
                mcq(
                    "Que signifie « dévorer un livre » ?",
                    ["manger le papier", "lire avec passion", "déchirer le livre"],
                    1,
                    explanation="« dévorer un livre » est une expression au sens figuré : lire avec passion.",
                ),
                mcq(
                    "Dans « Il a le cœur brisé », l'expression est au sens…",
                    ["propre", "figuré"],
                    1,
                ),
                mcq(
                    "« La branche de l'arbre est cassée. » Le mot « branche » est au sens…",
                    ["propre", "figuré"],
                    0,
                ),
            ],
        ),
        # 11 — Synonymes, antonymes, homonymes
        L(
            20,
            4,
            "CM1 — Synonymes, antonymes, homonymes 🔤",
            "Jouer avec les relations entre les mots.",
            [
                mcq(
                    "Quel mot est un synonyme de « content » ?",
                    ["triste", "joyeux", "fatigué"],
                    1,
                ),
                mcq(
                    "Quel est l'antonyme (le contraire) de « grand » ?",
                    ["énorme", "petit", "haut"],
                    1,
                ),
                mcq(
                    "Quelle paire de mots sont des homonymes ?",
                    ["ver / verre", "chat / chien", "grand / petit"],
                    0,
                    explanation="Les homonymes se prononcent pareil mais s'écrivent différemment : ver / verre.",
                ),
                mcq(
                    "Quel est le contraire de « rapide » ?",
                    ["vite", "lent", "pressé"],
                    1,
                ),
            ],
        ),
        # 12 — Préfixes et suffixes
        L(
            21,
            5,
            "CM1 — Préfixes et suffixes 🧱",
            "Décomposer les mots avec préfixes et suffixes.",
            [
                mcq(
                    "Un préfixe se place…",
                    ["avant le radical", "après le radical", "au milieu du mot"],
                    0,
                ),
                mcq(
                    "Dans « refaire », quel est le préfixe ?",
                    ["re-", "-faire", "fai-"],
                    0,
                    explanation="Le préfixe « re- » indique la répétition : refaire = faire à nouveau.",
                ),
                mcq(
                    "Dans « lentement », quel est le suffixe ?",
                    ["len-", "-ment", "-tement"],
                    1,
                    explanation="Le suffixe « -ment » sert à former des adverbes à partir d'adjectifs.",
                ),
                mcq(
                    "Que veut dire le préfixe « in- » dans « incorrect » ?",
                    ["la répétition", "le contraire", "quelque chose de petit"],
                    1,
                    explanation="« in- » exprime le contraire : incorrect = pas correct.",
                ),
            ],
        ),
        # 13 — Les homophones (a/à, et/est, on/ont)
        L(
            22,
            4,
            "CM1 — Les homophones a/à, et/est, on/ont ✏️",
            "Choisir le bon homophone grammatical.",
            [
                mcq("Elle ___ fini ses devoirs.", ["a", "à"], 0, explanation="« a » = verbe avoir (elle avait fini)."),
                mcq("Nous allons ___ la plage.", ["a", "à"], 1, explanation="« à » = préposition."),
                mcq("Le chien ___ le chat jouent.", ["et", "est"], 0, explanation="« et » = et puis (addition)."),
                mcq("Ils ___ gagné le match.", ["on", "ont"], 1, explanation="« ont » = verbe avoir (ils avaient)."),
            ],
        ),
        # 14 — Les homophones (ces/ses/c'est/s'est)
        L(
            23,
            5,
            "CM1 — Les homophones ces/ses/c'est/s'est 🏝️",
            "Distinguer les homophones en [sɛ].",
            [
                mcq(
                    "___ un très beau jardin.",
                    ["c'est", "s'est", "ces", "ses"],
                    0,
                    explanation="« c'est » = cela est.",
                ),
                mcq(
                    "Il ___ blessé au genou.",
                    ["c'est", "s'est", "ces", "ses"],
                    1,
                    explanation="« s'est » = se + est (verbe pronominal : il s'est blessé).",
                ),
                mcq(
                    "Regarde ___ oiseaux là-bas (ceux-là) !",
                    ["ces", "ses", "c'est", "s'est"],
                    0,
                    explanation="« ces » = déterminant démonstratif pluriel (ceux-là).",
                ),
                mcq(
                    "Paul a rangé ___ jouets (les siens).",
                    ["ces", "ses", "c'est", "s'est"],
                    1,
                    explanation="« ses » = déterminant possessif (les siens).",
                ),
            ],
        ),
        # 15 — Lecture — compréhension
        L(
            24,
            5,
            "CM1 — Lecture : La cité engloutie 📖",
            "Lire un texte et répondre à des questions.",
            [
                reading(
                    "Lis attentivement le texte.",
                    "Depuis des générations, les pêcheurs du village racontaient qu'une cité entière "
                    "dormait au fond de la baie. On disait que, les nuits de pleine lune, on pouvait "
                    "apercevoir la lueur pâle de ses clochers sous la surface. Léonie, une jeune "
                    "plongeuse curieuse, décida un matin de vérifier cette légende. Munie de son masque, "
                    "elle plongea dans l'eau froide et transparente. À mesure qu'elle descendait, des "
                    "formes étranges se dessinaient : des murs couverts d'algues, des colonnes brisées, "
                    "et même une cloche verdie par le temps. La cité n'était donc pas un simple conte ! "
                    "Émerveillée, Léonie remonta à la surface, bien décidée à revenir avec de quoi "
                    "photographier sa découverte.",
                ),
                mcq(
                    "Que racontaient les pêcheurs du village ?",
                    [
                        "Qu'un trésor était caché sur la plage",
                        "Qu'une cité dormait au fond de la baie",
                        "Qu'un monstre vivait dans la baie",
                    ],
                    1,
                ),
                mcq(
                    "Pourquoi Léonie décide-t-elle de plonger ?",
                    ["Pour pêcher des poissons", "Pour vérifier la légende", "Pour retrouver un ami"],
                    1,
                ),
                mcq(
                    "Que découvre-t-elle sous l'eau ?",
                    [
                        "Un bateau moderne",
                        "Des murs, des colonnes et une cloche",
                        "Un coffre rempli d'or",
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CM1 Français "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
