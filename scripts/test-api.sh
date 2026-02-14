#!/bin/bash
# Test API endpoints for Explorito
# Run this after backend changes to verify endpoints work

set -e
set -o pipefail

API_URL="${API_URL:-http://localhost:8000}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED=0
PASSED=0

test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local data=$4
    local auth=$5

    local status
    if [[ -n "$auth" && -n "$data" ]]; then
        status=$(curl -s -o /dev/null -w '%{http_code}' -X "$method" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $auth" \
            -d "$data" \
            "$API_URL$endpoint" 2>/dev/null || echo "000")
    elif [[ -n "$auth" ]]; then
        status=$(curl -s -o /dev/null -w '%{http_code}' -X "$method" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $auth" \
            "$API_URL$endpoint" 2>/dev/null || echo "000")
    elif [[ -n "$data" ]]; then
        status=$(curl -s -o /dev/null -w '%{http_code}' -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint" 2>/dev/null || echo "000")
    else
        status=$(curl -s -o /dev/null -w '%{http_code}' -X "$method" \
            "$API_URL$endpoint" 2>/dev/null || echo "000")
    fi

    if [[ "$status" == "$expected_status" ]]; then
        echo -e "${GREEN}✓${NC} $method $endpoint -> $status"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $method $endpoint -> $status (expected $expected_status)"
        FAILED=$((FAILED + 1))
        return 0
    fi
}

echo "=========================================="
echo "API Endpoint Tests - Explorito"
echo "=========================================="
echo ""

# Health check
echo "--- Health ---"
test_endpoint "GET" "/health" "200"
test_endpoint "GET" "/" "200"

# Auth endpoints (no auth required)
echo ""
echo "--- Auth (Public) ---"
test_endpoint "POST" "/api/v1/auth/login" "200" '{"email":"admin@explorito.fr","password":"admin123"}'

# Get token for authenticated requests
TOKEN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@explorito.fr","password":"admin123"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [[ -z "$TOKEN" ]]; then
    echo -e "${RED}✗${NC} Failed to get auth token!"
    exit 1
fi
echo -e "${GREEN}✓${NC} Got auth token"

# Auth endpoints (auth required)
echo ""
echo "--- Auth (Protected) ---"
test_endpoint "GET" "/api/v1/auth/me" "200" "" "$TOKEN"

# Subjects
echo ""
echo "--- Subjects ---"
test_endpoint "GET" "/api/v1/subjects" "200" "" "$TOKEN"

# Get first subject ID for further tests
SUBJECT_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/api/v1/subjects" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [[ -n "$SUBJECT_ID" ]]; then
    echo "  Using subject: $SUBJECT_ID"
    test_endpoint "GET" "/api/v1/subjects/$SUBJECT_ID" "200" "" "$TOKEN"
fi

# Lessons
echo ""
echo "--- Lessons ---"
test_endpoint "GET" "/api/v1/lessons" "200" "" "$TOKEN"

if [[ -n "$SUBJECT_ID" ]]; then
    test_endpoint "GET" "/api/v1/lessons?subject_id=$SUBJECT_ID" "200" "" "$TOKEN"
fi

# Get first lesson ID
LESSON_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/api/v1/lessons" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [[ -n "$LESSON_ID" ]]; then
    echo "  Using lesson: $LESSON_ID"
    test_endpoint "GET" "/api/v1/lessons/$LESSON_ID" "200" "" "$TOKEN"
fi

# Exercises
echo ""
echo "--- Exercises ---"
if [[ -n "$LESSON_ID" ]]; then
    test_endpoint "GET" "/api/v1/exercises?lesson_id=$LESSON_ID" "200" "" "$TOKEN"
fi

# Progress
echo ""
echo "--- Progress ---"
test_endpoint "GET" "/api/v1/progress/me" "200" "" "$TOKEN"

# Gamification
echo ""
echo "--- Gamification ---"
test_endpoint "GET" "/api/v1/gamification/achievements" "200" "" "$TOKEN"
test_endpoint "GET" "/api/v1/gamification/achievements/me" "200" "" "$TOKEN"
test_endpoint "GET" "/api/v1/gamification/streak" "200" "" "$TOKEN"

# Child stats access test
echo ""
echo "--- Child Stats Access (Bug Fix Validation) ---"
# Get child token
CHILD_TOKEN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"arthur@pascalfamily.fr","password":"child123"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [[ -n "$CHILD_TOKEN" ]]; then
    echo -e "${GREEN}✓${NC} Child login successful"

    # Get child ID from token
    CHILD_ID="060bad82-6f38-473e-b414-5aeb8a560306"

    # Test child can access their own stats (should succeed with 200)
    test_endpoint "GET" "/api/v1/gamification/$CHILD_ID/stats" "200" "" "$CHILD_TOKEN"

    # Test child cannot access another child's stats (should fail with 403)
    OTHER_CHILD_ID="9769ea1f-8950-4252-a779-93f16e5f2104"
    test_endpoint "GET" "/api/v1/gamification/$OTHER_CHILD_ID/stats" "403" "" "$CHILD_TOKEN"
else
    echo -e "${YELLOW}⚠${NC} Could not test child stats access (child login failed)"
fi

# Children (requires parent account)
echo ""
echo "--- Children (requires parent account) ---"
# Admin can't access children endpoint, so expect 403
test_endpoint "GET" "/api/v1/children" "403" "" "$TOKEN"

# Summary
echo ""
echo "=========================================="
echo "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
echo "=========================================="

if [[ $FAILED -gt 0 ]]; then
    echo ""
    echo -e "${YELLOW}Some endpoints failed. Check if they need to be implemented.${NC}"
    exit 1
fi

exit 0
