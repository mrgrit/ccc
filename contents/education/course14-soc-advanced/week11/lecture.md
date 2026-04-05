# Week 11: 인시던트 대응 심화

## 학습 목표
- NIST SP 800-61r2 인시던트 대응 프레임워크를 심화 수준으로 이해한다
- 봉쇄(Containment) 전략을 인시던트 유형별로 설계하고 적용할 수 있다
- 디지털 증거를 법적 요건에 맞게 수집하고 보존할 수 있다
- 증거 체인(Chain of Custody)을 관리할 수 있다
- 인시던트 타임라인을 구성하고 근본 원인 분석을 수행할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:50 | NIST IR 심화 + 봉쇄 전략 (Part 1) | 강의 |
| 0:50-1:30 | 증거 수집 + 체인 관리 (Part 2) | 강의/토론 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | IR 시뮬레이션 실습 (Part 3) | 실습 |
| 2:30-3:10 | 근본 원인 분석 + 보고서 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **IR** | Incident Response | 인시던트 대응 | 소방 대응 |
| **봉쇄** | Containment | 피해 확산 방지 조치 | 화재 방화벽 |
| **근절** | Eradication | 위협 요소 완전 제거 | 잔불 진화 |
| **복구** | Recovery | 정상 운영 상태로 복원 | 재건 |
| **증거 체인** | Chain of Custody | 증거의 접근/이동 기록 | 증거물 관리 일지 |
| **포렌식 이미지** | Forensic Image | 디스크/메모리의 비트 단위 복제 | 원본 복사본 |
| **IOC** | Indicator of Compromise | 침해 지표 | 범행 흔적 |
| **RCA** | Root Cause Analysis | 근본 원인 분석 | 화재 원인 조사 |
| **Lessons Learned** | Lessons Learned | 교훈 도출 회의 | 사후 검토 |
| **RACI** | Responsible, Accountable, Consulted, Informed | 역할 책임 매트릭스 | 업무 분담표 |

---

# Part 1: NIST IR 심화 + 봉쇄 전략 (50분)

## 1.1 NIST SP 800-61r2 4단계

```
Phase 1: 준비 (Preparation)
    → IR 팀 구성, 도구 준비, 플레이북 작성
    → "사고 전에 준비하는 단계"

Phase 2: 탐지 및 분석 (Detection & Analysis)
    → 인시던트 식별, 심각도 판정, 범위 파악
    → "사고를 인지하고 파악하는 단계"

Phase 3: 봉쇄, 근절, 복구 (Containment, Eradication, Recovery)
    → 확산 방지, 위협 제거, 시스템 복원
    → "사고를 처리하는 단계"

Phase 4: 사후 활동 (Post-Incident Activity)
    → 교훈 도출, 프로세스 개선, 보고서
    → "사고에서 배우는 단계"
```

## 1.2 봉쇄 전략

### 단기 봉쇄 vs 장기 봉쇄

```
[단기 봉쇄 (Short-term Containment)]
  목적: 즉각적 피해 확산 방지 (분 단위)
  조치:
    - 공격 IP 방화벽 차단
    - 감염 서버 네트워크 격리
    - 침해 계정 비활성화
    - 악성 프로세스 종료
  주의: 증거 보존을 위해 시스템 종료는 최후 수단

[장기 봉쇄 (Long-term Containment)]
  목적: 근절 준비 기간 동안 안전 운영 (시간~일)
  조치:
    - 임시 보안 패치 적용
    - 추가 모니터링 강화
    - 백업 시스템으로 전환
    - 접근 통제 강화
```

### 인시던트 유형별 봉쇄 전략

| 유형 | 단기 봉쇄 | 장기 봉쇄 | 근절 |
|------|----------|----------|------|
| 무차별 대입 | IP 차단, 계정 잠금 | MFA 활성화 | 비밀번호 전체 변경 |
| 웹셸 | 웹서버 격리 | WAF 강화 | 웹셸 제거, 패치 |
| 랜섬웨어 | 네트워크 격리 | 백업 복원 | 전체 재구축 |
| 데이터 유출 | 아웃바운드 차단 | DLP 강화 | 유출 경로 차단 |
| 내부자 위협 | 계정 비활성화 | 감사 로그 강화 | 접근 권한 재검토 |

## 1.3 증거 수집 절차

```bash
# 증거 수집 자동화 스크립트
cat << 'SCRIPT' > /tmp/evidence_collect.sh
#!/bin/bash
# 인시던트 대응 - 증거 수집 스크립트
EVIDENCE_DIR="/tmp/ir_evidence/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EVIDENCE_DIR"

echo "============================================"
echo "  인시던트 대응 - 증거 수집"
echo "  서버: $(hostname)"
echo "  시각: $(date)"
echo "  저장: $EVIDENCE_DIR"
echo "============================================"

# 1. 시스템 정보
echo "=== 1. 시스템 정보 ===" | tee "$EVIDENCE_DIR/01_system_info.txt"
{
    echo "Date: $(date)"
    echo "Hostname: $(hostname)"
    echo "Uptime: $(uptime)"
    echo "Kernel: $(uname -a)"
    echo ""
    echo "=== IP 구성 ==="
    ip addr show 2>/dev/null
    echo ""
    echo "=== 라우팅 ==="
    ip route show 2>/dev/null
} >> "$EVIDENCE_DIR/01_system_info.txt"
echo "  [수집] 시스템 정보"

# 2. 프로세스 목록
ps auxf > "$EVIDENCE_DIR/02_processes.txt" 2>/dev/null
echo "  [수집] 프로세스 목록"

# 3. 네트워크 연결
ss -tnpa > "$EVIDENCE_DIR/03_network_connections.txt" 2>/dev/null
echo "  [수집] 네트워크 연결"

# 4. 사용자 계정
{
    echo "=== /etc/passwd ==="
    cat /etc/passwd
    echo ""
    echo "=== 현재 로그인 ==="
    who
    echo ""
    echo "=== 최근 로그인 ==="
    last -20
} > "$EVIDENCE_DIR/04_users.txt" 2>/dev/null
echo "  [수집] 사용자 정보"

# 5. 크론 작업
{
    echo "=== System crontabs ==="
    ls -la /etc/cron* 2>/dev/null
    echo ""
    for user in root $(awk -F: '$3>=1000{print $1}' /etc/passwd); do
        echo "=== $user crontab ==="
        crontab -l -u "$user" 2>/dev/null || echo "(없음)"
    done
} > "$EVIDENCE_DIR/05_cron.txt" 2>/dev/null
echo "  [수집] 크론 작업"

# 6. 최근 수정된 파일
find / -type f -mmin -60 \
  -not -path "/proc/*" -not -path "/sys/*" -not -path "/dev/*" \
  -not -path "/run/*" 2>/dev/null | head -100 > "$EVIDENCE_DIR/06_recent_files.txt"
echo "  [수집] 최근 수정 파일"

# 7. 로그 수집
cp /var/log/auth.log "$EVIDENCE_DIR/07_auth.log" 2>/dev/null
cp /var/log/syslog "$EVIDENCE_DIR/07_syslog.log" 2>/dev/null
echo "  [수집] 시스템 로그"

# 해시 생성
echo ""
echo "=== 증거 무결성 해시 ==="
cd "$EVIDENCE_DIR"
sha256sum * > "$EVIDENCE_DIR/CHECKSUMS.sha256" 2>/dev/null
cat "$EVIDENCE_DIR/CHECKSUMS.sha256"

echo ""
echo "=== 증거 수집 완료 ==="
echo "총 파일: $(ls "$EVIDENCE_DIR" | wc -l)개"
echo "위치: $EVIDENCE_DIR"
SCRIPT

bash /tmp/evidence_collect.sh
```

> **실습 목적**: 인시던트 발생 시 증거를 체계적으로 수집하는 자동화 스크립트를 실행하고 증거 무결성을 보장한다.
>
> **실전 활용**: 이 스크립트를 USB에 넣어두거나 OpsClaw에 등록해두면 인시던트 발생 시 신속하게 증거를 수집할 수 있다.

---

# Part 2: 증거 수집 + 체인 관리 (40분)

## 2.1 증거 체인(Chain of Custody) 관리

```bash
cat << 'SCRIPT' > /tmp/chain_of_custody.py
#!/usr/bin/env python3
"""증거 체인(Chain of Custody) 관리"""
from datetime import datetime
import json

# 증거 체인 기록
coc = {
    "case_id": "IR-2026-0404-001",
    "incident": "웹서버 침해 (웹셸 발견)",
    "entries": [
        {
            "seq": 1,
            "timestamp": "2026-04-04 10:00:00",
            "action": "최초 인지",
            "person": "SOC L1 분석가 (김분석)",
            "description": "Wazuh 경보로 웹셸 의심 파일 탐지",
        },
        {
            "seq": 2,
            "timestamp": "2026-04-04 10:05:00",
            "action": "에스컬레이션",
            "person": "SOC L2 분석가 (이분석)",
            "description": "L1 분석가로부터 인수, 심화 분석 시작",
        },
        {
            "seq": 3,
            "timestamp": "2026-04-04 10:15:00",
            "action": "증거 수집",
            "person": "SOC L2 분석가 (이분석)",
            "description": "web 서버에서 증거 수집 스크립트 실행",
            "evidence": [
                {"file": "01_system_info.txt", "hash": "sha256:abc123..."},
                {"file": "02_processes.txt", "hash": "sha256:def456..."},
                {"file": "shell.php", "hash": "sha256:789abc..."},
            ],
        },
        {
            "seq": 4,
            "timestamp": "2026-04-04 10:30:00",
            "action": "봉쇄",
            "person": "SOC L2 분석가 (이분석)",
            "description": "웹서버 네트워크 격리, 공격 IP 차단",
        },
        {
            "seq": 5,
            "timestamp": "2026-04-04 11:00:00",
            "action": "증거 이관",
            "person": "SOC L3 분석가 (박분석)",
            "description": "포렌식 분석을 위해 L3에게 증거 이관",
        },
    ],
}

print("=" * 65)
print(f"  증거 체인 (Chain of Custody)")
print(f"  사건: {coc['case_id']}")
print(f"  내용: {coc['incident']}")
print("=" * 65)

for entry in coc["entries"]:
    print(f"\n  [{entry['seq']}] {entry['timestamp']}")
    print(f"      행위: {entry['action']}")
    print(f"      담당: {entry['person']}")
    print(f"      설명: {entry['description']}")
    if "evidence" in entry:
        print(f"      증거물:")
        for ev in entry["evidence"]:
            print(f"        - {ev['file']} ({ev['hash'][:20]}...)")
SCRIPT

python3 /tmp/chain_of_custody.py
```

---

# Part 3: IR 시뮬레이션 실습 (50분)

## 3.1 시나리오: 웹서버 침해 대응

> **시나리오**: web 서버(10.20.30.80)에서 웹셸이 발견되었다. SOC 분석가로서 NIST IR 프레임워크에 따라 대응하라.

```bash
# Phase 2: 탐지 및 분석
echo "============================================"
echo "  IR 시뮬레이션 - Phase 2: 탐지 및 분석"
echo "============================================"

# 웹서버 현황 확인
echo ""
echo "--- 웹서버 프로세스 상태 ---"
sshpass -p1 ssh web@10.20.30.80 "ps aux | grep -E 'apache|nginx|node|http' | head -5" 2>/dev/null

echo ""
echo "--- 의심 파일 검색 ---"
sshpass -p1 ssh web@10.20.30.80 "find /var/www /opt -name '*.php' -newer /etc/hostname 2>/dev/null | head -10" 2>/dev/null

echo ""
echo "--- 최근 SSH 접속 ---"
sshpass -p1 ssh web@10.20.30.80 "last -10" 2>/dev/null

echo ""
echo "--- 외부 네트워크 연결 ---"
sshpass -p1 ssh web@10.20.30.80 "ss -tnp 2>/dev/null | grep ESTAB" 2>/dev/null | head -10
```

## 3.2 Phase 3: 봉쇄 + 근절

```bash
# Phase 3: 봉쇄, 근절, 복구 (OpsClaw 활용)
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "ir-webserver-compromise",
    "request_text": "웹서버 침해 인시던트 대응 - 봉쇄 및 근절",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "IR Project: $PROJECT_ID"

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 봉쇄 조치
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[봉쇄] 의심 파일 검색\" && find /var/www /opt -name \"*.php\" -mtime -7 2>/dev/null | head -5 && echo CONTAINMENT_SEARCH_DONE",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[봉쇄] 방화벽 상태 확인\" && nft list ruleset 2>/dev/null | wc -l && echo FW_CHECK_DONE",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"[분석] Wazuh 최근 경보\" && tail -5 /var/ossec/logs/alerts/alerts.log 2>/dev/null && echo ALERT_CHECK_DONE",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'

sleep 3

# 완료 보고
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "웹서버 침해 IR 봉쇄 단계 완료",
    "outcome": "success",
    "work_details": ["의심 파일 검색", "방화벽 상태 확인", "경보 분석"]
  }'
```

---

# Part 4: 근본 원인 분석 + 보고서 (40분)

## 4.1 타임라인 구성

```bash
cat << 'SCRIPT' > /tmp/ir_timeline.py
#!/usr/bin/env python3
"""인시던트 타임라인 구성"""

timeline = [
    ("2026-04-03 23:30", "RECON", "203.0.113.50 → web:80", "포트 스캔 탐지 (Suricata)"),
    ("2026-04-03 23:45", "ATTACK", "203.0.113.50 → web:80", "SQL Injection 시도 (15회)"),
    ("2026-04-04 00:10", "EXPLOIT", "203.0.113.50 → web:80", "파일 업로드 취약점 악용"),
    ("2026-04-04 00:12", "INSTALL", "web 로컬", "웹셸 설치 (/var/www/uploads/cmd.php)"),
    ("2026-04-04 00:15", "C2", "web → 203.0.113.50:4444", "리버스 셸 연결"),
    ("2026-04-04 00:20", "DISCOVERY", "web 로컬", "whoami, id, cat /etc/passwd"),
    ("2026-04-04 00:30", "LATERAL", "web → siem:22", "SSH 접속 시도 (실패)"),
    ("2026-04-04 01:00", "EXFIL", "web → 203.0.113.50:443", "데이터 전송 (8MB)"),
    ("2026-04-04 10:00", "DETECT", "Wazuh", "SOC L1 경보 확인"),
    ("2026-04-04 10:05", "RESPOND", "SOC", "에스컬레이션 + 봉쇄 시작"),
]

print("=" * 80)
print("  인시던트 타임라인")
print("=" * 80)
print(f"\n{'시각':>20s} {'유형':>8s} {'위치':>25s}  설명")
print("-" * 80)

for time, type_, location, desc in timeline:
    print(f"{time:>20s} [{type_:>7s}] {location:>25s}  {desc}")

# 체류 시간 계산
print(f"\n=== 핵심 지표 ===")
print(f"  최초 침투: 2026-04-04 00:10")
print(f"  최초 탐지: 2026-04-04 10:00")
print(f"  체류 시간(Dwell Time): 약 10시간")
print(f"  MTTD: 10시간")
print(f"  봉쇄 시작: 2026-04-04 10:05")
print(f"  MTTR: 5분 (탐지 후)")
SCRIPT

python3 /tmp/ir_timeline.py
```

## 4.2 근본 원인 분석 (RCA)

```bash
cat << 'SCRIPT' > /tmp/root_cause_analysis.py
#!/usr/bin/env python3
"""근본 원인 분석 (5 Whys)"""

print("=" * 60)
print("  근본 원인 분석 (5 Whys Method)")
print("=" * 60)

whys = [
    ("문제", "웹서버가 침해되었다"),
    ("Why 1", "웹셸이 업로드되었다"),
    ("Why 2", "파일 업로드 기능에 확장자 검증이 없었다"),
    ("Why 3", "개발팀이 보안 코드 리뷰를 하지 않았다"),
    ("Why 4", "보안 코드 리뷰 프로세스가 없었다"),
    ("Why 5", "보안 개발 가이드라인이 수립되지 않았다 (근본 원인)"),
]

for q, a in whys:
    if q == "문제":
        print(f"\n  {q}: {a}")
    elif "근본 원인" in a:
        print(f"  {q}: {a}")
        print(f"         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    else:
        print(f"  {q}: {a}")

print("\n=== 재발 방지 대책 ===")
recommendations = [
    ("즉시", "웹 애플리케이션 파일 업로드 취약점 패치"),
    ("단기 (1주)", "WAF 파일 업로드 검증 룰 강화"),
    ("중기 (1개월)", "보안 코드 리뷰 프로세스 수립"),
    ("장기 (3개월)", "보안 개발 가이드라인 + 교육 프로그램"),
]

for period, action in recommendations:
    print(f"  [{period:15s}] {action}")
SCRIPT

python3 /tmp/root_cause_analysis.py
```

## 4.3 인시던트 보고서 생성

```bash
cat << 'SCRIPT' > /tmp/ir_report.py
#!/usr/bin/env python3
"""인시던트 대응 보고서"""

print("""
================================================================
          인시던트 대응 보고서
================================================================

1. 개요
   사건 번호: IR-2026-0404-001
   일시: 2026-04-03 23:30 ~ 2026-04-04 10:30
   유형: 웹서버 침해 (웹셸 업로드)
   심각도: High
   상태: 봉쇄 완료

2. 영향 범위
   침해 서버: web (10.20.30.80)
   영향 서비스: JuiceShop 웹 애플리케이션
   데이터 유출: 약 8MB (사용자 데이터 포함 여부 확인 중)
   2차 피해: siem 서버 SSH 접속 시도 (실패)

3. 대응 타임라인
   00:10  최초 침투 (파일 업로드 취약점)
   00:12  웹셸 설치
   00:15  C2 통신 시작
   01:00  데이터 유출
   10:00  SOC 탐지 (Wazuh 경보)
   10:05  봉쇄 시작 (IP 차단, 서버 격리)
   10:30  봉쇄 완료

4. IOC
   공격 IP: 203.0.113.50
   웹셸: /var/www/uploads/cmd.php (SHA256: ...)
   C2 포트: 4444
   User-Agent: Python-urllib/3.9

5. 근본 원인
   파일 업로드 기능에 확장자/MIME 검증이 없어
   PHP 웹셸이 업로드됨

6. 재발 방지 대책
   - [즉시] 업로드 취약점 패치
   - [단기] WAF 룰 강화
   - [중기] 보안 코드 리뷰 프로세스 수립
   - [장기] 보안 개발 가이드라인 + 교육

7. 교훈 (Lessons Learned)
   - MTTD 10시간은 개선 필요 → 웹셸 탐지 YARA 룰 추가
   - 파일 업로드 모니터링 Wazuh 룰 부재 → 추가
   - 자동 대응(SOAR) 미적용 → 다음 분기 도입
""")
SCRIPT

python3 /tmp/ir_report.py
```

---

## 체크리스트

- [ ] NIST SP 800-61r2의 4단계를 설명할 수 있다
- [ ] 단기/장기 봉쇄 전략의 차이를 알고 있다
- [ ] 인시던트 유형별 봉쇄 조치를 설계할 수 있다
- [ ] 디지털 증거 수집 스크립트를 실행하고 해시를 기록할 수 있다
- [ ] 증거 체인(Chain of Custody)을 관리할 수 있다
- [ ] 인시던트 타임라인을 구성할 수 있다
- [ ] 5 Whys 기법으로 근본 원인 분석을 수행할 수 있다
- [ ] OpsClaw로 다중 서버 IR 조치를 자동화할 수 있다
- [ ] 인시던트 대응 보고서를 작성할 수 있다
- [ ] Lessons Learned 회의의 목적과 산출물을 알고 있다

---

## 복습 퀴즈

**Q1.** NIST IR 4단계를 순서대로 나열하시오.

<details><summary>정답</summary>
1) 준비(Preparation), 2) 탐지 및 분석(Detection & Analysis), 3) 봉쇄, 근절, 복구(Containment, Eradication, Recovery), 4) 사후 활동(Post-Incident Activity)
</details>

**Q2.** 봉쇄 시 시스템 전원을 끄지 않는 이유는?

<details><summary>정답</summary>
메모리의 휘발성 증거(실행 중인 프로세스, 네트워크 연결, 암호화 키)가 소실되기 때문이다. 전원 차단 대신 네트워크 격리로 봉쇄하고, 메모리 덤프를 먼저 수집해야 한다.
</details>

**Q3.** 증거 수집 후 해시값을 기록하는 이유는?

<details><summary>정답</summary>
증거 무결성을 보장하기 위해서다. 이후 분석이나 법적 절차에서 증거가 변조되지 않았음을 해시값 비교로 증명할 수 있다.
</details>

**Q4.** 체류 시간(Dwell Time)이 길면 어떤 문제가 있는가?

<details><summary>정답</summary>
공격자가 더 많은 시스템에 접근하고, 더 많은 데이터를 유출하며, 지속성을 강화할 시간을 갖게 된다. 체류 시간이 길수록 피해 범위와 복구 비용이 기하급수적으로 증가한다.
</details>

**Q5.** 5 Whys 기법의 목적은?

<details><summary>정답</summary>
표면적 증상이 아닌 근본 원인을 찾기 위해서다. "왜?"를 5번 반복하면 기술적 문제에서 프로세스/조직 문제까지 파고들어 재발 방지를 위한 근본 대책을 수립할 수 있다.
</details>

**Q6.** 인시던트 보고서에 반드시 포함해야 할 5가지 항목은?

<details><summary>정답</summary>
1) 개요(시간, 유형, 심각도), 2) 영향 범위(침해 시스템, 데이터 유출), 3) 대응 타임라인, 4) IOC(공격 지표), 5) 재발 방지 대책
</details>

**Q7.** 랜섬웨어 인시던트에서 단기 봉쇄 조치는?

<details><summary>정답</summary>
감염 서버를 즉시 네트워크에서 격리하여 확산을 방지한다. 네트워크 케이블 분리 또는 방화벽에서 해당 서버의 모든 통신을 차단한다. 전원은 끄지 않는다(증거 보존).
</details>

**Q8.** Lessons Learned 회의의 주요 질문 3가지는?

<details><summary>정답</summary>
1) "무엇이 잘 되었는가?" (유지할 점), 2) "무엇이 잘 안 되었는가?" (개선할 점), 3) "다음에 같은 상황이 발생하면 어떻게 할 것인가?" (대응 절차 개선)
</details>

**Q9.** 증거 체인(Chain of Custody)이 끊기면 어떤 문제가 생기는가?

<details><summary>정답</summary>
법적 절차에서 증거의 진정성(authenticity)이 의심받아 증거 능력을 잃을 수 있다. 누군가가 증거를 변조했을 가능성을 배제할 수 없게 된다.
</details>

**Q10.** OpsClaw를 IR에 활용하는 장점 3가지를 설명하시오.

<details><summary>정답</summary>
1) 여러 서버에 동시에 증거 수집/봉쇄 명령을 실행할 수 있다. 2) 모든 대응 조치가 evidence로 자동 기록되어 감사 추적과 보고서 작성이 용이하다. 3) completion-report로 인시던트 종결 보고서를 체계적으로 생성할 수 있다.
</details>

---

## 과제

### 과제 1: IR 시뮬레이션 (필수)

가상 시나리오 "siem 서버에서 비인가 SSH 접속이 발견됨"에 대해 NIST IR 4단계를 수행하라:
1. 증거 수집 스크립트 실행 + 해시 기록
2. 타임라인 구성
3. 봉쇄 조치 계획 + OpsClaw로 실행
4. 근본 원인 분석 (5 Whys)
5. 인시던트 보고서 작성

### 과제 2: IR 플레이북 작성 (선택)

"랜섬웨어 감염" 시나리오에 대한 IR 플레이북을 작성하라:
1. 단기/장기 봉쇄 절차
2. 증거 수집 절차
3. 복구 절차 (백업 활용)
4. 재발 방지 대책

---

## 보충: IR 고급 절차

### 증거 수집 자동화 (전체 서버)

```bash
# OpsClaw를 활용한 전체 서버 동시 증거 수집
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

cat << 'SCRIPT' > /tmp/mass_evidence_collection.sh
#!/bin/bash
# 대규모 증거 수집 스크립트 (OpsClaw execute-plan용)
EVIDENCE="/tmp/evidence_$(hostname)_$(date +%Y%m%d%H%M%S)"
mkdir -p "$EVIDENCE"

# 1. 휘발성 증거 (우선)
date > "$EVIDENCE/00_collection_time.txt"
hostname >> "$EVIDENCE/00_collection_time.txt"
ps auxf > "$EVIDENCE/01_processes.txt" 2>/dev/null
ss -tnpa > "$EVIDENCE/02_network.txt" 2>/dev/null
who > "$EVIDENCE/03_logged_in.txt" 2>/dev/null
ip addr > "$EVIDENCE/04_ip_config.txt" 2>/dev/null
ip route > "$EVIDENCE/05_routes.txt" 2>/dev/null
arp -an > "$EVIDENCE/06_arp_cache.txt" 2>/dev/null
env > "$EVIDENCE/07_environment.txt" 2>/dev/null

# 2. 비휘발성 증거
last -50 > "$EVIDENCE/10_last_logins.txt" 2>/dev/null
cat /etc/passwd > "$EVIDENCE/11_passwd.txt" 2>/dev/null
cat /etc/group > "$EVIDENCE/12_group.txt" 2>/dev/null
crontab -l > "$EVIDENCE/13_crontab.txt" 2>/dev/null
systemctl list-units --type=service --state=running > "$EVIDENCE/14_services.txt" 2>/dev/null
find / -perm -4000 -type f > "$EVIDENCE/15_suid.txt" 2>/dev/null
find /tmp /var/tmp /dev/shm -type f > "$EVIDENCE/16_tmp_files.txt" 2>/dev/null

# 3. 로그 수집
cp /var/log/auth.log "$EVIDENCE/20_auth.log" 2>/dev/null
cp /var/log/syslog "$EVIDENCE/21_syslog" 2>/dev/null
journalctl --since "24 hours ago" > "$EVIDENCE/22_journal_24h.txt" 2>/dev/null

# 4. 해시 기록
cd "$EVIDENCE"
sha256sum * > CHECKSUMS.sha256 2>/dev/null

echo "증거 수집 완료: $EVIDENCE"
echo "파일 수: $(ls "$EVIDENCE" | wc -l)"
echo "총 크기: $(du -sh "$EVIDENCE" | awk '{print $1}')"
SCRIPT

echo "=== 증거 수집 스크립트 준비 완료 ==="
echo "사용법: OpsClaw execute-plan으로 전체 서버에 배포"

# 실행 (로컬 테스트)
bash /tmp/mass_evidence_collection.sh
```

> **실전 활용**: 이 스크립트를 OpsClaw의 execute-plan에 등록하면 인시던트 발생 시 전체 서버의 증거를 1분 내에 동시 수집할 수 있다. 증거 수집 순서는 RFC 3227의 휘발성 순서를 따른다.

### RACI 매트릭스

```bash
cat << 'SCRIPT' > /tmp/ir_raci.py
#!/usr/bin/env python3
"""인시던트 대응 RACI 매트릭스"""

# R=Responsible, A=Accountable, C=Consulted, I=Informed
raci = {
    "활동": [
        "경보 확인",
        "트리아지",
        "에스컬레이션",
        "심화 분석",
        "봉쇄 결정",
        "봉쇄 실행",
        "포렌식",
        "근절",
        "복구",
        "보고서 작성",
        "경영진 보고",
        "Lessons Learned",
    ],
    "Tier 1": ["R", "R", "R", "I", "I", "I", "I", "I", "I", "C", "I", "C"],
    "Tier 2": ["I", "C", "A", "R", "R", "R", "C", "R", "R", "R", "C", "R"],
    "Tier 3": ["I", "I", "C", "C", "C", "C", "R", "A", "A", "A", "C", "A"],
    "SOC 매니저": ["I", "I", "I", "I", "A", "A", "I", "C", "C", "C", "R", "R"],
    "CISO": ["I", "I", "I", "I", "C", "I", "I", "I", "I", "I", "A", "I"],
}

print("=" * 80)
print("  인시던트 대응 RACI 매트릭스")
print("  R=Responsible, A=Accountable, C=Consulted, I=Informed")
print("=" * 80)

header = f"{'활동':16s} {'Tier 1':>6s} {'Tier 2':>6s} {'Tier 3':>6s} {'매니저':>6s} {'CISO':>6s}"
print(f"\n{header}")
print("-" * 55)

for i, activity in enumerate(raci["활동"]):
    row = f"{activity:16s}"
    for role in ["Tier 1", "Tier 2", "Tier 3", "SOC 매니저", "CISO"]:
        val = raci[role][i]
        row += f" {val:>6s}"
    print(row)
SCRIPT

python3 /tmp/ir_raci.py
```

### 인시던트 심각도 분류 기준

```bash
cat << 'SCRIPT' > /tmp/incident_severity.py
#!/usr/bin/env python3
"""인시던트 심각도 분류 기준"""

severity_matrix = {
    "P1 (Critical)": {
        "기준": "핵심 서비스 중단 또는 대규모 데이터 유출",
        "예시": "랜섬웨어 감염, 고객 DB 유출, 핵심 서버 장악",
        "대응 시간": "즉시 (15분 내 봉쇄 시작)",
        "에스컬레이션": "SOC 매니저 + CISO + 법률팀",
        "교대": "24/7 전담 팀 구성",
    },
    "P2 (High)": {
        "기준": "공격 진행 중이나 핵심 서비스 영향 없음",
        "예시": "웹셸 발견, 내부 서버 측면 이동, C2 통신",
        "대응 시간": "1시간 내 봉쇄",
        "에스컬레이션": "SOC 매니저",
        "교대": "업무 시간 집중 대응",
    },
    "P3 (Medium)": {
        "기준": "공격 시도 확인, 성공 여부 불확실",
        "예시": "무차별 대입, 포트 스캔, SQL Injection 시도",
        "대응 시간": "4시간 내 분석 완료",
        "에스컬레이션": "Tier 2 분석가",
        "교대": "정상 업무 내 처리",
    },
    "P4 (Low)": {
        "기준": "정상 활동의 변형, 위험도 낮음",
        "예시": "정책 위반, 비인가 소프트웨어, 설정 오류",
        "대응 시간": "24시간 내",
        "에스컬레이션": "불필요",
        "교대": "정상 업무 내 처리",
    },
}

print("=" * 60)
print("  인시던트 심각도 분류 기준")
print("=" * 60)

for level, info in severity_matrix.items():
    print(f"\n  --- {level} ---")
    for key, value in info.items():
        print(f"    {key}: {value}")
SCRIPT

python3 /tmp/incident_severity.py
```

### 포렌식 이미지 수집 절차

```bash
cat << 'SCRIPT' > /tmp/forensic_imaging.py
#!/usr/bin/env python3
"""포렌식 이미지 수집 절차"""

print("""
================================================================
  포렌식 이미지 수집 절차
================================================================

1. 디스크 이미지 수집 (dd/dcfldd)

   # 원본 디스크 → 이미지 파일
   dcfldd if=/dev/sda of=/evidence/disk_image.dd \\
     hash=sha256 hashlog=/evidence/disk_hash.log \\
     hashwindow=1G

   # 압축 이미지 (용량 절감)
   dd if=/dev/sda bs=4M | gzip > /evidence/disk_image.dd.gz

   # 해시 기록
   sha256sum /evidence/disk_image.dd > /evidence/disk_image.dd.sha256

2. 메모리 이미지 수집 (LiME)

   # LiME 모듈 로드
   insmod lime-$(uname -r).ko \\
     "path=/evidence/memory.lime format=lime"

   # 해시 기록
   sha256sum /evidence/memory.lime > /evidence/memory.lime.sha256

3. 증거 보존

   # 읽기 전용 마운트
   mount -o ro,loop /evidence/disk_image.dd /mnt/evidence/

   # 해시 검증
   sha256sum -c /evidence/disk_image.dd.sha256

4. 증거 보관

   # 암호화 보관
   gpg -c /evidence/disk_image.dd
   # → disk_image.dd.gpg

   # 이중 보관 (원본 + 사본)
   rsync -av /evidence/ /backup/evidence/
""")
SCRIPT

python3 /tmp/forensic_imaging.py
```

### 인시던트 대응 자동화 스크립트 라이브러리

```bash
cat << 'SCRIPT' > /tmp/ir_scripts_library.py
#!/usr/bin/env python3
"""IR 자동화 스크립트 라이브러리"""

scripts = {
    "ip_block.sh": {
        "용도": "공격 IP 방화벽 차단",
        "사용": "./ip_block.sh <IP>",
        "내용": "nft add rule ip filter input ip saddr $1 drop",
    },
    "account_lock.sh": {
        "용도": "침해 계정 잠금",
        "사용": "./account_lock.sh <username>",
        "내용": "usermod -L $1 && passwd -l $1",
    },
    "evidence_collect.sh": {
        "용도": "증거 수집 (휘발성 우선)",
        "사용": "./evidence_collect.sh",
        "내용": "ps, ss, who, last, 로그 수집 + 해시",
    },
    "timeline_build.sh": {
        "용도": "파일 시스템 타임라인 구축",
        "사용": "./timeline_build.sh /",
        "내용": "find / -printf '%T+ %p\\n' | sort",
    },
    "ioc_scan.sh": {
        "용도": "IOC 일괄 검색",
        "사용": "./ioc_scan.sh ioc_list.txt",
        "내용": "grep -rF -f ioc_list.txt /var/log/",
    },
    "snapshot_system.sh": {
        "용도": "시스템 상태 스냅샷",
        "사용": "./snapshot_system.sh",
        "내용": "프로세스, 네트워크, 사용자, cron, 서비스 전체 기록",
    },
}

print("=" * 60)
print("  IR 자동화 스크립트 라이브러리")
print("=" * 60)

for name, info in scripts.items():
    print(f"\n  --- {name} ---")
    print(f"    용도: {info['용도']}")
    print(f"    사용: {info['사용']}")
    print(f"    내용: {info['내용']}")

print("""
배포 위치:
  /opt/ir-toolkit/scripts/
  OpsClaw Playbook으로 등록 가능

사용 원칙:
  1. 실행 전 반드시 해시 확인 (변조 방지)
  2. 결과는 중앙 저장소에 자동 업로드
  3. 실행 로그는 별도 기록
""")
SCRIPT

python3 /tmp/ir_scripts_library.py
```

### 인시던트 커뮤니케이션 템플릿

```bash
cat << 'SCRIPT' > /tmp/ir_communication.py
#!/usr/bin/env python3
"""인시던트 커뮤니케이션 템플릿"""

templates = {
    "초기 알림 (Slack)": """
[INCIDENT] IR-2026-XXXX - {severity}
시각: {time}
유형: {type}
영향: {impact}
상태: 조사 중
담당: {assignee}
다음 업데이트: 30분 후
""",
    "경영진 보고 (이메일)": """
제목: [보안 인시던트] {type} - {severity}

1. 현황: {status}
2. 영향: {impact}
3. 조치: {actions}
4. 예상 복구: {eta}
5. 다음 보고: {next_update}
""",
    "종결 알림 (Slack)": """
[RESOLVED] IR-2026-XXXX
종결 시각: {time}
대응 시간: {response_time}
결과: {outcome}
후속: Lessons Learned 예정
""",
}

print("=" * 60)
print("  인시던트 커뮤니케이션 템플릿")
print("=" * 60)

for name, template in templates.items():
    print(f"\n  --- {name} ---")
    print(template)
SCRIPT

python3 /tmp/ir_communication.py
```

### 인시던트 대응 테이블탑 연습(TTX) 가이드

```bash
cat << 'SCRIPT' > /tmp/ttx_guide.py
#!/usr/bin/env python3
"""인시던트 대응 테이블탑 연습(TTX) 가이드"""

print("""
================================================================
  테이블탑 연습(TTX) 운영 가이드
================================================================

1. 목적
   → IR 프로세스와 의사결정 능력을 검증
   → 실제 시스템을 건드리지 않는 토론 기반 연습

2. 참가자
   → SOC 팀 (Tier 1/2/3)
   → SOC 매니저
   → IT 운영팀 대표
   → (선택) 경영진, 법률, HR, PR

3. 시나리오 예시

   [시나리오 A: 랜섬웨어]
   "금요일 오후 5시, 회계팀에서 파일이 열리지 않는다고 보고.
    확인 결과 다수 파일이 .encrypted로 변경됨.
    몸값 요구 메모가 바탕화면에 생성됨."

   질문:
   - 누가 가장 먼저 알림을 받아야 하는가?
   - 어떤 서버를 우선 격리해야 하는가?
   - 백업에서 복구 가능한가?
   - 몸값을 지불해야 하는가?
   - 고객에게 어떻게 알릴 것인가?

   [시나리오 B: 공급망 공격]
   "월요일 아침, 자동 업데이트 서버에서 배포된 패키지에
    백도어가 포함되어 있다는 외부 제보를 받음."

   질문:
   - 해당 패키지를 설치한 서버를 어떻게 식별하는가?
   - 공급망 전체를 차단해야 하는가?
   - 이미 실행된 백도어를 어떻게 탐지하는가?

4. 진행 절차
   0:00-0:10  시나리오 브리핑
   0:10-0:30  Phase 1 상황 제시 + 토론
   0:30-0:50  Phase 2 상황 악화 + 의사결정
   0:50-1:10  Phase 3 복구/보고 + 토론
   1:10-1:30  교훈 도출 + 개선 사항

5. 평가 기준
   - 의사결정 속도와 적절성
   - 팀 간 소통 효과성
   - 에스컬레이션 정확성
   - 증거 보존 인식
   - 커뮤니케이션 적절성
""")
SCRIPT

python3 /tmp/ttx_guide.py
```

---

## 다음 주 예고

**Week 12: 로그 엔지니어링**에서는 커스텀 디코더 작성, 로그 파서 개발, 정규화, 보존 정책을 학습한다.
