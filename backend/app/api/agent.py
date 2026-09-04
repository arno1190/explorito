"""Instructions publiques pour les assistants IA (« charge ta compétence ici »).

Raison d'être, constatée en production : un parent a collé la phrase
« Connecte-toi à Explorito avec le code Q97E-89JJ, puis fais-moi un pack… »
dans un assistant neuf. L'assistant ne connaissait pas Explorito, a cherché sur
le web, deviné ``/device``, ``/code``, ``/connect``, ``/mcp``, récolté quatre
404 et abandonné en redemandant l'adresse au parent.

Deux causes, toutes deux fatales pour l'adoption :

1. la phrase à recopier ne portait ni hôte, ni point d'entrée, ni instructions ;
2. la compétence de rédaction vivait dans ``.claude/skills/``, **ignoré par
   git** : elle n'a jamais été livrée et ne pouvait atteindre personne.

D'où ce module : le texte de référence est versionné dans ``app/agent/``, donc
embarqué dans l'image, et servi **sans authentification**. N'importe quel
assistant capable de lire une URL peut s'auto-instruire — aucun greffon, aucune
installation, aucune variable d'environnement.

Les documents servis ne contiennent jamais d'hôte en dur : ``{{API_BASE}}`` et
``{{APP_URL}}`` sont substitués à la volée depuis la requête et la
configuration, de sorte qu'une instance auto-hébergée renvoie ses propres URLs.
"""

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import PlainTextResponse

from app.core.config import settings

router = APIRouter()

#: Répertoire des documents de référence, embarqué dans l'image (``COPY . .``).
AGENT_DOCS_DIR = Path(__file__).resolve().parent.parent / "agent"

#: Documents publiés, du plus utile au moins utile pour un assistant qui arrive
#: sans rien savoir. Le slug fait partie du contrat : il est cité dans la phrase
#: que le parent recopie, donc il ne change pas sans casser des copier-coller.
AGENT_DOCS: dict[str, str] = {
    "pack-author": "Rédiger et déposer un pack de leçons Explorito (guide complet, autoportant)",
    "rubric": "Bornes de contenu par niveau scolaire, de la petite section au CM2",
}


@lru_cache(maxsize=len(AGENT_DOCS))
def _read_doc(slug: str) -> str:
    """Contenu brut d'un document de référence (lu une fois, immuable en image)."""
    return (AGENT_DOCS_DIR / f"{slug}.md").read_text(encoding="utf-8")


def _api_base(request: Request) -> str:
    """Base publique de l'API, déduite de la requête reçue.

    Déduite plutôt que configurée : derrière Caddy, la requête porte déjà le
    bon hôte et le bon schéma, et un réglage de plus serait un réglage de plus à
    oublier — c'est exactement ce qui a rendu ``PUBLIC_APP_URL`` absente en
    production.
    """
    return str(request.base_url).rstrip("/")


def _render(slug: str, request: Request) -> str:
    """Document avec ses URLs substituées."""
    return (
        _read_doc(slug)
        .replace("{{API_BASE}}", _api_base(request))
        .replace("{{APP_URL}}", settings.PUBLIC_APP_URL.rstrip("/"))
    )


@router.get("")
async def manifest(request: Request) -> dict:
    """Point d'entrée pour un assistant : quoi lire, où envoyer, quelles limites.

    Volontairement plat et sans authentification : c'est la première requête
    d'un agent qui ne sait rien, et elle doit suffire à trouver le reste.
    """
    base = _api_base(request)
    return {
        "name": "Explorito",
        "description": (
            "Application éducative pour enfants (programme français, de la petite section au CM2). "
            "Un parent peut faire rédiger des leçons par son propre assistant IA et les déposer ici."
        ),
        "format_version": settings.PACK_FORMAT_VERSION,
        "app_url": settings.PUBLIC_APP_URL.rstrip("/"),
        "docs": [
            {"slug": slug, "title": title, "url": f"{base}/api/v1/agent/{slug}.md"}
            for slug, title in AGENT_DOCS.items()
        ],
        "endpoints": {
            "pairing_claim": f"{base}{settings.API_PREFIX}/contributions/pairing/claim",
            "upload": f"{base}{settings.API_PREFIX}/contributions",
            "terms": f"{base}{settings.API_PREFIX}/contributions/terms",
            "my_packs": f"{base}{settings.API_PREFIX}/contributions",
        },
        "limits": {
            "max_lessons": settings.PACK_MAX_LESSONS,
            "max_exercises_per_lesson": settings.PACK_MAX_EXERCISES_PER_LESSON,
            "max_text_length": settings.PACK_MAX_TEXT_LENGTH,
            "max_uploads_per_day": settings.PACK_MAX_UPLOADS_PER_DAY,
            "max_file_size": settings.PACK_MAX_FILE_SIZE,
        },
    }


@router.get("/{slug}.md", response_class=PlainTextResponse)
async def document(slug: str, request: Request) -> PlainTextResponse:
    """Sert un document de référence en Markdown, sans authentification."""
    if slug not in AGENT_DOCS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "unknown_doc",
                "message": f"Document inconnu. Disponibles : {', '.join(sorted(AGENT_DOCS))}.",
            },
        )
    return PlainTextResponse(
        _render(slug, request),
        media_type="text/markdown; charset=utf-8",
        # Le contenu ne change qu'au déploiement : un cache court évite de
        # relire le fichier à chaque agent curieux, sans figer une correction.
        headers={"Cache-Control": "public, max-age=600"},
    )


@router.get("/{slug}", response_class=PlainTextResponse)
async def document_without_extension(slug: str, request: Request) -> PlainTextResponse:
    """Même document sans le suffixe ``.md``.

    Un agent recopie l'URL de mémoire ou tronque l'extension : renvoyer un 404
    pour une virgule d'écart est exactement le mur sur lequel nous venons de
    buter en production.
    """
    return await document(slug.removesuffix(".md"), request)


@router.get("/{slug}.md/", include_in_schema=False)
async def document_trailing_slash(slug: str, request: Request) -> PlainTextResponse:
    """Tolère la barre oblique finale, pour la même raison."""
    return await document(slug, request)
