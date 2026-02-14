#!/bin/bash
# Validate frontend-backend integration
# Checks that frontend API calls match backend endpoints

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "=== Integration Validation ==="
echo ""

# Get all backend routes
echo "Fetching backend routes..."
BACKEND_ROUTES=$(curl -s "$API_URL/openapi.json" 2>/dev/null | grep -o '"\/api\/v1[^"]*' | sort -u | tr -d '"')

if [[ -z "$BACKEND_ROUTES" ]]; then
    echo "✗ Could not fetch backend routes"
    exit 1
fi

echo "Backend routes found:"
echo "$BACKEND_ROUTES" | head -20
echo ""

# Check frontend API file for endpoint references
echo "Checking frontend API calls..."
FRONTEND_API="frontend/src/lib/api.ts"

if [[ ! -f "$FRONTEND_API" ]]; then
    echo "✗ Frontend API file not found: $FRONTEND_API"
    exit 1
fi

# Extract API paths from frontend
FRONTEND_PATHS=$(grep -oE '"/[a-z/_\-{}]+' "$FRONTEND_API" | tr -d '"' | sort -u)

echo "Frontend API paths:"
echo "$FRONTEND_PATHS" | head -20
echo ""

# Check for potential mismatches
WARNINGS=0

# Check children endpoint (known issue)
if grep -q "/children" "$FRONTEND_API"; then
    if ! echo "$BACKEND_ROUTES" | grep -q "/children"; then
        echo "⚠ WARNING: Frontend uses /children but backend may not have this endpoint"
        ((WARNINGS++))
    fi
fi

# Check activities endpoint
if grep -q "/activities" "$FRONTEND_API"; then
    if ! echo "$BACKEND_ROUTES" | grep -q "/activities"; then
        echo "⚠ WARNING: Frontend uses /activities but backend may not have this endpoint"
        ((WARNINGS++))
    fi
fi

echo ""
if [[ $WARNINGS -gt 0 ]]; then
    echo "=== $WARNINGS potential issues found ==="
    echo "Review the warnings above and ensure endpoints exist"
else
    echo "=== No obvious mismatches found ==="
fi

exit 0
