# Week 06: 경보 분석 (2) - 실전 + ATT&CK 매핑

## 학습 목표
- 실제 공격 로그를 분석하고 공격 유형을 식별할 수 있다
- MITRE ATT&CK 프레임워크의 구조를 이해한다
- 탐지된 경보를 ATT&CK 전술/기법에 매핑할 수 있다
- 킬 체인 관점에서 공격 흐름을 재구성할 수 있다

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
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

---

## 용어 해설 (보안관제/SOC 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOC** | Security Operations Center | 보안 관제 센터 (24/7 모니터링) | 경찰 112 상황실 |
| **관제** | Monitoring/Surveillance | 보안 이벤트를 실시간 감시하는 활동 | CCTV 관제 |
| **경보** | Alert | 보안 이벤트가 탐지 규칙에 매칭되어 발생한 알림 | 화재 경보기 울림 |
| **이벤트** | Event | 시스템에서 발생한 모든 활동 기록 | 일어난 일 하나하나 |
| **인시던트** | Incident | 보안 정책을 위반한 이벤트 (실제 위협) | 실제 화재 발생 |
| **오탐** | False Positive | 정상 활동을 공격으로 잘못 탐지 | 화재 경보기가 요리 연기에 울림 |
| **미탐** | False Negative | 실제 공격을 놓침 | 도둑이 CCTV에 안 잡힘 |
| **TTD** | Time to Detect | 공격 발생~탐지까지 걸리는 시간 | 화재 발생~경보 울림 시간 |
| **TTR** | Time to Respond | 탐지~대응까지 걸리는 시간 | 경보~소방차 도착 시간 |
| **SIGMA** | SIGMA | SIEM 벤더에 무관한 범용 탐지 룰 포맷 | 국제 표준 수배서 양식 |
| **Tier 1/2/3** | SOC Tiers | 관제 인력 수준 (L1:모니터링, L2:분석, L3:전문가) | 일반의→전문의→교수 |
| **트리아지** | Triage | 경보를 우선순위별로 분류하는 작업 | 응급실 환자 분류 |
| **플레이북** | Playbook (IR) | 인시던트 유형별 대응 절차 매뉴얼 | 화재 대응 매뉴얼 |
| **포렌식** | Forensics | 사이버 범죄 수사를 위한 증거 수집·분석 | 범죄 현장 감식 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 도메인, 해시) | 수배범의 지문, 차량번호 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술·기법·절차 | 범인의 범행 수법 |
| **위협 헌팅** | Threat Hunting | 탐지 룰에 걸리지 않는 위협을 능동적으로 찾는 활동 | 잠복 수사 |
| **syslog** | syslog | 시스템 로그를 원격 전송하는 프로토콜 (UDP 514) | 모든 부서 보고서를 본사로 모으는 시스템 |

---

# Week 06: 경보 분석 (2) - 실전 + ATT&CK 매핑

## 학습 목표

- 실제 공격 로그를 분석하고 공격 유형을 식별할 수 있다
- MITRE ATT&CK 프레임워크의 구조를 이해한다
- 탐지된 경보를 ATT&CK 전술/기법에 매핑할 수 있다
- 킬 체인 관점에서 공격 흐름을 재구성할 수 있다

---

## 1. MITRE ATT&CK 프레임워크

### 1.1 ATT&CK이란?

**ATT&CK** = Adversarial Tactics, Techniques, and Common Knowledge

- 실제 사이버 공격에서 관찰된 전술/기법을 체계적으로 정리한 지식 기반
- https://attack.mitre.org
- SOC, Red/Blue Team에서 사실상의 표준으로 사용

### 1.2 구조

```
전술 (Tactic)          = "공격자의 목표" (WHY)
  +-- 기법 (Technique)     = "목표 달성 방법" (HOW)
      +-- 하위 기법 (Sub-technique) = "구체적 구현"
```

### 1.3 Enterprise ATT&CK 14개 전술

| ID | 전술 | 설명 | 예시 |
|----|------|------|------|
| TA0001 | 초기 접근 (Initial Access) | 시스템 침입 | 피싱, 취약점 악용 |
| TA0002 | 실행 (Execution) | 코드 실행 | 명령줄, 스크립트 |
| TA0003 | 지속성 (Persistence) | 재접근 확보 | 백도어, cron 등록 |
| TA0004 | 권한 상승 (Privilege Escalation) | 높은 권한 획득 | sudo 악용, 커널 취약점 |
| TA0005 | 방어 회피 (Defense Evasion) | 탐지 회피 | 로그 삭제, 난독화 |
| TA0006 | 자격 증명 접근 (Credential Access) | 인증 정보 탈취 | 비밀번호 크래킹 |
| TA0007 | 탐색 (Discovery) | 환경 파악 | 포트 스캔, 계정 조회 |
| TA0008 | 측면 이동 (Lateral Movement) | 다른 시스템 침투 | SSH, RDP |
| TA0009 | 수집 (Collection) | 데이터 수집 | 파일 수집 |
| TA0010 | 유출 (Exfiltration) | 데이터 유출 | HTTP, DNS 터널링 |
| TA0011 | 명령 및 제어 (C2) | 원격 조종 | 리버스 셸 |
| TA0040 | 영향 (Impact) | 시스템 파괴 | 랜섬웨어, 데이터 삭제 |
| TA0042 | 정찰 (Reconnaissance) | 사전 정보 수집 | OSINT |
| TA0043 | 자원 개발 (Resource Dev.) | 공격 인프라 준비 | 도메인 등록, 악성코드 제작 |

---

## 2. 실제 공격 로그 분석

> **이 실습을 왜 하는가?**
> "경보 분석 (2) - 실전 + ATT&CK 매핑" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안관제/SOC 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 시나리오: SSH 무차별 대입 → 권한 상승

> **실습 목적**: 실전 공격 시나리오의 경보를 MITRE ATT&CK 전술에 매핑하여 공격 체인을 분석한다
>
> **배우는 것**: SSH 무차별 대입, 권한 상승 등 다단계 공격의 경보를 ATT&CK 매트릭스에 매핑하는 방법을 배운다
>
> **결과 해석**: 여러 전술(정찰→초기접근→권한상승)에 걸친 경보가 연속 발생하면 다단계 공격이 진행 중이다
>
> **실전 활용**: SOC L2 분석가는 개별 경보를 ATT&CK 기반 킬 체인으로 연결하여 공격 전체 그림을 파악한다

```bash
# 1단계: 정찰 (Reconnaissance) - TA0043
# 포트 스캔 흔적
sshpass -p1 ssh secu@10.20.30.1 "grep -i 'scan' /var/log/suricata/fast.log 2>/dev/null | tail -5"

# 2단계: 초기 접근 (Initial Access) - TA0001
# SSH 무차별 대입 공격
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -5"

# 무차별 대입 후 성공 여부
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Accepted password' /var/log/auth.log 2>/dev/null | tail -5"

# 3단계: 실행 (Execution) - TA0002
# 로그인 후 실행된 명령 (auth.log에서 sudo 사용 확인)
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'sudo:' /var/log/auth.log 2>/dev/null | tail -10"

# 4단계: 권한 상승 (Privilege Escalation) - TA0004
# sudo를 통한 root 권한 획득
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'COMMAND=' /var/log/auth.log 2>/dev/null | tail -10"
```

### 2.2 시나리오: 웹 공격 체인

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 1단계: 정찰 - 디렉토리 스캐닝
sshpass -p1 ssh web@10.20.30.80 "grep ' 404 ' /var/log/nginx/access.log 2>/dev/null | \
  awk '{print \$1}' | sort | uniq -c | sort -rn | head -5"  # 텍스트 필드 처리

# 2단계: 초기 접근 - SQL Injection 시도
sshpass -p1 ssh web@10.20.30.80 "grep -iE 'union|select.*from|or.1=1' /var/log/nginx/access.log 2>/dev/null | tail -5"  # 비밀번호 자동입력 SSH

# 3단계: Suricata에서 웹 공격 탐지
sshpass -p1 ssh secu@10.20.30.1 "grep -i 'SQL\|XSS\|injection\|web' /var/log/suricata/fast.log 2>/dev/null | tail -10"  # 비밀번호 자동입력 SSH

# 4단계: Wazuh에서 웹 공격 경보
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"  # 비밀번호 자동입력 SSH
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        groups = r.get('groups',[])
        if 'web' in str(groups) or 'attack' in str(groups):
            print(f'  [{r.get(\"level\",0)}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -10"
```

---

## 3. ATT&CK 매핑 실습

### 3.1 Wazuh의 ATT&CK 매핑

Wazuh는 일부 규칙에 MITRE ATT&CK ID를 포함하고 있다.

```bash
# ATT&CK 매핑이 있는 경보 확인
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"  # 비밀번호 자동입력 SSH
import sys, json
from collections import Counter
techniques = Counter()
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        mitre = r.get('mitre',{})
        for tech in mitre.get('technique',[]):         # 반복문 시작
            techniques[tech] += 1
        for tid in mitre.get('id',[]):                 # 반복문 시작
            techniques[tid] += 1
    except: pass
if techniques:
    print('=== ATT&CK 기법별 통계 ===')
    for tech, cnt in techniques.most_common(15):       # 반복문 시작
        print(f'  {cnt:4d}건: {tech}')
else:
    print('ATT&CK 매핑된 경보가 없거나 mitre 필드 미포함')
\" 2>/dev/null"
```

### 3.2 수동 ATT&CK 매핑

경보에 ATT&CK 매핑이 없어도, 분석원이 직접 매핑할 수 있다:

| 경보 유형 | ATT&CK 전술 | ATT&CK 기법 |
|-----------|------------|------------|
| SSH 인증 실패 다수 | 자격증명 접근 (TA0006) | Brute Force (T1110) |
| SSH 로그인 성공 (외부IP) | 초기 접근 (TA0001) | Valid Accounts (T1078) |
| sudo 실행 | 권한 상승 (TA0004) | Abuse Elevation Control (T1548) |
| 파일 변경 탐지 | 지속성 (TA0003) | Modify System Process (T1543) |
| 포트 스캔 | 탐색 (TA0007) | Network Service Discovery (T1046) |
| SQL Injection | 초기 접근 (TA0001) | Exploit Public-Facing App (T1190) |
| 로그 파일 삭제 | 방어 회피 (TA0005) | Indicator Removal (T1070) |
| 대량 데이터 전송 | 유출 (TA0010) | Exfiltration Over C2 (T1041) |

---

## 4. 킬 체인 분석

### 4.1 Cyber Kill Chain (Lockheed Martin)

```
1. 정찰 (Reconnaissance)     → 포트 스캔, 정보 수집
2. 무기화 (Weaponization)     → 악성코드 제작
3. 배달 (Delivery)            → 피싱, 웹 취약점 악용
4. 악용 (Exploitation)        → 취약점 실행
5. 설치 (Installation)        → 백도어 설치
6. 명령/제어 (C2)              → 원격 조종
7. 목표 달성 (Actions)         → 데이터 유출, 파괴
```

### 4.2 실습: 킬 체인 재구성

```bash
# 실습 환경에서 관찰 가능한 킬 체인 단계를 추적

echo "=== 1. 정찰 단계 ==="
echo "포트 스캔 흔적:"
sshpass -p1 ssh secu@10.20.30.1 "grep -i 'scan' /var/log/suricata/fast.log 2>/dev/null | wc -l"  # 비밀번호 자동입력 SSH

echo ""
echo "=== 2. 초기 접근 시도 ==="
echo "SSH 무차별 대입:"
sshpass -p1 ssh opsclaw@10.20.30.201 "grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo '0'"  # 비밀번호 자동입력 SSH
echo "웹 공격 시도:"
sshpass -p1 ssh web@10.20.30.80 "grep -cE 'union|select|script' /var/log/nginx/access.log 2>/dev/null || echo '0'"  # 비밀번호 자동입력 SSH

echo ""
echo "=== 3. 초기 접근 성공 ==="
echo "외부IP SSH 로그인 성공:"
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Accepted' /var/log/auth.log 2>/dev/null | grep -v '192.168.208' | head -5"  # 비밀번호 자동입력 SSH

echo ""
echo "=== 4. 권한 상승 ==="
echo "sudo 사용:"
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'COMMAND=' /var/log/auth.log 2>/dev/null | tail -5"  # 비밀번호 자동입력 SSH

echo ""
echo "=== 5. 지속성 확보 (의심) ==="
echo "cron 변경:"
sshpass -p1 ssh opsclaw@10.20.30.201 "ls -la /var/spool/cron/crontabs/ 2>/dev/null"  # 비밀번호 자동입력 SSH
echo "SSH authorized_keys:"
sshpass -p1 ssh opsclaw@10.20.30.201 "ls -la ~/.ssh/authorized_keys 2>/dev/null || echo '없음'"  # 비밀번호 자동입력 SSH
```

---

## 5. ATT&CK Navigator 활용

### 5.1 ATT&CK Navigator란?

ATT&CK 매트릭스를 시각화하는 도구이다.
https://mitre-attack.github.io/attack-navigator/

### 5.2 실습: 관찰된 기법 매핑

지금까지 실습 환경에서 탐지한 기법을 정리한다:

```
관찰된 ATT&CK 기법:
- T1110 Brute Force (SSH 무차별 대입)
- T1078 Valid Accounts (로그인 성공)
- T1046 Network Service Discovery (포트 스캔)
- T1190 Exploit Public-Facing App (웹 공격)
- T1548 Abuse Elevation Control (sudo)
```

ATT&CK Navigator에서 해당 기법에 색상을 표시하여 "우리 환경의 위협 맵"을 만든다.

---

## 6. 종합 분석 보고서

### 6.1 양식

```
=== 공격 분석 보고서 ===
분석일: 2026-03-27
분석원: (이름)

[공격 개요]
- 공격 유형: (SSH 무차별 대입 / 웹 공격 등)
- 공격 기간: YYYY-MM-DD HH:MM ~ YYYY-MM-DD HH:MM
- 출발지: X.X.X.X
- 대상: (서버명/IP)

[킬 체인 분석]
1. 정찰: (관찰 내용)
2. 무기화: (해당 없음 / 정보 없음)
3. 배달: (공격 방법)
4. 악용: (취약점 이용 내용)
5. 설치: (관찰 내용)
6. C2: (관찰 내용)
7. 목표: (성공/실패)

[ATT&CK 매핑]
| 전술 | 기법 ID | 기법명 | 증거 |
|------|---------|--------|------|
| TA0006 | T1110 | Brute Force | auth.log 실패 150건 |
| ... | ... | ... | ... |

[판정]
- TP / FP 판정 및 근거
- 공격 성공 여부
- 피해 범위

[권고사항]
- 즉시 조치
- 단기 개선
- 중장기 개선
```

---

## 7. 핵심 정리

1. **ATT&CK** = 전술(WHY) → 기법(HOW) → 하위기법 체계
2. **14개 전술** = 정찰부터 영향까지 공격의 전 단계
3. **킬 체인** = 공격의 시간순 흐름을 재구성
4. **매핑** = 경보를 ATT&CK 기법에 연결하여 공격 맥락 파악
5. **상관 분석** = 여러 경보를 연결하여 전체 공격 그림 파악

---

## 과제

1. 실습 환경의 Wazuh/Suricata 경보를 분석하여 ATT&CK 매핑 표를 작성하시오
2. 관찰된 공격 시나리오를 킬 체인으로 재구성하시오
3. 공격 분석 보고서를 작성하시오

---

## 참고 자료

- MITRE ATT&CK (https://attack.mitre.org)
- ATT&CK Navigator (https://mitre-attack.github.io/attack-navigator/)
- Lockheed Martin Cyber Kill Chain

---

---

## 심화: 보안관제(SOC) 실무 보충

### 경보 분석 워크플로

```
[1단계] 경보 수신
    → Wazuh Dashboard에서 경보 확인
    → 심각도(level), 출처(src), 대상(dst) 즉시 파악

[2단계] 초기 분류 (Triage, 5분 이내)
    → 오탐(False Positive)인가? → 기존 사례와 비교
    → 실제 위협인가? → IOC 확인 (악성 IP, 해시)
    → 긴급도 결정: P1(즉시) / P2(4시간) / P3(24시간) / P4(일반)

[3단계] 심층 분석 (Investigation)
    → 관련 로그 추가 수집 (시간 범위 확대)
    → ATT&CK 기법 매핑
    → 영향 범위 파악 (어떤 서버, 어떤 데이터)

[4단계] 대응 (Response)
    → 격리: 감염 서버 네트워크 분리
    → 차단: 공격자 IP 방화벽 차단
    → 복구: 백업에서 복원, 패치 적용

[5단계] 사후 분석 (Post-Incident)
    → 타임라인 작성 (attack→detect→respond→recover)
    → 탐지 룰 개선
    → 보고서 작성
```

### Wazuh 로그 분석 실습

원격 서버에 접속하여 명령을 실행합니다.

```bash
# siem 서버에서 최근 경보 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 "  # 비밀번호 자동입력 SSH
  echo '=== 최근 경보 (level >= 7) ==='
  sudo cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | \
    python3 -c '                                       # Python 코드 실행
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line.strip())
        if a.get("rule",{}).get("level",0) >= 7:
            print(f"[{a[\"rule\"][\"level\"]}] {a[\"rule\"].get(\"description\",\"?\")[:60]} src={a.get(\"srcip\",\"?\")}")
    except: pass
' 2>/dev/null | tail -10
" 2>/dev/null
```

### SIGMA 룰 작성 가이드

```yaml
# SIGMA 룰 기본 구조
title: SSH Brute Force Detection     # 룰 이름
id: 12345678-abcd-efgh-...           # 고유 ID (UUID)
status: experimental                  # experimental/test/stable
description: |                        # 상세 설명
    5분 내 동일 IP에서 10회 이상 SSH 인증 실패 탐지
author: Student Name                  # 작성자
date: 2026/03/27                      # 작성일

logsource:                            # 어떤 로그를 볼 것인가
    product: linux
    service: sshd

detection:                            # 어떤 패턴을 찾을 것인가
    selection:
        eventid: 4625                 # 또는 sshd 실패 이벤트
    filter:                           # 제외 조건
        srcip: "10.20.30.*"           # 내부 IP는 제외
    condition: selection and not filter
    timeframe: 5m                     # 시간 범위
    count: 10                         # 최소 횟수

level: high                           # 심각도
tags:                                 # ATT&CK 매핑
    - attack.credential_access
    - attack.t1110.001
falsepositives:                       # 오탐 가능성
    - 자동화 스크립트의 반복 접속
    - 비밀번호 정책 변경 후 재접속
```

### TTD/TTR 측정 실습

```bash
# 공격→탐지 시간(TTD) 측정 시나리오
echo "=== 공격 시작 시각 기록 ==="
ATTACK_TIME=$(date +%s)
echo "공격 시작: $(date)"

# (여기서 공격 실행)

echo "=== SIEM 경보 확인 ==="
# (경보 발생 시각 확인)
DETECT_TIME=$(date +%s)
TTD=$((DETECT_TIME - ATTACK_TIME))
echo "TTD (탐지 소요 시간): ${TTD}초"
```

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** SOC에서 False Positive(오탐)란?
- (a) 공격을 정확히 탐지  (b) **정상 활동을 공격으로 잘못 탐지**  (c) 공격을 놓침  (d) 로그 미수집

**Q2.** SIGMA 룰의 핵심 장점은?
- (a) 특정 SIEM에서만 동작  (b) **SIEM 벤더에 독립적인 범용 포맷**  (c) 자동 차단 기능  (d) 로그 압축

**Q3.** TTD(Time to Detect)를 줄이기 위한 방법은?
- (a) 경보를 비활성화  (b) **실시간 경보 규칙 최적화 + 자동화**  (c) 분석 인력 감축  (d) 로그 보관 기간 단축

**Q4.** 인시던트 대응 NIST 6단계에서 첫 번째는?
- (a) 탐지(Detection)  (b) **준비(Preparation)**  (c) 격리(Containment)  (d) 근절(Eradication)

**Q5.** Wazuh logtest의 용도는?
- (a) 서버 성능 측정  (b) **탐지 룰을 실제 배포 전에 테스트**  (c) 네트워크 속도 측정  (d) 디스크 점검

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): Wazuh alerts.json/logtest/agent_control, SIGMA 룰, 경보 분석
