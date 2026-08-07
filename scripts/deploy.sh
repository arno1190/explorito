#!/bin/bash
set -euo pipefail

# Explorito deployment script
# Usage: ./scripts/deploy.sh [server-host]

SERVER=${1:-${DEPLOY_HOST:-""}}

if [ -z "$SERVER" ]; then
  echo "Usage: ./scripts/deploy.sh <server-host>"
  echo "  or set DEPLOY_HOST environment variable"
  exit 1
fi

echo "=== Deploying Explorito to $SERVER ==="

# Pull latest code
ssh "$SERVER" "cd /opt/explorito && git pull origin main"

# Build and restart
ssh "$SERVER" "cd /opt/explorito && docker compose -f docker-compose.prod.yml up -d --build"

# Run migrations / seed if needed
ssh "$SERVER" "cd /opt/explorito && docker compose -f docker-compose.prod.yml exec -T backend uv run python scripts/seed_math_decouverte.py"

# Verify
ssh "$SERVER" "cd /opt/explorito && docker compose -f docker-compose.prod.yml ps"

echo "=== Deployment complete ==="
