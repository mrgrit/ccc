# Bastion Autopilot — Reset Cycle 7 (2026-05-18, 7 mission + F15)

**시각**: 2026-05-18 20:10-20:50 (UTC) 약 40분
**대상**: F15 (llm_translate prompt — 컨테이너명 보존) + KG schema 탐사
**누적**: cycle 1-7 = 93 mission

## F15 fix: llm_translate prompt

`_extract_shell_from_prose` 가 명령 추출 실패 시 LLM 변환 path. 기존 prompt 가 컨테이너명 `6v6-bastion` → `127.0.0.1` 잘못 변환 (M17, M84, M87 패턴).

**Fix**: prompt 에 명시 룰 추가
```
1. NEVER convert container names to IPs. If task says `6v6-bastion`, `6v6-fw`, `6v6-attacker` — keep as-is. DO NOT replace with 127.0.0.1, 10.20.30.x.
2. Preserve exact command syntax including `docker exec`, `ssh`, quotes, pipes.
3. If task contains shell command after `실행:` or `Run:` — copy verbatim.
```

## Mission 결과 (cycle 7, M87-M93)

| # | Mission | F15 효과 | 결과 |
|---|---------|---------|-----|
| M87 | docker exec bastion sqlite3 EG db | F15 적용 전 | ❌ llm_translate `6v6-bastion → 127.0.0.1` |
| M88 | M87 재시도 (F15 후) | F15 ✅ | △ 명령 정확 변환, sqlite3 미설치 정직 보고 |
| M89 | docker exec bastion ls /var/lib/bastion | - | ✅ 빈 디렉토리 정확 |
| M90 | docker exec bastion find *.db | - | ✅ 5 DB 파일 정확 (evidence/graph/audit/+) |
| M91 | python3 sqlite SELECT schema | - | ✅ 13 테이블 정확 (history_anchors/events/narratives/nodes/edges/FTS) |
| M92 | anchor COUNT | - | △ "90" 정확 인용했으나 LLM 응답 짧음 |
| M93 | anchor kind GROUP BY | - | ❌ output `[('task_outcome', 91)]` 정확, **LLM 가짜 "192.168.1.100 brd ..." hallucination** |

## 통계 (cycle 7)

- PASS: **3/7 = 43%** strict
- △ partial: 2 (F15 적용으로 명령 정확 / 환경 fact 의 정직 보고)
- ❌ fail: 2 (M87 F15 전, M93 LLM hallucination)
- skill success: 6/7 = 86%

## 누적 통계 (1-7 = 93 mission)

| 누적 | PASS | △ | ❌ |
|------|-----|---|---|
| **93** | **60/93 (65%) strict** | **14** | **19** |

## 핵심 발견 (cycle 7)

### F15 ✅ 효과 입증
- M88 의 명령 변환 = `6v6-bastion` 보존 (json 안에 정확)
- llm_translate path 의 컨테이너→IP 잘못 변환 차단

### KG schema 실 검증 (paper §4 의 PE-KG 구현)
- `history_anchors` (M91 schema, M92 count=90)
- `nodes / edges + nodes_fts` (FTS 검색)
- `history_events / narratives / changelogs`
- → paper 의 5 tier (Anchor/Concept/Playbook/Asset/Policy) 의 SQL 구현 확인

### M93 의 결정적 LLM hallucination
- stdout: `[('task_outcome', 91)]`
- LLM: "192.168.1.100: brd 192.168.1.255 ... 9cac370b74: cip4 inet ..."
- = **완전 fake** (ip addr show 의 과거 anchor 의 잔흔)
- gemma3:4b 의 한계 — F15 fix 후도 일부 mission 의 LLM 응답 noise

## 다음 cycle (8)

- F16 (multi-agent — Manager 120b review SubAgent 4b)
- 100+ mission 누적
- 환경 fact 보고 (sqlite3 부재) 의 학생 평가 측면 분석
