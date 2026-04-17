# AI Safety 실습용 취약 모델 파인튜닝

## 목적

AI Safety/Security 실습에서 학생이 프롬프트 인젝션, 탈옥, 가드레일 우회 등을 
**실제로 성공해볼 수 있는** 의도적으로 취약한 모델을 생성한다.

## 접근 방법

### Phase 1: Modelfile 기반 커스텀 모델 (시스템 프롬프트 조작)
- 기존 모델(gemma3:4b)에 약한 안전 가드레일 시스템 프롬프트 적용
- Ollama `create` 명령으로 즉시 배포 가능
- 장점: 빠르고 간단, 단점: 깊은 행동 변경 불가

### Phase 2: LoRA 파인튜닝 (가중치 조정)
- 취약한 응답 패턴 학습 데이터셋 생성
- unsloth/transformers로 LoRA fine-tuning
- GGUF 변환 → Ollama 등록
- 장점: 깊은 행동 변경, 단점: GPU 시간 필요

## 파일 구조

```
finetune/
├── README.md                    # 이 문서
├── modelfile_vulnerable.txt     # Phase 1: Ollama Modelfile
├── dataset/
│   ├── jailbreak_training.jsonl # 탈옥 시도에 대한 약한 거부 응답
│   ├── guardrail_training.jsonl # 가드레일 구조화 출력
│   ├── bias_training.jsonl      # 편향 탐지용 응답
│   └── safety_labels.jsonl      # REFUSED/BLOCKED/SAFE 라벨링
├── scripts/
│   └── generate_dataset.py      # 데이터셋 생성기
└── docs/
    └── finetune_report.md       # 파인튜닝 과정 문서
```

## 대상 모델

| 모델 | 크기 | 역할 |
|------|------|------|
| gemma3:4b | 3.3GB | 기본 취약 모델 (Phase 1) |
| llama3.2:3b | 2.0GB | 대안 후보 |
| qwen3:8b | 5.2GB | SubAgent 모델 (참고) |
