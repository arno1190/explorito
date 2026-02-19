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

# Test with auth
TOKEN=$(curl -s -X POST http://localhost:8005/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@explorito.fr","password":"admin123"}' | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" http://localhost:8005/api/v1/your-endpoint
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
docker compose exec backend uv run python scripts/seed_database.py

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

## User Credentials

| Role  | Email              | Password |
|-------|-------------------|----------|
| Admin | admin@explorito.fr | admin123 |
| Child | alice (login)    | alice123 |

## Design System - Candy Garden

### Color Palette

| Token | Name | Hex | Tailwind Class | Usage |
|-------|------|-----|---------------|-------|
| Primary | Vivid Purple | `#7C3AED` | `candy-purple` | Main actions, active states, logo |
| Primary Light | Soft Lavender | `#EDE9FE` | `candy-purple-light` | Backgrounds, highlights, skeleton loading |
| Primary Dark | Deep Purple | `#5B21B6` | `candy-purple-dark` | Hover states |
| Secondary | Coral Orange | `#F97316` | `candy-orange` | Gamification, streaks |
| Secondary Light | Peach | `#FFF7ED` | `candy-orange-light` | Warm backgrounds |
| Success | Emerald | `#10B981` | `candy-green` | Correct answers, completed items |
| Success Light | Mint | `#D1FAE5` | `candy-green-light` | Success backgrounds |
| Error | Strawberry | `#EF4444` | `candy-red` | Wrong answers |
| Error Light | Rose | `#FEE2E2` | `candy-red-light` | Error backgrounds |
| Reward | Sunshine | `#F59E0B` | `candy-yellow` | Stars, XP, rewards |
| Reward Light | Lemon | `#FEF3C7` | `candy-yellow-light` | Reward backgrounds |
| Accent | Cotton Candy | `#EC4899` | `candy-pink` | Fun accents |
| Surface | Cream | `#FFFBF5` | `candy-surface` | Page backgrounds |
| Text | Deep Indigo | `#1E1B4B` | `candy-text` | Primary text |
| Text Muted | Warm Gray | `#6B7280` | `candy-text-muted` | Secondary text |
| Border | Soft Lavender | `#E5E1F5` | `candy-border` | Borders, dividers |

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
| Progress bars | `h-3 rounded-full`, track `bg-candy-purple-light`, fill gradient |
| Dialogs | `rounded-2xl`, overlay `bg-black/40` |
| Touch targets | Minimum `48px` height for all interactive elements (kids' fingers) |

### Custom CSS Classes (defined in globals.css)

```
candy-shadow      - Subtle purple-tinted shadow for cards
candy-shadow-lg   - Larger shadow for hover states
candy-shadow-glow - Glowing shadow for active/focus states
```

### Animations (defined as @keyframes in globals.css)

| Name | Usage | Example |
|------|-------|---------|
| `candy-bounce` | Bouncing mascot/icons | `animate-[candy-bounce_2s_ease-in-out_infinite]` |
| `candy-wiggle` | Playful wiggle | `animate-[candy-wiggle_1s_ease-in-out_infinite]` |
| `candy-pop` | Entry/appear animation | `animate-[candy-pop_0.6s_ease-out]` |
| `candy-glow` | Pulsing glow (active items) | `animate-[candy-glow_2s_infinite]` |
| `candy-float` | Float up and fade (XP gain) | `animate-[candy-float_1.2s_ease-out_forwards]` |
| `candy-spin-slow` | Loading spinner | `animate-[candy-spin-slow_1s_linear_infinite]` |
| `candy-shake` | Wrong answer shake | `animate-[candy-shake_0.5s_ease-in-out]` |
| `confetti-fall` | Confetti particles | `animate-[confetti-fall_Xs_ease-in_forwards]` |
| `feedback-slide-up` | Feedback panel entry | `animate-[feedback-slide-up_0.4s_ease-out]` |

### Loading Spinner Pattern
```html
<div class="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-candy-purple-light border-t-candy-purple"></div>
```

### Mobile-First Responsive Patterns

| Pattern | Implementation |
|---------|---------------|
| Bottom tab bar | `<BottomNav />` component, hidden on `md:` and above |
| Header nav | Desktop nav links hidden on mobile (`hidden md:flex`), shown in bottom nav instead |
| Content padding | `pb-20 md:pb-6` to account for bottom nav |
| Page backgrounds | Candy gradients: `from-candy-purple-light via-candy-surface to-candy-orange-light` |
| Grid layouts | `grid-cols-1 md:grid-cols-2 lg:grid-cols-3` |
| CTA buttons | Stack on mobile: `flex-col sm:flex-row` |

### Do's and Don'ts

**Do:**
- Use candy palette tokens (`text-candy-text`, `bg-candy-purple-light`) instead of raw Tailwind colors
- Use `candy-shadow` / `candy-shadow-lg` instead of Tailwind `shadow` / `shadow-lg`
- Use global animations from globals.css instead of component-scoped `<style jsx>`
- Keep all interactive elements >= 48px tall
- Use `rounded-xl` or larger for kid-facing elements
- Test at 375px width for mobile

**Don't:**
- Use raw gray/blue/green colors (`text-gray-600`, `bg-blue-50`) -- always use candy tokens
- Use `animate-spin` -- use `animate-[candy-spin-slow_1s_linear_infinite]`
- Use `shadow` directly on Card -- it's already set to `candy-shadow` in the base component
- Add dark mode styles -- the app is light-only for kids
- Use font sizes smaller than `text-sm` in child-facing content

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
