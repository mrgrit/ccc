#!/usr/bin/env bash
# secu VM 의 nftables DNAT(80→10.20.30.80) 동작 진단.
# 사용: scp 후 secu 에서 sudo bash check_secu_dnat.sh
set -u

echo "=== 1. ip_forward ==="
fw=$(cat /proc/sys/net/ipv4/ip_forward)
echo "net.ipv4.ip_forward = $fw"
[ "$fw" != "1" ] && echo "  ✗ ip_forward 비활성. sysctl -w net.ipv4.ip_forward=1 필요"

echo
echo "=== 2. NIC ==="
ip -o link show | grep -v 'lo\|docker\|veth' | awk '{print "  "$2}' | tr -d ':'
EXTERNAL=$(ip -o link show | grep -v 'lo\|docker\|veth' | awk '{print $2}' | tr -d ':' | head -1)
INTERNAL=$(ip -o link show | grep -v 'lo\|docker\|veth' | awk '{print $2}' | tr -d ':' | tail -1)
echo "  EXTERNAL=$EXTERNAL  INTERNAL=$INTERNAL"
[ -z "$EXTERNAL" ] && echo "  ✗ EXTERNAL 빈 값"
[ "$EXTERNAL" = "$INTERNAL" ] && echo "  ✗ NIC 1개만 — 외부/내부 구분 불가"

echo
echo "=== 3. nftables nat 룰 ==="
nft list table ip nat 2>&1 | head -25 || echo "  ✗ ip nat 테이블 없음"

echo
echo "=== 4. DNAT 룰 검증 ==="
nft list ruleset | grep -E "dnat|dport 80" || echo "  ✗ DNAT 룰 없음"

echo
echo "=== 5. 외부 IP ==="
ip -4 addr show "$EXTERNAL" 2>/dev/null | awk '/inet / {print "  "$2}'

echo
echo "=== 6. secu→web 직통 (10.20.30.80:80) ==="
timeout 5 curl -sS -o /dev/null -w "  status=%{http_code} time=%{time_total}s\n" http://10.20.30.80/ || echo "  ✗ web 도달 실패 (서비스/네트워크 확인)"

echo
echo "=== 7. 외부 IP 로 80 self-test (DNAT 경로) ==="
EXT_IP=$(ip -4 addr show "$EXTERNAL" | awk '/inet / {print $2}' | cut -d/ -f1 | head -1)
if [ -n "$EXT_IP" ]; then
    echo "  외부IP=$EXT_IP"
    timeout 5 curl -sS -o /dev/null -w "  status=%{http_code} time=%{time_total}s\n" "http://$EXT_IP/" || echo "  ✗ 외부 IP 80 → DNAT 실패"
fi

echo
echo "=== 8. conntrack — 진행 중 80 세션 ==="
sudo conntrack -L 2>/dev/null | grep ":80" | head -5 || echo "  conntrack 활성 세션 없음 (또는 conntrack 도구 미설치)"

echo
echo "=== 9. 패킷 추적 (DNAT trace) ==="
echo "  10초간 nft trace 켜고 외부에서 :80 접근 → 결과:"
nft add rule inet filter input meta nftrace set 1 2>/dev/null
nft add rule inet filter forward meta nftrace set 1 2>/dev/null
nft add rule ip nat prerouting meta nftrace set 1 2>/dev/null
timeout 10 nft monitor trace 2>&1 | head -30 || true
# 클린업
nft -a list ruleset | grep "nftrace set 1" -B 1 | grep handle | awk '{print $NF}' | while read h; do
    nft delete rule inet filter input handle $h 2>/dev/null
    nft delete rule inet filter forward handle $h 2>/dev/null
    nft delete rule ip nat prerouting handle $h 2>/dev/null
done

echo
echo "=== 10. 권장 fix ==="
echo "  EXTERNAL/INTERNAL 양 NIC 잡힌 경우 추가 룰:"
echo "    nft add rule ip nat postrouting ip saddr != 10.20.30.0/24 oifname \"$INTERNAL\" ip daddr 10.20.30.0/24 masquerade"
