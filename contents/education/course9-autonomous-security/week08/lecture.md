# Week 08: 중간고사 — 자율 보안 점검 CTF

## 학습 목표
- Week 01~07의 지식을 종합하여 실전 보안 점검 CTF를 수행한다
- OpsClaw의 프로젝트 생명주기, execute-plan, PoW, RL을 통합 활용한다
- 4대 서버에 대한 종합 보안 점검을 병렬로 실행할 수 있다
- 시간 내에 최대한 많은 Flag를 획득하는 전략을 수립·실행한다
- CTF 결과를 evidence 기반으로 분석하고 보고서를 작성할 수 있다

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
| 0:00-0:40 | CTF 규칙 설명 + 환경 확인 (Part 1) | 강의 |
| 0:40-1:10 | CTF Phase 1: 정보 수집 (Part 2) | 실습/CTF |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | CTF Phase 2: 보안 점검 (Part 3) | 실습/CTF |
| 2:00-2:40 | CTF Phase 3: 분석 + 대응 (Part 4) | 실습/CTF |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | CTF Phase 4: 보고서 + 검증 (Part 5) | 실습/CTF |
| 3:20-3:40 | 점수 집계 + 리뷰 (Part 6) | 퀴즈/토론 |

---

---

## 용어 해설 (자율보안시스템 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **CTF** | Capture The Flag | 보안 기술을 겨루는 경쟁 대회 | 보안 올림픽 |
| **Flag** | Flag | CTF에서 획득해야 하는 정답 문자열 | 숨겨진 깃발 |
| **챌린지** | Challenge | CTF의 개별 문제 | 시험 문제 |
| **스코어보드** | Scoreboard | 참가자별 점수 현황판 | 대회 순위표 |
| **정보 수집** | Reconnaissance | 대상 시스템의 정보를 수집하는 단계 | 적진 정찰 |
| **취약점 점검** | Vulnerability Assessment | 시스템의 보안 취약점을 찾는 과정 | 건물 안전 점검 |
| **설정 감사** | Configuration Audit | 시스템 설정의 보안 적합성 확인 | 안전 규정 준수 점검 |
| **병렬 점검** | Parallel Scanning | 여러 서버를 동시에 점검 | 동시 다발 수색 |
| **evidence** | Evidence | 점검 결과의 감사 증거 | 점검 보고서 |
| **PoW 검증** | PoW Verification | 작업 이력의 무결성 확인 | 작업 일지 진위 확인 |
| **리더보드** | Leaderboard | 에이전트별 보상 순위 | 게임 랭킹 |
| **execute-plan** | execute-plan | 다수 명령 병렬 실행 | 동시 다발 점검 |
| **dispatch** | dispatch | 단일 명령 실행 | 개별 점검 |
| **completion-report** | completion-report | 프로젝트 완료 보고서 | 최종 보고서 |
| **replay** | replay | 프로젝트 이력 재생 | 블랙박스 재생 |
| **risk_level** | risk_level | 작업 위험 등급 | 작업 난이도 |

---

# Week 08: 중간고사 — 자율 보안 점검 CTF

## 시험 목표
- Week 01~07 지식 종합 평가
- OpsClaw 전체 기능 활용 능력 검증
- 실전 보안 점검 역량 확인

## 전제 조건
- Week 01~07 전체 수강 및 과제 완료
- OpsClaw API 호출 능숙
- 보안 점검 명령어 숙지

---

## CTF 규칙

### 채점 기준

| 항목 | 배점 | 설명 |
|------|------|------|
| **Phase 1: 정보 수집** | 20점 | 4대 서버 기본 정보 수집 (각 5점) |
| **Phase 2: 보안 점검** | 30점 | 보안 설정 점검 Flag 획득 (각 5-10점) |
| **Phase 3: 분석 + 대응** | 30점 | 이상 탐지 및 대응 시나리오 (각 10점) |
| **Phase 4: 보고서** | 20점 | evidence 기반 완료 보고서 품질 |
| **합계** | 100점 | |

### 규칙
1. 모든 작업은 OpsClaw API를 통해 수행한다 (직접 SSH 접속 금지)
2. API 호출에는 반드시 인증 키를 포함한다
3. 파괴적 명령(rm, drop, kill 등)은 사용 금지
4. 각 Phase별 제한 시간 내에 수행한다
5. evidence에 기록된 결과만 채점 대상이다

---

## 1. CTF 환경 준비 (Part 1, 40분)

### 1.1 환경 접속 및 API 확인

> **실습 목적**: 전반기에 학습한 자율보안 기술을 종합하여 실전 수준의 자동 대응 시나리오를 구축하기 위해 수행한다
>
> **배우는 것**: OODA Loop, Playbook, PoW, RL을 결합한 완전 자율 보안 대응 파이프라인의 설계와 구현 능력을 기른다
>
> **결과 해석**: 전체 파이프라인의 탐지-분석-대응 소요 시간(MTTR)과 정확도로 자율보안 시스템의 성숙도를 평가한다
>
> **실전 활용**: SOC 자동화 로드맵 수립, 자율보안 시스템 PoC 설계, 보안 자동화 투자 대비 효과 분석에 활용한다

```bash
# opsclaw 서버 접속
ssh opsclaw@10.20.30.201
```

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026
```

```bash
# Manager API 상태 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/health | python3 -m json.tool
# 정상 응답 확인
```

```bash
# 전체 SubAgent 상태 확인
for server in "10.20.30.201:8002" "10.20.30.1:8002" "10.20.30.80:8002" "10.20.30.100:8002"; do
  # 각 SubAgent health check (2초 타임아웃)
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 http://$server/health)
  # 결과 출력
  if [ "$status" = "200" ]; then
    echo "[OK]   $server"
  else
    echo "[FAIL] $server (HTTP $status)"
  fi
done
# 4대 SubAgent 모두 OK 확인
```

### 1.2 CTF 프로젝트 생성

```bash
# CTF 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "midterm-ctf-autonomous-security",
    "request_text": "중간고사 CTF: 4대 서버 종합 보안 점검",
    "master_mode": "external"
  }' | python3 -m json.tool
# 프로젝트 ID를 기록한다
```

```bash
# 프로젝트 ID 설정 (실제 값으로 교체)
export PROJECT_ID="반환된-프로젝트-ID"
# stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# executing 단계 진입 확인
```

---

## 2. Phase 1: 정보 수집 (Part 2, 30분) — 20점

### Challenge 1-1: 전 서버 기본 정보 (5점)

**목표**: 4대 서버의 hostname, OS, 커널 버전을 한 번에 수집하라.

```bash
# Flag 획득: 4대 서버 기본 정보 병렬 수집
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== $(hostname) ===\" && cat /etc/os-release | head -2 && uname -r",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== $(hostname) ===\" && cat /etc/os-release | head -2 && uname -r",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== $(hostname) ===\" && cat /etc/os-release | head -2 && uname -r",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"=== $(hostname) ===\" && cat /etc/os-release | head -2 && uname -r",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 4대 서버의 hostname, OS, 커널 정보가 evidence에 기록된다
```

### Challenge 1-2: 네트워크 포트 스캔 (5점)

**목표**: 전 서버의 열린 TCP 포트를 수집하라.

```bash
# 전 서버 열린 포트 수집
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 5,
        "instruction_prompt": "echo \"=== $(hostname) open ports ===\" && ss -tlnp | grep LISTEN",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 6,
        "instruction_prompt": "echo \"=== $(hostname) open ports ===\" && ss -tlnp | grep LISTEN",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 7,
        "instruction_prompt": "echo \"=== $(hostname) open ports ===\" && ss -tlnp | grep LISTEN",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 각 서버의 LISTEN 상태 포트 목록이 수집된다
```

### Challenge 1-3: 리소스 현황 (5점)

**목표**: 전 서버의 디스크 사용률, 메모리 사용률, CPU 로드를 수집하라.

```bash
# 전 서버 리소스 현황 수집
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 8,
        "instruction_prompt": "echo \"=== $(hostname) resources ===\" && echo \"Disk:\" && df -h / | tail -1 && echo \"Memory:\" && free -h | head -2 && echo \"CPU Load:\" && cat /proc/loadavg",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 9,
        "instruction_prompt": "echo \"=== $(hostname) resources ===\" && echo \"Disk:\" && df -h / | tail -1 && echo \"Memory:\" && free -h | head -2 && echo \"CPU Load:\" && cat /proc/loadavg",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 10,
        "instruction_prompt": "echo \"=== $(hostname) resources ===\" && echo \"Disk:\" && df -h / | tail -1 && echo \"Memory:\" && free -h | head -2 && echo \"CPU Load:\" && cat /proc/loadavg",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### Challenge 1-4: 사용자 계정 감사 (5점)

**목표**: 전 서버에서 UID 0(root 권한) 계정과 로그인 가능 계정을 식별하라.

```bash
# 사용자 계정 감사
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 11,
        "instruction_prompt": "echo \"=== $(hostname) users ===\" && echo \"UID 0:\" && awk -F: \"\\$3==0\" /etc/passwd && echo \"Login shells:\" && grep -v nologin /etc/passwd | grep -v /bin/false | grep -v /usr/sbin/nologin",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 12,
        "instruction_prompt": "echo \"=== $(hostname) users ===\" && echo \"UID 0:\" && awk -F: \"\\$3==0\" /etc/passwd && echo \"Login shells:\" && grep -v nologin /etc/passwd | grep -v /bin/false | grep -v /usr/sbin/nologin",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 13,
        "instruction_prompt": "echo \"=== $(hostname) users ===\" && echo \"UID 0:\" && awk -F: \"\\$3==0\" /etc/passwd && echo \"Login shells:\" && grep -v nologin /etc/passwd | grep -v /bin/false | grep -v /usr/sbin/nologin",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

---

## 3. Phase 2: 보안 점검 (Part 3, 40분) — 30점

### Challenge 2-1: 방화벽 정책 검증 (10점)

**목표**: secu 서버의 방화벽 규칙을 분석하고, 불필요하게 열린 포트가 있는지 확인하라.

```bash
# secu 방화벽 정책 상세 조회
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"=== nftables ruleset ===\" && sudo nft list ruleset",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -m json.tool
# 전체 방화벽 규칙이 출력된다 — 불필요한 ACCEPT 규칙이 있는지 분석
```

```bash
# Suricata IPS 상태 확인
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"=== Suricata status ===\" && systemctl is-active suricata 2>/dev/null && suricata --build-info 2>/dev/null | head -5 || echo suricata-not-found",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -m json.tool
```

### Challenge 2-2: 웹 서비스 보안 점검 (10점)

**목표**: web 서버의 웹 서비스 보안 상태를 점검하라.

```bash
# 웹 서비스 보안 점검
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 20,
        "instruction_prompt": "echo \"=== HTTP Headers ===\" && curl -s -I http://localhost:3000 | head -15",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 21,
        "instruction_prompt": "echo \"=== Server Version Exposure ===\" && curl -s -I http://localhost:80 | grep -i server",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 22,
        "instruction_prompt": "echo \"=== Directory Listing ===\" && curl -s -o /dev/null -w \"%{http_code}\" http://localhost:80/icons/ && echo --- && curl -s -o /dev/null -w \"%{http_code}\" http://localhost:3000/api/",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 23,
        "instruction_prompt": "echo \"=== HTTPS Check ===\" && curl -s -o /dev/null -w \"%{http_code}\" --max-time 3 https://localhost:443 2>/dev/null || echo no-https",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# HTTP 헤더, 서버 버전 노출, 디렉토리 리스팅, HTTPS 설정 확인
```

### Challenge 2-3: SIEM 상태 및 에이전트 점검 (10점)

**목표**: siem 서버의 Wazuh 상태와 연결된 에이전트를 확인하라.

```bash
# SIEM 종합 점검
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 24,
        "instruction_prompt": "echo \"=== Wazuh Manager ===\" && systemctl is-active wazuh-manager 2>/dev/null || echo not-found && systemctl is-active wazuh-indexer 2>/dev/null || echo indexer-not-found",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 25,
        "instruction_prompt": "echo \"=== Wazuh Agents ===\" && /var/ossec/bin/agent_control -l 2>/dev/null | head -20 || echo no-agent-control",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 26,
        "instruction_prompt": "echo \"=== Recent Alerts ===\" && ls -la /var/ossec/logs/alerts/ 2>/dev/null | tail -5 || echo no-alerts-dir",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

---

## 4. Phase 3: 분석 + 대응 (Part 4, 40분) — 30점

### Challenge 3-1: 이상 로그인 탐지 (10점)

**목표**: 전 서버의 인증 로그에서 실패한 로그인 시도를 탐지하라.

```bash
# 전 서버 인증 실패 로그 수집
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 30,
        "instruction_prompt": "echo \"=== $(hostname) auth failures ===\" && grep -c \"Failed password\" /var/log/auth.log 2>/dev/null || echo 0 && echo \"Recent failures:\" && grep \"Failed password\" /var/log/auth.log 2>/dev/null | tail -5 || echo none",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 31,
        "instruction_prompt": "echo \"=== $(hostname) auth failures ===\" && grep -c \"Failed password\" /var/log/auth.log 2>/dev/null || echo 0 && echo \"Recent failures:\" && grep \"Failed password\" /var/log/auth.log 2>/dev/null | tail -5 || echo none",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 32,
        "instruction_prompt": "echo \"=== $(hostname) auth failures ===\" && grep -c \"Failed password\" /var/log/auth.log 2>/dev/null || echo 0 && echo \"Recent failures:\" && grep \"Failed password\" /var/log/auth.log 2>/dev/null | tail -5 || echo none",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 인증 실패 건수와 최근 로그가 수집된다
```

### Challenge 3-2: 비정상 프로세스 탐지 (10점)

**목표**: 각 서버에서 비정상적으로 리소스를 소비하는 프로세스를 탐지하라.

```bash
# 비정상 프로세스 탐지
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 33,
        "instruction_prompt": "echo \"=== $(hostname) top CPU ===\" && ps aux --sort=-%cpu | head -6 && echo \"=== top MEM ===\" && ps aux --sort=-%mem | head -6",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 34,
        "instruction_prompt": "echo \"=== $(hostname) top CPU ===\" && ps aux --sort=-%cpu | head -6 && echo \"=== top MEM ===\" && ps aux --sort=-%mem | head -6",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 35,
        "instruction_prompt": "echo \"=== $(hostname) top CPU ===\" && ps aux --sort=-%cpu | head -6 && echo \"=== top MEM ===\" && ps aux --sort=-%mem | head -6",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### Challenge 3-3: LLM 기반 위협 분석 (10점)

**목표**: 수집된 로그를 LLM에 분석 요청하고 결과를 해석하라.

```bash
# LLM에 수집된 로그 분석 요청
curl -s -X POST http://192.168.0.105:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {
        "role": "system",
        "content": "당신은 SOC 분석관입니다. 다음 보안 점검 결과를 분석하고 JSON으로 출력하세요: {\"risk_summary\": \"전체 위험도 요약\", \"findings\": [{\"server\": \"서버명\", \"issue\": \"발견 사항\", \"severity\": \"low|medium|high|critical\", \"action\": \"권장 조치\"}], \"overall_score\": \"1-10 (10이 가장 안전)\"}"
      },
      {
        "role": "user",
        "content": "4대 서버 보안 점검 결과:\n- secu: nftables 방화벽 활성, Suricata IPS 동작, SSH 로그인 실패 0건\n- web: JuiceShop(3000) 및 Apache(80) 응답 정상, Server 헤더 노출, HTTPS 미설정\n- siem: Wazuh Manager 동작, 경보 로그 존재\n- 전 서버: 디스크 사용률 50% 이하, 메모리 정상"
      }
    ],
    "stream": false,
    "options": {"temperature": 0.1}
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['message']['content'])"
# LLM의 종합 분석 결과가 출력된다
```

---

## 5. Phase 4: 보고서 + 검증 (Part 5, 30분) — 20점

### Challenge 4-1: Evidence 요약 (5점)

```bash
# 전체 evidence 요약 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool
# 모든 task의 실행 결과가 기록되어 있는지 확인
```

### Challenge 4-2: PoW 체인 검증 (5점)

```bash
# PoW 체인 무결성 검증
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/verify" \
  | python3 -m json.tool
# valid: true, tampered: [] 확인
```

```bash
# 프로젝트 PoW 블록 수 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?project_id=$PROJECT_ID" \
  | python3 -c "import sys,json; blocks=json.load(sys.stdin); print(f'PoW 블록 수: {len(blocks) if isinstance(blocks,list) else 0}')"
```

### Challenge 4-3: RL 추천 조회 (5점)

```bash
# RL 추천 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/rl/recommend?agent_id=http://10.20.30.1:8002&risk_level=low" \
  | python3 -m json.tool
```

```bash
# 리더보드 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/pow/leaderboard | python3 -m json.tool
```

### Challenge 4-4: 완료 보고서 작성 (5점)

```bash
# 완료 보고서 작성 (내용의 품질이 채점 대상)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "중간고사 CTF: 4대 서버 종합 보안 점검 완료",
    "outcome": "success",
    "work_details": [
      "Phase 1: 4대 서버 기본 정보(OS, 커널, 포트, 리소스, 계정) 수집 완료",
      "Phase 2: secu 방화벽/IPS 점검, web HTTP 보안 헤더/HTTPS 점검, siem Wazuh 상태 점검",
      "Phase 3: 인증 실패 로그 분석, 비정상 프로세스 탐지, LLM 종합 분석",
      "Phase 4: evidence 확인, PoW 체인 무결성 검증(valid=true), 리더보드 확인",
      "발견 사항: web 서버 Server 헤더 노출, HTTPS 미설정 (보안 개선 필요)",
      "전체 task 수: 20+ 건, 전체 PoW 블록 생성 확인"
    ]
  }' | python3 -m json.tool
# 프로젝트 closed 확인
```

### Challenge 보너스: Replay

```bash
# 전체 CTF 이력 재생
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID/replay \
  | python3 -m json.tool
# 전체 4 Phase의 작업 이력이 시간순으로 출력된다
```

---

## 6. 점수 집계 + 리뷰 (Part 6, 20분)

### 채점 체크리스트

| Phase | 항목 | 배점 | 체크 |
|-------|------|------|------|
| 1 | 4대 서버 기본 정보 수집 | 5 | [ ] |
| 1 | 열린 포트 수집 | 5 | [ ] |
| 1 | 리소스 현황 수집 | 5 | [ ] |
| 1 | 사용자 계정 감사 | 5 | [ ] |
| 2 | 방화벽 정책 검증 | 10 | [ ] |
| 2 | 웹 서비스 보안 점검 | 10 | [ ] |
| 2 | SIEM 상태 점검 | 10 | [ ] |
| 3 | 이상 로그인 탐지 | 10 | [ ] |
| 3 | 비정상 프로세스 탐지 | 10 | [ ] |
| 3 | LLM 위협 분석 | 10 | [ ] |
| 4 | evidence + PoW 검증 | 10 | [ ] |
| 4 | 완료 보고서 품질 | 10 | [ ] |
| **합계** | | **100** | |

### 리뷰 토론

1. **가장 어려웠던 Challenge**: 어떤 점검이 가장 어려웠는가? 이유는?
2. **OpsClaw 효과**: SSH 수동 점검 대비 OpsClaw 사용 시 시간이 얼마나 절약되었는가?
3. **개선 제안**: CTF를 통해 발견한 OpsClaw 개선 사항은?
4. **자율화 가능성**: 이번 CTF의 어떤 부분을 완전 자율화할 수 있는가?

---

## 검증 체크리스트

- [ ] OpsClaw 프로젝트 생명주기(생성→계획→실행→보고→종료)를 완전히 수행했는가?
- [ ] execute-plan으로 다수 서버에 병렬 명령을 실행했는가?
- [ ] dispatch로 단일 서버에 특화 명령을 실행했는가?
- [ ] evidence 요약으로 전체 실행 결과를 확인했는가?
- [ ] PoW 체인 무결성을 검증했는가?
- [ ] LLM을 활용한 보안 분석을 수행했는가?
- [ ] completion-report로 프로젝트를 종료했는가?
- [ ] replay로 전체 이력을 확인했는가?

---

## 다음 주 예고

**Week 09: 자율 Purple Team (1) — Red Team Agent**
- 자율 공격 에이전트 개념
- LLM 기반 공격 시나리오 생성
- OpsClaw A2A mission 엔드포인트 활용
- 통제된 환경에서의 자율 공격 실습

---

---

## 자가 점검 퀴즈 (4문항)

이번 주차(중간고사)의 핵심 개념을 최종 점검한다.

**Q1.** OpsClaw에서 4대 서버에 동시에 명령을 보내는 API는?
- (a) dispatch  (b) **execute-plan (tasks 배열에 각 서버의 subagent_url 지정)**  (c) health  (d) replay

**Q2.** PoW 체인 검증 결과에서 "valid": true, "tampered": []의 의미는?
- (a) 서버가 정상  (b) 학습 완료  (c) **모든 블록의 해시 체인이 무결하고 위변조가 없음**  (d) 프로젝트 종료

**Q3.** evidence 기록이 중요한 이유는?
- (a) 속도 향상  (b) 비용 절감  (c) **감사 추적 가능, 재현성 보장, 규정 준수 증거**  (d) 서버 보호

**Q4.** CTF에서 모든 작업을 OpsClaw API로 수행해야 하는 이유는?
- (a) SSH가 느리기 때문  (b) **evidence 자동 기록 + PoW 블록 생성 + 감사 추적이 가능하기 때문**  (c) 비밀번호를 모르기 때문  (d) 네트워크 제한

**정답:** Q1:b, Q2:c, Q3:c, Q4:b

---
---
