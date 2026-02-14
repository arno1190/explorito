# 🎓 Explorito - Application Éducative Famille (CP+)

Application éducative gamifiée inspirée de Duolingo pour les enfants de 6 ans en CP. Permet de progresser dans **toutes les matières du programme** avec un système de suivi famille complet.

## 📋 Vue d'ensemble

### Fonctionnalités principales

- ✅ **Authentification complète** : Parents et enfants avec gestion de rôles
- ✅ **Contenu Ratus intégré** : 24 leçons + 120+ exercices de lecture syllabique
- ✅ **6 matières** : Français, Mathématiques, Écriture, Questionner le Monde, Arts, Musique
- ✅ **12 types d'exercices** : QCM, Drag & Drop, Fill Blanks, True/False, Image Selection, etc.
- ✅ **Gamification complète** : XP, niveaux, badges, streaks, récompenses
- ✅ **Dashboard parent** : Suivi multi-enfants avec statistiques détaillées
- ✅ **130+ images Ratus** extraites et optimisées (format WebP)

### Tech Stack

**Backend:**
- Python 3.12 + FastAPI + SQLAlchemy 2.0
- PostgreSQL
- JWT Authentication
- Alembic migrations

**Frontend:**
- Next.js 16 (App Router)
- React 19 + TypeScript
- TailwindCSS 4 + shadcn/ui
- React Query (TanStack Query)
- Lucide Icons

**Infrastructure:**
- Docker + Docker Compose
- Multi-container (PostgreSQL + Backend + Frontend)

## 🚀 Démarrage Rapide

### Prérequis

- Docker et Docker Compose installés
- Node.js 20+ (pour le dev frontend hors Docker)
- Python 3.12+ (pour le dev backend hors Docker)

### Installation

```bash
# Cloner le repo (si applicable)
cd explorito

# Copier les variables d'environnement
cp .env.example .env

# Démarrer l'infrastructure avec Docker
docker-compose up -d

# Attendre que les services soient prêts (PostgreSQL + Backend)
# Vérifier avec: docker-compose logs -f backend
# Le backend crée automatiquement les tables au démarrage

# Le backend démarre sur http://localhost:8000
# Le frontend démarre sur http://localhost:3000
```

### Initialisation de la base de données

> **Note**: Les tables sont créées automatiquement au démarrage du backend (`Base.metadata.create_all`). Aucune migration manuelle n'est requise.

```bash
# 1. Vérifier que le backend est prêt
curl http://localhost:8000/health
# Doit retourner: {"status": "ok"}

# 2. Se connecter au container backend
docker-compose exec backend bash

# 3. Lancer le script de seed
python scripts/seed_database.py

# Le script va :
# - Créer 6 matières
# - Créer 24 leçons Ratus avec 120+ exercices
# - Créer 8 achievements
# - Créer un admin : admin@explorito.fr / admin123
# - Copier 130+ images Ratus dans uploads/
```

### Troubleshooting

Si vous rencontrez des erreurs lors du seed:
```bash
# Vérifier les logs du backend
docker-compose logs backend

# Redémarrer les services si nécessaire
docker-compose restart backend

# Vérifier la connexion à PostgreSQL
docker-compose exec backend python -c "from app.core.database import engine; print(engine.url)"
```

### Accès à l'application

- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8000
- **API Documentation** : http://localhost:8000/docs
- **Admin credentials** : admin@explorito.fr / admin123

## 📂 Structure du Projet

```
explorito/
├── backend/                        # Backend FastAPI
│   ├── app/
│   │   ├── models/                 # Modèles SQLAlchemy
│   │   │   ├── user.py             # User, Profile
│   │   │   ├── content.py          # Subject, Lesson, Exercise, Media
│   │   │   ├── progress.py         # UserProgress, ExerciseResult
│   │   │   ├── gamification.py     # Achievement, Streak, Reward
│   │   │   ├── family.py           # FamilyGroup, FamilyMember
│   │   │   └── review.py           # ReviewQueue (spaced repetition)
│   │   ├── schemas/                # Schémas Pydantic
│   │   ├── api/                    # Endpoints API
│   │   │   ├── auth.py             # Authentication (register, login, refresh)
│   │   │   ├── subjects.py         # Gestion des matières
│   │   │   ├── lessons.py          # Gestion des leçons
│   │   │   ├── exercises.py        # Gestion des exercices + submit
│   │   │   ├── progress.py         # Suivi de progression
│   │   │   └── gamification.py     # XP, achievements, streaks
│   │   ├── core/                   # Configuration
│   │   │   ├── config.py           # Settings
│   │   │   ├── database.py         # SQLAlchemy setup
│   │   │   └── security.py         # JWT + password hashing
│   │   ├── services/               # Logique métier
│   │   │   └── gamification.py     # Calcul XP, niveaux, unlocks
│   │   └── main.py                 # Application FastAPI
│   ├── scripts/
│   │   ├── extract_ratus_content.py     # Extraction PDF Ratus
│   │   ├── process_images.py            # Optimisation images (WebP)
│   │   ├── create_lesson_structure.py   # Structure 24 leçons Ratus
│   │   └── seed_database.py             # Peupler la DB
│   ├── extracted_content/
│   │   ├── ratus_manifest.json          # Manifest Ratus (24 leçons)
│   │   └── images/                      # 130+ images extraites
│   ├── uploads/                    # Uploads utilisateur + images Ratus
│   ├── tests/                      # Tests pytest
│   ├── requirements.txt            # Dépendances Python
│   ├── Dockerfile                  # Docker backend
│   └── alembic/                    # Migrations DB
│
├── frontend/                       # Frontend Next.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/             # Pages auth (login, register)
│   │   │   ├── (app)/              # Pages protégées
│   │   │   │   ├── dashboard/      # Dashboard parent
│   │   │   │   ├── subjects/       # Liste des matières
│   │   │   │   ├── lessons/        # Liste des leçons
│   │   │   │   └── exercises/      # Page exercice + submit
│   │   │   ├── layout.tsx          # Root layout
│   │   │   └── providers.tsx       # React Query + Auth
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui components
│   │   │   ├── layout/             # Header, ChildLayout
│   │   │   ├── exercises/          # Composants exercices
│   │   │   │   ├── MultipleChoice.tsx
│   │   │   │   ├── DragAndDrop.tsx
│   │   │   │   ├── FillBlanks.tsx
│   │   │   │   ├── TrueFalse.tsx
│   │   │   │   ├── ImageSelection.tsx
│   │   │   │   └── ExerciseRenderer.tsx
│   │   │   └── gamification/       # XPBar, Streak, Badge, Confetti
│   │   ├── lib/
│   │   │   ├── api.ts              # Client API Axios
│   │   │   ├── auth.tsx            # AuthContext + useAuth
│   │   │   └── utils.ts            # Utilitaires (cn, etc.)
│   │   └── types/
│   │       └── index.ts            # Types TypeScript
│   ├── public/                     # Assets statiques
│   ├── package.json                # Dépendances npm
│   └── Dockerfile                  # Docker frontend
│
├── docker-compose.yml              # Docker Compose config
├── .env.example                    # Variables d'environnement exemple
└── README.md                       # Ce fichier
```

## 🎮 Guide Utilisateur

### Pour les Parents

1. **Inscription**
   - Créer un compte parent sur la page `/register`
   - Email + mot de passe

2. **Ajouter des enfants**
   - Dashboard parent : ajouter un ou plusieurs enfants
   - Nom + date de naissance

3. **Suivre la progression**
   - Dashboard : voir les statistiques de chaque enfant
   - XP total, niveau, leçons complétées, précision

### Pour les Enfants

1. **Connexion** (avec compte parent)
   - Le parent se connecte et sélectionne l'enfant

2. **Choisir une matière**
   - Page `/subjects` : grille colorée des 6 matières

3. **Faire les leçons**
   - Cliquer sur une matière → liste des leçons
   - Commencer une leçon → faire les exercices
   - Gagner des points XP et des badges !

4. **Types d'exercices disponibles**
   - ✅ QCM (Multiple Choice)
   - ✅ Vrai/Faux
   - ✅ Drag & Drop (glisser-déposer)
   - ✅ Fill Blanks (remplir les trous)
   - ✅ Image Selection (cliquer sur l'image)
   - 🚧 Ordering (remettre dans l'ordre)
   - 🚧 Dictée Audio
   - 🚧 Dessin/Traçage
   - 🚧 Comptage
   - 🚧 Puzzle
   - 🚧 Memory Game
   - 🚧 Odd One Out (intrus)

## 🗂️ Contenu Pédagogique Actuel

### Français - Lecture Ratus (24 leçons)

1. Le rat et le chat (son [a])
2. Marou le pirate (sons [m], [ma], [mo], [mu])
3. Ralette (sons [r], [ra], [ri], [ro], [ru])
4. L'école de Ratus (sons [l], [la], [le], [li], [lo], [lu])
5. Mina la fourmi (sons [i], [mi], [ni])
6. Papa, maman (sons [p], [pa], [pi], [po])
7. Belo a disparu (sons [b], [ba], [bi], [bo], [bu])
8. Le vélo de Ratus (sons [v], [va], [vi], [vo], [vu])
9. Ratus à la télévision (sons [t], [ta], [ti], [to], [tu])
10. Ratus raconte des salades (sons [s], [sa], [si], [so], [su])
11. Au feu ! (sons [f], [fa], [fi], [fo], [fu])
12. Une drôle de poule (son [ou])
13. On a volé Marou (son [on])
14. Ratus champion (son [ch])
15. Un invité bizarre (sons [in], [im])
16. Ratus sur l'île déserte (sons [an], [am], [en], [em])
17. La soupe aux étoiles (sons [é], [è], [ê])
18. Ratus magicien (sons [c], [ç])
19. Un voyage en auto (sons [au], [eau])
20. Un roi sur un pois (son [oi])
21. Ratus chez le coiffeur (sons [eu], [œu])
22. La grande aiguille (sons [g], [gu])
23. La montagne (son [gn])
24. Récapitulation (révision)

**Total actuel** : 24 leçons × 4-5 exercices = ~120 exercices

### Matières disponibles (structure créée)

- ✅ Français (Lecture Ratus)
- 🚧 Mathématiques (à peupler)
- 🚧 Écriture & Orthographe (à peupler)
- 🚧 Questionner le Monde (à peupler)
- 🚧 Arts Visuels (à peupler)
- 🚧 Éducation Musicale (à peupler)

## 🎖️ Gamification

### Système XP et Niveaux

- **XP par exercice** : 10 points
- **XP par leçon** : 50 points
- **Calcul du niveau** : `Level = floor(sqrt(XP/100)) + 1`

### Achievements (8 créés)

1. 🎓 **Première leçon** - Compléter 1 leçon (Common)
2. 🔥 **Série de 3 jours** - Streak de 3 jours (Common)
3. 📚 **Expert en lecture** - Compléter 10 leçons (Rare)
4. 🏆 **Champion Ratus** - Compléter les 24 leçons Ratus (Epic)
5. 🔢 **Mathématicien Junior** - Compléter 5 leçons de maths (Rare)
6. 🔥 **Série de 7 jours** - Streak de 7 jours (Epic)
7. 💯 **100 Exercices** - Compléter 100 exercices (Rare)
8. ⭐ **Perfectionniste** - Obtenir 3 étoiles sur 10 leçons (Legendary)

### Streaks

- Série de jours consécutifs
- Jokers disponibles (freeze)
- Affichage du record personnel

## 🔧 Développement

### Backend

```bash
cd backend

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur (mode dev)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Lancer les tests
pytest tests/ -v --cov=app

# Créer une migration Alembic
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Frontend

```bash
cd frontend

# Installer les dépendances
pnpm install

# Lancer le serveur dev
pnpm dev

# Build de production
pnpm build

# Lancer en mode production
pnpm start

# Linter
pnpm lint

# Formatter (Prettier)
pnpm format
```

### Extraction Ratus (déjà fait)

```bash
cd backend

# Extraire les images du PDF
python scripts/extract_ratus_content.py

# Optimiser les images (WebP)
python scripts/process_images.py

# Créer la structure des leçons
python scripts/create_lesson_structure.py
```

## 📊 API Documentation

Accéder à la documentation Swagger interactive :

**http://localhost:8000/docs**

### Endpoints principaux

**Authentification**
- `POST /api/v1/auth/register` - Inscription
- `POST /api/v1/auth/login` - Connexion
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Utilisateur actuel

**Contenu**
- `GET /api/v1/subjects` - Liste des matières
- `GET /api/v1/lessons?subject_id=<uuid>` - Leçons d'une matière
- `GET /api/v1/lessons/{id}` - Détails d'une leçon
- `POST /api/v1/lessons/{id}/start` - Commencer une leçon
- `GET /api/v1/exercises?lesson_id=<uuid>` - Exercices d'une leçon
- `POST /api/v1/exercises/{id}/submit` - Soumettre une réponse

**Progression**
- `GET /api/v1/progress/me` - Ma progression globale
- `GET /api/v1/progress/subjects/{id}` - Progression par matière
- `GET /api/v1/progress/lessons/{id}` - Progression par leçon

**Gamification**
- `GET /api/v1/gamification/achievements` - Tous les achievements
- `GET /api/v1/gamification/achievements/me` - Mes achievements
- `GET /api/v1/gamification/streak` - Ma série
- `GET /api/v1/gamification/daily-goal` - Objectif du jour

## 🐳 Docker

### Structure Docker Compose

```yaml
services:
  postgres:     # Base de données PostgreSQL
  backend:      # API FastAPI (port 8000)
  frontend:     # Next.js (port 3000)
```

### Commandes Docker utiles

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Redémarrer un service
docker-compose restart backend

# Arrêter tous les services
docker-compose down

# Reconstruire les images
docker-compose build

# Nettoyer les volumes (⚠️ supprime les données)
docker-compose down -v
```

## 🚀 Déploiement Production

### Configuration

1. Générer une SECRET_KEY sécurisée :
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. Mettre à jour `.env` avec :
   - `SECRET_KEY` généré
   - `DATABASE_URL` de production
   - `DEBUG=False`
   - `CORS_ORIGINS` avec le domaine frontend

3. Utiliser `docker-compose.prod.yml` (à créer)

### Backups

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U explorito explorito > backup.sql

# Restore
cat backup.sql | docker-compose exec -T postgres psql -U explorito explorito
```

## 📝 TODOs / Roadmap

### Backend ✅ Complété

- [x] Modèles SQLAlchemy complets
- [x] Authentification JWT
- [x] Endpoints CRUD pour tout le contenu
- [x] Système de progression
- [x] Gamification (XP, achievements, streaks)
- [x] Service de gamification
- [x] Extraction PDF Ratus + 130 images
- [x] Script de seed avec 24 leçons + 120 exercices

### Frontend ✅ Complété

- [x] Setup Next.js 16 + TypeScript
- [x] shadcn/ui configuré
- [x] AuthContext + hooks
- [x] Pages auth (login, register)
- [x] Dashboard parent
- [x] Pages subjects, lessons, exercises
- [x] 5 composants d'exercices (MCQ, TrueFalse, DragDrop, FillBlanks, ImageSelection)
- [x] Composants gamification (XPBar, Streak, Badge, Confetti)
- [x] Layout enfant coloré

### À compléter 🚧

**Contenu**
- [ ] Ajouter 50+ leçons de Mathématiques
- [ ] Ajouter 30+ leçons d'Écriture/Orthographe
- [ ] Ajouter 25+ leçons Questionner le Monde
- [ ] Ajouter 10+ leçons Arts
- [ ] Ajouter 5+ leçons Musique
- [ ] Objectif : 200+ leçons, 1000+ exercices

**Fonctionnalités**
- [ ] 7 types d'exercices supplémentaires
- [ ] Synthèse vocale (Web Speech API)
- [ ] Mode révision (spaced repetition)
- [ ] Rapports PDF pour parents
- [ ] Notifications email
- [ ] Mode hors-ligne (PWA)
- [ ] Graphiques de progression
- [ ] Leaderboard famille
- [ ] Interface admin CMS
- [ ] Upload de médias

**Qualité**
- [ ] Tests backend >60% coverage
- [ ] Tests frontend E2E (Playwright)
- [ ] CI/CD GitHub Actions
- [ ] Monitoring (logs, Sentry)
- [ ] Documentation utilisateur complète
- [ ] Guide vidéo

## 📄 Licence

Projet privé - Tous droits réservés.

Méthode Ratus : © Hatier (contenu éducatif utilisé à des fins pédagogiques personnelles)

## 👨‍💻 Auteur

Créé avec Claude Code - Agent de développement IA

## 🙏 Crédits

- **Méthode Ratus et Ses Amis** : Hatier (Jean Guion, Jeanine Guion)
- **Next.js** : Vercel
- **FastAPI** : Sebastián Ramírez
- **shadcn/ui** : shadcn
- **Lucide Icons** : Lucide

---

**Version actuelle** : 1.0.0
**Dernière mise à jour** : 2 février 2026

🎓 **Bon apprentissage avec Explorito !**
