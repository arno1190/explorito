# Explorito — Deploy Runbook (family / small pilot)

Single small VPS, Docker Compose + Caddy (auto-HTTPS). Target: <50 invited users.

## 1. Prerequisites

- A VPS (Hetzner / Scaleway / DigitalOcean, ~€5–10/mo) with **Docker** + **Docker Compose v2**.
- A domain with two DNS **A records** pointing at the VPS IP. The live instance
  uses `explorito.pascalfamily.fr`; substitute your own everywhere below —
  nothing in the code hardcodes it, but `.env` must agree with DNS.
  - `explorito.pascalfamily.fr`      → frontend
  - `api.explorito.pascalfamily.fr`  → backend
- Ports **80** and **443** open.

## 2. Get the code

```bash
git clone <repo-url> /opt/explorito && cd /opt/explorito
```

## 3. Configure secrets

```bash
cp .env.production.example .env
```

Edit `.env` and set **all** of:

| Var | Value |
|-----|-------|
| `POSTGRES_PASSWORD` | a strong random password |
| `SECRET_KEY` | `openssl rand -hex 32` (the backend refuses to boot in prod with the default) |
| `DOMAIN` | `explorito.pascalfamily.fr` |
| `CORS_ORIGINS` | `https://explorito.pascalfamily.fr` |
| `NEXT_PUBLIC_API_URL` | `https://api.explorito.pascalfamily.fr` (baked into the frontend at build time) |
| `PUBLIC_APP_URL` | `https://explorito.pascalfamily.fr` — **not optional**: the backend builds pack-preview links and email unsubscribe links from it. Left unset, it falls back to `http://localhost:3005` and those URLs ship broken. |
| `MODERATION_TOKEN` | `openssl rand -hex 32`, or empty to disable the token door (an admin session still reaches `/moderation/*`) |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | your mail relay, or empty — announcement sending then fails cleanly with a 503 instead of silently |

## 4. Build & start

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

- The backend container runs **`alembic upgrade head`** automatically before starting, so the schema is created/migrated on every deploy.
- Caddy provisions HTTPS certificates automatically for both hosts on first request.

Watch it come up:

```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

## 5. Seed content (one-time)

Loads the 238 CP/CE1 exercises (8 subjects × CP/CE1 × 3 levels):

```bash
docker compose -f docker-compose.prod.yml exec backend uv run python scripts/seed_cp_content.py
```

> Idempotent guard: it refuses to run if content already exists. Use `--reset` only to wipe & reseed (destructive — also removes progress).

## 6. Create an admin + a parent

There is **no password login**: `api/auth.py` exposes `/google`, `/dev-login`
(DEBUG only), `/pin`, `/verify-pin` and `/refresh`. Admin rights are granted by
email allowlist, not by a row you insert — set `ADMIN_EMAILS` in `.env` to the
Google addresses that should be admins, comma-separated, and the role is applied
on their next login.

```bash
# .env
ADMIN_EMAILS=arnaud@pascalfamily.fr
```

Parents sign in with Google at `https://explorito.pascalfamily.fr/login`, then
create their children from the dashboard. **Children have no login of their
own**: a parent enters child mode from the dashboard, protected by a 4-digit
PIN.

## 7. Smoke test

```bash
curl https://api.explorito.pascalfamily.fr/health          # -> {"status":"ok"}
```

Then in a browser:
1. Sign in with Google as a parent → dashboard → add a child.
2. Enter child mode ("Jouer comme …", PIN-protected) → `/play` → pick a theme → complete a lesson.
3. Confirm XP / streak / stars appear and the lesson shows completed.
4. Check the contribution surface: `/contributions` must show the terms modal on
   first visit, and a pack upload must return a `preview_url` on your real
   domain — a `localhost` URL there means `PUBLIC_APP_URL` is missing.

## 8. Backups (recommended)

A backup script is provided (`scripts/backup.sh`, gzip + 7-day retention). Add a daily cron on the host:

```bash
# crontab -e
0 3 * * * cd /opt/explorito && POSTGRES_USER=explorito POSTGRES_DB=explorito \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U explorito explorito | gzip > /opt/explorito/backups/explorito_$(date +\%Y\%m\%d).sql.gz
```

## 9. Updating the pilot

```bash
cd /opt/explorito && git pull
docker compose -f docker-compose.prod.yml up -d --build   # migrations run automatically
```

## Notes / known limits (pilot scope)

- **mypy** is non-blocking in CI (models use classic `Column()`; a `Mapped[]` migration would let it become blocking).
- **Parent "impersonate child"** exists in the UI, but exercise submissions attribute progress to the *authenticated* user — so children should log in as themselves for their progress to be recorded. (A parent playing "as" a child would log progress under the parent.)
- **Per-child content restriction** is intentionally deferred; progression already gates content via star-unlocks.
