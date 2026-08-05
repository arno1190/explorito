#!/usr/bin/env bash
# Staged prod build on the server. Sequential build + cache pruning keeps peak
# disk low on the small (~9 GB) VPS. Run from CI after code is rsynced to
# /opt/explorito. Migrations run automatically on backend container start.
set -euo pipefail

cd /opt/explorito
COMPOSE="docker compose -f docker-compose.prod.yml"

echo "[0/4] reclaim disk before build (small VPS)"
# Free build cache, dangling images, apt cache and journals so the image
# extraction has headroom. Never prune volumes (would drop the DB / uploads).
docker builder prune -af >/dev/null 2>&1 || true
docker image prune -af >/dev/null 2>&1 || true
apt-get clean >/dev/null 2>&1 || true
journalctl --vacuum-size=20M >/dev/null 2>&1 || true
df -h / | tail -1

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
