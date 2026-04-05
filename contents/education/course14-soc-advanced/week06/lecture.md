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
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:50 | 위협 헌팅 이론 + 방법론 (Part 1) | 강의 |
| 0:50-1:30 | ATT&CK 매핑 + 베이스라인 (Part 2) | 강의/토론 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | 헌팅 실습 - 프로세스/네트워크 (Part 3) | 실습 |
| 2:30-3:10 | 헌팅 결과 문서화 + 룰 전환 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

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

echo "=== opsclaw 서버 베이스라인 ==="
bash /tmp/baseline_collect.sh

echo ""
echo "=== web 서버 베이스라인 ==="
sshpass -p1 ssh web@10.20.30.80 'bash -s' < /tmp/baseline_collect.sh 2>/dev/null | head -50
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

echo "=== opsclaw 서버 프로세스 헌팅 ==="
bash /tmp/hunt_process.sh

echo ""
echo "=== secu 서버 프로세스 헌팅 ==="
sshpass -p1 ssh secu@10.20.30.1 'bash -s' < /tmp/hunt_process.sh 2>/dev/null

echo ""
echo "=== web 서버 프로세스 헌팅 ==="
sshpass -p1 ssh web@10.20.30.80 'bash -s' < /tmp/hunt_process.sh 2>/dev/null
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
for server in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
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
sshpass -p1 ssh secu@10.20.30.1 'bash -s' < /tmp/hunt_network.sh 2>/dev/null
```

## 3.4 OpsClaw 자동화 헌팅

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 헌팅 프로젝트 생성
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "threat-hunting-campaign",
    "request_text": "ATT&CK T1053.003(Cron) 기반 지속성 헌팅",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Project: $PROJECT_ID"

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 전체 서버 동시 헌팅
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
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
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PROJECT_ID/evidence/summary" | \
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
            "description": "secu 서버에 OpsClaw 관련 cron 작업 존재 (정상)",
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
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

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

## 복습 퀴즈

**Q1.** 위협 헌팅과 인시던트 대응의 가장 큰 차이점은?

<details><summary>정답</summary>
위협 헌팅은 경보가 없는 상태에서 분석가가 능동적으로 위협을 찾는 활동이고, 인시던트 대응은 경보나 사고 발생 후 반응적으로 처리하는 활동이다. 헌팅은 "경보를 만드는 활동"이고, IR은 "경보에 반응하는 활동"이다.
</details>

**Q2.** 가설 기반 헌팅의 4가지 가설 유형을 설명하시오.

<details><summary>정답</summary>
1) 인텔리전스 기반: 외부 TI 보고서에서 영감. 2) 상황 인식 기반: 조직 내부 상황(퇴사, 합병 등). 3) ATT&CK 기반: 특정 기법의 존재 여부. 4) 이상 징후 기반: 데이터에서 발견된 이상 패턴.
</details>

**Q3.** "Living off the Land" 공격이 헌팅에서 중요한 이유는?

<details><summary>정답</summary>
시스템 기본 도구(bash, curl, python 등)를 악용하므로 시그니처 기반 탐지로는 잡을 수 없다. 정상 도구의 비정상 사용 패턴을 찾아야 하므로 헌팅이 필수적이다.
</details>

**Q4.** 베이스라인이 없으면 헌팅이 어려운 이유는?

<details><summary>정답</summary>
"정상"이 무엇인지 모르면 "비정상"을 판단할 수 없기 때문이다. 예: 프로세스 50개가 정상인지 비정상인지, cron 작업 10개가 원래 있었는지 새로 생긴 것인지 판단할 기준이 없다.
</details>

**Q5.** /tmp에서 실행 파일이 발견된 경우 어떤 추가 분석을 해야 하는가?

<details><summary>정답</summary>
1) 파일 해시 계산 후 VirusTotal 검색, 2) strings 명령으로 내용 확인, 3) 생성 시각과 사용자 확인(stat), 4) 관련 프로세스가 실행 중인지 확인(ps), 5) 네트워크 연결 여부 확인(ss/netstat).
</details>

**Q6.** crontab이 수정되었을 때 정상/악성을 구분하는 기준은?

<details><summary>정답</summary>
1) 변경 관리 기록에 해당 변경이 있는지, 2) cron 작업의 내용이 정당한 업무인지, 3) 실행되는 스크립트가 알려진 것인지, 4) 실행 경로가 /tmp 등 비정상인지, 5) 외부 서버와 통신하는지 확인한다.
</details>

**Q7.** HMM(Hunting Maturity Model) Level 3의 특징은?

<details><summary>정답</summary>
가설 기반 자체 헌팅을 수행하며, 데이터 분석 역량을 보유하고, 새로운 TTP를 발견할 수 있는 수준이다. 외부 IOC 검색을 넘어서 독자적인 헌팅 캠페인을 운영한다.
</details>

**Q8.** 헌팅 결과를 탐지 룰로 전환하는 이유는?

<details><summary>정답</summary>
수동 헌팅으로 발견한 위협 패턴을 자동화하여, 같은 위협이 다시 발생하면 경보가 자동으로 울리게 하기 위해서다. 이를 통해 SOC의 탐지 커버리지가 지속적으로 확대된다.
</details>

**Q9.** T1036(Masquerading) 기법을 헌팅할 때 확인해야 할 것은?

<details><summary>정답</summary>
1) 프로세스명과 실제 바이너리 경로가 일치하는지(예: sshd인데 /tmp에서 실행), 2) 부모-자식 관계가 정상인지(예: apache → bash는 비정상), 3) 파일 해시가 원본과 일치하는지 확인한다.
</details>

**Q10.** OpsClaw를 헌팅에 활용하는 장점은?

<details><summary>정답</summary>
여러 서버에 동일한 헌팅 쿼리를 동시에 실행하고 결과를 중앙에서 수집/비교할 수 있다. evidence 기능으로 헌팅 이력이 자동 기록되어 감사 추적이 가능하다.
</details>

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
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

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
