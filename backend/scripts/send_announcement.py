"""Envoie une annonce produit aux parents, depuis la ligne de commande.

Pensé pour être lancé sur la machine qui héberge l'app, sans passer par le
navigateur. L'annonce est créée en base (donc auditée et reprenable) puis
diffusée ; relancer la même commande avec ``--announcement-id`` ne réexpédie que
les destinataires non encore servis.

Usage:
    uv run python scripts/send_announcement.py --subject "..." \
        --body-file scripts/announcements/community_lessons.md [--dry-run] \
        [--limit 3] [--preview] [--announcement-id <uuid>]

Le corps peut contenir le motif ``{PUBLIC_APP_URL}``, remplacé par l'URL publique
configurée (settings.PUBLIC_APP_URL).
"""

import argparse
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import UUID

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.announcement import Announcement, AnnouncementStatus
from app.services.mail import (
    MailNotConfigured,
    build_html,
    build_text,
    recipients,
    send_announcement,
)

PLACEHOLDER = "{PUBLIC_APP_URL}"


def _load_body(path: Path) -> str:
    """Lit le corps Markdown et résout l'URL publique."""
    return path.read_text(encoding="utf-8").replace(PLACEHOLDER, settings.PUBLIC_APP_URL.rstrip("/"))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Envoie une annonce produit aux parents Explorito.")
    parser.add_argument("--subject", help="Sujet de l'email (requis sauf avec --announcement-id)")
    parser.add_argument("--body-file", help="Fichier Markdown du corps (requis sauf avec --announcement-id)")
    parser.add_argument("--announcement-id", help="Reprend une annonce existante au lieu d'en créer une")
    parser.add_argument("--dry-run", action="store_true", help="Prépare les livraisons sans envoyer d'email")
    parser.add_argument("--limit", type=int, default=None, help="Nombre maximal d'emails réellement expédiés")
    parser.add_argument("--preview", action="store_true", help="Écrit le rendu HTML dans un fichier et s'arrête")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    db = SessionLocal()
    try:
        if args.announcement_id:
            announcement = db.query(Announcement).filter(Announcement.id == UUID(args.announcement_id)).first()
            if announcement is None:
                print(f"Annonce {args.announcement_id} introuvable.")
                return 1
        else:
            if not args.subject or not args.body_file:
                print("--subject et --body-file sont requis (ou --announcement-id).")
                return 2
            body = _load_body(Path(args.body_file))
            announcement = Announcement(
                subject=args.subject,
                body_markdown=body,
                from_email=settings.MAIL_FROM,
                status=AnnouncementStatus.DRAFT.value,
            )
            db.add(announcement)
            db.commit()
            db.refresh(announcement)
            print(f"Annonce créée : {announcement.id}")

        if args.preview:
            link = f"{settings.PUBLIC_APP_URL.rstrip('/')}/desinscription?token=apercu"
            html = build_html(announcement.subject, announcement.body_markdown, link)
            out = Path(tempfile.gettempdir()) / f"annonce-{announcement.id}.html"
            out.write_text(html, encoding="utf-8")
            print(f"Aperçu HTML : {out}")
            print(f"Destinataires : {len(recipients(db))}")
            print("--- texte ---")
            print(build_text(announcement.body_markdown, link))
            return 0

        try:
            counts = send_announcement(db, announcement, dry_run=args.dry_run, limit=args.limit)
        except MailNotConfigured as exc:
            print(str(exc))
            return 3

        if not args.dry_run:
            announcement.status = AnnouncementStatus.FAILED.value if counts["failed"] else AnnouncementStatus.SENT.value
            announcement.sent_at = datetime.utcnow()
            db.commit()

        label = "Simulation terminée" if args.dry_run else "Envoi terminé"
        print(f"{label} — " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
