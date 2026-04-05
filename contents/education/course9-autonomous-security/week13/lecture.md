# Week 13: 분산 지식 아키텍처

## 학습 목표

- SubAgent별 독립 Experience DB의 필요성과 설계를 이해한다
- 지식 교환 API를 통해 SubAgent 간 경험을 공유하는 방법을 실습한다
- PoW 교차 검증으로 공유된 지식의 무결성을 보장하는 원리를 이해한다
- 분산 환경에서 지식 충돌(conflict) 해결 전략을 설계한다
- 중앙 집중형 vs 분산형 지식 관리의 트레이드오프를 분석한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

## 강의 시간 배분 (3시간)

| 시간 | 파트 | 내용 | 형태 |
|------|------|------|------|
| 0:00-0:30 | Part 1 | 분산 지식의 필요성과 아키텍처 | 이론 |
| 0:30-1:00 | Part 2 | SubAgent별 Experience DB | 이론+실습 |
| 1:00-1:25 | Part 3 | 지식 교환 API | 실습 |
| 1:25-1:35 | — | 휴식 | — |
| 1:35-2:05 | Part 4 | PoW 교차 검증 | 실습 |
| 2:05-2:35 | Part 5 | 지식 충돌 해결과 합의 | 이론+실습 |
| 2:35-3:00 | Part 6 | 종합 실습 + 퀴즈 | 실습+평가 |

## 용어 해설 (자율보안시스템 과목)

| 용어 | 설명 | 예시 |
|------|------|------|
| **분산 지식 아키텍처** | 여러 SubAgent가 독립 Experience DB를 유지하면서 지식을 공유하는 구조 | secu/web/siem 각각의 Experience |
| **Experience DB** | 에이전트의 장기 경험을 저장하는 데이터베이스 | PostgreSQL FTS 기반 |
| **지식 교환 (Knowledge Exchange)** | SubAgent 간 Experience를 공유하는 프로토콜 | push/pull 방식 |
| **PoW 교차 검증** | 여러 SubAgent의 PoW 체인을 상호 검증하는 과정 | 해시 일관성 확인 |
| **agent_id** | SubAgent의 고유 식별자 | `http://10.20.30.1:8002` |
| **PoW 체인** | 태스크 실행 증적의 해시 연결 블록 체인 | prev_hash → hash → next |
| **orphan block** | 메인 체인에 연결되지 않은 분기 블록 | 동시 실행 시 발생 |
| **advisory lock** | PostgreSQL의 협력적 잠금 메커니즘 | 동시 블록 생성 방지 |
| **conflict resolution** | 분산 환경에서 동일 키에 대한 충돌 해결 | last-writer-wins, merge |
| **CAP 정리** | 분산 시스템의 Consistency/Availability/Partition tolerance 트레이드오프 | CP vs AP 선택 |
| **eventual consistency** | 최종적 일관성 — 시간이 지나면 모든 노드가 동일한 상태에 도달 | Experience 동기화 |
| **gossip protocol** | 노드 간 정보를 전파하는 분산 프로토콜 | 경험 전파 |
| **leaderboard** | PoW 보상 기반 SubAgent 순위표 | 기여도 랭킹 |
| **replay** | 프로젝트의 태스크 실행 과정을 시간순으로 재현 | 실행 타임라인 |
| **ts_raw** | PoW 블록의 원시 타임스탬프 | 블록 생성 시각 |
| **backfill** | 기존 데이터에 누락된 필드를 채우는 마이그레이션 | ts_raw 칼럼 추가 |

---

## Part 1: 분산 지식의 필요성과 아키텍처 (0:00-0:30)

### 1.1 왜 분산 지식이 필요한가?

중앙 집중형 Experience DB의 한계:

| 문제 | 설명 |
|------|------|
| 단일 장애점 | Manager DB 장애 시 전체 지식 접근 불가 |
| 네트워크 병목 | 모든 SubAgent가 중앙 DB에 쓰기/읽기 |
| 도메인 혼재 | 방화벽/웹/SIEM 지식이 구분 없이 섞임 |
| 확장성 한계 | SubAgent 수 증가에 따라 중앙 DB 부하 증가 |

### 1.2 분산 지식 아키텍처

```
[Manager (10.20.30.201)]
  Global Experience (중앙 인덱스) ← 교환된 지식 통합
        |               |               |
    push/pull       push/pull       push/pull
        |               |               |
        v               v               v
  [secu]           [web]           [siem]
  Exp DB (방화벽)   Exp DB (웹보안)  Exp DB (관제)
  Local PoW Chain   Local PoW Chain  Local PoW Chain
```

### 1.3 중앙 집중형 vs 분산형 비교

| 속성 | 중앙 집중형 | 분산형 |
|------|-----------|--------|
| 일관성 | 강한 일관성 (Strong) | 최종적 일관성 (Eventual) |
| 가용성 | 단일 장애점 존재 | 개별 노드 독립 운영 |
| 지연 | 네트워크 왕복 필요 | 로컬 읽기 가능 |
| 도메인 특화 | 어려움 | 자연스러움 |
| 무결성 검증 | 중앙 DB 신뢰 | PoW 교차 검증 |

---

## Part 2: SubAgent별 Experience DB (0:30-1:00)

### 2.1 SubAgent별 Experience 구조

각 SubAgent는 자신의 도메인에 특화된 Experience를 독립적으로 관리한다.

| SubAgent | 도메인 | Experience 예시 |
|----------|--------|----------------|
| secu (10.20.30.1) | 방화벽/IPS | nftables 규칙 패턴, Suricata 시그니처 |
| web (10.20.30.80) | 웹 보안 | XSS/SQLi 패턴, WAF 규칙, JuiceShop 취약점 |
| siem (10.20.30.100) | SIEM/관제 | Wazuh 경보 패턴, 인시던트 대응 절차 |

### 2.2 SubAgent별 Experience 축적 실습

> **실습 목적**: 자율보안 시스템을 실제 인시던트 시나리오에 적용하여 종합 대응 능력을 검증하기 위해 수행한다
>
> **배우는 것**: 웹 공격 탐지 → 분석 → 차단 → 보고의 전체 대응 사이클을 자동화하는 방법과 각 단계의 검증 포인트를 이해한다
>
> **결과 해석**: 전체 대응 사이클의 완료 시간과 각 단계의 성공 여부로 시스템의 실전 준비도를 평가한다
>
> **실전 활용**: 실제 보안 사고 대응 자동화, 인시던트 대응 훈련(TTX) 자동화, 대응 절차 검증에 활용한다

```bash
# 환경 변수 설정
export OPSCLAW_API_KEY="opsclaw-api-key-2026"
# Manager API 주소
export MGR="http://localhost:8000"

# 1. 분산 지식 프로젝트 생성
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week13-distributed-knowledge",
    "request_text": "분산 지식 아키텍처 실습 — SubAgent별 Experience 축적",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export PID="반환된-프로젝트-ID"

# 2. 스테이지 전환
# plan 스테이지
curl -s -X POST $MGR/projects/$PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지
curl -s -X POST $MGR/projects/$PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. 각 SubAgent에서 도메인 특화 정보 수집
curl -s -X POST $MGR/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== secu Experience: Firewall Knowledge ===\"; nft list ruleset 2>/dev/null | grep -c \"rule\" || echo 0; echo \"rules counted\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== web Experience: Web Security Knowledge ===\"; curl -s http://localhost:3000/api/SecurityQuestions 2>/dev/null | python3 -c \"import sys,json; print(f\\\"Security items: {len(json.load(sys.stdin).get(\\\\\\\"data\\\\\\\", []))}\\\")\" 2>/dev/null || echo web-check-done",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== siem Experience: SIEM Knowledge ===\"; ls /var/ossec/ruleset/rules/ 2>/dev/null | wc -l || echo 0; echo \"rule files counted\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 각 SubAgent가 자기 도메인의 지식을 수집하여 Experience에 축적한다
```

### 2.3 SubAgent별 PoW 블록 확인

```bash
# 4. 각 SubAgent의 PoW 블록 현황 조회
for AGENT in "http://10.20.30.1:8002" "http://10.20.30.80:8002" "http://10.20.30.100:8002"; do
  echo "=== $AGENT ==="
  # 각 SubAgent의 PoW 블록 수 확인
  curl -s "$MGR/pow/blocks?agent_id=$AGENT" \
    -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
blocks = data.get('blocks', [])
print(f'  블록 수: {len(blocks)}')
if blocks:
    latest = blocks[-1]
    print(f'  최신 블록: height={latest.get(\"height\",\"?\")}, hash={latest.get(\"hash\",\"\")[:20]}...')
" 2>/dev/null || echo "  조회 실패"
done
# 3개 SubAgent의 독립 PoW 체인 현황을 비교한다
```

---

## Part 3: 지식 교환 API (1:00-1:25)

### 3.1 지식 교환 프로토콜

SubAgent 간 Experience를 교환하는 두 가지 방식:

| 방식 | 설명 | 사용 시나리오 |
|------|------|-------------|
| **Push** | 발신 SubAgent가 수신 측에 Experience를 전송 | 긴급 지식 공유 (새 공격 패턴 발견) |
| **Pull** | 수신 SubAgent가 필요 시 발신 측에서 가져옴 | 정기 동기화, 온디맨드 검색 |

### 3.2 지식 교환 시뮬레이션

실제 환경에서 Manager API를 통해 SubAgent 간 지식을 교환한다.

```bash
# 1. secu의 방화벽 지식을 수집
curl -s -X POST $MGR/projects/$PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"{\\\"source\\\": \\\"secu\\\", \\\"type\\\": \\\"firewall_knowledge\\\", \\\"content\\\": \\\"nftables rate-limit SSH: ct state new limit rate 3/minute accept\\\", \\\"timestamp\\\": \\\"$(date -Iseconds)\\\"}\"",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -m json.tool
# secu SubAgent의 방화벽 지식을 구조화하여 수집한다
```

```bash
# 2. web의 웹 보안 지식을 수집
curl -s -X POST $MGR/projects/$PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"{\\\"source\\\": \\\"web\\\", \\\"type\\\": \\\"web_security_knowledge\\\", \\\"content\\\": \\\"JuiceShop SQLi endpoint: /rest/products/search?q= - parameterized query required\\\", \\\"timestamp\\\": \\\"$(date -Iseconds)\\\"}\"",
    "subagent_url": "http://10.20.30.80:8002"
  }' | python3 -m json.tool
# web SubAgent의 웹 보안 지식을 수집한다
```

```bash
# 3. siem의 관제 지식을 수집
curl -s -X POST $MGR/projects/$PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"{\\\"source\\\": \\\"siem\\\", \\\"type\\\": \\\"siem_knowledge\\\", \\\"content\\\": \\\"Wazuh rule 5712: SSH brute force detected - threshold 5 failures in 120s\\\", \\\"timestamp\\\": \\\"$(date -Iseconds)\\\"}\"",
    "subagent_url": "http://10.20.30.100:8002"
  }' | python3 -m json.tool
# siem SubAgent의 관제 지식을 수집한다
```

### 3.3 지식 통합 (LLM으로 교차 참조)

```bash
# 4. 수집된 지식을 Evidence에서 가져와 LLM으로 통합 분석
curl -s "$MGR/projects/$PID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /tmp/distributed_knowledge.json

# 5. LLM으로 분산 지식 통합 분석
python3 -c "
import json, requests

with open('/tmp/distributed_knowledge.json') as f:
    knowledge = json.load(f)

knowledge_text = json.dumps(knowledge, indent=2, ensure_ascii=False)[:3000]

resp = requests.post(
    'http://192.168.0.105:11434/v1/chat/completions',
    json={
        'model': 'gemma3:12b',
        'messages': [
            {
                'role': 'system',
                'content': '분산 지식 통합 분석가. 여러 SubAgent에서 수집된 보안 지식을 분석하여 상호 관련성을 파악하고 통합 보안 인사이트를 제공하라.'
            },
            {
                'role': 'user',
                'content': f'다음 분산 지식을 통합 분석하라:\\n{knowledge_text}\\n\\n1. 각 SubAgent의 지식 요약\\n2. 지식 간 상호 관련성\\n3. 통합 보안 권고'
            }
        ],
        'temperature': 0.2,
        'max_tokens': 800
    }
)
# 분산 지식 통합 분석 결과 출력
print('=== 분산 지식 통합 분석 ===')
print(resp.json()['choices'][0]['message']['content'])
"
```

---

## Part 4: PoW 교차 검증 (1:35-2:05)

### 4.1 PoW 교차 검증의 필요성

분산 환경에서 Experience의 신뢰성을 보장하려면:
- 각 SubAgent의 PoW 체인이 무결한지 확인해야 한다
- 변조된 Experience가 다른 SubAgent로 전파되는 것을 방지해야 한다
- 교차 검증을 통해 합의된 지식만 Global Experience에 반영한다

### 4.2 PoW 체인 검증 실습

```bash
# 1. secu SubAgent의 PoW 체인 무결성 검증
curl -s "$MGR/pow/verify?agent_id=http://10.20.30.1:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# 검증 결과 출력
print('=== secu PoW 검증 ===')
print(f'  valid: {data.get(\"valid\", \"?\")}')
print(f'  blocks: {data.get(\"blocks\", 0)}')
print(f'  orphans: {data.get(\"orphans\", 0)}')
print(f'  tampered: {data.get(\"tampered\", [])}')
"
# valid=true이면 체인 무결성 확인, orphans는 분기 블록 수
```

```bash
# 2. web SubAgent의 PoW 체인 검증
curl -s "$MGR/pow/verify?agent_id=http://10.20.30.80:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('=== web PoW 검증 ===')
print(f'  valid: {data.get(\"valid\", \"?\")}')
print(f'  blocks: {data.get(\"blocks\", 0)}')
print(f'  orphans: {data.get(\"orphans\", 0)}')
"

# 3. siem SubAgent의 PoW 체인 검증
curl -s "$MGR/pow/verify?agent_id=http://10.20.30.100:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('=== siem PoW 검증 ===')
print(f'  valid: {data.get(\"valid\", \"?\")}')
print(f'  blocks: {data.get(\"blocks\", 0)}')
print(f'  orphans: {data.get(\"orphans\", 0)}')
"
```

### 4.3 전체 SubAgent PoW 비교

```bash
# 4. 전체 SubAgent PoW 비교 — 리더보드 조회
curl -s "$MGR/pow/leaderboard" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# 리더보드에서 각 SubAgent의 기여도 확인
print('=== PoW 리더보드 ===')
entries = data if isinstance(data, list) else data.get('leaderboard', data.get('agents', []))
for i, entry in enumerate(entries, 1):
    agent = entry.get('agent_id', entry.get('agent', '?'))
    blocks = entry.get('blocks', entry.get('total_blocks', 0))
    rewards = entry.get('total_reward', entry.get('rewards', 0))
    print(f'  {i}. {agent}: blocks={blocks}, rewards={rewards}')
"
# 각 SubAgent의 PoW 블록 수와 보상을 비교한다
```

### 4.4 교차 검증 자동화

```bash
# 5. 3개 SubAgent의 PoW를 한 번에 교차 검증하는 스크립트
python3 -c "
import requests, json

API = 'http://localhost:8000'
KEY = 'opsclaw-api-key-2026'
headers = {'X-API-Key': KEY}
agents = [
    ('secu', 'http://10.20.30.1:8002'),
    ('web', 'http://10.20.30.80:8002'),
    ('siem', 'http://10.20.30.100:8002'),
]

print('=== PoW 교차 검증 결과 ===')
all_valid = True
for name, agent_id in agents:
    try:
        resp = requests.get(f'{API}/pow/verify?agent_id={agent_id}', headers=headers, timeout=5)
        data = resp.json()
        valid = data.get('valid', False)
        blocks = data.get('blocks', 0)
        orphans = data.get('orphans', 0)
        tampered = data.get('tampered', [])
        status = 'PASS' if valid else 'FAIL'
        if not valid:
            all_valid = False
        print(f'  [{status}] {name} ({agent_id}): blocks={blocks}, orphans={orphans}, tampered={len(tampered)}')
    except Exception as e:
        print(f'  [ERROR] {name}: {e}')
        all_valid = False

print(f'\\n전체 결과: {\"ALL VALID\" if all_valid else \"VERIFICATION FAILED\"}\')
"
# 모든 SubAgent의 PoW 체인이 무결하면 "ALL VALID" 출력
```

---

## Part 5: 지식 충돌 해결과 합의 (2:05-2:35)

### 5.1 지식 충돌 시나리오

분산 환경에서 동일한 주제에 대해 SubAgent 간 상충하는 지식이 발생할 수 있다.

| 충돌 유형 | 예시 | 해결 전략 |
|-----------|------|----------|
| 버전 충돌 | secu: "SSH 포트 22 차단", web: "SSH 포트 22 유지" | 도메인 우선순위 |
| 시간 충돌 | 구 경험 vs 신 경험 | 최신 우선 (LWW) |
| 신뢰도 충돌 | PoW 검증된 vs 미검증 | PoW 검증 우선 |
| 도메인 충돌 | 방화벽 관점 vs 웹 관점 | 도메인 전문가 우선 |

### 5.2 충돌 해결 전략

**Last-Writer-Wins (LWW):**
- 가장 최근에 생성/수정된 Experience가 우선
- 단순하지만 구 경험이 손실될 수 있음

**Domain Authority:**
- 각 SubAgent가 자신의 도메인에서 권위를 가짐
- secu의 방화벽 지식 > web의 방화벽 의견

**PoW-Weighted Consensus:**
- PoW 블록 수(기여도)에 비례하여 가중치 부여
- 더 많이 기여한 SubAgent의 지식을 우선

### 5.3 합의 기반 지식 통합 실습

```bash
# 1. 충돌 시나리오 시뮬레이션 프로젝트
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week13-conflict-resolution",
    "request_text": "분산 지식 충돌 해결 시뮬레이션",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export CONFLICT_PID="반환된-프로젝트-ID"

# 2. 스테이지 전환
# plan 스테이지
curl -s -X POST $MGR/projects/$CONFLICT_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지
curl -s -X POST $MGR/projects/$CONFLICT_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. 충돌하는 지식 수집
curl -s -X POST $MGR/projects/$CONFLICT_PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"{\\\"agent\\\": \\\"secu\\\", \\\"topic\\\": \\\"ssh_policy\\\", \\\"recommendation\\\": \\\"SSH rate-limit 3/min으로 제한, 외부 IP 차단\\\", \\\"confidence\\\": 0.9}\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"{\\\"agent\\\": \\\"web\\\", \\\"topic\\\": \\\"ssh_policy\\\", \\\"recommendation\\\": \\\"SSH 포트 변경(2222), key-only 인증으로 전환\\\", \\\"confidence\\\": 0.7}\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"{\\\"agent\\\": \\\"siem\\\", \\\"topic\\\": \\\"ssh_policy\\\", \\\"recommendation\\\": \\\"SSH 실패 5회 시 Wazuh 경보 + 자동 IP 차단(active response)\\\", \\\"confidence\\\": 0.85}\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 3개 SubAgent가 SSH 정책에 대해 서로 다른 권고를 제시한다
```

```bash
# 4. LLM 기반 합의 — 충돌하는 지식을 통합
python3 -c "
import requests, json

# 충돌하는 3개 SubAgent의 SSH 정책 권고
conflict_data = {
    'secu': {'recommendation': 'SSH rate-limit 3/min, 외부 IP 차단', 'confidence': 0.9, 'domain': 'firewall'},
    'web': {'recommendation': 'SSH 포트 변경(2222), key-only 인증', 'confidence': 0.7, 'domain': 'web'},
    'siem': {'recommendation': 'SSH 실패 5회시 Wazuh 경보 + IP 자동 차단', 'confidence': 0.85, 'domain': 'siem'},
}

resp = requests.post(
    'http://192.168.0.105:11434/v1/chat/completions',
    json={
        'model': 'gemma3:12b',
        'messages': [
            {
                'role': 'system',
                'content': '''분산 지식 합의 엔진. 여러 SubAgent의 상충하는 권고를 분석하여 최적의 통합 정책을 결정하라.
규칙:
1. 각 SubAgent의 도메인 전문성(domain authority)을 고려하라
2. confidence 점수를 가중치로 활용하라
3. 상충하지 않는 권고는 모두 포함하라
4. 통합 정책을 단계별로 제시하라'''
            },
            {
                'role': 'user',
                'content': f'SSH 정책에 대한 3개 SubAgent의 권고:\\n{json.dumps(conflict_data, indent=2, ensure_ascii=False)}\\n\\n통합 SSH 보안 정책을 도출하라.'
            }
        ],
        'temperature': 0.2,
        'max_tokens': 600
    }
)
# 합의된 통합 정책 출력
print('=== 합의 결과: 통합 SSH 보안 정책 ===')
print(resp.json()['choices'][0]['message']['content'])
"
# LLM이 3개 SubAgent의 권고를 종합하여 최적 정책을 도출한다
```

---

## Part 6: 종합 실습 + 퀴즈 (2:35-3:00)

### 6.1 종합 실습 과제

**과제**: 분산 지식 교환 파이프라인을 구현하라.

1. 프로젝트 생성 (`week13-distributed-final`)
2. 3개 SubAgent에서 도메인 특화 지식 수집 (execute-plan)
3. 각 SubAgent의 PoW 교차 검증 (pow/verify)
4. LLM으로 분산 지식 통합 분석 (Ollama API)
5. 리더보드 확인 (pow/leaderboard)
6. completion-report 작성

### 6.2 퀴즈 (4지선다)

**문제 1.** 분산 지식 아키텍처에서 SubAgent별 Experience DB를 분리하는 주된 이유는?

- A) 저장 비용을 절감하기 위해
- B) 도메인 특화, 장애 격리, 로컬 읽기 성능을 확보하기 위해
- C) SubAgent 간 통신을 차단하기 위해
- D) Manager API의 기능을 제거하기 위해

**정답: B) 도메인 특화, 장애 격리, 로컬 읽기 성능을 확보하기 위해**

---

**문제 2.** PoW 교차 검증의 목적은?

- A) SubAgent의 CPU 성능을 측정한다
- B) 분산 환경에서 Experience의 무결성과 신뢰성을 보장한다
- C) SubAgent 간 네트워크 속도를 측정한다
- D) Manager API의 응답 시간을 단축한다

**정답: B) 분산 환경에서 Experience의 무결성과 신뢰성을 보장한다**

---

**문제 3.** `pow/verify` API 응답에서 `orphans` 필드의 의미는?

- A) 삭제된 블록의 수
- B) 메인 체인에 연결되지 않은 분기 블록의 수
- C) 검증에 실패한 블록의 수
- D) 생성 중인 블록의 수

**정답: B) 메인 체인에 연결되지 않은 분기 블록의 수**

---

**문제 4.** 지식 충돌 해결에서 "Domain Authority" 전략이란?

- A) 가장 최근에 생성된 지식을 우선한다
- B) 각 SubAgent가 자신의 전문 도메인에서 권위를 가지므로 해당 도메인 지식을 우선한다
- C) PoW 블록이 가장 많은 SubAgent의 지식을 우선한다
- D) Manager API가 모든 충돌을 자동으로 해결한다

**정답: B) 각 SubAgent가 자신의 전문 도메인에서 권위를 가지므로 해당 도메인 지식을 우선한다**

---

**문제 5.** CAP 정리에서 OpsClaw의 분산 지식 아키텍처가 선택한 모델은?

- A) CA (일관성 + 가용성)
- B) CP (일관성 + 분할 내성)
- C) AP (가용성 + 분할 내성) — 최종적 일관성
- D) CAP 모두 충족

**정답: C) AP (가용성 + 분할 내성) — 최종적 일관성**

---

### 6.3 다음 주 예고

Week 14에서는 **RL Steering과 정책 최적화**를 학습한다.
reward 가중치 조절, risk_penalty/speed_bonus를 통한 에이전트 행동 유도를 실습한다.
