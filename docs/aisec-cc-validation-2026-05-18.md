# aisec (인공지능보안) CC 검증 보고서 (2026-05-18)

## 1. 검증 환경
- mrgrit/6v6 의 fresh deploy 위 진행
- bastion API = port 9100 (HAProxy 통해 9100 → bastion 컨테이너 의 uvicorn)

## 2. 핵심 결함 발견

### #1. bastion base API 의 LLM 미연결
`/health` = `{"status":"ok", "llm_configured":false}` — fresh deploy 의 .env 의
`LLM_BASE_URL=` (빈 값) → Ollama 미연결.

### #2. bastion base API 에 /chat /kg/* endpoint 부재
`POST /chat` = `{"detail":"Not Found"}` — base bastion 컨테이너 의 api.py 는 /health
만 노출. aisec 의 80% step (LLM 호출 + KG 활용) 이 작동 불가.

### #3. 옵션 C (override.yaml) 의 의존성
mrgrit/6v6 의 docker-compose.override.yaml 가 활성화 되어야 /chat /kg/* 노출 (mrgrit/bastion
clone 을 /home/ccc/bastion 으로 bind mount + port 9200 publish). 학생 신규 배포는
base 만 → aisec 코스 자체 작동 불가.

## 3. 검증 결과 (89 step 중)

| Week | 결과 |
|------|------|
| W01-S1 (16 컨테이너 + ai.6v6.lab) | ✅ |
| W01-S2 ~ W15 (모든 bastion /chat 호출 step) | ❌ (Not Found — base api.py 의 endpoint 부재) |

## 4. 해결 방향 (보류 작업)

### 옵션 A (권장, 큰 작업)
mrgrit/bastion 의 full api.py 를 mrgrit/6v6 의 bastion Dockerfile 에 통합:
- bastion/Dockerfile 에 `COPY bastion-api/ /opt/bastion-api/`
- entrypoint 에 mrgrit/bastion 의 api.py 가동
- Ollama 컨테이너 추가 (gpu/cpu 모드 선택)
- KG sqlite DB 자동 init

### 옵션 B (간단)
aisec instruction 에 "본 코스는 옵션 C 환경 (mrgrit/bastion + Ollama 별도 설치) 필요"
명시 + 학생 PC 의 Ollama 설치 가이드 추가.

### 옵션 C (zero-cost)
aisec 코스 자체 재설계 — bastion API 의존 줄이고 학생이 직접 Ollama CLI 사용.

## 5. 종합

- **secuops 132/132 ✅** (mrgrit/6v6 base 만으로 100%)
- **attack 45/45 ✅** (실측 결함 0)
- **aisec 1/89** (S1 만 통과 — 나머지 = bastion + Ollama 통합 필요)

aisec 는 base 인프라 외 추가 의존성 큼. 다음 세션 작업 권장.
