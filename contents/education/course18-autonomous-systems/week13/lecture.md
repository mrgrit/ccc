# Week 13: AI 모델 공격/방어 — 적대적 입력, 로버스트니스, 검증

## 학습 목표
- 적대적 공격(Adversarial Attack)의 이론적 기반을 심층 이해한다
- FGSM, PGD, C&W 등 주요 공격 기법을 비교 분석할 수 있다
- AI 모델 로버스트니스(Robustness) 평가 기법을 실습할 수 있다
- 적대적 훈련, 입력 전처리 등 방어 기법을 구현할 수 있다
- CPS 맥락에서 AI 보안의 중요성을 평가할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM | `ssh ccc@10.20.30.100` |
| manager | 10.20.30.200 | AI/관리 (Ollama LLM) | `ssh ccc@10.20.30.200` |

**LLM API:** `${LLM_URL:-http://localhost:8003}`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 이론: 적대적 공격 이론 (Part 1) | 강의 |
| 0:30-1:00 | 이론: 방어 기법과 로버스트니스 (Part 2) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | 실습: 적대적 공격 구현 (Part 3) | 실습 |
| 1:50-2:30 | 실습: 방어 기법 구현 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 실습: LLM 기반 AI 모델 보안 평가 (Part 5) | 실습 |
| 3:10-3:30 | 과제 안내 + 정리 | 정리 |

---

## Part 1: 적대적 공격 이론 (0:00-0:30)

### 1.1 적대적 공격 분류 체계

```
적대적 공격 분류
│
├── 공격자 지식 기준
│   ├── White-box: 모델 구조/파라미터 완전히 알고 있음
│   ├── Black-box: 입출력만 관찰 가능
│   └── Gray-box: 부분적 지식 (아키텍처만, 훈련 데이터만)
│
├── 공격 목적 기준
│   ├── Untargeted: 아무 다른 클래스로 오분류
│   └── Targeted: 특정 클래스로 오분류
│
├── 섭동 범위 기준
│   ├── Lp norm (L0, L2, L-inf): 수학적 거리 제한
│   ├── Patch: 특정 영역만 변경
│   └── Universal: 모든 입력에 적용 가능
│
└── 환경 기준
    ├── Digital: 이미지 픽셀 직접 수정
    └── Physical: 현실 세계에서 물리적 변형
```

### 1.2 주요 공격 알고리즘

```
FGSM (Fast Gradient Sign Method):
  x_adv = x + ε × sign(∇_x L(θ, x, y))
  - 한 번의 그래디언트 계산
  - 빠르지만 덜 정밀

PGD (Projected Gradient Descent):
  x_0 = x + random noise
  x_{t+1} = Π_{x+S} (x_t + α × sign(∇_x L(θ, x_t, y)))
  - 반복적 최적화
  - FGSM보다 강력

C&W (Carlini & Wagner):
  minimize ‖δ‖_p + c × f(x+δ)
  - 최적화 기반
  - 최소 섭동으로 공격 성공
  - 많은 방어를 돌파

DeepFool:
  최소 섭동을 찾아 결정 경계를 넘김
  - 기하학적 접근
  - L2 norm 최소화
```

### 1.3 CPS에서의 AI 공격 영향

| CPS 시스템 | AI 모델 | 공격 시나리오 | 물리적 영향 |
|------------|---------|-------------|-------------|
| 자율주행 | 객체 탐지(YOLO) | 정지표지판 오인식 | 교차로 사고 |
| 드론 | 장애물 회피 | 가짜 장애물 인식 | 충돌/추락 |
| 산업 로봇 | 품질 검사 | 불량품 정상 판정 | 제품 결함 |
| 의료 로봇 | 영상 분석 | 오진 유발 | 환자 위해 |
| 보안 카메라 | 얼굴 인식 | 인식 회피 | 보안 실패 |

---

## Part 2: 방어 기법과 로버스트니스 (0:30-1:00)

### 2.1 방어 기법 분류

```
방어 기법
│
├── 입력 전처리 (Input Transformation)
│   ├── JPEG 압축
│   ├── 가우시안 노이즈 추가
│   ├── 이미지 리사이징
│   └── 특징 스퀴징 (Feature Squeezing)
│
├── 모델 강화 (Model Hardening)
│   ├── 적대적 훈련 (Adversarial Training)
│   ├── 디스틸레이션 (Defensive Distillation)
│   ├── 랜덤화 (Randomized Smoothing)
│   └── 앙상블 방법
│
├── 탐지 기반 (Detection)
│   ├── 통계적 이상 탐지
│   ├── 특징 공간 분석
│   └── 입력 변환 일관성 검사
│
└── 인증 방어 (Certified Defense)
    ├── 랜덤 스무딩 (Randomized Smoothing)
    └── 구간 경계 검증 (Interval Bound Propagation)
```

### 2.2 적대적 훈련

```
일반 훈련:
  min_θ E[(L(f_θ(x), y)]

적대적 훈련:
  min_θ E[max_{δ∈S} L(f_θ(x+δ), y)]

  = 모델이 적대적 입력에서도 올바르게 분류하도록 훈련
  = 내부 최대화: 가장 강한 적대적 예시 생성
  = 외부 최소화: 적대적 예시에서도 정확한 모델 학습
```

---

## Part 3: 적대적 공격 구현 (1:10-1:50)

### 3.1 수치 기반 적대적 공격 시뮬레이션

```bash
python3 << 'PYEOF'
import math
import random

class SimpleClassifier:
    """간소화된 이진 분류기 (결정 경계 시뮬레이션)"""

    def __init__(self):
        self.weights = [0.8, -0.3, 0.5, 0.2, -0.4]
        self.bias = -0.5

    def predict(self, x):
        logit = sum(w * xi for w, xi in zip(self.weights, x)) + self.bias
        prob = 1 / (1 + math.exp(-logit))
        return ("STOP_SIGN" if prob > 0.5 else "NOT_STOP_SIGN"), prob

    def gradient(self, x):
        """손실 함수의 그래디언트 (FGSM용)"""
        logit = sum(w * xi for w, xi in zip(self.weights, x)) + self.bias
        prob = 1 / (1 + math.exp(-logit))
        # Cross-entropy gradient w.r.t. input
        return [(prob - 1) * w for w in self.weights]

class AdversarialAttacks:
    def __init__(self, model):
        self.model = model

    def fgsm(self, x, epsilon):
        """FGSM 공격"""
        grad = self.model.gradient(x)
        sign_grad = [1 if g > 0 else -1 for g in grad]
        x_adv = [xi + epsilon * si for xi, si in zip(x, sign_grad)]
        return x_adv

    def pgd(self, x, epsilon, alpha=0.01, steps=10):
        """PGD 공격"""
        x_adv = [xi + random.uniform(-epsilon, epsilon) for xi in x]

        for _ in range(steps):
            grad = self.model.gradient(x_adv)
            sign_grad = [1 if g > 0 else -1 for g in grad]
            x_adv = [xi + alpha * si for xi, si in zip(x_adv, sign_grad)]
            # 프로젝션: epsilon-ball 내로 제한
            x_adv = [max(xi - epsilon, min(xi + epsilon, xai))
                     for xi, xai in zip(x, x_adv)]

        return x_adv

    def deepfool_simple(self, x, max_iter=20):
        """간소화된 DeepFool"""
        x_adv = list(x)
        for _ in range(max_iter):
            pred, prob = self.model.predict(x_adv)
            if pred != "STOP_SIGN":
                break
            grad = self.model.gradient(x_adv)
            grad_norm = math.sqrt(sum(g**2 for g in grad))
            if grad_norm == 0:
                break
            perturbation = [(prob - 0.5) * g / (grad_norm**2) for g in grad]
            x_adv = [xi - pi for xi, pi in zip(x_adv, perturbation)]
        return x_adv

model = SimpleClassifier()
attacker = AdversarialAttacks(model)

# 정상 정지 표지판 특징
x_orig = [0.9, 0.2, 0.7, 0.5, 0.3]

print("=== Adversarial Attack Comparison ===")
print()

# 원본
pred, prob = model.predict(x_orig)
print(f"[Original]  Prediction: {pred}  Confidence: {prob:.4f}")
print(f"  Features: {[f'{xi:.3f}' for xi in x_orig]}")
print()

# FGSM
for eps in [0.1, 0.2, 0.3, 0.5]:
    x_adv = attacker.fgsm(x_orig, eps)
    pred, prob = attacker.model.predict(x_adv)
    l2 = math.sqrt(sum((a-b)**2 for a, b in zip(x_orig, x_adv)))
    status = "EVADED" if pred != "STOP_SIGN" else "DETECTED"
    print(f"[FGSM eps={eps}]  {pred}  Conf:{prob:.4f}  L2:{l2:.3f}  [{status}]")

print()

# PGD
for eps in [0.1, 0.2, 0.3]:
    x_adv = attacker.pgd(x_orig, eps, alpha=0.02, steps=20)
    pred, prob = attacker.model.predict(x_adv)
    l2 = math.sqrt(sum((a-b)**2 for a, b in zip(x_orig, x_adv)))
    status = "EVADED" if pred != "STOP_SIGN" else "DETECTED"
    print(f"[PGD eps={eps}]   {pred}  Conf:{prob:.4f}  L2:{l2:.3f}  [{status}]")

print()

# DeepFool
x_adv = attacker.deepfool_simple(x_orig)
pred, prob = model.predict(x_adv)
l2 = math.sqrt(sum((a-b)**2 for a, b in zip(x_orig, x_adv)))
print(f"[DeepFool]  {pred}  Conf:{prob:.4f}  L2:{l2:.3f}")
print(f"  Minimal perturbation found!")

print()
print("[Comparison]")
print("  FGSM:     Fast, single step, larger perturbation")
print("  PGD:      Iterative, stronger, bounded perturbation")
print("  DeepFool: Minimal perturbation, crosses decision boundary")
PYEOF
```

---

## Part 4: 방어 기법 구현 (1:50-2:30)

### 4.1 입력 전처리 방어

```bash
python3 << 'PYEOF'
import math
import random

class DefenseModule:
    """적대적 공격 방어 모듈"""

    @staticmethod
    def gaussian_noise(x, sigma=0.05):
        """가우시안 노이즈 추가 (랜덤화 방어)"""
        return [xi + random.gauss(0, sigma) for xi in x]

    @staticmethod
    def feature_squeezing(x, precision=1):
        """특징 스퀴징: 정밀도 감소"""
        scale = 10 ** precision
        return [round(xi * scale) / scale for xi in x]

    @staticmethod
    def input_clipping(x, lower=0.0, upper=1.0):
        """입력 클리핑"""
        return [max(lower, min(upper, xi)) for xi in x]

    @staticmethod
    def ensemble_predict(models, x, threshold=0.5):
        """앙상블 예측"""
        votes = []
        for model in models:
            pred, prob = model.predict(x)
            votes.append(1 if prob > threshold else 0)
        avg = sum(votes) / len(votes)
        return ("STOP_SIGN" if avg > 0.5 else "NOT_STOP_SIGN"), avg

    @staticmethod
    def detect_adversarial(x_orig, x_transformed, threshold=0.15):
        """적대적 입력 탐지: 변환 전후 차이 분석"""
        diff = math.sqrt(sum((a-b)**2 for a, b in zip(x_orig, x_transformed)))
        return diff > threshold, diff

class SimpleClassifier:
    def __init__(self, weights=None, bias=-0.5):
        self.weights = weights or [0.8, -0.3, 0.5, 0.2, -0.4]
        self.bias = bias

    def predict(self, x):
        logit = sum(w * xi for w, xi in zip(self.weights, x)) + self.bias
        prob = 1 / (1 + math.exp(-logit))
        return ("STOP_SIGN" if prob > 0.5 else "NOT_STOP_SIGN"), prob

model = SimpleClassifier()
defense = DefenseModule()

# 적대적 샘플 (FGSM eps=0.3으로 생성된)
x_orig = [0.9, 0.2, 0.7, 0.5, 0.3]
x_adv = [1.2, -0.1, 1.0, 0.7, 0.0]  # 적대적 입력

print("=== Defense Techniques Evaluation ===")
print()

pred_orig, prob_orig = model.predict(x_orig)
pred_adv, prob_adv = model.predict(x_adv)
print(f"Original:     {pred_orig} ({prob_orig:.4f})")
print(f"Adversarial:  {pred_adv} ({prob_adv:.4f})")
print()

# 방어 1: 가우시안 노이즈
print("[Defense 1] Gaussian Noise (sigma=0.1)")
successes = 0
for _ in range(10):
    x_def = defense.gaussian_noise(x_adv, 0.1)
    pred, prob = model.predict(x_def)
    if pred == "STOP_SIGN":
        successes += 1
print(f"  Recovery rate: {successes}/10 ({successes*10}%)")
print()

# 방어 2: 특징 스퀴징
print("[Defense 2] Feature Squeezing")
x_def = defense.feature_squeezing(x_adv, precision=1)
pred, prob = model.predict(x_def)
print(f"  Before: {[f'{xi:.3f}' for xi in x_adv]}")
print(f"  After:  {[f'{xi:.3f}' for xi in x_def]}")
print(f"  Result: {pred} ({prob:.4f})")
print()

# 방어 3: 앙상블
print("[Defense 3] Ensemble (3 models)")
models = [
    SimpleClassifier([0.8, -0.3, 0.5, 0.2, -0.4]),
    SimpleClassifier([0.7, -0.2, 0.6, 0.1, -0.3]),
    SimpleClassifier([0.9, -0.4, 0.4, 0.3, -0.5]),
]
pred, conf = defense.ensemble_predict(models, x_adv)
print(f"  Ensemble result: {pred} (agreement: {conf:.2f})")
print()

# 방어 4: 탐지
print("[Defense 4] Adversarial Detection")
x_squeezed = defense.feature_squeezing(x_adv, 1)
detected, diff = defense.detect_adversarial(x_adv, x_squeezed)
print(f"  L2 difference after squeezing: {diff:.4f}")
print(f"  Adversarial detected: {detected}")
print()

print("=== Defense Summary ===")
print("  Gaussian Noise:     Effective for small perturbations")
print("  Feature Squeezing:  Simple but may reduce accuracy")
print("  Ensemble:           Robust but computationally expensive")
print("  Detection:          Can flag suspicious inputs")
PYEOF
```

---

## Part 5: LLM 기반 AI 모델 보안 평가 (2:40-3:10)

### 5.1 LLM으로 AI 보안 위험 평가

```bash
curl -s ${LLM_URL:-http://localhost:8003}/api/chat \
  -d '{
    "model":"gemma3:4b",
    "messages":[
      {"role":"system","content":"You are an AI security researcher specializing in adversarial ML for cyber-physical systems."},
      {"role":"user","content":"Compare FGSM, PGD, and C&W attacks in terms of: 1) computational cost, 2) attack success rate, 3) perturbation visibility, 4) defense bypass capability. Provide a concise comparison table."}
    ],
    "stream":false,
    "options":{"num_predict":300}
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['message']['content'])"
```

### 5.2 CPS AI 보안 체크리스트

```bash
python3 << 'PYEOF'
checklist = [
    ("모델 로버스트니스 테스트", "FGSM/PGD로 적대적 강건성 평가", "필수"),
    ("입력 검증", "센서 입력 범위/일관성 검사", "필수"),
    ("앙상블/다중 모델", "단일 모델 의존 방지", "권장"),
    ("적대적 훈련", "적대적 예시 포함 학습", "권장"),
    ("실시간 모니터링", "추론 결과 이상 탐지", "필수"),
    ("센서 퓨전 검증", "다중 센서 교차 검증", "필수"),
    ("모델 업데이트 보안", "모델 무결성 서명 검증", "필수"),
    ("설명 가능성", "모델 결정 근거 추적", "권장"),
    ("물리적 공격 테스트", "패치/스티커 등 물리 공격 시험", "권장"),
    ("페일세이프", "AI 실패 시 안전 모드 전환", "필수"),
]

print("=== CPS AI Security Checklist ===")
print()
print(f"{'#':>2} {'Item':<30} {'Requirement':<8} {'Description'}")
print("-" * 80)
for i, (item, desc, req) in enumerate(checklist, 1):
    marker = "[!!]" if req == "필수" else "[ ]"
    print(f"{i:>2} {marker} {item:<28} {req:<8} {desc}")

print()
essential = sum(1 for _, _, r in checklist if r == "필수")
print(f"Essential items: {essential}/{len(checklist)}")
print(f"Total items: {len(checklist)}")
PYEOF
```

---

## Part 6: 과제 안내 (3:10-3:30)

### 과제

**과제:** 자율주행 객체 탐지 모델에 대한 적대적 로버스트니스 평가 보고서를 작성하시오.
- 3가지 이상의 공격 기법 적용 및 성공률 비교
- 2가지 이상의 방어 기법 적용 후 재평가
- CPS 안전성 관점에서의 위험도 분석

---

## 참고 자료

- "Explaining and Harnessing Adversarial Examples" - Goodfellow et al.
- "Towards Deep Learning Models Resistant to Adversarial Attacks" - Madry et al.
- "Towards Evaluating the Robustness of Neural Networks" - Carlini & Wagner
- CleverHans Library: https://github.com/cleverhans-lab/cleverhans
