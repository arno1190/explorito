# Explorito 🦉

A playful, Duolingo-style learning web app for primary-school children (French
curriculum, **PS → CM2**). Kids progress through bite-sized lessons, earn points,
keep streaks, and spend their points to unlock collectibles. Parents run
everything from a dashboard and can reward offline effort and good behaviour.

Monorepo: **FastAPI** backend + **Next.js** frontend, fully typed end-to-end via
an OpenAPI-generated client.

---

## Features

### Learning
- **Subjects → learning paths (by grade) → lessons → exercises.** Content is
  filtered to each child's grade level.
- **Typed exercises**: `multiple_choice`, `fill_blanks`, `reveal`,
  `math_problem`, `reading`, `soroban` (Japanese abacus), and `pythagore`
  (multiplication-table fill-in mini-game). Answer grading is server-side.
- **Tier-based unlocking** as the single source of truth: a lesson unlocks only
  when the previous tier is complete (enforced on the API, not just the UI).
- **Per-exercise difficulty (1–5)** that drives the XP reward, so harder
  exercises are worth more. Difficulty is stored per exercise; XP is configurable
  (`XP_BY_LEVEL`).
- **Curriculum is generated or hand-authored**: maths are produced
  programmatically (correct by construction); knowledge/reading lessons are
  hand-written from public-domain facts and light Jules-Verne–themed texts.

### Gamification & economy
- **Two spendable wallets**, both usable to buy collectibles (the child picks
  which at checkout):
  - **⭐ Points** — earned from exercises/Pythagore **plus** parent-awarded
    "hardskill" points (e.g. an offline dictée). Additive only.
  - **💚 Comportement** — parent-awarded behaviour points (can be + or −).
- **Parent-awarded points** for offline activities, from the dashboard, with
  quick presets or a custom amount + reason. A celebratory toast greets the child;
  parents see the full award history.
- **Collections**: multi-catalogue reward shop (Pokémon, dinosaurs, solar
  system) with a per-catalogue completion bar. Prices scale along an eased curve.
- **Streaks, daily goals, achievements/badges, XP-based levels.**
- **Progress analytics** for parents: 14-day activity, accuracy per subject,
  lesson timeline, and an error journal.

### Accounts & safety
- **Google Sign-In only** for parents (open signup). Admins are designated by an
  email allowlist (`ADMIN_EMAILS`).
- **Children have no login**: they're login-less profiles a parent "launches"
  into ("play as child") via a client-side impersonation header.
- **Parent PIN** (4-digit, bcrypt-hashed): returning from child mode to the
  parent view is gated by the PIN. Forgotten PIN → sign out and back in with
  Google.

---

## Tech stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, [uv](https://docs.astral.sh/uv/) |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, TanStack Query |
| API client | [Orval](https://orval.dev/) generates a typed React-Query + axios client from the backend's OpenAPI schema |
| DB | PostgreSQL |
| Auth | Google Identity Services (ID-token flow) → app-issued JWT |
| Tooling | ruff (lint + format), mypy, pytest; pnpm; Docker Compose |

---

## Repository layout

```
explorito/
├── backend/
│   ├── app/
│   │   ├── api/        # Route handlers (auth, subjects, lessons, exercises,
│   │   │               #   children, collection, gamification, progress, pythagore)
│   │   ├── models/     # SQLAlchemy models
│   │   ├── schemas/    # Pydantic schemas
│   │   ├── services/   # Business logic (gamification, collection, progression…)
│   │   ├── core/       # Config, DB, security (JWT, Google verify, hashing)
│   │   └── data/       # Collectible catalogues (JSON) + difficulty assessment
│   ├── alembic/        # Migrations
│   └── scripts/        # Curriculum seeders (generated maths, hand-authored content)
├── frontend/
│   └── src/
│       ├── app/        # App Router pages (play, subjects, lessons, exercises,
│       │               #   collection, dashboard, progress, auth)
│       ├── components/ # UI + feature components
│       └── lib/        # auth context, generated API client, navigation
└── docker-compose.yml  # Local dev stack
```

---

## Getting started (local)

Prerequisites: Docker + Docker Compose (or local Postgres + [uv] + [pnpm]).

```bash
# 1. Backend + frontend env
cp backend/.env.example backend/.env         # set DATABASE_URL, SECRET_KEY, CORS_ORIGINS
cp frontend/.env.local.example frontend/.env.local 2>/dev/null || true

# 2. Start the stack
docker compose up -d

# 3. Apply migrations (runs automatically on backend start; or manually):
docker compose exec backend uv run alembic upgrade head

# 4. Seed a curriculum (generated maths + hand-authored content)
docker compose exec backend uv run python scripts/seed_curriculum.py
docker compose exec backend uv run python scripts/seed_ce1_maths.py
docker compose exec backend uv run python scripts/generate_catalogs.py   # collectibles
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3005 |
| API + docs | http://localhost:8005 · http://localhost:8005/docs |

### Google Sign-In setup

Auth is Google-only. Create an **OAuth 2.0 Client ID** (Web application) in the
Google Cloud Console with your app origins as **Authorized JavaScript origins**
(e.g. `http://localhost:3005`), no redirect URIs (the app uses the ID-token
flow), and an External+Published consent screen with scopes `openid email
profile`. Then set:

```
# backend/.env
GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
ADMIN_EMAILS=you@example.com          # comma-separated admins

# frontend/.env.local
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<same client id>
```

In development (`DEBUG=true`) a `/auth/dev-login` endpoint lets you sign in by
email without Google (used by the test suite); it is never mounted in production.

---

## Development

```bash
# Backend
cd backend
uv run pytest                 # tests
uv run ruff check . && uv run ruff format .
uv run mypy -p app

# Frontend
cd frontend
pnpm install
pnpm dev                      # http://localhost:3005
pnpm exec tsc --noEmit
pnpm build

# Regenerate the API client after backend API changes
pnpm generate:api             # reads http://localhost:8005/openapi.json
```

Migrations: `uv run alembic revision -m "..."` then `uv run alembic upgrade head`.

---

## Contributing

Issues and PRs welcome. Please keep the typed contracts intact (Pydantic
schemas + regenerated Orval client), add tests for backend behaviour, and run
ruff/mypy/tsc before opening a PR.

## License

MIT — see [LICENSE](LICENSE).

> Note: collectible imagery is fetched at build time from public sources
> (e.g. Wikipedia, PokéAPI); respect their terms. No third-party copyrighted
> curriculum content is included in this repository.
