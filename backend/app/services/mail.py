"""Envoi d'emails d'annonce, sur la bibliothèque standard uniquement.

Le besoin est minuscule (quelques dizaines de parents, deux ou trois envois par
an) : ajouter une dépendance d'emailing coûterait plus cher que les ~200 lignes
ci-dessous. Deux invariants guident le module :

- **Rendu sûr** : le corps est écrit en Markdown restreint par l'admin, mais il
  est échappé *avant* toute conversion, pour qu'aucun fragment de HTML saisi
  (volontairement ou par copier-coller) ne se retrouve dans l'email.
- **Envoi reprenable** : chaque destinataire a sa ligne ``AnnouncementDelivery``
  commitée immédiatement après sa tentative. Un plantage au 12e email ne
  réexpédie pas les 11 premiers.
"""

import html as html_escaper
import re
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import formataddr
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.announcement import Announcement, AnnouncementDelivery, DeliveryStatus
from app.models.user import User, UserRole

# Durée de vie d'un lien de désinscription : volontairement très longue, un
# parent peut se désinscrire depuis un email vieux d'un an.
UNSUBSCRIBE_TOKEN_DAYS = 400
UNSUBSCRIBE_TOKEN_TYPE = "unsubscribe"

# Schémas autorisés dans les liens : interdit `javascript:` et consorts même si
# le corps est rédigé par un admin (un copier-coller reste un copier-coller).
_SAFE_LINK_SCHEMES = ("http://", "https://", "mailto:", "/")

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_STAR_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_ITALIC_UNDERSCORE_RE = re.compile(r"(?<!\w)_([^_\n]+)_(?!\w)")


class MailNotConfigured(RuntimeError):
    """Aucun serveur SMTP configuré : l'envoi est refusé, jamais ignoré."""


# --------------------------------------------------------------------- #
# Rendu Markdown restreint
# --------------------------------------------------------------------- #


def _render_link(match: re.Match[str]) -> str:
    """Rend un lien Markdown, ou son texte brut si l'URL n'est pas sûre."""
    label, url = match.group(1), match.group(2)
    if not url.startswith(_SAFE_LINK_SCHEMES):
        return label
    return f'<a href="{url}">{label}</a>'


def _render_inline(text: str) -> str:
    """Applique les marques en ligne (lien, gras, italique) à un texte déjà échappé."""
    rendered = _LINK_RE.sub(_render_link, text)
    rendered = _BOLD_RE.sub(r"<strong>\1</strong>", rendered)
    rendered = _ITALIC_STAR_RE.sub(r"<em>\1</em>", rendered)
    return _ITALIC_UNDERSCORE_RE.sub(r"<em>\1</em>", rendered)


def render_markdown(body: str) -> str:
    """Convertit un Markdown restreint en HTML d'email.

    Sous-ensemble volontairement pauvre : titres ``#``/``##``, gras, italique,
    listes à puces, liens et paragraphes. Tout le reste est du texte.

    Args:
        body: Corps rédigé par l'admin.

    Returns:
        Fragment HTML (sans ``<html>``), sûr à insérer dans le gabarit.
    """
    lines = html_escaper.escape(body).splitlines()
    blocks: list[str] = []
    paragraph: list[str] = []
    items: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            # Retour à la ligne simple = coupure de confort dans la source, pas
            # dans l'email : on rejoint, pour que le texte reflue sur mobile.
            blocks.append("<p>" + _render_inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def flush_list() -> None:
        if items:
            rendered = "".join(f"<li>{_render_inline(item)}</li>" for item in items)
            blocks.append(f"<ul>{rendered}</ul>")
            items.clear()

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_list()
        elif line.startswith("## "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h2>{_render_inline(line[3:].strip())}</h2>")
        elif line.startswith("# "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h1>{_render_inline(line[2:].strip())}</h1>")
        elif line.startswith(("- ", "* ")):
            flush_paragraph()
            items.append(line[2:].strip())
        elif items:
            # Continuation « paresseuse » : une puce coupée sur plusieurs lignes
            # reste une seule puce (les corps sont écrits en dur à ~80 colonnes).
            items[-1] = f"{items[-1]} {line}"
        else:
            paragraph.append(line)

    flush_paragraph()
    flush_list()
    return "\n".join(blocks)


# --------------------------------------------------------------------- #
# Désinscription
# --------------------------------------------------------------------- #


def unsubscribe_token(user_id: UUID) -> str:
    """Jeton signé autorisant la désinscription d'un compte, sans connexion."""
    payload = {
        "sub": str(user_id),
        "typ": UNSUBSCRIBE_TOKEN_TYPE,
        "exp": datetime.utcnow() + timedelta(days=UNSUBSCRIBE_TOKEN_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def read_unsubscribe_token(token: str) -> UUID | None:
    """Vérifie un jeton de désinscription et renvoie l'utilisateur visé.

    Le claim ``typ`` empêche qu'un jeton d'accès (qui porte aussi ``sub``) soit
    rejoué ici, et inversement.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("typ") != UNSUBSCRIBE_TOKEN_TYPE:
        return None
    try:
        return UUID(str(payload.get("sub")))
    except ValueError:
        return None


def unsubscribe_url(user_id: UUID) -> str:
    """Lien public de désinscription, propre à un destinataire."""
    return f"{settings.PUBLIC_APP_URL.rstrip('/')}/desinscription?token={unsubscribe_token(user_id)}"


# --------------------------------------------------------------------- #
# Gabarit
# --------------------------------------------------------------------- #


def build_html(subject: str, body_markdown: str, unsubscribe_link: str) -> str:
    """Assemble l'email HTML complet (gabarit + corps rendu + pied de page)."""
    return (
        "<!DOCTYPE html>"
        '<html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html_escaper.escape(subject)}</title></head>"
        '<body style="margin:0;padding:24px;background:#f8fafc;'
        "font-family:'Nunito',system-ui,sans-serif;color:#042C60;\">"
        '<div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:16px;padding:28px;">'
        f"{render_markdown(body_markdown)}"
        '<hr style="border:none;border-top:1px solid #E2E8F0;margin:28px 0 12px;">'
        '<p style="font-size:12px;color:#64748B;">'
        "Vous recevez ce message parce que vous avez un compte Explorito.<br>"
        f'<a href="{unsubscribe_link}" style="color:#64748B;">Ne plus recevoir ces annonces</a>.'
        "</p></div></body></html>"
    )


def build_text(body_markdown: str, unsubscribe_link: str) -> str:
    """Repli texte : le Markdown source, qui se lit très bien tel quel."""
    return (
        f"{body_markdown.strip()}\n\n"
        "--\n"
        "Vous recevez ce message parce que vous avez un compte Explorito.\n"
        f"Ne plus recevoir ces annonces : {unsubscribe_link}\n"
    )


# --------------------------------------------------------------------- #
# Transport SMTP
# --------------------------------------------------------------------- #


def _transport_send(message: EmailMessage) -> None:
    """Ouvre une connexion SMTP et remet un message.

    Une connexion par message : au volume visé, la simplicité (et la résistance
    à une coupure au milieu du lot) vaut mieux que la réutilisation de session.
    """
    if settings.SMTP_SSL:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        return
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
        if settings.SMTP_STARTTLS:
            smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def send_email(*, to: str, subject: str, html: str, text: str) -> None:
    """Envoie un email multipart (texte + HTML).

    Args:
        to: Adresse du destinataire.
        subject: Sujet.
        html: Corps HTML complet.
        text: Corps texte de repli.

    Raises:
        MailNotConfigured: Si aucun serveur SMTP n'est configuré.
    """
    if not settings.mail_configured:
        raise MailNotConfigured(
            "Envoi impossible : SMTP_HOST et MAIL_FROM doivent être configurés (voir backend/.env)."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.MAIL_FROM_NAME, settings.MAIL_FROM))
    message["To"] = to
    if settings.MAIL_REPLY_TO:
        message["Reply-To"] = settings.MAIL_REPLY_TO
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    _transport_send(message)


# --------------------------------------------------------------------- #
# Destinataires et diffusion
# --------------------------------------------------------------------- #


def recipients(db: Session) -> list[tuple[UUID, str]]:
    """Comptes adultes joignables par une annonce produit.

    Parents et admins actifs, avec un email, non désinscrits. Dédoublonné sur
    l'email en minuscules : deux comptes ne doivent jamais valoir deux copies.

    Returns:
        Couples ``(user_id, email normalisé)``, dans l'ordre de création.
    """
    users = (
        db.query(User)
        .filter(
            User.email.isnot(None),
            User.is_active.is_(True),
            User.email_opt_out.is_(False),
            User.role.in_([UserRole.PARENT, UserRole.ADMIN]),
        )
        .order_by(User.created_at)
        .all()
    )
    seen: set[str] = set()
    targets: list[tuple[UUID, str]] = []
    for user in users:
        email = (user.email or "").strip().lower()
        if not email or email in seen:
            continue
        seen.add(email)
        targets.append((user.id, email))
    return targets


def _sync_deliveries(db: Session, announcement: Announcement, targets: list[tuple[UUID, str]]) -> None:
    """Aligne les lignes de livraison sur la liste courante des destinataires.

    Les lignes déjà ``sent`` ou ``failed`` ne sont jamais recréées ni écrasées :
    elles sont la mémoire de l'envoi précédent.
    """
    rows = {row.email: row for row in db.query(AnnouncementDelivery).filter_by(announcement_id=announcement.id)}
    wanted: dict[str, UUID] = {email: user_id for user_id, email in targets}

    for email, user_id in wanted.items():
        row = rows.get(email)
        if row is None:
            db.add(
                AnnouncementDelivery(
                    announcement_id=announcement.id,
                    user_id=user_id,
                    email=email,
                    status=DeliveryStatus.PENDING.value,
                    attempts=0,
                )
            )
        elif row.status == DeliveryStatus.SKIPPED.value:
            # Le parent s'était désinscrit puis est revenu : on le réarme.
            row.status = DeliveryStatus.PENDING.value

    # Désinscription (ou désactivation) survenue depuis la rédaction : la ligne
    # reste, pour l'audit, mais ne partira pas.
    for email, row in rows.items():
        if email not in wanted and row.status == DeliveryStatus.PENDING.value:
            row.status = DeliveryStatus.SKIPPED.value

    db.commit()


def send_announcement(
    db: Session,
    announcement: Announcement,
    *,
    dry_run: bool = False,
    limit: int | None = None,
) -> dict[str, int]:
    """Diffuse une annonce à tous les destinataires, de façon reprenable.

    Args:
        db: Session de base de données.
        announcement: Annonce à diffuser.
        dry_run: Prépare et compte les livraisons sans rien envoyer.
        limit: Nombre maximal d'emails réellement expédiés (essai grandeur nature).

    Returns:
        Compteurs ``recipients``/``sent``/``failed``/``skipped``/``already_sent``/``pending``.

    Raises:
        MailNotConfigured: Si l'envoi est demandé sans configuration SMTP.
    """
    if not dry_run and not settings.mail_configured:
        raise MailNotConfigured(
            "Envoi impossible : SMTP_HOST et MAIL_FROM doivent être configurés (voir backend/.env)."
        )

    targets = recipients(db)
    _sync_deliveries(db, announcement, targets)

    rows = (
        db.query(AnnouncementDelivery)
        .filter(AnnouncementDelivery.announcement_id == announcement.id)
        .order_by(AnnouncementDelivery.email)
        .all()
    )
    counts = {
        "recipients": len(targets),
        "sent": 0,
        "failed": 0,
        "skipped": 0,
        "already_sent": 0,
        "pending": 0,
    }

    for row in rows:
        if row.status == DeliveryStatus.SENT.value:
            counts["already_sent"] += 1
        elif row.status == DeliveryStatus.SKIPPED.value:
            counts["skipped"] += 1

    if dry_run:
        counts["pending"] = sum(1 for row in rows if row.status == DeliveryStatus.PENDING.value)
        return counts

    subject = announcement.subject
    body = announcement.body_markdown
    for row in rows:
        if row.status in (DeliveryStatus.SENT.value, DeliveryStatus.SKIPPED.value):
            continue
        if limit is not None and counts["sent"] + counts["failed"] >= limit:
            counts["pending"] += 1
            continue

        link = unsubscribe_url(row.user_id) if row.user_id else f"{settings.PUBLIC_APP_URL.rstrip('/')}/desinscription"
        row.attempts = (row.attempts or 0) + 1
        try:
            send_email(
                to=row.email,
                subject=subject,
                html=build_html(subject, body, link),
                text=build_text(body, link),
            )
        except Exception as exc:  # noqa: BLE001 — un destinataire fautif ne doit pas arrêter le lot
            row.status = DeliveryStatus.FAILED.value
            row.error = f"{type(exc).__name__}: {exc}"[:1000]
            counts["failed"] += 1
        else:
            row.status = DeliveryStatus.SENT.value
            row.error = None
            row.sent_at = datetime.utcnow()
            counts["sent"] += 1
        # Commit par ligne : c'est ce qui rend l'envoi reprenable après un crash.
        db.commit()

    return counts
