# Week 15: 프로젝트 C — 보안 교육 에이전트 + 최종 발표

## 학습 목표

- RAG 기반 보안 교육 AI 튜터 에이전트를 구축하고 통합 시연한다
- OpsClaw Experience를 학습 기록으로 활용하는 시스템을 완성한다
- 프로젝트 A(인시던트 대응), B(CTF 풀이), C(교육 에이전트) 3개를 동시 시연한다
- 각 프로젝트의 completion-report를 작성하고 최종 발표를 수행한다
- 15주간의 AI 보안 에이전트 학습을 종합 정리한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

## 강의 시간 배분 (3시간)

| 시간 | 파트 | 내용 | 형태 |
|------|------|------|------|
| 0:00-0:20 | Part 1 | 프로젝트 C 보안 교육 에이전트 설계 | 이론+실습 |
| 0:20-0:55 | Part 2 | RAG 튜터 에이전트 구현 | 실습 |
| 0:55-1:25 | Part 3 | Experience 학습 기록 시스템 | 실습 |
| 1:25-1:35 | — | 휴식 | — |
| 1:35-2:05 | Part 4 | 3개 프로젝트 통합 시연 준비 | 실습 |
| 2:05-2:40 | Part 5 | 최종 발표 (팀당 10분) | 발표 |
| 2:40-3:00 | Part 6 | 과정 종합 정리 + 수료 | 마무리 |

## 용어 해설 (AI보안에이전트 과목)

| 용어 | 설명 | 예시 |
|------|------|------|
| **AI 튜터** | AI가 학습자의 질문에 답하고 학습을 안내하는 에이전트 | "nftables 규칙 작성법 알려줘" |
| **RAG** | Retrieval-Augmented Generation, 검색 증강 생성 | 교안 검색 후 LLM이 답변 생성 |
| **학습 기록** | 학생의 질문/답변 이력을 기록하는 시스템 | OpsClaw Experience 활용 |
| **교안 인덱싱** | 교안 콘텐츠를 검색 가능하게 등록하는 과정 | FTS tsvector 인덱싱 |
| **Chunk** | 긴 문서를 검색 단위로 분할한 조각 | 500자 단위 |
| **Context** | LLM에 전달하는 참고 정보 | 검색된 교안 내용 |
| **Grounding** | LLM 응답을 실제 문서에 근거하게 만드는 기법 | RAG로 교안 참조 |
| **Hallucination** | LLM이 사실과 다른 내용을 생성 | 존재하지 않는 명령어 설명 |
| **completion-report** | OpsClaw 프로젝트 완료 보고서 | summary + outcome + details |
| **Evidence** | 에이전트 실행 결과 감사 기록 | 모든 질의/응답 기록 |
| **시연 (Demo)** | 구현된 시스템의 실제 동작을 보여주는 발표 | 라이브 데모 |
| **PoW 리더보드** | 에이전트별 작업 증명 순위 | 팀별 evidence 수 비교 |
| **FTS** | Full-Text Search, 전문 검색 | PostgreSQL tsquery |
| **Prompt Template** | LLM 프롬프트의 재사용 가능한 양식 | 교육 질의 전용 프롬프트 |
| **Feedback Loop** | 결과를 다시 입력으로 활용하는 순환 구조 | 학생 피드백 → 교안 개선 |
| **Rubric** | 평가 기준표 | evidence 수 30%, 발표 20% |

---

## Part 1: 프로젝트 C 보안 교육 에이전트 설계 (0:00-0:20)

### 1.1 프로젝트 요구사항

| 항목 | 요구사항 |
|------|---------|
| 팀 구성 | 동일 팀 (2-3명) |
| 목표 | 교안/문서를 RAG로 참조하여 학생 질문에 답하는 AI 튜터 |
| 지식 소스 | 보안 교안 (lecture.md), OpsClaw Experience |
| LLM | llama3.1:8b (답변 생성) |
| 기록 | 모든 질의/응답을 OpsClaw Evidence로 기록 |
| 평가 | 답변 정확도 + Evidence 수 + 시연 품질 |

### 1.2 교육 에이전트 아키텍처

```
[보안 교육 AI 튜터 에이전트]

  학생 질문 → Retrieve (FTS) → Augment (Context) → Generate (LLM)
                  |                                      |
                  v                                      v
             교안 DB + Exp.                         답변 + 출처
                                                        |
                                                        v
                                                  Evidence (학습 기록)
```

### 1.3 최종 평가 기준 (3개 프로젝트 합산)

| 프로젝트 | 배점 | 핵심 평가 항목 |
|----------|------|---------------|
| A. 인시던트 대응 | 35% | 파이프라인 완성도, 자동 차단 성공률 |
| B. CTF 풀이 | 35% | 발견 취약점 수, 안전성 준수 |
| C. 교육 에이전트 | 30% | 답변 정확도, RAG 품질, 시연 |
| **공통** | 보너스 | Evidence 총합, PoW 리더보드 순위 |

---

## Part 2: RAG 튜터 에이전트 구현 (0:20-0:55)

### 2.1 교안 인덱싱 확인

> **실습 목적**: 한 학기 동안 학습한 AI 보안 에이전트 기술을 종합하여 완전한 자율 보안 에이전트를 설계하고 발표하기 위해 수행한다
>
> **배우는 것**: 에이전트 설계, 도구 통합, 안전 제어, RAG, PoW, RL을 종합한 프로덕션급 보안 에이전트의 아키텍처를 이해한다
>
> **결과 해석**: 설계한 에이전트의 기능 완성도, 안전성, 성능, 확장성 항목별 점수로 프로젝트 품질을 종합 평가한다
>
> **실전 활용**: 보안 에이전트 제품 설계, 스타트업 PoC 개발, 조직의 AI 보안 자동화 전략 수립에 활용한다

```bash
# security_knowledge 테이블에 교안이 인덱싱되어 있는지 확인
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw << 'SQLEOF'
-- 인덱싱된 교안 수 확인
SELECT category, COUNT(*) AS cnt
FROM security_knowledge
GROUP BY category
ORDER BY cnt DESC;

-- education 카테고리 검색 테스트
SELECT title, LEFT(content, 100) AS preview
FROM security_knowledge
WHERE category = 'education'
LIMIT 5;
SQLEOF
```

### 2.2 교안 추가 인덱싱 (필요시)

```bash
# 부족한 교안 데이터를 추가 삽입
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw << 'SQLEOF'
-- 핵심 보안 주제별 교안 데이터 추가
INSERT INTO security_knowledge (category, title, content, tags, source) VALUES
('education', 'Suricata IPS 규칙 작성법',
 'Suricata 규칙 구조: action protocol src_ip src_port -> dst_ip dst_port (options). 예시: alert http any any -> any any (msg:"SQL Injection Detected"; content:"UNION SELECT"; sid:1000001; rev:1;). action: alert(경보), drop(차단), pass(통과). protocol: tcp, udp, http, dns.',
 ARRAY['suricata', 'ips', 'rule', 'tutorial'],
 'edu-suricata-001'),

('education', 'OpsClaw 프로젝트 생성과 실행',
 'OpsClaw 프로젝트 생성: POST /projects (name, request_text, master_mode). Stage 전환: /plan → /execute. 태스크 실행: /execute-plan (tasks 배열, subagent_url). 결과 확인: /evidence/summary. 완료: /completion-report. 인증: X-API-Key 헤더 필수.',
 ARRAY['opsclaw', 'project', 'api', 'tutorial'],
 'edu-opsclaw-001'),

('education', 'LLM 프롬프트 엔지니어링 기초',
 'LLM 프롬프트 작성법: 1) system 메시지로 역할 부여 2) 구체적 출력 형식 지정 (JSON 등) 3) temperature 0.1~0.3으로 결정론적 응답 유도 4) few-shot 예시 제공 5) 부정형 지시("하지 마세요") 보다 긍정형("만 하세요") 사용.',
 ARRAY['llm', 'prompt', 'engineering', 'tutorial'],
 'edu-prompt-001'),

('education', 'Wazuh 경보 rule_level 해석',
 'Wazuh rule_level: 0-3(정보), 4-7(낮은 위험), 8-11(높은 위험), 12-15(심각). 주요 rule_id: 5710(SSH 인증 실패), 5712(SSH 브루트포스), 31103(웹서버 에러), 550(사용자 로그인). level 10 이상은 즉시 분석 필요.',
 ARRAY['wazuh', 'rule', 'level', 'alert'],
 'edu-wazuh-level-001'),

('education', 'SQL Injection 방어 기법',
 'SQL Injection 방어: 1) 파라미터화된 쿼리 사용 (Prepared Statement) 2) ORM 사용 3) 입력 검증 (화이트리스트) 4) 웹 방화벽(WAF) 적용 5) 최소 권한 DB 계정 사용. JuiceShop의 /rest/products/search 엔드포인트가 SQLi에 취약한 대표 사례.',
 ARRAY['sql-injection', 'defense', 'waf', 'tutorial'],
 'edu-sqli-defense-001');

SELECT 'education 데이터 추가 완료' AS status;
SELECT COUNT(*) AS total FROM security_knowledge WHERE category = 'education';
SQLEOF
```

### 2.3 RAG 튜터 에이전트 구현

```python
#!/usr/bin/env python3
"""education_tutor.py — RAG 기반 보안 교육 AI 튜터 에이전트"""
import json
import time
import requests
import psycopg2

OLLAMA_URL = "http://192.168.0.105:11434"
MANAGER_URL = "http://localhost:8000"
API_KEY = "opsclaw-api-key-2026"
HEADERS = {"Content-Type": "application/json", "X-API-Key": API_KEY}
DB_CONFIG = {
    "host": "127.0.0.1", "port": 5432,
    "dbname": "opsclaw", "user": "opsclaw", "password": "opsclaw",
}

class EducationTutor:
    """보안 교안을 RAG로 참조하여 학생 질문에 답하는 AI 튜터."""

    def __init__(self, project_id: str, model: str = "llama3.1:8b"):
        self.project_id = project_id
        self.model = model
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.session_log = []

    def retrieve(self, question: str, limit: int = 3) -> list:
        """학생 질문에 관련된 교안/경험을 검색한다."""
        # 질문을 FTS 쿼리로 변환
        words = [w for w in question.strip().split() if len(w) > 1]
        if not words:
            return []
        tsquery = " | ".join(words[:5])  # OR 연산으로 넓게 검색

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT title, content, category, source,
                       ts_rank(search_vector, to_tsquery('simple', %s)) AS score
                FROM security_knowledge
                WHERE search_vector @@ to_tsquery('simple', %s)
                ORDER BY score DESC
                LIMIT %s
            """, (tsquery, tsquery, limit))
            results = []
            for row in cur.fetchall():
                results.append({
                    "title": row[0], "content": row[1],
                    "category": row[2], "source": row[3],
                    "score": float(row[4]),
                })
        # 검색 결과 수 출력
        print(f"  [검색] {len(results)}건 관련 교안 발견")
        return results

    def generate_answer(self, question: str, context_docs: list) -> str:
        """RAG로 증강된 프롬프트로 답변을 생성한다."""
        # 컨텍스트 구성
        context = ""
        for i, doc in enumerate(context_docs, 1):
            context += f"\n[참고{i}] {doc['title']}:\n{doc['content'][:400]}\n"

        system_prompt = """당신은 보안 교육 AI 튜터입니다.
학생의 질문에 친절하고 정확하게 답변하세요.

규칙:
1. 반드시 제공된 참고 자료를 근거로 답변하세요
2. 참고 자료에 없는 내용은 "교안에 해당 내용이 없습니다"라고 답하세요
3. 실습 명령어를 포함하여 구체적으로 설명하세요
4. 답변 끝에 참조한 자료를 [출처: ...]로 표기하세요
5. 한국어로 답변하세요"""

        user_prompt = f"""참고 자료:
{context}

학생 질문: {question}

위 참고 자료를 바탕으로 답변해주세요."""

        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
                timeout=120,
            )
            answer = resp.json()["message"]["content"]
            return answer
        except Exception as e:
            return f"답변 생성 오류: {e}"

    def record_evidence(self, question: str, answer: str, docs_used: int):
        """질의/응답을 OpsClaw Evidence로 기록한다."""
        try:
            resp = requests.post(
                f"{MANAGER_URL}/projects/{self.project_id}/dispatch",
                headers=HEADERS,
                json={
                    "command": f"echo '질문: {question[:100]}... | 답변길이: {len(answer)}자 | 참조문서: {docs_used}건'",
                    "subagent_url": "http://localhost:8002",
                },
            )
            # Evidence 기록 결과 출력
            print(f"  [기록] Evidence 저장 완료")
        except Exception as e:
            print(f"  [기록] Evidence 저장 실패: {e}")

    def ask(self, question: str) -> dict:
        """학생 질문에 RAG 기반으로 답변한다."""
        print(f"\n[질문] {question}")

        # 1. Retrieve
        docs = self.retrieve(question)

        # 2. Generate
        print("  [생성] LLM 답변 생성 중...")
        answer = self.generate_answer(question, docs)
        print(f"  [완료] {len(answer)}자 답변 생성")

        # 3. Record
        self.record_evidence(question, answer, len(docs))

        # 세션 로그 저장
        entry = {
            "question": question,
            "answer": answer,
            "docs_used": [d["title"] for d in docs],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        self.session_log.append(entry)

        return entry

    def get_session_summary(self) -> dict:
        """세션 요약을 생성한다."""
        return {
            "total_questions": len(self.session_log),
            "total_answer_chars": sum(len(e["answer"]) for e in self.session_log),
            "unique_docs": list(set(
                d for e in self.session_log for d in e["docs_used"]
            )),
        }

    def close(self):
        """리소스를 정리한다."""
        self.conn.close()


if __name__ == "__main__":
    # 프로젝트 C 생성은 아래 Part 3에서 수행
    print("=== 보안 교육 AI 튜터 에이전트 ===")
    print("사용법:")
    print("  tutor = EducationTutor('프로젝트ID')")
    print("  result = tutor.ask('nftables 규칙 작성법 알려줘')")
    print("  print(result['answer'])")
```

### 2.4 튜터 에이전트 테스트

```bash
# 프로젝트 C 생성
export OPSCLAW_API_KEY=opsclaw-api-key-2026

RESP=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"project-C-education-agent","request_text":"보안 교육 AI 튜터 에이전트","master_mode":"external"}')
# 프로젝트 ID 추출
PC_PID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Project C ID: $PC_PID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/${PC_PID}/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 단계 전환
curl -s -X POST "http://localhost:8000/projects/${PC_PID}/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# RAG 검색 테스트 (DB에서 교안 검색)
curl -s -X POST "http://localhost:8000/projects/${PC_PID}/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -t -c \"SELECT title FROM security_knowledge WHERE search_vector @@ to_tsquery('"'"'simple'"'"', '"'"'nftables | firewall'"'"') ORDER BY ts_rank(search_vector, to_tsquery('"'"'simple'"'"', '"'"'nftables | firewall'"'"')) DESC LIMIT 3\"",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# nftables/firewall 관련 교안 검색 결과 확인
```

---

## Part 3: Experience 학습 기록 시스템 (0:55-1:25)

### 3.1 학습 기록 Experience 저장

```python
#!/usr/bin/env python3
"""learning_tracker.py — 학생 학습 기록을 Experience로 관리"""
import json
import time
import requests

MANAGER_URL = "http://localhost:8000"
API_KEY = "opsclaw-api-key-2026"
HEADERS = {"Content-Type": "application/json", "X-API-Key": API_KEY}

class LearningTracker:
    """학생의 학습 활동을 OpsClaw Evidence와 Experience로 기록한다."""

    def __init__(self, project_id: str, student_id: str):
        self.project_id = project_id
        self.student_id = student_id
        self.records = []

    def record_question(self, question: str, answer: str,
                        category: str, quality: str = "good"):
        """질의/응답을 기록한다."""
        record = {
            "student_id": self.student_id,
            "type": "qa",
            "question": question,
            "answer_length": len(answer),
            "category": category,
            "quality": quality,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        self.records.append(record)

        # OpsClaw dispatch로 Evidence 기록
        evidence_text = json.dumps({
            "student": self.student_id,
            "q": question[:80],
            "category": category,
            "quality": quality,
        }, ensure_ascii=False)

        try:
            resp = requests.post(
                f"{MANAGER_URL}/projects/{self.project_id}/dispatch",
                headers=HEADERS,
                json={
                    "command": f"echo '{evidence_text}'",
                    "subagent_url": "http://localhost:8002",
                },
            )
            # 기록 결과 출력
            print(f"[TRACK] {self.student_id}: {category} — {quality}")
        except Exception as e:
            print(f"[TRACK] 기록 실패: {e}")

    def get_progress(self) -> dict:
        """학생의 학습 진행 상황을 분석한다."""
        if not self.records:
            return {"student_id": self.student_id, "total": 0}

        # 카테고리별 통계
        categories = {}
        for r in self.records:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"count": 0, "good": 0}
            categories[cat]["count"] += 1
            if r["quality"] == "good":
                categories[cat]["good"] += 1

        return {
            "student_id": self.student_id,
            "total_questions": len(self.records),
            "categories": categories,
            "first_question": self.records[0]["timestamp"],
            "last_question": self.records[-1]["timestamp"],
        }

    def generate_report(self) -> str:
        """학습 리포트를 생성한다."""
        progress = self.get_progress()
        report = f"""
=== 학습 진행 리포트 ===
학생: {progress['student_id']}
총 질문: {progress['total_questions']}건

카테고리별 통계:"""
        for cat, stats in progress.get("categories", {}).items():
            # 각 카테고리의 통계 출력
            rate = stats["good"] / stats["count"] * 100 if stats["count"] > 0 else 0
            report += f"\n  {cat}: {stats['count']}건 (이해도: {rate:.0f}%)"

        return report


if __name__ == "__main__":
    # 사용 예시
    print("LearningTracker — OpsClaw 프로젝트 ID로 초기화")
    print("사용법:")
    print("  tracker = LearningTracker('프로젝트ID', 'student-001')")
    print("  tracker.record_question('nftables란?', '답변...', 'firewall', 'good')")
    print("  print(tracker.generate_report())")
```

### 3.2 학습 기록 활용 시나리오

```bash
# 학생의 질문 패턴을 분석하여 약점 영역 파악
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 여러 질문을 dispatch로 기록
curl -s -X POST "http://localhost:8000/projects/${PC_PID}/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo {\"student\":\"s001\",\"q\":\"nftables 규칙 작성법\",\"category\":\"firewall\"}",
        "risk_level": "low"
      },
      {
        "order": 2,
        "instruction_prompt": "echo {\"student\":\"s001\",\"q\":\"Wazuh 경보 분석법\",\"category\":\"siem\"}",
        "risk_level": "low"
      },
      {
        "order": 3,
        "instruction_prompt": "echo {\"student\":\"s001\",\"q\":\"SQL Injection 방어법\",\"category\":\"web-security\"}",
        "risk_level": "low"
      },
      {
        "order": 4,
        "instruction_prompt": "echo {\"student\":\"s002\",\"q\":\"Suricata 규칙 작성\",\"category\":\"ips\"}",
        "risk_level": "low"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 4건의 학습 기록을 Evidence로 저장
```

---

## Part 4: 3개 프로젝트 통합 시연 준비 (1:35-2:05)

### 4.1 프로젝트별 completion-report 작성

```bash
# 프로젝트 A — 자율 인시던트 대응 에이전트 completion-report
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 프로젝트 A 완료 보고서 (PA_PID는 실제 ID로 교체)
curl -s -X POST "http://localhost:8000/projects/${PA_PID}/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "Wazuh 경보 자동 수신 → LLM 분석 → nftables 차단 → Slack 알림 → Evidence 기록 파이프라인 완성",
    "outcome": "success",
    "work_details": [
      "Wazuh API 연동으로 경보 자동 수집 구현",
      "LLM(llama3.1:8b) 기반 위협 분석 엔진 구축",
      "risk_level에 따른 자동/수동 차단 분기 구현",
      "Slack Bot 알림 연동 완료",
      "전체 파이프라인 10건 이상 자동 처리 테스트 완료"
    ]
  }' | python3 -m json.tool 2>/dev/null || echo "PA_PID 설정 필요"
```

```bash
# 프로젝트 B — CTF 자동 풀이 에이전트 completion-report
export OPSCLAW_API_KEY=opsclaw-api-key-2026

curl -s -X POST "http://localhost:8000/projects/${PB_PID}/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "JuiceShop 취약점 자동 스캔 + LLM 공격 전략 수립 + 익스플로잇 자동화 Red Agent 완성",
    "outcome": "success",
    "work_details": [
      "14개 엔드포인트 자동 스캔 완료",
      "LLM(gemma3:12b) 기반 공격 전략 수립 엔진 구축",
      "SQL Injection 및 사용자 열거 익스플로잇 성공",
      "가드레일(대상 제한, 파괴적 공격 금지) 준수 확인",
      "모든 행위를 Evidence로 전수 기록"
    ]
  }' | python3 -m json.tool 2>/dev/null || echo "PB_PID 설정 필요"
```

```bash
# 프로젝트 C — 보안 교육 에이전트 completion-report
export OPSCLAW_API_KEY=opsclaw-api-key-2026

curl -s -X POST "http://localhost:8000/projects/${PC_PID}/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "보안 교안 RAG 기반 AI 튜터 에이전트 구축 + Experience 학습 기록 시스템 완성",
    "outcome": "success",
    "work_details": [
      "PostgreSQL FTS 기반 교안 인덱싱 완료",
      "RAG 파이프라인(Retrieve→Augment→Generate) 구현",
      "LLM(llama3.1:8b) 기반 질의응답 엔진 구축",
      "학습 기록을 OpsClaw Experience로 자동 저장",
      "학생별 학습 진행 리포트 생성 기능 구현"
    ]
  }' | python3 -m json.tool 2>/dev/null || echo "PC_PID 설정 필요"
```

### 4.2 통합 현황 조회

```bash
# 3개 프로젝트의 evidence와 PoW 종합 현황
export OPSCLAW_API_KEY=opsclaw-api-key-2026

echo "=== PoW 리더보드 (전체 에이전트) ==="
# 에이전트별 작업량 순위
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/leaderboard" | python3 -m json.tool

echo ""
echo "=== 체인 무결성 검증 ==="
# 각 에이전트의 PoW 체인 무결성 확인
for AGENT in "http://localhost:8002" "http://10.20.30.1:8002" "http://10.20.30.80:8002" "http://10.20.30.100:8002"; do
  # 에이전트별 체인 검증
  RESULT=$(curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
    "http://localhost:8000/pow/verify?agent_id=${AGENT}" 2>/dev/null)
  VALID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('valid','?'))" 2>/dev/null || echo "?")
  echo "  ${AGENT}: valid=${VALID}"
done
```

### 4.3 시연 준비 체크리스트

```bash
# 시연 전 환경 점검
export OPSCLAW_API_KEY=opsclaw-api-key-2026

echo "=== 시연 환경 점검 ==="

# 1. Manager API 상태
echo -n "Manager API: "
curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects 2>/dev/null || echo "FAIL"

# 2. Ollama LLM 상태
echo -n "Ollama LLM: "
curl -s -o /dev/null -w "%{http_code}" http://192.168.0.105:11434/api/tags 2>/dev/null || echo "FAIL"

# 3. SubAgent 상태 확인
for AGENT_URL in "http://localhost:8002" "http://10.20.30.1:8002" "http://10.20.30.80:8002" "http://10.20.30.100:8002"; do
  # 각 SubAgent 헬스 체크
  echo -n "SubAgent ${AGENT_URL}: "
  curl -s -o /dev/null -w "%{http_code}" "${AGENT_URL}/health" 2>/dev/null || echo "FAIL"
done

# 4. PostgreSQL FTS 확인
echo -n "PostgreSQL FTS: "
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -t -c \
  "SELECT COUNT(*) FROM security_knowledge" 2>/dev/null || echo "FAIL"

# 5. JuiceShop 상태
echo -n "JuiceShop: "
curl -s -o /dev/null -w "%{http_code}" http://10.20.30.80:3000/ 2>/dev/null || echo "FAIL"
```

---

## Part 5: 최종 발표 (2:05-2:40)

### 5.1 발표 형식

각 팀 10분 (발표 7분 + Q&A 3분):

| 시간 | 내용 |
|------|------|
| 0-1분 | 팀 소개 + 프로젝트 개요 |
| 1-3분 | 프로젝트 A: 자율 인시던트 대응 시연 |
| 3-5분 | 프로젝트 B: CTF 자동 풀이 시연 |
| 5-7분 | 프로젝트 C: 교육 에이전트 시연 |
| 7-10분 | Q&A |

### 5.2 발표 평가 기준

| 항목 | 배점 | 세부 기준 |
|------|------|----------|
| 시스템 완성도 | 30% | 3개 프로젝트 모두 동작하는지 |
| Evidence 품질 | 25% | OpsClaw evidence 수와 상세도 |
| 기술적 깊이 | 20% | LLM 활용, RAG 구현, 안전장치 |
| 발표력 | 15% | 설명 명확성, 시연 원활성 |
| Q&A 대응 | 10% | 질문에 대한 답변 품질 |

### 5.3 시연 시나리오 예시

```
시나리오: "SSH 브루트포스 공격 발생 → 자율 대응"

1. [프로젝트 A] Wazuh에서 SSH 브루트포스 경보 수신
   → LLM이 분석하여 "threat, severity=high" 판정
   → nftables로 소스 IP 자동 차단
   → Slack으로 알림 전송
   → Evidence에 전 과정 기록

2. [프로젝트 B] 동시에 Red Agent가 JuiceShop 점검
   → LLM이 공격 전략 수립 (SQLi, 사용자 열거)
   → OpsClaw가 전략 실행
   → 발견된 취약점 Evidence로 기록

3. [프로젝트 C] 학생이 "SSH 브루트포스 대응법" 질문
   → RAG가 교안과 인시던트 경험에서 관련 내용 검색
   → LLM이 실습 명령까지 포함한 답변 생성
   → 학습 기록 Evidence 저장

4. [통합] PoW 리더보드로 3개 프로젝트의 에이전트 활동 종합
```

---

## Part 6: 과정 종합 정리 + 수료 (2:40-3:00)

### 6.1 15주 커리큘럼 회고

| 주차 | 주제 | 핵심 기술 |
|------|------|----------|
| 01-04 | 기초 | LLM, 프롬프트 엔지니어링, OpsClaw 기초 |
| 05-08 | 심화 | SubAgent, PoW, RL, Tool/Skill |
| 09 | 에이전트 보안 | OWASP LLM Top 10, Injection 방어 |
| 10 | 멀티에이전트 | 오케스트레이션, Red/Blue 동시 운영 |
| 11 | RAG | FTS 검색, Experience 승급 |
| 12 | 평가 | F1 Score, A/B 테스트, RL 수렴 |
| 13-15 | 프로젝트 | 인시던트 대응 + CTF 풀이 + 교육 에이전트 |

### 6.2 핵심 역량 정리

```
[AI 보안 에이전트 핵심 역량]

  LLM 활용              보안 분석            시스템 운영
  -----------           -----------         -----------
  Prompting             위협 탐지            OpsClaw
  RAG                   인시던트             nftables
  RL                    취약점              Wazuh
  에이전트 설계          평가                안전/가드레일
  아키텍처              F1/MTTR             Approval Gate
  오케스트/LangGraph     A/B 테스트/PoW 비교
```

### 6.3 프로젝트 과제 (최종)

**최종 제출물**:

1. 3개 프로젝트의 OpsClaw 프로젝트 ID
2. 각 프로젝트의 completion-report (API 응답 스크린샷)
3. 전체 evidence summary (3개 프로젝트 합산)
4. 발표 슬라이드 (PDF, 10페이지 이내)
5. 팀 회고 보고서 (자유 형식, 1페이지)

**평가 총합**:

| 항목 | 배점 |
|------|------|
| 프로젝트 A (인시던트 대응) | 35% |
| 프로젝트 B (CTF 풀이) | 35% |
| 프로젝트 C (교육 에이전트) | 30% |
| PoW 리더보드 보너스 | +5% |
| 전체 Evidence 수 보너스 | +5% |

### 6.4 수료 기준

| 기준 | 최소 요구 |
|------|----------|
| 출석 | 12/15주 이상 |
| 프로젝트 | 3개 모두 제출 |
| Evidence | 총 30건 이상 |
| 발표 | 팀 발표 참여 |

### 6.5 다음 단계 학습 권장

| 분야 | 추천 학습 |
|------|----------|
| LLM 심화 | 파인튜닝, RLHF, LoRA |
| 보안 자동화 | SOAR, CALDERA, Atomic Red Team |
| AI 안전 | AI Safety, Alignment, Red Teaming |
| 인프라 | Kubernetes, 서비스 메시, GitOps |
| 연구 | 보안 에이전트 논문, MITRE ATT&CK |
