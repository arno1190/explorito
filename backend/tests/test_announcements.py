"""Tests des annonces produit : rendu, destinataires, envoi reprenable, API.

Aucun test n'ouvre de socket : ``smtplib.SMTP`` est remplacé dans l'espace de
noms du service par un faux transport qui enregistre les messages.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.announcement import Announcement, AnnouncementDelivery, AnnouncementStatus, DeliveryStatus
from app.models.user import Profile, User, UserRole
from app.services import mail
from tests.helpers import dev_login


class FakeSMTP:
    """Faux serveur SMTP : enregistre les messages, n'ouvre jamais de connexion."""

    sent: list[tuple[str, str]] = []
    fail_for: set[str] = set()
    logins: list[str] = []
    starttls_calls = 0

    def __init__(self, host: str, port: int, timeout: int | None = None) -> None:
        self.host = host
        self.port = port

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def starttls(self) -> None:
        type(self).starttls_calls += 1

    def login(self, user: str, password: str) -> None:
        type(self).logins.append(user)

    def send_message(self, message: object) -> None:
        to = message["To"]  # type: ignore[index]
        if to in type(self).fail_for:
            raise OSError(f"boîte pleine pour {to}")
        type(self).sent.append((to, message["Subject"]))  # type: ignore[index]


@pytest.fixture
def smtp(monkeypatch: pytest.MonkeyPatch) -> type[FakeSMTP]:
    """SMTP configuré + transport moqué."""
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_USER", "arnaud")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(settings, "SMTP_SSL", False)
    monkeypatch.setattr(settings, "SMTP_STARTTLS", True)
    monkeypatch.setattr(mail.smtplib, "SMTP", FakeSMTP)
    FakeSMTP.sent = []
    FakeSMTP.fail_for = set()
    FakeSMTP.logins = []
    FakeSMTP.starttls_calls = 0
    return FakeSMTP


def _parent(db: Session, email: str, *, opt_out: bool = False, active: bool = True) -> User:
    user = User(email=email, role=UserRole.PARENT, is_active=active, email_opt_out=opt_out)
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, display_name=email.split("@")[0], is_child=False))
    db.commit()
    db.refresh(user)
    return user


def _announcement(db: Session, subject: str = "Nouveauté") -> Announcement:
    announcement = Announcement(
        subject=subject,
        body_markdown="# Bonjour\n\nUn **mot** rapide.",
        from_email=settings.MAIL_FROM,
        status=AnnouncementStatus.DRAFT.value,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


def _admin_headers(client: TestClient, monkeypatch: pytest.MonkeyPatch, email: str = "boss@qa.fr") -> dict[str, str]:
    monkeypatch.setattr(settings, "ADMIN_EMAILS", email)
    return dev_login(client, email)


# --------------------------------------------------------------------- #
# Rendu Markdown
# --------------------------------------------------------------------- #


def test_render_markdown_escapes_source_html():
    html = mail.render_markdown("Coucou <script>alert(1)</script> & compagnie")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html and "&amp;" in html


def test_render_markdown_titles_lists_links_and_marks():
    html = mail.render_markdown(
        "# Titre\n## Sous-titre\n\nUn **gras** et un *italique*.\n\n- premier\n- [tuto](https://exemple.fr/t)\n"
    )
    assert "<h1>Titre</h1>" in html
    assert "<h2>Sous-titre</h2>" in html
    assert "<strong>gras</strong>" in html and "<em>italique</em>" in html
    assert '<ul><li>premier</li><li><a href="https://exemple.fr/t">tuto</a></li></ul>' in html


def test_render_markdown_reflows_hard_wrapped_source():
    """Un corps coupé à 80 colonnes ne doit pas garder ses coupures dans l'email."""
    html = mail.render_markdown("Une phrase\ncoupée en deux.\n\n- une puce\n  coupée aussi\n")
    assert "<p>Une phrase coupée en deux.</p>" in html
    assert "<ul><li>une puce coupée aussi</li></ul>" in html


def test_render_markdown_refuses_unsafe_link_scheme():
    html = mail.render_markdown("[clique](javascript:alert(1))")
    assert "javascript:" not in html
    assert "clique" in html


# --------------------------------------------------------------------- #
# Destinataires
# --------------------------------------------------------------------- #


def test_recipients_excludes_opted_out_inactive_and_emailless(db_session: Session):
    kept = _parent(db_session, "ok@qa.fr")
    _parent(db_session, "stop@qa.fr", opt_out=True)
    _parent(db_session, "off@qa.fr", active=False)
    child = User(email=None, role=UserRole.CHILD, is_active=True)
    db_session.add(child)
    db_session.commit()

    assert mail.recipients(db_session) == [(kept.id, "ok@qa.fr")]


# --------------------------------------------------------------------- #
# Envoi
# --------------------------------------------------------------------- #


def test_send_marks_deliveries_and_is_idempotent(db_session: Session, smtp: type[FakeSMTP]):
    _parent(db_session, "a@qa.fr")
    _parent(db_session, "b@qa.fr")
    announcement = _announcement(db_session)

    counts = mail.send_announcement(db_session, announcement)
    assert counts["sent"] == 2 and counts["failed"] == 0
    assert sorted(to for to, _ in smtp.sent) == ["a@qa.fr", "b@qa.fr"]
    assert smtp.starttls_calls == 2 and smtp.logins == ["arnaud", "arnaud"]

    rows = db_session.query(AnnouncementDelivery).all()
    assert {row.status for row in rows} == {DeliveryStatus.SENT.value}
    assert all(row.sent_at is not None and row.attempts == 1 for row in rows)

    # Relance : rien ne repart.
    smtp.sent = []
    again = mail.send_announcement(db_session, announcement)
    assert smtp.sent == []
    assert again["sent"] == 0 and again["already_sent"] == 2


def test_failing_recipient_is_recorded_without_blocking_the_others(db_session: Session, smtp: type[FakeSMTP]):
    _parent(db_session, "good@qa.fr")
    _parent(db_session, "bad@qa.fr")
    smtp.fail_for = {"bad@qa.fr"}
    announcement = _announcement(db_session)

    counts = mail.send_announcement(db_session, announcement)
    assert counts == {
        "recipients": 2,
        "sent": 1,
        "failed": 1,
        "skipped": 0,
        "already_sent": 0,
        "pending": 0,
    }
    failed = db_session.query(AnnouncementDelivery).filter_by(email="bad@qa.fr").one()
    assert failed.status == DeliveryStatus.FAILED.value
    assert "boîte pleine" in failed.error
    assert db_session.query(AnnouncementDelivery).filter_by(email="good@qa.fr").one().status == "sent"

    # Une relance ne rejoue que l'échec.
    smtp.fail_for = set()
    smtp.sent = []
    retry = mail.send_announcement(db_session, announcement)
    assert [to for to, _ in smtp.sent] == ["bad@qa.fr"]
    assert retry["sent"] == 1 and retry["already_sent"] == 1
    assert db_session.query(AnnouncementDelivery).filter_by(email="bad@qa.fr").one().attempts == 2


def test_dry_run_prepares_rows_without_sending(db_session: Session, smtp: type[FakeSMTP]):
    _parent(db_session, "a@qa.fr")
    announcement = _announcement(db_session)

    counts = mail.send_announcement(db_session, announcement, dry_run=True)
    assert smtp.sent == []
    assert counts["pending"] == 1 and counts["sent"] == 0
    assert db_session.query(AnnouncementDelivery).one().status == DeliveryStatus.PENDING.value


def test_send_without_smtp_configuration_raises(db_session: Session, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    _parent(db_session, "a@qa.fr")
    announcement = _announcement(db_session)

    with pytest.raises(mail.MailNotConfigured):
        mail.send_announcement(db_session, announcement)
    with pytest.raises(mail.MailNotConfigured):
        mail.send_email(to="a@qa.fr", subject="x", html="<p>x</p>", text="x")


def test_sent_email_carries_a_per_recipient_unsubscribe_link(db_session: Session, smtp: type[FakeSMTP]):
    user = _parent(db_session, "a@qa.fr")
    link = mail.unsubscribe_url(user.id)
    assert mail.read_unsubscribe_token(link.split("token=")[1]) == user.id
    assert link in mail.build_html("Sujet", "Corps", link)
    assert link in mail.build_text("Corps", link)


# --------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------- #


def test_unsubscribe_flips_opt_out_and_rejects_forged_token(
    client: TestClient, db_session: Session, smtp: type[FakeSMTP]
):
    user = _parent(db_session, "a@qa.fr")
    token = mail.unsubscribe_token(user.id)

    assert client.post("/api/v1/announcements/unsubscribe", json={"token": "bidon"}).status_code == 400

    r = client.post("/api/v1/announcements/unsubscribe", json={"token": token})
    assert r.status_code == 200, r.text
    assert r.json() == {"unsubscribed": True, "email": "a@qa.fr"}
    db_session.refresh(user)
    assert user.email_opt_out is True
    assert mail.recipients(db_session) == []


def test_admin_flow_create_preview_send_and_delete(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch, smtp: type[FakeSMTP]
):
    headers = _admin_headers(client, monkeypatch)
    _parent(db_session, "famille@qa.fr")

    created = client.post(
        "/api/v1/announcements",
        json={"subject": "Leçons communautaires", "body_markdown": "# Salut\n\n- [tuto](https://x.fr)"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    announcement_id = created.json()["id"]
    assert created.json()["from_email"] == settings.MAIL_FROM

    preview = client.get(f"/api/v1/announcements/{announcement_id}/preview", headers=headers).json()
    assert "<h1>Salut</h1>" in preview["html"]
    # L'admin connecté est parent lui aussi : il compte parmi les destinataires.
    assert preview["recipient_count"] == 2

    dry = client.post(f"/api/v1/announcements/{announcement_id}/send?dry_run=true", headers=headers).json()
    assert dry["dry_run"] is True and dry["counts"]["pending"] == 2 and smtp.sent == []

    sent = client.post(f"/api/v1/announcements/{announcement_id}/send", headers=headers).json()
    assert sent["status"] == AnnouncementStatus.SENT.value and sent["counts"]["sent"] == 2
    assert len(smtp.sent) == 2

    detail = client.get(f"/api/v1/announcements/{announcement_id}", headers=headers).json()
    assert detail["delivery_counts"]["sent"] == 2
    assert {d["email"] for d in detail["deliveries"]} == {"famille@qa.fr", "boss@qa.fr"}
    assert [a["id"] for a in client.get("/api/v1/announcements", headers=headers).json()] == [announcement_id]

    # Une annonce envoyée est une trace : suppression refusée.
    assert client.delete(f"/api/v1/announcements/{announcement_id}", headers=headers).status_code == 409


def test_draft_can_be_deleted(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    headers = _admin_headers(client, monkeypatch)
    announcement_id = client.post(
        "/api/v1/announcements",
        json={"subject": "Brouillon", "body_markdown": "texte"},
        headers=headers,
    ).json()["id"]

    assert client.delete(f"/api/v1/announcements/{announcement_id}", headers=headers).status_code == 204
    assert client.get(f"/api/v1/announcements/{announcement_id}", headers=headers).status_code == 404


def test_send_without_smtp_returns_503(client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    headers = _admin_headers(client, monkeypatch)
    announcement_id = client.post(
        "/api/v1/announcements",
        json={"subject": "Sans SMTP", "body_markdown": "texte"},
        headers=headers,
    ).json()["id"]

    r = client.post(f"/api/v1/announcements/{announcement_id}/send", headers=headers)
    assert r.status_code == 503
    detail = client.get(f"/api/v1/announcements/{announcement_id}", headers=headers).json()
    assert detail["status"] == AnnouncementStatus.DRAFT.value


def test_admin_routes_are_forbidden_to_parents(client: TestClient, db_session: Session):
    headers = dev_login(client, "simple@qa.fr")
    announcement = _announcement(db_session)
    aid = str(announcement.id)

    assert client.get("/api/v1/announcements", headers=headers).status_code == 403
    assert (
        client.post("/api/v1/announcements", json={"subject": "x", "body_markdown": "y"}, headers=headers).status_code
        == 403
    )
    assert client.get(f"/api/v1/announcements/{aid}", headers=headers).status_code == 403
    assert client.get(f"/api/v1/announcements/{aid}/preview", headers=headers).status_code == 403
    assert client.post(f"/api/v1/announcements/{aid}/send", headers=headers).status_code == 403
    assert client.delete(f"/api/v1/announcements/{aid}", headers=headers).status_code == 403
