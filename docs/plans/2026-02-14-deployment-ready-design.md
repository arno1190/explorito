# Explorito: Path to Deployment

**Date**: 2026-02-14
**Goal**: Take Explorito from MVP to a deployed, polished family educational app.

## Context

Explorito is a Duolingo-like educational app for CP-level children (6-7 years). The MVP was built through 8 Ralph iterations (completed 2026-02-02). Core features work: role-based routing, parent dashboard with impersonation, child play interface with Duolingo-style lesson tree, gamification (XP/streaks/achievements), 24 French reading lessons with 120+ exercises.

**Target audience**: Family use only (Arthur + siblings).
**Deployment target**: Scaleway DEV1-S with Docker Compose + Caddy.

## Phase 1: Project Foundation

**Git initialization:**
- Init git repo with `.gitignore` (Python, Node, Docker, env files, generated API code)
- Initial commit with existing code
- Push to GitHub (personal account via `gh auth switch`)

**Cleanup:**
- Remove Ralph artifacts: `BUG_FIX_SUMMARY.md`, `progress.txt`, `prompt.md`
- Create `.env.example` files for backend and frontend
- Verify `.gitignore` excludes secrets, node_modules, __pycache__, .env files

## Phase 2: Bug Fixing & Verification

**Boot and verify:**
- Start Docker services, seed database
- Walk through each role flow end-to-end:
  - Admin: login -> /admin dashboard -> user management
  - Parent: login -> /dashboard -> child cards -> impersonate child -> back to parent
  - Child: login -> /play -> select subject -> lesson tree -> exercise flow
- Run `./scripts/test-api.sh` (17 tests)
- Fix any regressions found

**Known concerns to reverify:**
- Child stats 403 fix (gamification.py permission logic)
- Promise.all sequential loading fix (play/page.tsx)
- Exercise interactions (drag & drop, image selection, fill blanks)

## Phase 3: UX Polish (Full)

**Animations:**
- Confetti on lesson completion (enhance existing)
- XP gain animation (+10 XP floating text)
- Streak celebration (fire animation on milestones: 3, 7, 14, 30 days)
- Correct answer: green glow + bounce
- Wrong answer: gentle shake + encouragement text
- Smooth transitions between exercises
- Level up celebration

**Sound effects:**
- Correct answer chime
- Wrong answer gentle tone
- Lesson complete fanfare
- Button tap feedback
- Achievement unlock sound

**Visual polish:**
- Skeleton loading screens (replace spinners)
- Empty states with illustrations
- Touch target verification (60px+ minimum)
- Smooth page transitions

**Files to create:**
- `frontend/src/components/gamification/XPGain.tsx`
- `frontend/src/components/gamification/StreakCelebration.tsx`
- `frontend/src/components/gamification/LevelUp.tsx`
- `frontend/src/components/exercises/ExerciseFeedback.tsx`
- `frontend/src/hooks/useSound.ts`

## Phase 4: Content - Math & Decouverte

**Math (CP level):**
- 12-15 lessons, progressive difficulty
- Topics: counting 0-20, number recognition, addition, subtraction, shapes, comparison
- Exercise types: MCQ, fill-in-the-blank, drag-to-order, counting objects

**Decouverte du monde:**
- 10-12 lessons
- Topics: animals, seasons, human body, senses, day/night, plants
- Exercise types: image matching, MCQ, true/false, categorization

**Implementation:**
- Add content via seed script (like Ratus lessons)
- 5-8 exercises per lesson
- Progressive difficulty with unlock gates
- Images: use emoji or simple SVG illustrations (no external dependencies)

## Phase 5: Production Deployment

**Server: Scaleway DEV1-S (~3.60 EUR/month)**
- 2 vCPU, 2GB RAM, Ubuntu 24.04 LTS
- Docker + Docker Compose

**Architecture:**
```
Internet -> Caddy (auto-HTTPS) ->
  ├── explorito.domain.fr -> Frontend (Next.js)
  └── api.explorito.domain.fr -> Backend (FastAPI)

PostgreSQL (internal only, port 5435)
```

**Production config:**
- `docker-compose.prod.yml` extending base
- Next.js production build (no hot-reload)
- Restart policies (`unless-stopped`)
- Resource limits
- Production environment variables
- Caddy reverse proxy with automatic Let's Encrypt HTTPS

**Deployment workflow:**
- Manual: `git pull && docker compose -f docker-compose.prod.yml up -d --build`
- Future: GitHub Actions for CI/CD

**Backup:**
- Nightly `pg_dump` via cron to Scaleway Object Storage
- Retain last 7 days

## Implementation Order

1. Phase 1 (Foundation) - must be first
2. Phase 2 (Bug fixes) - verify before adding features
3. Phase 3 (UX polish) - parallel with Phase 4
4. Phase 4 (Content) - parallel with Phase 3
5. Phase 5 (Deploy) - after everything works locally

## Success Criteria

- [ ] Git repo initialized with clean history on GitHub
- [ ] All 3 role flows work end-to-end without errors
- [ ] Sound effects play on exercise interactions
- [ ] Animations feel responsive and child-friendly
- [ ] Math has 12+ lessons with exercises
- [ ] Decouverte has 10+ lessons with exercises
- [ ] App accessible via HTTPS on custom domain
- [ ] Database backed up nightly
