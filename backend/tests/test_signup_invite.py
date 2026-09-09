"""Porte d'entrée : code d'invitation à l'inscription (issue #22).

L'inscription était ouverte à quiconque avait l'URL. Ces tests décrivent la
porte : elle ne se referme que sur la **création** d'un compte, jamais sur la
connexion d'une famille déjà installée.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.guardianship import INVITE_ALL, INVITE_SIGNUP, Invitation
from app.models.user import User
from tests.helpers import dev_login, ensure_parent

NEWCOMER = "famille.amie@exemple.fr"


@pytest.fixture
def invite_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Referme la porte d'entrée pour la durée du test."""
    monkeypatch.setattr(settings, "SIGNUP_INVITE_REQUIRED", True)


def _signup(client: TestClient, email: str, invite: str | None = None):
    body: dict[str, str] = {"email": email}
    if invite is not None:
        body["invite"] = invite
    return client.post("/api/v1/auth/dev-login", json=body)


ADMIN_EMAIL = "admin@qa.fr"


@pytest.fixture
def admin_headers(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """En-têtes d'un compte admin (le rôle est recalculé depuis l'allowlist à chaque connexion)."""
    monkeypatch.setattr(settings, "ADMIN_EMAILS", ADMIN_EMAIL)
    return dev_login(client, ADMIN_EMAIL)


def _make_code(client: TestClient, admin_headers: dict[str, str]) -> str:
    """Crée un code d'inscription via la surface admin."""
    response = client.post("/api/v1/admin/signup-invites", headers=admin_headers)
    assert response.status_code == 201, response.text
    return response.json()["token"]


# --------------------------------------------------------------------------- #
# Réglage désactivé : rien ne change
# --------------------------------------------------------------------------- #
def test_signup_stays_open_while_the_setting_is_off(client: TestClient):
    """Défaut `False` : l'inscription libre, comportement historique, est intacte."""
    assert settings.SIGNUP_INVITE_REQUIRED is False

    assert _signup(client, NEWCOMER).status_code == 200


# --------------------------------------------------------------------------- #
# Réglage activé : la porte se referme sur la création
# --------------------------------------------------------------------------- #
def test_a_stranger_without_a_code_is_turned_away(client: TestClient, invite_required: None):
    """403 et un message qui dit quoi faire, pas une erreur technique."""
    response = _signup(client, NEWCOMER)

    assert response.status_code == 403, response.text
    assert "invitation" in response.json()["detail"].lower()


def test_a_valid_code_lets_the_family_in(
    client: TestClient,
    db_session: Session,
    admin_headers: dict[str, str],
    invite_required: None,
):
    """Le chemin heureux : un code valide crée le compte, et le code est consommé."""
    token = _make_code(client, admin_headers)

    assert _signup(client, NEWCOMER, token).status_code == 200, "le code valide doit ouvrir"

    invitation = db_session.query(Invitation).filter(Invitation.token == token).one()
    created = db_session.query(User).filter(User.email == NEWCOMER).one()
    assert invitation.accepted_at is not None
    assert invitation.accepted_by == created.id


def test_a_code_serves_exactly_one_family(
    client: TestClient,
    db_session: Session,
    admin_headers: dict[str, str],
    invite_required: None,
):
    """« Un code = une famille » : le second usage est refusé."""
    token = _make_code(client, admin_headers)
    assert _signup(client, NEWCOMER, token).status_code == 200

    second = _signup(client, "autre.famille@exemple.fr", token)

    assert second.status_code == 403, second.text
    assert db_session.query(User).filter(User.email == "autre.famille@exemple.fr").first() is None


def test_an_expired_code_is_refused(
    client: TestClient,
    db_session: Session,
    admin_headers: dict[str, str],
    invite_required: None,
):
    """Un code périmé ne vaut pas mieux qu'aucun code."""
    token = _make_code(client, admin_headers)
    invitation = db_session.query(Invitation).filter(Invitation.token == token).one()
    invitation.expires_at = datetime.utcnow() - timedelta(days=1)
    db_session.commit()

    assert _signup(client, NEWCOMER, token).status_code == 403


def test_a_revoked_code_is_refused(
    client: TestClient,
    db_session: Session,
    admin_headers: dict[str, str],
    invite_required: None,
):
    """Révoquer un code doit réellement refermer la porte."""
    token = _make_code(client, admin_headers)
    revoked = client.delete(
        f"/api/v1/admin/signup-invites/{token}",
        headers=admin_headers,
    )
    assert revoked.status_code == 204, revoked.text

    assert _signup(client, NEWCOMER, token).status_code == 403


def test_an_unknown_code_is_refused(client: TestClient, invite_required: None):
    """Un jeton inventé n'ouvre rien."""
    assert _signup(client, NEWCOMER, "ce-code-nexiste-pas").status_code == 403


def test_a_guardianship_invitation_is_not_a_signup_code(
    client: TestClient,
    db_session: Session,
    invite_required: None,
):
    """Un lien de partage de garde ne doit pas ouvrir la porte d'inscription.

    Les deux jetons vivent dans la même table : confondre les `kind` laisserait
    n'importe quel lien de partage — qui circule bien plus largement — servir
    d'inscription.
    """
    inviter = ensure_parent(db_session, "hote@exemple.fr")
    sharing = Invitation(
        token="jeton-de-partage",
        inviter_id=inviter.id,
        kind=INVITE_ALL,
        child_id=None,
        role="parent",
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db_session.add(sharing)
    db_session.commit()

    assert _signup(client, NEWCOMER, "jeton-de-partage").status_code == 403


# --------------------------------------------------------------------------- #
# Ce que la porte ne doit jamais casser
# --------------------------------------------------------------------------- #
def test_an_existing_family_is_never_locked_out(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    """Activer le réglage ne verrouille pas dehors une famille déjà installée.

    C'est la garantie qui rend le réglage activable sans prévenir personne.
    """
    assert _signup(client, "deja.la@exemple.fr").status_code == 200

    monkeypatch.setattr(settings, "SIGNUP_INVITE_REQUIRED", True)

    again = _signup(client, "deja.la@exemple.fr")
    assert again.status_code == 200, again.text


def test_a_signup_code_cannot_be_burnt_by_the_sharing_route(
    client: TestClient,
    db_session: Session,
    admin_headers: dict[str, str],
    invite_required: None,
):
    """Accepter un code d'inscription comme un partage n'accorde rien — et ne le consomme pas.

    Sans ce garde-fou, la route de partage marquait le code accepté tout en
    n'accordant aucune garde : le code était perdu pour la famille invitée.
    """
    token = _make_code(client, admin_headers)
    ensure_parent(db_session, "curieux@exemple.fr")

    response = client.post(
        f"/api/v1/invitations/{token}/accept",
        headers=dev_login(client, "curieux@exemple.fr"),
    )

    assert response.status_code == 400, response.text
    invitation = db_session.query(Invitation).filter(Invitation.token == token).one()
    assert invitation.accepted_at is None, "le code doit rester utilisable"
    assert invitation.is_usable


def test_the_public_preview_of_a_signup_code_leaks_nothing(
    client: TestClient,
    admin_headers: dict[str, str],
    invite_required: None,
):
    """L'aperçu public dit « valide », sans publier les prénoms des enfants de l'hôte."""
    token = _make_code(client, admin_headers)

    preview = client.get(f"/api/v1/invitations/{token}")

    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["valid"] is True
    assert body["kind"] == INVITE_SIGNUP
    assert body["children_names"] == []
    assert body["inviter_name"] is None


def test_the_admin_sees_the_link_to_hand_over(client: TestClient, admin_headers: dict[str, str]):
    """La surface admin liste les codes et fournit le lien prêt à transmettre."""
    token = _make_code(client, admin_headers)

    listed = client.get("/api/v1/admin/signup-invites", headers=admin_headers)

    assert listed.status_code == 200, listed.text
    rows = {row["token"]: row for row in listed.json()}
    assert token in rows
    assert rows[token]["url"].endswith(f"/register?invite={token}")
    assert rows[token]["is_usable"] is True


def test_signup_codes_are_admin_only(client: TestClient, db_session: Session):
    """Un parent ordinaire ne fabrique pas ses propres invitations."""
    ensure_parent(db_session, "parent.ordinaire@exemple.fr")

    response = client.post(
        "/api/v1/admin/signup-invites",
        headers=dev_login(client, "parent.ordinaire@exemple.fr"),
    )

    assert response.status_code == 403, response.text
