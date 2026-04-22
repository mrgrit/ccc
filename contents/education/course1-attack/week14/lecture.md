# Week 14: Bastion 자연어 자동 침투 테스트

## 학습 목표
- Bastion 에이전트의 실제 아키텍처(LLM + Skill + Evidence DB)를 이해한다
- `/chat` (스트리밍)과 `/ask` (단답) 엔드포인트의 차이를 구분한다
- 자연어 지시로 다단계 공격 시나리오(정찰→취약점→악용→보고)를 실행한다
- Bastion이 선택한 Skill과 실제 실행 결과를 Evidence DB에서 검증한다
- 수동 침투 테스트와 자연어 자동화의 차이·한계를 비교한다
- 자동화 결과를 모의해킹 보고서 형식으로 정리한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | **Bastion 에이전트 호스트** (:8003 API, :11434 Ollama) |
| secu | 10.20.30.1 | 표적 (방화벽) |
| web | 10.20.30.80 | 표적 (JuiceShop :3000) |
| siem | 10.20.30.100 | 표적 (Wazuh) |

## 강의 시간 배분 (3시간)

| 시간 | 내용 |
|------|------|
| 0:00-0:30 | Bastion 실제 아키텍처 (Part 1) |
| 0:30-1:00 | /chat vs /ask, Skill·Evidence 구조 (Part 2) |
| 1:00-1:10 | 휴식 |
| 1:10-1:50 | 단일 지시 자동화 (Part 3) |
| 1:50-2:30 | 다단계 킬체인 자동화 (Part 4) |
| 2:30-2:40 | 휴식 |
| 2:40-3:10 | Evidence 검증·보고서 생성 (Part 5) |
| 3:10-3:30 | 수동 vs 자동 비교 + 한계 (Part 6) |
| 3:30-3:40 | 과제 |

---

# Part 1: Bastion 실제 아키텍처

## 1.1 구성요소

```
[학생/Claude Code/CLI] → HTTP (:8003)
                              ↓
                         [Bastion Agent]
                           ┌───────────────────┐
                           │ LLM (Ollama)      │  ← 자연어 해석 (:11434)
                           │ Skill Registry    │  ← 실행 가능한 Python 함수들
                           │ Playbook Store    │  ← Skill 조합 시나리오
                           │ Evidence DB       │  ← 실행 이력 (SQLite)
                           └───────────────────┘
                              ↓
                         실행 결과 (자연어 요약)
```

**핵심 차이 (이전 주차 대비):**
- ~~Project/Stage/Task/PoW-Block~~ 구조 **없음** (기존 교안은 오류)
- 실제는 **대화형 Agent**: 학생이 자연어로 요청 → LLM이 의도 파악 → Skill 실행 → 결과 반환

## 1.2 제공 엔드포인트 (실측)

```bash
curl -s http://10.20.30.200:8003/health | python3 -m json.tool
```

**예상 출력:**
```json
{
    "status": "ok",
    "model": "gemma3:4b",
    "llm": "http://localhost:11434",
    "skills": 12,
    "playbooks": 5
}
```

| 엔드포인트 | 메서드 | 용도 |
|-----------|--------|------|
| `/health` | GET | 가동 상태·모델 정보 |
| `/skills` | GET | 보유 Skill 목록 |
| `/playbooks` | GET | Playbook 목록 |
| `/chat` | POST | 자연어 요청 (NDJSON 스트림) |
| `/ask` | POST | 자연어 질문 (단답형) |
| `/evidence` | GET | 실행 이력 (limit 파라미터) |
| `/assets` | GET | 관리 대상 자산 목록 |
| `/onboard` | POST | 새 VM 온보딩 |

## 1.3 핵심 데이터 구조

**Skill 객체:**
```json
{
  "name": "ssh_exec",
  "description": "원격 VM에 SSH로 명령 실행",
  "params": ["host", "cmd"],
  "risk_level": "medium"
}
```

**Evidence 레코드:**
```json
{
  "timestamp": "2026-04-23T14:30:22",
  "user_message": "web 서버의 포트 스캔해줘",
  "skill": "nmap_scan",
  "params": {"target": "10.20.30.80", "ports": "22,80,3000"},
  "output": "PORT STATE SERVICE\n22/tcp open ssh\n...",
  "success": true
}
```

---

# Part 2: /chat vs /ask

## 2.1 /ask — 단답형

**이것은 무엇인가?** 가장 간단한 인터페이스. 자연어 질문 → 자연어 답변 + skill_outputs 배열만 반환.

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 서버의 주요 포트를 스캔해줘"}'
```

**응답 구조:**
```json
{
  "answer": "web 서버(10.20.30.80) 스캔 결과:\n- 22/tcp SSH\n- 80/tcp HTTP\n- 3000/tcp Node.js\n...",
  "success": true,
  "skill_outputs": [
    {"skill": "nmap_scan", "output": "...", "success": true}
  ],
  "event_count": 7
}
```

**언제 쓰나:** 빠른 점검, 스크립트에서 한 번 호출하고 결과만 필요할 때.

## 2.2 /chat — 스트리밍

**이것은 무엇인가?** NDJSON(한 줄당 한 JSON) 스트림으로 **이벤트 진행상황**을 실시간 반환. TUI·대화형 UI에 적합.

```bash
curl -N -s -X POST http://10.20.30.200:8003/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 서버 공격 표면 요약해줘", "stream": true}' \
  | head -20
```

**명령 분해:**
- `-N`: no-buffer (스트림을 즉시 출력)
- `"stream": true`: NDJSON 스트림 요청

**이벤트 유형:**
- `thought`: LLM의 추론 단계
- `skill_call`: Skill 호출 결정
- `skill_result`: Skill 실행 결과
- `stream_token`: 최종 응답 토큰 단위
- `done`: 완료

**언제 쓰나:** UI에서 "생각 중..." 표시, Skill 호출 과정을 사용자에게 보여줄 때.

## 2.3 Skill 목록 확인

```bash
curl -s http://10.20.30.200:8003/skills | python3 -c "
import sys, json
for s in json.load(sys.stdin):
    print(f\"  [{s.get('name','?'):20s}] {s.get('description','')[:50]}\")
"
```

**예상 출력 (일부):**
```
  [ssh_exec            ] 원격 VM에 SSH로 명령 실행
  [nmap_scan           ] 포트 스캔
  [http_probe          ] HTTP 요청 + 헤더 수집
  [wazuh_query         ] Wazuh alert 검색
  [suricata_rules_show ] Suricata 룰 덤프
  [nft_show            ] nftables 룰 조회
  ...
```

---

# Part 3: 단일 지시 자동화

## 3.1 정찰 자동화

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "10.20.30.0/24 네트워크 호스트 발견 후, web(10.20.30.80)의 열린 포트와 서비스 버전을 nmap -sV로 확인하고 결과를 표로 정리해줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

**예상 응답:**
```
네트워크 스캔 결과:
- 10.20.30.1 (secu)   up
- 10.20.30.80 (web)   up
- 10.20.30.100 (siem) up
- 10.20.30.200 (manager) up

web 서버 포트:
| 포트 | 서비스 | 버전 |
|-----|--------|------|
| 22  | SSH    | OpenSSH 8.9p1 |
| 80  | HTTP   | Apache 2.4.52 |
| 3000| HTTP   | Node.js Express (JuiceShop) |
```

**내부 동작:** LLM이 의도 파악 → `nmap_scan` Skill 호출 → 결과를 표로 가공 → 자연어 응답.

## 3.2 웹 공격 점검

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "JuiceShop(http://10.20.30.80:3000) 로그인 API에 '"'"' OR 1=1-- 페이로드로 SQL Injection을 시도하고, 성공 시 받은 JWT의 role 필드를 디코딩해서 보여줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

## 3.3 방어 설정 조회

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "secu 서버(10.20.30.1)의 nftables 룰셋 전체를 조회하고, forward chain의 기본 정책이 무엇인지 알려줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

---

# Part 4: 다단계 킬체인 자동화

## 4.1 Week 02~13 통합 시나리오

**이것은 무엇인가?** 단일 `/ask`로 여러 단계의 공격을 연쇄 실행. LLM이 내부에서 Skill들을 조합.

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "JuiceShop에 대한 전체 킬체인을 자동 실행해줘: (1) web 포트 스캔, (2) HTTP 보안 헤더 수집, (3) /ftp 파일 목록, (4) SQLi로 admin 로그인 시도, (5) 성공 시 JWT에서 role 확인, (6) admin 토큰으로 /api/Users 호출, (7) MITRE ATT&CK 기법으로 매핑한 결론. 각 단계를 번호 매겨서 결과를 보여줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

**예상 응답 (자연어):**
```
JuiceShop 전체 킬체인 결과:

1. 포트 스캔 (T1046)
   22 SSH, 80 Apache, 3000 Node.js

2. 보안 헤더 (T1592)
   CSP 부재, HSTS 부재, CORS 완전 개방

3. /ftp 파일 목록 (T1083)
   8개 파일: legal.md, package.json.bak, coupons_2013.md.bak 등

4. SQLi 관리자 로그인 (T1190)
   페이로드: ' OR 1=1--
   결과: HTTP 200, JWT 토큰 발급

5. JWT 디코딩
   role: admin, id: 1, email: admin@juice-sh.op

6. /api/Users
   21명 이메일 + MD5 해시 덤프 성공

7. ATT&CK 매핑
   Reconnaissance → T1595
   Initial Access → T1190
   Credential Access → T1552
   Discovery → T1083

결론: CRITICAL 취약점 다수 발견, admin 권한 탈취 성공.
```

## 4.2 스트리밍 모드로 "생각 과정" 관찰

```bash
curl -N -s -X POST http://10.20.30.200:8003/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 서버 공격 체인 실행해줘", "stream": true}' \
  | head -30
```

**출력 (NDJSON, 이벤트별 1줄):**
```
{"event":"thought","content":"포트 스캔부터 시작해야겠군요"}
{"event":"skill_call","skill":"nmap_scan","params":{"target":"10.20.30.80"}}
{"event":"skill_result","skill":"nmap_scan","success":true,"output":"..."}
{"event":"thought","content":"JuiceShop이 있네요. HTTP 헤더 확인."}
{"event":"skill_call","skill":"http_probe","params":{"url":"..."}}
...
{"event":"stream_token","token":"결론"}
{"event":"stream_token","token":":"}
...
{"event":"done"}
```

**결과 해석:** LLM의 **ReAct 루프**(Thought → Action → Observation → Thought → ...)를 관찰 가능. 한 번의 `/chat` 호출이 내부적으로 3~10회의 Skill 호출로 이어짐.

---

# Part 5: Evidence 검증·보고서 생성

## 5.1 Evidence 조회

**이것은 무엇인가?** Bastion의 모든 작업은 **SQLite Evidence DB**에 영구 저장. 감사·재현·학습용.

```bash
# 최근 20건
curl -s "http://10.20.30.200:8003/evidence?limit=20" | python3 -c "
import sys, json
events = json.load(sys.stdin)
print(f'총 {len(events)}건 이력')
print('-' * 80)
for e in events[:10]:
    ts = e.get('timestamp','')[:19]
    skill = e.get('skill','?')
    ok = '✓' if e.get('success') else '✗'
    msg = e.get('user_message','')[:50]
    print(f'{ts} {ok} [{skill:15s}] {msg}')
"
```

## 5.2 Skill별 통계

```bash
curl -s "http://10.20.30.200:8003/evidence?limit=100" | python3 -c "
import sys, json
from collections import Counter
events = json.load(sys.stdin)
skills = Counter(e.get('skill','?') for e in events)
success = Counter(e.get('skill','?') for e in events if e.get('success'))
print(f'{\"Skill\":<20s} {\"Total\":>6s} {\"Success\":>8s}  Rate')
for s, total in skills.most_common():
    rate = (success[s] / total * 100) if total else 0
    print(f'{s:<20s} {total:>6d} {success[s]:>8d} {rate:>5.0f}%')
"
```

**결과 해석:** 어떤 Skill이 자주 호출되는지, 실패율은 어느 정도인지 → Skill 품질 개선·추가 필요 여부 판단.

## 5.3 자산(Assets) 확인

```bash
curl -s http://10.20.30.200:8003/assets | python3 -m json.tool
```

**결과 해석:** Bastion이 알고 있는 관리 대상 VM 목록. 역할·IP·상태(healthy/unreachable). 이 목록이 없으면 `/ask`에서 "web 서버"가 어딘지 모름.

## 5.4 /ask로 직접 보고서 요청

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "오늘 수행한 최근 20건의 evidence를 분석해서 (1) 발견한 취약점 목록 (2) 각 취약점의 CVSS 심각도 (3) 방어 권고 3가지를 포함한 모의해킹 보고서를 한국어로 작성해줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

**예상 응답:** 자동으로 `/evidence` 조회 Skill → 분석 → 보고서 자연어 생성.

---

# Part 6: 수동 vs 자동 비교

## 6.1 비교 매트릭스

| 항목 | 수동 (Week 02~13) | Bastion 자연어 |
|------|-------------------|----------------|
| 타이핑 | 명령별 매번 | 자연어 1회 |
| 학습 곡선 | nmap/curl/sqlmap 등 개별 도구 | 자연어만 |
| 재현성 | 쉘 히스토리 (불완전) | Evidence DB (완전) |
| 공유 | 스크립트 작성 | `/evidence` 공유만으로 |
| 창의적 탐색 | 높음 | LLM 의도 해석 한계 |
| 정밀 제어 | 높음 (옵션 조합 자유) | 중간 (LLM 선택에 의존) |
| 속도 | 익숙하면 빠름 | LLM 응답 대기 |
| 증거 | 부분적 | 모든 호출 자동 기록 |
| 한계 | 작업자 지식 한계 | LLM 지식 한계, hallucination |

## 6.2 Bastion이 못 하는 것

- **전혀 새로운 Skill**이 필요한 작업 (Skill 레지스트리에 없으면 실패)
- **복잡한 상호작용형 툴** (msfconsole 같은 인터랙티브)
- **매우 세밀한 타이밍 제어** (스텔스 스캔 미세 조정)
- **LLM hallucination 리스크**: 존재하지 않는 명령을 생성하거나, 실제와 다른 결과 요약

→ **수동과 자동의 적절한 조합**이 실무 현실.

## 6.3 자동화에 적합한 작업

✓ 반복적 정찰·헤더 점검
✓ 대량 호스트 동시 확인
✓ 보고서 자동 생성
✓ 증적 중심 감사 대응

## 6.4 자동화가 위험한 작업

✗ 운영 시스템에 파괴적 변경
✗ 검증되지 않은 Skill 호출
✗ 외부 공개 시스템 스캔 (탐지·법적 문제)

---

## 과제 (다음 주까지)

### 과제 1: 단일 지시 자동화 (30점)
다음 5개 자연어 지시를 각각 실행 후 응답·`/evidence` 기록을 제출 (각 6점):

1. `10.20.30.0/24 네트워크 맵을 그려줘 (각 호스트 역할·IP·주요 포트)`
2. `JuiceShop의 보안 헤더 점검 + 누락된 헤더 위험도 분석`
3. `secu의 nftables forward chain 정책 + 의심 룰 3개 선정`
4. `web 서버에서 SUID 바이너리 전수 검사 + GTFOBins 연동 위험도`
5. `최근 1시간 동안 Wazuh에서 level>=5 alert 상위 5건 요약`

### 과제 2: 킬체인 자동화 (30점)
`/chat` 스트리밍 모드로 **전체 킬체인 1회 실행** + 관찰 이벤트 로그 제출.

- `thought`, `skill_call`, `skill_result` 이벤트 몇 개 발생했는가?
- Bastion이 호출한 Skill 이름 전체 목록
- 최종 `answer`에서 ATT&CK 기법 매핑

### 과제 3: 보고서 (25점)
`/ask`로 "최근 50건 evidence 분석 후 모의해킹 보고서 작성" 실행 + 결과 md로 편집하여 제출.
- Exec Summary / Findings / CVSS / Remediations 4섹션 포함
- 보고서의 정확도·누락·환각 사례 본인 코멘트 추가

### 과제 4: 수동 vs 자동 비교 (15점)
같은 시나리오(예: web 서버 SQLi 탐지)를 **수동(Week 04)**과 **Bastion(/ask)** 두 방식으로 실행 후 비교표 작성.
- 소요 시간·타이핑 수·발견 누락·hallucination 사례

---

## 다음 주 예고

**Week 15: 최종 프로젝트 — PTES 보고서 작성**
- PTES 방법론 (Pre-engagement → Recon → Threat → Exploit → Post-exploit → Reporting)
- 전체 인프라 대상 침투 테스트 시험
- CVSS v3.1 기반 보고서
- 방어 권고 포함

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 |
|------|------|------|
| **Bastion Agent** | - | LLM 기반 보안 운영 에이전트 (:8003) |
| **Skill** | - | Bastion이 실행 가능한 Python 함수 단위 |
| **Playbook** | - | Skill 조합 시나리오 |
| **Evidence DB** | - | SQLite 기반 작업 이력 영구 저장 |
| **NDJSON** | Newline-Delimited JSON | 한 줄당 한 JSON 스트림 포맷 |
| **ReAct 루프** | - | LLM Agent의 Thought→Action→Observation 패턴 |
| **Hallucination** | - | LLM이 실제와 다른 내용을 생성하는 현상 |
| **`/ask`** | - | 단답형 엔드포인트 |
| **`/chat`** | - | 스트리밍 이벤트 엔드포인트 |
| **`/evidence`** | - | 이력 조회 엔드포인트 |

---

## 📂 실습 참조 파일 가이드

### Bastion API (이번 주 중심)

| 메서드 | 경로 | 이번 주 사용 |
|--------|------|--------------|
| GET | `/health` | 가동 확인 |
| GET | `/skills` | 보유 Skill 확인 |
| GET | `/playbooks` | Playbook 확인 |
| POST | `/ask` | 단일 지시 (Part 3, 과제 1·3·4) |
| POST | `/chat` | 스트리밍 지시 (Part 4, 과제 2) |
| GET | `/evidence?limit=N` | 이력·통계 (Part 5) |
| GET | `/assets` | 자산 목록 (Part 5) |

**요청 옵션 (`/chat`, `/ask` 공통):**
```json
{
  "message": "자연어 지시",
  "stream": true,            // chat만
  "auto_approve": true,      // high risk 자동 승인
  "course": "attack-ai",     // Evidence 메타데이터
  "lab_id": "w14_t1",
  "test_session": "..."
}
```

### curl 이번 주 패턴

| 패턴 | 용도 |
|------|------|
| `curl -X POST /ask -d '{"message":"..."}'` | 단답 자동화 |
| `curl -N -X POST /chat -d '{...,"stream":true}'` | 스트림 실시간 |
| `curl /evidence?limit=N` | 이력 |
| `curl /health` | 가동 확인 |

### python3 후처리

- `json.load(sys.stdin)` → JSON 파싱
- `collections.Counter` → Skill 빈도 통계
- NDJSON 스트림은 한 줄씩 `json.loads` 후 `.get("event")`로 분기

---

> **참고:** Bastion API는 외부 노출 금지(내부망만). 자연어 요청에 파괴적 명령이 포함되면 `auto_approve: false`로 사전 승인 대화를 유도할 수 있다.
