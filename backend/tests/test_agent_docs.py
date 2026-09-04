"""Tests des instructions publiques pour assistants IA.

Ces routes existent parce qu'un assistant neuf, à qui un parent avait collé la
phrase de connexion, n'avait aucun moyen de savoir ce qu'est Explorito : il a
deviné des URLs et récolté des 404. Les garanties testées ici sont donc celles
de l'auto-instruction : aucune authentification, aucun hôte en dur, et une
tolérance sur la forme de l'URL.
"""

from fastapi.testclient import TestClient

from app.api.agent import AGENT_DOCS
from app.core.config import settings


def test_manifest_is_public_and_points_at_everything_needed(client: TestClient):
    response = client.get("/api/v1/agent")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["format_version"] == settings.PACK_FORMAT_VERSION
    assert {doc["slug"] for doc in body["docs"]} == set(AGENT_DOCS)
    # Un agent doit pouvoir suivre les URLs telles quelles.
    for doc in body["docs"]:
        assert doc["url"].endswith(f"/api/v1/agent/{doc['slug']}.md")
        assert client.get(doc["url"]).status_code == 200
    assert body["endpoints"]["pairing_claim"].endswith("/contributions/pairing/claim")
    assert body["endpoints"]["upload"].endswith("/contributions")
    assert body["limits"]["max_lessons"] == settings.PACK_MAX_LESSONS


def test_documents_are_served_as_markdown_without_auth(client: TestClient):
    for slug in AGENT_DOCS:
        response = client.get(f"/api/v1/agent/{slug}.md")
        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("text/markdown")
        assert len(response.text) > 500


def test_no_placeholder_survives_and_no_host_is_hardcoded(client: TestClient):
    """Les documents servis doivent porter l'hôte de *cette* instance, pas le nôtre."""
    for slug in AGENT_DOCS:
        text = client.get(f"/api/v1/agent/{slug}.md").text
        assert "{{API_BASE}}" not in text
        assert "{{APP_URL}}" not in text
        # Une instance auto-hébergée ne doit jamais se voir renvoyer notre domaine.
        assert "explorito.pascalfamily.fr" not in text


def test_pack_author_guide_is_self_sufficient(client: TestClient):
    """Le guide doit contenir de quoi s'authentifier, écrire et envoyer, sans rien demander."""
    text = client.get("/api/v1/agent/pack-author.md").text

    for needle in (
        "/contributions/pairing/claim",  # étape 0 : échanger le code
        "/api/v1/contributions",  # étape finale : déposer le brouillon
        "X-Upload-Token",
        "difficulty_level",
        "format_version",
        "self_check",
        "rubric.md",  # renvoi vers les bornes du niveau
    ):
        assert needle in text, f"guide incomplet : {needle} absent"


def test_url_shape_is_forgiving(client: TestClient):
    """Extension oubliée ou barre oblique en trop : un agent ne doit pas buter là-dessus."""
    canonical = client.get("/api/v1/agent/pack-author.md").text
    assert client.get("/api/v1/agent/pack-author").text == canonical
    assert client.get("/api/v1/agent/pack-author.md/").text == canonical


def test_unknown_document_names_what_exists(client: TestClient):
    response = client.get("/api/v1/agent/mcp.md")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "unknown_doc"
    # Le message doit permettre de rebondir plutôt que d'abandonner.
    assert "pack-author" in detail["message"]
