#!/usr/bin/env bash
# CCC E2E 학생 플로우 테스트
set -uo pipefail

API="${CCC_API:-http://localhost:9100/api}"
KEY="${CCC_API_KEY:-ccc-api-key-2026}"
PASS=0; FAIL=0; TOTAL=0

check() {
    TOTAL=$((TOTAL+1))
    local name="$1" expected="$2" actual="$3"
    if echo "$actual" | grep -qi "$expected" 2>/dev/null; then
        PASS=$((PASS+1)); echo "  [PASS] $name"
    else
        FAIL=$((FAIL+1)); echo "  [FAIL] $name (expect=$expected)"
    fi
}

apicall() {
    curl -s --max-time 15 -H "X-API-Key: $KEY" -H "Content-Type: application/json" "$@" 2>/dev/null || echo "{}"
}

echo "=== CCC E2E Student Flow Test ==="

# 1. Health
echo -e "\n--- Health ---"
check "API health" "ok" "$(apicall "$API/health")"

# 2. Register + Login
echo -e "\n--- Auth ---"
TS=$(date +%s)
REG=$(apicall -X POST "$API/auth/register" -d "{\"student_id\":\"e2e-$TS\",\"name\":\"E2E\",\"password\":\"test1234\"}")
SID=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin).get('user',{}).get('id',''))" 2>/dev/null)
check "Register" "id" "$REG"

LOGIN=$(apicall -X POST "$API/auth/login" -d "{\"student_id\":\"e2e-$TS\",\"password\":\"test1234\"}")
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
check "Login" "token" "$LOGIN"

# 3. Training
echo -e "\n--- Training ---"
COURSES=$(apicall -H "Authorization: Bearer $TOKEN" "$API/training/courses")
check "15 courses" "15" "$(echo "$COURSES" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("total",0))' 2>/dev/null)"

# 4. Labs
echo -e "\n--- Labs ---"
LABS=$(apicall "$API/labs/catalog?course=attack")
check "Lab catalog" "lab_id" "$LABS"

# 5. Lab submit + CCCNet
echo -e "\n--- Lab + Blockchain ---"
apicall -X POST "$API/labs/start" -d "{\"student_id\":\"$SID\",\"lab_id\":\"attack-nonai-week01\"}" > /dev/null
SUBMIT=$(apicall -X POST "$API/labs/submit" -d "{\"student_id\":\"$SID\",\"lab_id\":\"attack-nonai-week01\",\"evidence\":{\"a\":\"1\"}}")
check "Lab submit" "completed" "$SUBMIT"

BLOCKS=$(apicall "$API/cccnet/blocks?student_id=$SID")
check "CCCNet block" "lab_complete" "$BLOCKS"

check "CCCNet stats" "total_points" "$(apicall "$API/cccnet/stats")"

# 6. User stats + Rank
echo -e "\n--- Stats + Rank ---"
check "User stats" "rank" "$(apicall -H "Authorization: Bearer $TOKEN" "$API/user/stats")"
check "Rank check" "current_rank" "$(apicall "$API/rank/check/$SID")"

# 7. Groups (admin)
echo -e "\n--- Admin ---"
ALOGIN=$(apicall -X POST "$API/auth/login" -d '{"student_id":"admin","password":"admin1234"}')
ATOKN=$(echo "$ALOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
check "Groups" "commander" "$(apicall -H "Authorization: Bearer $ATOKN" "$API/groups")"

# 8. Leaderboard
echo -e "\n--- Leaderboard ---"
check "CCCNet leaderboard" "leaderboard" "$(apicall "$API/cccnet/leaderboard")"

# Summary
echo -e "\n==============================="
echo "  E2E: $PASS/$TOTAL passed"
[ $FAIL -eq 0 ] && echo "  ALL PASS" || echo "  $FAIL FAILED"
echo "==============================="
exit $FAIL
