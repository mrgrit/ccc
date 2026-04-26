# Week 06: 모델 탈취/추출

## 학습 목표
- 모델 추출(Model Extraction) 공격의 원리와 위협을 이해한다
- API 쿼리 기반 모델 복제 기법을 실습한다
- 모델 역공학(Reverse Engineering) 접근법을 학습한다
- 워터마킹(Watermarking)과 핑거프린팅 방어 기법을 구현한다
- 모델 도난 탐지 시스템을 구축할 수 있다

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
| 0:00-0:40 | Part 1: 모델 추출 공격 이론 | 강의 |
| 0:40-1:20 | Part 2: 모델 보호 기법 | 강의/토론 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: API 기반 모델 복제 실습 | 실습 |
| 2:10-2:50 | Part 4: 워터마킹과 탐지 시스템 | 실습 |
| 2:50-3:00 | 정리 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **모델 추출** | Model Extraction | API 응답으로 모델을 복제하는 공격 | 시험 문제를 외워서 복제 |
| **Knowledge Distillation** | Knowledge Distillation | 큰 모델의 지식을 작은 모델로 이전 | 교수가 학생에게 지식 전달 |
| **워터마킹** | Watermarking | 모델에 추적 가능한 고유 마커 삽입 | 지폐의 워터마크 |
| **핑거프린팅** | Fingerprinting | 모델의 고유 특성으로 식별 | 지문 인식 |
| **쿼리 예산** | Query Budget | 공격에 필요한 API 호출 수 | 비용 제한 |
| **충실도** | Fidelity | 복제 모델과 원본의 유사도 | 복사본의 품질 |
| **부채널** | Side Channel | 의도치 않은 정보 유출 경로 | 벽 너머로 들리는 소리 |
| **Rate Limiting** | Rate Limiting | API 호출 빈도 제한 | 출입 속도 통제 |

---

# Part 1: 모델 추출 공격 이론 (40분)

## 1.1 모델 추출이란

모델 추출은 API로만 접근 가능한 모델(블랙박스)에 쿼리를 반복하여, 유사한 기능을 하는 복제 모델을 만드는 공격이다.

```
모델 추출 공격 개요

  공격자                              피해자
  ------                             ------
  [쿼리 생성기]                       [원본 모델 (API)]
       |                                  |
       | -- 질문1: "한국의 수도는?" -----→ |
       | ←---- 답변1: "서울입니다" ------- |
       |                                  |
       | -- 질문2: "2+3은?" -----------→  |
       | ←---- 답변2: "5입니다" --------- |
       |                                  |
       | -- ... (수천~수만 회) --------→  |
       | ←---- ... ---------------------- |
       |
       v
  [학습 데이터셋 구축]
  (질문, 답변) 쌍 수만 개
       |
       v
  [대리 모델 학습]
  파인튜닝: 작은 모델이 원본과
  유사하게 응답하도록 학습
       |
       v
  [복제 모델 완성]
  원본의 ~90% 성능을 자체 보유
```

### 모델 추출의 동기

| 동기 | 설명 | 예시 |
|------|------|------|
| **경제적** | API 비용 절감 | GPT-4 API 대신 자체 모델 |
| **경쟁** | 경쟁사 모델 복제 | 상용 모델의 지식 탈취 |
| **규제 우회** | 검열 없는 복제 모델 | 안전 제한 없는 버전 |
| **연구** | 모델 내부 이해 | 행동 분석, 취약점 연구 |
| **공격 준비** | 적대적 예제 생성 | 원본 공격용 프록시 모델 |

## 1.2 추출 공격의 분류

### 유형 1: 기능적 추출 (Functional Extraction)

모델의 입출력 관계를 복제한다.

```
목표: 원본 모델 f(x)에 대해 f'(x) ≈ f(x)인 f'를 학습

  방법:
  1. 다양한 x를 생성
  2. 원본에 x를 쿼리하여 y = f(x) 수집
  3. (x, y) 쌍으로 f' 학습

  평가: 충실도(Fidelity)
  Fidelity = P(f'(x) == f(x)) for random x
```

### 유형 2: 지식 증류 (Knowledge Distillation)

원본 모델의 지식을 작은 모델로 이전한다.

```
Knowledge Distillation 과정

  [Teacher: 원본 대형 모델]
       |
       | soft labels (확률 분포)
       v
  [Student: 소형 복제 모델]
  
  Teacher: "서울" (p=0.85), "수원" (p=0.08), "부산" (p=0.05), ...
  Student: 이 확률 분포를 학습 (hard label보다 정보가 풍부)
```

### 유형 3: 부채널 추출 (Side-channel Extraction)

API 응답의 메타데이터를 활용한다.

| 부채널 | 정보 | 용도 |
|--------|------|------|
| **응답 시간** | 모델 크기/복잡도 추정 | 아키텍처 추론 |
| **토큰 확률** | logprobs (일부 API 제공) | 정밀 증류 |
| **에러 메시지** | 모델명, 버전, 제한 | 취약점 발견 |
| **응답 패턴** | 특유의 문체, 거부 패턴 | 모델 식별 |
| **Rate Limit 헤더** | 요금제, 사용량 | 서비스 구조 파악 |

## 1.3 추출 공격의 비용 분석

```
모델 추출 비용 대비 효과

  원본 모델 학습 비용:    $1,000,000+ (GPU, 데이터, 인력)
  API 추출 비용:          $1,000~$10,000 (API 호출)
  비용 비율:              0.1% ~ 1%

  추출 효율:
  ┌─────────────────────────────────────────────┐
  │ 쿼리 수    충실도     비용     시간           │
  │ 1,000      ~40%      $10     1시간          │
  │ 10,000     ~60%      $100    10시간         │
  │ 100,000    ~80%      $1,000  4일            │
  │ 1,000,000  ~90%      $10,000 40일           │
  └─────────────────────────────────────────────┘

  → 원본의 0.1% 비용으로 90% 성능 복제 가능
```

## 1.4 실제 사례

### 사례 1: OpenAI 모델의 Distillation

```
2024년 다수의 사례:
- 연구자들이 GPT-4 API로 대량 쿼리를 수행
- 수집된 (질문, 답변) 쌍으로 Llama 7B를 파인튜닝
- 결과: 특정 도메인에서 GPT-4의 ~85% 성능 달성
- 비용: GPT-4 학습비의 0.01% 미만

대응: OpenAI가 이용 약관에 "경쟁 모델 학습 금지" 조항 추가
```

### 사례 2: 모델 API 리버스 엔지니어링

```
2023-2025년 지속적 발생:
- API 응답 패턴 분석으로 모델 버전/크기 추정
- 에러 메시지에서 내부 구조 정보 유출
- Rate Limit 헤더에서 서비스 아키텍처 추론
```

---

# Part 2: 모델 보호 기법 (40분)

## 2.1 워터마킹 (Watermarking)

### 출력 워터마킹

```
출력 워터마킹 원리

  LLM 생성 과정:
  각 토큰 선택 시 확률 분포에서 샘플링

  일반:     P(token) = softmax(logits)
  워터마킹: P(token) = modified_softmax(logits, watermark_key)

  Green/Red list 방식:
  1. 토큰 사전을 Green(선호)/Red(비선호)로 분류
  2. Green 토큰의 확률을 약간 높임
  3. 생성된 텍스트에 Green 토큰이 통계적으로 더 많음
  4. 검증: Green 토큰 비율이 임계값 초과 → 워터마크 탐지

  사용자 인식: 텍스트 품질에 거의 영향 없음
  통계 검증: p-value로 워터마크 존재 확률 계산
```

### 모델 워터마킹

```
모델 자체에 워터마크 삽입

  1. 백도어 워터마크
     특정 트리거 입력에 대해 고유 응답을 생성하도록 학습
     예: "Watermark-Check-2026" → "This model is WM-ABC123"
     
  2. 파라미터 워터마크
     모델 가중치의 특정 패턴에 서명 삽입
     예: 가중치의 LSB에 서명 임베딩
```

## 2.2 핑거프린팅 (Fingerprinting)

```
모델 핑거프린팅

  특정 입력에 대한 모델의 고유 반응 패턴을 수집

  핑거프린트 입력 세트:
  ┌─────────────────────────────┐
  │ 입력              원본 응답   │
  │ "2+2="            "4"       │
  │ "Hello"           "Hi!"     │
  │ "AAAA...A(100개)" "..."     │
  │ "[특수 시퀀스]"    "..."     │
  └─────────────────────────────┘

  → 이 응답 패턴이 "지문"이 됨
  → 의심 모델에 같은 입력 → 응답 비교
  → 핑거프린트 일치 → 복제 모델로 판정
```

## 2.3 API 보안

| 방어 기법 | 설명 | 효과 |
|----------|------|------|
| **Rate Limiting** | API 호출 빈도 제한 | 대량 쿼리 방지 |
| **쿼리 예산** | 사용자별 일일 쿼리 수 제한 | 추출 비용 증가 |
| **응답 제한** | logprobs 비제공, 토큰 확률 숨김 | 정밀 증류 방지 |
| **쿼리 다양성 탐지** | 비정상 쿼리 패턴 탐지 | 추출 시도 탐지 |
| **출력 섭동** | 응답에 약간의 노이즈 추가 | 학습 데이터 품질 저하 |
| **워터마킹** | 출력에 추적 마커 삽입 | 도난 증명 |
| **이용 약관** | 모델 복제 금지 조항 | 법적 보호 |

## 2.4 탐지 메커니즘

```
모델 추출 탐지 파이프라인

  [API 요청 로그]
       |
       v
  [패턴 분석기]
  ├── 쿼리 빈도 분석 (burst detection)
  ├── 쿼리 다양성 분석 (entropy)
  ├── 쿼리 유형 분석 (분류/생성/특수)
  └── 사용자 프로파일링
       |
       v
  [이상 탐지]
  ├── 정상 사용자 프로파일과 비교
  ├── 알려진 추출 패턴 매칭
  └── 통계적 이상치 탐지
       |
       v
  [대응]
  ├── 경고 발생
  ├── Rate Limit 강화
  ├── 계정 차단
  └── 증거 수집
```

---

# Part 3: API 기반 모델 복제 실습 (40분)

> **이 실습을 왜 하는가?**
> 모델 추출 공격의 실제 과정을 체험해야 방어 기법의 필요성을 이해할 수 있다.
> 간이 추출 파이프라인을 구축하여 공격의 비용과 효과를 측정한다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 모델 추출에 필요한 쿼리 수와 시간
> - 복제 모델의 충실도 측정 방법
> - 추출 과정에서 남는 흔적
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

## 3.1 데이터 수집 파이프라인

```bash
# 모델 추출을 위한 데이터 수집기
cat > /tmp/model_extract.py << 'PYEOF'
import json
import urllib.request
import time
import random

OLLAMA_URL = "http://10.20.30.200:11434/v1/chat/completions"
TARGET_MODEL = "gemma3:12b"

class ModelExtractor:
    """API 기반 모델 추출 시뮬레이터"""

    # 다양한 도메인의 질문 생성
    QUERY_TEMPLATES = [
        # 일반 지식
        "{country}의 수도는 어디인가요?",
        "{topic}에 대해 한 문장으로 설명해주세요.",
        # 분류
        "'{text}'의 감정은 긍정/부정/중립 중 무엇인가요? 한 단어로만 답하세요.",
        # 추론
        "{num1} + {num2} = ?",
        # 코드
        "Python으로 {task}하는 함수를 작성하세요.",
    ]

    COUNTRIES = ["한국", "일본", "미국", "프랑스", "독일", "브라질", "호주"]
    TOPICS = ["양자컴퓨팅", "블록체인", "딥러닝", "사이버보안", "클라우드"]
    TEXTS = ["정말 좋은 서비스입니다", "최악의 경험이었어요", "그냥 보통이에요"]
    TASKS = ["리스트 정렬", "피보나치 수열 계산", "문자열 뒤집기"]

    def __init__(self):
        self.collected = []
        self.query_count = 0
        self.total_tokens = 0
        self.start_time = None

    def generate_query(self):
        template = random.choice(self.QUERY_TEMPLATES)
        try:
            query = template.format(
                country=random.choice(self.COUNTRIES),
                topic=random.choice(self.TOPICS),
                text=random.choice(self.TEXTS),
                num1=random.randint(1, 100),
                num2=random.randint(1, 100),
                task=random.choice(self.TASKS),
            )
        except KeyError:
            query = template
        return query

    def query_model(self, prompt, system="Answer concisely in Korean."):
        payload = json.dumps({
            "model": TARGET_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 200,
        }).encode()
        req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", len(content) // 4)
                return content, tokens
        except Exception as e:
            return f"ERROR: {e}", 0

    def extract(self, n_queries=20):
        self.start_time = time.time()
        print(f"=== 모델 추출 시작: {n_queries}개 쿼리 ===\n")

        for i in range(n_queries):
            query = self.generate_query()
            response, tokens = self.query_model(query)
            self.query_count += 1
            self.total_tokens += tokens

            self.collected.append({
                "query": query,
                "response": response,
                "tokens": tokens,
            })
            print(f"[{i+1}/{n_queries}] Q: {query[:40]}... → A: {response[:40]}...")
            time.sleep(0.3)

        elapsed = time.time() - self.start_time
        print(f"\n=== 수집 완료 ===")
        print(f"  쿼리 수: {self.query_count}")
        print(f"  총 토큰: {self.total_tokens}")
        print(f"  소요 시간: {elapsed:.1f}초")
        print(f"  수집 속도: {self.query_count/elapsed:.1f} qps")

        return self.collected

    def save(self, path="/tmp/extraction_data.jsonl"):
        with open(path, "w") as f:
            for item in self.collected:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"저장: {path} ({len(self.collected)}건)")


if __name__ == "__main__":
    extractor = ModelExtractor()
    data = extractor.extract(n_queries=15)
    extractor.save()
PYEOF

python3 /tmp/model_extract.py
```

## 3.2 충실도 측정

```bash
# 복제 모델의 충실도 측정 (동일 모델에서 시뮬레이션)
cat > /tmp/fidelity_test.py << 'PYEOF'
import json
import urllib.request
import time

OLLAMA_URL = "http://10.20.30.200:11434/v1/chat/completions"

# 일관성 테스트: 같은 질문을 여러 번 하여 응답 일관성 측정
TEST_QUERIES = [
    "한국의 수도는?",
    "1+1=?",
    "Python에서 리스트를 정렬하는 방법은?",
    "AI의 가장 큰 위험은?",
    "HTTP 상태코드 404는 무엇을 의미하나요?",
]

def query(model, prompt):
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "Answer concisely in Korean."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,  # 낮은 temperature로 일관성 높임
        "max_tokens": 100,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except:
        return "ERROR"

def similarity(text1, text2):
    """간이 텍스트 유사도 (토큰 겹침)"""
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(intersection) / len(union) if union else 0.0

print("=== 모델 응답 충실도 테스트 ===\n")
print(f"{'질문':30s} | {'응답1':20s} | {'응답2':20s} | {'유사도':6s}")
print("-" * 80)

total_sim = 0
for q in TEST_QUERIES:
    r1 = query("gemma3:12b", q)
    time.sleep(0.5)
    r2 = query("gemma3:12b", q)
    sim = similarity(r1, r2)
    total_sim += sim
    print(f"{q:30s} | {r1[:18]:20s} | {r2[:18]:20s} | {sim:.3f}")
    time.sleep(0.5)

avg_sim = total_sim / len(TEST_QUERIES)
print(f"\n평균 자기 일관성: {avg_sim:.3f}")
print(f"해석: {'높음' if avg_sim > 0.6 else '중간' if avg_sim > 0.3 else '낮음'}")
PYEOF

python3 /tmp/fidelity_test.py
```

## 3.3 모델 핑거프린팅

```bash
# 모델 핑거프린팅: 고유 응답 패턴 수집
cat > /tmp/fingerprint.py << 'PYEOF'
import json
import urllib.request
import hashlib
import time

OLLAMA_URL = "http://10.20.30.200:11434/v1/chat/completions"

# 핑거프린트 입력 세트 (고정)
FINGERPRINT_INPUTS = [
    "What is 2+2?",
    "Say hello in 3 languages.",
    "Complete: The quick brown fox",
    "What is your name?",
    "Translate to Korean: I love AI safety",
    "AAAAAAAAAA",  # 반복 패턴
    "###",  # 특수 문자
    "null undefined NaN",  # 에지 케이스
]

def query(model, prompt):
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 50,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except:
        return "ERROR"

def generate_fingerprint(model):
    responses = []
    for prompt in FINGERPRINT_INPUTS:
        resp = query(model, prompt)
        responses.append(resp[:100])
        time.sleep(0.3)

    # 핑거프린트 해시 생성
    combined = "|".join(responses)
    fp_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]

    return {
        "model": model,
        "fingerprint": fp_hash,
        "responses": responses,
    }

print("=== 모델 핑거프린팅 ===\n")
fp = generate_fingerprint("gemma3:12b")
print(f"모델: {fp['model']}")
print(f"핑거프린트: {fp['fingerprint']}")
print(f"\n응답 패턴:")
for i, (inp, resp) in enumerate(zip(FINGERPRINT_INPUTS, fp['responses'])):
    print(f"  [{i+1}] {inp:35s} → {resp[:40]}")

# 핑거프린트 저장
with open("/tmp/model_fingerprint.json", "w") as f:
    json.dump(fp, f, ensure_ascii=False, indent=2)
print(f"\n핑거프린트 저장: /tmp/model_fingerprint.json")
PYEOF

python3 /tmp/fingerprint.py
```

---

# Part 4: 워터마킹과 탐지 시스템 (40분)

> **이 실습을 왜 하는가?**
> 모델 도난을 방지하고, 도난 시 증거를 확보하기 위한 기술을 구현한다.
> 워터마킹, 핑거프린팅, 이상 쿼리 탐지 등 방어 기술을 실습한다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 텍스트 워터마킹의 구현 방법
> - 추출 시도 탐지 패턴
> - 모델 보호 종합 전략
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

## 4.1 텍스트 워터마킹

```bash
# 간이 텍스트 워터마킹 시스템
cat > /tmp/watermark.py << 'PYEOF'
import hashlib
import json
import re

class TextWatermarker:
    """텍스트 출력에 통계적 워터마크를 삽입/탐지"""

    def __init__(self, secret_key="watermark-secret-2026"):
        self.key = secret_key

    def _green_tokens(self, prev_token):
        """이전 토큰 기반으로 Green/Red 토큰 집합 결정"""
        seed = hashlib.sha256(f"{self.key}:{prev_token}".encode()).hexdigest()
        # 해시값 기반으로 확률 결정
        return int(seed[:8], 16) % 2 == 0  # 50% Green

    def embed(self, text):
        """텍스트에 워터마크 삽입 (동의어 치환 방식)"""
        SYNONYMS = {
            "좋은": "우수한",
            "나쁜": "좋지 않은",
            "큰": "대규모의",
            "작은": "소규모의",
            "중요한": "핵심적인",
            "사용하다": "활용하다",
            "확인하다": "점검하다",
            "시작하다": "개시하다",
        }
        watermarked = text
        substitutions = 0
        for original, replacement in SYNONYMS.items():
            if original in watermarked:
                watermarked = watermarked.replace(original, replacement, 1)
                substitutions += 1

        return {
            "original": text,
            "watermarked": watermarked,
            "substitutions": substitutions,
        }

    def detect(self, text, threshold=2):
        """워터마크 탐지: 치환된 동의어의 수를 확인"""
        WATERMARK_INDICATORS = [
            "우수한", "좋지 않은", "대규모의", "소규모의",
            "핵심적인", "활용하다", "점검하다", "개시하다",
        ]
        found = []
        for indicator in WATERMARK_INDICATORS:
            if indicator in text:
                found.append(indicator)

        is_watermarked = len(found) >= threshold
        confidence = min(len(found) / max(threshold, 1), 1.0)

        return {
            "is_watermarked": is_watermarked,
            "confidence": confidence,
            "indicators_found": found,
            "indicator_count": len(found),
        }


# 테스트
wm = TextWatermarker()

test_text = "서버 보안은 중요한 주제입니다. 좋은 방화벽을 사용하다 보면 큰 효과를 확인하다."
result = wm.embed(test_text)
print("=== 워터마킹 삽입 ===")
print(f"원본: {result['original']}")
print(f"워터마크: {result['watermarked']}")
print(f"치환 수: {result['substitutions']}")

print("\n=== 워터마크 탐지 ===")
detect_result = wm.detect(result['watermarked'])
print(f"탐지 결과: {detect_result['is_watermarked']}")
print(f"신뢰도: {detect_result['confidence']:.2f}")
print(f"발견된 지표: {detect_result['indicators_found']}")

# 워터마크 없는 텍스트 테스트
clean_text = "서버 보안은 중요한 주제입니다. 좋은 방화벽을 사용하면 큰 효과가 있습니다."
clean_result = wm.detect(clean_text)
print(f"\n정상 텍스트 탐지: {clean_result['is_watermarked']} (지표: {clean_result['indicator_count']}개)")
PYEOF

python3 /tmp/watermark.py
```

## 4.2 추출 시도 탐지

```bash
# API 사용 패턴 기반 모델 추출 시도 탐지
cat > /tmp/extraction_detector.py << 'PYEOF'
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta

class ExtractionDetector:
    """모델 추출 시도를 API 사용 패턴으로 탐지"""

    THRESHOLDS = {
        "queries_per_minute": 20,
        "queries_per_hour": 500,
        "query_diversity_min": 0.3,  # 최소 다양성 (낮으면 의심)
        "avg_response_usage_min": 0.5,  # 응답을 실제로 사용하는지
        "systematic_pattern_score": 0.7,  # 체계적 패턴 점수
    }

    def __init__(self):
        self.user_logs = defaultdict(list)
        self.alerts = []

    def log_query(self, user_id, query, response_tokens):
        self.user_logs[user_id].append({
            "timestamp": datetime.now(),
            "query": query,
            "response_tokens": response_tokens,
        })

    def analyze_user(self, user_id):
        logs = self.user_logs[user_id]
        if len(logs) < 5:
            return {"risk": "low", "detail": "데이터 부족"}

        findings = []

        # 1. 빈도 분석
        recent = [l for l in logs if (datetime.now() - l["timestamp"]).seconds < 60]
        qpm = len(recent)
        if qpm > self.THRESHOLDS["queries_per_minute"]:
            findings.append(f"분당 쿼리 {qpm}회 (임계: {self.THRESHOLDS['queries_per_minute']})")

        # 2. 다양성 분석
        queries = [l["query"] for l in logs]
        unique_words = set()
        for q in queries:
            unique_words.update(q.split())
        total_words = sum(len(q.split()) for q in queries)
        diversity = len(unique_words) / max(total_words, 1)

        if diversity < self.THRESHOLDS["query_diversity_min"]:
            findings.append(f"쿼리 다양성 낮음: {diversity:.2f}")

        # 3. 체계적 패턴 탐지
        # 연속 번호, 순차 질문 등
        sequential_count = 0
        for i in range(1, len(queries)):
            if queries[i][:5] == queries[i-1][:5]:
                sequential_count += 1
        systematic_score = sequential_count / max(len(queries) - 1, 1)

        if systematic_score > self.THRESHOLDS["systematic_pattern_score"]:
            findings.append(f"체계적 패턴 감지: {systematic_score:.2f}")

        risk = "critical" if len(findings) >= 3 else "high" if len(findings) >= 2 else "medium" if findings else "low"

        return {
            "user_id": user_id,
            "total_queries": len(logs),
            "qpm": qpm,
            "diversity": round(diversity, 3),
            "systematic_score": round(systematic_score, 3),
            "risk": risk,
            "findings": findings,
        }


# 시뮬레이션
detector = ExtractionDetector()

# 정상 사용자
normal_queries = [
    "오늘 날씨 어때?", "파이썬 설치 방법", "맛있는 음식 추천",
    "서울에서 부산까지 거리", "AI 뉴스 알려줘",
]
for q in normal_queries:
    detector.log_query("user_normal", q, 50)

# 추출 시도 사용자
extract_queries = [
    f"{c}의 수도는?" for c in ["한국", "일본", "미국", "프랑스", "독일",
                              "영국", "중국", "이탈리아", "스페인", "캐나다",
                              "브라질", "호주", "인도", "러시아", "멕시코"]
]
for q in extract_queries:
    detector.log_query("user_extract", q, 20)

# 분석
print("=== 모델 추출 시도 탐지 ===\n")
for uid in ["user_normal", "user_extract"]:
    result = detector.analyze_user(uid)
    print(f"[{uid}]")
    print(f"  총 쿼리: {result['total_queries']}")
    print(f"  다양성: {result['diversity']}")
    print(f"  체계성: {result['systematic_score']}")
    print(f"  위험도: {result['risk']}")
    for f in result.get("findings", []):
        print(f"  경고: {f}")
    print()
PYEOF

python3 /tmp/extraction_detector.py
```

## 4.3 Bastion 연동

```bash
curl -s -X POST http://localhost:9100/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ccc-api-key-2026" \
  -d '{
    "name": "model-theft-week06",
    "request_text": "모델 추출/탈취 테스트 - API 복제, 핑거프린팅, 워터마킹, 추출 탐지",
    "master_mode": "external"
  }' | python3 -m json.tool
```

---

## 체크리스트

- [ ] 모델 추출 공격의 원리와 동기를 설명할 수 있다
- [ ] Knowledge Distillation의 과정을 이해한다
- [ ] API 기반 모델 복제 파이프라인을 구축할 수 있다
- [ ] 충실도(Fidelity)를 정의하고 측정할 수 있다
- [ ] 모델 핑거프린팅을 수행할 수 있다
- [ ] 텍스트 워터마킹을 구현할 수 있다
- [ ] 워터마크 탐지를 수행할 수 있다
- [ ] 추출 시도 탐지 시스템을 구축할 수 있다
- [ ] API 보안 기법을 열거하고 설명할 수 있다
- [ ] 부채널 정보 유출 위험을 인식한다

---

## 4.4 모델 보호 종합 프레임워크

```bash
# 종합 모델 보호 프레임워크
cat > /tmp/model_protection.py << 'PYEOF'
import json
import hashlib
from datetime import datetime

class ModelProtectionFramework:
    """종합 모델 보호 프레임워크"""

    def __init__(self, model_name):
        self.model_name = model_name
        self.protection_layers = {}

    def add_rate_limiting(self, max_per_minute=20, max_per_hour=500, max_per_day=5000):
        self.protection_layers["rate_limiting"] = {
            "per_minute": max_per_minute,
            "per_hour": max_per_hour,
            "per_day": max_per_day,
            "action": "429 Too Many Requests",
        }

    def add_query_monitoring(self, diversity_threshold=0.3, systematic_threshold=0.7):
        self.protection_layers["query_monitoring"] = {
            "diversity_threshold": diversity_threshold,
            "systematic_threshold": systematic_threshold,
            "action": "경고 + Rate Limit 강화",
        }

    def add_watermarking(self, method="synonym_replacement"):
        self.protection_layers["watermarking"] = {
            "method": method,
            "detection_threshold": 3,
            "action": "출력에 자동 삽입",
        }

    def add_fingerprinting(self, n_probes=10):
        self.protection_layers["fingerprinting"] = {
            "n_probes": n_probes,
            "stored": True,
            "action": "도난 모델 식별용",
        }

    def add_legal_protection(self):
        self.protection_layers["legal"] = {
            "tos_clause": "경쟁 모델 학습을 위한 API 사용 금지",
            "license": "비상업적 사용만 허용",
            "monitoring": "이용 약관 위반 감지",
        }

    def generate_report(self):
        report = f"""
{'='*60}
모델 보호 프레임워크 보고서
{'='*60}
모델: {self.model_name}
보고일: {datetime.now().strftime('%Y-%m-%d')}
보호 계층: {len(self.protection_layers)}개

보호 계층 상세:
"""
        for i, (name, config) in enumerate(self.protection_layers.items(), 1):
            report += f"\n  [{i}] {name}\n"
            for key, value in config.items():
                report += f"      {key}: {value}\n"

        report += f"""
종합 보호 수준:
  - Rate Limiting: {'적용' if 'rate_limiting' in self.protection_layers else '미적용'}
  - 쿼리 모니터링: {'적용' if 'query_monitoring' in self.protection_layers else '미적용'}
  - 워터마킹: {'적용' if 'watermarking' in self.protection_layers else '미적용'}
  - 핑거프린팅: {'적용' if 'fingerprinting' in self.protection_layers else '미적용'}
  - 법적 보호: {'적용' if 'legal' in self.protection_layers else '미적용'}

보호 등급: {'Strong' if len(self.protection_layers) >= 4 else 'Medium' if len(self.protection_layers) >= 2 else 'Weak'}
{'='*60}
"""
        return report


# 사용 예시
framework = ModelProtectionFramework("AcmeCorp SecureBot (gemma3:12b)")
framework.add_rate_limiting()
framework.add_query_monitoring()
framework.add_watermarking()
framework.add_fingerprinting()
framework.add_legal_protection()

print(framework.generate_report())
PYEOF

python3 /tmp/model_protection.py
```

## 4.5 모델 보호 전략 종합

```
모델 보호 종합 전략

  기술적 보호:
  ├── API Rate Limiting (분/시/일 단위)
  ├── 쿼리 예산 (사용자별 일일 한도)
  ├── 출력 제한 (logprobs 비공개, 토큰 확률 숨김)
  ├── 응답 노이즈 추가 (학습 데이터 품질 저하)
  ├── 출력 워터마킹 (Green/Red list)
  ├── 모델 핑거프린팅 (고유 응답 패턴)
  └── 이상 쿼리 탐지 (다양성, 체계성 분석)

  운영적 보호:
  ├── 접근 제어 (API 키 인증, IP 화이트리스트)
  ├── 사용량 모니터링 (대시보드)
  ├── 감사 로그 (전체 쿼리/응답 기록)
  └── 정기 보안 감사

  법적 보호:
  ├── 이용 약관 (경쟁 모델 학습 금지)
  ├── 라이선스 (비상업적 사용 제한)
  ├── 특허/저작권 보호
  └── 법적 대응 준비 (증거 수집)

  탐지 및 대응:
  ├── 추출 시도 실시간 탐지
  ├── 자동 Rate Limit 강화
  ├── 계정 차단
  └── 포렌식 증거 보존
```

---

## 과제

### 과제 1: 모델 핑거프린트 비교 (필수)
- Ollama에서 사용 가능한 2개 이상의 모델에 대해 핑거프린트 생성
- 핑거프린트 간 유사도를 계산하여 모델 구별 가능성 분석
- 결과를 표와 그래프로 정리

### 과제 2: 추출 탐지기 개선 (필수)
- extraction_detector.py에 시계열 분석 추가 (시간대별 쿼리 패턴)
- 정상 사용자 5명 + 추출 시도자 3명의 시뮬레이션 데이터 생성
- precision/recall 측정 및 보고

### 과제 3: 모델 보호 정책 설계 (심화)
- 가상의 LLM 서비스를 위한 종합 모델 보호 정책 설계
- 포함: API 보안, 워터마킹, 핑거프린팅, 이상 탐지, 법적 대응
- 비용 대비 효과 분석 포함

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### Ollama + LangChain
> **역할:** 로컬 LLM 서빙(Ollama) + 체인 오케스트레이션(LangChain)  
> **실행 위치:** `bastion (LLM 서버)`  
> **접속/호출:** `OLLAMA_HOST=http://10.20.30.201:11434`, Python `from langchain_ollama import OllamaLLM`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `~/.ollama/models/` | 다운로드된 모델 블롭 |
| `/etc/systemd/system/ollama.service` | 서비스 유닛 |

**핵심 설정·키**

- `OLLAMA_HOST=0.0.0.0:11434` — 외부 바인드
- `OLLAMA_KEEP_ALIVE=30m` — 모델 유휴 유지
- `LLM_MODEL=gemma3:4b (env)` — CCC 기본 모델

**로그·확인 명령**

- `journalctl -u ollama` — 서빙 로그
- `LangChain `verbose=True`` — 체인 단계 출력

**UI / CLI 요점**

- `ollama list` — 설치된 모델
- `curl -XPOST $OLLAMA_HOST/api/generate -d '{...}'` — REST 생성
- LangChain `RunnableSequence | parser` — 체인 조립 문법

> **해석 팁.** Ollama는 **첫 호출에 모델 로드**가 커서 지연이 크다. 성능 실험 시 워밍업 호출을 배제하고 측정하자.

---

## 실제 사례 (WitFoo Precinct 6)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화됨.

### Case 1: `T1041 (Data Theft)` 패턴

```
incident_id=d45fc680-cb9b-11ee-9d8c-014a3c92d0a7 mo_name=Data Theft
red=172.25.238.143 blue=100.64.5.119 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

### Case 2: `T1041 (Data Theft)` 패턴

```
incident_id=c6f8acf0-df14-11ee-9778-4184b1db151c mo_name=Data Theft
red=100.64.3.190 blue=100.64.3.183 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

