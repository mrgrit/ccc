# Week 08: 적대적 입력 심화

## 학습 목표
- 적대적 입력(Adversarial Input)의 이론적 배경을 심화 학습한다
- 텍스트 적대적 샘플 생성 기법을 실습한다
- 이미지 적대적 샘플의 원리를 이해하고 시뮬레이션한다
- 멀티모달 적대적 공격의 가능성을 분석한다
- 적대적 입력 방어 기법(적대적 훈련, 입력 정화)을 구현한다

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
| 0:00-0:40 | Part 1: 적대적 입력 이론 심화 | 강의 |
| 0:40-1:20 | Part 2: 텍스트/이미지 적대적 샘플 | 강의/토론 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: 텍스트 적대적 샘플 생성 실습 | 실습 |
| 2:10-2:50 | Part 4: 적대적 입력 방어 구현 | 실습 |
| 2:50-3:00 | 복습 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **적대적 예제** | Adversarial Example | AI를 속이도록 설계된 입력 | 눈속임 |
| **섭동** | Perturbation | 원본에 가하는 미세한 변형 | 눈에 보이지 않는 수정 |
| **FGSM** | Fast Gradient Sign Method | 경사도 기반 공격 기법 | 가장 효과적인 방향으로 한 걸음 |
| **PGD** | Projected Gradient Descent | 반복적 경사도 공격 | 여러 걸음 반복 |
| **적대적 훈련** | Adversarial Training | 적대적 예제로 학습하여 강건화 | 백신 접종 |
| **입력 정화** | Input Purification | 입력에서 적대적 섭동을 제거 | 소독/정화 |
| **전이성** | Transferability | 한 모델의 공격이 다른 모델에도 유효 | 만능 열쇠 |
| **강건성** | Robustness | 적대적 입력에 대한 내성 | 면역력 |

---

# Part 1: 적대적 입력 이론 심화 (40분)

## 1.1 적대적 예제의 수학적 정의

적대적 예제는 원본 입력 x에 작은 섭동 delta를 더하여, 모델이 잘못된 예측을 하도록 만드는 입력이다.

```
수학적 정의:

  원본: x, 정상 예측: f(x) = y (정답)
  
  적대적: x' = x + delta
  조건:   ||delta|| < epsilon (작은 변화)
  결과:   f(x') = y' != y (오분류)

  목표: delta를 최소화하면서 오분류를 유발

  비표적 공격: f(x') != y (아무 잘못된 답)
  표적 공격:  f(x') = t  (특정 답 t로 유도)
```

### 이미지에서의 적대적 예제

```
이미지 적대적 예제 (시각적 설명)

  [원본 이미지: 판다]     +     [미세 노이즈]     =     [적대적 이미지]
  사람: "판다"                  사람: "노이즈?"         사람: "판다" (변화 모름)
  모델: "판다" (99.7%)          (눈에 거의 안 보임)     모델: "원숭이" (99.3%)
  
  핵심: 사람 눈에는 동일하게 보이지만 모델은 전혀 다르게 인식
```

### 텍스트에서의 적대적 예제

```
텍스트 적대적 예제

  원본: "이 영화는 정말 재미있었습니다"
  분류: 긍정 (0.95)

  적대적 변형 1 (동의어 치환):
  "이 영화는 진짜 재미있었습니다"
  분류: 부정 (0.62)  ← 동의어 하나로 반전

  적대적 변형 2 (문자 교란):
  "이 영화는 정말 재미잇었습니다"  (오타 삽입)
  분류: 부정 (0.51)

  적대적 변형 3 (삽입):
  "이 영화는 정말 매우 재미있었습니다"
  분류: 부정 (0.48)
```

## 1.2 주요 공격 기법

### 화이트박스 공격 (모델 접근 가능)

| 기법 | 설명 | 복잡도 | 효과 |
|------|------|--------|------|
| **FGSM** | 1회 경사도 업데이트 | O(1) | 빠르지만 약한 공격 |
| **PGD** | 반복 경사도 업데이트 | O(n) | 강한 공격 |
| **C&W** | 최적화 기반 | O(n^2) | 매우 강한 공격 |
| **AutoAttack** | 앙상블 공격 | O(n) | 벤치마크 표준 |

### 블랙박스 공격 (API만 접근)

| 기법 | 설명 | 쿼리 수 | 효과 |
|------|------|---------|------|
| **전이 공격** | 대리 모델에서 생성한 공격을 전이 | 0 (추론시) | 중간 |
| **스코어 기반** | 출력 확률로 경사도 추정 | 수천 | 높음 |
| **결정 기반** | 최종 라벨만으로 공격 | 수만 | 높음 |
| **쿼리 효율** | 차원 축소 기반 | 수백 | 중간 |

## 1.3 텍스트 적대적 공격의 특수성

텍스트는 이미지와 달리 이산적(discrete)이므로 경사도 기반 공격이 직접 적용되지 않는다.

```
이미지 vs 텍스트 적대적 공격

  이미지 (연속 공간):
  - 픽셀값을 미세하게 조정 (0.001 단위)
  - 경사도를 직접 사용 가능
  - 변화가 사람 눈에 보이지 않음

  텍스트 (이산 공간):
  - 단어를 "0.5만큼" 변경할 수 없음
  - 단어 교체, 삽입, 삭제만 가능
  - 작은 변화도 의미가 바뀔 수 있음

  텍스트 공격 전략:
  1. 동의어 치환 (Synonym Swap)
  2. 문자 교란 (Character Perturbation)
  3. 문장 패러프레이징 (Paraphrasing)
  4. 구조 변형 (Structural Modification)
```

## 1.4 전이성 (Transferability)

```
적대적 예제의 전이성

  모델 A에서 생성한 적대적 예제 x'
       ↓
  모델 B에도 적용 → 성공 확률 ~40-70%
  모델 C에도 적용 → 성공 확률 ~30-60%

  전이성이 높은 조건:
  - 유사한 아키텍처 (같은 계열 모델)
  - 유사한 학습 데이터
  - 앙상블 공격 (여러 모델에 동시 최적화)

  보안 함의:
  - 블랙박스 모델도 공격 가능
  - 대리 모델로 공격 생성 → 원본에 전이
```

---

# Part 2: 텍스트/이미지 적대적 샘플 (40분)

## 2.1 텍스트 적대적 공격 기법

### 문자 수준 공격

| 기법 | 예시 | 사람 인식 | 모델 영향 |
|------|------|----------|----------|
| **오타 삽입** | "재미있다" → "재미잇다" | 이해 가능 | 혼란 |
| **문자 교체** | "좋다" → "졸다" | 다른 단어 | 오분류 |
| **유사 문자** | "security" → "secur1ty" | 유사 | 미인식 |
| **제로폭 삽입** | "hack" → "ha\u200bck" | 동일 | 토큰 분리 |
| **유니코드 혼동** | "a" → "а" (키릴) | 동일 | 다른 토큰 |

### 단어 수준 공격

| 기법 | 예시 | 의미 보존 | 효과 |
|------|------|----------|------|
| **동의어 치환** | "좋은" → "훌륭한" | 높음 | 중간 |
| **반의어 삽입** | "좋은 아닌" → 이중부정 | 혼란 | 높음 |
| **중요 단어 삭제** | "정말 좋다" → "좋다" | 일부 | 중간 |
| **단어 순서 변경** | "영화 좋다" → "좋다 영화" | 낮음 | 높음 |

### 문장 수준 공격

| 기법 | 예시 | 자연스러움 | 효과 |
|------|------|----------|------|
| **패러프레이징** | 문장 전체를 다른 표현으로 | 높음 | 중간 |
| **문장 추가** | 무관한 문장 삽입 | 낮음 | 높음 |
| **구조 변경** | 능동→수동, 긍정→이중부정 | 중간 | 중간 |

## 2.2 이미지 적대적 공격 기법

```
이미지 공격 기법 분류

  1. 픽셀 섭동 (Pixel Perturbation)
     - L_inf: 모든 픽셀을 최대 epsilon만큼 변경
     - L_2: 전체 변화량의 유클리드 노름 제한
     - L_0: 변경된 픽셀 수 제한

  2. 패치 공격 (Patch Attack)
     - 이미지의 특정 영역에 패치를 부착
     - 사람에게는 스티커처럼 보임
     - 물리적 환경에서도 작동 가능

  3. 공간 변환 (Spatial Transformation)
     - 회전, 이동, 왜곡으로 오분류 유도
     - 자연스러운 변형처럼 보임
```

## 2.3 오디오 적대적 공격

```
오디오 공격

  원본 오디오: "오늘 날씨가 좋습니다"
  적대적 오디오: "오늘 날씨가 좋습니다" + [미세 노이즈]
  
  사람 귀: "오늘 날씨가 좋습니다" (동일하게 들림)
  음성 인식: "계좌 이체 실행" (전혀 다르게 인식)

  응용:
  - 스마트 스피커 공격 (Alexa, Siri)
  - 음성 인증 우회
  - 음성 명령 주입
```

---

# Part 3: 텍스트 적대적 샘플 생성 실습 (40분)

> **이 실습을 왜 하는가?**
> 텍스트 적대적 샘플을 직접 생성하여, 텍스트 분류/생성 모델의 취약성을 체험한다.
> LLM 기반 시스템의 입력 검증 강화에 필수적인 이해를 제공한다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 텍스트 적대적 공격의 실제 효과
> - 동의어 치환, 문자 교란 등의 구체적 기법
> - 모델별 강건성 차이
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

## 3.1 텍스트 적대적 생성기

```bash
# 텍스트 적대적 샘플 생성기
cat > /tmp/text_adversarial.py << 'PYEOF'
import json
import random
import urllib.request
import time

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"

class TextAdversarialGenerator:
    """텍스트 적대적 샘플 생성기"""

    SYNONYM_MAP = {
        "좋은": ["훌륭한", "우수한", "뛰어난", "멋진"],
        "나쁜": ["형편없는", "열악한", "최악의", "끔찍한"],
        "정말": ["진짜", "매우", "아주", "참으로"],
        "재미있다": ["흥미롭다", "즐겁다", "신나다"],
        "서비스": ["품질", "대응", "지원"],
        "추천": ["권장", "제안", "소개"],
    }

    CHAR_SUBSTITUTIONS = {
        'ㅎ': 'ㅍ', 'ㅋ': 'ㅌ', 'ㅅ': 'ㅆ',
        'a': '@', 'e': '3', 'o': '0', 'i': '1',
    }

    ZERO_WIDTH_CHARS = ['\u200b', '\u200c', '\u200d', '\ufeff']

    def synonym_attack(self, text, n_swaps=1):
        """동의어 치환 공격"""
        result = text
        swapped = 0
        for original, synonyms in self.SYNONYM_MAP.items():
            if original in result and swapped < n_swaps:
                replacement = random.choice(synonyms)
                result = result.replace(original, replacement, 1)
                swapped += 1
        return result

    def typo_attack(self, text, n_typos=1):
        """오타 삽입 공격"""
        chars = list(text)
        positions = [i for i, c in enumerate(chars) if c.strip() and not c.isspace()]
        if not positions:
            return text
        for _ in range(min(n_typos, len(positions))):
            pos = random.choice(positions)
            # 인접 문자와 교체
            if pos < len(chars) - 1:
                chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
        return "".join(chars)

    def invisible_char_attack(self, text):
        """제로폭 문자 삽입"""
        words = text.split()
        result = []
        for word in words:
            if random.random() < 0.3:
                mid = len(word) // 2
                word = word[:mid] + random.choice(self.ZERO_WIDTH_CHARS) + word[mid:]
            result.append(word)
        return " ".join(result)

    def homoglyph_attack(self, text):
        """유사 문자 치환 (영문 부분)"""
        HOMOGLYPHS = {'a': 'а', 'e': 'е', 'o': 'о', 'p': 'р', 'c': 'с'}
        chars = list(text)
        for i, c in enumerate(chars):
            if c.lower() in HOMOGLYPHS and random.random() < 0.3:
                chars[i] = HOMOGLYPHS[c.lower()]
        return "".join(chars)

    def generate_all(self, text):
        """모든 공격 기법 적용"""
        return {
            "original": text,
            "synonym": self.synonym_attack(text),
            "typo": self.typo_attack(text),
            "invisible": self.invisible_char_attack(text),
            "homoglyph": self.homoglyph_attack(text),
        }


def test_with_llm(text, task="감정 분석"):
    system = f"다음 텍스트의 감정을 '긍정', '부정', '중립' 중 하나로만 분류하세요. 한 단어로 답하세요."
    payload = json.dumps({
        "model": "gemma3:12b",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        "temperature": 0.0,
        "max_tokens": 10,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except:
        return "error"


# 테스트
gen = TextAdversarialGenerator()

test_texts = [
    ("이 제품은 정말 좋은 품질입니다. 강력 추천합니다.", "긍정"),
    ("서비스가 정말 나쁜 경험이었습니다.", "부정"),
]

print("=== 텍스트 적대적 샘플 테스트 ===\n")
for text, expected in test_texts:
    variants = gen.generate_all(text)
    print(f"원본: {text} (기대: {expected})")
    for name, variant in variants.items():
        result = test_with_llm(variant)
        match = expected[:2] in result if result != "error" else False
        status = "일치" if match else "불일치"
        display = variant if name != "invisible" else f"{variant} (제로폭 포함)"
        print(f"  {name:12s}: {display[:50]:50s} → {result:6s} [{status}]")
        time.sleep(0.5)
    print()
PYEOF

python3 /tmp/text_adversarial.py
```

## 3.2 적대적 샘플 대량 생성 및 효과 측정

```bash
# 대량 테스트로 공격 효과 측정
cat > /tmp/adv_benchmark.py << 'PYEOF'
import json
import urllib.request
import random
import time
import sys

sys.path.insert(0, "/tmp")
from text_adversarial import TextAdversarialGenerator

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"

BENCHMARK = [
    ("이 영화 정말 재미있었습니다. 추천합니다.", "긍정"),
    ("최고의 서비스였습니다. 다시 방문하겠습니다.", "긍정"),
    ("품질이 뛰어나고 가격도 합리적입니다.", "긍정"),
    ("직원들이 매우 친절했습니다.", "긍정"),
    ("이 제품은 실망스럽습니다. 추천하지 않습니다.", "부정"),
    ("최악의 경험이었습니다. 다시는 이용하지 않겠습니다.", "부정"),
    ("서비스가 형편없었습니다.", "부정"),
    ("품질이 낮고 비쌉니다.", "부정"),
]

gen = TextAdversarialGenerator()

def classify(text):
    payload = json.dumps({
        "model": "gemma3:12b",
        "messages": [
            {"role": "system", "content": "감정을 '긍정' 또는 '부정'으로 분류. 한 단어로만 답하세요."},
            {"role": "user", "content": text},
        ],
        "temperature": 0.0, "max_tokens": 10,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except:
        return "error"

attacks = {
    "원본": lambda t: t,
    "동의어": lambda t: gen.synonym_attack(t, n_swaps=2),
    "오타": lambda t: gen.typo_attack(t, n_typos=2),
}

results = {name: {"correct": 0, "total": 0} for name in attacks}

for text, expected in BENCHMARK[:4]:  # 시간 제한으로 4개만
    for attack_name, attack_fn in attacks.items():
        adv_text = attack_fn(text)
        pred = classify(adv_text)
        is_correct = expected[:2] in pred
        results[attack_name]["total"] += 1
        if is_correct:
            results[attack_name]["correct"] += 1
        time.sleep(0.3)

print("=== 적대적 공격 효과 벤치마크 ===\n")
print(f"{'공격':10s} | {'정확':4s} | {'전체':4s} | {'정확률':8s} | {'공격 성공률':8s}")
print("-" * 50)
for name, r in results.items():
    acc = r["correct"] / max(r["total"], 1) * 100
    asr = 100 - acc  # 공격 성공률 = 1 - 정확률
    print(f"{name:10s} | {r['correct']:4d} | {r['total']:4d} | {acc:6.1f}%  | {asr:6.1f}%")
PYEOF

python3 /tmp/adv_benchmark.py
```

---

# Part 4: 적대적 입력 방어 구현 (40분)

> **이 실습을 왜 하는가?**
> 적대적 입력 방어 기법을 구현하여 모델의 강건성을 높이는 방법을 배운다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 입력 정화(Input Purification) 기법
> - 적대적 훈련의 원리
> - 앙상블 방어의 효과
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

## 4.1 입력 정화기 (Input Purifier)

```bash
# 적대적 입력 정화기
cat > /tmp/input_purifier.py << 'PYEOF'
import re
import unicodedata

class InputPurifier:
    """적대적 텍스트 입력 정화"""

    ZERO_WIDTH = re.compile('[\u200b\u200c\u200d\ufeff\u00ad]')
    HOMOGLYPHS = {'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'і': 'i'}

    def remove_zero_width(self, text):
        return self.ZERO_WIDTH.sub('', text)

    def normalize_unicode(self, text):
        text = unicodedata.normalize('NFKC', text)
        return ''.join(self.HOMOGLYPHS.get(c, c) for c in text)

    def fix_common_typos(self, text):
        COMMON_FIXES = {
            "잇었": "있었", "좃은": "좋은", "낳은": "나은",
        }
        for wrong, right in COMMON_FIXES.items():
            text = text.replace(wrong, right)
        return text

    def normalize_whitespace(self, text):
        return re.sub(r'\s+', ' ', text).strip()

    def purify(self, text):
        original = text
        text = self.remove_zero_width(text)
        text = self.normalize_unicode(text)
        text = self.fix_common_typos(text)
        text = self.normalize_whitespace(text)
        changed = text != original
        return {"purified": text, "original": original, "was_modified": changed}


purifier = InputPurifier()
tests = [
    "정상적인 텍스트입니다",
    "제로\u200b폭\u200c문자 포함",
    "hоmоglyph cоntaining text",
    "여러   공백이   있는    텍스트",
    "이 영화는 정말 재미잇었습니다",
]

print("=== 입력 정화 테스트 ===\n")
for text in tests:
    result = purifier.purify(text)
    status = "수정됨" if result["was_modified"] else "원본 유지"
    print(f"  입력: {repr(text)[:50]}")
    print(f"  출력: {result['purified']}")
    print(f"  상태: {status}\n")
PYEOF

python3 /tmp/input_purifier.py
```

## 4.2 앙상블 방어

```bash
# 다중 분류기 앙상블로 적대적 입력 방어
cat > /tmp/ensemble_defense.py << 'PYEOF'
import json
import urllib.request
import time

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"

CLASSIFIERS = [
    {"name": "직접 분류", "system": "텍스트 감정을 '긍정' 또는 '부정'으로 분류. 한 단어로만."},
    {"name": "점수 분류", "system": "텍스트 감정 점수를 1(매우 부정)~5(매우 긍정)로 평가. 숫자만."},
    {"name": "설명 분류", "system": "텍스트가 긍정적인지 부정적인지 한 문장으로 설명하세요."},
]

def query(system, text):
    payload = json.dumps({
        "model": "gemma3:12b",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": text}],
        "temperature": 0.0, "max_tokens": 50,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except:
        return "error"

def ensemble_classify(text):
    votes = {"긍정": 0, "부정": 0}
    details = []
    for clf in CLASSIFIERS:
        result = query(clf["system"], text)
        if "긍정" in result or "positive" in result.lower() or any(c in result for c in "45"):
            votes["긍정"] += 1
            details.append(f"{clf['name']}: 긍정")
        elif "부정" in result or "negative" in result.lower() or any(c in result for c in "12"):
            votes["부정"] += 1
            details.append(f"{clf['name']}: 부정")
        else:
            details.append(f"{clf['name']}: 불명확({result[:20]})")
        time.sleep(0.3)

    final = "긍정" if votes["긍정"] > votes["부정"] else "부정"
    confidence = max(votes.values()) / len(CLASSIFIERS)
    return {"verdict": final, "confidence": confidence, "votes": votes, "details": details}

test = "이 영화는 진짜 재미잇었습니다"  # 적대적 변형
print(f"테스트: {test}")
result = ensemble_classify(test)
print(f"앙상블 결과: {result['verdict']} (신뢰도: {result['confidence']:.2f})")
for d in result["details"]:
    print(f"  {d}")
PYEOF

python3 /tmp/ensemble_defense.py
```

## 4.3 OpsClaw 연동

```bash
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "adversarial-input-week08",
    "request_text": "적대적 입력 심화 - 텍스트 공격, 방어, 앙상블",
    "master_mode": "external"
  }' | python3 -m json.tool
```

---

## 체크리스트

- [ ] 적대적 예제의 수학적 정의를 설명할 수 있다
- [ ] 화이트박스 vs 블랙박스 공격의 차이를 이해한다
- [ ] 텍스트 적대적 공격 기법 4가지 이상을 열거할 수 있다
- [ ] 동의어 치환 공격을 구현하고 실행할 수 있다
- [ ] 제로폭 문자 공격을 수행할 수 있다
- [ ] 적대적 전이성의 보안 함의를 설명할 수 있다
- [ ] 입력 정화기를 구현할 수 있다
- [ ] 앙상블 방어의 원리를 이해하고 구현할 수 있다
- [ ] 공격 벤치마크를 수행하고 ASR을 측정할 수 있다
- [ ] 적대적 입력 방어 전략을 수립할 수 있다

---

## 복습 퀴즈

### 퀴즈 1: 적대적 예제에서 "섭동(perturbation)"의 조건은?
- A) 입력을 완전히 바꾸는 것
- B) 원본과 거의 동일하게 보이면서 모델을 속이는 작은 변화
- C) 입력을 삭제하는 것
- D) 모델을 재학습시키는 것

**정답: B) 원본과 거의 동일하게 보이면서 모델을 속이는 작은 변화**

### 퀴즈 2: 텍스트에서 경사도 기반 공격이 직접 적용되기 어려운 이유는?
- A) 텍스트가 너무 길어서
- B) 텍스트는 이산적(discrete) 공간이므로 연속적 경사도를 직접 사용할 수 없어서
- C) 경사도 계산이 불가능해서
- D) 텍스트 모델이 경사도를 사용하지 않아서

**정답: B) 텍스트는 이산적(discrete) 공간이므로 연속적 경사도를 직접 사용할 수 없어서**

### 퀴즈 3: 적대적 전이성(Transferability)이 보안에 미치는 영향은?
- A) 보안에 도움이 된다
- B) 블랙박스 모델도 대리 모델에서 생성한 적대적 예제로 공격 가능
- C) 전이성은 실제로 존재하지 않는다
- D) 같은 모델에서만 작동한다

**정답: B) 블랙박스 모델도 대리 모델에서 생성한 적대적 예제로 공격 가능**

### 퀴즈 4: 제로폭 문자 공격이 효과적인 이유는?
- A) 문자가 보이지 않아 사람은 탐지하기 어렵지만 토크나이저는 다른 토큰으로 분할
- B) 모든 모델이 제로폭 문자에 취약하므로
- C) 문자열 길이가 변하지 않으므로
- D) 유니코드를 지원하지 않는 모델이 많으므로

**정답: A) 문자가 보이지 않아 사람은 탐지하기 어렵지만 토크나이저는 다른 토큰으로 분할**

### 퀴즈 5: 입력 정화(Input Purification)의 핵심 아이디어는?
- A) 입력을 삭제하는 것
- B) 입력에서 적대적 섭동을 제거하여 원본에 가까운 상태로 복원
- C) 모든 입력을 차단하는 것
- D) 입력을 암호화하는 것

**정답: B) 입력에서 적대적 섭동을 제거하여 원본에 가까운 상태로 복원**

### 퀴즈 6: 앙상블 방어가 단일 분류기보다 강건한 이유는?
- A) 더 비싸서
- B) 동일 적대적 입력이 모든 분류기를 동시에 속이기 어렵기 때문
- C) 앙상블이 항상 정확하므로
- D) 단일 분류기는 항상 실패하므로

**정답: B) 동일 적대적 입력이 모든 분류기를 동시에 속이기 어렵기 때문**

### 퀴즈 7: 호모글리프(Homoglyph) 공격에서 "а"(키릴 문자)와 "a"(라틴 문자)의 차이는?
- A) 차이 없음
- B) 모양은 동일하지만 유니코드 코드포인트가 달라 토크나이저가 다르게 처리
- C) 키릴 문자가 더 크다
- D) 라틴 문자만 AI가 이해함

**정답: B) 모양은 동일하지만 유니코드 코드포인트가 달라 토크나이저가 다르게 처리**

### 퀴즈 8: FGSM과 PGD의 차이는?
- A) 전혀 다른 종류의 공격
- B) FGSM은 1회 업데이트, PGD는 반복 업데이트로 더 강한 공격
- C) PGD가 더 빠르다
- D) FGSM이 더 강하다

**정답: B) FGSM은 1회 업데이트, PGD는 반복 업데이트로 더 강한 공격**

### 퀴즈 9: 적대적 훈련(Adversarial Training)의 원리는?
- A) 적대적 예제를 학습 데이터에 포함시켜 모델의 강건성을 높임
- B) 적대적 예제를 생성하는 모델을 학습
- C) 모든 입력을 차단
- D) 모델을 더 크게 만듦

**정답: A) 적대적 예제를 학습 데이터에 포함시켜 모델의 강건성을 높임**

### 퀴즈 10: 물리적 적대적 공격(예: 패치 공격)이 디지털 공격보다 위험한 경우는?
- A) 온라인 서비스
- B) 자율주행차, 감시 카메라 등 물리적 세계와 상호작용하는 AI 시스템
- C) 텍스트 분류
- D) 음악 추천

**정답: B) 자율주행차, 감시 카메라 등 물리적 세계와 상호작용하는 AI 시스템**

## 4.3 적대적 훈련 시뮬레이션

```bash
# 적대적 훈련 시뮬레이션: 적대적 예제를 포함한 프롬프트 강화
cat > /tmp/adversarial_training.py << 'PYEOF'
import json
import urllib.request
import time

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"

# 적대적 훈련의 핵심: 공격 예제를 시스템 프롬프트에 포함
STANDARD_SYSTEM = """감정을 '긍정' 또는 '부정'으로 분류하세요. 한 단어로만."""

ADVERSARIAL_SYSTEM = """감정을 '긍정' 또는 '부정'으로 분류하세요. 한 단어로만.

주의사항:
- 오타가 있어도 전체 맥락에서 감정을 판단하세요
- 동의어로 바뀌어도 원래 감정을 유지하세요
- 제로폭 문자나 특수문자가 포함되어도 무시하세요

예시:
- "이 제품은 진짜 훌륭합니다" → 긍정 (동의어 변형)
- "이 영화는 정말 재미잇었습니다" → 긍정 (오타)
- "서비스가 형편없었습니다" → 부정 (일반)
"""

ADVERSARIAL_TEST_CASES = [
    ("이 제품은 진짜 우수합니다", "긍정"),
    ("서비스가 정말 형편없엇습니다", "부정"),
    ("품질이 뛰어나고 가격도 합리적", "긍정"),
    ("최악의 경험이엇습니다", "부정"),
]

def query(system, text):
    payload = json.dumps({
        "model": "gemma3:12b",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        "temperature": 0.0, "max_tokens": 10,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except:
        return "error"

print("=== 적대적 훈련 효과 비교 ===\n")

for system_name, system_prompt in [("표준", STANDARD_SYSTEM), ("강화", ADVERSARIAL_SYSTEM)]:
    correct = 0
    total = len(ADVERSARIAL_TEST_CASES)
    print(f"[{system_name} 프롬프트]")
    for text, expected in ADVERSARIAL_TEST_CASES:
        result = query(system_prompt, text)
        is_correct = expected[:2] in result
        if is_correct:
            correct += 1
        print(f"  {text[:30]:32s} → {result:6s} ({'O' if is_correct else 'X'})")
        time.sleep(0.3)
    print(f"  정확도: {correct}/{total} ({correct/total*100:.0f}%)\n")
PYEOF

python3 /tmp/adversarial_training.py
```

## 4.4 적대적 강건성 평가 종합 도구

```bash
# 모델 강건성 종합 평가 도구
cat > /tmp/robustness_eval.py << 'PYEOF'
import json
import sys
sys.path.insert(0, "/tmp")
from text_adversarial import TextAdversarialGenerator

class RobustnessEvaluator:
    """모델 적대적 강건성 종합 평가"""

    ATTACK_TYPES = {
        "synonym": "동의어 치환",
        "typo": "오타 삽입",
        "invisible": "제로폭 문자",
        "homoglyph": "유사 문자",
    }

    def __init__(self):
        self.gen = TextAdversarialGenerator()
        self.results = {}

    def evaluate_text(self, original, expected_label):
        """하나의 텍스트에 대해 모든 공격 유형 평가"""
        variants = self.gen.generate_all(original)
        text_results = {}
        for attack_name, variant_text in variants.items():
            if attack_name == "original":
                continue
            text_results[attack_name] = {
                "original": original[:40],
                "variant": variant_text[:40],
                "attack_type": self.ATTACK_TYPES.get(attack_name, attack_name),
            }
        return text_results

    def report(self, test_data):
        """벤치마크 데이터로 종합 보고서 생성"""
        print("=== 적대적 강건성 평가 보고서 ===\n")
        print(f"테스트 데이터: {len(test_data)}개")
        print(f"공격 유형: {len(self.ATTACK_TYPES)}가지")
        print(f"총 테스트 케이스: {len(test_data) * len(self.ATTACK_TYPES)}개\n")

        for attack_name, desc in self.ATTACK_TYPES.items():
            print(f"[{desc}]")
            for text, label in test_data[:3]:
                variants = self.gen.generate_all(text)
                variant = variants.get(attack_name, text)
                print(f"  원본: {text[:35]}")
                print(f"  변형: {variant[:35]}")
            print()

        print("권고사항:")
        print("  1. 입력 정규화(유니코드 NFC, 제로폭 제거) 적용")
        print("  2. 맞춤법 교정 레이어 추가")
        print("  3. 유사 문자(호모글리프) 정규화")
        print("  4. 정기적 강건성 벤치마크 실행")


evaluator = RobustnessEvaluator()
test_data = [
    ("이 제품은 정말 좋은 품질입니다", "긍정"),
    ("서비스가 형편없었습니다", "부정"),
    ("추천합니다", "긍정"),
    ("다시는 이용하지 않겠습니다", "부정"),
]
evaluator.report(test_data)
PYEOF

python3 /tmp/robustness_eval.py
```

## 4.5 OpsClaw 연동: 적대적 강건성 평가 프로젝트

```bash
# OpsClaw 프로젝트로 적대적 강건성 평가 관리
# 이전에 생성한 프로젝트에 추가 태스크를 디스패치할 수 있다
# curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
#   -H "Content-Type: application/json" \
#   -H "X-API-Key: opsclaw-api-key-2026" \
#   -d '{"command":"python3 /tmp/robustness_eval.py","subagent_url":"http://localhost:8002"}'
```

## 4.6 적대적 공격 방어 전략 종합

```
적대적 입력 방어 전략 정리

  Layer 1: 입력 정규화 (Input Normalization)
  ├── 유니코드 정규화 (NFC/NFKC)
  ├── 제로폭 문자 제거
  ├── 호모글리프 정규화
  ├── 공백 정규화
  └── 특수문자 필터링

  Layer 2: 입력 교정 (Input Correction)
  ├── 맞춤법 교정기 적용
  ├── 오타 자동 수정
  └── 동의어 정규화 (선택적)

  Layer 3: 모델 강화 (Model Hardening)
  ├── 적대적 훈련 (Adversarial Training)
  ├── 적대적 예시를 프롬프트에 포함
  ├── Temperature 조정
  └── 앙상블 추론

  Layer 4: 출력 검증 (Output Verification)
  ├── 자기 일관성 검증 (동일 질문 반복)
  ├── 교차 모델 검증 (다른 모델로 검증)
  └── 이상치 탐지 (비정상 출력 패턴)

  Layer 5: 모니터링 (Monitoring)
  ├── 입력 이상 패턴 로깅
  ├── 분류 신뢰도 모니터링
  └── 공격 시도 탐지/알림
```

---

## 과제

### 과제 1: 텍스트 적대적 생성기 확장 (필수)
- text_adversarial.py에 패러프레이징 공격 추가 (LLM을 이용한 문장 재구성)
- 벤치마크 8개 문장에 대해 모든 공격 기법의 ASR 측정
- 가장 효과적인 공격 기법 Top 3 분석

### 과제 2: 입력 정화기 강화 (필수)
- input_purifier.py에 맞춤법 검사 기반 교정 로직 추가
- 적대적 샘플 10개 + 정상 샘플 10개로 정화기의 효과 측정
- 정화 전후의 분류 정확도 비교

### 과제 3: 강건성 평가 프레임워크 설계 (심화)
- 모델 강건성을 종합적으로 평가하는 프레임워크 설계
- 포함: 다양한 공격 유형, 자동 벤치마킹, 점수 산출, 보고서 생성
- 실습 환경에서 실행하여 결과 보고서 제출
