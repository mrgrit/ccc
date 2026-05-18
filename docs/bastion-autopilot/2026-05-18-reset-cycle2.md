# Bastion Autopilot — Reset Cycle 2 (2026-05-18, F8 적용)

**시각**: 2026-05-18 16:00-16:55 (UTC) 약 55분 연속
**대상**: F8 fix (LLM hallucination 더 엄격 _synth_prompt) 적용 후 mission 재시도
**누적**: cycle 1 의 23 mission + cycle 2 의 4 mission = 27

## F8 fix 의 내용

`agent.py:2382` 의 `_synth_prompt` (skill_ok branch) 에 4 룰 추가:

```
6. **PID 숫자 vs '개수' 구분**: stdout 가 `49 suricata ...` 면 49 는 PID.
   '49개', '49 개 실행' 표현 금지. 정확히 'PID 49' 또는 '1 process' 보고.
7. **HTTP code vs 차단 일치**: stdout 의 HTTP code 가 200/302 이면 '통과/응답 OK'.
   403/406/501 이어야 '차단' 보고. 200 + '차단' 같은 모순 표현 절대 금지.
8. **stdout 가 banner/help text 만**: 실제 명령 결과 없으면 '결과 없음' 정직 보고.
   '스캔 완료', '실행 결과 확인' 가짜 결론 금지.
9. **결론은 json tool-call format 금지**: `{"tool":...}` 같은 json 으로
   결론 대체 금지. 한국어 평문 으로 결론 마무리.
```

## Mission 결과 (cycle 2)

| # | Mission | F8 룰 | 결과 | 분석 |
|---|---------|-------|-----|------|
| M24 | F8 검증 — suricata PID (M13 재시도) | 룰 6 | △ | LLM 룰 6 메타-인용 ("PID vs 개수 구분: 충족") 하지만 결론 에서 여전히 "49개 프로세스 실행 중" 표현. 룰 인식 ≠ 적용. |
| M25 | F8 검증 — WAF HTTP code (M15 재시도) | 룰 7,9 | ❌ | LLM 응답 = json tool-call format 만 + 결론 없음. 룰 9 실패. |
| M26 | web Apache version | 룰 8 | ❌ | stdout = ssh known_hosts warning 만 (apache2 -v 의 stderr 못 잡음). LLM "Apache 버전 확인 충족" 가짜 결론. 룰 8 실패. |
| M27 | fw ip -br addr show | (해당 X) | ❌ | KG context "used:true, hits:2" → 이전 docker anchor 가 응답 유도. "메모리 사용량 0%, 네트워크 구성 확인 필요" 같은 일반론 (M19 와 동일 패턴). |

## 🔴 결정적 발견 — F8 fix 효과 미미

### gemma3:4b 의 instruction-following 한계
- F8 의 4 룰 (6-9) 을 LLM 가 **메타-인용은 가능** (M24 의 "룰 6 충족")
- 하지만 **결론 에서는 룰 위배** (M24 의 "49개 실행 중" 그대로)
- 4B 모델 의 multi-rule instruction following 한계

### KG context 의 relevance 문제 (M27, cycle 1 M19 와 동일)
- KG hit 의 anchor 가 sim score 만 기반 → 무관한 컨텍스트 도 inject
- "docker inspect" anchor 가 "ip addr show" mission 에 inject → 응답 왜곡

## 다음 fix candidate

### F9: Manager-SubAgent 2-tier review
- SubAgent (gemma3:4b) 1차 응답 → Manager (gpt-oss:120b) 가 review/correct
- 룰 위배 검출 시 재호출. paper §4 의 multi-agent 아키텍처 활용
- Cost: latency 2x, 정확도 향상 기대

### F10: KG context relevance filtering
- sim 0.7 cutoff 외에 **course / step_order / domain 매칭** 추가 필터
- M27 의 "ip addr show" mission 에 "docker inspect" anchor inject 차단

### F11: post-process hallucination detection
- LLM 응답 stream 종료 후 regex/keyword 검출:
  - "N개" + PID 가 stdout 에 있으면 → 재호출 (한국어 평문, "PID N" 으로)
  - "200" + "차단" 동시 출현 → 재호출
  - json tool-call format 만 + 결론 없음 → 재호출

## 시간 한계

이번 cycle 의 핵심 발견 = **prompt 엔지니어링 만으로는 한계**.
진짜 개선은 multi-agent (F9) 또는 hard-coded post-process (F11) 필요.
이건 다음 cycle 또는 별도 세션 의 큰 작업.

## 누적 통계 (reset cycle 1+2 = 27 mission)

| 단계 | PASS | △ | ❌ |
|------|-----|---|---|
| cycle 1 M1-M2 (F7 전) | 0 | 0 | 2 |
| cycle 1 M3-M23 (F7 후) | 15 | 5 | 1 |
| cycle 2 M24-M27 (F8 후) | 0 | 1 | 3 |
| **누적** | **15/27** | **6** | **6** |

→ F7 fix 는 robust (skill execution 보장), F8 fix 는 효과 미미 (LLM 한계).

## 다음 cycle (3)

- F11 (post-process) 시도 — hallucination 검출 시 재호출 hard-code
- 또는 multi-agent (F9) 의 더 정밀 검토
- W04~W15 mission 더 진행
