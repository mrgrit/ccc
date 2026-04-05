# Week 12: 블루팀 운영 — SOC 구축, SIEM, SOAR 자동화, IR 플레이북

## 학습 목표
- SOC(Security Operations Center)의 Tier 1/2/3 구조와 운영 프로세스를 이해한다
- Wazuh SIEM을 활용하여 실시간 보안 모니터링과 알림 규칙을 구성할 수 있다
- SOAR(Security Orchestration, Automation and Response) 자동화 플레이북을 설계할 수 있다
- 인시던트 대응(IR) 절차의 6단계를 실행하고 문서화할 수 있다
- OpsClaw를 SOAR 엔진으로 활용하여 보안 대응을 자동화할 수 있다
- 공격 탐지-분석-대응의 전체 사이클을 실습 환경에서 수행할 수 있다

## 전제 조건
- Week 11 레드팀 운영 이수 완료
- MITRE ATT&CK 프레임워크 이해
- Wazuh 기본 개념 (에이전트, 매니저, 규칙)
- 네트워크 보안 기본 (방화벽, IDS/IPS, 로그 분석)
- OpsClaw execute-plan, dispatch API 사용 경험

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane / SOAR 엔진 | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (JuiceShop, Apache) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh 4.11.2) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`
**Wazuh API:** `https://10.20.30.100:55000` (admin/admin)

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: SOC 아키텍처와 운영 프로세스 | 강의 |
| 0:40-1:20 | Part 2: Wazuh SIEM 심화 — 규칙, 디코더, 알림 | 강의/실습 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: SOAR 자동화와 OpsClaw 연동 | 실습 |
| 2:10-2:50 | Part 4: 인시던트 대응(IR) 실전 시뮬레이션 | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:20 | IR 보고서 작성 + 교훈 토론 | 토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOC** | Security Operations Center | 보안 운영 센터 — 24/7 모니터링 | 비행기 관제탑 |
| **SIEM** | Security Information and Event Management | 보안 이벤트 수집/분석/상관 분석 | 범죄 수사 데이터베이스 |
| **SOAR** | Security Orchestration, Automation and Response | 보안 자동화 오케스트레이션 | 자동화된 응급 대응 시스템 |
| **IR** | Incident Response | 보안 인시던트 대응 절차 | 화재 대응 절차 |
| **Playbook** | 대응 절차서 | 특정 인시던트에 대한 단계별 대응 절차 | 응급 처치 매뉴얼 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인) | 범죄 증거물 |
| **Triage** | 분류/우선순위 결정 | 알림의 심각도와 긴급도 분류 | 응급실 환자 분류 |
| **False Positive** | 오탐 | 정상 활동을 공격으로 잘못 탐지 | 화재 오경보 |
| **MTTD** | Mean Time to Detect | 평균 탐지 시간 | 화재 발견 시간 |
| **MTTR** | Mean Time to Respond | 평균 대응 시간 | 화재 진압 시간 |
| **Sigma** | Sigma 규칙 | SIEM 독립적 탐지 규칙 형식 | 범용 범죄 수배 양식 |
| **Enrichment** | 보강/풍부화 | 알림에 추가 컨텍스트(GeoIP, 위협 인텔) 부가 | 수사 보고서 보충 |

---

# Part 1: SOC 아키텍처와 운영 프로세스 (40분)

## 1.1 SOC의 구조

SOC(Security Operations Center)는 조직의 **보안 이벤트를 24/7 모니터링하고 대응**하는 중앙 조직이다.

### SOC Tier 구조

```
+--------------------------------------------------+
|                    SOC 계층 구조                    |
+--------------------------------------------------+
|                                                    |
|  Tier 3: 고급 분석가 (Threat Hunter)               |
|  +------------------------------------+            |
|  | - 고급 위협 헌팅, 멀웨어 분석        |            |
|  | - 신규 탐지 규칙 개발                |            |
|  | - APT 분석, 포렌식                  |            |
|  +--------------------+---------------+            |
|                       | 에스컬레이션                 |
|  Tier 2: 인시던트 대응 전문가                        |
|  +--------------------+---------------+            |
|  | - 심층 분석, 상관 분석               |            |
|  | - IR 절차 실행, 억제/격리            |            |
|  | - 근본 원인 분석                     |            |
|  +--------------------+---------------+            |
|                       | 에스컬레이션                 |
|  Tier 1: 모니터링 분석가                             |
|  +--------------------+---------------+            |
|  | - 알림 모니터링, 초기 분류(Triage)   |            |
|  | - 오탐/실탐 판단, 티켓 생성          |            |
|  | - 기본 대응(차단, 격리)              |            |
|  +------------------------------------+            |
+--------------------------------------------------+
```

### Tier별 역할과 도구

| Tier | 역할 | 주요 도구 | 대응 시간 | 인력 비율 |
|------|------|----------|----------|----------|
| **Tier 1** | 모니터링, 초기 분류 | SIEM 대시보드, 티켓 시스템 | 15분 이내 | 60% |
| **Tier 2** | 심층 분석, IR 실행 | SIEM, EDR, 네트워크 포렌식 | 1시간 이내 | 30% |
| **Tier 3** | 위협 헌팅, 규칙 개발 | 멀웨어 분석, OSINT, 커스텀 도구 | 비동기 | 10% |

## 1.2 SOC 운영 프로세스

### 알림 처리 워크플로

```
이벤트 발생 → SIEM 수집 → 상관 분석 → 알림 생성
                                        |
                                        ▼
                                  Tier 1: Triage
                                   +- 오탐 → 닫기
                                   +- 정보성 → 기록
                                   +- 실탐 → Tier 2 에스컬레이션
                                              |
                                              ▼
                                        Tier 2: 분석/대응
                                         +- 억제 (Containment)
                                         +- 근본 원인 분석
                                         +- 복구 + 보고서
```

### 핵심 SOC 메트릭

| 메트릭 | 설명 | 목표 값 | 계산 방법 |
|--------|------|---------|----------|
| **MTTD** | 평균 탐지 시간 | < 1시간 | 공격 시작 → 첫 알림 |
| **MTTR** | 평균 대응 시간 | < 4시간 | 알림 → 억제 완료 |
| **오탐률** | False Positive 비율 | < 20% | 오탐 수 / 전체 알림 수 |
| **에스컬레이션률** | Tier 2로 올라간 비율 | 30-50% | Tier 2 건수 / Tier 1 건수 |
| **알림 커버리지** | ATT&CK 기법 탐지율 | > 60% | 탐지 기법 수 / 전체 기법 수 |

## 1.3 SIEM의 핵심 기능

| 기능 | 설명 | Wazuh 구현 |
|------|------|-----------|
| **로그 수집** | 다양한 소스에서 로그 수집 | Wazuh Agent → Manager |
| **정규화** | 다른 형식의 로그를 통일 | Decoder 규칙 |
| **상관 분석** | 여러 이벤트를 연결하여 패턴 탐지 | Correlation 규칙 |
| **알림 생성** | 탐지 조건 충족 시 알림 | Rules (level 1-16) |
| **대시보드** | 시각적 모니터링 | Wazuh Dashboard (OpenSearch) |
| **보고서** | 정기/임시 보고서 생성 | Wazuh Reports |

## 1.4 Wazuh 아키텍처 심화

### Wazuh 구성 요소

```
+----------------------------------------------+
|              Wazuh SIEM 아키텍처               |
|                                              |
|  Agent ----▶ Manager ----▶ Indexer           |
|  (수집)       (분석)        (저장/검색)        |
|                |                             |
|                ▼                             |
|           Dashboard                          |
|           (시각화)                             |
|                                              |
|  Agent 배포:                                  |
|  - web (10.20.30.80): 웹 서버 로그            |
|  - secu (10.20.30.1): 방화벽/IPS 로그         |
|  - opsclaw (10.20.30.201): 시스템 로그        |
+----------------------------------------------+
```

### Wazuh 규칙 레벨

| 레벨 | 의미 | 예시 | SOC 대응 |
|------|------|------|---------|
| 0-4 | 시스템/디버그 | 서비스 시작/종료 | 무시 |
| 5-7 | 정보/낮은 위험 | 로그인 성공, 파일 변경 | 기록 |
| 8-10 | 중간 위험 | 인증 실패 5회, 비정상 프로세스 | Tier 1 확인 |
| 11-13 | 높은 위험 | 권한 상승 시도, 웹 공격 탐지 | Tier 2 분석 |
| 14-16 | 치명적 | 루트킷 탐지, 대량 데이터 유출 | 즉시 대응 |

---

# Part 2: Wazuh SIEM 심화 — 규칙, 디코더, 알림 (40분)

## 2.1 Wazuh 규칙 구조

Wazuh 규칙은 **XML 기반**으로, 로그 패턴을 매칭하여 알림을 생성한다.

### 규칙 예시: SQL Injection 탐지

```xml
<!-- /var/ossec/etc/rules/local_rules.xml -->
<group name="web,attack,sqli">
  <rule id="100001" level="12">
    <if_group>web</if_group>
    <url>rest/products/search</url>
    <match>UNION|SELECT|OR 1=1|DROP TABLE|INSERT INTO</match>
    <description>SQL Injection attempt detected on JuiceShop</description>
    <mitre>
      <id>T1190</id>
    </mitre>
    <group>attack,sqli,</group>
  </rule>
</group>
```

### 규칙 작성 요소

| 요소 | 설명 | 예시 |
|------|------|------|
| `id` | 고유 규칙 ID (100000+: 커스텀) | 100001 |
| `level` | 심각도 (0-16) | 12 (높은 위험) |
| `if_group` | 전제 조건 그룹 | web |
| `match` | 패턴 매칭 (정규식 가능) | UNION\|SELECT |
| `url` | URL 패턴 | rest/products/search |
| `description` | 알림 설명 | SQL Injection 탐지 |
| `mitre` | ATT&CK 매핑 | T1190 |

## 2.2 Wazuh 디코더

디코더는 **원시 로그를 구조화된 필드로 파싱**하는 역할을 한다.

### Apache 접근 로그 디코더 예시

```xml
<!-- /var/ossec/etc/decoders/local_decoder.xml -->
<decoder name="apache-access-custom">
  <parent>apache-access</parent>
  <regex>(\S+) \S+ \S+ \[(.+?)\] "(\S+) (\S+) \S+" (\d+) (\d+)</regex>
  <order>srcip,timestamp,method,url,status,size</order>
</decoder>
```

### 주요 디코더 필드

| 필드 | 설명 | 활용 |
|------|------|------|
| `srcip` | 출발지 IP | GeoIP 조회, 차단 |
| `url` | 요청 URL | 공격 패턴 매칭 |
| `status` | HTTP 상태 코드 | 성공/실패 판단 |
| `method` | HTTP 메서드 | 비정상 메서드 탐지 |
| `user` | 사용자 ID | 계정 이상 탐지 |

## 2.3 Sigma 규칙과 호환성

Sigma는 **SIEM 독립적인 탐지 규칙 형식**이다. Wazuh, Splunk, ELK 등 다양한 SIEM으로 변환할 수 있다.

### Sigma 규칙 예시

```yaml
title: SQL Injection via Web Application
id: a1234567-b890-cdef-1234-567890abcdef
status: experimental
description: Detects SQL injection attempts in web server logs
logsource:
    category: webserver
    product: apache
detection:
    selection:
        cs-uri-query|contains:
            - 'UNION SELECT'
            - 'OR 1=1'
            - "' OR '"
            - 'DROP TABLE'
    condition: selection
falsepositives:
    - Legitimate SQL queries in URL parameters
level: high
tags:
    - attack.initial_access
    - attack.t1190
```

### Sigma → Wazuh 변환

| Sigma 필드 | Wazuh 매핑 | 설명 |
|-----------|-----------|------|
| `detection.selection` | `<match>` 또는 `<regex>` | 탐지 패턴 |
| `level: high` | `level="12"` | 심각도 매핑 |
| `logsource.product` | `<if_group>` | 로그 소스 |
| `tags` | `<mitre><id>` | ATT&CK 매핑 |

---

# Part 3: SOAR 자동화와 OpsClaw 연동 (40분)

## 실습 3.1: Wazuh 알림 확인 및 분석

> **실습 목적**: Wazuh SIEM에서 발생한 보안 알림을 확인하고 분류(Triage)하는 SOC Tier 1 업무를 체험한다.
>
> **배우는 것**: Wazuh 알림 로그의 구조, 알림 심각도 분류 방법, 오탐/실탐 판단 기준을 이해한다.
>
> **결과 해석**: level 10 이상의 알림이 존재하면 실제 공격 가능성이 높다. 동일 IP에서 반복된 알림은 자동화 공격을 의미한다.
>
> **실전 활용**: SOC Tier 1 분석관의 핵심 업무이다. 신속한 Triage 능력이 MTTD를 좌우한다.

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 1. Wazuh 최근 알림 확인
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week12-blueteam-soc",
    "request_text": "블루팀 SOC 운영: Wazuh 알림 분석 및 SOAR 자동화",
    "master_mode": "external"
  }' | python3 -m json.tool
# PROJECT_ID 메모
```

```bash
export PROJECT_ID="반환된-프로젝트-ID"

curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# Wazuh 알림 수집 및 분석
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== SOC Tier 1: Wazuh 알림 수집 ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \"tail -50 /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \\\"import sys,json; [print(json.dumps({\\x27level\\x27:json.loads(l).get(\\x27rule\\x27,{}).get(\\x27level\\x27), \\x27desc\\x27:json.loads(l).get(\\x27rule\\x27,{}).get(\\x27description\\x27,\\x27\\x27)[:60], \\x27src\\x27:json.loads(l).get(\\x27data\\x27,{}).get(\\x27srcip\\x27,\\x27-\\x27)})) for l in sys.stdin if l.strip()]\\\" 2>/dev/null | tail -20 || echo No alerts\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== SOC Tier 1: Suricata IPS 알림 ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"tail -30 /var/log/suricata/fast.log 2>/dev/null | tail -15 || echo No Suricata alerts\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== SOC Tier 1: 웹 서버 에러 로그 ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -20 /var/log/apache2/error.log 2>/dev/null | tail -10 || echo No errors\"; echo \"---\"; echo \"=== 접근 로그 이상 패턴 ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -100 /var/log/apache2/access.log 2>/dev/null | grep -iE \\\"union|select|script|alert|../|etc/passwd\\\" | tail -10 || echo No suspicious patterns\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - task 1: Wazuh alerts.json에서 level, description, srcip를 추출하여 Triage용 요약 생성
> - task 2: Suricata fast.log에서 IPS 탐지 알림을 확인
> - task 3: Apache 에러 로그와 접근 로그에서 공격 시그니처 패턴을 검색
>
> **트러블슈팅**: alerts.json이 비어있으면 Wazuh 에이전트가 비활성 상태이다. `ssh siem "systemctl status wazuh-manager"`로 확인한다.

## 실습 3.2: SOAR 자동화 플레이북 — OpsClaw 연동

> **실습 목적**: OpsClaw를 SOAR 엔진으로 활용하여 "SQL Injection 탐지 시 자동 차단" 플레이북을 구현한다.
>
> **배우는 것**: SOAR 플레이북의 구조(트리거→분석→대응→통보), OpsClaw execute-plan으로 자동화 플레이북을 구현하는 방법, 방화벽 규칙 동적 추가를 이해한다.
>
> **결과 해석**: 플레이북이 성공적으로 실행되면 공격 IP가 방화벽에 차단되고, SIEM에 대응 기록이 남고, 관리자에게 통보된다.
>
> **실전 활용**: SOAR 자동화는 MTTR을 크게 단축한다. 반복적인 대응을 자동화하면 Tier 1 분석관의 피로를 줄이고 고급 분석에 집중할 수 있다.

```bash
# SOAR 플레이북: SQL Injection 탐지 시 자동 대응
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== SOAR Step 1: 트리거 — SQLi 탐지 확인 ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -100 /var/log/apache2/access.log 2>/dev/null | grep -iE \\\"union|select.*from|or 1=1\\\" | tail -5 || echo No SQLi detected\"; echo \"탐지 시각: $(date +%Y-%m-%d_%H:%M:%S)\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== SOAR Step 2: 분석 — 공격 IP 추출 ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -200 /var/log/apache2/access.log 2>/dev/null | grep -iE \\\"union|select.*from|or 1=1\\\" | awk '{print \\$1}' | sort | uniq -c | sort -rn | head -5 || echo No attacking IPs found\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== SOAR Step 3: 대응 — 방화벽 규칙 확인 (dry-run) ===\"; echo \"[DRY-RUN] nft add rule inet filter input ip saddr {공격IP} drop\"; echo \"실제 차단은 수동 확인 후 실행합니다.\"; echo \"---\"; echo \"현재 nftables 규칙:\"; sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"nft list ruleset 2>/dev/null | head -20 || echo nftables not available\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"=== SOAR Step 4: 통보 — 대응 기록 생성 ===\"; echo \"[SOAR 보고서]\"; echo \"시각: $(date +%Y-%m-%d_%H:%M:%S)\"; echo \"유형: SQL Injection 탐지\"; echo \"대상: web (10.20.30.80)\"; echo \"조치: 공격 IP 식별, 방화벽 차단 준비\"; echo \"상태: 분석 완료, 차단 대기\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - Step 1 (트리거): Apache 로그에서 SQLi 패턴을 탐지하여 플레이북을 기동
> - Step 2 (분석): 공격 IP를 추출하고 빈도 분석하여 주요 공격원 식별
> - Step 3 (대응): nftables 방화벽 규칙 추가를 dry-run으로 확인 (안전을 위해 실제 차단은 수동)
> - Step 4 (통보): 구조화된 대응 보고서를 생성하여 evidence에 기록
>
> **트러블슈팅**: Apache 로그에 SQLi 패턴이 없으면 Week 11 실습을 먼저 수행하여 공격 로그를 생성한다. nftables가 없으면 iptables를 대안으로 사용한다.

## 실습 3.3: 커스텀 Wazuh 탐지 규칙 작성

> **실습 목적**: Wazuh에 커스텀 탐지 규칙을 추가하여 특정 공격 패턴(SQLi, 브루트포스)을 실시간 탐지한다.
>
> **배우는 것**: Wazuh 규칙 XML 문법, 규칙 레벨 설정 기준, ATT&CK 매핑 방법, 규칙 테스트 절차를 이해한다.
>
> **결과 해석**: 규칙을 추가한 후 공격을 재실행했을 때 Wazuh 알림이 생성되면 규칙이 올바르게 동작하는 것이다.
>
> **실전 활용**: SOC Tier 3 분석관의 핵심 업무가 탐지 규칙 개발이다. 새로운 공격 기법에 대한 규칙을 신속히 개발하는 능력이 조직의 보안 성숙도를 결정한다.

```bash
# Wazuh 커스텀 규칙 확인 (SIEM 서버)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== Wazuh 현재 규칙 확인 ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \"cat /var/ossec/etc/rules/local_rules.xml 2>/dev/null | head -30 || echo No custom rules\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== 규칙 추가 예시 (참고용) ===\"; echo \"아래 규칙을 /var/ossec/etc/rules/local_rules.xml에 추가:\"; echo; echo \"<group name=\\\"web,sqli\\\">\"; echo \"  <rule id=\\\"100001\\\" level=\\\"12\\\">\"; echo \"    <if_group>web</if_group>\"; echo \"    <match>UNION SELECT|OR 1=1|DROP TABLE</match>\"; echo \"    <description>SQL Injection attempt detected</description>\"; echo \"    <mitre><id>T1190</id></mitre>\"; echo \"  </rule>\"; echo \"</group>\"; echo; echo \"규칙 추가 후: systemctl restart wazuh-manager\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== Wazuh 규칙 테스트 ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \"/var/ossec/bin/wazuh-logtest 2>/dev/null <<< '10.20.30.201 - - [01/Apr/2026:10:00:00 +0900] \\\"GET /rest/products/search?q=UNION+SELECT+1,2,3 HTTP/1.1\\\" 200 1234' 2>/dev/null | tail -10 || echo logtest not available\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - task 1: 현재 Wazuh 커스텀 규칙 파일의 내용을 확인한다
> - task 2: SQLi 탐지 커스텀 규칙의 XML 구조를 표시한다 (참고용)
> - task 3: wazuh-logtest로 규칙이 올바르게 매칭되는지 테스트한다
>
> **트러블슈팅**: wazuh-logtest가 없으면 Wazuh 버전을 확인한다 (`/var/ossec/bin/wazuh-control info`). 규칙 문법 오류 시 XML 유효성을 검사한다.

---

# Part 4: 인시던트 대응(IR) 실전 시뮬레이션 (40분)

## 4.1 IR 6단계 프로세스 (NIST SP 800-61)

| 단계 | 활동 | SOC Tier | OpsClaw 매핑 |
|------|------|---------|-------------|
| **1. 준비 (Preparation)** | IR 계획, 도구 준비, 훈련 | 전체 | 프로젝트 생성, 환경 확인 |
| **2. 식별 (Identification)** | 인시던트 탐지, 분류 | Tier 1 | 알림 수집, Triage |
| **3. 억제 (Containment)** | 피해 확산 방지 | Tier 2 | 방화벽 차단, 격리 |
| **4. 근절 (Eradication)** | 근본 원인 제거 | Tier 2/3 | 멀웨어 제거, 패치 |
| **5. 복구 (Recovery)** | 정상 운영 복귀 | Tier 2 | 서비스 재시작, 검증 |
| **6. 교훈 (Lessons Learned)** | 사후 분석, 개선 | 전체 | completion-report |

## 실습 4.2: IR 시뮬레이션 — SQL Injection 인시던트 대응

> **실습 목적**: 실제 SQL Injection 인시던트를 시뮬레이션하고 IR 6단계를 실행한다.
>
> **배우는 것**: 인시던트 대응의 전체 사이클, 각 단계의 구체적 행동, 의사결정 과정, 문서화 방법을 이해한다.
>
> **결과 해석**: 모든 6단계가 순서대로 완료되고, 각 단계의 결과가 evidence에 기록되면 IR 절차가 올바르게 수행된 것이다.
>
> **실전 활용**: 이 IR 절차는 NIST SP 800-61 표준에 기반하며, 실제 기업 SOC에서 사용하는 것과 동일한 구조이다.

```bash
# IR 시뮬레이션 프로젝트
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week12-ir-simulation",
    "request_text": "IR 시뮬레이션: SQL Injection 인시던트 대응 6단계",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export PROJECT_ID2="반환된-프로젝트-ID"

curl -s -X POST http://localhost:8000/projects/$PROJECT_ID2/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID2/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# IR 6단계 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID2/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== IR Step 1: 준비 (Preparation) ===\"; echo \"IR 계획: SQLi 인시던트 대응\"; echo \"도구: Wazuh, Suricata, nftables, OpsClaw\"; echo \"팀: Tier 1(모니터링), Tier 2(분석/대응)\"; echo \"통신 채널: OpsClaw Slack #bot-cc\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== IR Step 2: 식별 (Identification) ===\"; echo \"[알림 확인]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -50 /var/log/apache2/access.log 2>/dev/null | grep -iE \\\"union|select|or 1=1|script\\\" | wc -l\" 2>/dev/null; echo \"건의 의심스러운 요청 발견\"; echo \"---\"; echo \"[공격 IP]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -200 /var/log/apache2/access.log 2>/dev/null | grep -iE \\\"union|select|or 1=1\\\" | awk '{print \\$1}' | sort -u\" 2>/dev/null || echo \"IP 추출 실패\"; echo \"---\"; echo \"[판정] 실제 SQL Injection 공격으로 분류\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== IR Step 3: 억제 (Containment) ===\"; echo \"[단기 억제] 공격 IP 차단 (dry-run)\"; echo \"  nft add rule inet filter input ip saddr {공격IP} drop\"; echo \"[장기 억제] WAF 규칙 강화\"; echo \"  JuiceShop search 파라미터에 입력 검증 추가 필요\"; echo \"---\"; echo \"현재 방화벽 상태:\"; sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"nft list ruleset 2>/dev/null | grep -c rule || echo 0\"; echo \"개의 규칙 활성\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"=== IR Step 4: 근절 (Eradication) ===\"; echo \"[근본 원인] JuiceShop search API의 입력 검증 부재\"; echo \"[수정 방안]\"; echo \"  1. Prepared Statement 사용 (SQLi 근본 해결)\"; echo \"  2. WAF에 SQLi 시그니처 규칙 추가\"; echo \"  3. 입력값 화이트리스트 필터링\"; echo \"[데이터 무결성 확인]\"; echo \"  DB 백업과 현재 데이터 비교 필요\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "echo \"=== IR Step 5: 복구 (Recovery) ===\"; echo \"[서비스 상태 확인]\"; curl -s -o /dev/null -w \"JuiceShop: HTTP %{http_code}\" http://10.20.30.80:3000 2>/dev/null; echo; echo \"[정상 기능 검증]\"; curl -s \"http://10.20.30.80:3000/rest/products/search?q=apple\" 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f\\\"정상 검색: {len(d.get(\\x27data\\x27,[]))}건\\\")\" 2>/dev/null; echo \"[모니터링 강화] 향후 72시간 집중 모니터링\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 6,
        "instruction_prompt": "echo \"=== IR Step 6: 교훈 (Lessons Learned) ===\"; echo \"[타임라인]\"; echo \"  탐지: Wazuh 알림 + Apache 로그 분석\"; echo \"  분류: SQL Injection (T1190) 확인\"; echo \"  대응: IP 차단 준비, WAF 강화 권고\"; echo \"[개선 사항]\"; echo \"  1. Wazuh SQLi 전용 규칙 추가\"; echo \"  2. SOAR 자동 차단 플레이북 구현\"; echo \"  3. 개발팀 보안 교육 (Prepared Statement)\"; echo \"[메트릭]\"; echo \"  MTTD: ~15분 (수동 분석)\"; echo \"  MTTR: ~30분 (dry-run 포함)\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - Step 1-6: NIST SP 800-61의 IR 6단계를 순서대로 실행
> - Step 2: 실제 로그에서 공격 증거를 추출하여 인시던트를 식별
> - Step 3: 방화벽 차단을 dry-run으로 확인 (안전)
> - Step 5: 서비스 정상 복구 여부를 HTTP 응답 코드와 정상 검색으로 검증
> - Step 6: MTTD/MTTR 메트릭을 산출하여 성과를 측정
>
> **트러블슈팅**: Apache 로그에 공격 흔적이 없으면 Week 11 실습에서 생성된 것이 만료된 것이다. 간단한 SQLi 테스트를 실행하여 로그를 생성한 후 재시도한다.

```bash
# IR 완료 보고서 생성
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID2/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "SQL Injection 인시던트 대응 시뮬레이션 완료. IR 6단계 전 과정 수행.",
    "outcome": "success",
    "work_details": [
      "Step 1 준비: IR 계획, 도구, 팀 구성 확인",
      "Step 2 식별: Apache 로그에서 SQLi 패턴 탐지, 공격 IP 추출",
      "Step 3 억제: 방화벽 차단 규칙 준비 (dry-run)",
      "Step 4 근절: 근본 원인(입력 검증 부재) 식별, Prepared Statement 권고",
      "Step 5 복구: 서비스 정상 동작 확인, 72시간 모니터링 계획",
      "Step 6 교훈: MTTD ~15분, MTTR ~30분, 개선 사항 3건 도출"
    ]
  }' | python3 -m json.tool
```

> **명령어 해설**: `completion-report`로 IR 시뮬레이션의 최종 보고서를 생성한다. work_details에 각 IR 단계의 핵심 결과를 기록한다.
>
> **트러블슈팅**: "stage transition not allowed" 시 프로젝트 상태를 `GET /projects/{id}`로 확인하고 필요한 단계 전환을 수행한다.

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] SOC Tier 1/2/3의 역할과 에스컬레이션 기준을 설명할 수 있는가?
- [ ] SIEM의 핵심 기능 6가지(수집, 정규화, 상관분석, 알림, 대시보드, 보고서)를 설명할 수 있는가?
- [ ] Wazuh 규칙의 XML 구조를 이해하고 커스텀 규칙을 작성할 수 있는가?
- [ ] Sigma 규칙의 구조와 Wazuh 변환 방법을 이해하는가?
- [ ] SOAR 플레이북의 4단계(트리거→분석→대응→통보)를 설계할 수 있는가?
- [ ] NIST IR 6단계를 순서대로 나열하고 각 단계의 활동을 설명할 수 있는가?
- [ ] MTTD와 MTTR의 차이와 측정 방법을 설명할 수 있는가?
- [ ] OpsClaw를 SOAR 엔진으로 활용하여 자동 대응 플레이북을 구현할 수 있는가?
- [ ] Wazuh 알림 레벨(0-16)의 의미와 SOC 대응 매핑을 이해하는가?
- [ ] IR 시뮬레이션 결과를 completion-report로 문서화할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** SOC에서 "알림의 초기 분류(Triage)"를 담당하는 계층은?
- (a) Tier 3  (b) Tier 2  (c) **Tier 1**  (d) CISO

**Q2.** MTTD가 의미하는 것은?
- (a) 평균 복구 시간  (b) **평균 탐지 시간 (공격 시작→첫 알림)**  (c) 평균 대응 시간  (d) 평균 분석 시간

**Q3.** Wazuh 규칙에서 level 14는 어떤 심각도인가?
- (a) 정보  (b) 중간  (c) 높음  (d) **치명적**

**Q4.** SOAR의 핵심 가치는?
- (a) 로그 저장  (b) **반복적 보안 대응의 자동화로 MTTR 단축**  (c) 취약점 스캔  (d) 비밀번호 관리

**Q5.** NIST IR 6단계에서 "피해 확산을 방지하는 단계"는?
- (a) 식별  (b) 준비  (c) **억제 (Containment)**  (d) 복구

**Q6.** Sigma 규칙의 가장 큰 장점은?
- (a) XML 기반  (b) **SIEM 독립적 — 다양한 SIEM으로 변환 가능**  (c) 무료  (d) 자동 학습

**Q7.** SOC 메트릭에서 "오탐률" 20%의 의미는?
- (a) 80%가 미탐지  (b) **전체 알림의 20%가 실제 공격이 아닌 정상 활동**  (c) 20%만 탐지  (d) 대응률 20%

**Q8.** OpsClaw에서 SOAR 플레이북의 "트리거"에 해당하는 것은?
- (a) 프로젝트 생성  (b) **보안 알림 탐지 (SIEM 알림, 로그 패턴)**  (c) API 키 설정  (d) PoW 검증

**Q9.** IR의 "교훈(Lessons Learned)" 단계에서 반드시 포함해야 하는 것은?
- (a) 범인 체포  (b) **MTTD/MTTR 측정, 개선 사항 도출, 문서화**  (c) 시스템 포맷  (d) 법적 소송

**Q10.** Wazuh 디코더의 핵심 역할은?
- (a) 알림 생성  (b) 대시보드 표시  (c) **원시 로그를 구조화된 필드로 파싱**  (d) 로그 삭제

**정답:** Q1:c, Q2:b, Q3:d, Q4:b, Q5:c, Q6:b, Q7:b, Q8:b, Q9:b, Q10:c

---

## 과제

### 과제 1: Wazuh 커스텀 규칙 세트 개발 (필수)
다음 공격 유형 각각에 대한 Wazuh 탐지 규칙을 작성하라:
- SQL Injection (level 12, ATT&CK T1190)
- XSS (level 10, ATT&CK T1059.007)
- 브루트포스 (level 11, ATT&CK T1110)
- 디렉토리 트래버설 (level 10, ATT&CK T1083)
- 각 규칙에 대한 테스트 로그와 예상 알림을 포함하라

### 과제 2: SOAR 플레이북 3종 설계 (필수)
다음 인시던트 유형별 SOAR 플레이북을 설계하라:
- (A) 브루트포스 공격 탐지 시: 계정 잠금 + IP 차단 + 관리자 통보
- (B) 웹 공격 탐지 시: WAF 규칙 강화 + 로그 분석 + 보고서 생성
- (C) 내부 이상 행위 탐지 시: 세션 종료 + 감사 로그 수집 + 에스컬레이션
- 각 플레이북을 OpsClaw execute-plan 형식으로 구현하라

### 과제 3: SOC 성숙도 평가 (선택)
실습 환경의 SOC 성숙도를 다음 기준으로 평가하라:
- MTTD/MTTR 현재 수준과 목표 수준
- ATT&CK 탐지 커버리지 (14개 전술 중 몇 개를 탐지 가능한가)
- 자동화 수준 (수동 vs SOAR 자동화 비율)
- 개선 로드맵을 3단계로 제시하라

---

## 다음 주 예고

**Week 13: 퍼플팀 — Red+Blue 협업, ATT&CK Gap 분석, 탐지 규칙 개선**
- 퍼플팀의 개념과 Red/Blue 팀 협업 방법론
- ATT&CK 기반 탐지 Gap 분석 수행
- 공격 결과를 바탕으로 탐지 규칙 개선
- 보안 성숙도 측정과 개선 계획 수립
