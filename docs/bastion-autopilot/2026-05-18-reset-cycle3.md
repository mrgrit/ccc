# Bastion Autopilot — Reset Cycle 3 (2026-05-18, F12 시도)

**시각**: 2026-05-18 16:55-17:25 (UTC) 약 30분 (mission 시간 효율)
**대상**: F12 fix (punt 마커 확장 + general-punt 검출)
**누적**: cycle 1+2+3 = 39 mission

## F12 fix 의 시도

### F12 v1: punt 마커 확장
`_punt_markers` 에 KG context echo 의 일반론 마커 추가:
```
"확인 필요", "검토 권장", "추가 모니터링", "정상 작동 여부 확인",
"방화벽 규칙 검토", "네트워크 설정 확인", "비정상적인 활동",
"필요하다면", "권장합니다",
```

### F12 v2: `_is_general_punt` 검출 → prompt_fallback 강제
`if not all_tool_outputs or _is_general_punt:` 조건 추가.
last_assistant_content 가 일반론 응답 면 도구 실행 강제.

## Mission 결과 (cycle 3)

| # | Mission | KG hit | 결과 | 분석 |
|---|---------|--------|-----|------|
| M33 | F12 검증 — fw uptime (M32 재시도) | 0 | ✅ | prompt_fallback 정상 트리거 → "9 days, 20 min" 정확 인용 |
| M34 | F12 + KG hit — fw ip addr (M28 재시도) | 3 | ❌ | F12 v1 마커 매칭 안 됨. LLM 직접 응답 |
| M35 | F12 v2 검증 — fw ip addr 재시도 | 3 | ❌ | F12 v2 마커 매칭 안 됨 ("이상 징후 없음" 응답) |
| M36 | web ModSec SecRuleEngine | 3 | ✅ | "SecRuleEngine On" 정확 인용 (json 안에) |
| M37 | siem Wazuh rules count | 3 | ✅ | "84" 정확 |
| M38 | ips Suricata rules count | 3 | ✅ | "7" 정확 |
| M39 | siem alerts.log 카운트 | 3 | ✅ | "4" 정확 |

## 🔴 핵심 발견 — F12 의 한계

### LLM 응답 variation 의 커버 불가
- F12 의 마커 매칭은 specific patterns 만 catch
- M35 의 "이상 징후 없음, 정상" → 마커 매칭 안 됨
- LLM 응답 variation 무한 → marker-based filtering 한계

### KG hit 자체 가 정상 작동 (M36-M39)
- M36-M39 모두 KG hit=3 인데 prompt_fallback 정상 트리거
- 즉 KG hit 자체가 문제 아니라 LLM 의 응답 generation path 가 randomly punt vs not-punt
- 같은 KG hit=3 인데 어떤 mission 은 punt, 어떤 mission 은 정상

### 진짜 fix 후보 — F13 (`_extract_shell_from_prose` 우선)
- 사용자 message 에 "실행:" 패턴 + 명령 추출 가능 → **LLM 첫 응답 보다 도구 실행 우선**
- 즉, planning phase 의 LLM 호출 자체 skip + 곧바로 prose extraction + skill_start
- 가장 확실한 path, paper §4 의 "fast-path" 패턴

### 진짜 fix 후보 — F14 (multi-agent review)
- SubAgent (gemma3:4b) 응답 → Manager (gpt-oss:120b) 가 review/correct
- F14 가 진짜 paper-grade fix. 별도 큰 작업.

## 누적 통계 (reset cycle 1+2+3 = 39 mission)

| 단계 | PASS | △ | ❌ |
|------|-----|---|---|
| cycle 1 M1-M2 (F7 전) | 0 | 0 | 2 |
| cycle 1 M3-M23 (F7 후) | 15 | 5 | 1 |
| cycle 2 M24-M27 (F8 후) | 0 | 1 | 3 |
| cycle 2 M28-M32 (F10 후) | 2 | 1 | 2 |
| cycle 3 M33-M39 (F12 후) | 5 | 0 | 2 |
| **누적** | **22/39 (56%) strict** | **7** | **10** |

- F7 = robust (skill execution 보장) ✅
- F8 = 효과 미미 (gemma3:4b 한계)
- F10 = 효과 미미 (keyword 너무 흔함)
- F12 = 효과 부분적 (KG hit 시 일부 catch — M33 fallback 정상)

## Mission 추가 (M40-M43, cycle 3 후반)

| # | Mission | KG hit | 결과 | 분석 |
|---|---------|--------|-----|------|
| M40 | sysmon-host 상태 (W11) | 3 | ✅ | "Up 28 minutes" 정확 인용 |
| M41 | opencti 상태 (W12) | 3 | ✅ | "Restarting (1) 19 seconds ago" 정확 (환경 문제) |
| M42 | misp 상태 (W13) | 3 | ✅ | "6v6-misp-modules-1 Up 28 minutes (healthy)" 정확 |
| M43 | aicompanion 상태 (aisec) | 3 | △ | "Up 28 minutes" 인용 → "미충족" 자기모순 (F8 부작용) |

## 누적 통계 (reset cycle 1+2+3 = 43 mission)

| 단계 | PASS | △ | ❌ |
|------|-----|---|---|
| cycle 1 M1-M2 (F7 전) | 0 | 0 | 2 |
| cycle 1 M3-M23 (F7 후) | 15 | 5 | 1 |
| cycle 2 M24-M27 (F8 후) | 0 | 1 | 3 |
| cycle 2 M28-M32 (F10 후) | 2 | 1 | 2 |
| cycle 3 M33-M39 (F12 후) | 5 | 0 | 2 |
| cycle 3 M40-M43 (추가) | 3 | 1 | 0 |
| **누적** | **25/43 (58%) strict** | **8** | **10** |

### F8 부작용 발견 (M43)
M43 의 LLM 자기모순: "Up 28 minutes" 인용 → "미충족" 보고.
F8 의 룰 8 ("결과 없으면 미충족 정직 보고") 가 일부 mission 에서 over-applied.
LLM 이 "한국어 평문 결론 = 미충족" 의 default 로 회귀.

## 환경 발견 (cycle 3)

- **opencti**: Restarting (1) 19s — 컨테이너 loop. fresh deploy 의 known issue (이전 cycle 도 동일)
- **misp-modules**: healthy (cycle 1 baseline 의 unhealthy 와 다름 — fresh deploy 28분 후 안정화)

## 다음 cycle (4)

- F13 (prose extraction 우선) — turn loop 시작 전 사용자 message 의 _extract_shell_from_prose 적용
- 또는 self_verify 의 hard-check: `if not tool_outputs: return False` 즉시 (LLM 호출 skip)
- W04~W15 R/B/P 시나리오 mission
