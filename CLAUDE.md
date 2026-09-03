# Explorito - Project Instructions

## Overview
Educational Duolingo-like app for children (CP level). Monorepo with FastAPI backend and Next.js frontend.

## Architecture

```
explorito/
├── backend/          # FastAPI + SQLAlchemy + uv
│   ├── app/
│   │   ├── api/      # Route handlers
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── core/     # Config, DB, security
│   ├── pyproject.toml # Dependencies (uv)
│   └── scripts/      # Seed, extraction scripts
├── frontend/         # Next.js 16 + React 19 + Orval
│   └── src/
│       ├── app/      # App router pages
│       ├── components/
│       ├── lib/
│       │   ├── api/  # Generated API client (Orval)
│       │   └── auth.tsx
│       └── types/    # TypeScript types
└── scripts/          # Validation scripts
```

## Critical Rules

### 1. Package Management
**Backend: Always use `uv` (never pip)**
```bash
# Add dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Sync dependencies
uv sync

# Run commands
uv run pytest
uv run ruff check app/
```

**Frontend: Always use `pnpm`**
```bash
pnpm add package-name
pnpm add -D package-name
pnpm install
```

### 2. API Type Generation with Orval
**ALWAYS regenerate types after backend API changes:**
```bash
# Generate TypeScript types and API client from OpenAPI
cd frontend && pnpm generate:api

# Watch mode during development
cd frontend && pnpm generate:api:watch
```

Generated files location:
- Types: `frontend/src/lib/api/model/`
- API hooks: `frontend/src/lib/api/generated/`

**Workflow after backend changes:**
1. Make changes to backend schemas/endpoints
2. Restart backend: `docker compose restart backend`
3. Regenerate frontend API: `pnpm generate:api`
4. Update components to use new types/hooks

### 3. Frontend-Backend Contract
With Orval, types are auto-generated from `openapi.json`. Manual types in `frontend/src/types/` can be gradually deprecated.

| Source | Location |
|--------|----------|
| OpenAPI spec | `http://localhost:8005/openapi.json` |
| Generated types | `frontend/src/lib/api/model/` |
| Generated hooks | `frontend/src/lib/api/generated/` |
| Legacy manual types | `frontend/src/types/index.ts` (deprecated) |

### 4. API Endpoint Verification
```bash
# Check endpoint exists (note port 8005)
curl http://localhost:8005/openapi.json | jq '.paths | keys' | grep "endpoint"

# Test with auth — there is NO password login. `api/auth.py` exposes only
# /google (id_token), /dev-login (DEBUG builds only), /pin, /verify-pin, /refresh.
# In dev, /dev-login takes an email and returns a parent token; the account is
# created on the fly and promoted to admin if the email is in ADMIN_EMAILS.
TOKEN=$(curl -s -X POST http://localhost:8005/api/v1/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@explorito.fr"}' | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" http://localhost:8005/api/v1/your-endpoint

# Moderation surface: scoped token instead of an admin session. Grants
# /api/v1/moderation/* ONLY (never user deletion or impersonation), and is
# disabled entirely when MODERATION_TOKEN is empty.
curl -H "X-Moderation-Token: $MODERATION_TOKEN" \
  "http://localhost:8005/api/v1/moderation/queue?status=pending"
```

### 5. Code Quality
**Backend (automatic checks):**
```bash
uv run ruff check --fix app/
uv run ruff format app/
uv run mypy app/ --no-error-summary
```

**Frontend (automatic checks):**
```bash
pnpm exec prettier --write src/
pnpm exec tsc --noEmit
```

## Ports Configuration

| Service  | Port |
|----------|------|
| Postgres | 5435 |
| Backend  | 8005 |
| Frontend | 3005 |

Access frontend at: http://localhost:3005
API documentation at: http://localhost:8005/docs

## Commands

### Development
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart after code changes
docker compose restart backend
docker compose restart frontend

# Rebuild after dependency changes (uses uv)
docker compose build backend --no-cache
docker compose build frontend --no-cache
```

### Backend Development
```bash
# Run linter and formatter
docker compose exec backend uv run ruff check --fix app/
docker compose exec backend uv run ruff format app/

# Run tests
docker compose exec backend uv run pytest

# Add dependency
docker compose exec backend uv add package-name
```

### Frontend Development
```bash
# Generate API types from backend OpenAPI
cd frontend && pnpm generate:api

# Type check
docker compose exec frontend pnpm exec tsc --noEmit

# Format
docker compose exec frontend pnpm format
```

### Database
```bash
# Run seed script
docker compose exec backend uv run python scripts/seed_curriculum.py

# Access database
docker compose exec postgres psql -U explorito explorito
```

### Validation
```bash
# Test all API endpoints
./scripts/test-api.sh

# Check integration
./scripts/validate-integration.sh

# Check frontend
./scripts/validate-frontend.sh
```

## Dev Accounts

Passwords do not exist: parents sign in with Google, children have no login at
all (a parent "acts as" a child via the `X-Acting-Child-Id` header).

| Role | How to authenticate |
|-------|-------------------|
| Admin | `POST /api/v1/auth/dev-login {"email":"admin@explorito.fr"}` — email must be listed in `ADMIN_EMAILS` |
| Parent | `POST /api/v1/auth/dev-login {"email":"parent@explorito.fr"}` |
| Child | No login. Parent token + `X-Acting-Child-Id: <child_id>` |
| Moderator | `X-Moderation-Token: $MODERATION_TOKEN` on `/api/v1/moderation/*` only |

## Design System - Fun Palette

### Color Palette

| Token | Name | Hex | Tailwind Class | Usage |
|-------|------|-----|---------------|-------|
| Primary | Lime Green | `#58CC02` | `fun-green` | Main CTA buttons, active states, correct answers, logo |
| Primary Light | Soft Lime | `#E8F5D6` | `fun-green-light` | Backgrounds, highlights, skeleton loading |
| Primary Dark | Deep Lime | `#45A302` | `fun-green-dark` | Hover states on primary buttons |
| Secondary | Fresh Sky | `#1CAFF6` | `fun-sky` | Secondary buttons, selected states, links |
| Secondary Light | Pale Sky | `#E0F4FF` | `fun-sky-light` | Info backgrounds, selected backgrounds |
| Accent | Violet | `#F28DEE` | `fun-violet` | Fun accents, badges, decorative elements |
| Accent Light | Soft Violet | `#FCE7FB` | `fun-violet-light` | Accent backgrounds |
| Reward | Tuscan Sun | `#F3C35B` | `fun-sun` | Stars, XP, streaks, rewards |
| Reward Light | Pale Sun | `#FEF5E0` | `fun-sun-light` | Reward backgrounds |
| Error | Strawberry | `#EF4444` | `fun-red` | Wrong answers |
| Error Light | Rose | `#FEE2E2` | `fun-red-light` | Error backgrounds |
| Surface | White | `#FFFFFF` | `fun-surface` | Page background base |
| Text | Oxford Navy | `#042C60` | `fun-text` | Primary text, headings |
| Text Muted | Slate | `#64748B` | `fun-text-muted` | Secondary text, labels |
| Border | Light Gray | `#E2E8F0` | `fun-border` | Borders, dividers |

### Font
- **Primary:** Nunito (loaded via `next/font/google`, variable `--font-nunito`)
- **Weights:** 400 (body), 600 (semi), 700 (bold), 800 (extrabold for headings)
- **Fallback:** system-ui, sans-serif

### Component Styling Rules

| Element | Rule |
|---------|------|
| Cards | `rounded-2xl candy-shadow` (or `rounded-3xl` for hero cards) |
| Buttons | `rounded-xl`, min height `h-11`, `active:scale-95` for tap feedback |
| Inputs | `rounded-xl h-12 border-2` |
| Progress bars | `h-3 rounded-full`, track `bg-fun-green-light`, fill `bg-fun-green` |
| Dialogs | `rounded-2xl`, overlay `bg-black/40` |
| Touch targets | Minimum `48px` height for all interactive elements (kids' fingers) |

### Shadows (Neutral Gray, defined in globals.css)

```
candy-shadow      - Subtle neutral shadow for cards: rgba(0,0,0,0.06)
candy-shadow-lg   - Larger shadow for hover states: rgba(0,0,0,0.10)
candy-shadow-glow - Glowing green shadow for active/focus: rgba(88,204,2,0.15)
```

### Animations (defined as @keyframes in globals.css)

| Name | Usage | Example |
|------|-------|---------|
| `candy-bounce` | Bouncing mascot/icons | `animate-[candy-bounce_2s_ease-in-out_infinite]` |
| `candy-wiggle` | Playful wiggle | `animate-[candy-wiggle_1s_ease-in-out_infinite]` |
| `candy-pop` | Entry/appear animation | `animate-[candy-pop_0.6s_ease-out]` |
| `candy-glow` | Pulsing green glow (active items) | `animate-[candy-glow_2s_infinite]` |
| `candy-float` | Float up and fade (XP gain) | `animate-[candy-float_1.2s_ease-out_forwards]` |
| `candy-spin-slow` | Loading spinner | `animate-[candy-spin-slow_1s_linear_infinite]` |
| `candy-shake` | Wrong answer shake | `animate-[candy-shake_0.5s_ease-in-out]` |
| `confetti-fall` | Confetti particles | `animate-[confetti-fall_Xs_ease-in_forwards]` |
| `feedback-slide-up` | Feedback panel entry | `animate-[feedback-slide-up_0.4s_ease-out]` |

### Loading Spinner Pattern
```html
<div class="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-fun-green-light border-t-fun-green"></div>
```

### Mobile-First Responsive Patterns

| Pattern | Implementation |
|---------|---------------|
| Bottom tab bar | `<BottomNav />` component, hidden on `md:` and above |
| Header nav | Desktop nav links hidden on mobile (`hidden md:flex`), shown in bottom nav instead |
| Content padding | `pb-20 md:pb-6` to account for bottom nav |
| Page backgrounds | Light gradients: `from-fun-sky-light via-white to-fun-violet-light` |
| Grid layouts | `grid-cols-1 md:grid-cols-2 lg:grid-cols-3` |
| CTA buttons | Stack on mobile: `flex-col sm:flex-row` |

### Exercise State Colors

| State | Color Token | Usage |
|-------|------------|-------|
| Selected (not validated) | `fun-sky` / `fun-sky-light` | Border, background, text for selected options |
| Correct | `fun-green` / `fun-green-light` | Border, background, check marks |
| Wrong | `fun-red` / `fun-red-light` | Border, background, X marks |

### Do's and Don'ts

**Do:**
- Use fun palette tokens (`text-fun-text`, `bg-fun-green-light`) instead of raw Tailwind colors
- Use `candy-shadow` / `candy-shadow-lg` instead of Tailwind `shadow` / `shadow-lg`
- Use global animations from globals.css instead of component-scoped `<style jsx>`
- Keep all interactive elements >= 48px tall
- Use `rounded-xl` or larger for kid-facing elements
- Test at 375px width for mobile
- Use `fun-sky` for selected-but-not-validated states in exercises

**Don't:**
- Use raw gray/blue/green colors (`text-gray-600`, `bg-blue-50`) -- always use fun tokens
- Use `animate-spin` -- use `animate-[candy-spin-slow_1s_linear_infinite]`
- Use `shadow` directly on Card -- it's already set to `candy-shadow` in the base component
- Add dark mode styles -- the app is light-only for kids
- Use font sizes smaller than `text-sm` in child-facing content
- Use old `candy-*` color tokens -- they have been replaced with `fun-*`

## Error Handling

### Common Issues

1. **CORS Error**: Check `backend/.env` CORS_ORIGINS includes frontend URL (http://localhost:3005)
2. **404 on API call**: Endpoint doesn't exist - check `/openapi.json`
3. **Type mismatch**: Regenerate with `pnpm generate:api`
4. **Auth error**: Token expired or invalid - re-login
5. **Port conflict**: Update docker-compose.yml ports

### Debug Steps
1. Check backend logs: `docker compose logs backend --tail 50`
2. Check frontend logs: `docker compose logs frontend --tail 50`
3. Test endpoint with curl first
4. Check browser Network tab for actual request/response
5. Regenerate API types: `pnpm generate:api`
