# Findings for tubewar — bastion test 사이드 산출물

> 본 파일은 bastion test cycle 에서 발견되는 *LLM 평가 메커니즘 한계* 와 그
> 정정 패턴 을 정리한다. **작업 주체만 다르고 (LLM 에이전트 vs 학생) 평가 구조는
> 동일** 이므로 본 발견이 tubewar (github.com/mrgrit/tubewar) 의 학생 결과 평가
> 정확도 개선에 직접 적용 가능.

## 평가 메커니즘 대조 (두 시스템 같음)

| 측면 | bastion test (본 보고서) | tubewar (학생 평가) |
|------|--------------------------|---------------------|
| Mission | bastion 의 lab YAML step | 학생의 mission |
| 작업 주체 | LLM 에이전트 (gpt-oss:120b) | 학생 (사람) |
| 결과 | bastion 의 ReAct trace + stdout | 학생의 답안 input |
| 평가 | semantic-judge (LLM) + success_criteria | semantic-judge (LLM) + 평가 기준 |
| 출력 | assistance_level (none/env/lab/retry) | PASS/PARTIAL/FAIL + 피드백 |

→ **평가 측면은 같은 LLM judge + criteria 기반**. bastion test 의 *judge 한계* 가
   곧 tubewar 의 *학생 평가 한계*.

---

## Finding #1 (cycle 3~4) — exit_code 해석

### bastion test 에서 발견

`which nmap sqlmap hydra ... msfconsole ... gobuster` 실행 시:
- exit_code 1 (msfconsole 못 찾음)
- 그러나 stdout 에 *12 도구 PATH 출력*

bastion 의 LLM 이 *exit_code 1 → 전체 fail* 로 해석. 12 도구 가용 인식 못함.
fallback 로 `find / -name msfconsole` + `chmod 750` 무의미 반복.

### tubewar 적용

학생이 *부분 결과* 만 제출 시 LLM 평가도 동일 함정 위험:
- 학생 답: "nmap, sqlmap, hydra 설치됨, msfconsole 없음"
- 평가 LLM: "msfconsole 누락 → FAIL"
- 정답: "12/13 PARTIAL, msfconsole 누락 명시 + 원인 추정 = MITRE Tactic 매핑 시도"

### 권장 — tubewar 평가 prompt 정정

```
평가 시 다음을 우선:
1. 학생 답안의 *부분 결과* 도 PARTIAL PASS 로 인정. FAIL 은 *완전 실패* 시만.
2. 누락 항목은 학생이 *원인 추정* + *대안 방법* 시도했는지 확인.
3. exit_code / 단순 키워드 매칭 보다 *의미적 충족* 우선.
4. "12/13 매트릭스 출력 + 핵심 5 충족" → PARTIAL PASS + 누락 1 보강 권장.
```

---

## Finding #2 (cycle 2~3) — output truncation 영향

### bastion test 에서 발견

subagent.py 의 `r.stdout[:10000]` 가 nikto -Version (수십 라인 plugin) 출력으로
*나머지 9 도구의 which 결과 잘림*. 다음 step 의 input 부족.

### tubewar 적용

학생 답안의 *long output paste* 가 평가 LLM 의 context 제한에 잘리면 *후반 정답* 안 평가됨:
- 학생: 10000 자 답안 (전반 정답 + 후반 누락)
- LLM: 전반 분석 → "FAIL" (후반 답 안 봄)

### 권장 — tubewar 답안 처리

```
1. 학생 답안 길이 측정 → 평가 prompt 의 context limit 초과 시 *분할 평가*:
   - 답안을 *의미 단위* 분할 (문단 / 명령 / 결과)
   - 각 분할에 평가 → 종합
2. *중요 영역 우선* — 결론 / 실행 결과 / 코드 블록 우선 평가
3. 잘림 발생 시 *학생에게 통지* + 분할 재제출 요청
```

---

## Finding #3 (cycle 4) — agent retry 의 LLM prompt 무력화

### bastion test 에서 발견

bastion 의 system prompt 에 "같은 명령 5 회 반복 시 중단" 추가 (bastion@26799b8).
그러나 cycle 4 에서 `nmap -V` 4 회 반복 — *임계치 직전*. agent.py 의 `step_retry`
가 *프로그램적 retry* (LLM 호출 없이) — system prompt 영향 X.

### tubewar 적용

학생이 같은 답을 반복 제출 시 LLM 평가가 같은 피드백 반복 → 학생 답답함:
- 학생 1차: "nmap 설치됨"
- LLM: "더 자세히 답해주세요"
- 학생 2차: "nmap 설치됨" (똑같음)
- LLM: "더 자세히 답해주세요" (똑같음) — 무한 루프 위험

### 권장 — tubewar 평가 loop

```
1. 학생 같은 답 N 회 (예: 3 회) 감지 → *피드백 변경*:
   - "이전과 같은 답입니다. 다음 중 하나를 시도해보세요: [구체적 옵션 3 종]"
2. *진행 안 됨* 자동 감지 → 강사 알림 또는 hint 자동 제공
3. 평가 LLM 의 *temperature* 조정 — 같은 피드백 반복 회피
```

---

## Finding #4 (cycle 2~3) — multi-intent task 분해

### bastion test 에서 발견

bastion 의 lab step "13 도구 매트릭스 + nmap/nikto 버전 + ATT&CK 매핑" 같은
*3 의도 1 task* 가 LLM 의 1 step 합성 어려움. 1 의도씩 분해 시 PASS.

### tubewar 적용

학생 mission 이 *복합 의도* 일 때:
- 단순 채점 — "전체 충족 시 PASS" → 학생이 *어느 부분* 충족했는지 모름
- 정답 — 의도 별 *분리 평가* + 종합

### 권장 — tubewar mission 분해

```
1. mission 작성 시 *의도 단위 분리* 명시:
   - intent_1, intent_2, intent_3 ...
   - 각 intent 별 success_criteria
2. 평가 결과 — 의도 별 PASS/FAIL 매트릭스 + 종합 점수
3. 학생 피드백 — "intent_1 PASS, intent_2 PARTIAL (X 누락), intent_3 미시도"
```

---

## Finding #5 (cycle 1) — env_corrected 의 운영적 의미

### bastion test 에서 발견

cycle 1 의 fail 원인 = *Asset 미등록* + *shell denied* — 둘 다 *환경 결함*,
bastion 능력 외. 환경 정정 (Asset 자동 등록 hook + auto_approve) 후 cycle 2~4
점진 개선.

### tubewar 적용

학생 fail 의 원인이 *학생 능력 부족* 인지 *환경 결함* 인지 구분:
- 환경 결함 (예: lab 인프라 down, 도구 미설치) → 학생에게 책임 묻기 X
- 학생 능력 부족 (예: 잘못된 명령, 도구 선택 오류) → 학습 피드백

### 권장 — tubewar 평가 차원

```
1. 평가 결과에 *원인 분류* 추가:
   - student_skill — 학생 능력
   - lab_env — 인프라 결함 (lab 측 정정 필요)
   - mission_ambiguity — mission 자체 모호
2. lab_env / mission_ambiguity 는 *학생 점수 영향 X*, lab 측 즉시 정정 알림
3. student_skill 만 점수 반영 + 학습 피드백
```

---

## 적용 시점

| 시점 | 작업 |
|------|------|
| bastion test cycle 진행 중 | 본 파일 누적 (각 cycle 마다 새 finding 발견 시 추가) |
| step 1 종결 후 | tubewar repo 에 issue 생성 (또는 PR) |
| 본 paper P22 평가 종결 | tubewar 의 평가 prompt 정정 + 비교 측정 |

## 참조 commit

- bastion@88ea6e4 (Asset 자동 등록) — finding #5 원인 정정
- 6v6@4b54196 (output 30000) — finding #2 부분 완화
- bastion@26799b8 (reasoning 섹션) — finding #1, #3, #4 prompt 정정
