# Week 06: PoW 작업증명과 블록체인

## 학습 목표
- SHA-256 해시 함수의 원리와 보안에서의 역할을 이해한다
- PoW(Proof of Work) 블록체인의 구조와 동작 원리를 설명할 수 있다
- Nonce mining 과정을 직접 수행하고 난이도의 의미를 체감한다
- OpsClaw PoW 블록을 조회·검증하여 작업 무결성을 확인할 수 있다
- 리더보드와 보상 시스템의 구조를 이해한다

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

## 용어 해설 (자율보안시스템 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **PoW** | Proof of Work | 작업을 수행했음을 암호학적으로 증명하는 메커니즘 | 공사 완료 사진 + 타임스탬프 |
| **블록** | Block | PoW 체인의 단위, 작업 기록과 해시를 포함 | 일지의 한 페이지 |
| **블록체인** | Blockchain | 블록이 해시로 연결된 불변의 체인 | 체인으로 묶인 일지 |
| **SHA-256** | SHA-256 | 256비트 출력의 암호학적 해시 함수 | 지문 채취기 (입력→고유 지문) |
| **해시** | Hash | 임의 길이 입력을 고정 길이 출력으로 변환 | 문서의 디지털 지문 |
| **Nonce** | Nonce | 해시 조건을 만족시키기 위해 찾는 임의 값 | 금고 비밀번호 |
| **난이도** | Difficulty | PoW 퍼즐의 어려운 정도 (선행 0의 수) | 금고 자릿수 |
| **prev_hash** | Previous Hash | 이전 블록의 해시 (체인 연결) | 이전 페이지의 지문 |
| **block_hash** | Block Hash | 현재 블록의 해시 | 현재 페이지의 지문 |
| **무결성** | Integrity | 데이터가 변조되지 않았음을 보장 | 봉인된 봉투 |
| **위변조** | Tampering | 데이터를 무단으로 수정 | 문서 조작 |
| **리더보드** | Leaderboard | 에이전트별 보상 점수 순위표 | 게임 랭킹 |
| **보상** | Reward | 성공적 작업에 대한 점수 | 월급/보너스 |
| **orphan** | Orphan Block | 메인 체인에 포함되지 않은 분기 블록 | 본선에서 탈락한 후보 |
| **advisory lock** | Advisory Lock | DB 수준의 동시성 제어 잠금 | 화장실 "사용 중" 표시 |
| **ts_raw** | Timestamp Raw | 블록 생성 시각의 원본 타임스탬프 | 영수증의 발행 시각 |

---

# Week 06: PoW 작업증명과 블록체인

## 학습 목표
- SHA-256과 PoW 원리를 이해한다
- Nonce mining을 직접 수행한다
- OpsClaw PoW 블록을 조회·검증한다
- 리더보드와 보상 구조를 파악한다

## 전제 조건
- Week 01-05 완료 (프로젝트 생명주기, execute-plan)
- 해시 함수 기본 개념
- Python 기초 (해시 계산 실습)

---

## 1. 해시 함수와 SHA-256 (40분)

### 1.1 해시 함수란

해시 함수는 임의 길이의 입력을 고정 길이의 출력으로 변환하는 일방향 함수이다.

```
입력 (임의 길이)              해시 (고정 256비트)
"hello"            →  2cf24dba5fb0a30e26e83b2ac5b9e29e...
"hello!"           →  ce06092fb948d9ffac7d1a376e404b26...
"안녕하세요"         →  e97bc9c5de7cbb19d70ef35b5959de44...
"이 문서는 1000페이지" →  a3f5b9c82d4e7f1a...  (여전히 256비트)
```

**핵심 성질**:

| 성질 | 설명 | 보안 의미 |
|------|------|----------|
| **결정론적** | 같은 입력 → 항상 같은 해시 | 검증 가능 |
| **일방향** | 해시에서 입력 역산 불가 | 원본 보호 |
| **눈사태 효과** | 1비트 변경 → 해시 전체 변경 | 위변조 탐지 |
| **충돌 저항** | 다른 입력이 같은 해시를 가질 확률 극히 낮음 | 고유성 보장 |

### 1.2 SHA-256의 보안에서의 활용

| 용도 | 예시 |
|------|------|
| 파일 무결성 검증 | 다운로드 파일의 SHA-256 체크섬 비교 |
| 비밀번호 저장 | 비밀번호를 해시로 저장 (원문 저장 금지) |
| 디지털 서명 | 문서 해시에 서명하여 인증 |
| 블록체인 | 블록의 해시로 체인 연결 |
| 포렌식 | 증거 파일의 해시로 원본 증명 |

---

## 2. PoW 블록체인 구조 (30분)

### 2.1 블록 구조

OpsClaw의 각 PoW 블록은 다음 필드를 포함한다:

```
  PoW Block #N
  id: 5
  project_id: "abc-123"
  agent_id: "http://10.20.30.1"
  task_order: 2
  risk_level: "low"
  exit_code: 0
  prev_hash: "00a3f5b9c8..."  | ← Block #(N-1)의 해시
  nonce: 42857  | ← mining으로 찾은 값
  block_hash: "0012de7f8a..."  | ← 이 블록의 해시
  ts_raw: "2026-03-25T10:00:01Z"
  reward: 1.0
```

### 2.2 해시 체인 구조

```
Block #1               Block #2               Block #3
  prev: "000..."         prev: "00a3f"          prev: "0012d"
  data: task1            data: task2            data: task3
  nonce: 12345           nonce: 42857           nonce: 98761
  hash: "00a3f"    --->  hash: "0012d"    --->  hash: "00f7e"

Block #2의 prev_hash = Block #1의 block_hash
Block #3의 prev_hash = Block #2의 block_hash

만약 Block #1을 수정하면:
Block #1의 hash가 변경 → Block #2의 prev_hash와 불일치
→ 체인 전체가 무효화 = 위변조 탐지!
```

### 2.3 Nonce Mining

Nonce mining은 블록 해시가 특정 조건(난이도)을 만족하는 nonce 값을 찾는 과정이다.

```
난이도 = 2 (해시가 "00"으로 시작해야 함)

시도 1: nonce=0 → hash="a3f5b9..." (시작이 "00" 아님) → 실패
시도 2: nonce=1 → hash="7c2e1d..." (시작이 "00" 아님) → 실패
...
시도 42857: nonce=42857 → hash="0012de..." (시작이 "00"!) → 성공!
```

**난이도와 소요 시간**:

| 난이도 | 조건 | 평균 시도 횟수 | 의미 |
|--------|------|-------------|------|
| 1 | 해시 "0"으로 시작 | ~16회 | 거의 즉시 |
| 2 | 해시 "00"으로 시작 | ~256회 | 수 ms |
| 3 | 해시 "000"으로 시작 | ~4,096회 | 수십 ms |
| 4 | 해시 "0000"으로 시작 | ~65,536회 | 수 초 |

---

## 3. SHA-256 직접 실습 (40분)

### 3.1 해시 계산

> **실습 목적**: 강화학습(RL) 기반으로 에이전트의 위험 판단을 자동 최적화하는 과정을 체험하기 위해 수행한다
>
> **배우는 것**: Q-learning으로 (상태, 행동) 쌍의 최적 정책을 학습하는 원리와, UCB1 전략으로 탐험/활용을 균형 잡는 방법을 이해한다
>
> **결과 해석**: rl/recommend API 응답의 recommended_action과 q_value로 학습된 최적 행동과 그 신뢰도를 판단한다
>
> **실전 활용**: 보안 자동 대응의 최적 전략 학습, 오탐 감소를 위한 임계값 자동 조정, 적응형 보안 정책 구축에 활용한다

```bash
# opsclaw 서버 접속
ssh opsclaw@10.20.30.201
```

```bash
# 문자열의 SHA-256 해시 계산
echo -n "hello" | sha256sum
# 출력: 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824  -
```

```bash
# 1글자만 바꿔도 해시가 완전히 달라짐 (눈사태 효과)
echo -n "hello" | sha256sum
# 2cf24dba5fb0a30e26e83b2ac5b9e29e...
echo -n "hellp" | sha256sum
# 완전히 다른 해시가 출력된다
```

```bash
# 파일의 SHA-256 해시
sha256sum /etc/hostname
# 파일 내용의 고유한 해시값이 출력된다
```

### 3.2 Python으로 Nonce Mining 실습

```bash
# Python으로 간단한 PoW mining 구현
python3 << 'PYTHON'
import hashlib
import time

# PoW mining 함수
def mine_block(data, prev_hash, difficulty):
    """
    data: 블록에 포함할 데이터
    prev_hash: 이전 블록의 해시
    difficulty: 선행 0의 수
    """
    # 목표: 해시가 '0' * difficulty로 시작하는 nonce 찾기
    target = '0' * difficulty
    nonce = 0
    start = time.time()

    while True:
        # 블록 내용 = prev_hash + data + nonce
        block_content = f"{prev_hash}{data}{nonce}"
        # SHA-256 해시 계산
        block_hash = hashlib.sha256(block_content.encode()).hexdigest()

        # 난이도 조건 확인
        if block_hash.startswith(target):
            elapsed = time.time() - start
            print(f"=== Mining 성공! ===")
            print(f"Data: {data}")
            print(f"Nonce: {nonce}")
            print(f"Hash: {block_hash}")
            print(f"시도 횟수: {nonce + 1}")
            print(f"소요 시간: {elapsed:.4f}초")
            return nonce, block_hash
        nonce += 1

# 난이도별 mining 실행
print("--- 난이도 1 ---")
mine_block("task:hostname on secu", "0000000000", 1)
print()
print("--- 난이도 2 ---")
mine_block("task:hostname on secu", "0000000000", 2)
print()
print("--- 난이도 3 ---")
mine_block("task:hostname on secu", "0000000000", 3)
print()
print("--- 난이도 4 ---")
mine_block("task:hostname on secu", "0000000000", 4)
PYTHON
# 난이도가 올라갈수록 시도 횟수와 소요 시간이 급격히 증가한다
```

### 3.3 해시 체인 구현

```bash
# 3-블록 해시 체인 구현
python3 << 'PYTHON'
import hashlib

def hash_block(prev_hash, data, nonce):
    """블록 해시 계산"""
    content = f"{prev_hash}{data}{nonce}"
    return hashlib.sha256(content.encode()).hexdigest()

# Genesis Block (첫 블록)
genesis_hash = hash_block("0"*64, "genesis", 0)
print(f"Block 0 (Genesis): {genesis_hash[:32]}...")

# Block 1
block1_hash = hash_block(genesis_hash, "task:check disk on secu", 12345)
print(f"Block 1: {block1_hash[:32]}...")
print(f"  prev_hash: {genesis_hash[:16]}...")

# Block 2
block2_hash = hash_block(block1_hash, "task:check firewall on secu", 67890)
print(f"Block 2: {block2_hash[:32]}...")
print(f"  prev_hash: {block1_hash[:16]}...")

# Block 3
block3_hash = hash_block(block2_hash, "task:check web on web", 11111)
print(f"Block 3: {block3_hash[:32]}...")
print(f"  prev_hash: {block2_hash[:16]}...")

# 위변조 탐지 시뮬레이션
print("\n=== 위변조 시뮬레이션 ===")
# Block 1의 데이터를 변경
tampered_hash = hash_block(genesis_hash, "task:TAMPERED DATA", 12345)
print(f"Block 1 (변조): {tampered_hash[:32]}...")
print(f"Block 2 prev_hash: {block1_hash[:16]}...")
print(f"불일치! → 위변조 탐지됨!")
PYTHON
# 한 블록이라도 수정하면 이후 모든 블록의 prev_hash가 불일치한다
```

---

## 4. OpsClaw PoW 블록 조회 (40분)

### 4.1 작업 실행 후 PoW 블록 확인

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026
```

```bash
# PoW 블록 생성을 위한 프로젝트 생성 및 실행
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week06-pow-practice",
    "request_text": "PoW 블록 생성 및 검증 실습",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export PROJECT_ID="반환된-프로젝트-ID"
# stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
```

```bash
# 3개 task 실행 → 3개 PoW 블록 생성
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo block-1-secu && hostname",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo block-2-web && hostname",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo block-3-siem && hostname",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 3개 task가 실행되고 각각 PoW 블록이 생성된다
```

### 4.2 PoW 블록 조회

```bash
# 프로젝트별 PoW 블록 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?project_id=$PROJECT_ID" \
  | python3 -c "
import sys, json
# 블록 목록을 읽기 쉬운 형태로 출력
blocks = json.load(sys.stdin)
if isinstance(blocks, list):
    for b in blocks:
        print(f\"Block #{b.get('id','')}\")
        print(f\"  agent_id: {b.get('agent_id','')}\")
        print(f\"  task_order: {b.get('task_order','')}\")
        print(f\"  prev_hash: {str(b.get('prev_hash',''))[:24]}...\")
        print(f\"  block_hash: {str(b.get('block_hash',''))[:24]}...\")
        print(f\"  nonce: {b.get('nonce','')}\")
        print(f\"  reward: {b.get('reward','')}\")
        print()
"
# 3개 블록의 상세 정보가 출력된다
```

### 4.3 체인 무결성 검증

```bash
# 전체 PoW 체인 무결성 검증
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/verify?agent_id=http://localhost:8002" \
  | python3 -m json.tool
# 정상: {"valid": true, "blocks": N, "orphans": 0, "tampered": []}
# orphans: 메인 체인에 포함되지 않은 분기 블록 수
# tampered: 위변조가 감지된 블록 목록 (빈 배열이면 정상)
```

```bash
# 특정 에이전트의 체인 검증
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/verify?agent_id=http://10.20.30.1:8002" \
  | python3 -m json.tool
# secu SubAgent의 체인만 검증
```

### 4.4 에이전트별 블록 조회

```bash
# secu SubAgent의 블록만 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?agent_id=http://10.20.30.1:8002" \
  | python3 -m json.tool
# secu에서 실행된 모든 task의 PoW 블록 목록
```

```bash
# web SubAgent의 블록만 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?agent_id=http://10.20.30.80:8002" \
  | python3 -m json.tool
```

---

## 5. 리더보드와 보상 시스템 (30분)

### 5.1 리더보드 조회

```bash
# 보상 랭킹 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/pow/leaderboard | python3 -c "
import sys, json
# 리더보드를 순위별로 출력
data = json.load(sys.stdin)
if isinstance(data, list):
    print(f\"{'순위':>4} {'Agent ID':40s} {'보상 합계':>10}\")
    print('-' * 60)
    for i, entry in enumerate(data, 1):
        print(f\"{i:>4} {entry.get('agent_id',''):40s} {entry.get('total_reward',0):>10.1f}\")
"
# 각 SubAgent의 누적 보상 점수가 순위별로 출력된다
```

### 5.2 보상 구조

| risk_level | 기본 보상 | 설명 |
|-----------|----------|------|
| low | 1.0 | 안전한 조회 작업 |
| medium | 2.0 | 설정 변경 등 중간 위험 |
| high | 3.0 | 서비스 영향 가능성 있는 작업 |
| critical | 5.0 | 시스템 핵심 변경 (confirmed 필요) |

**보상의 의미**: 보상 점수는 각 SubAgent가 얼마나 많은 작업을 성공적으로 수행했는지를 수치화한다. 이는 Week 07의 강화학습(RL)에서 최적 정책을 학습하는 데이터로 활용된다.

### 5.3 프로젝트 완료

```bash
# 프로젝트 완료 보고서
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "Week06 PoW 작업증명 실습 완료",
    "outcome": "success",
    "work_details": [
      "SHA-256 해시 함수 직접 실험 (눈사태 효과 확인)",
      "Python으로 Nonce mining 구현 (난이도 1~4 비교)",
      "3-블록 해시 체인 구현 및 위변조 탐지 시뮬레이션",
      "OpsClaw PoW 블록 생성·조회·검증",
      "리더보드로 에이전트별 보상 점수 확인"
    ]
  }' | python3 -m json.tool
```

---

## 6. 복습 퀴즈 + 과제 안내 (20분)

### 토론 주제

1. **PoW의 보안 가치**: 해시 체인 없이도 DB에 로그를 기록하면 되지 않는가? PoW가 추가로 보장하는 것은?
2. **난이도 설정**: OpsClaw에서 PoW 난이도를 높이면 보안은 올라가지만 실행 속도가 떨어진다. 적절한 난이도는?
3. **블록체인 vs 전통 감사**: 기존 SIEM 로그와 OpsClaw PoW 블록의 감사 증거로서의 차이는?

---

## 과제

### 과제 1: 해시 체인 구현 (필수)
Python으로 5-블록 해시 체인을 구현하고, 3번째 블록을 변조하여 무결성 검증이 실패하는 것을 시연하라. 코드와 실행 결과를 제출한다.

### 과제 2: PoW 블록 분석 (필수)
OpsClaw에서 최소 5개의 task를 실행하고, 생성된 PoW 블록의 block_hash, prev_hash, nonce를 표로 정리하라. 체인의 연결 관계를 그림으로 그린다.

### 과제 3: 난이도 벤치마크 (선택)
Python mining 코드를 사용하여 난이도 1~6까지 각각 100회 mining하고, 평균 시도 횟수와 소요 시간의 그래프를 그린다.

---

## 검증 체크리스트

- [ ] SHA-256의 4가지 핵심 성질을 설명할 수 있는가?
- [ ] 해시 체인이 위변조를 탐지하는 원리를 설명할 수 있는가?
- [ ] Nonce mining의 과정을 단계별로 설명할 수 있는가?
- [ ] 난이도가 mining 시간에 미치는 영향을 수치로 설명할 수 있는가?
- [ ] OpsClaw에서 PoW 블록을 조회할 수 있는가?
- [ ] PoW 체인 무결성 검증 API를 사용할 수 있는가?
- [ ] 리더보드에서 에이전트별 보상 점수를 확인할 수 있는가?

---

## 다음 주 예고

**Week 07: 강화학습(RL)과 보상**
- Q-learning과 UCB1 알고리즘 기초
- Reward 설계와 risk_level 최적화
- OpsClaw RL 학습 및 추천 API 활용
- 보상 데이터 기반 자율 의사결정

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** SHA-256의 "눈사태 효과"란?
- (a) 해시가 매우 길다  (b) **입력 1비트 변경 시 출력 해시가 완전히 달라진다**  (c) 해시가 항상 같다  (d) 속도가 느리다

**Q2.** PoW 블록의 prev_hash 역할은?
- (a) 비밀번호 저장  (b) **이전 블록과 연결하여 체인을 형성**  (c) 에이전트 인증  (d) 데이터 암호화

**Q3.** Nonce mining에서 난이도가 3이면?
- (a) 3번 시도  (b) 3초 소요  (c) **해시가 "000"으로 시작하는 nonce를 찾아야 함**  (d) 3개 블록 생성

**Q4.** PoW 체인에서 중간 블록을 변조하면?
- (a) 아무 일도 없다  (b) 그 블록만 무효화  (c) **해당 블록 이후 모든 블록의 연결이 깨진다**  (d) 자동으로 복구된다

**Q5.** OpsClaw에서 risk_level=critical의 기본 보상은?
- (a) 1.0  (b) 2.0  (c) 3.0  (d) **5.0**

**정답:** Q1:b, Q2:b, Q3:c, Q4:c, Q5:d

---
---
