# Week 06: 위협 헌팅 심화

## 학습 목표
- 가설 기반(Hypothesis-driven) 위협 헌팅 방법론을 이해하고 적용할 수 있다
- ATT&CK 매트릭스를 기반으로 헌팅 캠페인을 설계할 수 있다
- 베이스라인 이탈(Baseline Deviation) 분석으로 비정상 행위를 탐지할 수 있다
- Wazuh 로그와 시스템 데이터를 활용하여 실제 헌팅을 수행할 수 있다
- 헌팅 결과를 문서화하고 탐지 룰로 전환할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| bastion | 10.20.30.201 | Control Plane (Bastion) | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh Dashboard:443, OpenCTI:8080) | `ssh ccc@10.20.30.100` |

**Bastion API:** `http://localhost:9100` / Key: `ccc-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:50 | 위협 헌팅 이론 + 방법론 (Part 1) | 강의 |
| 0:50-1:30 | ATT&CK 매핑 + 베이스라인 (Part 2) | 강의/토론 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | 헌팅 실습 - 프로세스/네트워크 (Part 3) | 실습 |
| 2:30-3:10 | 헌팅 결과 문서화 + 룰 전환 (Part 4) | 실습 |
| 3:10-3:20 | 정리 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **위협 헌팅** | Threat Hunting | 탐지 룰에 걸리지 않는 위협을 능동적으로 찾는 활동 | 잠복 수사 |
| **가설** | Hypothesis | 헌팅의 출발점이 되는 위협 시나리오 가정 | "내부에 스파이가 있다" |
| **베이스라인** | Baseline | 정상 상태의 기준선 | 평소 체온 36.5도 |
| **이탈** | Deviation | 베이스라인에서 벗어난 비정상 | 체온이 39도로 올라감 |
| **피벗** | Pivot | 발견한 단서를 기반으로 추가 조사하는 것 | 용의자 A → 연락처 → 공범 B |
| **IOA** | Indicator of Attack | 공격 행위 지표 (TTP 기반) | 범행 수법 |
| **IOC** | Indicator of Compromise | 침해 지표 (결과물) | 범행 흔적 |
| **헌팅 매트릭스** | Hunting Matrix | ATT&CK 기법별 헌팅 쿼리 매핑 | 수사 시나리오 목록 |
| **living off the land** | LOTL | 시스템 기본 도구를 악용하는 공격 기법 | 현지 조달 작전 |

---

# Part 1: 위협 헌팅 이론 + 방법론 (50분)

## 1.1 위협 헌팅이란?

위협 헌팅은 **기존 탐지 시스템(SIEM, IDS)이 놓친 위협을 능동적으로 찾아내는** 고급 보안 활동이다. 경보가 울리기를 기다리는 것이 아니라, 분석가가 주도적으로 위협을 탐색한다.

### 반응적 vs 능동적 보안

```
[반응적 보안 (Reactive)]
  경보 발생 → 분석 → 대응
  → 경보가 없으면 아무것도 안 함
  → 탐지 룰에 없는 공격은 놓침

[능동적 보안 (Proactive)]
  가설 수립 → 데이터 수집 → 분석 → 발견 → 대응
  → 경보 없이도 위협을 찾음
  → 새로운 공격 기법도 발견 가능
```

### 위협 헌팅이 필요한 이유

```
현실: 평균 체류 시간(Dwell Time) = 21일

공격자 침투         탐지          대응
    |__________________|___________|
    |    21일 (발견 안 됨)  |
    |                      |
    |  데이터 수집, 측면 이동, 권한 상승  |
    |  → 이 기간에 헌팅으로 찾아야 함    |
```

## 1.2 헌팅 방법론

### SQRRL 프레임워크 (TaHiTI)

```
Step 1: 가설 생성 (Hypothesis)
  → "공격자가 PowerShell/bash를 이용해 데이터를 유출하고 있을 수 있다"
  → 근거: TI 보고서, ATT&CK, 과거 사고

Step 2: 도구/기법 선택 (Tooling)
  → Wazuh 로그 쿼리, 프로세스 분석, 네트워크 플로우

Step 3: 데이터 수집 (Collection)
  → 관련 로그, 프로세스 목록, 네트워크 연결

Step 4: 분석 (Analysis)
  → 베이스라인 대비 이상 패턴 식별
  → 상관관계 분석, 타임라인 구성

Step 5: 결과 (Findings)
  → 위협 발견 → 인시던트 대응
  → 위협 미발견 → 새 가설 수립
  → 탐지 룰 개선

Step 6: 문서화 (Documentation)
  → 헌팅 보고서 작성
  → 새로운 탐지 룰/플레이북 생성
```

### 가설 유형

```
[인텔리전스 기반 가설]
  "최근 TI 보고서에 따르면 우리 산업에 Lazarus 그룹이
   공급망 공격을 하고 있다. 우리 환경에도 침투했을 수 있다."

[상황 인식 기반 가설]
  "최근 퇴사자가 있었다. 퇴사 전 데이터를 유출했을 수 있다."

[ATT&CK 기반 가설]
  "T1053.003(Cron) 기법으로 지속성을 확보한 악성코드가
   우리 Linux 서버에 있을 수 있다."

[이상 징후 기반 가설]
  "평소보다 야간 SSH 접속이 50% 증가했다.
   비인가 접근이 있을 수 있다."
```

## 1.3 헌팅 성숙도 모델 (HMM)

```
HMM Level 0: Initial (초기)
  → 자동화 경보에만 의존
  → 헌팅 활동 없음

HMM Level 1: Minimal (최소)
  → IOC 기반 검색 수행
  → 외부에서 받은 IOC로만 검색

HMM Level 2: Procedural (절차적)
  → 정기적 헌팅 절차 존재
  → ATT&CK 기반 체크리스트 활용

HMM Level 3: Innovative (혁신적)
  → 가설 기반 자체 헌팅
  → 데이터 분석 역량 보유
  → 새로운 TTP 발견 가능

HMM Level 4: Leading (선도)
  → 자동화된 헌팅 파이프라인
  → ML/AI 기반 이상 탐지
  → 업계 TI 기여
```

---

# Part 2: ATT&CK 매핑 + 베이스라인 (40분)

## 2.1 ATT&CK 기반 헌팅 매트릭스

```
[Linux 환경 우선순위 높은 기법]

Tactic              Technique           헌팅 포인트
--------------------------------------------------------------------
Initial Access      T1190 Exploit       웹 로그 이상 요청
                    T1566 Phishing      메일 첨부파일 실행

Execution           T1059.004 Unix Sh   비정상 셸 실행
                    T1053.003 Cron      신규/수정된 cron 작업

Persistence         T1098 Account       새 계정 생성
                    T1136 Create Acct   sudoers 수정
                    T1543.002 Systemd   새 서비스 등록

Priv Escalation     T1548.003 Sudo      비정상 sudo 사용
                    T1068 Exploitation  커널 익스플로잇

Defense Evasion     T1070.004 File Del  로그 파일 삭제
                    T1036 Masquerading  정상 프로세스 위장

Credential Access   T1110 Brute Force   반복 인증 실패
                    T1003.008 /etc/shd  shadow 파일 접근

Discovery           T1082 System Info   whoami, uname 등
                    T1049 Network Conn  netstat, ss 실행

Lateral Movement    T1021.004 SSH       비정상 SSH 접속
                    T1570 Tool Transfer scp, wget 전송

Collection          T1005 Local Data    민감 파일 접근
                    T1560 Archive       tar, zip 압축

Exfiltration        T1048 Alt Protocol  nc, curl 아웃바운드
                    T1041 C2 Channel    C2 서버 통신

C2                  T1071.001 Web       비정상 HTTP 요청
                    T1095 Non-App       비표준 포트 통신
```

## 2.2 베이스라인 구축

```bash
# 정상 베이스라인 수집 스크립트
cat << 'SCRIPT' > /tmp/baseline_collect.sh
#!/bin/bash
echo "============================================"
echo "  정상 베이스라인 수집"
echo "  서버: $(hostname) / $(date)"
echo "============================================"

echo ""
echo "=== 1. 프로세스 베이스라인 ==="
ps aux --sort=-%mem | head -20

echo ""
echo "=== 2. 네트워크 연결 베이스라인 ==="
ss -tlnp 2>/dev/null | head -20

echo ""
echo "=== 3. 크론 작업 베이스라인 ==="
for user in root $(cut -d: -f1 /etc/passwd | head -10); do
    crontab -l -u "$user" 2>/dev/null | grep -v "^#" | grep -v "^$"
done

echo ""
echo "=== 4. 사용자 계정 베이스라인 ==="
awk -F: '$3 >= 1000 {print $1, $3, $7}' /etc/passwd

echo ""
echo "=== 5. SUID 파일 베이스라인 ==="
find / -perm -4000 -type f 2>/dev/null | sort

echo ""
echo "=== 6. /tmp 디렉토리 베이스라인 ==="
ls -la /tmp/ 2>/dev/null | head -20

echo ""
echo "=== 7. systemd 서비스 베이스라인 ==="
systemctl list-units --type=service --state=running 2>/dev/null | head -20

echo ""
echo "=== 8. SSH 설정 베이스라인 ==="
grep -v "^#" /etc/ssh/sshd_config 2>/dev/null | grep -v "^$" | head -15
SCRIPT

echo "=== bastion 서버 베이스라인 ==="
bash /tmp/baseline_collect.sh

echo ""
echo "=== web 서버 베이스라인 ==="
ssh ccc@10.20.30.80 'bash -s' < /tmp/baseline_collect.sh 2>/dev/null | head -50
```

> **실습 목적**: 정상 상태의 베이스라인을 수집하여, 향후 헌팅 시 이탈 여부를 판단하는 기준으로 사용한다.
>
> **실전 활용**: 베이스라인은 주기적으로(주 1회) 갱신하고 버전 관리한다. 변경 사항이 있으면 정상 변경인지 위협인지 확인한다.

---

# Part 3: 헌팅 실습 (50분)

## 3.1 헌팅 #1: 비정상 프로세스 탐지

> **가설**: "공격자가 정상 프로세스명으로 위장한 악성 프로세스를 실행하고 있을 수 있다 (T1036 Masquerading)"
>
> **배우는 것**: 프로세스 트리 분석, 부모-자식 관계 확인, 비정상 경로 탐지

```bash
# 각 서버의 프로세스 분석
cat << 'SCRIPT' > /tmp/hunt_process.sh
#!/bin/bash
echo "============================================"
echo "  헌팅 #1: 비정상 프로세스 탐지"
echo "  서버: $(hostname) / $(date)"
echo "============================================"

echo ""
echo "--- 1. /tmp, /dev/shm 에서 실행 중인 프로세스 ---"
ls -la /proc/*/exe 2>/dev/null | grep -E "/tmp/|/dev/shm/" || echo "(없음)"

echo ""
echo "--- 2. 삭제된 바이너리로 실행 중인 프로세스 ---"
ls -la /proc/*/exe 2>/dev/null | grep "(deleted)" || echo "(없음)"

echo ""
echo "--- 3. 비정상 부모 프로세스 (웹서버에서 셸 생성) ---"
ps -eo pid,ppid,user,comm --forest 2>/dev/null | \
  grep -B1 -E "bash|sh|python|perl|nc|ncat" | \
  grep -E "apache|nginx|www|node|java" || echo "(없음)"

echo ""
echo "--- 4. root 권한으로 실행 중인 비표준 프로세스 ---"
KNOWN_ROOT="systemd|sshd|cron|rsyslog|wazuh|suricata|nft|docker|postgres|containerd|snapd"
ps -eo pid,user,comm 2>/dev/null | awk '$2=="root"' | \
  grep -vE "$KNOWN_ROOT" | head -15

echo ""
echo "--- 5. 네트워크 리스닝 중인 비표준 포트 ---"
KNOWN_PORTS="22|80|443|3000|5432|8000|8001|8002|9400|11434|55000"
ss -tlnp 2>/dev/null | grep -vE "$KNOWN_PORTS" | grep -v "State" || echo "(없음)"

echo ""
echo "--- 6. 최근 1시간 내 생성된 실행 파일 ---"
find /tmp /var/tmp /dev/shm /home -type f -executable -mmin -60 2>/dev/null || echo "(없음)"

echo ""
echo "--- 7. 환경변수에 의심스러운 값 ---"
env 2>/dev/null | grep -iE "proxy|LD_PRELOAD|LD_LIBRARY" || echo "(없음)"
SCRIPT

echo "=== bastion 서버 프로세스 헌팅 ==="
bash /tmp/hunt_process.sh

echo ""
echo "=== secu 서버 프로세스 헌팅 ==="
ssh ccc@10.20.30.1 'bash -s' < /tmp/hunt_process.sh 2>/dev/null

echo ""
echo "=== web 서버 프로세스 헌팅 ==="
ssh ccc@10.20.30.80 'bash -s' < /tmp/hunt_process.sh 2>/dev/null
```

> **결과 해석**:
> - /tmp이나 /dev/shm에서 실행 중인 프로세스가 있다면 악성코드 의심
> - "(deleted)" 바이너리는 실행 후 자신을 삭제한 것으로 고도 위협 의심
> - 웹서버 프로세스가 셸을 생성했다면 웹셸 실행 가능성
>
> **트러블슈팅**:
> - "Permission denied" → sudo 필요 (일부 /proc 정보)
> - 정상 프로세스도 표시됨 → 베이스라인과 비교하여 판단

## 3.2 헌팅 #2: 지속성 메커니즘 점검

```bash
cat << 'SCRIPT' > /tmp/hunt_persistence.sh
#!/bin/bash
echo "============================================"
echo "  헌팅 #2: 지속성 메커니즘 점검"
echo "  서버: $(hostname) / $(date)"
echo "============================================"

echo ""
echo "--- 1. 최근 수정된 cron 작업 (7일 이내) ---"
find /etc/cron* /var/spool/cron -type f -mtime -7 2>/dev/null -exec ls -la {} \;
echo ""
for user in root $(awk -F: '$3>=1000{print $1}' /etc/passwd); do
    jobs=$(crontab -l -u "$user" 2>/dev/null | grep -v "^#" | grep -v "^$")
    if [ -n "$jobs" ]; then
        echo "  [$user] crontab:"
        echo "$jobs" | while read line; do echo "    $line"; done
    fi
done

echo ""
echo "--- 2. 최근 생성/수정된 systemd 서비스 (7일) ---"
find /etc/systemd/system/ /usr/lib/systemd/system/ \
  -name "*.service" -mtime -7 2>/dev/null -exec ls -la {} \;

echo ""
echo "--- 3. SSH authorized_keys 변경 점검 ---"
find /home/ /root/ -name "authorized_keys" 2>/dev/null -exec ls -la {} \;
find /home/ /root/ -name "authorized_keys" -mtime -7 2>/dev/null -exec echo "  최근 변경: {}" \;

echo ""
echo "--- 4. sudoers 변경 점검 ---"
ls -la /etc/sudoers /etc/sudoers.d/* 2>/dev/null
find /etc/sudoers.d/ -mtime -7 2>/dev/null -exec echo "  최근 변경: {}" \;

echo ""
echo "--- 5. 최근 생성된 사용자 계정 ---"
awk -F: '$3>=1000{print $1, $3, $5, $6, $7}' /etc/passwd
echo ""
echo "  /etc/passwd 최종 수정: $(stat -c %y /etc/passwd 2>/dev/null)"

echo ""
echo "--- 6. .bashrc / .profile 변조 점검 ---"
for dir in /root /home/*; do
    for rc in .bashrc .profile .bash_profile; do
        if [ -f "$dir/$rc" ]; then
            suspicious=$(grep -n "curl\|wget\|nc \|python\|base64\|eval" "$dir/$rc" 2>/dev/null)
            if [ -n "$suspicious" ]; then
                echo "  [경고] $dir/$rc 에 의심스러운 내용:"
                echo "$suspicious" | head -3
            fi
        fi
    done
done

echo ""
echo "--- 7. LD_PRELOAD 하이재킹 점검 ---"
cat /etc/ld.so.preload 2>/dev/null || echo "(ld.so.preload 없음 - 정상)"
echo "  /etc/ld.so.conf.d/ 내용:"
ls /etc/ld.so.conf.d/ 2>/dev/null
SCRIPT

echo "=== 전체 서버 지속성 헌팅 ==="
for server in "ccc@10.20.30.201" "ccc@10.20.30.1" "ccc@10.20.30.80" "ccc@10.20.30.100"; do
    user=$(echo $server | cut -d@ -f1)
    ip=$(echo $server | cut -d@ -f2)
    echo ""
    echo "========== $user ($ip) =========="
    if [ "$ip" = "10.20.30.201" ]; then
        bash /tmp/hunt_persistence.sh
    else
        sshpass -p1 ssh -o ConnectTimeout=5 "$server" 'bash -s' < /tmp/hunt_persistence.sh 2>/dev/null
    fi
done
```

> **결과 해석**: 최근 7일 내 변경된 cron, systemd 서비스, authorized_keys, sudoers가 있다면 정상 변경인지 확인해야 한다. .bashrc에 curl/wget이 있으면 백도어 가능성이 있다.

## 3.3 헌팅 #3: 네트워크 이상 탐지

```bash
cat << 'SCRIPT' > /tmp/hunt_network.sh
#!/bin/bash
echo "============================================"
echo "  헌팅 #3: 네트워크 이상 탐지"
echo "  서버: $(hostname) / $(date)"
echo "============================================"

echo ""
echo "--- 1. 외부로의 아웃바운드 연결 ---"
ss -tnp 2>/dev/null | grep ESTAB | \
  awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | \
  while read count ip; do
    # 내부 IP 필터링
    if ! echo "$ip" | grep -qE "^10\.|^172\.(1[6-9]|2[0-9]|3[01])\.|^192\.168\.|^127\."; then
        echo "  외부 IP $ip: $count 연결"
    fi
  done

echo ""
echo "--- 2. 비표준 포트 아웃바운드 연결 ---"
STANDARD="80|443|53|22|25|123|8080|8443"
ss -tnp 2>/dev/null | grep ESTAB | \
  awk '{print $5}' | grep -vE "10\.|172\.(1[6-9]|2|3[01])\.|192\.168\." | \
  grep -vE ":($STANDARD)$" | head -10 || echo "(비표준 포트 외부 연결 없음)"

echo ""
echo "--- 3. DNS 쿼리 이상 (dnsmasq/systemd-resolved 로그) ---"
journalctl -u systemd-resolved --since "1 hour ago" 2>/dev/null | \
  grep -iE "query|lookup" | tail -10 || echo "(DNS 로그 미확인)"

echo ""
echo "--- 4. 대량 데이터 전송 의심 ---"
ss -tnp 2>/dev/null | grep ESTAB | while read line; do
    recv=$(echo "$line" | awk '{print $2}')
    send=$(echo "$line" | awk '{print $3}')
    if [ "$send" -gt 1048576 ] 2>/dev/null; then
        echo "  [경고] 대량 전송: $(echo $line | awk '{print $4, $5}') (전송: ${send} bytes)"
    fi
done || echo "(대량 전송 없음)"

echo ""
echo "--- 5. LISTEN 포트 변경 감지 ---"
ss -tlnp 2>/dev/null | awk 'NR>1{print $4}' | sort
SCRIPT

echo "=== 네트워크 헌팅 ==="
bash /tmp/hunt_network.sh

echo ""
echo "=== secu(방화벽) 서버 ==="
ssh ccc@10.20.30.1 'bash -s' < /tmp/hunt_network.sh 2>/dev/null
```

## 3.4 Bastion 자동화 헌팅

```bash
export BASTION_API_KEY="ccc-api-key-2026"

# 헌팅 프로젝트 생성
PROJECT_ID=$(curl -s -X POST http://localhost:9100/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $BASTION_API_KEY" \
  -d '{
    "name": "threat-hunting-campaign",
    "request_text": "ATT&CK T1053.003(Cron) 기반 지속성 헌팅",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Project: $PROJECT_ID"

curl -s -X POST "http://localhost:9100/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $BASTION_API_KEY"
curl -s -X POST "http://localhost:9100/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $BASTION_API_KEY"

# 전체 서버 동시 헌팅
curl -s -X POST "http://localhost:9100/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $BASTION_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "find /etc/cron* /var/spool/cron -type f -mtime -7 2>/dev/null | wc -l && crontab -l 2>/dev/null | grep -vc \"^#\" && echo CRON_CHECK_DONE",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "find /etc/cron* /var/spool/cron -type f -mtime -7 2>/dev/null | wc -l && crontab -l 2>/dev/null | grep -vc \"^#\" && echo CRON_CHECK_DONE",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "find /etc/cron* /var/spool/cron -type f -mtime -7 2>/dev/null | wc -l && crontab -l 2>/dev/null | grep -vc \"^#\" && echo CRON_CHECK_DONE",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'

sleep 3
curl -s -H "X-API-Key: $BASTION_API_KEY" \
  "http://localhost:9100/projects/$PROJECT_ID/evidence/summary" | \
  python3 -m json.tool 2>/dev/null | head -40
```

---

# Part 4: 헌팅 결과 문서화 + 룰 전환 (40분)

## 4.1 헌팅 보고서 템플릿

```bash
cat << 'SCRIPT' > /tmp/hunting_report.py
#!/usr/bin/env python3
"""위협 헌팅 보고서 생성기"""
from datetime import datetime

report = {
    "campaign": "HUNT-2026-004",
    "title": "Linux 지속성 메커니즘 헌팅",
    "date": "2026-04-04",
    "hunter": "SOC Tier 3 분석가",
    "hypothesis": "공격자가 cron/systemd를 통해 Linux 서버에 지속성을 확보했을 수 있다",
    "technique": "T1053.003 (Scheduled Task/Job: Cron)",
    "scope": ["10.20.30.1 (secu)", "10.20.30.80 (web)", "10.20.30.100 (siem)"],
    "data_sources": ["프로세스 목록", "crontab", "systemd 서비스", "파일 시스템"],
    "findings": [
        {
            "severity": "INFO",
            "description": "secu 서버에 Bastion 관련 cron 작업 존재 (정상)",
            "action": "문서화",
        },
        {
            "severity": "LOW",
            "description": "web 서버 /tmp에 실행 가능 파일 2개 존재",
            "action": "파일 분석 후 정상 여부 확인",
        },
    ],
    "new_detections": [
        "SIGMA 룰: Cron 작업 생성/수정 탐지",
        "Wazuh 룰: /tmp 디렉토리 실행 파일 생성 알림",
    ],
    "recommendations": [
        "주간 cron 감사 자동화 추가",
        "/tmp 실행 권한 제거 검토 (noexec 마운트)",
        "새 systemd 서비스 등록 시 알림 룰 추가",
    ],
}

print("=" * 60)
print(f"  위협 헌팅 보고서: {report['campaign']}")
print("=" * 60)
print(f"\n제목: {report['title']}")
print(f"날짜: {report['date']}")
print(f"담당: {report['hunter']}")
print(f"\n가설: {report['hypothesis']}")
print(f"ATT&CK: {report['technique']}")
print(f"\n범위: {', '.join(report['scope'])}")
print(f"데이터: {', '.join(report['data_sources'])}")

print(f"\n--- 발견 사항 ({len(report['findings'])}건) ---")
for i, f in enumerate(report['findings'], 1):
    print(f"  {i}. [{f['severity']}] {f['description']}")
    print(f"     조치: {f['action']}")

print(f"\n--- 신규 탐지 룰 ({len(report['new_detections'])}건) ---")
for d in report['new_detections']:
    print(f"  - {d}")

print(f"\n--- 권고 사항 ---")
for r in report['recommendations']:
    print(f"  - {r}")
SCRIPT

python3 /tmp/hunting_report.py
```

## 4.2 헌팅 결과 → 탐지 룰 전환

```bash
# 헌팅에서 발견한 패턴을 Wazuh 탐지 룰로 전환
ssh ccc@10.20.30.100 << 'REMOTE'

sudo tee -a /var/ossec/etc/rules/local_rules.xml << 'RULES'

<group name="local,hunting,persistence,">

  <!-- 헌팅 결과: crontab 수정 탐지 -->
  <rule id="100700" level="10">
    <match>crontab</match>
    <regex>REPLACE|DELETE|LIST</regex>
    <description>[HUNT→DETECT] crontab 수정 탐지 (T1053.003)</description>
    <mitre>
      <id>T1053.003</id>
    </mitre>
    <group>hunting_derived,persistence,cron,</group>
  </rule>

  <!-- 헌팅 결과: /tmp에서 실행 파일 생성 -->
  <rule id="100701" level="8">
    <if_group>syscheck</if_group>
    <match>/tmp/</match>
    <regex>\.sh$|\.py$|\.pl$|\.elf$</regex>
    <description>[HUNT→DETECT] /tmp에 스크립트/실행파일 생성</description>
    <group>hunting_derived,suspicious_file,</group>
  </rule>

  <!-- 헌팅 결과: 새 systemd 서비스 등록 -->
  <rule id="100702" level="10">
    <match>systemd</match>
    <regex>new unit|unit created|service enabled</regex>
    <description>[HUNT→DETECT] 새 systemd 서비스 등록 (T1543.002)</description>
    <mitre>
      <id>T1543.002</id>
    </mitre>
    <group>hunting_derived,persistence,systemd,</group>
  </rule>

</group>
RULES

sudo /var/ossec/bin/wazuh-analysisd -t
echo "Exit code: $?"

REMOTE
```

> **실전 활용**: 헌팅 → 탐지 룰 전환(Hunt-to-Detect)은 SOC의 탐지 역량을 지속적으로 향상시키는 핵심 프로세스다. 모든 헌팅 캠페인은 최소 1개의 새 탐지 룰을 생성해야 한다.

---

## 체크리스트

- [ ] 위협 헌팅의 정의와 반응적 보안과의 차이를 설명할 수 있다
- [ ] 가설 기반 헌팅의 SQRRL 프레임워크를 설명할 수 있다
- [ ] 4가지 가설 유형(인텔리전스/상황/ATT&CK/이상징후)을 구분할 수 있다
- [ ] ATT&CK 매트릭스에서 Linux 환경 주요 기법을 알고 있다
- [ ] 베이스라인 수집 방법과 활용법을 이해한다
- [ ] 프로세스 헌팅(위장, /tmp 실행, 삭제 바이너리)을 수행할 수 있다
- [ ] 지속성 헌팅(cron, systemd, authorized_keys)을 수행할 수 있다
- [ ] 네트워크 헌팅(아웃바운드, 비표준 포트)을 수행할 수 있다
- [ ] 헌팅 보고서를 작성할 수 있다
- [ ] 헌팅 결과를 Wazuh 탐지 룰로 전환할 수 있다

---

## 과제

### 과제 1: ATT&CK 기반 헌팅 캠페인 (필수)

ATT&CK T1059.004(Unix Shell) 기법을 대상으로 헌팅 캠페인을 수행하라:
1. 가설 수립 (근거 포함)
2. 전체 서버에서 셸 실행 이력 수집
3. 베이스라인 대비 이탈 분석
4. 헌팅 보고서 작성
5. 최소 1개 탐지 룰 생성

### 과제 2: 네트워크 이상 헌팅 (선택)

전체 서버의 네트워크 연결을 분석하여:
1. 비표준 포트 아웃바운드 연결 식별
2. 대량 데이터 전송 패턴 확인
3. 내부 서버 간 비인가 통신 확인
4. 결과 보고서 작성

---

## 보충: 위협 헌팅 고급 기법

### 로그 기반 헌팅 쿼리 작성

```bash
# Wazuh 로그에서 비정상 패턴 헌팅
ssh ccc@10.20.30.100 << 'REMOTE'

echo "=== 헌팅 쿼리 1: 야간 SSH 접속 ==="
# 업무 시간 외(22:00-06:00) SSH 접속 시도
cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        alert = json.loads(line.strip())
        ts = alert.get('timestamp', '')
        rule = alert.get('rule', {})
        if 'ssh' in str(rule.get('groups', [])).lower():
            hour = int(ts[11:13]) if len(ts) > 13 else -1
            if hour >= 22 or hour < 6:
                print(f'  [{ts[:19]}] {rule.get(\"description\",\"\")} (Level {rule.get(\"level\",\"\")})')
    except: pass
" 2>/dev/null | head -10

echo ""
echo "=== 헌팅 쿼리 2: 비정상 프로세스 실행 순서 ==="
# whoami → cat /etc/passwd → wget 순서 패턴 탐지
cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | \
  python3 -c "
import sys, json
recon_cmds = []
for line in sys.stdin:
    try:
        alert = json.loads(line.strip())
        full_log = alert.get('full_log', '')
        if any(cmd in full_log for cmd in ['whoami', 'id ', 'uname', 'cat /etc/passwd', 'wget ', 'curl ']):
            src = alert.get('data', {}).get('srcip', 'unknown')
            ts = alert.get('timestamp', '')[:19]
            cmd = full_log[:60]
            recon_cmds.append(f'  [{ts}] {src}: {cmd}')
    except: pass
for r in recon_cmds[-10:]:
    print(r)
" 2>/dev/null

echo ""
echo "=== 헌팅 쿼리 3: 대용량 파일 접근 ==="
# /etc/shadow, /etc/passwd 등 민감 파일 접근
cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        alert = json.loads(line.strip())
        full_log = alert.get('full_log', '')
        if any(f in full_log for f in ['/etc/shadow', '/etc/passwd', '.ssh/id_rsa', '.bash_history']):
            ts = alert.get('timestamp', '')[:19]
            rule = alert.get('rule', {})
            print(f'  [{ts}] {rule.get(\"description\",\"\")}')
    except: pass
" 2>/dev/null | head -10

REMOTE
```

> **실습 목적**: SIEM 로그를 직접 쿼리하여 경보 룰에 걸리지 않는 위협 패턴을 찾는다.
>
> **배우는 것**: 헌팅 쿼리 작성 기법, 시간대 기반 분석, 행위 순서 분석
>
> **결과 해석**: 야간 SSH 접속이 발견되면 정상 업무인지 확인해야 한다. 정찰 명령이 순서대로 실행되었다면 공격자의 활동 가능성이 높다.
>
> **트러블슈팅**:
> - JSON 파싱 오류 → alerts.json 형식 확인 (각 줄이 독립 JSON)
> - 결과가 없음 → 시간 범위 확장 또는 다른 로그 파일 확인

### 데이터 과학 기반 헌팅

```bash
cat << 'SCRIPT' > /tmp/data_science_hunting.py
#!/usr/bin/env python3
"""데이터 과학 기반 위협 헌팅"""
import random
import statistics
from collections import Counter
from datetime import datetime, timedelta

# 시뮬레이션: 서버별 SSH 접속 패턴
servers = {
    "secu": {"normal_daily": 15, "variance": 3},
    "web": {"normal_daily": 25, "variance": 5},
    "siem": {"normal_daily": 20, "variance": 4},
}

print("=" * 60)
print("  데이터 과학 기반 위협 헌팅")
print("=" * 60)

# 30일간 SSH 접속 시뮬레이션
for server, params in servers.items():
    daily_counts = []
    for day in range(30):
        count = max(0, int(random.gauss(params["normal_daily"], params["variance"])))
        # Day 25에 이상값 삽입 (공격 시뮬레이션)
        if day == 25:
            count = params["normal_daily"] * 3 + random.randint(10, 20)
        daily_counts.append(count)
    
    mean = statistics.mean(daily_counts)
    stdev = statistics.stdev(daily_counts)
    
    print(f"\n--- {server} 서버 SSH 접속 분석 ---")
    print(f"  평균: {mean:.1f}건/일, 표준편차: {stdev:.1f}")
    
    # Z-score 기반 이상 탐지
    for i, count in enumerate(daily_counts):
        z_score = (count - mean) / stdev if stdev > 0 else 0
        if abs(z_score) > 2:
            print(f"  [경고] Day {i+1}: {count}건 (Z={z_score:.2f}) - 이상값!")

print("\n=== 이상 탐지 기준 ===")
print("  Z-score > 2: 95% 신뢰구간 밖 → 의심")
print("  Z-score > 3: 99.7% 신뢰구간 밖 → 강력 의심")
print("  IQR 방법: Q1-1.5*IQR ~ Q3+1.5*IQR 밖 → 이상")
SCRIPT

python3 /tmp/data_science_hunting.py
```

> **배우는 것**: 통계적 방법(Z-score, IQR)을 활용하여 베이스라인 이탈을 정량적으로 탐지하는 기법. 시각적 판단이 아닌 데이터 기반 판단이 가능하다.

### 헌팅 캘린더 수립

```bash
cat << 'SCRIPT' > /tmp/hunting_calendar.py
#!/usr/bin/env python3
"""분기별 헌팅 캘린더"""

calendar = {
    "1월": {"기법": "T1059 (Execution)", "가설": "비정상 스크립트 실행", "범위": "전체 서버"},
    "2월": {"기법": "T1053 (Persistence)", "가설": "신규 cron/systemd 변조", "범위": "전체 서버"},
    "3월": {"기법": "T1110 (Credential)", "가설": "느린 무차별 대입", "범위": "SSH/웹"},
    "4월": {"기법": "T1021 (Lateral)", "가설": "비정상 SSH 접속 패턴", "범위": "내부 서버"},
    "5월": {"기법": "T1048 (Exfiltration)", "가설": "대용량 아웃바운드", "범위": "네트워크"},
    "6월": {"기법": "T1071 (C2)", "가설": "비콘 통신 패턴", "범위": "네트워크"},
    "7월": {"기법": "T1136 (Account)", "가설": "비인가 계정 생성", "범위": "전체 서버"},
    "8월": {"기법": "T1070 (Defense Evasion)", "가설": "로그 삭제/변조", "범위": "로그 서버"},
    "9월": {"기법": "T1505 (Webshell)", "가설": "웹셸 존재 여부", "범위": "웹서버"},
    "10월": {"기법": "T1543 (Systemd)", "가설": "비인가 서비스 등록", "범위": "전체 서버"},
    "11월": {"기법": "T1003 (Credential Dump)", "가설": "민감 파일 접근", "범위": "전체 서버"},
    "12월": {"기법": "종합 리뷰", "가설": "연간 헌팅 결과 정리", "범위": "전체"},
}

print("=" * 70)
print("  연간 위협 헌팅 캘린더")
print("=" * 70)
print(f"\n{'월':>4s}  {'기법':20s}  {'가설':25s}  {'범위':>10s}")
print("-" * 70)

for month, info in calendar.items():
    print(f"{month:>4s}  {info['기법']:20s}  {info['가설']:25s}  {info['범위']:>10s}")

print("\n→ 월 1회 정기 헌팅, 분기 1회 대규모 헌팅 권장")
SCRIPT

python3 /tmp/hunting_calendar.py
```

> **실전 활용**: 연간 헌팅 캘린더를 수립하면 체계적으로 ATT&CK 커버리지를 확대할 수 있다. 매월 다른 기법을 집중 헌팅하면 1년에 12개 기법의 탐지 역량을 강화할 수 있다.

---

## 다음 주 예고

**Week 07: 네트워크 포렌식**에서는 Wireshark/tshark를 심화 활용하여 네트워크 패킷 분석과 NetFlow 기반 트래픽 분석을 수행한다.

---

## 웹 UI 실습

### Wazuh Dashboard — SIGMA 룰 + 위협 헌팅 워크플로우

> **접속 URL:** `https://10.20.30.100:443`

1. 브라우저에서 `https://10.20.30.100:443` 접속 → 로그인
2. **Modules → Security events** 클릭
3. 가설 기반 헌팅 쿼리 실행 (예: 비정상 프로세스 탐지):
   ```
   data.process.name: (nc OR ncat OR socat OR python*) AND NOT rule.level: 0
   ```
4. 시간 범위를 **Last 30 days**로 확대하여 장기 패턴 분석
5. **Discover** 탭에서 결과를 시간축으로 정렬 → 이상 클러스터 식별
6. **Save search** 로 헌팅 쿼리 저장 → 반복 헌팅에 재활용
7. 의심 이벤트 발견 시 **Inspect** 클릭 → 원본 로그 전문 확인

### OpenCTI — 위협 헌팅 워크플로우 연동

> **접속 URL:** `http://10.20.30.100:8080`

1. `http://10.20.30.100:8080` 접속 → 로그인
2. **Techniques → Attack patterns** 에서 헌팅 대상 ATT&CK 기법 검색
3. 해당 기법 페이지 → **Knowledge** 탭에서 알려진 위협 그룹/캠페인 확인
4. **Observations → Indicators** 에서 해당 기법과 연관된 IOC 수집
5. 수집한 IOC를 Wazuh Dashboard 검색에 활용하여 헌팅 범위 구체화
6. 헌팅 결과를 OpenCTI에 **Sighting** 으로 등록하여 조직 내 탐지 이력 기록

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### Wazuh SIEM (4.11.x)
> **역할:** 에이전트 기반 로그·FIM·SCA 통합 분석 플랫폼  
> **실행 위치:** `siem (10.20.30.100)`  
> **접속/호출:** Dashboard `https://10.20.30.100` (admin/admin), Manager API `:55000`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `/var/ossec/etc/ossec.conf` | Manager 메인 설정 (원격, 전송, syscheck 등) |
| `/var/ossec/etc/rules/local_rules.xml` | 커스텀 룰 (id ≥ 100000) |
| `/var/ossec/etc/decoders/local_decoder.xml` | 커스텀 디코더 |
| `/var/ossec/logs/alerts/alerts.json` | 실시간 JSON 알림 스트림 |
| `/var/ossec/logs/archives/archives.json` | 전체 이벤트 아카이브 |
| `/var/ossec/logs/ossec.log` | Manager 데몬 로그 |
| `/var/ossec/queue/fim/db/fim.db` | FIM 기준선 SQLite DB |

**핵심 설정·키**

- `<rule id='100100' level='10'>` — 커스텀 룰 — level 10↑은 고위험
- `<syscheck><directories>...` — FIM 감시 경로
- `<active-response>` — 자동 대응 (firewall-drop, restart)

**로그·확인 명령**

- `jq 'select(.rule.level>=10)' alerts.json` — 고위험 알림만
- `grep ERROR ossec.log` — Manager 오류 (룰 문법 오류 등)

**UI / CLI 요점**

- Dashboard → Security events — KQL 필터 `rule.level >= 10`
- Dashboard → Integrity monitoring — 변경된 파일 해시 비교
- `/var/ossec/bin/wazuh-logtest` — 룰 매칭 단계별 확인 (Phase 1→3)
- `/var/ossec/bin/wazuh-analysisd -t` — 룰·설정 문법 검증

> **해석 팁.** Phase 3에서 원하는 `rule.id`가 떠야 커스텀 룰 정상. `local_rules.xml` 수정 후 `systemctl restart wazuh-manager`, 문법 오류가 있으면 **분석 데몬 전체가 기동 실패**하므로 `-t`로 먼저 검증.

### SIGMA + YARA
> **역할:** SIGMA=플랫폼 독립 탐지 룰, YARA=파일/메모리 시그니처  
> **실행 위치:** `SOC 분석가 PC / siem`  
> **접속/호출:** `sigmac` 변환기, `yara <rule> <target>`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `~/sigma/rules/` | SIGMA 룰 저장 |
| `~/yara-rules/` | YARA 룰 저장 |

**핵심 설정·키**

- `SIGMA logsource:product/service` — 로그 소스 매핑
- `YARA `strings: $s1 = "..." ascii wide`` — 시그니처 정의
- `YARA `condition: all of them and filesize < 1MB`` — 매칭 조건

**UI / CLI 요점**

- `sigmac -t elasticsearch-qs rule.yml` — Elastic용 KQL 변환
- `sigmac -t wazuh rule.yml` — Wazuh XML 룰 변환
- `yara -r rules.yar /var/tmp/sample.bin` — 재귀 스캔

> **해석 팁.** SIGMA는 *탐지 의도*, YARA는 *바이너리 패턴*으로 역할 분리. SIGMA 룰은 반드시 **false positive 조건**까지 기술해야 SIEM 운영 가능.

---

## 실제 사례 (WitFoo Precinct 6 — SOAR 자동화)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *SOAR 자동화* 학습 항목 매칭.

### SOAR 자동화 의 dataset 흔적 — "playbook + IR"

dataset 의 정상 운영에서 *playbook + IR* 신호의 baseline 을 알아두면, *SOAR 자동화* 시도 시 발생하는 anomaly 를 정량으로 탐지할 수 있다. 핵심 정량 지표는 — Playbook 자동 실행 사이클.

```mermaid
graph LR
    SCENE["SOAR 자동화 시나리오"]
    TRACE["dataset 흔적<br/>playbook + IR"]
    DETECT["탐지 / 분석"]

    SCENE --> TRACE
    TRACE --> DETECT

    style SCENE fill:#ffe6cc
    style DETECT fill:#cce6ff
```

### Case 1: dataset 정량 지표

| 항목 | 값 |
|---|---|
| 핵심 신호 | playbook + IR |
| 정량 baseline | Playbook 자동 실행 사이클 |
| 학습 매핑 | Tines/Phantom playbook |

**자세한 해석**: Tines/Phantom playbook. 이 차이를 정량으로 측정해야 *공격 시도와 정상 운영의 구분* 이 가능. 학생이 baseline 숫자를 외워두면 — 운영 환경에서 anomaly 를 즉시 탐지할 수 있다.

### Case 2: 실전 적용 시나리오

| 단계 | dataset 활용 |
|---|---|
| 시도 식별 | playbook + IR 의 spike |
| 정상 vs 이상 | baseline 대비 비율 |
| 룰 작성 | Suricata / Wazuh / Sigma |
| 검증 | dataset 재실행 |

**자세한 해석**: 운영 환경 룰 작성은 — *baseline 측정 → 임계 결정 → 룰 작성 → dataset 검증* 의 4 단계. 한 단계라도 빠지면 false positive 폭증.

### 이 사례에서 학생이 배워야 할 3가지

1. **SOAR 자동화 = playbook + IR 의 anomaly** — 정량 신호로 탐지.
2. **baseline 숫자 외우기** — Playbook 자동 실행 사이클.
3. **4 단계 룰 작성** — 측정 → 임계 → 룰 → 검증.

**학생 액션**: 5 단계 SOAR 흐름.


---

## 부록: 학습 OSS 도구 매트릭스 (Course14 SOC Advanced — Week 06 위협 헌팅·HMM·ATT&CK 매트릭스)

> 이 부록은 lab `soc-adv-ai/week06.yaml` (15 step + multi_task) 의 모든 명령을
> 실제로 실행 가능한 형태로 도구·옵션·예상 출력·해석을 정리한다. 가설 기반/IOC 기반/
> 데이터 기반 헌팅, DNS 터널링/비콘/lateral/exfil/persistence 5종 헌팅, Jupyter
> 노트북, Sigma 룰 전환, ATT&CK Hunting Matrix, Sqrrl HMM 0-4 평가까지.

### lab step → 도구·헌팅 매핑 표

| step | 학습 항목 | 핵심 OSS 도구 / 명령 | ATT&CK |
|------|----------|---------------------|--------|
| s1 | 헌팅 3 접근법 (가설/IOC/데이터) | 매트릭스 + 사례 | - |
| s2 | DNS 터널링 가설 + 데이터 소스 정의 | 가설 템플릿 + 데이터 매핑 | T1071.004 |
| s3 | DNS 로그 수집 + 도메인 빈도 | Wazuh + jq + dnsmasq log | T1071.004 |
| s4 | 비콘 활동 (interval std deviation) | python pandas + numpy + Wazuh | T1071 |
| s5 | 비정상 프로세스 헌팅 | syscheck + rootcheck + ps -ef | T1059 / T1014 |
| s6 | Lateral Movement 헌팅 | SSH log + nft conntrack + BloodHound | T1021 |
| s7 | Exfiltration 헌팅 (대용량 / 비정상 protocol) | NetFlow + Zeek conn.log + entropy | T1041 / T1048 |
| s8 | Persistence 헌팅 (cron/systemd/.bashrc/kmod) | osquery + Wazuh syscheck | T1053 / T1546 |
| s9 | Jupyter 헌팅 노트북 템플릿 | Jupyter + pandas + plotly + msticpy | - |
| s10 | 헌팅 발견 → SIGMA 룰 전환 | sigma-cli (week03 도구 재사용) | - |
| s11 | ATT&CK 헌팅 매트릭스 | ATT&CK Navigator + DeTT&CT | - |
| s12 | 헌팅 캠페인 계획 (월간/우선순위/RACI) | mermaid Gantt + RACI 표 | - |
| s13 | 헌팅 도구 체인 (수집→분석→시각화→문서화) | Wazuh + python + Grafana + Jupyter | - |
| s14 | Sqrrl HMM 5단계 평가 | HMM 자가진단 + radar chart | - |
| s15 | 헌팅 종합 보고서 | markdown + Jupyter export + roadmap | - |
| s99 | 통합 다단계 (s1→s2→s3→s4→s5) | Bastion plan: 접근법→가설→DNS log→비콘→프로세스 | 다중 |

### 학생 환경 준비 (헌팅 풀세트)

```bash
# === [s9·s13] Jupyter + 분석 ===
pip install --user jupyter jupyterlab pandas numpy matplotlib plotly seaborn
pip install --user msticpy yara-python
jupyter lab --port 8888 --ip 0.0.0.0 --no-browser &

# === [s3·s4] DNS / 네트워크 ===
sudo apt install -y dnsmasq tshark zeek bind-utils
sudo apt install -y zeek-aux zeek-spicy

# === [s5·s8] 호스트 헌팅 ===
sudo apt install -y osquery auditd
sudo systemctl enable --now osqueryd

# === [s6] Lateral ===
sudo apt install -y openssh-client conntrack jq

# === [s7] NetFlow + entropy ===
sudo apt install -y nfcapd nfdump
pip install --user scapy

# === [s10] SIGMA (week03 와 동일) ===
pip install --user sigma-cli pysigma pysigma-backend-elasticsearch

# === [s11·s14] ATT&CK + HMM ===
ls /tmp/nav 2>/dev/null
ls /tmp/dettect 2>/dev/null

# === Wazuh API ===
TOKEN=$(curl -sk -u wazuh:wazuh -X POST "https://10.20.30.100:55000/security/user/authenticate?raw=true")
```

### 핵심 도구별 상세 사용법

#### 도구 1: 헌팅 3 접근법 (Step 1)

| 접근법 | 시작점 | 데이터 소스 | 도구 | 적용 |
|-------|--------|------------|------|------|
| **가설 기반** | "내부가 DNS 터널링" | targeted query | Jupyter + Wazuh API | TI 부족 / 신규 위협 |
| **IOC 기반** | 알려진 IOC | TI 피드 + 로그 | Wazuh CDB + grep | TI 풍부 / 빠른 |
| **데이터 기반** | baseline 이탈 | 모든 로그 (long-term) | ML / pandas / Spark | 대용량 / unsupervised |

#### 도구 2: DNS 터널링 헌팅 (Step 2·3)

```python
import requests, pandas as pd, math
TOKEN = "Bearer ..."
INDEX = "https://10.20.30.100:9200"

r = requests.get(
    f"{INDEX}/wazuh-alerts-*/_search",
    auth=("admin", "admin"), verify=False,
    json={"size": 10000,
          "query": {"bool": {"must": [
              {"range": {"@timestamp": {"gte": "now-24h"}}},
              {"prefix": {"rule.id": "31"}}]}}})

df = pd.json_normalize([h["_source"] for h in r.json()["hits"]["hits"]])

def entropy(s):
    if not s: return 0
    freq = {}
    for c in s: freq[c] = freq.get(c, 0) + 1
    total = len(s)
    return -sum((c/total) * math.log2(c/total) for c in freq.values())

df['domain_length'] = df['data.dns_query'].str.len()
df['domain_entropy'] = df['data.dns_query'].fillna('').apply(entropy)

# 의심 — 길이 50+ + entropy 4.5+ (DNS 터널링 시그니처)
suspicious = df[(df['domain_length'] > 50) & (df['domain_entropy'] > 4.5)]
print(f"DNS tunneling 의심: {len(suspicious)} queries")

import plotly.express as px
fig = px.scatter(df, x='domain_length', y='domain_entropy',
                 hover_data=['data.dns_query'],
                 title='DNS Query — Length vs Entropy')
fig.add_shape(type="rect", x0=50, y0=4.5, x1=df.domain_length.max(),
              y1=df.domain_entropy.max(), line=dict(color="red"),
              fillcolor="rgba(255,0,0,0.1)")
fig.show()
```

```bash
# bash 빠른 분석
ssh ccc@10.20.30.100 'sudo grep -i "dns_query" /var/ossec/logs/alerts/alerts.json | \
  jq -r ".data.dns_query" | sort | uniq -c | sort -rn | head -20'

# 긴 도메인 추출
ssh ccc@10.20.30.100 'sudo jq -r "select(.data.dns_query | length > 50) | .data.dns_query" \
  /var/ossec/logs/alerts/alerts.json | sort -u | head -10'

# Zeek
ssh ccc@10.20.30.1 'sudo zeek-cut id.orig_h query qtype_name < /var/log/zeek/dns.log' | \
  awk '{ print $2 }' | sort | uniq -c | sort -rn | head -10
```

#### 도구 3: 비콘 헌팅 (Step 4)

```python
# 통신 interval CV (coefficient of variation) 분석
def beacon_score(group):
    if len(group) < 5: return None
    intervals = group['ts'].sort_values().diff().dt.total_seconds().dropna()
    if len(intervals) < 4: return None
    mean = intervals.mean(); std = intervals.std()
    cv = std / mean if mean > 0 else float('inf')
    return {'count': len(group), 'mean_interval_sec': mean, 'std_sec': std, 'cv': cv}

results = df.groupby(['data.src_ip', 'data.dest_ip']).apply(beacon_score).dropna()
suspicious = results[results.apply(lambda x: x and x['cv'] < 0.3 and x['count'] > 10)]
print("Beacon 의심:")
for (src, dst), info in suspicious.items():
    print(f"  {src} → {dst}: count={info['count']}, "
          f"interval={info['mean_interval_sec']:.1f}s, cv={info['cv']:.3f}")
```

```bash
# Zeek conn.log 빠른 분석
ssh ccc@10.20.30.1 'sudo zeek-cut ts id.orig_h id.resp_h duration < /var/log/zeek/conn.log' | \
  awk '
    { key = $2 "->" $3
      if (last[key]) { diff = $1 - last[key]; sum[key] += diff; sumsq[key] += diff*diff; count[key]++ }
      last[key] = $1 }
    END {
      for (k in count) {
        if (count[k] > 5) {
          mean = sum[k]/count[k]; var = sumsq[k]/count[k] - mean*mean
          std = sqrt(var); cv = std/mean
          if (cv < 0.3) printf "%s count=%d mean=%.1fs cv=%.3f\n", k, count[k], mean, cv
        }
      }
    }' | sort -k 2 -rn | head -10
```

#### 도구 4: 비정상 프로세스 + Persistence 헌팅 (Step 5·8)

```bash
# === osquery — 시스템 SQL ===
sudo osqueryi << 'SQL'
-- SUID 바이너리
SELECT path, mode FROM file WHERE path LIKE '/usr/%/%' AND mode LIKE '%4%%%%%%';
-- 의심 cron
SELECT * FROM crontab WHERE command LIKE '%curl%' OR command LIKE '%wget%';
-- systemd persistence
SELECT name, path FROM systemd_units WHERE source_path LIKE '%/tmp/%';
-- .bashrc 변조
SELECT path, mtime FROM file WHERE path LIKE '/home/%/.bashrc';
-- 부모-자식 이상
SELECT p.pid, p.name, pp.name AS parent_name FROM processes p
JOIN processes pp ON p.parent = pp.pid
WHERE p.name IN ('bash','sh','nc') AND pp.name IN ('nginx','apache2');
SQL

# 부모 미상
ps -eo pid,ppid,comm,args | awk '$2 == 1 && $3 != "systemd" && $3 != "init"'

# 메모리만 (fileless)
ps -eo pid,comm,args | grep -E '/proc/[0-9]+/(fd|exe)|/dev/shm'

# 숨겨진 프로세스
diff <(ps -eo pid --no-headers | sort -n) <(ls /proc | grep '^[0-9]' | sort -n)

# === Persistence 5종 ===
# 1. Cron
sudo crontab -l && sudo cat /etc/crontab && sudo ls /etc/cron.{d,daily,hourly,monthly,weekly}/
# 2. Systemd
sudo find / -name "*.service" -newer /tmp/baseline -mtime -7 2>/dev/null
# 3. Shell init
for u in $(cut -d: -f1 /etc/passwd); do
    home=$(getent passwd $u | cut -d: -f6)
    [ -d "$home" ] && find "$home" -maxdepth 1 -name ".*rc" -newer /tmp/baseline 2>/dev/null
done
# 4. Kernel modules
sudo lsmod | head && sudo dmesg | grep -i 'loaded\|inserted' | tail
# 5. SUID 신규
sudo find / -perm -4000 -newer /tmp/baseline -ls 2>/dev/null
```

#### 도구 5: Lateral + Exfiltration 헌팅 (Step 6·7)

```python
# Lateral — 내부-내부 SSH + 신규 user×host
INTERNAL = "10.20.30."
df['internal_to_internal'] = (
    df['data.srcip'].fillna('').str.startswith(INTERNAL) &
    df['agent.ip'].fillna('').str.startswith(INTERNAL))
lateral = df[df['internal_to_internal']]

baseline = df[df['@timestamp'] < '2026-04-01'].groupby(['data.dstuser','agent.name']).size()
recent = df[df['@timestamp'] >= '2026-04-01'].groupby(['data.dstuser','agent.name']).size()
new_pairs = recent.index.difference(baseline.index)
print(f"신규 user×host: {len(new_pairs)}")
```

```bash
# Exfil — 대용량 outbound (Zeek)
ssh ccc@10.20.30.1 'sudo zeek-cut id.orig_h id.resp_h proto orig_bytes resp_bytes duration < /var/log/zeek/conn.log' | \
  awk -v threshold=10485760 '
    $4 > threshold || $5 > threshold {
      printf "%s -> %s | %s | %d | %d\n", $1, $2, $3, $4, $5
    }' | sort -t'|' -k 5 -rn | head -10

# 비정상 protocol
ssh ccc@10.20.30.1 'sudo zeek-cut id.orig_h id.resp_h id.resp_p proto service < /var/log/zeek/conn.log' | \
  awk '($3 == 25 || $3 == 587) && $1 !~ /mailserver/ { print "Suspicious SMTP:", $0 }'

# entropy — 인코딩된 exfil
python3 -c "
import math, json
def ent(s):
    f={}; [f.__setitem__(c,f.get(c,0)+1) for c in s]
    t=len(s); return -sum((c/t)*math.log2(c/t) for c in f.values())

import subprocess
out = subprocess.run(['ssh','ccc@10.20.30.100',
                     'sudo jq -r \".data.dns_query // empty\" /var/ossec/logs/alerts/alerts.json'],
                    capture_output=True, text=True)
queries = out.stdout.strip().split('\n')
high = [q for q in queries if ent(q) > 4.5 and len(q) > 30]
print(f'High-entropy DNS (potential exfil): {len(high)}')
"
```

#### 도구 6: Jupyter 헌팅 노트북 템플릿 (Step 9)

```python
"""
# H001 - DNS Tunneling Detection
**ATT&CK**: T1071.004
**가설**: 내부 호스트가 DNS subdomain 으로 C2 통신
**데이터 소스**: Wazuh DNS rules + Suricata DNS log
"""

# Cell 1: Setup
import pandas as pd, requests, plotly.express as px, math
from datetime import datetime
TOKEN = "..."; INDEX = "https://10.20.30.100:9200"

# Cell 2: Data Collection
def fetch_wazuh(query, size=10000, days=7):
    r = requests.get(f"{INDEX}/wazuh-alerts-*/_search",
                     auth=("admin","admin"), verify=False,
                     json={"size": size, "query": {"bool": {"must": [
                         {"range": {"@timestamp": {"gte": f"now-{days}d"}}}, query]}}})
    return pd.json_normalize([h["_source"] for h in r.json()["hits"]["hits"]])

df = fetch_wazuh({"prefix": {"rule.id": "31"}}, size=50000, days=7)

# Cell 3: Analysis
def entropy(s):
    if not s: return 0
    f={}; [f.__setitem__(c,f.get(c,0)+1) for c in s]
    t=len(s); return -sum((c/t)*math.log2(c/t) for c in f.values())
df['domain_length'] = df['data.dns_query'].fillna('').str.len()
df['domain_entropy'] = df['data.dns_query'].fillna('').apply(entropy)

# Cell 4: Visualization
fig = px.scatter(df, x='domain_length', y='domain_entropy',
                 hover_data=['data.dns_query'])
fig.show()

# Cell 5: Findings
suspicious = df[(df['domain_length'] > 50) & (df['domain_entropy'] > 4.5)]
print(f"의심: {len(suspicious)} queries")

# Cell 6: Conclusion
"""
## 결론
- 의심 query: N건
- 다음 단계: SIGMA 룰 변환 + Wazuh 연동
"""

# Cell 7: Export
suspicious[['@timestamp','agent.name','data.dns_query','domain_length','domain_entropy']].to_csv(
    f'/tmp/h001-findings-{datetime.now():%Y%m%d}.csv', index=False)
# !jupyter nbconvert --to html h001_dns_tunneling.ipynb
```

#### 도구 7: 헌팅 발견 → SIGMA 룰 (Step 10)

```yaml
title: DNS Query with Suspicious Length and Entropy (Hunting H001)
id: hunting-h001-dns-tunnel-1234
status: experimental
description: H001 의 발견을 자동 탐지로 — DNS query 50자+, entropy 4.5+
references:
  - notebook://h001_dns_tunneling.ipynb
tags:
  - attack.command_and_control
  - attack.t1071.004
logsource:
  category: dns
detection:
  selection:
    query|re: '^[a-zA-Z0-9_\-]{50,}\..*'
  condition: selection
falsepositives:
  - 합법적 긴 도메인 (CDN / cloud)
level: medium
---
title: Beaconing Detection — Low CV Periodic Communication (Hunting H002)
id: hunting-h002-beacon-5678
correlation:
  type: temporal
  rules: [out_connection_event]
  group-by: [src_ip, dst_ip]
  timespan: 24h
tags:
  - attack.command_and_control
  - attack.t1071
level: medium
```

```bash
sigma convert -t wazuh -p wazuh_default ~/sigma-rules/hunting/h001_dns_tunnel.yml
sigma convert -t splunk -p splunk_default ~/sigma-rules/hunting/h002_beacon.yml
```

#### 도구 8: ATT&CK Hunting Matrix + HMM (Step 11·14)

| Tactic | Technique | 헌팅 가설 | 데이터 소스 | 우선순위 |
|--------|-----------|----------|------------|---------|
| Initial Access | T1190 | 비정상 web request | Apache + ModSecurity | High |
| Initial Access | T1078 | 신규 user × host | SSH log + AD | Medium |
| Execution | T1059 | bash from non-shell parent | auth + ps | High |
| Persistence | T1053.003 | 신규 cron | osquery + auditd | High |
| Persistence | T1546 | bashrc 변조 | osquery FIM | Medium |
| PrivEsc | T1068 | 신규 SUID | osquery + find | Critical |
| Defense Evasion | T1070.002 | log clear | wtmp 비교 | Critical |
| Cred Access | T1003.008 | shadow read by non-root | auditd | Critical |
| Lateral | T1021.004 | internal SSH | SSH log | High |
| Collection | T1005 | 다수 파일 read | auditd PATH | Medium |
| Exfil | T1041 | 대용량 outbound | Zeek + NetFlow | High |
| C2 | T1071.004 | DNS 터널링 | DNS log | High |
| C2 | T1071 | beaconing | conn.log | Critical |

```bash
# ATT&CK Navigator JSON
python3 << 'PY' > /tmp/hunting-coverage.json
import json
techs = ["T1190","T1078","T1059","T1053.003","T1546","T1068","T1070.002",
         "T1003.008","T1021.004","T1005","T1041","T1071.004","T1071"]
print(json.dumps({
    "name": "Hunting Coverage 2026-Q2",
    "versions": {"attack": "14", "navigator": "4.9.4", "layer": "4.5"},
    "domain": "enterprise-attack",
    "techniques": [{"techniqueID": t, "score": 100, "color": "#00ff00",
                    "comment": "Hunting playbook 보유"} for t in techs]
}, indent=2))
PY
```

**Sqrrl HMM 5 단계**:

| Level | 명칭 | 특성 |
|-------|------|------|
| HM0 | Initial | 자동 보고 의존, hunting 없음 |
| HM1 | Minimal | 검색 시 가끔 hunting, 도구 부족 |
| HM2 | Procedural | 절차 정립, 도구 설치, 가설 기반 |
| HM3 | Innovative | 데이터 기반, ML 활용 |
| HM4 | Leading | 사내 도구 개발, 외부 contribute |

```python
# Radar chart
import matplotlib.pyplot as plt
import numpy as np
domains = ["Procedural","Hypothesis","Tools","Data","Innovation"]
current = [2,2,2,1,1]; target = [3,3,3,3,3]
angles = np.linspace(0, 2*np.pi, len(domains), endpoint=False).tolist()
current += current[:1]; target += target[:1]; angles += angles[:1]
fig, ax = plt.subplots(figsize=(8,8), subplot_kw=dict(polar=True))
ax.plot(angles, current, 'o-', linewidth=2, label='Current', color='#3b82f6')
ax.fill(angles, current, alpha=0.25, color='#3b82f6')
ax.plot(angles, target, 'o-', linewidth=2, label='Target HM3', color='#ef4444', linestyle='--')
ax.set_xticks(angles[:-1]); ax.set_xticklabels(domains)
ax.set_ylim(0, 4); ax.set_yticks([0,1,2,3,4])
ax.set_yticklabels(['HM0','HM1','HM2','HM3','HM4'])
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.savefig('/tmp/hmm-radar.png', dpi=150, bbox_inches='tight')
```

#### 도구 9: 캠페인 + 도구 체인 (Step 12·13)

```bash
# 월간 Gantt
cat > /tmp/hunting-campaign.mmd << 'M'
gantt
    title 2026-Q3 Hunting Campaign
    dateFormat  YYYY-MM-DD
    section Week 1
      H001 DNS Tunneling     :h1, 2026-07-01, 5d
      H002 Beaconing         :h2, 2026-07-01, 5d
    section Week 2
      H003 Lateral SSH       :h3, 2026-07-08, 5d
      H004 Persistence cron  :h4, 2026-07-08, 5d
    section Week 3
      H005 Exfil bulk        :h5, 2026-07-15, 5d
      H006 SUID changes      :h6, 2026-07-15, 5d
    section Week 4
      Findings → SIGMA       :sg, 2026-07-22, 5d
      Coverage report        :rep, 2026-07-22, 5d
M
mmdc -i /tmp/hunting-campaign.mmd -o /tmp/hunting-campaign.png
```

**RACI**:

| 항목 | Hunt Lead | T1 | T2 | T3 | CISO |
|------|-----------|-----|-----|-----|------|
| 가설 작성 | A | I | C | R | I |
| 데이터 수집 | C | R | R | C | - |
| 분석 | C | R | A/R | C | - |
| SIGMA 변환 | C | I | R | A | I |
| 보고서 | A | I | C | C | R |

**도구 체인**:

| 단계 | 도구 |
|------|------|
| 수집 | Wazuh API + OpenSearch |
| 분석 | Python (pandas/numpy) |
| 시각화 | Plotly + matplotlib |
| 문서화 | Jupyter + nbconvert HTML |
| 룰화 | sigma-cli (week03) |
| 자동화 | TheHive + Cortex |
| 협업 | git PR + GitHub Issues |

### 점검 / 작성 / 캠페인 흐름 (15 step + multi_task 통합)

#### Phase A — 가설 + 데이터 (s1·s2·s3·s4·s5·s6·s7·s8)

```bash
jupyter lab --ip 0.0.0.0 --port 8888 --no-browser &

mkdir ~/hunting-notebooks
for h in h001-dns-tunnel h002-beacon h003-lateral-ssh h004-exfil-bulk h005-persistence h006-suid; do
  cp /templates/hunting-notebook.ipynb ~/hunting-notebooks/${h}.ipynb
done
jupyter nbconvert --execute --to html ~/hunting-notebooks/*.ipynb
```

#### Phase B — 룰 변환 + Coverage (s10·s11)

```bash
mkdir ~/sigma-rules/hunting
for f in ~/sigma-rules/hunting/*.yml; do
    sigma convert -t wazuh -p wazuh_default $f
done
sigma2attack --rules-directory ~/sigma-rules/hunting/ --out-file ~/sigma-rules/hunting-coverage.json
```

#### Phase C — 캠페인 + 보고 (s12·s13·s14·s15)

```bash
mmdc -i /tmp/hunting-campaign.mmd -o /tmp/hunting-campaign.png
python3 /tmp/hmm-radar.py

cat > /tmp/hunting-report.md << 'EOF'
# Threat Hunting Report — 2026-Q2

## 헌팅 가설 (이번 분기 6개)
- H001 DNS Tunneling → 발견 23 / SIGMA 1
- H002 Beaconing → 발견 8 / SIGMA 1
- H003 Lateral SSH → 발견 3 / SIGMA 1
- H004 Exfil Bulk → 발견 5 / SIGMA 1
- H005 Persistence → 발견 12 / SIGMA 2
- H006 SUID Changes → 발견 4 / SIGMA 1

## 발견 위협 (validated)
- T1071.004 DNS 터널링: 1 호스트
- T1041 대용량 exfil: 2 호스트
- 총 validated true positive: 3 incidents

## 생성된 탐지 룰
- SIGMA: 7 신규 → Wazuh + Splunk + Elastic 변환

## HMM 평가
- 현재: HM1 / 6개월 목표 HM2 / 12개월 목표 HM3

## 개선 권고
1. msticpy 통합
2. Zeek 풀 운영
3. Jupyter git PR 워크플로우
4. TI 피드 통합 (week05 와 결합)
EOF
```

#### Phase D — 통합 시나리오 (s99 multi_task)

s1 → s2 → s3 → s4 → s5 를 Bastion 가 한 번에:

1. **plan**: 3 접근법 → DNS 가설 → DNS 로그 수집 → 비콘 분석 → 비정상 프로세스
2. **execute**: jupyter + Wazuh API + zeek + osquery
3. **synthesize**: 5 산출물 (approach.md / hypothesis.md / dns-findings.csv / beacon-findings.csv / process-findings.csv)

### 도구 비교표 — 헌팅 단계별 도구

| 단계 | 1순위 | 2순위 | 사용 조건 |
|------|-------|-------|----------|
| 가설 정의 | text + ATT&CK | TIBER-EU template | 표준 |
| 데이터 수집 | Wazuh API + OpenSearch | Splunk REST | OSS 우선 |
| 분석 (소규모) | Jupyter + pandas | Excel | 코드 통합 |
| 분석 (대규모) | Spark / Dask | Polars | TB+ |
| 시각화 | Plotly (interactive) | matplotlib | embed |
| 노트북 협업 | git + nbconvert + nbviewer | JupyterHub | 팀 |
| 네트워크 | Zeek + zeek-cut | tcpdump + tshark | depth |
| 호스트 | osquery + auditd | Velociraptor | EDR |
| ML / anomaly | scikit-learn + isolation forest | River (online) | unsupervised |
| 룰 변환 | sigma-cli (week03) | 직접 backend XML | multi-SIEM |
| 캠페인 | git Issues + Notion | JIRA | OSS |
| HMM 평가 | spreadsheet + radar | dedicated tool | 단순 |

### 도구 선택 매트릭스 — 시나리오별 권장

| 시나리오 | 우선 도구 | 이유 |
|---------|---------|------|
| "처음 헌팅 도입" | Jupyter + Wazuh API + ATT&CK | 즉시 시작 |
| "TI 풍부 환경" | IOC 기반 + CDB lookup | 빠른 탐색 |
| "신규 위협 (TI 부족)" | 가설 기반 + Jupyter | depth |
| "대용량 (TB+)" | 데이터 기반 + Spark + ML | 자동 anomaly |
| "Windows 환경" | Hayabusa + EVTX + Sigma | EVTX 강력 |
| "Linux 환경" | osquery + auditd + Zeek | 위 |
| "AD 환경" | BloodHound + ADRecon + Zeek | path |
| "regulator 보고" | HMM 평가 + ATT&CK Coverage | 정량 |

### 학생 셀프 체크리스트 (각 step 완료 기준)

- [ ] s1: 3 접근법 비교 매트릭스
- [ ] s2: DNS 터널링 가설 + 데이터 소스 + 기법 (length + entropy)
- [ ] s3: Wazuh DNS 이벤트 + 도메인 빈도 top 20
- [ ] s4: 비콘 헌팅 — interval CV + plotly 시각화
- [ ] s5: osquery / ps / find 5개 카테고리
- [ ] s6: SSH log + internal-to-internal + 신규 user×host
- [ ] s7: Zeek conn.log 대용량 + entropy 인코딩
- [ ] s8: 5 종 persistence (cron/systemd/.bashrc/kmod/SUID)
- [ ] s9: Jupyter 7-cell 템플릿
- [ ] s10: SIGMA 룰 2개 (DNS + 비콘)
- [ ] s11: ATT&CK Hunting Matrix (10+ technique)
- [ ] s12: 월간 Gantt + RACI
- [ ] s13: 도구 체인 7 단계
- [ ] s14: HMM 5단계 자가진단 + radar + Gap
- [ ] s15: 종합 보고서 (가설 6 + 발견 + SIGMA + HMM + 권고)
- [ ] s99: Bastion 가 5 작업 (접근법/가설/DNS/비콘/프로세스) 순차

### 추가 참조 자료

- **Sqrrl Hunting Maturity Model** Cole, "The Threat Hunting Project" (2016)
- **MITRE ATT&CK Navigator**
- **DeTT&CT** https://github.com/rabobank-cdc/DeTTECT
- **Zeek** https://docs.zeek.org/
- **osquery** https://osquery.io/schema/
- **msticpy** https://github.com/microsoft/msticpy
- **MITRE TRAM** https://github.com/center-for-threat-informed-defense/tram
- **Hayabusa** Yamato Security
- **Velociraptor** OSS EDR + 헌팅
- **TheHive Project**
- **Microsoft Defender Hunting Notebooks** (참고)

위 모든 헌팅 작업은 **격리 lab + 사전 baseline 측정** 으로 수행한다. baseline 없이 anomaly
탐지하면 정상 패턴까지 의심으로 분류 — 7일 baseline 후 헌팅 시작 권장. 운영 환경 적용 시
False positive 측정 (1주 staging) 후 운영 룰 추가. **개인 정보 (사용자명, IP) 가 보고서에
포함되면 anonymization** 후 외부 공유.
