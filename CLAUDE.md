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
| Child | arthur (login)    | arthur123 |

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
