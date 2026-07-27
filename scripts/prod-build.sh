#!/usr/bin/env bash
# Staged prod build on the server. Sequential build + cache pruning keeps peak
# disk low on the small (10 GB) VPS. Run from CI after code is rsynced to
# /opt/explorito. Migrations run automatically on backend container start.
set -euo pipefail

cd /opt/explorito
COMPOSE="docker compose -f docker-compose.prod.yml"

echo "[1/4] build backend"
$COMPOSE build backend
docker builder prune -af >/dev/null 2>&1 || true

echo "[2/4] build frontend (standalone)"
$COMPOSE build frontend
docker builder prune -af >/dev/null 2>&1 || true

echo "[3/4] up (migrations run on backend start)"
$COMPOSE up -d
docker image prune -af >/dev/null 2>&1 || true

echo "[4/4] status"
$COMPOSE ps --format "{{.Service}}: {{.State}}"
