"""Porte d'entrée : code d'invitation à l'inscription (issue #22).

L'inscription était ouverte à quiconque avait l'URL. Ces tests décrivent la
porte : elle ne se referme que sur la **création** d'un compte, jamais sur la
connexion d'une famille déjà installée.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api import auth as auth_module
from app.core.config import settings
from app.models.guardianship import INVITE_ALL, INVITE_SIGNUP, Guardianship, Invitation
from app.models.user import User
from app.services.guardianship import consume_signup_invitation, create_signup_invitation
from tests.helpers import dev_login, ensure_parent, make_child

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


def _google_signin(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    email: str,
    invite: str | None = None,
):
    """Vraie route de production : ``POST /auth/google``, vérification Google neutralisée.

    ``/dev-login`` n'est monté que sous ``DEBUG`` et n'existe donc pas sur le
    serveur : seule cette route-ci décide qui obtient un compte en vrai.
    """
    monkeypatch.setattr(
        auth_module,
        "verify_google_id_token",
        lambda credential: {
            "email": email,
            "email_verified": True,
            "name": "Famille Test",
            "sub": f"google-sub-{email}",
        },
    )
    body: dict[str, str] = {"credential": "id-token-factice"}
    if invite is not None:
        body["invite"] = invite
    return client.post("/api/v1/auth/google", json=body)


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


def _sharing_invitation(db: Session, inviter_email: str = "hote@exemple.fr") -> Invitation:
    """Invitation de co-parentalité (kind ``all``) émise par un parent avec un enfant."""
    make_child(db, parent_email=inviter_email, name="Lila")
    inviter = ensure_parent(db, inviter_email)
    sharing = Invitation(
        token="jeton-de-partage",
        inviter_id=inviter.id,
        kind=INVITE_ALL,
        child_id=None,
        role="parent",
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(sharing)
    db.commit()
    return sharing


def test_an_invited_coparent_gets_an_account_without_burning_the_sharing_link(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    invite_required: None,
):
    """Être invité à co-parenter vaut droit d'avoir un compte — et le lien survit.

    Sans cela, refermer la porte d'entrée condamnait tout le parcours de partage :
    le grand-parent invité arrivait sur son lien et se prenait un 403. Le jeton
    ne doit pas non plus être consommé à l'inscription, sinon il n'accorderait
    plus aucune garde ensuite.
    """
    _sharing_invitation(db_session)

    created = _google_signin(client, monkeypatch, NEWCOMER, "jeton-de-partage")

    assert created.status_code == 200, created.text
    invitation = db_session.query(Invitation).filter(Invitation.token == "jeton-de-partage").one()
    assert invitation.accepted_at is None, "le partage ne se consomme pas à l'inscription"

    accepted = client.post(
        "/api/v1/invitations/jeton-de-partage/accept",
        headers={"Authorization": f"Bearer {created.json()['access_token']}"},
    )

    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["granted"] == 1
    newcomer = db_session.query(User).filter(User.email == NEWCOMER).one()
    assert db_session.query(Guardianship).filter(Guardianship.guardian_id == newcomer.id).count() == 1


def test_a_revoked_sharing_link_opens_nothing(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    invite_required: None,
):
    """Un partage révoqué n'est plus un droit d'inscription non plus."""
    sharing = _sharing_invitation(db_session)
    sharing.revoked_at = datetime.utcnow()
    db_session.commit()

    assert _google_signin(client, monkeypatch, NEWCOMER, "jeton-de-partage").status_code == 403
    assert db_session.query(User).filter(User.email == NEWCOMER).first() is None


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


# --------------------------------------------------------------------------- #
# La vraie porte de production : POST /auth/google
# --------------------------------------------------------------------------- #
# `/dev-login` n'est monté que sous DEBUG : en production, `/auth/google` est le
# seul chemin d'inscription. Ces tests-là sont ceux qui tombent si le câblage
# `invite_token=payload.invite` disparaît du handler.
def test_google_refuses_a_stranger_without_a_code(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    invite_required: None,
):
    """Un inconnu qui se connecte avec Google n'obtient pas de compte."""
    response = _google_signin(client, monkeypatch, NEWCOMER)

    assert response.status_code == 403, response.text
    assert db_session.query(User).filter(User.email == NEWCOMER).first() is None


def test_google_with_a_valid_code_creates_the_account_and_burns_the_code(
    client: TestClient,
    db_session: Session,
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    invite_required: None,
):
    """Chemin heureux de production : le code ouvre le compte, puis il est consommé."""
    token = _make_code(client, admin_headers)

    response = _google_signin(client, monkeypatch, NEWCOMER, token)

    assert response.status_code == 200, response.text
    created = db_session.query(User).filter(User.email == NEWCOMER).one()
    invitation = db_session.query(Invitation).filter(Invitation.token == token).one()
    assert invitation.accepted_at is not None
    assert invitation.accepted_by == created.id


def test_google_refuses_a_code_that_already_served(
    client: TestClient,
    db_session: Session,
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    invite_required: None,
):
    """« Un code = une famille » vaut aussi sur la route Google."""
    token = _make_code(client, admin_headers)
    assert _google_signin(client, monkeypatch, NEWCOMER, token).status_code == 200

    second = _google_signin(client, monkeypatch, "autre.famille@exemple.fr", token)

    assert second.status_code == 403, second.text
    assert db_session.query(User).filter(User.email == "autre.famille@exemple.fr").first() is None


def test_google_lets_an_existing_family_back_in_without_a_code(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    invite_required: None,
):
    """Régression de verrouillage : une famille déjà installée se reconnecte sans code."""
    ensure_parent(db_session, "deja.la@exemple.fr")

    again = _google_signin(client, monkeypatch, "deja.la@exemple.fr")

    assert again.status_code == 200, again.text


def test_google_tolerates_a_code_pasted_with_whitespace(
    client: TestClient,
    db_session: Session,
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    invite_required: None,
):
    """Un code collé avec un retour à la ligne reste un code valide."""
    token = _make_code(client, admin_headers)

    response = _google_signin(client, monkeypatch, NEWCOMER, f"  {token}\n")

    assert response.status_code == 200, response.text
    assert db_session.query(User).filter(User.email == NEWCOMER).first() is not None


def test_a_code_cannot_be_consumed_twice_even_by_a_concurrent_signup(db_session: Session):
    """Deux inscriptions simultanées sur le même code : une seule l'emporte.

    La lecture ``is_usable`` ne protège de rien si deux requêtes la passent
    avant que l'une écrive. La consommation est donc conditionnée en base
    (``WHERE accepted_at IS NULL``) et la perdante repart bredouille.
    """
    admin = ensure_parent(db_session, "hote.code@exemple.fr")
    invitation = create_signup_invitation(admin.id, db_session)
    first = ensure_parent(db_session, "premiere@exemple.fr")
    second = ensure_parent(db_session, "seconde@exemple.fr")

    assert consume_signup_invitation(invitation, first.id, db_session) is True
    assert consume_signup_invitation(invitation, second.id, db_session) is False

    db_session.commit()
    stored = db_session.query(Invitation).filter(Invitation.id == invitation.id).one()
    assert stored.accepted_by == first.id
