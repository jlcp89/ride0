#!/usr/bin/env bash
# =============================================================================
# Wingz Ride API — Deployed Endpoint Validation
# Usage: bash tests/test_deployed_api.sh [BASE_URL]
# Requires: curl, jq
#
# Auth: the API is Bearer-only. Pre-flight POSTs /api/auth/login/ with the
# seed admin, rider, and driver accounts and stores the returned access tokens
# in ADMIN_TOKEN / RIDER_TOKEN / DRIVER_TOKEN, which are then sent via
# "Authorization: Bearer ..." on every subsequent request.
# =============================================================================
set -euo pipefail

BASE_URL="${1:-http://107.23.122.99}"
ENDPOINT="${BASE_URL}/api/rides/"
LOGIN_URL="${BASE_URL}/api/auth/login/"

ADMIN_EMAIL="admin@wingz.com"
ADMIN_PASSWORD="adminpass123"
RIDER_EMAIL="alice@example.com"
RIDER_PASSWORD="driverpass123"
DRIVER_EMAIL="chris@wingz.com"
DRIVER_PASSWORD="driverpass123"

ADMIN_TOKEN=""
RIDER_TOKEN=""
DRIVER_TOKEN=""

PASS=0
FAIL=0
SKIP=0
TOTAL=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Temp vars set by fetch()
HTTP_CODE=""
BODY=""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

fetch() {
    local url="$1"
    shift
    local raw
    raw=$(curl -s -w "\n%{http_code}" "$@" "$url")
    HTTP_CODE=$(echo "$raw" | tail -1)
    BODY=$(echo "$raw" | sed '$d')
}

fetch_auth() {
    local url="$1"
    fetch "$url" -H "Authorization: Bearer $ADMIN_TOKEN"
}

# POST /api/auth/login/ and echo the access_token (empty string on failure).
get_token() {
    local email="$1" password="$2"
    local body resp
    body=$(jq -n --arg e "$email" --arg p "$password" '{email:$e, password:$p}')
    resp=$(curl -s -X POST "$LOGIN_URL" \
        -H "Content-Type: application/json" \
        -d "$body")
    echo "$resp" | jq -r '.access_token // empty'
}

pass_test() {
    local id="$1" desc="$2"
    ((PASS++)) || true
    ((TOTAL++)) || true
    printf "  ${GREEN}PASS${NC}  %-12s %s\n" "$id" "$desc"
}

fail_test() {
    local id="$1" desc="$2" reason="${3:-}"
    ((FAIL++)) || true
    ((TOTAL++)) || true
    printf "  ${RED}FAIL${NC}  %-12s %s\n" "$id" "$desc"
    if [[ -n "$reason" ]]; then
        printf "        ${RED}→ %s${NC}\n" "$reason"
    fi
}

skip_test() {
    local id="$1" desc="$2" reason="${3:-}"
    ((SKIP++)) || true
    ((TOTAL++)) || true
    printf "  ${YELLOW}SKIP${NC}  %-12s %s\n" "$id" "$desc"
    if [[ -n "$reason" ]]; then
        printf "        ${YELLOW}→ %s${NC}\n" "$reason"
    fi
}

assert_status() {
    local id="$1" desc="$2" expected="$3"
    if [[ "$HTTP_CODE" == "$expected" ]]; then
        pass_test "$id" "$desc"
    else
        fail_test "$id" "$desc" "Expected HTTP $expected, got $HTTP_CODE"
    fi
}

assert_jq() {
    local id="$1" desc="$2" expr="$3" expected="$4"
    local actual
    actual=$(echo "$BODY" | jq -r "$expr" 2>/dev/null) || actual="JQ_ERROR"
    if [[ "$actual" == "$expected" ]]; then
        pass_test "$id" "$desc"
    else
        fail_test "$id" "$desc" "Expected '$expected', got '$actual'"
    fi
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

printf "\n${BOLD}Wingz Ride API — Deployment Validation${NC}\n"
printf "Target: %s\n" "$ENDPOINT"
printf "Date:   %s\n\n" "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"

for cmd in curl jq; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd is required but not installed." >&2
        exit 2
    fi
done

# Quick connectivity check — anonymous GET must return a real HTTP code.
fetch "$ENDPOINT"
if [[ "$HTTP_CODE" == "000" ]]; then
    echo "ERROR: Cannot reach $ENDPOINT — check URL and network." >&2
    exit 2
fi

# Obtain JWT access tokens for the three seed accounts used in subsequent tests.
ADMIN_TOKEN=$(get_token "$ADMIN_EMAIL" "$ADMIN_PASSWORD")
RIDER_TOKEN=$(get_token "$RIDER_EMAIL" "$RIDER_PASSWORD")
DRIVER_TOKEN=$(get_token "$DRIVER_EMAIL" "$DRIVER_PASSWORD")

if [[ -z "$ADMIN_TOKEN" || -z "$RIDER_TOKEN" || -z "$DRIVER_TOKEN" ]]; then
    echo "ERROR: Failed to obtain one or more JWT tokens from $LOGIN_URL." >&2
    echo "       admin=${ADMIN_TOKEN:+ok}${ADMIN_TOKEN:-missing}" >&2
    echo "       rider=${RIDER_TOKEN:+ok}${RIDER_TOKEN:-missing}" >&2
    echo "       driver=${DRIVER_TOKEN:+ok}${DRIVER_TOKEN:-missing}" >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# 1. Authentication & Authorization
# ---------------------------------------------------------------------------

printf "${CYAN}${BOLD}[1/7] Authentication & Authorization${NC}\n"

fetch "$ENDPOINT" -H "Authorization: Bearer $ADMIN_TOKEN"
assert_status "AUTH-01" "Admin Bearer token returns 200" "200"

fetch "$ENDPOINT"
assert_status "AUTH-02" "No credentials return 401" "401"

fetch "$LOGIN_URL" -X POST -H "Content-Type: application/json" \
    -d "$(jq -n --arg e "$ADMIN_EMAIL" '{email:$e, password:"wrongpassword"}')"
assert_status "AUTH-03" "Login with wrong password returns 401" "401"

fetch "$ENDPOINT" -H "Authorization: Bearer $RIDER_TOKEN"
assert_status "AUTH-04" "Rider (non-admin) Bearer returns 403" "403"

fetch "$ENDPOINT" -H "Authorization: Bearer $DRIVER_TOKEN"
assert_status "AUTH-05" "Driver (non-admin) Bearer returns 403" "403"

fetch "$LOGIN_URL" -X POST -H "Content-Type: application/json" \
    -d '{"email":"nobody@wingz.com","password":"whatever"}'
assert_status "AUTH-06" "Login with non-existent email returns 401" "401"

fetch "$ENDPOINT" -H "Authorization: Basic YWRtaW5Ad2luZ3ouY29tOmFkbWlucGFzczEyMw=="
assert_status "AUTH-07" "Basic Auth header is rejected (Bearer-only)" "401"

# ---------------------------------------------------------------------------
# 2. Response Structure
# ---------------------------------------------------------------------------

printf "\n${CYAN}${BOLD}[2/7] Response Structure${NC}\n"

fetch_auth "$ENDPOINT"

assert_jq "STRUCT-01" "Envelope has count/next/previous/results" \
    '[has("count","next","previous","results")] | all' "true"

assert_jq "STRUCT-02" "Total ride count is 24" \
    '.count' "24"

assert_jq "STRUCT-03" "Ride has all 10 required fields" \
    '.results[0] | [has("id_ride","status","id_rider","id_driver","pickup_latitude","pickup_longitude","dropoff_latitude","dropoff_longitude","pickup_time","todays_ride_events")] | all' "true"

assert_jq "STRUCT-04" "id_rider is nested user object (6 fields)" \
    '.results[0].id_rider | [has("id_user","role","first_name","last_name","email","phone_number")] | all' "true"

assert_jq "STRUCT-05" "id_driver is nested user object (6 fields)" \
    '.results[0].id_driver | [has("id_user","role","first_name","last_name","email","phone_number")] | all' "true"

assert_jq "STRUCT-06" "Password NOT in id_rider" \
    '.results[0].id_rider | has("password")' "false"

assert_jq "STRUCT-07" "Password NOT in id_driver" \
    '.results[0].id_driver | has("password")' "false"

# ---------------------------------------------------------------------------
# 3. Pagination
# ---------------------------------------------------------------------------

printf "\n${CYAN}${BOLD}[3/7] Pagination${NC}\n"

fetch_auth "$ENDPOINT"
assert_jq "PAGE-01" "Default page returns 10 items" \
    '.results | length' "10"

fetch_auth "${ENDPOINT}?page_size=5"
assert_jq "PAGE-02" "page_size=5 returns 5 items" \
    '.results | length' "5"

fetch_auth "${ENDPOINT}?page=2&page_size=5"
PREV=$(echo "$BODY" | jq -r '.previous')
if [[ "$PREV" != "null" && -n "$PREV" ]]; then
    pass_test "PAGE-03" "page=2 has non-null previous"
else
    fail_test "PAGE-03" "page=2 has non-null previous" "previous was null"
fi

fetch_auth "${ENDPOINT}?page_size=5"
NEXT_URL=$(echo "$BODY" | jq -r '.next')
if echo "$NEXT_URL" | grep -q "page=2"; then
    pass_test "PAGE-04" "Page 1 next URL contains page=2"
else
    fail_test "PAGE-04" "Page 1 next URL contains page=2" "next=$NEXT_URL"
fi

fetch_auth "${ENDPOINT}?page=5&page_size=5"
assert_jq "PAGE-05a" "Last page (5) has null next" \
    '.next' "null"
assert_jq "PAGE-05b" "Last page has 4 items (24 mod 5)" \
    '.results | length' "4"

fetch_auth "${ENDPOINT}?page_size=200"
assert_jq "PAGE-06" "page_size>max capped, returns all 24" \
    '.results | length' "24"

# ---------------------------------------------------------------------------
# 4. Filtering
# ---------------------------------------------------------------------------

printf "\n${CYAN}${BOLD}[4/7] Filtering${NC}\n"

fetch_auth "${ENDPOINT}?status=pickup&page_size=100"
assert_jq "FILT-01a" "status=pickup count is 8" '.count' "8"
FILT01_ALL=$(echo "$BODY" | jq '[.results[].status] | all(. == "pickup")')
if [[ "$FILT01_ALL" == "true" ]]; then
    pass_test "FILT-01b" "All results have status=pickup"
else
    fail_test "FILT-01b" "All results have status=pickup" "Some results have wrong status"
fi

fetch_auth "${ENDPOINT}?status=dropoff&page_size=100"
assert_jq "FILT-02" "status=dropoff count is 8" '.count' "8"

fetch_auth "${ENDPOINT}?status=en-route&page_size=100"
assert_jq "FILT-03" "status=en-route count is 8" '.count' "8"

fetch_auth "${ENDPOINT}?rider_email=alice@example.com&page_size=100"
assert_jq "FILT-04a" "rider_email=alice count is 8" '.count' "8"
FILT04_ALL=$(echo "$BODY" | jq '[.results[].id_rider.email] | all(. == "alice@example.com")')
if [[ "$FILT04_ALL" == "true" ]]; then
    pass_test "FILT-04b" "All results have rider_email=alice"
else
    fail_test "FILT-04b" "All results have rider_email=alice" "Some results have wrong rider"
fi

fetch_auth "${ENDPOINT}?status=pickup&rider_email=alice@example.com&page_size=100"
assert_jq "FILT-05" "Combined pickup+alice count is 4" '.count' "4"

fetch_auth "${ENDPOINT}?status=invalid"
assert_status "FILT-06a" "Invalid status returns 200 (not error)" "200"
assert_jq "FILT-06b" "Invalid status returns count=0" '.count' "0"

fetch_auth "${ENDPOINT}?rider_email=nobody@example.com"
assert_status "FILT-07a" "Nonexistent email returns 200" "200"
assert_jq "FILT-07b" "Nonexistent email returns count=0" '.count' "0"

# ---------------------------------------------------------------------------
# 5. Sorting
# ---------------------------------------------------------------------------

printf "\n${CYAN}${BOLD}[5/7] Sorting${NC}\n"

fetch_auth "${ENDPOINT}?sort_by=pickup_time&page_size=100"
SORTED=$(echo "$BODY" | jq '[.results[].pickup_time] | . == sort')
if [[ "$SORTED" == "true" ]]; then
    pass_test "SORT-01" "sort_by=pickup_time is ascending"
else
    fail_test "SORT-01" "sort_by=pickup_time is ascending" "pickup_times not in order"
fi

fetch_auth "${ENDPOINT}?sort_by=distance&latitude=14.5995&longitude=-90.5131&page_size=100"
assert_status "SORT-02" "Distance sort returns 200" "200"

# First result should be zone10 (lat ~14.5995)
FIRST_LAT=$(echo "$BODY" | jq '.results[0].pickup_latitude')
FIRST_LAT_OK=$(echo "$FIRST_LAT" | awk '{print ($1 > 14.598 && $1 < 14.601) ? "true" : "false"}')
if [[ "$FIRST_LAT_OK" == "true" ]]; then
    pass_test "SORT-03" "Distance: first result is zone10 (lat=$FIRST_LAT)"
else
    fail_test "SORT-03" "Distance: first result is zone10" "Got lat=$FIRST_LAT, expected ~14.5995"
fi

# Last result should be antigua (lat ~14.5586)
LAST_LAT=$(echo "$BODY" | jq '.results[-1].pickup_latitude')
LAST_LAT_OK=$(echo "$LAST_LAT" | awk '{print ($1 > 14.557 && $1 < 14.560) ? "true" : "false"}')
if [[ "$LAST_LAT_OK" == "true" ]]; then
    pass_test "SORT-04" "Distance: last result is antigua (lat=$LAST_LAT)"
else
    fail_test "SORT-04" "Distance: last result is antigua" "Got lat=$LAST_LAT, expected ~14.5586"
fi

fetch "${ENDPOINT}?sort_by=distance" -H "Authorization: Bearer $ADMIN_TOKEN"
assert_status "SORT-05" "Distance without lat/lng returns 400" "400"
if echo "$BODY" | jq -r '.error' 2>/dev/null | grep -qi "latitude and longitude are required"; then
    pass_test "SORT-05b" "Error message mentions lat/lng required"
else
    fail_test "SORT-05b" "Error message mentions lat/lng required" "Body: $BODY"
fi

fetch "${ENDPOINT}?sort_by=distance&latitude=abc&longitude=-90.5131" -H "Authorization: Bearer $ADMIN_TOKEN"
assert_status "SORT-06" "Non-numeric latitude returns 400" "400"
if echo "$BODY" | jq -r '.error' 2>/dev/null | grep -qi "valid numbers"; then
    pass_test "SORT-06b" "Error message mentions valid numbers"
else
    fail_test "SORT-06b" "Error message mentions valid numbers" "Body: $BODY"
fi

fetch "${ENDPOINT}?sort_by=distance&latitude=14.5995" -H "Authorization: Bearer $ADMIN_TOKEN"
assert_status "SORT-07" "Lat only (no lng) returns 400" "400"

# ---------------------------------------------------------------------------
# 6. Today's Ride Events
# ---------------------------------------------------------------------------

printf "\n${CYAN}${BOLD}[6/7] Today's Ride Events${NC}\n"

fetch_auth "${ENDPOINT}?page_size=100"

# EVENTS-01: todays_ride_events is an array on every ride
ALL_ARRAYS=$(echo "$BODY" | jq '[.results[].todays_ride_events | type] | all(. == "array")')
if [[ "$ALL_ARRAYS" == "true" ]]; then
    pass_test "EVENTS-01" "todays_ride_events is an array on all rides"
else
    fail_test "EVENTS-01" "todays_ride_events is an array on all rides" "Some are not arrays"
fi

# EVENTS-02: Old rides (pickup_time in 2024-01 through 2024-04-15) should have empty arrays
# These have events from Jan-Apr 2024, well outside the 24h window
OLD_EMPTY=$(echo "$BODY" | jq '[.results[] | select(.pickup_time < "2024-12-01") | .todays_ride_events | length] | all(. == 0)')
if [[ "$OLD_EMPTY" == "true" ]]; then
    pass_test "EVENTS-02" "Old rides have empty todays_ride_events"
else
    fail_test "EVENTS-02" "Old rides have empty todays_ride_events" "Some old rides have events"
fi

# EVENTS-03: Recent rides (pickup_time = now, i.e. 2026-*) may have events if within 24h of seed
RECENT_COUNT=$(echo "$BODY" | jq '[.results[] | select(.pickup_time > "2025-01-01") | .todays_ride_events | length] | add // 0')
if [[ "$RECENT_COUNT" -gt 0 ]]; then
    # Events are still fresh — validate count (2 per ride for 3 rides = 6 total)
    if [[ "$RECENT_COUNT" -ge 4 ]]; then
        pass_test "EVENTS-03" "Recent rides have todays_ride_events ($RECENT_COUNT events)"
    else
        fail_test "EVENTS-03" "Recent rides have todays_ride_events" "Expected >=4, got $RECENT_COUNT"
    fi
else
    skip_test "EVENTS-03" "Recent rides have todays_ride_events" "Events aged out (>24h since seed)"
fi

# EVENTS-04: Event objects have correct 3 fields (only if we have any events)
if [[ "$RECENT_COUNT" -gt 0 ]]; then
    EVT_FIELDS=$(echo "$BODY" | jq '
        [.results[] | select(.pickup_time > "2025-01-01") | .todays_ride_events[] | has("id_ride_event","description","created_at")]
        | all
    ')
    if [[ "$EVT_FIELDS" == "true" ]]; then
        pass_test "EVENTS-04" "Event objects have 3 required fields"
    else
        fail_test "EVENTS-04" "Event objects have 3 required fields" "Missing fields in some events"
    fi
else
    skip_test "EVENTS-04" "Event objects have 3 required fields" "No recent events to inspect"
fi

# ---------------------------------------------------------------------------
# 7. Edge Cases
# ---------------------------------------------------------------------------

printf "\n${CYAN}${BOLD}[7/7] Edge Cases${NC}\n"

fetch "$ENDPOINT" -X POST -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json"
assert_status "EDGE-01" "POST returns 405 Method Not Allowed" "405"

fetch "$ENDPOINT" -X PUT -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json"
assert_status "EDGE-02" "PUT returns 405 Method Not Allowed" "405"

fetch "$ENDPOINT" -X DELETE -H "Authorization: Bearer $ADMIN_TOKEN"
assert_status "EDGE-03" "DELETE returns 405 Method Not Allowed" "405"

fetch "${ENDPOINT}?page=999" -H "Authorization: Bearer $ADMIN_TOKEN"
assert_status "EDGE-04" "Page beyond data returns 404" "404"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

printf "\n${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
printf "${BOLD}Results: ${GREEN}%d passed${NC}  ${RED}%d failed${NC}  ${YELLOW}%d skipped${NC}  (${BOLD}%d total${NC})\n" \
    "$PASS" "$FAIL" "$SKIP" "$TOTAL"
printf "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n\n"

if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi
exit 0
