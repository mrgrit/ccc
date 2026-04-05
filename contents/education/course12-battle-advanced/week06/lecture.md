# Week 06: 실시간 방어 — Suricata IPS Inline Mode, fail2ban, 자동차단 스크립트, 허니팟, 실시간 알림

## 학습 목표
- Suricata를 IPS inline 모드로 구성하여 악성 트래픽을 실시간 차단하는 방법을 실습할 수 있다
- fail2ban을 활용하여 SSH/HTTP 브루트포스 공격을 자동 탐지·차단하는 시스템을 구축할 수 있다
- nftables 연동 자동차단 스크립트를 작성하여 로그 기반 실시간 대응 체계를 구현할 수 있다
- Cowrie SSH 허니팟을 배포하여 공격자 행동을 수집하고 분석할 수 있다
- Slack/Webhook 기반 실시간 알림 체계를 구성하여 보안 이벤트에 즉각 대응할 수 있다
- OpsClaw execute-plan을 통해 다중 서버에 방어 체계를 자동 배포할 수 있다

## 전제 조건
- 공방전 기초 과정(course11) 이수 완료
- Week 01-05 학습 완료 (APT 킬체인, 침투, 권한 상승, 측면 이동, 데이터 유출 이해)
- nftables 기본 사용법 (체인, 룰 추가/삭제)
- Suricata IDS 모드 경험 (Week 01-05에서 룰 작성 경험)
- Linux 서비스 관리 (systemctl) 기초
- OpsClaw 플랫폼 기본 사용법 (프로젝트 생성, execute-plan)

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 기지 / Control Plane | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (JuiceShop, Apache) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh, OpenCTI) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: Suricata IPS Inline Mode | 강의/실습 |
| 0:40-1:20 | Part 2: fail2ban SSH/HTTP 자동차단 | 강의/실습 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: 자동차단 스크립트(nftables+로그) | 강의/실습 |
| 2:10-2:50 | Part 4: 허니팟(Cowrie)과 실시간 알림 | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:20 | 종합 시나리오: 다층 실시간 방어 체계 구축 | 실습/토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **IPS** | Intrusion Prevention System | 침입 방지 시스템 (탐지 + 차단) | 경비원이 수상한 사람을 막아서는 것 |
| **IDS** | Intrusion Detection System | 침입 탐지 시스템 (탐지만) | CCTV로 감시만 하는 것 |
| **Inline Mode** | 인라인 모드 | 트래픽 경로에 직접 삽입되어 실시간 차단 | 도로 위의 검문소 |
| **AF_PACKET** | AF_PACKET | Linux 패킷 소켓으로 직접 캡처 | 네트워크 카드에서 직접 읽기 |
| **NFQUEUE** | Netfilter Queue | nftables에서 패킷을 사용자 공간으로 전달 | 검문소에서 짐 검사 의뢰 |
| **fail2ban** | fail2ban | 로그 기반 자동 차단 데몬 | 3번 틀리면 출입 금지 |
| **Jail** | 감옥 | fail2ban의 감시 단위 (서비스별 설정) | 서비스별 경비 초소 |
| **Honeypot** | 허니팟 | 공격자를 유인하는 미끼 시스템 | 파리잡이 끈끈이 |
| **Cowrie** | Cowrie | SSH/Telnet 허니팟 (명령 기록) | 가짜 금고 (열면 알림) |
| **Webhook** | 웹훅 | 이벤트 발생 시 HTTP 호출로 알림 | 초인종 누르면 알림 오는 것 |
| **nftables** | nftables | Linux 커널 방화벽 프레임워크 | 건물 출입 통제 시스템 |
| **Drop** | 차단/폐기 | 패킷을 버리는 동작 | 문전박대 |
| **Reject** | 거부 | 패킷을 버리고 RST/ICMP 응답 | 거절 통보 |

---

# Part 1: Suricata IPS Inline Mode (40분)

## 1.1 IDS vs IPS: 패시브와 인라인의 차이

IDS(Intrusion Detection System)는 트래픽을 복제하여 분석하고 알림만 발생시킨다. IPS(Intrusion Prevention System)는 트래픽 경로에 직접 삽입되어 악성 패킷을 실시간으로 차단한다.

### IDS vs IPS 아키텍처 비교

```
+--------------------------------------------------------------+
|                    IDS 모드 (패시브)                          |
+--------------------------------------------------------------+
|                                                              |
|  [클라이언트] ----> [스위치] ----> [서버]                     |
|                       | (미러링)                              |
|                       ▼                                      |
|                   [Suricata IDS]                              |
|                       |                                      |
|                   알림만 발생 (차단 불가)                      |
|                                                              |
+--------------------------------------------------------------+
|                    IPS 모드 (인라인)                          |
+--------------------------------------------------------------+
|                                                              |
|  [클라이언트] ----> [Suricata IPS] ----> [서버]              |
|                       |                                      |
|                   매칭 시 drop/reject                         |
|                   → 악성 패킷이 서버에 도달하지 않음            |
|                                                              |
+--------------------------------------------------------------+
```

### Suricata 인라인 구동 방식 비교

| 방식 | 구성 | 장점 | 단점 |
|------|------|------|------|
| **AF_PACKET inline** | 2개 인터페이스 브릿지 | 설정 간단, 성능 양호 | 전용 NIC 2개 필요 |
| **NFQUEUE** | nftables → Suricata | NIC 1개로 가능, 유연 | nftables 의존, 오버헤드 |
| **NFTables inline** | nft + Suricata | 세밀한 제어 가능 | 구성 복잡 |
| **XDP** | eBPF 기반 | 최고 성능 | 복잡, 제한적 기능 |

### ATT&CK 방어 매핑

| 방어 기능 | MITRE D3FEND ID | 설명 |
|-----------|-----------------|------|
| 네트워크 트래픽 필터링 | D3-NTF | 인라인 패킷 검사 및 차단 |
| 프로토콜 분석 | D3-PA | HTTP/DNS/TLS 프로토콜 심층 분석 |
| 시그니처 기반 탐지 | D3-SBD | 알려진 공격 패턴 매칭 |
| 이상 행위 탐지 | D3-ABD | 트래픽 임계값 초과 탐지 |

## 1.2 NFQUEUE 기반 Suricata IPS 구성

### 실습 1: Suricata NFQUEUE 인라인 모드 설정

**실습 목적**: nftables의 NFQUEUE를 활용하여 Suricata를 IPS 인라인 모드로 구성하고, 실제 트래픽에서 공격 패킷을 차단하는 과정을 체험한다.

**배우는 것**: NFQUEUE 동작 원리, Suricata IPS 설정 파일 구성, 인라인 모드에서의 룰 액션(drop/reject), 성능 튜닝

```bash
# -- secu 서버에서 실행 --

# 1. 현재 Suricata 모드 확인
echo "[+] 현재 Suricata 상태 확인:"
systemctl status suricata 2>/dev/null | head -5 || echo "  Suricata 서비스 확인 필요"
echo ""
echo "[+] Suricata 설정 파일 위치: /etc/suricata/suricata.yaml"

# 2. NFQUEUE 설정
echo ""
echo "[+] nftables NFQUEUE 설정:"
cat << 'NFT_EOF'
#!/usr/sbin/nft -f
# /etc/nftables.d/suricata-ips.nft

# Suricata IPS를 위한 NFQUEUE 설정
table inet suricata_ips {
    chain input_ips {
        type filter hook input priority -150; policy accept;

        # 이미 확인된 패킷은 통과
        ct state established,related accept

        # HTTP/HTTPS 트래픽을 Suricata로 전달
        tcp dport {80, 443, 8080} queue num 0 bypass
        
        # DNS 트래픽을 Suricata로 전달
        udp dport 53 queue num 0 bypass
        tcp dport 53 queue num 0 bypass

        # SSH 브루트포스 검사
        tcp dport 22 queue num 0 bypass
    }

    chain forward_ips {
        type filter hook forward priority -150; policy accept;

        # 포워딩 트래픽도 Suricata 검사
        queue num 0 bypass
    }
}
NFT_EOF

echo ""
echo "[+] NFQUEUE 옵션 설명:"
echo "  queue num 0   : 큐 번호 0 (Suricata가 리스닝)"
echo "  bypass        : Suricata가 다운되면 패킷 통과 (안전장치)"
echo "  fanout        : 멀티 큐로 부하 분산 (고성능 환경)"

# 3. Suricata IPS 모드 설정 (suricata.yaml 변경)
echo ""
echo "[+] suricata.yaml IPS 설정 변경:"
cat << 'YAML_EOF'
# /etc/suricata/suricata.yaml 수정 사항

# NFQUEUE 모드 활성화
nfq:
  mode: accept    # accept: Suricata가 판정, repeat: 재검사
  fail-open: yes  # Suricata 장애 시 패킷 통과
  queue: 0        # 큐 번호
  queue-count: 4  # 멀티 큐 (CPU 코어 수에 맞게)

# 인라인 모드에서 drop 액션 활성화
stream:
  inline: auto

# 성능 튜닝
detect:
  profile: high
  sgh-mpm-context: auto
YAML_EOF

# 4. Suricata IPS 모드로 실행
echo ""
echo "[+] Suricata IPS 실행 명령:"
echo "  # NFQUEUE 모드 실행"
echo "  suricata -c /etc/suricata/suricata.yaml -q 0"
echo ""
echo "  # 멀티 큐 실행 (4개 큐)"
echo "  suricata -c /etc/suricata/suricata.yaml -q 0 -q 1 -q 2 -q 3"
echo ""
echo "  # systemd 서비스로 실행"
echo "  systemctl start suricata"

# 5. IPS 차단 룰 작성
echo ""
echo "[+] IPS 차단 룰 예시 (drop/reject 사용):"
cat << 'RULES_EOF'
# -- /etc/suricata/rules/local-ips.rules --

# SQL Injection 차단 (drop = 패킷 버림, 응답 없음)
drop http any any -> any any (msg:"IPS BLOCK SQL Injection attempt"; \
  flow:to_server,established; \
  http.uri; content:"UNION"; nocase; content:"SELECT"; nocase; distance:0; \
  classtype:web-application-attack; sid:4001001; rev:1;)

# XSS 공격 차단
drop http any any -> any any (msg:"IPS BLOCK XSS script tag"; \
  flow:to_server,established; \
  http.uri; content:"<script"; nocase; \
  classtype:web-application-attack; sid:4001002; rev:1;)

# SSH 브루트포스 차단 (reject = RST 패킷 전송)
reject ssh any any -> any 22 (msg:"IPS REJECT SSH brute force"; \
  flow:to_server; \
  threshold:type both, track by_src, count 5, seconds 60; \
  classtype:attempted-admin; sid:4001003; rev:1;)

# 포트 스캔 차단
drop tcp any any -> any any (msg:"IPS BLOCK port scan detected"; \
  flags:S; \
  threshold:type both, track by_src, count 20, seconds 10; \
  classtype:attempted-recon; sid:4001004; rev:1;)

# DNS 터널링 차단 (Week 05에서 학습)
drop dns any any -> any 53 (msg:"IPS BLOCK DNS tunnel - long subdomain"; \
  dns.query; content:"."; offset:50; \
  threshold:type both, track by_src, count 5, seconds 60; \
  classtype:policy-violation; sid:4001005; rev:1;)

# C2 비콘 차단 (주기적 HTTPS 요청)
drop tls any any -> any 443 (msg:"IPS BLOCK suspicious C2 beacon"; \
  flow:to_server,established; \
  threshold:type both, track by_src, count 60, seconds 60; \
  classtype:trojan-activity; sid:4001006; rev:1;)
RULES_EOF

# 6. 룰 액션 차이 설명
echo ""
echo "[+] IPS 룰 액션 비교:"
echo "  +----------+------------------------------------------+"
echo "  | 액션     | 동작                                     |"
echo "  +----------┼------------------------------------------+"
echo "  | alert    | 알림만 발생 (IDS 모드와 동일)              |"
echo "  | drop     | 패킷 버림 + 알림 (클라이언트는 타임아웃)   |"
echo "  | reject   | RST/ICMP unreachable 전송 + 알림          |"
echo "  | pass     | 룰 매칭 무시 (화이트리스트)                |"
echo "  | rewrite  | 패킷 내용 수정 후 전달                    |"
echo "  +----------+------------------------------------------+"
```

**명령어 해설**:
- `queue num 0 bypass`: nftables에서 패킷을 NFQUEUE 0번으로 전달한다. bypass 옵션은 Suricata가 다운되었을 때 패킷을 통과시키는 안전장치이다
- `suricata -c /etc/suricata/suricata.yaml -q 0`: Suricata를 NFQUEUE 모드로 실행하며 큐 0번에서 패킷을 수신한다
- `drop`: 매칭된 패킷을 조용히 버린다 (클라이언트는 타임아웃 경험)
- `reject`: 매칭된 패킷을 버리고 TCP RST 또는 ICMP unreachable을 전송한다 (클라이언트에 즉시 거부 통보)

**결과 해석**: NFQUEUE 방식은 기존 네트워크 구성을 변경하지 않고 Suricata를 IPS로 전환할 수 있는 가장 실용적인 방법이다. bypass 옵션으로 Suricata 장애 시에도 서비스 연속성을 보장한다. drop과 reject는 보안(은밀성) vs 사용성(빠른 에러 확인)의 트레이드오프가 있다.

**실전 활용**: 프로덕션 환경에서 IPS를 처음 도입할 때는 alert 모드로 충분히 테스트한 후, 확인된 오탐을 제거하고 단계적으로 drop 모드로 전환한다. 갑자기 모든 룰을 drop으로 변경하면 정상 서비스가 차단될 위험이 있다.

**트러블슈팅**:
- `NFQUEUE: can't set verdict`: Suricata가 root 권한으로 실행되지 않음 → `sudo` 또는 CAP_NET_ADMIN 부여
- 패킷 드롭으로 서비스 장애: `nft delete table inet suricata_ips`로 즉시 IPS 해제
- 성능 저하: 멀티 큐(`-q 0 -q 1 -q 2 -q 3`)로 CPU 부하 분산

### 실습 2: IPS 차단 테스트와 로그 분석

**실습 목적**: Suricata IPS가 실제로 공격 패킷을 차단하는지 테스트하고, 차단 로그를 분석하여 IPS 운영의 실무 노하우를 습득한다.

**배우는 것**: IPS 차단 테스트 방법론, eve.json 로그 분석, 오탐 처리와 룰 튜닝, 차단 통계 모니터링

```bash
# -- opsclaw 서버에서 실행 (공격자 역할) --

# 1. SQL Injection 차단 테스트
echo "[+] SQL Injection 차단 테스트:"
echo "  # 정상 요청 (통과되어야 함)"
echo "  curl -s -o /dev/null -w '%{http_code}' 'http://10.20.30.80/search?q=hello'"
echo ""
echo "  # SQL Injection 요청 (차단되어야 함)"
echo "  curl -s -o /dev/null -w '%{http_code}' --max-time 5 \\"
echo "    'http://10.20.30.80/search?q=1+UNION+SELECT+username,password+FROM+users'"
echo ""
echo "  예상 결과:"
echo "    - drop 룰: 타임아웃 (응답 없음)"
echo "    - reject 룰: Connection refused"

# 2. SSH 브루트포스 차단 테스트
echo ""
echo "[+] SSH 브루트포스 차단 테스트:"
echo "  # 5회 실패 시도 → 차단 트리거"
echo "  for i in \$(seq 1 6); do"
echo "    sshpass -p 'wrongpass' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 test@10.20.30.1 2>&1 | tail -1"
echo "    echo \"시도 \$i 완료\""
echo "  done"

# 3. 포트 스캔 차단 테스트
echo ""
echo "[+] 포트 스캔 차단 테스트:"
echo "  nmap -sS -T4 --top-ports 30 10.20.30.1"
echo "  # IPS가 동작하면 중간에 스캔이 멈추거나 'filtered' 표시"

# 4. IPS 차단 로그 분석 (secu 서버)
echo ""
echo "[+] IPS 차단 로그 분석 명령 (secu 서버의 eve.json):"
echo ""
echo "  # 차단 이벤트만 필터"
echo "  cat /var/log/suricata/eve.json | \\"
echo "    jq 'select(.event_type == \"alert\" and .alert.action == \"blocked\")' | \\"
echo "    jq '{timestamp, src_ip: .src_ip, dest_ip: .dest_ip, alert: .alert.signature, action: .alert.action}'"
echo ""
echo "  # 출발지 IP별 차단 횟수"
echo "  cat /var/log/suricata/eve.json | \\"
echo "    jq -r 'select(.alert.action == \"blocked\") | .src_ip' | \\"
echo "    sort | uniq -c | sort -rn | head -10"
echo ""
echo "  # 룰별 차단 횟수"
echo "  cat /var/log/suricata/eve.json | \\"
echo "    jq -r 'select(.alert.action == \"blocked\") | .alert.signature' | \\"
echo "    sort | uniq -c | sort -rn"

# 5. 오탐 처리
echo ""
echo "[+] 오탐 처리 방법:"
echo "  # 방법 1: pass 룰로 화이트리스트"
echo "  pass http 10.20.30.201 any -> any any (msg:\"Whitelist admin\"; sid:999001; rev:1;)"
echo ""
echo "  # 방법 2: suppress로 특정 IP 제외"
echo "  echo 'suppress gen_id 1, sig_id 4001001, track by_src, ip 10.20.30.201' >> /etc/suricata/threshold.config"
echo ""
echo "  # 방법 3: 룰 비활성화"
echo "  echo '1:4001001' >> /etc/suricata/disable.conf"
echo "  suricata-update"
```

**명령어 해설**:
- `jq 'select(.alert.action == "blocked")'`: eve.json에서 실제 차단된 이벤트만 필터링한다
- `suppress gen_id 1, sig_id 4001001, track by_src, ip 10.20.30.201`: 특정 IP에서 발생하는 특정 룰의 알림을 억제한다
- `pass` 룰은 다른 룰보다 우선 적용되어 화이트리스트 역할을 한다

**결과 해석**: IPS 인라인 모드에서 drop 액션이 적용된 룰에 매칭되면 패킷이 즉시 버려진다. 클라이언트는 타임아웃을 경험하며, 서버는 해당 요청을 전혀 수신하지 않는다. 차단 로그에서 action이 "blocked"로 표시된다.

**실전 활용**: IPS 운영의 핵심은 오탐 관리이다. 새 룰을 배포하기 전에 반드시 alert 모드로 1-2주 관찰 기간을 두고, 오탐을 확인한 후 drop으로 전환한다. 차단 로그를 SIEM에 수집하여 대시보드로 모니터링하면 운영 효율이 높아진다.

**트러블슈팅**:
- 정상 트래픽이 차단됨: 즉시 해당 룰을 alert로 변경하거나 disable → 분석 후 재적용
- eve.json이 비어 있음: Suricata 로그 경로와 eve-log 설정 확인
- 차단이 동작하지 않음: nftables NFQUEUE 룰 확인 → `nft list ruleset | grep queue`

---

# Part 2: fail2ban SSH/HTTP 자동차단 (40분)

## 2.1 fail2ban의 동작 원리

fail2ban은 로그 파일을 모니터링하여 비정상 패턴(인증 실패 등)을 탐지하고, 일정 횟수 초과 시 자동으로 방화벽 룰을 추가하여 해당 IP를 차단하는 데몬이다.

### fail2ban 아키텍처

```
+--------------------------------------------------------------+
|                    fail2ban 동작 흐름                         |
+--------------------------------------------------------------+
|                                                              |
|  [로그 파일]                                                  |
|  /var/log/auth.log -+                                        |
|  /var/log/nginx/*.log-+                                      |
|  /var/log/apache/*.log+                                      |
|                      ▼                                       |
|  +-------------------------+                                 |
|  |  fail2ban-server         |                                |
|  |  +-----------+          |                                |
|  |  | Filter    | 정규식 매칭 (failregex)                    |
|  |  +-----+-----+          |                                |
|  |        ▼                |                                |
|  |  +-----------+          |                                |
|  |  | Counter   | 실패 횟수 추적 (maxretry/findtime)        |
|  |  +-----+-----+          |                                |
|  |        ▼                |                                |
|  |  +-----------+          |                                |
|  |  | Action    | 차단 실행 (bantime)                       |
|  |  +-----------+          |                                |
|  +---------+---------------+                                |
|            ▼                                                |
|  +-------------------+                                       |
|  | nftables/iptables | → IP 차단 룰 자동 추가/제거           |
|  +-------------------+                                       |
|                                                              |
+--------------------------------------------------------------+
```

### fail2ban 핵심 설정

| 설정 항목 | 설명 | 기본값 |
|-----------|------|--------|
| **maxretry** | 차단 전 허용되는 실패 횟수 | 5 |
| **findtime** | 실패 횟수를 세는 시간 창 | 600초 (10분) |
| **bantime** | 차단 지속 시간 | 600초 (10분) |
| **filter** | 로그에서 실패를 식별하는 정규식 | 서비스별 다름 |
| **action** | 차단 시 실행할 동작 | iptables 또는 nftables |

## 2.2 fail2ban SSH/HTTP 보호 구성

### 실습 3: fail2ban SSH Jail 구성과 테스트

**실습 목적**: fail2ban을 설치하고 SSH 서비스에 대한 Jail을 구성하여, 브루트포스 공격을 자동으로 탐지·차단하는 체계를 구축한다.

**배우는 것**: fail2ban 설치/설정, SSH Jail 구성, nftables 연동 action 설정, 차단 상태 모니터링

```bash
# -- web 서버에서 실행 (방어 대상) --

# 1. fail2ban 설치 확인
echo "[+] fail2ban 설치 확인:"
which fail2ban-server 2>/dev/null && echo "  설치됨" || echo "  sudo apt install fail2ban"

# 2. fail2ban SSH Jail 설정
echo ""
echo "[+] fail2ban SSH Jail 설정:"
cat << 'JAIL_EOF'
# /etc/fail2ban/jail.local

[DEFAULT]
# 차단 백엔드: nftables 사용
banaction = nftables-multiport
banaction_allports = nftables-allports

# 기본 차단 시간: 1시간
bantime = 3600

# 실패 횟수 추적 시간: 10분
findtime = 600

# 기본 최대 실패 횟수: 5회
maxretry = 5

# 화이트리스트 (관리 서버)
ignoreip = 127.0.0.1/8 10.20.30.201

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
findtime = 300
bantime = 7200

# 반복 위반자 장기 차단
[sshd-aggressive]
enabled = true
port = ssh
filter = sshd[mode=aggressive]
logpath = /var/log/auth.log
maxretry = 1
findtime = 86400
bantime = 604800
JAIL_EOF

# 3. fail2ban 시작
echo ""
echo "[+] fail2ban 서비스 관리:"
echo "  systemctl enable --now fail2ban"
echo "  systemctl status fail2ban"
echo ""
echo "[+] Jail 상태 확인:"
echo "  fail2ban-client status"
echo "  fail2ban-client status sshd"

# 4. SSH 브루트포스 시뮬레이션 (opsclaw에서 실행)
echo ""
echo "[+] SSH 브루트포스 시뮬레이션 (opsclaw → web):"
echo "  for i in 1 2 3 4; do"
echo "    echo \"시도 \$i\""
echo "    sshpass -p 'wrongpass' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 test@10.20.30.80 2>&1 | tail -1"
echo "  done"
echo "  # 4번째 시도에서 Connection refused → 차단 확인"

# 5. 차단 상태 확인
echo ""
echo "[+] 차단 확인:"
echo "  fail2ban-client status sshd"
echo "  nft list set inet f2b-table addr-set-sshd"
echo "  # 차단 해제: fail2ban-client set sshd unbanip 10.20.30.201"

# 6. 로그 분석
echo ""
echo "[+] fail2ban 로그 분석:"
echo "  grep 'Ban' /var/log/fail2ban.log | tail -20"
echo "  grep 'Ban' /var/log/fail2ban.log | awk '{print \$1}' | sort | uniq -c | sort -rn"
```

**명령어 해설**:
- `banaction = nftables-multiport`: fail2ban이 차단 시 nftables 룰을 사용한다
- `maxretry = 3`: 3회 실패 시 차단이 트리거된다
- `findtime = 300`: 5분(300초) 이내의 실패 횟수를 카운트한다
- `ignoreip = 10.20.30.201`: 관리 서버 IP를 화이트리스트에 추가

**결과 해석**: fail2ban은 `/var/log/auth.log`에서 SSH 인증 실패 로그를 실시간 모니터링하여, 설정된 임계값(3회/5분)을 초과하면 자동으로 nftables에 차단 룰을 추가한다. 차단된 IP는 설정된 시간(2시간) 후 자동 해제된다.

**실전 활용**: SSH 서비스는 인터넷에 노출된 서버의 가장 흔한 공격 대상이다. fail2ban은 봇넷의 자동화 공격을 효과적으로 방어한다. 반복 위반자에 대해서는 점진적으로 차단 시간을 늘리는 설정이 권장된다.

**트러블슈팅**:
- fail2ban이 차단하지 않음: `fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf`로 필터 테스트
- nftables 연동 실패: `banaction = nftables-multiport` 설정 확인
- 자기 자신이 차단됨: `ignoreip`에 자신의 IP 추가

### 실습 4: fail2ban HTTP 보호 (Apache/Nginx)

**실습 목적**: fail2ban을 웹 서버에 적용하여 HTTP 기반 공격(브루트포스 로그인, 디렉토리 탐색, 웹 스캔)을 자동 차단한다.

**배우는 것**: HTTP 서비스용 Jail 구성, 커스텀 필터 작성, 다중 Jail 운영 전략

```bash
# -- web 서버에서 실행 --

# 1. HTTP 관련 Jail 설정
echo "[+] fail2ban HTTP Jail 설정:"
cat << 'HTTP_JAIL'
# /etc/fail2ban/jail.local에 추가

# 디렉토리 탐색 (404 과다)
[apache-scan]
enabled = true
port = http,https
filter = apache-scan
logpath = /var/log/apache2/access.log
maxretry = 30
findtime = 60
bantime = 1800

# 웹 애플리케이션 공격 (SQLi, XSS 등)
[apache-attack]
enabled = true
port = http,https
filter = apache-attack
logpath = /var/log/apache2/access.log
maxretry = 3
findtime = 300
bantime = 7200
HTTP_JAIL

# 2. 커스텀 필터: 디렉토리 스캔 탐지
echo ""
echo "[+] 커스텀 필터: /etc/fail2ban/filter.d/apache-scan.conf"
cat << 'FILTER_SCAN'
[Definition]
# 404/403 응답이 과다한 IP 탐지
failregex = ^<HOST> .* "(GET|POST|HEAD) .* HTTP/.*" (404|403) .*$
ignoreregex = ^<HOST> .* "(GET|POST) .*(\.css|\.js|\.png|\.jpg|\.ico) HTTP/.*"
FILTER_SCAN

# 3. 커스텀 필터: 웹 공격 탐지
echo ""
echo "[+] 커스텀 필터: /etc/fail2ban/filter.d/apache-attack.conf"
cat << 'FILTER_ATTACK'
[Definition]
# SQL Injection, XSS, Path Traversal 패턴 탐지
failregex = ^<HOST> .* "(GET|POST) .*(\bunion\b.*\bselect\b|\b<script\b|\.\.\/|\/etc\/passwd).* HTTP/.*"
ignoreregex =
FILTER_ATTACK

# 4. 필터 테스트
echo ""
echo "[+] 필터 테스트:"
echo "  fail2ban-regex /var/log/apache2/access.log /etc/fail2ban/filter.d/apache-scan.conf"
echo "  fail2ban-regex /var/log/apache2/access.log /etc/fail2ban/filter.d/apache-attack.conf"

# 5. 디렉토리 스캔 시뮬레이션 (opsclaw에서)
echo ""
echo "[+] 디렉토리 스캔 시뮬레이션 (opsclaw → web):"
echo "  for path in admin login config backup database wp-admin phpmyadmin; do"
echo "    curl -s -o /dev/null -w '%{http_code} ' http://10.20.30.80/\$path"
echo "  done"

# 6. 전체 Jail 모니터링
echo ""
echo "[+] 전체 Jail 상태 확인:"
echo "  fail2ban-client status"
echo "  for jail in sshd apache-scan apache-attack; do"
echo "    echo \"--- \$jail ---\""
echo "    fail2ban-client status \$jail 2>/dev/null"
echo "  done"
```

**명령어 해설**:
- `failregex = ^<HOST>`: `<HOST>`는 fail2ban이 자동으로 IP 주소를 추출하는 특수 매크로이다
- `ignoreregex`: 정적 리소스(CSS, JS, 이미지) 요청은 실패로 카운트하지 않는다
- `fail2ban-regex`: 로그 파일에 필터를 적용하여 매칭 결과를 테스트한다

**결과 해석**: HTTP Jail은 웹 서버 로그에서 공격 패턴을 탐지한다. 디렉토리 스캔(404 과다)은 30회/1분, 웹 공격(SQLi/XSS)은 3회/5분으로 임계값을 다르게 설정한다.

**실전 활용**: 웹 서버에 fail2ban을 적용할 때는 정상 크롤러(Googlebot 등)를 ignoreip에 추가해야 한다. WAF(BunkerWeb 등)와 fail2ban을 조합하면 다층 방어가 가능하다.

**트러블슈팅**:
- 필터가 매칭되지 않음: 로그 포맷이 다를 수 있음 → `fail2ban-regex`로 확인
- 정상 사용자 차단: `ignoreregex`에 정상 패턴 추가
- 로그 파일 경로 오류: `logpath`가 실제 로그 위치와 일치하는지 확인

---

# Part 3: 자동차단 스크립트 — nftables + 로그 (40분)

## 3.1 커스텀 자동차단 스크립트의 필요성

fail2ban은 범용적이지만, 특수한 탐지 로직(Suricata 알림 연동, 다중 로그 소스 상관분석 등)이 필요할 때는 커스텀 스크립트가 유용하다.

### 자동차단 아키텍처

```
+--------------------------------------------------------------+
|                 커스텀 자동차단 아키텍처                       |
+--------------------------------------------------------------+
|                                                              |
|  [로그 소스]                                                  |
|  Suricata eve.json ---+                                      |
|  auth.log ------------+                                      |
|  access.log ----------+                                      |
|  Wazuh alerts --------+                                      |
|                       ▼                                      |
|  +----------------------------+                              |
|  |  auto_block.sh             |                              |
|  |  +----------+             |                              |
|  |  | 로그 파싱 | (tail -F + grep/jq)                       |
|  |  +----+-----+             |                              |
|  |       ▼                   |                              |
|  |  +----------+             |                              |
|  |  | 판정 로직 | (임계값, 화이트리스트)                      |
|  |  +----+-----+             |                              |
|  |       ▼                   |                              |
|  |  +----------+             |                              |
|  |  | nft 차단  | → nftables 룰 추가                        |
|  |  +----+-----+             |                              |
|  |       ▼                   |                              |
|  |  +----------+             |                              |
|  |  | 알림 전송 | → Slack/Webhook                           |
|  |  +----------+             |                              |
|  +----------------------------+                              |
|                                                              |
+--------------------------------------------------------------+
```

### 실습 5: Suricata 연동 자동차단 스크립트

**실습 목적**: Suricata의 eve.json 로그를 실시간 모니터링하여 고위험 알림 발생 시 nftables로 자동 차단하는 스크립트를 작성한다.

**배우는 것**: tail -F를 활용한 실시간 로그 모니터링, jq를 이용한 JSON 파싱, nftables 동적 룰 관리, 차단 자동 해제

```bash
# -- secu 서버에서 실행 --

# 1. 자동차단 스크립트
echo "[+] Suricata 연동 자동차단 스크립트:"
cat << 'SCRIPT_EOF'
#!/bin/bash
# /opt/scripts/auto_block.sh
# Suricata eve.json 알림 기반 자동 차단

# -- 설정 --
EVE_LOG="/var/log/suricata/eve.json"
BLOCK_SET="auto_blocked"
WHITELIST="10.20.30.201 10.20.30.1 127.0.0.1"
BLOCK_DURATION=3600  # 1시간 차단
MIN_SEVERITY=2       # severity 2 이상만 차단
LOG_FILE="/var/log/auto_block.log"
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"

# -- nftables 셋 초기화 --
setup_nft() {
    nft list set inet filter "$BLOCK_SET" &>/dev/null || {
        nft add set inet filter "$BLOCK_SET" '{ type ipv4_addr; flags timeout; }'
        nft add rule inet filter input ip saddr @"$BLOCK_SET" drop
        echo "$(date '+%Y-%m-%d %H:%M:%S') [INIT] nftables 차단 셋 생성" >> "$LOG_FILE"
    }
}

# -- 화이트리스트 확인 --
is_whitelisted() {
    local ip=$1
    for wl in $WHITELIST; do
        [[ "$ip" == "$wl" ]] && return 0
    done
    return 1
}

# -- IP 차단 --
block_ip() {
    local ip=$1
    local reason=$2
    local severity=$3
    
    is_whitelisted "$ip" && {
        echo "$(date '+%Y-%m-%d %H:%M:%S') [SKIP] $ip (화이트리스트)" >> "$LOG_FILE"
        return
    }
    
    nft list set inet filter "$BLOCK_SET" 2>/dev/null | grep -q "$ip" && return
    
    nft add element inet filter "$BLOCK_SET" "{ $ip timeout ${BLOCK_DURATION}s }"
    
    local msg="$(date '+%Y-%m-%d %H:%M:%S') [BLOCK] $ip (사유: $reason, 심각도: $severity)"
    echo "$msg" >> "$LOG_FILE"
    echo "$msg"
    
    # Slack 알림
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -s -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"자동차단: $ip | 사유: $reason | 심각도: $severity\"}" &>/dev/null &
    fi
}

# -- 메인 루프 --
main() {
    setup_nft
    echo "$(date '+%Y-%m-%d %H:%M:%S') [START] 자동차단 시작" >> "$LOG_FILE"
    
    tail -F "$EVE_LOG" 2>/dev/null | while read -r line; do
        echo "$line" | jq -e '.event_type == "alert"' &>/dev/null || continue
        
        src_ip=$(echo "$line" | jq -r '.src_ip // empty')
        severity=$(echo "$line" | jq -r '.alert.severity // 3')
        signature=$(echo "$line" | jq -r '.alert.signature // "unknown"')
        
        [[ -z "$src_ip" ]] && continue
        [[ "$severity" -gt "$MIN_SEVERITY" ]] && continue
        
        block_ip "$src_ip" "$signature" "$severity"
    done
}

main "$@"
SCRIPT_EOF

# 2. systemd 서비스 등록
echo ""
echo "[+] systemd 서비스 등록:"
cat << 'SERVICE_EOF'
# /etc/systemd/system/auto-block.service
[Unit]
Description=Suricata Auto Block Service
After=suricata.service

[Service]
ExecStart=/opt/scripts/auto_block.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE_EOF

echo ""
echo "  systemctl daemon-reload"
echo "  systemctl enable --now auto-block"

# 3. 차단 현황 모니터링
echo ""
echo "[+] 차단 현황 확인:"
echo "  nft list set inet filter auto_blocked"
echo "  tail -f /var/log/auto_block.log"
echo "  # 수동 해제: nft delete element inet filter auto_blocked '{ 1.2.3.4 }'"
```

**명령어 해설**:
- `nft add set inet filter auto_blocked '{ type ipv4_addr; flags timeout; }'`: 타임아웃 기능이 있는 IP 셋을 생성한다
- `nft add element inet filter auto_blocked "{ $ip timeout 3600s }"`: IP를 셋에 추가하며 3600초 후 자동 삭제된다
- `tail -F`: 파일이 로테이션(재생성)되어도 계속 추적한다
- `jq -e '.event_type == "alert"'`: alert 이벤트만 필터링한다

**결과 해석**: 이 스크립트는 Suricata의 고위험 알림(severity 1-2)이 발생하면 즉시 해당 IP를 nftables 셋에 추가하여 차단한다. 타임아웃으로 자동 해제되며, 화이트리스트로 관리 서버를 보호한다.

**실전 활용**: 프로덕션 환경에서는 severity 기준 외에도 특정 SID(룰 ID)를 지정하여 정밀한 차단이 필요하다. 반복 차단 IP에 대해 차단 시간을 점진적으로 늘리는 로직이 효과적이다.

**트러블슈팅**:
- jq 파싱 오류: eve.json 형식 확인
- nft 권한 오류: root 권한 또는 CAP_NET_ADMIN 필요
- 과도한 차단: MIN_SEVERITY를 1로 조정

### 실습 6: 상관분석 기반 위협 점수 차단

**실습 목적**: 다중 로그 소스를 동시에 모니터링하여 상관분석 기반의 지능적인 자동차단을 구현한다.

**배우는 것**: 다중 로그 소스 동시 모니터링, 위협 점수(Threat Score) 기반 차단, 점수 감쇠 로직

```bash
# -- secu 서버에서 실행 --

# 1. 위협 점수 기반 차단 로직
echo "[+] 상관분석 위협 점수 차단 핵심 로직:"
cat << 'CORR_SCRIPT'
#!/bin/bash
# /opt/scripts/correlation_block.sh

declare -A THREAT_SCORES  # IP별 위협 점수
BLOCK_THRESHOLD=10        # 차단 임계값

# 이벤트 유형별 점수
score_event() {
    local ip=$1
    local event_type=$2
    local points=0
    
    case "$event_type" in
        "suricata_high")    points=5 ;;
        "suricata_medium")  points=3 ;;
        "ssh_fail")         points=2 ;;
        "http_scan")        points=1 ;;
        "http_attack")      points=4 ;;
        "port_scan")        points=3 ;;
    esac
    
    current=${THREAT_SCORES[$ip]:-0}
    THREAT_SCORES[$ip]=$((current + points))
    
    echo "$(date '+%H:%M:%S') [SCORE] $ip: +$points ($event_type) = ${THREAT_SCORES[$ip]}"
    
    if [[ ${THREAT_SCORES[$ip]} -ge $BLOCK_THRESHOLD ]]; then
        echo "$(date '+%H:%M:%S') [BLOCK] $ip: 점수 ${THREAT_SCORES[$ip]} >= $BLOCK_THRESHOLD"
        nft add element inet filter auto_blocked "{ $ip timeout 7200s }"
        unset THREAT_SCORES[$ip]
    fi
}

# 점수 감쇠 (5분마다 1점 감소)
decay_scores() {
    while true; do
        sleep 300
        for ip in "${!THREAT_SCORES[@]}"; do
            current=${THREAT_SCORES[$ip]}
            if [[ $current -gt 0 ]]; then
                THREAT_SCORES[$ip]=$((current - 1))
                [[ ${THREAT_SCORES[$ip]} -le 0 ]] && unset THREAT_SCORES[$ip]
            fi
        done
    done
}
CORR_SCRIPT

# 2. 상관분석 시나리오
echo ""
echo "[+] 상관분석 시나리오:"
echo "  +----------+--------------+------+------+"
echo "  | 시간     | 이벤트       | 점수 | 누적 |"
echo "  +----------┼--------------┼------┼------+"
echo "  | 10:00:00 | 포트 스캔    | +3   | 3    |"
echo "  | 10:00:30 | SSH 실패 #1  | +2   | 5    |"
echo "  | 10:00:45 | SSH 실패 #2  | +2   | 7    |"
echo "  | 10:01:10 | HTTP SQLi    | +4   | 11   |"
echo "  | 10:01:10 | ★ 차단 ★    |      | >=10 |"
echo "  +----------+--------------+------+------+"
echo ""
echo "  → 개별 이벤트로는 차단되지 않지만, 상관분석으로 복합 공격 탐지"

# 3. 감쇠 메커니즘
echo ""
echo "[+] 점수 감쇠 메커니즘:"
echo "  - 5분마다 모든 IP의 점수가 1점씩 감소"
echo "  - 점수가 0 이하가 되면 추적 목록에서 삭제"
echo "  - 오래된 이벤트가 과도하게 누적되는 것을 방지"
echo "  - 지속적인 공격만 차단 임계값에 도달"
```

**명령어 해설**:
- `declare -A THREAT_SCORES`: Bash 연관 배열로 IP별 위협 점수를 관리한다
- 점수 감쇠(decay): 시간이 지나면 점수가 자동 감소하여 오래된 이벤트의 누적을 방지한다
- 차단 임계값 10점: 단일 이벤트로는 차단되지 않지만 복합 공격 시 차단이 트리거된다

**결과 해석**: 상관분석 기반 차단은 단일 이벤트 기반보다 정밀하다. 포트 스캔 단독으로는 차단되지 않지만, SSH 브루트포스와 웹 공격이 연이어 발생하면 차단된다. APT 킬체인 패턴(정찰 → 침투 → 공격) 탐지에 효과적이다.

**실전 활용**: 상용 SIEM의 상관분석 엔진도 유사한 점수 기반 로직을 사용한다. 환경에 따라 점수와 임계값을 지속적으로 튜닝해야 한다.

**트러블슈팅**:
- Bash 연관 배열: Bash 4.0 이상 필요
- 메모리 누수: decay 루프가 오래된 IP를 정리하는지 확인
- 실시간성: tail -F 지연 시 inotifywait 검토

---

# Part 4: 허니팟(Cowrie)과 실시간 알림 (40분)

## 4.1 허니팟의 개념과 종류

허니팟(Honeypot)은 공격자를 유인하여 공격 기법을 수집하고 분석하는 미끼 시스템이다. 정상 사용자는 접근하지 않으므로, 모든 접속이 공격으로 간주된다.

### 허니팟 분류

| 분류 | 예시 | 상호작용 수준 | 수집 데이터 |
|------|------|-------------|-----------|
| **Low-interaction** | Honeyd, Dionaea | 서비스 시뮬레이션 | IP, 포트, 기본 명령 |
| **Medium-interaction** | Cowrie, Kippo | 가짜 셸 제공 | 명령 기록, 파일 다운로드 |
| **High-interaction** | 실제 VM/컨테이너 | 완전한 OS | 전체 공격 행위 |
| **Research** | HoneyNet | 네트워크 규모 | 트래픽 전체 |

### Cowrie 동작 원리

```
+--------------------------------------------------------------+
|                    Cowrie SSH/Telnet 허니팟                    |
+--------------------------------------------------------------+
|                                                              |
|  공격자가 SSH 22번 포트로 접속                                 |
|       ↓                                                      |
|  (실제 SSH는 2222번으로 이동, 22번을 Cowrie가 점유)            |
|       ↓                                                      |
|  가짜 로그인 프롬프트 제공 (약한 비밀번호 허용)                 |
|       ↓                                                      |
|  가짜 셸 환경에서 명령 실행 기록                               |
|  - 입력한 모든 명령 기록                                      |
|  - wget/curl로 다운로드하는 파일 저장                          |
|  - 세션 전체를 TTY 레코딩으로 재생 가능                        |
|       ↓                                                      |
|  실제 시스템에는 영향 없음 (샌드박스)                           |
|                                                              |
+--------------------------------------------------------------+
```

## 4.2 Cowrie SSH 허니팟 배포

### 실습 7: Cowrie SSH 허니팟 설치와 설정

**실습 목적**: Cowrie SSH 허니팟을 배포하여 공격자의 접속 시도와 명령을 실시간으로 수집하고, 공격 행위를 분석하는 체계를 구축한다.

**배우는 것**: Cowrie 설치/설정, 가짜 파일시스템 구성, 세션 로그 분석, 다운로드된 악성코드 수집

```bash
# -- opsclaw 서버에서 실행 --

# 1. Cowrie Docker 배포
echo "[+] Cowrie Docker 배포:"
cat << 'DOCKER_EOF'
# Docker로 Cowrie 실행
docker run -d \
    --name cowrie \
    -p 2222:2222 \
    -p 2223:2223 \
    -v cowrie-data:/cowrie/var \
    -v cowrie-etc:/cowrie/etc \
    cowrie/cowrie:latest

# 실제 SSH를 다른 포트로 이동
# /etc/ssh/sshd_config: Port 22 → Port 22222
# systemctl restart sshd

# nftables로 22번 포트를 Cowrie(2222)로 리다이렉트
nft add table nat
nft add chain nat prerouting '{ type nat hook prerouting priority -100; }'
nft add rule nat prerouting tcp dport 22 redirect to 2222
DOCKER_EOF

# 2. Cowrie 수동 설치 절차
echo ""
echo "[+] Cowrie 수동 설치 (Python venv):"
cat << 'INSTALL_EOF'
sudo apt install git python3-venv python3-dev libssl-dev libffi-dev
cd /opt && sudo git clone https://github.com/cowrie/cowrie.git
cd cowrie
python3 -m venv cowrie-env
source cowrie-env/bin/activate
pip install -r requirements.txt
cp etc/cowrie.cfg.dist etc/cowrie.cfg
INSTALL_EOF

# 3. Cowrie 핵심 설정
echo ""
echo "[+] Cowrie 핵심 설정 (cowrie.cfg):"
cat << 'CFG_EOF'
[ssh]
listen_endpoints = tcp:2222:interface=0.0.0.0

[output_jsonlog]
enabled = true
logfile = ${honeypot:log_path}/cowrie.json

[output_textlog]
enabled = true
logfile = ${honeypot:log_path}/cowrie.log

[shell]
hostname = web-prod-01
filesystem = ${honeypot:share_path}/fs.pickle

[downloads]
enabled = true
CFG_EOF

# 4. 가짜 사용자 설정
echo ""
echo "[+] 가짜 사용자 설정 (userdb.txt):"
cat << 'USERDB_EOF'
# etc/userdb.txt
# * = 아무 비밀번호 허용, ! = 거부
root:0:*
admin:1000:admin
admin:1000:admin123
admin:1000:password
ubuntu:1001:ubuntu
deploy:1002:deploy123
USERDB_EOF

# 5. Cowrie 실행
echo ""
echo "[+] Cowrie 실행:"
echo "  cd /opt/cowrie && source cowrie-env/bin/activate"
echo "  bin/cowrie start"
echo "  bin/cowrie status"
echo "  tail -f var/log/cowrie/cowrie.log"

# 6. 세션 로그 분석
echo ""
echo "[+] Cowrie 세션 로그 분석:"
echo "  # 로그인 시도"
echo "  cat var/log/cowrie/cowrie.json | jq 'select(.eventid == \"cowrie.login.success\")'"
echo ""
echo "  # 입력된 명령"
echo "  cat var/log/cowrie/cowrie.json | jq 'select(.eventid == \"cowrie.command.input\") | {timestamp, src_ip, input}'"
echo ""
echo "  # 다운로드된 파일"
echo "  cat var/log/cowrie/cowrie.json | jq 'select(.eventid == \"cowrie.session.file_download\") | {url, shasum}'"
echo ""
echo "  # TTY 세션 재생"
echo "  bin/playlog var/lib/cowrie/tty/SESSION_ID.log"

# 7. 공격 패턴 분석
echo ""
echo "[+] 수집된 데이터 분석:"
echo "  # 가장 많이 시도된 사용자명"
echo "  cat var/log/cowrie/cowrie.json | jq -r 'select(.eventid==\"cowrie.login.success\") | .username' | sort | uniq -c | sort -rn | head -10"
echo ""
echo "  # 가장 많이 실행된 명령"
echo "  cat var/log/cowrie/cowrie.json | jq -r 'select(.eventid==\"cowrie.command.input\") | .input' | sort | uniq -c | sort -rn | head -20"
echo ""
echo "  # 출발지 국가별 통계 (geoip)"
echo "  cat var/log/cowrie/cowrie.json | jq -r 'select(.eventid==\"cowrie.login.success\") | .src_ip' | sort -u"
```

**명령어 해설**:
- `docker run -p 2222:2222 cowrie/cowrie`: Cowrie Docker 컨테이너를 실행한다
- `nft add rule nat prerouting tcp dport 22 redirect to 2222`: 22번 포트를 Cowrie로 리다이렉트한다
- `root:0:*`: root 계정에 아무 비밀번호로 접속 허용 (공격자 유인)
- `bin/playlog`: 기록된 TTY 세션을 재생한다

**결과 해석**: Cowrie는 공격자에게 진짜 Linux 셸처럼 보이는 환경을 제공한다. 모든 명령, 다운로드 파일, 네트워크 활동이 기록된다. 이 데이터로 공격 도구, C2 서버, 공격 패턴을 파악할 수 있다.

**실전 활용**: 기업 내부망에 허니팟을 배치하면 측면 이동 시도를 탐지할 수 있다. SIEM과 연동하여 허니팟 접속 시 즉시 사고 대응을 트리거하는 것이 효과적이다.

**트러블슈팅**:
- Cowrie 시작 실패: Python 가상환경 확인
- 포트 충돌: 실제 SSH와 Cowrie가 같은 포트 → sshd 포트 변경
- 공격자가 가짜 셸 감지: Cowrie 커스터마이징 필요

## 4.3 실시간 알림 체계 구축

### 실습 8: Slack/Webhook 기반 실시간 보안 알림

**실습 목적**: 보안 이벤트 발생 시 Slack과 Webhook으로 실시간 알림을 전송하는 통합 체계를 구축한다.

**배우는 것**: Slack Incoming Webhook 설정, 이벤트별 알림 스크립트, 알림 피로도 관리

```bash
# -- opsclaw 서버에서 실행 --

# 1. 보안 알림 통합 스크립트
echo "[+] 보안 알림 통합 스크립트:"
cat << 'ALERT_SCRIPT'
#!/bin/bash
# /opt/scripts/security_alert.sh

SLACK_WEBHOOK="${SLACK_WEBHOOK_URL}"
ALERT_LOG="/var/log/security_alerts.log"

send_alert() {
    local severity=$1  # critical, high, medium, low
    local source=$2    # suricata, fail2ban, cowrie, wazuh
    local title=$3
    local detail=$4
    local ip=$5
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 로그 기록
    echo "$timestamp [$severity] [$source] $title | $ip | $detail" >> "$ALERT_LOG"
    
    # Slack 알림
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        local payload=$(cat << EOF
{
    "blocks": [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "[$severity] $title"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": "*Source:*\n$source"},
                {"type": "mrkdwn", "text": "*IP:*\n$ip"},
                {"type": "mrkdwn", "text": "*Time:*\n$timestamp"},
                {"type": "mrkdwn", "text": "*Detail:*\n$detail"}
            ]
        }
    ]
}
EOF
)
        curl -s -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "$payload" &>/dev/null
    fi
}
ALERT_SCRIPT

# 2. fail2ban 알림 연동
echo ""
echo "[+] fail2ban Slack 알림 Action:"
cat << 'F2B_ACTION'
# /etc/fail2ban/action.d/slack-notify.conf
[Definition]
actionban = /opt/scripts/security_alert.sh medium fail2ban "IP 차단: <name>" "<failures>회 실패" "<ip>"
actionunban = /opt/scripts/security_alert.sh low fail2ban "IP 해제: <name>" "차단시간 만료" "<ip>"
F2B_ACTION

# 3. Cowrie 알림 연동
echo ""
echo "[+] Cowrie 알림 모니터링:"
cat << 'COWRIE_ALERT'
# Cowrie JSON 로그 → 알림
tail -F /opt/cowrie/var/log/cowrie/cowrie.json | while read -r line; do
    eventid=$(echo "$line" | jq -r '.eventid // empty')
    src_ip=$(echo "$line" | jq -r '.src_ip // empty')
    
    case "$eventid" in
        "cowrie.login.success")
            username=$(echo "$line" | jq -r '.username')
            /opt/scripts/security_alert.sh "critical" "cowrie" \
                "허니팟 SSH 로그인" "user=$username" "$src_ip"
            ;;
        "cowrie.command.input")
            input=$(echo "$line" | jq -r '.input')
            /opt/scripts/security_alert.sh "high" "cowrie" \
                "허니팟 명령 실행" "$input" "$src_ip"
            ;;
        "cowrie.session.file_download")
            url=$(echo "$line" | jq -r '.url')
            /opt/scripts/security_alert.sh "critical" "cowrie" \
                "허니팟 파일 다운로드" "$url" "$src_ip"
            ;;
    esac
done
COWRIE_ALERT

# 4. 알림 피로도 관리
echo ""
echo "[+] 알림 피로도 관리 전략:"
echo "  1. 집계: 동일 IP 알림을 5분 단위로 모아 전송"
echo "  2. 채널 분리: #alerts-critical (high+), #alerts-all (모두)"
echo "  3. 업무시간: 09-18시 medium 이상, 야간 low 이상"
echo "  4. 자동 요약: 매시간 차단 IP 수, 알림 통계 보고"

# 5. OpsClaw 방어 상태 통합 점검
echo ""
echo "[+] OpsClaw 다층 방어 상태 점검:"
cat << 'CHECK_EOF'
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"suricata -T 2>&1 | tail -1", "risk_level":"low", "subagent_url":"http://10.20.30.1:8002"},
      {"order":2, "instruction_prompt":"fail2ban-client status | head -5", "risk_level":"low", "subagent_url":"http://10.20.30.80:8002"},
      {"order":3, "instruction_prompt":"nft list set inet filter auto_blocked 2>/dev/null | wc -l", "risk_level":"low", "subagent_url":"http://10.20.30.1:8002"}
    ]
  }'
CHECK_EOF
```

**명령어 해설**:
- Slack Block Kit: 구조화된 메시지 형식으로 header, section, fields를 포함한다
- `actionban`: fail2ban에서 IP 차단 시 실행되는 액션으로 알림 스크립트를 호출한다
- `tail -F`: Cowrie 로그를 실시간 모니터링하여 이벤트별 알림을 전송한다

**결과 해석**: 실시간 알림 체계는 보안 이벤트 발생 즉시 SOC에 통보한다. 알림 과다(alert fatigue)를 방지하기 위해 집계, 필터링, 채널 분리 전략이 필수적이다.

**실전 활용**: critical 알림은 PagerDuty/OpsGenie와 연동하여 전화/문자로 통보한다. 허니팟 접속은 항상 critical이다.

**트러블슈팅**:
- Slack Webhook 403: URL 비활성화 → Slack 설정에서 재활성화
- 알림 지연: curl을 백그라운드(&)로 실행
- JSON 포맷 오류: `echo "$payload" | jq .`로 검증

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] Suricata IDS와 IPS의 차이(패시브 vs 인라인)를 설명할 수 있는가?
- [ ] NFQUEUE 기반 Suricata IPS 설정 방법을 이해하는가?
- [ ] drop과 reject 액션의 차이를 설명할 수 있는가?
- [ ] fail2ban의 동작 원리(로그 감시 → 카운터 → 차단)를 설명할 수 있는가?
- [ ] fail2ban SSH/HTTP Jail을 구성하고 테스트할 수 있는가?
- [ ] nftables 연동 자동차단 스크립트의 핵심 로직을 이해하는가?
- [ ] 상관분석 기반 위협 점수 차단의 장점을 설명할 수 있는가?
- [ ] Cowrie SSH 허니팟을 배포하고 로그를 분석할 수 있는가?
- [ ] Slack/Webhook 실시간 알림을 구성할 수 있는가?
- [ ] 알림 피로도 관리 전략 3가지를 나열할 수 있는가?
- [ ] OpsClaw로 다층 방어 체계를 통합 배포할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** Suricata IPS에서 패킷을 버리면서 RST를 보내지 않는 액션은?
- (a) alert  (b) **drop**  (c) reject  (d) pass

**Q2.** NFQUEUE에서 bypass 옵션의 역할은?
- (a) 패킷 암호화  (b) 로그 비활성화  (c) **Suricata 장애 시 패킷 통과**  (d) 성능 향상

**Q3.** fail2ban에서 maxretry=3, findtime=300의 의미는?
- (a) 3분 내 300회  (b) **300초 내 3회 실패 시 차단**  (c) 3시간 차단  (d) 300개 IP 차단

**Q4.** fail2ban이 nftables와 연동하려면 어떤 설정이 필요한가?
- (a) iptables  (b) **banaction = nftables-multiport**  (c) firewalld  (d) ufw

**Q5.** nftables에서 타임아웃이 있는 IP 셋을 만드는 옵션은?
- (a) type timeout  (b) **flags timeout**  (c) timeout yes  (d) auto-expire

**Q6.** Cowrie 허니팟의 주된 목적은?
- (a) 서비스 제공  (b) **공격자 행동 수집 및 분석**  (c) 네트워크 가속  (d) 백업

**Q7.** 상관분석 차단에서 점수 감쇠(decay)의 목적은?
- (a) 성능 향상  (b) **오래된 이벤트의 과도한 누적 방지**  (c) 로그 삭제  (d) 알림 전송

**Q8.** 알림 피로도(Alert Fatigue)를 줄이는 방법이 아닌 것은?
- (a) 집계 알림  (b) 심각도 필터링  (c) **모든 이벤트 즉시 알림**  (d) 자동 요약 보고서

**Q9.** Cowrie에서 공격자 세션을 재생하는 명령은?
- (a) replay  (b) **playlog**  (c) showlog  (d) catlog

**Q10.** IPS를 처음 도입할 때 권장하는 절차는?
- (a) 즉시 drop 모드  (b) reject 모드  (c) **alert 모드로 테스트 후 단계적 drop 전환**  (d) 모든 트래픽 차단

**정답:** Q1:b, Q2:c, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:c, Q9:b, Q10:c

---

## 과제

### 과제 1: 다층 방어 체계 구축 (필수)
본 강의에서 다룬 4가지 방어 기술을 조합하여:
- Suricata IPS 룰 5개 (SQLi, XSS, 포트스캔, DNS 터널, C2 비콘) 작성
- fail2ban SSH + HTTP Jail 2개 구성
- 자동차단 스크립트 작성 (Suricata 연동)
- 모든 컴포넌트의 연동 테스트 결과를 제출하라

### 과제 2: 상관분석 룰 설계 (필수)
3가지 이상의 복합 공격 시나리오에 대해:
- 상관분석 룰(이벤트 유형별 점수, 임계값) 설계
- 시나리오별 탐지 시퀀스 다이어그램 작성
- 오탐/미탐 분석과 튜닝 방안을 제시하라

### 과제 3: 허니팟 네트워크 설계 (선택)
가상의 기업 네트워크(DMZ, 내부망, 관리망)에:
- 허니팟 배치 위치와 유형을 설계하라
- 허니팟 탐지 데이터를 SIEM과 연동하는 방안을 제시하라
- 공격자가 허니팟을 식별하는 방법과 대응책을 논하라

---

## 다음 주 예고

**Week 07: 포렌식 기반 방어 — Volatility3 메모리 분석, 디스크 분석, 타임라인 구성, 증거 보존, 보고서 작성**
- Volatility3를 사용한 메모리 덤프 분석 (프로세스, 네트워크, 악성코드)
- dd/strings를 활용한 디스크 포렌식 분석
- log2timeline으로 사고 타임라인 구성
- 디지털 증거 보존과 Chain of Custody
