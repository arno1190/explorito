# Explorito — Deploy Runbook (family / small pilot)

Single small VPS, Docker Compose + Caddy (auto-HTTPS). Target: <50 invited users.

## 1. Prerequisites

- A VPS (Hetzner / Scaleway / DigitalOcean, ~€5–10/mo) with **Docker** + **Docker Compose v2**.
- A domain, e.g. `explorito.fr`, with two DNS **A records** pointing at the VPS IP:
  - `explorito.fr`         → frontend
  - `api.explorito.fr`     → backend
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
| `DOMAIN` | `explorito.fr` |
| `CORS_ORIGINS` | `https://explorito.fr` |
| `NEXT_PUBLIC_API_URL` | `https://api.explorito.fr` (baked into the frontend at build time) |

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
> Do **not** run `scripts/seed_database.py` — it predates the typed exercise contract.

## 6. Create an admin + a parent

Admin (content management):

```bash
docker compose -f docker-compose.prod.yml exec backend uv run python - <<'PY'
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, Profile, UserRole
db = SessionLocal()
u = User(email="admin@explorito.fr", password_hash=get_password_hash("CHANGE_ME"), role=UserRole.ADMIN, is_active=True)
db.add(u); db.flush()
db.add(Profile(user_id=u.id, display_name="Admin", is_child=False))
db.commit(); print("admin created:", u.email)
PY
```

Parents self-register at `https://explorito.fr/register` (role `parent`), then create their children's accounts from the dashboard. Children log in with their own credentials at `/login`.

## 7. Smoke test

```bash
curl https://api.explorito.fr/health          # -> {"status":"ok"}
```

Then in a browser:
1. Register/login as a parent → dashboard → add a child.
2. Log in as the child → `/play` → pick a subject → complete a lesson.
3. Confirm XP / streak / stars appear and the lesson shows completed.

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
