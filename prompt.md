# Explorito - Mission: Deploy-Ready App

## Design Document
Read `docs/plans/2026-02-14-deployment-ready-design.md` for the full design.

## Current Mission: Make Explorito deploy-ready with polish and content

### Phase 1: Project Foundation (DO FIRST)

1. Create `.gitignore` covering:
   - Python: `__pycache__/`, `*.pyc`, `.venv/`, `*.egg-info/`
   - Node: `node_modules/`, `.next/`, `.turbo/`
   - Docker: volumes, overrides
   - Environment: `.env`, `.env.local`, `.env.production`
   - Generated: `frontend/src/lib/api/generated/`, `frontend/src/lib/api/model/`
   - IDE: `.vscode/`, `.idea/`
   - OS: `.DS_Store`, `Thumbs.db`

2. Create `.env.example` files:
   - `backend/.env.example` (DATABASE_URL, SECRET_KEY, CORS_ORIGINS template)
   - `frontend/.env.example` (NEXT_PUBLIC_API_URL template)

3. Initialize git repo: `git init && git add -A && git commit -m "Initial commit: Explorito MVP"`

4. Set up GitHub remote (personal account):
   - Run `gh auth switch` to personal account if needed
   - Create private repo: `gh repo create explorito --private --source=.`

### Phase 2: Bug Fixing & Verification

1. Start Docker: `docker compose up -d --build`
2. Wait for services, seed database: `docker compose exec backend python scripts/seed_curriculum.py`
3. Run API tests: `./scripts/test-api.sh`
4. Test each login flow manually via curl:
   - Admin (admin@explorito.fr / admin123) -> verify /admin works
   - Parent (parent@test.com / parent123) -> verify /dashboard works
   - Child -> verify /play works with subjects loading
5. Fix any issues found
6. Verify exercise flows work (at least test one lesson's exercises via API)

### Phase 3: UX Polish

Create these components and integrate them:

**Sound system:**
- `frontend/src/hooks/useSound.ts` - Hook to play sounds
- Use Web Audio API or Howler.js for short sound effects
- Sounds: correct, wrong, complete, tap, levelup, achievement

**Animations:**
- `frontend/src/components/gamification/XPGain.tsx` - Floating +XP animation
- `frontend/src/components/gamification/StreakCelebration.tsx` - Fire/streak animation
- `frontend/src/components/gamification/LevelUp.tsx` - Level up overlay
- `frontend/src/components/exercises/ExerciseFeedback.tsx` - Correct/wrong feedback with animation

**Integration:**
- Wire XPGain into exercise completion flow
- Wire StreakCelebration into login/app load when streak milestone
- Wire ExerciseFeedback into each exercise type
- Add skeleton loading to play page and subject pages
- Enhance existing confetti on lesson completion

### Phase 4: Content - Math & Decouverte

**Add to seed script** (`backend/scripts/seed_curriculum.py`):

**Math lessons (12-15):**
1. Les nombres de 0 à 5
2. Les nombres de 6 à 10
3. Compter des objets (1-10)
4. Plus grand, plus petit, égal
5. Addition avec les doigts (0+1 à 5+5)
6. Addition simple (résultat < 10)
7. Soustraction avec les doigts
8. Soustraction simple
9. Les nombres de 11 à 20
10. Addition avec retenue (intro)
11. Les formes (cercle, carré, triangle, rectangle)
12. Mesurer et comparer (long/court, lourd/léger)

Each lesson: 5-8 exercises (MCQ, fill blank, ordering, counting)

**Decouverte du monde lessons (10-12):**
1. Les animaux de la ferme
2. Les animaux sauvages
3. Les 4 saisons
4. Le corps humain (parties)
5. Les 5 sens
6. Le jour et la nuit
7. Les plantes et les arbres
8. L'eau (états, cycle)
9. Les aliments et la nutrition
10. La météo

Each lesson: 5-8 exercises (image matching, MCQ, true/false, categorization)

### Phase 5: Production Config

1. Create `docker-compose.prod.yml`:
   - Next.js production build
   - No volume mounts for code (use COPY in Dockerfile)
   - Restart: unless-stopped
   - Resource limits
   - Production env vars

2. Create `Caddyfile`:
   ```
   explorito.{domain} {
     reverse_proxy frontend:3000
   }
   api.explorito.{domain} {
     reverse_proxy backend:8000
   }
   ```

3. Add Caddy service to prod compose

4. Create deployment script `scripts/deploy.sh`:
   - SSH to server
   - git pull
   - docker compose -f docker-compose.prod.yml up -d --build

5. Create backup script `scripts/backup.sh`:
   - pg_dump to local file
   - Upload to Scaleway Object Storage (s3cmd or rclone)

---

## CRITICAL RULES

1. **ALWAYS use `uv run`** for Python commands (never raw python/pytest)
2. **ALWAYS use `pnpm`** for Node commands (never npm/yarn)
3. **Port mapping**: Backend=8005, Frontend=3005, Postgres=5435
4. **Run quality checks** after editing:
   - Python: `docker compose exec backend uv run ruff check --fix app/ && docker compose exec backend uv run ruff format app/`
   - TypeScript: `docker compose exec frontend pnpm exec tsc --noEmit`
5. **Test after each phase** - don't move on until current phase works
6. **Update progress.txt** after completing each phase

## Test Accounts

| Role   | Email               | Password  |
|--------|---------------------|-----------|
| Admin  | admin@explorito.fr  | admin123  |
| Parent | parent@test.com     | parent123 |
| Child  | (created via parent) | child123 |

## Success Criteria

Update `progress.txt` to `COMPLETED` when ALL of these work:

- [ ] Git repo on GitHub with clean history
- [ ] All 3 role flows work end-to-end
- [ ] Sound effects play on exercise interactions
- [ ] Animations feel responsive and child-friendly
- [ ] Math has 12+ lessons with exercises
- [ ] Decouverte has 10+ lessons with exercises
- [ ] `docker-compose.prod.yml` builds and runs successfully
- [ ] Caddyfile configured for reverse proxy + HTTPS
- [ ] Backup script created and tested locally
