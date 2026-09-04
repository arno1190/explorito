"""Format `.explorito` et **validateur unique** de toute ingestion de contenu.

Trois chemins d'ingestion existent (dialogue d'envoi du parent, compétence
d'écriture via jeton, seeders `--pack`) et ils traversent tous
:func:`validate_pack`. C'est la raison d'être du module : dupliquer la validation
garantirait qu'un des trois chemins finisse plus permissif que les autres, et
c'est précisément celui-là qu'un contenu douteux emprunterait.

La validation est délibérément à **trois étages** (décisions 5 et 11 de
l'issue #7) :

- ``error`` — refus dur, levé via :class:`PackRejected`. Réservé à ce que le
  serveur peut affirmer sans juger : version de format, forme des exercices
  (déléguée à :func:`app.schemas.exercise.validate_exercise_payload`),
  ``difficulty_level`` manquant, plafonds, matière/niveau inconnus, langue.
- ``warning`` — alimente un score de qualité 0–100, ne bloque jamais. Ce sont
  des règles *pédagogiques* (courbe de difficulté plate, aucun mélange de types,
  texte trop long pour le niveau) : les imposer reviendrait à refuser du contenu
  correct parce qu'il ne ressemble pas à celui de l'équipe.
- ``flag`` — annotation à l'attention d'un humain (grossièreté, quasi-doublon).
  Ces deux détecteurs ont de vrais faux positifs : une leçon de français *sur*
  un gros mot, et une seconde version réellement meilleure d'une leçon
  d'additions. Ils ne refusent donc rien.

Chaque message d'erreur nomme la leçon et l'exercice fautifs **et** l'action
corrective : le validateur et la compétence d'écriture forment une boucle de
rétroaction (l'IA du parent lit le refus et corrige), ce qui est bien plus fiable
qu'un SKILL.md plus long. Le message *est* le produit.

Format accepté (``format_version`` = :attr:`Settings.PACK_FORMAT_VERSION`)::

    {"format_version": 1,
     "pack": {"title": "...", "emoji": "⚽", "description": "...", "tags": ["sport"]},
     "lessons": [{"subject_slug": "maths", "level": "ce1", "tier": 1,
                  "name": "...", "description": "...",
                  "exercises": [ /* formes typées existantes, difficulty_level requis */ ]}],
     "self_check": {"math_verified": true, "notes": "..."}}
"""

import hashlib
import re
import unicodedata
from collections.abc import Collection
from functools import lru_cache
from typing import Any

from app.core.config import settings
from app.models.content import ExerciseType, LevelEnum
from app.schemas.exercise import validate_exercise_payload
from app.schemas.pack import ValidationIssue

try:  # pragma: no cover - dépend de l'environnement d'installation
    from lingua import Language, LanguageDetectorBuilder

    _LINGUA_AVAILABLE = True
except ImportError:  # pragma: no cover
    _LINGUA_AVAILABLE = False

#: Matières canoniques du curriculum (cf. ``scripts/seed_curriculum.py``) avec leur
#: nom et leur icône, nécessaires quand une ingestion doit créer la matière. Sert
#: de repli quand l'appelant n'a pas de session : les chemins connectés passent
#: les slugs réellement présents en base via ``known_subject_slugs``.
CANONICAL_SUBJECTS: dict[str, tuple[str, str]] = {
    "maths": ("Mathématiques", "🌋"),
    "francais": ("Français", "🏝️"),
    "orthographe": ("Orthographe", "✏️"),
    "histoire": ("Histoire", "⏳"),
    "geo": ("Géographie France", "🗼"),
    "monde": ("Questionner le monde", "🚀"),
    "arts": ("Arts", "🎨"),
    "logique": ("Logique", "🧩"),
}

CANONICAL_SUBJECT_SLUGS: frozenset[str] = frozenset(CANONICAL_SUBJECTS)

#: En dessous de ce nombre de caractères, aucune détection de langue n'est
#: tentée : « 3 + 4 = ? » ou « Léa a 5 billes » ne portent pas assez de signal et
#: un refus serait un faux positif garanti.
MIN_LANGUAGE_CHARS = 40

#: Longueur de question raisonnable par niveau scolaire. Simple avertissement :
#: un texte long en CP n'est pas invalide, il est probablement mal calibré.
LEVEL_MAX_QUESTION_CHARS: dict[LevelEnum, int] = {
    LevelEnum.PS: 60,
    LevelEnum.MS: 60,
    LevelEnum.GS: 80,
    LevelEnum.CP: 120,
    LevelEnum.CE1: 180,
    LevelEnum.CE2: 240,
    LevelEnum.CM1: 320,
    LevelEnum.CM2: 400,
}

#: Pénalités du score de qualité, appliquées **une fois par code** (et non par
#: occurrence) : un pack de dix leçons trop bavardes n'est pas dix fois pire
#: qu'un pack d'une seule. Score = 100 − somme des pénalités, planché à 0.
DEDUCTIONS: dict[str, int] = {
    "flat_difficulty": 15,
    "no_type_mix": 15,
    "text_too_long_for_level": 10,
    "self_check_missing": 10,
    "single_lesson": 5,
    "xp_ignored": 0,
}

#: Liste de blocage volontairement courte et grossière : elle ne sert pas à
#: filtrer (elle ne refuse rien) mais à faire remonter un pack à un humain.
PROFANITY_BLOCKLIST: frozenset[str] = frozenset(
    {
        "batard",
        "bite",
        "chatte",
        "chier",
        "con",
        "connard",
        "conne",
        "couille",
        "couilles",
        "cul",
        "encule",
        "enculee",
        "foutre",
        "merde",
        "niquer",
        "pd",
        "pute",
        "putain",
        "salope",
        "salopard",
        "tapette",
        "zizi",
    }
)

#: Mots outils français fréquents, pour le repli de détection de langue.
_FRENCH_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "au",
        "aux",
        "avec",
        "ce",
        "ces",
        "combien",
        "dans",
        "de",
        "des",
        "du",
        "elle",
        "en",
        "est",
        "et",
        "il",
        "je",
        "la",
        "le",
        "les",
        "leur",
        "mais",
        "ne",
        "on",
        "ou",
        "par",
        "pas",
        "pour",
        "qui",
        "que",
        "quel",
        "quelle",
        "sa",
        "se",
        "ses",
        "son",
        "sont",
        "sur",
        "tu",
        "un",
        "une",
        "vous",
    }
)

_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)

#: Clés recopiées telles quelles depuis un exercice. ``xp_reward`` (et tout autre
#: champ) n'y figure pas : c'est cette liste blanche qui **jette l'XP déclarée**.
_EXERCISE_KEYS = ("hints", "explanation", "media_urls")


class PackRejected(Exception):
    """Refus dur d'un pack, portant la liste complète des erreurs.

    La liste est exhaustive (et non « première erreur rencontrée ») parce que le
    consommateur est un agent qui corrige puis renvoie : lui rendre les dix
    erreurs d'un coup évite dix allers-retours.
    """

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__("; ".join(issue.message for issue in issues) or "pack invalide")


def _issue(
    severity: str,
    code: str,
    message: str,
    *,
    lesson_index: int | None = None,
    exercise_index: int | None = None,
    field: str | None = None,
) -> ValidationIssue:
    """Construit un constat ancré sur l'élément fautif."""
    return ValidationIssue(
        severity=severity,  # type: ignore[arg-type]
        code=code,
        message=message,
        lesson_index=lesson_index,
        exercise_index=exercise_index,
        field=field,
    )


def _strip_accents(text: str) -> str:
    """Texte sans diacritiques, pour comparer des mots à la liste de blocage."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _words(text: str) -> list[str]:
    """Mots alphabétiques en minuscules, sans accents."""
    return _WORD_RE.findall(_strip_accents(text).lower())


#: Signes orthographiques propres au français : diacritiques que l'espagnol,
#: l'italien, l'allemand et l'anglais n'emploient pas de cette façon, et élisions
#: (``d'os``, ``l'arbre``). Volontairement sans ``í ñ ã ¿`` : ces caractères
#: signeraient une autre langue, pas le français.
_FRENCH_DIACRITICS = frozenset("éèêëàâäîïôöûùüÿçœæ")

_FRENCH_ELISION_RE = re.compile(r"\b[cdjlmnstCDJLMNST]['’]|\bqu['’]", re.UNICODE)


def _french_evidence(text: str) -> bool:
    """Le texte porte-t-il une marque **positive** de français ?

    Trois indices indépendants, dont un seul suffit : un diacritique français,
    une élision, ou une proportion suffisante de mots outils français.

    Sert de contre-signal au détecteur statistique. Un énoncé de CE1 conforme à
    la rubrique est court et saturé de chiffres (« Tom range 3 os par boîte. Il
    remplit 9 boîtes. »), et ``lingua`` y voit de l'espagnol avec 0,92 de
    confiance : sur ce seul signal, le contenu le plus banal de l'application
    serait refusé. La confiance ne sépare pas ces cas — un vrai texte espagnol
    sort à 1,00 — donc il faut un indice de nature différente.

    Args:
        text: Texte à examiner.

    Returns:
        Vrai si un indice de français est présent.
    """
    if any(char in _FRENCH_DIACRITICS for char in text.lower()):
        return True
    if _FRENCH_ELISION_RE.search(text):
        return True
    words = _words(text)
    if not words:
        return True
    hits = sum(1 for word in words if word in _FRENCH_STOPWORDS)
    return hits / len(words) >= 0.2


def _looks_french(text: str) -> bool:
    """Heuristique de repli : le texte ressemble-t-il à du français ?

    Utilisée **uniquement** si ``lingua`` n'est pas installé. C'est une
    heuristique assumée, pas une détection : elle compte les mots outils
    français. Le contrat du projet interdit un appel réseau et l'application
    n'appelle jamais de LLM (décision 1 de l'issue #7), donc le repli doit être
    local et déterministe — quitte à être grossier.

    Args:
        text: Texte à examiner.

    Returns:
        Vrai si assez de mots outils français sont présents.
    """
    words = _words(text)
    if not words:
        return True
    hits = sum(1 for word in words if word in _FRENCH_STOPWORDS)
    return hits >= 2 or hits / len(words) >= 0.2


@lru_cache(maxsize=1)
def _detector() -> Any:  # pragma: no cover - trivial, dépend de l'environnement
    """Détecteur ``lingua`` construit à la demande (mode basse précision).

    Construit paresseusement : importer ce module ne doit pas charger de modèle
    de langue, sinon chaque démarrage d'application le paierait.
    """
    return (
        LanguageDetectorBuilder.from_languages(
            Language.FRENCH,
            Language.ENGLISH,
            Language.SPANISH,
            Language.GERMAN,
            Language.ITALIAN,
            Language.PORTUGUESE,
        )
        .with_low_accuracy_mode()
        .build()
    )


def _is_non_french(text: str) -> bool:
    """Vrai seulement si le texte est, à deux titres, dans une autre langue.

    Le refus de langue est le seul refus dur qui porte sur du *sens* et non sur
    la forme : il doit donc demander l'accord de **deux signaux indépendants**,
    le détecteur statistique et la présence d'indices français
    (:func:`_french_evidence`). Un seul ne suffit pas, parce que chacun se
    trompe dans un sens différent — ``lingua`` classe « Tom range 3 os par
    boîte » en espagnol à 0,92, et le comptage de mots outils accepte « en la
    caja » comme du français.

    Le doute profite toujours à l'auteur : texte court, langue indéterminée, ou
    moindre indice de français ⇒ accepté.
    """
    stripped = text.strip()
    if len(stripped) < MIN_LANGUAGE_CHARS:
        return False
    if _french_evidence(stripped):
        return False
    if _LINGUA_AVAILABLE:
        detected = _detector().detect_language_of(stripped)
        return detected is not None and detected != Language.FRENCH
    return not _looks_french(stripped)


def _content_texts(exercise: dict[str, Any]) -> list[tuple[str, str]]:
    """Textes visibles par l'enfant enfouis dans ``content`` (champ, texte)."""
    content = exercise.get("content")
    if not isinstance(content, dict):
        return []
    texts: list[tuple[str, str]] = []
    for key in ("text", "prompt", "reveal"):
        value = content.get(key)
        if isinstance(value, str):
            texts.append((f"content.{key}", value))
    options = content.get("options")
    if isinstance(options, list):
        for idx, option in enumerate(options):
            if isinstance(option, dict) and isinstance(option.get("text"), str):
                texts.append((f"content.options[{idx}].text", option["text"]))
    return texts


def _exercise_texts(exercise: dict[str, Any]) -> list[tuple[str, str]]:
    """Tous les textes d'un exercice, question et explication comprises."""
    texts: list[tuple[str, str]] = []
    for key in ("question", "explanation"):
        value = exercise.get(key)
        if isinstance(value, str):
            texts.append((key, value))
    texts.extend(_content_texts(exercise))
    return texts


def normalised_title(title: str) -> str:
    """Titre réduit à sa forme comparable (sans accents, casse ni ponctuation)."""
    return " ".join(_words(title))


def pack_fingerprint(payload: dict[str, Any]) -> str:
    """Empreinte de contenu d'un pack : titre normalisé + questions concaténées.

    Sert la détection de quasi-doublon, qui n'est qu'une **annotation** : deux
    packs de même empreinte peuvent parfaitement être une révision assumée
    (clone-pour-réviser, issue #17).
    """
    pack = payload.get("pack") or {}
    parts = [normalised_title(str(pack.get("title", "")))]
    for lesson in payload.get("lessons") or []:
        for exercise in lesson.get("exercises") or []:
            parts.append(normalised_title(str(exercise.get("question", ""))))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def quality_score(issues: Collection[ValidationIssue]) -> int:
    """Score 0–100 dérivé des avertissements, une pénalité par code distinct."""
    codes = {issue.code for issue in issues if issue.severity == "warning"}
    return max(0, 100 - sum(DEDUCTIONS.get(code, 0) for code in codes))


def _validate_pack_header(
    payload: dict[str, Any],
    errors: list[ValidationIssue],
    soft: list[ValidationIssue],
) -> dict[str, Any]:
    """Valide et normalise le bloc ``pack`` ; renvoie sa forme normalisée."""
    raw = payload.get("pack")
    if not isinstance(raw, dict):
        errors.append(
            _issue(
                "error", "pack_missing", "Le bloc « pack » est absent : ajoutez pack.title au minimum.", field="pack"
            )
        )
        return {}

    title = str(raw.get("title") or "").strip()
    if not title:
        errors.append(
            _issue("error", "pack_title_missing", "pack.title est vide : donnez un titre au pack.", field="pack.title")
        )

    tags_raw = raw.get("tags") or []
    if not isinstance(tags_raw, list):
        errors.append(_issue("error", "tags_invalid", "pack.tags doit être une liste de mots-clés.", field="pack.tags"))
        tags_raw = []
    tags: list[str] = []
    for tag in tags_raw:
        cleaned = str(tag).strip()
        if cleaned and cleaned not in tags:
            tags.append(cleaned)
    if len(tags) > settings.PACK_MAX_TAGS:
        errors.append(
            _issue(
                "error",
                "too_many_tags",
                f"{len(tags)} mots-clés déclarés pour un maximum de {settings.PACK_MAX_TAGS} : "
                "conservez les plus discriminants.",
                field="pack.tags",
            )
        )

    if "xp_reward" in raw:
        soft.append(
            _issue(
                "warning",
                "xp_ignored",
                "pack.xp_reward est ignoré : l'XP est dérivée du contenu par le serveur, "
                "jamais déclarée par l'auteur. Retirez le champ.",
                field="pack.xp_reward",
            )
        )

    description = raw.get("description")
    for field, text in (("pack.title", title), ("pack.description", description)):
        if isinstance(text, str):
            _check_text(text, field, errors, soft)

    return {
        "title": title,
        "emoji": (str(raw["emoji"]).strip() or None) if raw.get("emoji") else None,
        "description": str(description).strip() if isinstance(description, str) and description.strip() else None,
        "tags": tags,
    }


def _check_text(
    text: str,
    field: str,
    errors: list[ValidationIssue],
    soft: list[ValidationIssue],
    *,
    lesson_index: int | None = None,
    exercise_index: int | None = None,
) -> None:
    """Applique aux textes les deux refus durs (longueur, langue) et le drapeau grossièreté."""
    if len(text) > settings.PACK_MAX_TEXT_LENGTH:
        errors.append(
            _issue(
                "error",
                "text_too_long",
                f"{field} fait {len(text)} caractères pour un maximum de "
                f"{settings.PACK_MAX_TEXT_LENGTH} : raccourcissez ce texte ou découpez-le en plusieurs exercices.",
                lesson_index=lesson_index,
                exercise_index=exercise_index,
                field=field,
            )
        )
    if _is_non_french(text):
        errors.append(
            _issue(
                "error",
                "not_french",
                f"{field} ne semble pas rédigé en français : Explorito ne diffuse que du contenu "
                "en français. Traduisez ce texte.",
                lesson_index=lesson_index,
                exercise_index=exercise_index,
                field=field,
            )
        )
    hits = sorted(set(_words(text)) & PROFANITY_BLOCKLIST)
    if hits:
        soft.append(
            _issue(
                "flag",
                "profanity",
                f"{field} contient un terme signalé ({', '.join(hits)}) : à confirmer par un humain. "
                "Aucun refus — une leçon de français peut légitimement porter sur ce mot.",
                lesson_index=lesson_index,
                exercise_index=exercise_index,
                field=field,
            )
        )


def _validate_exercise(
    raw: Any,
    lesson_index: int,
    exercise_index: int,
    max_question_chars: int,
    errors: list[ValidationIssue],
    soft: list[ValidationIssue],
) -> dict[str, Any] | None:
    """Valide un exercice et renvoie sa forme normalisée (``None`` si refusé)."""
    where = f"leçon {lesson_index + 1}, exercice {exercise_index + 1}"
    if not isinstance(raw, dict):
        errors.append(
            _issue(
                "error",
                "exercise_invalid",
                f"{where} : un exercice doit être un objet JSON.",
                lesson_index=lesson_index,
                exercise_index=exercise_index,
            )
        )
        return None

    try:
        ex_type = ExerciseType(raw.get("type"))
    except ValueError:
        accepted = ", ".join(sorted(item.value for item in ExerciseType))
        errors.append(
            _issue(
                "error",
                "exercise_type_unknown",
                f"{where} : type « {raw.get('type')} » inconnu. Types acceptés : {accepted}.",
                lesson_index=lesson_index,
                exercise_index=exercise_index,
                field="type",
            )
        )
        return None

    question = str(raw.get("question") or "").strip()
    if not question:
        errors.append(
            _issue(
                "error",
                "question_missing",
                f"{where} : la question est vide. Écrivez la consigne lue par l'enfant.",
                lesson_index=lesson_index,
                exercise_index=exercise_index,
                field="question",
            )
        )

    raw_content = raw.get("content")
    raw_correct = raw.get("correct_answer")
    content: dict[str, Any] = raw_content if isinstance(raw_content, dict) else {}
    correct: dict[str, Any] = raw_correct if isinstance(raw_correct, dict) else {}
    try:
        # Aucune règle de forme n'est réécrite ici : le contrat typé des exercices
        # a déjà une source de vérité, et la dupliquer la ferait diverger.
        validate_exercise_payload(ex_type, content, correct)
    except Exception as exc:  # ValueError, ValidationError Pydantic…
        errors.append(
            _issue(
                "error",
                "exercise_shape",
                f"{where} ({ex_type.value}) : {exc}",
                lesson_index=lesson_index,
                exercise_index=exercise_index,
                field="content",
            )
        )

    difficulty = raw.get("difficulty_level")
    if difficulty is None:
        errors.append(
            _issue(
                "error",
                "difficulty_level_missing",
                f"{where} : difficulty_level manquant. Ajoutez une difficulté de 1 (très facile) "
                "à 5 (très difficile) sur cet exercice — c'est elle qui détermine l'XP.",
                lesson_index=lesson_index,
                exercise_index=exercise_index,
                field="difficulty_level",
            )
        )
    else:
        try:
            difficulty = int(difficulty)
        except (TypeError, ValueError):
            difficulty = -1
        if not 1 <= difficulty <= 5:
            errors.append(
                _issue(
                    "error",
                    "difficulty_level_invalid",
                    f"{where} : difficulty_level={raw.get('difficulty_level')!r} hors bornes. "
                    "Attendu un entier de 1 à 5.",
                    lesson_index=lesson_index,
                    exercise_index=exercise_index,
                    field="difficulty_level",
                )
            )

    for field, text in _exercise_texts(raw):
        _check_text(text, field, errors, soft, lesson_index=lesson_index, exercise_index=exercise_index)

    if len(question) > max_question_chars:
        soft.append(
            _issue(
                "warning",
                "text_too_long_for_level",
                f"{where} : question de {len(question)} caractères pour un niveau qui en supporte "
                f"environ {max_question_chars}. Simplifiez la formulation.",
                lesson_index=lesson_index,
                exercise_index=exercise_index,
                field="question",
            )
        )

    normalised: dict[str, Any] = {
        "type": ex_type.value,
        "question": question,
        "content": content,
        "correct_answer": correct,
        "order_index": exercise_index,
        "difficulty_level": difficulty if isinstance(difficulty, int) and 1 <= difficulty <= 5 else None,
    }
    for key in _EXERCISE_KEYS:
        if raw.get(key) is not None:
            normalised[key] = raw[key]
    return normalised


def _validate_lesson(
    raw: Any,
    lesson_index: int,
    known_slugs: Collection[str],
    errors: list[ValidationIssue],
    soft: list[ValidationIssue],
) -> dict[str, Any] | None:
    """Valide une leçon et renvoie sa forme normalisée (``None`` si refusée)."""
    where = f"leçon {lesson_index + 1}"
    if not isinstance(raw, dict):
        errors.append(
            _issue(
                "error", "lesson_invalid", f"{where} : une leçon doit être un objet JSON.", lesson_index=lesson_index
            )
        )
        return None

    slug = str(raw.get("subject_slug") or "").strip()
    if slug not in known_slugs:
        errors.append(
            _issue(
                "error",
                "subject_unknown",
                f"{where} : matière « {slug} » inconnue. Matières acceptées : {', '.join(sorted(known_slugs))}.",
                lesson_index=lesson_index,
                field="subject_slug",
            )
        )

    level: LevelEnum | None = None
    try:
        level = LevelEnum(str(raw.get("level") or "").strip().lower())
    except ValueError:
        accepted = ", ".join(item.value for item in LevelEnum)
        errors.append(
            _issue(
                "error",
                "level_unknown",
                f"{where} : niveau « {raw.get('level')} » inconnu. Niveaux acceptés : {accepted}.",
                lesson_index=lesson_index,
                field="level",
            )
        )

    try:
        tier = int(raw.get("tier", 1))
    except (TypeError, ValueError):
        tier = 0
    if tier < 1:
        errors.append(
            _issue(
                "error",
                "tier_invalid",
                f"{where} : tier={raw.get('tier')!r} invalide. Attendu 1 (Découverte), 2 (Entraînement) ou 3 (Défi).",
                lesson_index=lesson_index,
                field="tier",
            )
        )
        tier = 1

    name = str(raw.get("name") or "").strip()
    if not name:
        errors.append(
            _issue(
                "error",
                "lesson_name_missing",
                f"{where} : nom de leçon vide. Donnez un titre lisible par un enfant.",
                lesson_index=lesson_index,
                field="name",
            )
        )
    if "xp_reward" in raw:
        soft.append(
            _issue(
                "warning",
                "xp_ignored",
                f"{where} : xp_reward est ignoré, l'XP est recalculée depuis les difficultés "
                "des exercices. Retirez le champ.",
                lesson_index=lesson_index,
                field="xp_reward",
            )
        )

    description = raw.get("description")
    for field, text in (("name", name), ("description", description)):
        if isinstance(text, str) and text:
            _check_text(text, field, errors, soft, lesson_index=lesson_index)

    exercises_raw = raw.get("exercises")
    if not isinstance(exercises_raw, list) or not exercises_raw:
        errors.append(
            _issue(
                "error",
                "exercises_missing",
                f"{where} : aucune liste « exercises ». Une leçon vide n'est pas jouable.",
                lesson_index=lesson_index,
                field="exercises",
            )
        )
        exercises_raw = []
    elif len(exercises_raw) > settings.PACK_MAX_EXERCISES_PER_LESSON:
        errors.append(
            _issue(
                "error",
                "too_many_exercises",
                f"{where} : {len(exercises_raw)} exercices pour un maximum de "
                f"{settings.PACK_MAX_EXERCISES_PER_LESSON}. Découpez la leçon en plusieurs paliers.",
                lesson_index=lesson_index,
                field="exercises",
            )
        )
        exercises_raw = exercises_raw[: settings.PACK_MAX_EXERCISES_PER_LESSON]

    max_question_chars = LEVEL_MAX_QUESTION_CHARS.get(level or LevelEnum.CM2, 400)
    exercises: list[dict[str, Any]] = []
    for idx, raw_exercise in enumerate(exercises_raw):
        normalised = _validate_exercise(raw_exercise, lesson_index, idx, max_question_chars, errors, soft)
        if normalised is not None:
            exercises.append(normalised)

    if level is None:
        return None
    return {
        "subject_slug": slug,
        "level": level.value,
        "tier": tier,
        "name": name,
        "description": str(description).strip() if isinstance(description, str) and description.strip() else None,
        "exercises": exercises,
    }


def _structural_warnings(lessons: list[dict[str, Any]], payload: dict[str, Any]) -> list[ValidationIssue]:
    """Avertissements pédagogiques : ils nourrissent le score, ne bloquent rien."""
    issues: list[ValidationIssue] = []

    if len(lessons) == 1:
        issues.append(
            _issue(
                "warning",
                "single_lesson",
                "Pack d'une seule leçon : la progression par paliers n'a rien à débloquer. "
                "Deux ou trois leçons de difficulté croissante fonctionnent mieux.",
            )
        )

    difficulties = [ex["difficulty_level"] for lesson in lessons for ex in lesson["exercises"]]
    if len(difficulties) >= 3 and len(set(difficulties)) == 1:
        issues.append(
            _issue(
                "warning",
                "flat_difficulty",
                f"Tous les exercices sont en difficulté {difficulties[0]} : la courbe est plate. "
                "Faites monter la difficulté au fil des exercices et des leçons.",
            )
        )

    types = [ex["type"] for lesson in lessons for ex in lesson["exercises"]]
    if len(types) >= 5 and len(set(types)) == 1:
        issues.append(
            _issue(
                "warning",
                "no_type_mix",
                f"Les {len(types)} exercices sont tous du même type ({types[0]}) : alternez les types "
                "(QCM, texte à trous, problème, lecture) pour tenir l'attention.",
            )
        )

    if not isinstance(payload.get("self_check"), dict):
        issues.append(
            _issue(
                "warning",
                "self_check_missing",
                "Bloc « self_check » absent : déclarez-y que les calculs et les réponses ont été "
                'vérifiés (ex. {"math_verified": true, "notes": "..."}).',
                field="self_check",
            )
        )
    return issues


def _duplicate_flags(lessons: list[dict[str, Any]]) -> list[ValidationIssue]:
    """Repère les redites **internes** au pack (titres et questions identiques)."""
    issues: list[ValidationIssue] = []
    seen_names: dict[str, int] = {}
    for index, lesson in enumerate(lessons):
        key = normalised_title(lesson["name"])
        if key and key in seen_names:
            issues.append(
                _issue(
                    "flag",
                    "near_duplicate",
                    f"leçon {index + 1} porte le même titre que la leçon {seen_names[key] + 1}. "
                    "Ce n'est pas un refus : ce peut être une seconde version assumée.",
                    lesson_index=index,
                    field="name",
                )
            )
        else:
            seen_names[key] = index

    seen_questions: dict[str, tuple[int, int]] = {}
    for l_index, lesson in enumerate(lessons):
        for e_index, exercise in enumerate(lesson["exercises"]):
            key = normalised_title(exercise["question"])
            if not key:
                continue
            if key in seen_questions:
                first_l, first_e = seen_questions[key]
                issues.append(
                    _issue(
                        "flag",
                        "near_duplicate",
                        f"leçon {l_index + 1}, exercice {e_index + 1} reprend mot pour mot la question de "
                        f"la leçon {first_l + 1}, exercice {first_e + 1}.",
                        lesson_index=l_index,
                        exercise_index=e_index,
                        field="question",
                    )
                )
            else:
                seen_questions[key] = (l_index, e_index)
    return issues


def validate_pack(
    payload: dict[str, Any],
    *,
    known_subject_slugs: Collection[str] | None = None,
) -> tuple[dict[str, Any], list[ValidationIssue], int]:
    """Valide un document `.explorito` et renvoie sa forme normalisée.

    Args:
        payload: Document `.explorito` déjà désérialisé.
        known_subject_slugs: Matières existantes. Les appelants disposant d'une
            session passent les slugs réellement en base ; à défaut, les matières
            canoniques du curriculum servent de référence.

    Returns:
        Un triplet ``(payload normalisé, constats non bloquants, score qualité)``.
        Le payload normalisé ne contient **aucune** XP déclarée par l'auteur.

    Raises:
        PackRejected: Si au moins une erreur dure est détectée ; l'exception
            porte la liste exhaustive des erreurs, prête à être renvoyée telle
            quelle à l'outil d'écriture.
    """
    known_slugs = set(known_subject_slugs) if known_subject_slugs else set(CANONICAL_SUBJECT_SLUGS)
    errors: list[ValidationIssue] = []
    soft: list[ValidationIssue] = []

    if not isinstance(payload, dict):
        raise PackRejected(
            [_issue("error", "payload_invalid", "Le fichier .explorito doit contenir un objet JSON à la racine.")]
        )

    version = payload.get("format_version")
    if version != settings.PACK_FORMAT_VERSION:
        # Refus immédiat : interpréter une version inconnue avec les règles de la
        # version courante produirait des faux diagnostics sur tout le reste.
        raise PackRejected(
            [
                _issue(
                    "error",
                    "format_version_unknown",
                    f"format_version={version!r} non pris en charge : cette instance lit uniquement la "
                    f"version {settings.PACK_FORMAT_VERSION}. Régénérez le fichier avec "
                    f'"format_version": {settings.PACK_FORMAT_VERSION}.',
                    field="format_version",
                )
            ]
        )

    pack_header = _validate_pack_header(payload, errors, soft)

    lessons_raw = payload.get("lessons")
    if not isinstance(lessons_raw, list) or not lessons_raw:
        errors.append(
            _issue(
                "error",
                "lessons_missing",
                "Aucune leçon : « lessons » doit être une liste d'au moins une leçon.",
                field="lessons",
            )
        )
        lessons_raw = []
    elif len(lessons_raw) > settings.PACK_MAX_LESSONS:
        errors.append(
            _issue(
                "error",
                "too_many_lessons",
                f"{len(lessons_raw)} leçons pour un maximum de {settings.PACK_MAX_LESSONS} par pack. "
                "Scindez le contenu en plusieurs packs thématiques.",
                field="lessons",
            )
        )
        # Tronqué pour ne pas valider (et détailler) un envoi délirant : le refus
        # sur le plafond suffit, inutile de produire mille messages en plus.
        lessons_raw = lessons_raw[: settings.PACK_MAX_LESSONS]

    lessons: list[dict[str, Any]] = []
    for index, raw_lesson in enumerate(lessons_raw):
        normalised = _validate_lesson(raw_lesson, index, known_slugs, errors, soft)
        if normalised is not None:
            lessons.append(normalised)

    if errors:
        raise PackRejected(errors)

    soft.extend(_structural_warnings(lessons, payload))
    soft.extend(_duplicate_flags(lessons))

    self_check = payload.get("self_check")
    normalised_payload: dict[str, Any] = {
        "format_version": settings.PACK_FORMAT_VERSION,
        "pack": pack_header,
        "lessons": lessons,
        "self_check": self_check if isinstance(self_check, dict) else None,
    }
    return normalised_payload, soft, quality_score(soft)
