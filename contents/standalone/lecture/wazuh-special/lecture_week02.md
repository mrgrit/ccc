# Week 02 — bastion 에이전트 로그 분석 (Lifecycle Timeline · KG · Self-Correct)

> **특강 2주차**. W01 의 KQL 기초 위에, bastion (KG-LLM 자율 에이전트) 의
> 작업 1건이 어떤 단계를 거치는지 wazuh dashboard 에서 시간순으로 추적.
> 자가 수정 (KG-3 Adapt), KG-2 Reuse, 위험 변경 mission 등 paper §4 의 PE-KG
> 동작을 학생이 직접 검증.

## 학습 목표

- bastion mission lifecycle 의 8 stage 이해
- request_id correlation 으로 1 mission 의 모든 단계 추적
- KG-2 Reuse / KG-3 Adapt 의 wazuh alert 패턴 식별
- 자신의 mission 의 timeline 을 dashboard 로 분석
- 운영/연구 의사결정 (slow mission 진단, 위험 mission 탐지, KG 효과 측정)

## 1. bastion 이 무엇이고 왜 로그를 분석하는가 (10 분)

### 1-1. bastion = KG-LLM 자율 보안 에이전트

학생이 자연어로 mission 을 던지면 bastion 이:

```
[user] → "fw 의 nftables 룰셋 확인해줘"
   │
   ▼
[bastion Manager (LLM, gpt-oss:120b)]
   │  ① KG (Experience Graph) 검색 — 비슷한 mission 과거 사례?
   │  ② Playbook 선택 또는 새 plan 작성
   │  ▼
   ├─ SubAgent (gemma3:4b) 에 skill 명령
   │     "skill=docker_manage target=10.20.30.1 cmd='nft list ruleset'"
   │     ▼
   ├─ SubAgent 실행 → 결과 반환 (stdout, exit code)
   │     ▼
   ├─ Manager 가 결과 판정 (성공/실패/추가 시도 필요)
   │     ▼ (실패 시)
   ├─ "이전 시도가 부족함, 자가 수정" → 다시 다른 skill 로 시도
   │     ▼ (성공 시)
   └─ KG 에 task_outcome anchor 저장 + 학생에게 응답
```

= 매 mission 마다 **5-30 개의 내부 의사결정 + skill 호출**. 모두 syslog 로 wazuh
에 송신 → dashboard 에서 시간순 분석.

### 1-2. 왜 분석하는가 (4 가지)

| 목적 | 사례 |
|------|------|
| **학생 학습** | 내 mission 이 어떻게 실행됐는지 단계별 이해 |
| **성능 진단** | 왜 어떤 mission 은 3초, 어떤 mission 은 5분? |
| **EG 효과 측정** | KG-2 Reuse 가 실제 발생했나? 시간 단축됐나? |
| **위험 통제** | bastion 이 운영 인프라를 함부로 변경했나? |

## 2. bastion lifecycle 8 stage (15 분)

### 2-1. 1 mission = 1 request_id

bastion API `/chat` 호출 시 backend 가 UUID 생성 → 모든 stage 의 syslog 에
`request_id` 필드로 포함. wazuh 에서 이 ID 로 group_by → mission 의 모든 단계가
한 화면에 시간순 나열.

### 2-2. 8 stage 와 Wazuh rule.id

| Stage | event | Wazuh rule.id | level | 의미 |
|-------|-------|---------------|-------|------|
| ① 요청 수신 | `bastion.request.received` | **100211** | 3 | user 가 mission 던짐 |
| ② Plan 단계 | `bastion.event.stage` (planning) | 100212 | 3 | KG 검색 → plan 작성 시작 |
| ③ KG lookup | `bastion.event.lookup_decision` | **100213** | 3 | new / reuse / adapt 결정 + confidence |
| ④ SubAgent 지시 | `bastion.event.skill_start` | **100214** | 3 | skill 이름 + target + attempt |
| ⑤ SubAgent 결과 | `bastion.event.skill_result` | **100215** | 3 | success + output_head |
| ⑥ 판정 | `bastion.event.self_verify` | 100216 | 4 | score + reasoning |
| ⑦ Retry (KG-3 Adapt) | `bastion.event.step_retry` | **100217** | 5 | 자가 수정 — attempt+1 |
| ⑧ 완료 | `bastion.request.completed` | **100218** | 3 | duration_ms + 총 event count |

추가:
- **요약 1줄** (mission 끝나고): `rule.id:100200` (bastion-audit)
- 위험 변경 (drop/MASQUERADE/reverse shell 등): `rule.id:100204` level 10

### 2-3. timeline 예시 — "fw 의 nftables 확인" (sample 1)

```
14:23:01.250  100211 (REQUEST)         course=secuops step=5 — "fw nftables 확인"
14:23:01.350  100213 (KG lookup)       decision=new confidence=0.055 reason=강제 new
14:23:01.400  100212 (stage)           bastion.event.stage planning
14:23:01.500  100214 (DISPATCH)        skill=docker_manage target=10.20.30.1 attempt=1
14:23:02.100  100215 (RETURN)          success=false (No such container)
14:23:02.200  100217 (RETRY)           attempt=2 reason="자기 수정 — 다시 시도"
14:23:02.300  100214 (DISPATCH)        skill=shell  cmd="docker exec 6v6-fw nft list ruleset"
14:23:03.500  100215 (RETURN)          success=true output_head="table inet six_filter..."
14:23:03.600  100216 (JUDGMENT)        score=0.9
14:23:03.700  100218 (COMPLETED)       duration=2450ms events=9
```

학생이 dashboard 에서 위 timeline 한 화면으로 볼 수 있음.

## 3. 핵심 KQL query 10 가지 (15 분)

### 3-1. 모든 bastion lifecycle (기본)

```kql
decoder.name:bastion-lifecycle
```

15분 안의 모든 bastion mission 의 모든 단계 표시.

### 3-2. 특정 mission 의 전체 timeline

```kql
data.request_id:"5271511e81724ab7b26d0b8f7e49fba8"
```

좌측 fields → `@timestamp`, `rule.id`, `data.stage`, `data.skill`, `data.success` 컬럼 추가 → 시간순 정렬 → timeline 완성.

### 3-3. 완료 mission 만 (요약)

```kql
rule.id:100218
```

`data.duration_ms`, `data.seq` 컬럼 추가 → 총 작업 + 시간.

### 3-4. KG decision 분포

```kql
rule.id:100213
```

`data.decision` (new/reuse/adapt), `data.confidence` 컬럼 → KG-2 Reuse 빈도 측정.

### 3-5. 자가 수정 (KG-3 Adapt) 발생

```kql
rule.id:100217
```

각 retry 의 `data.request_id`, `data.attempt` 로 어떤 mission 이 자가 수정 했나.

### 3-6. SubAgent 실패 패턴

```kql
rule.id:100215 AND data.success:false
```

어떤 skill 이 자주 실패하는가? `data.skill` 분포 확인.

### 3-7. 위험 mission

```kql
rule.id:100204 OR rule.id:100217
```

`100204` = drop/MASQUERADE/reverse shell 같은 변경 mission
`100217` = 자가 수정 (잠재 위험)

### 3-8. 느린 mission

```kql
rule.id:100218 AND data.duration_ms:>60000
```

60초 이상 mission. 좌측 fields 의 `data.user_prompt` 보고 원인 분석.

### 3-9. 과목별 mission 통계

```kql
rule.id:100218 AND data.course:secuops
```

`data.duration_ms` 평균 → 과목 별 LLM 부하 분석.

### 3-10. 학생 본인 session

```kql
data.session_id:"s1779156162"
```

자기 session 의 모든 mission timeline.

## 4. 분석 시나리오 5 가지 (15 분)

### 4-1. "왜 이 mission 이 3분 걸렸지?"

1. Discover → `rule.id:100218 AND data.duration_ms:>120000`
2. 가장 긴 mission row 클릭 → `data.request_id` 복사
3. 새 검색: `data.request_id:"<복사값>"`
4. 좌측 fields: `@timestamp`, `rule.id`, `data.stage`, `data.skill`
5. timeline 보고 어디서 시간 소모 식별:
   - LLM 호출 (100212/100213) → Manager LLM 응답 지연
   - skill 실행 (100214→100215 사이) → SubAgent 또는 target 컨테이너 부하
   - retry 다발 (100217 다수) → 자가 수정 무한 반복

### 4-2. "KG-2 Reuse 가 정말 작동하나?"

1. `rule.id:100213` 검색
2. 좌측 `data.decision` → "Visualize" → Pie
3. **new vs reuse vs adapt 비율** 즉시 표시
4. reuse 가 많을수록 EG 학습 효과 큼
5. 같은 user_prompt 의 두 mission 비교 — 두번째가 빠르면 reuse 효과 증명

### 4-3. "bastion 이 운영 인프라를 변경했나?"

1. `rule.id:100204` 검색 (level 10 = 위험)
2. 결과 있으면 → `data.user_prompt` 로 어떤 mission 인지
3. `data.request_id` 로 그 mission 의 100214/100215 추적
4. 변경된 컨테이너 확인 (`data.host`) → 수동 cleanup 결정

**실제 사고 예** (2026-05-19): bastion 의 P24 검증 mission "fw nftables drop counter
룰 추가" 가 자가 수정 후 실제로 `nft add rule drop` 실행 → fw 80/443 차단.
→ wazuh 의 rule.id 100204 alert 가 떠야 함.

### 4-4. "어제 가장 자주 실패한 skill?"

1. `rule.id:100215 AND data.success:false AND @timestamp:>now-1d`
2. 좌측 `data.skill` → Top values
3. 가장 많은 skill 식별 → 그 skill 의 docker exec 권한, target 컨테이너 가용성 등 점검

### 4-5. "내 mission 의 EG 학습 효과"

1. `data.session_id:"내세션"`
2. `rule.id:100213` 만 → `data.decision` 의 reuse 비율
3. 시간이 갈수록 reuse 비율 증가 → 학습 효과
4. `data.confidence` 평균 추세 → 신뢰도 향상

## 5. Dashboard 만들기 — Bastion Operations (10 분)

### 5-1. 추천 panel 7 개

1. **Total Mission** (Metric) — `rule.id:100218` count
2. **Avg Duration** (Metric) — `rule.id:100218` avg of `data.duration_ms`
3. **Mission by Course** (Bar) — `rule.id:100218` term=`data.course`
4. **KG Decision** (Pie) — `rule.id:100213` term=`data.decision`
5. **Self-Correct Trend** (Line) — `rule.id:100217` date_histogram
6. **Top SubAgent Skills** (Tag Cloud) — `rule.id:100214` term=`data.skill`
7. **Risky Missions** (Data Table) — `rule.id:100204` columns=`@timestamp,data.user_prompt`

### 5-2. 단계

1. ☰ → Dashboards → **Create new dashboard**
2. Add → 위 7 chart (각 자정 후 Visualize 에서 미리 저장)
3. Time picker → "Last 24 hours"
4. **Save** → "Bastion Operations"

### 5-3. 활용

- 강사: 매일 dashboard 1 분 보고 어제 학생들 활동 파악
- 학생: 자기 session_id filter 추가 → 자기 활동만
- 운영자: Risky Missions 알림 받으면 즉시 대응

## 6. Alert (실시간 알림) — 선택 학습 (5 분)

특정 패턴 발생 시 즉시 Slack/이메일 알림 받기.

### 6-1. Wazuh `active-response`

`/var/ossec/etc/ossec.conf` 에 추가:
```xml
<active-response>
  <command>bastion-alert</command>
  <location>local</location>
  <rules_id>100204,100217</rules_id>
</active-response>
```

- `100204` (위험 변경) 또는 `100217` (자가 수정) 발생 시 `bastion-alert` 명령 실행
- 명령은 별도 script (Slack webhook, 이메일 송신 등)

(상세는 별도 운영 매뉴얼)

### 6-2. Dashboard 내 alert (Watcher)

OpenSearch Watcher 로 5분마다 query → 결과 있으면 알림.
초보 학생은 Discover 만으로 충분.

## 7. 종합 평가 (lab 에서 실측)

학생은 lab 의 6 step 에서 직접:
- 자기 mission 1건 실행 → 모든 stage syslog 발생
- dashboard 에서 request_id 로 추적
- KG decision / self-correct / completed event 모두 식별
- duration_ms 측정 + 평균 vs 자기 mission 비교
- 위험 alert 발생 여부 확인 + 분석 report 1쪽 작성

## 8. paper §4 PE-KG 와의 매핑

P24 의 266 mission 검증 결과:
- KG-1 Lookup: 모든 mission (decoder.name 자동)
- KG-2 Reuse: 10+ 회 확정 (anchor_id 공유)
- KG-3 Adapt: anc-bce8d8cd594b (fail) → anc-dec0547e8f0d (success) 자가 수정 pair
- KG-4 New: 168+ anchor 영구 저장 (immune=1)

Wazuh dashboard 의 `data.decision`, `rule.id:100217`, `data.request_id` 가 위 4
단계의 실측 증거. **paper §4 의 PE-KG 가설을 학생이 직접 dashboard 로 검증 가능**.

## 9. 다음 학습 (선택)

- Wazuh Manager 의 custom rule 작성 (자기 환경의 특수 패턴 탐지)
- OpenSearch SQL plugin 으로 복잡 query
- bastion 의 graph DB (`/admin/bastion/graph/search`) 직접 조회
- 6bq5 EG 포털 (192.168.0.110:8500) 의 별도 view

## 정리 — 한 줄 가이드

```
"내 mission 의 모든 의사결정과 시간을 알고 싶다 →
 https://siem.6v6.lab 접속 → Discover → data.request_id:"내값" 검색"
```
