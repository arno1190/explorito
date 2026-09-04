"""Tests de l'entrée dans la contribution : acceptation des conditions et appariement.

Les deux mécanismes testés ici existent pour la même raison — l'abandon à
l'inscription. Les conditions surgissaient sous forme de 428 au premier envoi,
c'est-à-dire au pire moment ; et connecter un assistant demandait de poser une
variable d'environnement dans un terminal, ce qu'un parent ne fera pas.

Auth : parent via ``/auth/dev-login`` (monté seulement si DEBUG).
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.contribution import ContributorProfile, UploadPairing, UploadToken
from app.services.contributor_legal import CONTRIBUTOR_TERMS_VERSION
from tests.helpers import dev_login
from tests.test_pack_format import pack

PARENT = "appariement@qa.fr"


def test_terms_state_is_readable_before_any_upload(client: TestClient):
    """La page de contribution doit pouvoir se verrouiller *avant* le premier envoi."""
    headers = dev_login(client, PARENT)

    state = client.get("/api/v1/contributions/terms", headers=headers)
    assert state.status_code == 200, state.text
    body = state.json()
    assert body["accepted"] is False
    assert body["handle"] is None
    assert body["version"] == CONTRIBUTOR_TERMS_VERSION
    # Le texte doit être servi avec l'état : la modale l'affiche sans second appel.
    assert len(body["text"]) > 200


def test_accepting_terms_records_version_timestamp_and_handle(client: TestClient, db_session: Session):
    headers = dev_login(client, PARENT)

    accepted = client.post("/api/v1/contributions/terms/accept", json={"handle": "PapaRenard"}, headers=headers)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["accepted"] is True
    assert accepted.json()["handle"] == "PapaRenard"

    profile = db_session.query(ContributorProfile).filter(ContributorProfile.handle == "PapaRenard").first()
    assert profile is not None
    assert profile.terms_version == CONTRIBUTOR_TERMS_VERSION
    assert profile.terms_accepted_at is not None

    # Et l'état relu est cohérent : c'est ce que la page interroge au chargement.
    assert client.get("/api/v1/contributions/terms", headers=headers).json()["accepted"] is True


def test_accepted_terms_make_the_first_upload_pass_without_any_parameter(client: TestClient):
    """Une fois acceptées dans l'application, plus aucun ``accept_terms`` n'est requis.

    C'est tout l'intérêt : la compétence d'écriture n'a plus à transporter
    l'acceptation juridique dans une chaîne de requête.
    """
    headers = dev_login(client, PARENT)
    client.post("/api/v1/contributions/terms/accept", json={"handle": "PapaRenard"}, headers=headers)

    response = client.post("/api/v1/contributions", json=pack(), headers=headers)
    assert response.status_code == 201, response.text


def test_upload_without_accepted_terms_still_refuses_with_428(client: TestClient):
    """Le 428 reste le filet : il ne disparaît pas, il cesse d'être le seul chemin."""
    headers = dev_login(client, PARENT)

    response = client.post("/api/v1/contributions", json=pack(), headers=headers)
    assert response.status_code == 428
    assert response.json()["detail"]["code"] == "terms_required"


def test_a_handle_cannot_be_stolen_through_the_accept_route(client: TestClient):
    dev_headers = dev_login(client, PARENT)
    client.post("/api/v1/contributions/terms/accept", json={"handle": "PapaRenard"}, headers=dev_headers)

    other = dev_login(client, "voleur@qa.fr")
    stolen = client.post("/api/v1/contributions/terms/accept", json={"handle": "PapaRenard"}, headers=other)
    assert stolen.status_code == 409


def test_pairing_code_exchanges_for_a_draft_only_token(client: TestClient, db_session: Session):
    """Le parent dicte huit caractères ; l'assistant obtient un jeton et publie rien."""
    headers = dev_login(client, PARENT)
    client.post("/api/v1/contributions/terms/accept", json={"handle": "PapaRenard"}, headers=headers)

    started = client.post("/api/v1/contributions/pairing", headers=headers)
    assert started.status_code == 201, started.text
    code = started.json()["code"]
    assert len(code) == 8
    # Alphabet dicté à voix haute : aucun caractère ambigu.
    assert not set(code) & set("OIL01UV")

    claimed = client.post("/api/v1/contributions/pairing/claim", json={"code": code})
    assert claimed.status_code == 200, claimed.text
    body = claimed.json()
    assert body["handle"] == "PapaRenard"
    assert body["terms_accepted"] is True
    assert body["token"] and body["token"].startswith(body["prefix"])

    # Le jeton obtenu crée un brouillon…
    upload = client.post("/api/v1/contributions", json=pack(), headers={"X-Upload-Token": body["token"]})
    assert upload.status_code == 201, upload.text
    # …et ne peut pas le soumettre.
    submit = client.post(
        f"/api/v1/contributions/{upload.json()['pack_id']}/submit",
        headers={"X-Upload-Token": body["token"]},
    )
    assert submit.status_code == 403

    # Le secret n'est jamais stocké en clair.
    stored = db_session.query(UploadToken).filter(UploadToken.prefix == body["prefix"]).first()
    assert stored is not None and body["token"] not in stored.token_hash


def test_pairing_code_is_single_use(client: TestClient):
    headers = dev_login(client, PARENT)
    code = client.post("/api/v1/contributions/pairing", headers=headers).json()["code"]

    assert client.post("/api/v1/contributions/pairing/claim", json={"code": code}).status_code == 200
    replayed = client.post("/api/v1/contributions/pairing/claim", json={"code": code})
    assert replayed.status_code == 404
    assert replayed.json()["detail"]["code"] == "pairing_invalid"


def test_pairing_code_is_case_and_dash_insensitive(client: TestClient):
    """Un code dicté est retapé comme il est entendu : « k7qf-3m2p » doit passer."""
    headers = dev_login(client, PARENT)
    code = client.post("/api/v1/contributions/pairing", headers=headers).json()["code"]
    typed = f"{code[:4].lower()}-{code[4:].lower()}"

    assert client.post("/api/v1/contributions/pairing/claim", json={"code": typed}).status_code == 200


def test_expired_pairing_code_is_refused(client: TestClient, db_session: Session):
    headers = dev_login(client, PARENT)
    code = client.post("/api/v1/contributions/pairing", headers=headers).json()["code"]

    pairing = db_session.query(UploadPairing).filter(UploadPairing.claimed_at.is_(None)).one()
    pairing.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()

    refused = client.post("/api/v1/contributions/pairing/claim", json={"code": code})
    assert refused.status_code == 404
    assert refused.json()["detail"]["code"] == "pairing_invalid"


def test_a_new_code_kills_the_previous_one(client: TestClient):
    """Un code affiché puis abandonné sur un écran ne doit pas rester échangeable."""
    headers = dev_login(client, PARENT)
    first = client.post("/api/v1/contributions/pairing", headers=headers).json()["code"]
    second = client.post("/api/v1/contributions/pairing", headers=headers).json()["code"]
    assert first != second

    assert client.post("/api/v1/contributions/pairing/claim", json={"code": first}).status_code == 404
    assert client.post("/api/v1/contributions/pairing/claim", json={"code": second}).status_code == 200


def test_unknown_code_is_refused_and_reveals_nothing(client: TestClient):
    refused = client.post("/api/v1/contributions/pairing/claim", json={"code": "ZZZZ9999"})
    assert refused.status_code == 404
    body = refused.json()["detail"]
    assert body["code"] == "pairing_invalid"
    # Le message ne distingue pas inconnu / expiré / déjà utilisé.
    assert "inconnu, expiré ou déjà utilisé" in body["message"]


def test_pairing_requires_a_session(client: TestClient):
    """Émettre un code est un geste d'adulte connecté ; le réclamer ne l'est pas."""
    assert client.post("/api/v1/contributions/pairing").status_code == 401


def test_an_upload_token_cannot_accept_the_terms(client: TestClient):
    """Un jeton long ne signe pas un engagement juridique au nom d'une personne."""
    headers = dev_login(client, PARENT)
    code = client.post("/api/v1/contributions/pairing", headers=headers).json()["code"]
    token = client.post("/api/v1/contributions/pairing/claim", json={"code": code}).json()["token"]

    refused = client.post(
        "/api/v1/contributions/terms/accept",
        json={"handle": "AssistantMalin"},
        headers={"X-Upload-Token": token},
    )
    assert refused.status_code == 401
