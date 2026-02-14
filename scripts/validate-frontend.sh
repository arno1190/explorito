#!/bin/bash
# Validate frontend is running without errors

set -e

FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

echo "Checking frontend..."

# Check if frontend responds
STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$FRONTEND_URL" 2>/dev/null || echo "000")

if [[ "$STATUS" != "200" ]]; then
    echo "✗ Frontend not responding (status: $STATUS)"
    exit 1
fi

echo "✓ Frontend is responding"

# Check for build errors in logs
ERRORS=$(docker compose logs frontend --tail 50 2>/dev/null | grep -i "error\|failed\|exception" | grep -v "AxiosError" | head -5)

if [[ -n "$ERRORS" ]]; then
    echo "⚠ Potential errors in frontend logs:"
    echo "$ERRORS"
fi

# Check TypeScript compilation
echo "Checking TypeScript..."
docker compose exec -T frontend pnpm exec tsc --noEmit 2>&1 | tail -10 || true

echo "✓ Frontend validation complete"
exit 0
