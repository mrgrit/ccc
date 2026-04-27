# Week 08: 중간 실습 — 나만의 보안 에이전트 구축

## 학습 목표
- Week 01~07에서 학습한 내용을 종합하여 보안 에이전트를 구축한다
- Ollama 모델을 선택하고 보안 분석용 프롬프트를 설계한다
- Bastion 프로젝트를 생성하고 execute-plan으로 4대 서버를 자동 점검한다
- 점검 결과를 LLM으로 분석하고 보고서를 작성한다
- Evidence 기반으로 채점 가능한 결과물을 산출한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| bastion | 10.20.30.201 | Control Plane (Bastion) | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh Dashboard:443, OpenCTI:8080) | `ssh ccc@10.20.30.100` |

**Bastion API:** `http://localhost:9100` / Key: `ccc-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:15 | 실습 안내 및 채점 기준 (Part 1) | 강의 |
| 0:15-0:30 | 환경 점검 및 모델 선택 (Part 2) | 실습 |
| 0:30-0:40 | 휴식 | - |
| 0:40-1:20 | 프롬프트 설계 + Playbook 작성 (Part 3) | 실습 |
| 1:20-2:10 | 4대 서버 자동 점검 실행 (Part 4) | 실습 |
| 2:10-2:20 | 휴식 | - |
| 2:20-3:00 | 결과 분석 + 보고서 작성 (Part 5) | 실습 |
| 3:00-3:30 | 결과 발표 + 상호 평가 (Part 6) | 발표 |

---

## 용어 해설 (AI보안에이전트 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **보안 에이전트** | Security Agent | 보안 점검/대응을 자율 수행하는 AI 시스템 | AI 보안 관제사 |
| **Playbook** | Playbook | 사전 정의된 점검/대응 절차 | 작전 교범 |
| **execute-plan** | Execute Plan | 다중 Task 일괄 실행 API | 작전 전체 실행 |
| **Evidence** | Evidence | 작업 수행 증적 | 감사 증거물 |
| **PoW** | Proof of Work | 작업 증명 블록 체인 | 공사 완료 확인서 |
| **completion-report** | Completion Report | 프로젝트 완료 보고서 | 결과 보고서 |
| **risk_level** | Risk Level | 작업 위험 수준 (low~critical) | 작업 위험 등급 |
| **SubAgent** | SubAgent | 원격 명령 실행 에이전트 | 현장 파견 요원 |
| **프롬프트 엔지니어링** | Prompt Engineering | LLM 입력 설계 기술 | AI 업무 지시서 작성 |
| **Few-Shot** | Few-Shot | 예시 기반 응답 유도 | 샘플 제공 후 작업 요청 |
| **Chain-of-Thought** | CoT | 단계별 추론 출력 | 풀이 과정 보여주기 |
| **Tool Calling** | Tool Calling | LLM의 외부 도구 호출 | 전문가에게 전화 |
| **하이브리드** | Hybrid | Client+Server 하네스 결합 | 자율+원격 결합 |
| **MITRE ATT&CK** | MITRE ATT&CK | 사이버 공격 전술/기법 분류 체계 | 공격 카탈로그 |
| **오탐** | False Positive | 정상을 위협으로 오인 | 화재 오보 |
| **SUID** | Set User ID | 실행 시 소유자 권한 획득 비트 | 임시 관리자 권한 |

---

## Part 1: 실습 안내 및 채점 기준 (15분)

### 1.1 실습 개요

이 시간에는 Week 01~07에서 학습한 모든 기술을 종합하여 **나만의 보안 에이전트**를 구축한다.

```
  중간 실습 전체 흐름
  [Step 1] Ollama 모델 선택 + 연결 확인
  ↓
  [Step 2] 보안 분석 프롬프트 설계 (5원칙 적용)
  ↓
  [Step 3] Bastion 프로젝트 생성 + Playbook 작성
  ↓
  [Step 4] execute-plan으로 4대 서버 자동 점검
  ↓
  [Step 5] LLM으로 결과 분석 + 보고서 작성
  ↓
  [Step 6] Evidence 확인 + completion-report 제출
```

### 1.2 채점 기준 (100점)

| 항목 | 배점 | 세부 기준 |
|------|------|----------|
| **모델 선택** | 10점 | Ollama 연결 확인, 모델 선택 근거 제시 |
| **프롬프트 설계** | 20점 | 5원칙 적용 여부: 역할(4), 구조화(4), Few-Shot(4), 제약(4), CoT(4) |
| **Playbook 작성** | 15점 | 4대 서버별 점검 항목, risk_level 적절성 |
| **자동 점검 실행** | 25점 | execute-plan 성공 여부, 4대 서버 도달, PoW 블록 생성 |
| **결과 분석** | 15점 | LLM 분석 품질, MITRE ATT&CK 매핑, 위험 판정 |
| **보고서** | 15점 | completion-report 제출, 내용 완성도 |

### 1.3 제출물

1. `~/lab/week08/my_agent.py` — 에이전트 코드
2. `~/lab/week08/playbook.json` — Playbook 정의
3. `~/lab/week08/prompt.txt` — 프롬프트 설계
4. `~/lab/week08/report.md` — 최종 보고서
5. Bastion에 completion-report가 기록되어야 함

---

## Part 2: 환경 점검 및 모델 선택 (15분) — 실습

### 2.1 전체 환경 점검

> **실습 목적**: 전반기에 학습한 에이전트 기술을 종합하여 실전 수준의 보안 에이전트를 구축하기 위해 수행한다
>
> **배우는 것**: 에이전트 루프, Tool Calling, 메모리, 멀티 에이전트, 가드레일, RAG를 결합한 보안 에이전트 설계 능력을 기른다
>
> **결과 해석**: 에이전트의 보안 분석 정확도, 대응 시간, 안전 위반 발생 여부로 종합 품질을 평가한다
>
> **실전 활용**: SOC 보조 에이전트 개발, 보안 자동화 플랫폼 구축, AI 기반 보안 운영 체계 설계에 활용한다

```bash
# 작업 디렉토리 생성
mkdir -p ~/lab/week08

# 서비스 상태 점검 스크립트
cat > ~/lab/week08/env_check.sh << 'SHEOF'
#!/bin/bash
echo "=== 중간 실습 환경 점검 ==="
echo ""

# 1. Bastion 서비스
echo "[1] Bastion 서비스"
for svc in "Manager:8000" "SubAgent:8002"; do
    NAME=$(echo $svc | cut -d: -f1)
    PORT=$(echo $svc | cut -d: -f2)
    # HTTP 상태 확인
    CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/health 2>/dev/null)
    if [ "$CODE" = "200" ]; then
        echo "  $NAME (:$PORT) — OK"
    else
        echo "  $NAME (:$PORT) — DOWN (HTTP $CODE)"
    fi
done

# 2. PostgreSQL
echo ""
echo "[2] PostgreSQL"
PGPASSWORD=bastion psql -h 127.0.0.1 -U bastion -d bastion -c "SELECT 1" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  PostgreSQL — OK"
else
    echo "  PostgreSQL — DOWN"
fi

# 3. Ollama
echo ""
MODELS=$(curl -s http://10.20.30.200:11434/api/tags 2>/dev/null | \
  python3 -c "import sys,json; [print(f'  - {m[\"name\"]}') for m in json.load(sys.stdin).get('models',[])]" 2>/dev/null)
if [ -n "$MODELS" ]; then
    echo "  Ollama — OK"
    echo "  사용 가능한 모델:"
    echo "$MODELS"
else
    echo "  Ollama — UNREACHABLE"
fi

# 4. 원격 SubAgent
echo ""
echo "[4] 원격 SubAgent"
for host in "secu:192.168.208.150" "web:192.168.208.151" "siem:192.168.208.152"; do
    NAME=$(echo $host | cut -d: -f1)
    IP=$(echo $host | cut -d: -f2)
    # 2초 타임아웃
    CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 http://${IP}:8002/health 2>/dev/null)
    if [ "$CODE" = "200" ]; then
        echo "  $NAME ($IP:8002) — OK"
    else
        echo "  $NAME ($IP:8002) — DOWN/UNREACHABLE"
    fi
done

echo ""
echo "=== 환경 점검 완료 ==="
SHEOF

chmod +x ~/lab/week08/env_check.sh
bash ~/lab/week08/env_check.sh
```

### 2.2 모델 선택

```bash
cat > ~/lab/week08/model_selection.py << 'PYEOF'
"""
Week 08 실습: 모델 선택 테스트
사용 가능한 모델의 보안 분석 능력을 비교한다.
"""
import requests
import json
import time

OLLAMA_URL = "http://10.20.30.200:11434/v1/chat/completions"

# 모델 목록 가져오기
models_resp = requests.get("http://10.20.30.200:11434/api/tags", timeout=10)
available_models = [m["name"] for m in models_resp.json().get("models", [])]

# 테스트할 모델 (사용 가능한 것만)
test_models = []
for candidate in ["llama3.1:8b", "gemma3:12b", "qwen2.5:7b"]:
    if candidate in available_models:
        test_models.append(candidate)
if not test_models and available_models:
    test_models = available_models[:3]

# 보안 분석 테스트 질문
TEST_PROMPT = """다음 Wazuh 경보를 분석하라:
rule.id=5710, level=5, src=203.0.113.55, dst_user=root, count=89, time=03:15

반드시 JSON으로 응답하라:
{"severity":"low|medium|high|critical","is_threat":true|false,"analysis":"분석 내용","actions":["조치"]}"""

results = []
for model in test_models:
    print(f"\n--- 테스트: {model} ---")
    start = time.time()
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": model,
            "messages": [
                {"role": "system", "content": "너는 보안 분석가이다. JSON으로만 응답하라."},
                {"role": "user", "content": TEST_PROMPT}
            ],
            "temperature": 0.1,
        }, timeout=120)
        elapsed = time.time() - start
        content = resp.json()["choices"][0]["message"]["content"]

        # JSON 파싱 시도
        try:
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            parsed = json.loads(content[start_idx:end_idx])
            json_ok = True
        except:
            parsed = {}
            json_ok = False

        result = {
            "model": model,
            "elapsed_sec": round(elapsed, 2),
            "json_parseable": json_ok,
            "severity": parsed.get("severity", "N/A"),
            "response_preview": content[:200]
        }
    except Exception as e:
        result = {"model": model, "error": str(e)}

    results.append(result)
    print(f"  시간: {result.get('elapsed_sec', 'N/A')}초")
    print(f"  JSON 파싱: {result.get('json_parseable', False)}")
    print(f"  심각도: {result.get('severity', 'N/A')}")
    print(f"  응답: {result.get('response_preview', result.get('error', ''))[:150]}")

# 선택 결과 저장
with open("/root/lab/week08/model_comparison.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# 추천
print(f"\n{'='*60}")
print("모델 비교 결과")
print(f"{'='*60}")
best = None
for r in results:
    if r.get("json_parseable") and not r.get("error"):
        if best is None or r["elapsed_sec"] < best["elapsed_sec"]:
            best = r
if best:
    print(f"추천 모델: {best['model']} (응답 {best['elapsed_sec']}초, JSON 파싱 OK)")
else:
    print("JSON 파싱 가능한 모델 없음 — 프롬프트 개선 필요")
PYEOF

# 모델 비교 실행
python3 ~/lab/week08/model_selection.py
```

---

## Part 3: 프롬프트 설계 + Playbook 작성 (40분) — 실습

### 3.1 보안 분석 프롬프트 설계 (5원칙 적용)

Bastion 에이전트의 보안 분석 프롬프트를 5원칙(역할/맥락/형식/제약/예시)에 맞게 설계한다.

```bash
# 보안 분석 프롬프트 설계 (5원칙 적용)
cat > ~/lab/week08/prompt.txt << 'PROMPTEOF'
=== 보안 에이전트 프롬프트 (5원칙 적용) ===

[원칙 1: 역할 부여]
너는 10년 경력의 보안 관제센터(SOC) Tier-2 분석가이다.
4대 서버(bastion, secu, web, siem)의 보안 상태를 점검하고 분석하는 것이 임무이다.
MITRE ATT&CK 프레임워크를 기준으로 위협을 분류한다.

[원칙 2: 구조화 출력]
분석 결과는 반드시 다음 JSON 형식으로 출력하라:
{
  "server": "서버명",
  "overall_status": "정상|주의|경고|위험",
  "score": 0-100,
  "findings": [
    {
      "category": "분류",
      "severity": "low|medium|high|critical",
      "description": "설명",
      "mitre_tactic": "MITRE 전술",
      "recommendation": "권고 사항"
    }
  ],
  "summary": "종합 요약"
}

[원칙 3: Few-Shot 예시]
입력: hostname=bastion, disk_usage=45%, open_ports=6, failed_logins=3
출력: {"server":"bastion","overall_status":"정상","score":90,"findings":[{"category":"디스크","severity":"low","description":"디스크 사용량 45%로 정상","mitre_tactic":"N/A","recommendation":"모니터링 유지"}],"summary":"전반적으로 정상 상태"}

입력: hostname=web, disk_usage=92%, open_ports=15, failed_logins=234
출력: {"server":"web","overall_status":"위험","score":35,"findings":[{"category":"디스크","severity":"high","description":"디스크 92% 사용 — 서비스 장애 임박","mitre_tactic":"Impact (TA0040)","recommendation":"즉시 디스크 정리 필요"},{"category":"인증","severity":"critical","description":"234회 로그인 실패 — 브루트포스 공격 의심","mitre_tactic":"Credential Access (TA0006)","recommendation":"공격 IP 즉시 차단"}],"summary":"디스크 부족 + 브루트포스 공격 의심으로 위험 상태"}

[원칙 4: 제약 조건]
- 파괴적 명령(rm -rf, DROP, shutdown)을 생성하지 마라
- IP 차단 시 /32 CIDR만 사용하라
- 내부 IP(10.x, 172.16-31.x, 192.168.x)는 차단 대상에서 제외하라
- 확신도 60% 미만이면 "추가 조사 필요"로 판정하라

[원칙 5: Chain-of-Thought]
분석 시 다음 순서를 따르라:
STEP 1 — 기본 상태 확인: 디스크, 메모리, CPU 부하
STEP 2 — 네트워크 점검: 열린 포트, 불필요 서비스
STEP 3 — 인증/접근: 로그인 실패, SUID 파일, 권한 설정
STEP 4 — 방화벽/보안: 방화벽 규칙, 보안 에이전트 상태
STEP 5 — 종합 판정: 점수 산출, 우선순위 정렬
PROMPTEOF

echo "프롬프트 설계 완료: ~/lab/week08/prompt.txt"
wc -l ~/lab/week08/prompt.txt
```

### 3.2 4대 서버 점검 Playbook 작성

```bash
cat > ~/lab/week08/playbook.json << 'JSONEOF'
{
  "name": "week08-full-security-audit",
  "description": "4대 서버 종합 보안 점검 Playbook",
  "servers": {
    "bastion": {
      "subagent_url": "http://localhost:8002",
      "checks": [
        {"order": 1, "command": "hostname && uptime", "risk": "low", "purpose": "서버 식별"},
        {"order": 2, "command": "df -h / /tmp /var /home 2>/dev/null", "risk": "low", "purpose": "디스크 사용량"},
        {"order": 3, "command": "free -m && cat /proc/loadavg", "risk": "low", "purpose": "메모리/CPU 부하"},
        {"order": 4, "command": "ss -tlnp", "risk": "low", "purpose": "열린 포트"},
        {"order": 5, "command": "grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo 0", "risk": "medium", "purpose": "로그인 실패 횟수"},
        {"order": 6, "command": "last -10", "risk": "low", "purpose": "최근 로그인 기록"},
        {"order": 7, "command": "find / -perm -4000 -type f 2>/dev/null | wc -l", "risk": "medium", "purpose": "SUID 파일 수"}
      ]
    },
    "secu": {
      "subagent_url": "http://192.168.208.150:8002",
      "checks": [
        {"order": 1, "command": "hostname && uptime", "risk": "low", "purpose": "서버 식별"},
        {"order": 2, "command": "df -h / 2>/dev/null", "risk": "low", "purpose": "디스크 사용량"},
        {"order": 3, "command": "nft list ruleset 2>/dev/null | wc -l", "risk": "low", "purpose": "방화벽 규칙 수"},
        {"order": 4, "command": "systemctl is-active suricata 2>/dev/null || echo inactive", "risk": "low", "purpose": "Suricata 상태"},
        {"order": 5, "command": "ss -tlnp", "risk": "low", "purpose": "열린 포트"},
        {"order": 6, "command": "grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo 0", "risk": "medium", "purpose": "로그인 실패 횟수"}
      ]
    },
    "web": {
      "subagent_url": "http://192.168.208.151:8002",
      "checks": [
        {"order": 1, "command": "hostname && uptime", "risk": "low", "purpose": "서버 식별"},
        {"order": 2, "command": "df -h / 2>/dev/null", "risk": "low", "purpose": "디스크 사용량"},
        {"order": 3, "command": "ss -tlnp", "risk": "low", "purpose": "열린 포트"},
        {"order": 4, "command": "systemctl is-active apache2 2>/dev/null || systemctl is-active nginx 2>/dev/null || echo inactive", "risk": "low", "purpose": "웹서버 상태"},
        {"order": 5, "command": "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo 'unreachable'", "risk": "low", "purpose": "JuiceShop 접근성"},
        {"order": 6, "command": "grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo 0", "risk": "medium", "purpose": "로그인 실패 횟수"}
      ]
    },
    "siem": {
      "subagent_url": "http://192.168.208.152:8002",
      "checks": [
        {"order": 1, "command": "hostname && uptime", "risk": "low", "purpose": "서버 식별"},
        {"order": 2, "command": "df -h / 2>/dev/null", "risk": "low", "purpose": "디스크 사용량"},
        {"order": 3, "command": "systemctl is-active wazuh-manager 2>/dev/null || echo inactive", "risk": "low", "purpose": "Wazuh 상태"},
        {"order": 4, "command": "ss -tlnp", "risk": "low", "purpose": "열린 포트"},
        {"order": 5, "command": "free -m", "risk": "low", "purpose": "메모리 사용량"},
        {"order": 6, "command": "grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo 0", "risk": "medium", "purpose": "로그인 실패 횟수"}
      ]
    }
  }
}
JSONEOF

echo "Playbook 작성 완료: ~/lab/week08/playbook.json"
# Playbook 요약
python3 -c "
import json
with open('/root/lab/week08/playbook.json') as f:
    pb = json.load(f)
print(f'Playbook: {pb[\"name\"]}')
for server, config in pb['servers'].items():
    print(f'  {server}: {len(config[\"checks\"])}개 점검 항목')
"
```

---

## Part 4: 4대 서버 자동 점검 실행 (50분) — 실습

### 4.1 종합 보안 에이전트 구현

```bash
cat > ~/lab/week08/my_agent.py << 'PYEOF'
"""
Week 08 중간 실습: 나만의 보안 에이전트
4대 서버를 자동 점검하고 LLM으로 분석하여 보고서를 생성한다.
"""
import requests
import json
import time
import datetime

# ============================================================
# 설정
# ============================================================
OLLAMA_URL = "http://10.20.30.200:11434/v1/chat/completions"
MODEL = "llama3.1:8b"  # 모델 선택 결과에 따라 변경
BASTION = "http://localhost:9100"
API_KEY = "ccc-api-key-2026"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# 프롬프트 로드
with open("/root/lab/week08/prompt.txt") as f:
    SECURITY_PROMPT = f.read()

# Playbook 로드
with open("/root/lab/week08/playbook.json") as f:
    PLAYBOOK = json.load(f)

# ============================================================
# Phase 1: Bastion 프로젝트 생성
# ============================================================
def create_project() -> str:
    """Bastion 프로젝트 생성 및 stage 전환"""
    project = requests.post(f"{BASTION}/projects", headers=HEADERS, json={
        "name": f"week08-security-audit-{datetime.datetime.now().strftime('%H%M%S')}",
        "request_text": "4대 서버 종합 보안 점검",
        "master_mode": "external"
    }).json()
    pid = project["id"]

    # stage 전환: created → planning → executing
    requests.post(f"{BASTION}/projects/{pid}/plan", headers=HEADERS)
    requests.post(f"{BASTION}/projects/{pid}/execute", headers=HEADERS)

    return pid

# ============================================================
# Phase 2: 4대 서버 점검 실행
# ============================================================
def check_server(project_id: str, server_name: str, server_config: dict) -> dict:
    """단일 서버 점검: execute-plan API 사용"""
    subagent_url = server_config["subagent_url"]
    checks = server_config["checks"]

    # execute-plan 태스크 구성
    tasks = [
        {
            "order": check["order"],
            "instruction_prompt": check["command"],
            "risk_level": check["risk"],
            "subagent_url": subagent_url,
        }
        for check in checks
    ]

    try:
        resp = requests.post(
            f"{BASTION}/projects/{project_id}/execute-plan",
            headers=HEADERS,
            json={"tasks": tasks, "subagent_url": subagent_url},
            timeout=60
        )
        result = resp.json()

        # 결과 정리
        task_results = []
        for r in result.get("results", result.get("task_results", [])):
            order = r.get("order", 0)
            output = str(r.get("output", r.get("result", "")))
            # 원본 점검 항목의 purpose 찾기
            purpose = ""
            for check in checks:
                if check["order"] == order:
                    purpose = check["purpose"]
                    break
            task_results.append({
                "order": order,
                "purpose": purpose,
                "output": output[:500],
            })

        return {"server": server_name, "status": "success", "results": task_results}

    except requests.exceptions.RequestException as e:
        return {"server": server_name, "status": "error", "error": str(e)}

def check_all_servers(project_id: str) -> dict:
    """4대 서버 전체 점검"""
    all_results = {}
    for server_name, server_config in PLAYBOOK["servers"].items():
        print(f"  [{server_name}] 점검 중...")
        result = check_server(project_id, server_name, server_config)
        all_results[server_name] = result

        if result["status"] == "success":
            print(f"    성공: {len(result['results'])}개 항목 완료")
        else:
            print(f"    실패: {result.get('error', 'unknown')}")

    return all_results

# ============================================================
# Phase 3: LLM 분석
# ============================================================
def analyze_server(server_name: str, check_results: dict) -> dict:
    """개별 서버 분석"""
    # 점검 결과를 텍스트로 구성
    result_text = f"서버: {server_name}\n점검 결과:\n"
    for r in check_results.get("results", []):
        result_text += f"- {r['purpose']}: {r['output'][:200]}\n"

    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SECURITY_PROMPT},
            {"role": "user", "content": f"다음 서버 점검 결과를 분석하라:\n\n{result_text}"}
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
    }, timeout=180)

    content = resp.json()["choices"][0]["message"]["content"]

    # JSON 파싱 시도
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])
    except (ValueError, json.JSONDecodeError):
        return {
            "server": server_name,
            "overall_status": "분석 오류",
            "score": 0,
            "raw_analysis": content[:500]
        }

def analyze_all(all_results: dict) -> dict:
    """전체 서버 분석"""
    analyses = {}
    for server_name, result in all_results.items():
        if result["status"] == "success":
            print(f"  [{server_name}] LLM 분석 중...")
            analysis = analyze_server(server_name, result)
            analyses[server_name] = analysis
            print(f"    상태: {analysis.get('overall_status', 'N/A')}, 점수: {analysis.get('score', 'N/A')}")
        else:
            analyses[server_name] = {"server": server_name, "overall_status": "접근 불가", "score": 0}
    return analyses

# ============================================================
# Phase 4: 보고서 생성
# ============================================================
def generate_report(project_id: str, all_results: dict, analyses: dict) -> str:
    """종합 보고서 생성"""
    report_lines = [
        f"# 4대 서버 종합 보안 점검 보고서",
        f"",
        f"- 일시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Bastion Project: {project_id}",
        f"- 모델: {MODEL}",
        f"- Playbook: {PLAYBOOK['name']}",
        f"",
        f"## 서버별 점검 결과",
        f"",
        f"| 서버 | 상태 | 점수 | 주요 발견 |",
        f"|------|------|------|---------|",
    ]

    total_score = 0
    server_count = 0
    for server_name, analysis in analyses.items():
        status = analysis.get("overall_status", "N/A")
        score = analysis.get("score", 0)
        findings = analysis.get("findings", [])
        finding_summary = "; ".join([f.get("description", "")[:50] for f in findings[:2]]) if findings else "없음"
        report_lines.append(f"| {server_name} | {status} | {score}/100 | {finding_summary} |")
        total_score += score if isinstance(score, (int, float)) else 0
        server_count += 1

    avg_score = round(total_score / max(server_count, 1))
    report_lines.extend([
        f"",
        f"## 종합 평가",
        f"",
        f"- **종합 점수**: {avg_score}/100",
        f"- **점검 서버**: {server_count}대",
        f"- **성공**: {sum(1 for r in all_results.values() if r['status']=='success')}대",
        f"- **실패**: {sum(1 for r in all_results.values() if r['status']!='success')}대",
        f"",
        f"## 상세 분석",
        f"",
    ])

    for server_name, analysis in analyses.items():
        report_lines.append(f"### {server_name}")
        report_lines.append(f"")
        if "findings" in analysis:
            for f in analysis["findings"]:
                sev = f.get("severity", "N/A")
                desc = f.get("description", "N/A")
                rec = f.get("recommendation", "N/A")
                mitre = f.get("mitre_tactic", "N/A")
                report_lines.append(f"- [{sev}] {desc}")
                report_lines.append(f"  - MITRE: {mitre}")
                report_lines.append(f"  - 권고: {rec}")
        elif "summary" in analysis:
            report_lines.append(f"- {analysis['summary']}")
        elif "raw_analysis" in analysis:
            report_lines.append(f"- {analysis['raw_analysis'][:300]}")
        report_lines.append(f"")

    report = "\n".join(report_lines)
    return report

def submit_report(project_id: str, report: str, analyses: dict):
    """Bastion에 완료 보고서 제출"""
    # 보고서 파일 저장
    with open("/root/lab/week08/report.md", "w") as f:
        f.write(report)

    # 분석 결과 JSON 저장
    with open("/root/lab/week08/analysis_results.json", "w") as f:
        json.dump(analyses, f, indent=2, ensure_ascii=False)

    # Bastion completion-report 제출
    summary_parts = []
    for server, analysis in analyses.items():
        status = analysis.get("overall_status", "N/A")
        score = analysis.get("score", 0)
        summary_parts.append(f"{server}: {status} ({score}점)")

    requests.post(
        f"{BASTION}/projects/{project_id}/completion-report",
        headers=HEADERS,
        json={
            "summary": f"4대 서버 보안 점검 완료: {', '.join(summary_parts)}",
            "outcome": "success",
            "work_details": summary_parts
        }
    )

# ============================================================
# 메인 실행
# ============================================================
def main():
    print("=" * 70)
    print("  Week 08 중간 실습 — 나만의 보안 에이전트")
    print("=" * 70)
    start_time = time.time()

    # Phase 1: 프로젝트 생성
    print("\n[Phase 1] Bastion 프로젝트 생성...")
    project_id = create_project()
    print(f"  Project ID: {project_id}")

    # Phase 2: 4대 서버 점검
    print("\n[Phase 2] 4대 서버 자동 점검...")
    all_results = check_all_servers(project_id)

    # Phase 3: LLM 분석
    print("\n[Phase 3] LLM 분석...")
    analyses = analyze_all(all_results)

    # Phase 4: 보고서 생성
    print("\n[Phase 4] 보고서 생성...")
    report = generate_report(project_id, all_results, analyses)
    submit_report(project_id, report, analyses)

    elapsed = round(time.time() - start_time, 1)
    print(f"\n{'='*70}")
    print(f"  실습 완료!")
    print(f"  소요 시간: {elapsed}초")
    print(f"  Project ID: {project_id}")
    print(f"  보고서: ~/lab/week08/report.md")
    print(f"  분석 결과: ~/lab/week08/analysis_results.json")
    print(f"{'='*70}")

    # Evidence 확인
    print("\n[Evidence 확인]")
    evidence = requests.get(
        f"{BASTION}/projects/{project_id}/evidence/summary",
        headers=HEADERS
    ).json()
    print(json.dumps(evidence, indent=2, ensure_ascii=False)[:500])

    # PoW 검증
    print("\n[PoW 검증]")
    verify = requests.get(
        f"{BASTION}/pow/verify",
        headers=HEADERS,
        params={"agent_id": "http://localhost:8002"}
    ).json()
    print(f"  체인 유효: {verify.get('valid')}, 블록: {verify.get('blocks')}")

if __name__ == "__main__":
    main()
PYEOF

# 에이전트 실행
echo "=== 보안 에이전트 실행 시작 ==="
python3 ~/lab/week08/my_agent.py
```

### 4.2 실행 결과 확인

```bash
# 보고서 확인
echo "=== 보고서 미리보기 ==="
head -40 ~/lab/week08/report.md

# 분석 결과 JSON 확인
echo ""
echo "=== 분석 결과 요약 ==="
python3 -c "
import json
with open('/root/lab/week08/analysis_results.json') as f:
    data = json.load(f)
for server, analysis in data.items():
    status = analysis.get('overall_status', 'N/A')
    score = analysis.get('score', 'N/A')
    findings = len(analysis.get('findings', []))
    print(f'  {server}: {status} (점수: {score}, 발견: {findings}건)')
"
```

---

## Part 5: 결과 분석 + 보고서 완성 (40분) — 실습

### 5.1 종합 분석 보완

```bash
cat > ~/lab/week08/enhance_report.py << 'PYEOF'
"""
Week 08 실습: 보고서 보완
LLM을 사용하여 종합 분석을 추가한다.
"""
import requests
import json

OLLAMA_URL = "http://10.20.30.200:11434/v1/chat/completions"
MODEL = "llama3.1:8b"

# 분석 결과 로드
with open("/root/lab/week08/analysis_results.json") as f:
    analyses = json.load(f)

# 종합 분석 요청
resp = requests.post(OLLAMA_URL, json={
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": """너는 CISO(최고정보보안책임자)이다.
4대 서버의 보안 점검 결과를 종합하여 경영진 보고서를 작성하라.
다음 항목을 포함하라:
1. Executive Summary (3줄 요약)
2. 위험 우선순위 (가장 시급한 조치부터)
3. 서버 간 상관관계 분석
4. 30일 개선 로드맵
한국어로 작성하라."""
        },
        {
            "role": "user",
            "content": f"4대 서버 점검 결과:\n{json.dumps(analyses, indent=2, ensure_ascii=False)[:4000]}"
        }
    ],
    "temperature": 0.2,
    "max_tokens": 2048,
}, timeout=180)

executive_report = resp.json()["choices"][0]["message"]["content"]

# 기존 보고서에 추가
with open("/root/lab/week08/report.md", "a") as f:
    f.write(f"\n\n## 경영진 보고 (CISO Summary)\n\n{executive_report}\n")

print("=" * 60)
print("경영진 보고서 추가 완료")
print("=" * 60)
print(executive_report[:600])
PYEOF

# 보고서 보완 실행
python3 ~/lab/week08/enhance_report.py
```

### 5.2 채점 스크립트

```bash
cat > ~/lab/week08/grading.py << 'PYEOF'
"""
Week 08 실습: 자동 채점 스크립트
제출물의 완성도를 자동 평가한다.
"""
import os
import json

SCORE = 0
MAX_SCORE = 100
results = []

def check(description: str, points: int, condition: bool):
    """채점 항목 확인"""
    global SCORE
    if condition:
        SCORE += points
        results.append(f"  [PASS +{points:2d}] {description}")
    else:
        results.append(f"  [FAIL  0/{points:2d}] {description}")

# 1. 모델 선택 (10점)
check("model_comparison.json 존재",
      5, os.path.exists("/root/lab/week08/model_comparison.json"))
if os.path.exists("/root/lab/week08/model_comparison.json"):
    with open("/root/lab/week08/model_comparison.json") as f:
        mc = json.load(f)
    # 2개 이상 모델 비교
    check("2개 이상 모델 비교", 5, len(mc) >= 2)
else:
    check("2개 이상 모델 비교", 5, False)

# 2. 프롬프트 설계 (20점)
if os.path.exists("/root/lab/week08/prompt.txt"):
    with open("/root/lab/week08/prompt.txt") as f:
        prompt = f.read()
    check("prompt.txt 존재", 4, True)
    check("역할 부여 포함", 4, "역할" in prompt or "분석가" in prompt)
    check("구조화 출력 (JSON) 포함", 4, "JSON" in prompt or "json" in prompt)
    check("Few-Shot 예시 포함", 4, "예시" in prompt or "Few-Shot" in prompt)
    check("제약 조건 포함", 4, "제약" in prompt or "금지" in prompt or "마라" in prompt)
else:
    for item in ["prompt.txt 존재", "역할 부여", "구조화 출력", "Few-Shot", "제약 조건"]:
        check(item, 4, False)

# 3. Playbook (15점)
if os.path.exists("/root/lab/week08/playbook.json"):
    with open("/root/lab/week08/playbook.json") as f:
        pb = json.load(f)
    check("playbook.json 존재", 5, True)
    servers = pb.get("servers", {})
    check("4대 서버 포함", 5, len(servers) >= 4)
    # risk_level 다양성
    all_risks = set()
    for s in servers.values():
        for c in s.get("checks", []):
            all_risks.add(c.get("risk", ""))
    check("risk_level 2종 이상", 5, len(all_risks) >= 2)
else:
    for item in ["playbook.json 존재", "4대 서버", "risk_level"]:
        check(item, 5, False)

# 4. 자동 점검 실행 (25점)
check("my_agent.py 존재", 5, os.path.exists("/root/lab/week08/my_agent.py"))
if os.path.exists("/root/lab/week08/analysis_results.json"):
    with open("/root/lab/week08/analysis_results.json") as f:
        ar = json.load(f)
    check("analysis_results.json 존재", 5, True)
    success_servers = [s for s, r in ar.items() if r.get("overall_status") != "접근 불가"]
    check("1대 이상 서버 점검 성공", 5, len(success_servers) >= 1)
    check("3대 이상 서버 점검 성공", 5, len(success_servers) >= 3)
    check("4대 서버 모두 점검 성공", 5, len(success_servers) >= 4)
else:
    for item in ["analysis_results.json", "1대 성공", "3대 성공", "4대 성공"]:
        check(item, 5, False)

# 5. 결과 분석 (15점)
if os.path.exists("/root/lab/week08/analysis_results.json"):
    # MITRE 매핑 확인
    has_mitre = False
    has_score = False
    for analysis in ar.values():
        for f in analysis.get("findings", []):
            if f.get("mitre_tactic"):
                has_mitre = True
        if analysis.get("score"):
            has_score = True
    check("MITRE ATT&CK 매핑", 5, has_mitre)
    check("점수 산출", 5, has_score)
    check("발견사항 존재", 5, any(analysis.get("findings") for analysis in ar.values()))
else:
    for item in ["MITRE 매핑", "점수 산출", "발견사항"]:
        check(item, 5, False)

# 6. 보고서 (15점)
if os.path.exists("/root/lab/week08/report.md"):
    with open("/root/lab/week08/report.md") as f:
        report = f.read()
    check("report.md 존재", 5, True)
    check("보고서 50줄 이상", 5, report.count("\n") >= 50)
    check("서버별 상세 분석 포함", 5, "###" in report)
else:
    for item in ["report.md 존재", "50줄 이상", "상세 분석"]:
        check(item, 5, False)

# 결과 출력
print("=" * 60)
print("  Week 08 중간 실습 채점 결과")
print("=" * 60)
for r in results:
    print(r)
print(f"\n총점: {SCORE}/{MAX_SCORE}")
grade = "A" if SCORE >= 90 else "B" if SCORE >= 80 else "C" if SCORE >= 70 else "D" if SCORE >= 60 else "F"
print(f"등급: {grade}")
PYEOF

# 채점 실행
python3 ~/lab/week08/grading.py
```

---

## Part 6: 결과 발표 + 상호 평가 (30분)

### 발표 가이드

각 학생은 5분 내외로 다음을 발표한다:

1. **선택한 모델과 이유** (30초)
2. **프롬프트 설계 핵심** — 5원칙 중 가장 효과적이었던 것 (1분)
3. **점검 결과 요약** — 4대 서버 상태 (1분)
4. **주요 발견사항** — 가장 위험한 항목 (1분)
5. **개선 제안** — 에이전트를 더 좋게 만들려면? (1분)

### 상호 평가 기준

| 항목 | 평가 기준 |
|------|----------|
| 완성도 | 4대 서버 모두 점검했는가? |
| 분석 품질 | LLM 분석이 구체적이고 정확한가? |
| 프롬프트 | 5원칙이 잘 적용되었는가? |
| 보고서 | 경영진이 읽을 수 있는 수준인가? |
| 창의성 | 독자적인 점검 항목이나 분석 관점이 있는가? |

### 최종 과제

이번 주차의 최종 과제는 **실습 자체**이다. 채점 스크립트(`grading.py`)를 실행하여 자신의 점수를 확인하라.

**추가 도전 과제 (가산점):**

1. Wazuh API에서 실제 경보를 가져와 LLM으로 분석하라 (+10점)
2. RL 추천을 적용하여 risk_level을 자동 결정하라 (+5점)
3. 점검 결과를 Slack으로 알림 발송하라 (+5점)

**제출물:**
- `~/lab/week08/my_agent.py`
- `~/lab/week08/playbook.json`
- `~/lab/week08/prompt.txt`
- `~/lab/week08/report.md`
- `~/lab/week08/analysis_results.json`
- Bastion completion-report (Project ID 기록)

---

> **다음 학기 예고:** Week 09부터는 자율 보안 에이전트 심화 과정이 시작된다. Purple Team 에이전트(Red+Blue), MITRE ATT&CK 자동 매핑, 분산 지식 아키텍처, 에이전트 간 협업(A2A), 그리고 실제 침투 테스트 시나리오에서의 에이전트 운용을 학습한다.

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### CCC Bastion Agent
> **역할:** CCC 자율 운영 에이전트 — 스킬/플레이북/경험 학습  
> **실행 위치:** `bastion (10.20.30.201)`  
> **접속/호출:** TUI `./dev.sh bastion`, API `http://10.20.30.200:11434`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `packages/bastion/agent.py` | 메인 에이전트 루프 |
| `packages/bastion/skills.py` | 스킬 정의 |
| `packages/bastion/playbooks/` | 정적 플레이북 YAML |
| `data/bastion/experience/` | 수집된 경험 (pass/fail) |

**핵심 설정·키**

- `LLM_BASE_URL / LLM_MODEL` — Ollama 연결
- `CCC_API_KEY` — ccc-api 인증
- `max_retry=2` — 실패 시 self-correction 재시도

**로그·확인 명령**

- ``docs/test-status.md`` — 현재 테스트 진척 요약
- ``bastion_test_progress.json`` — 스텝별 pass/fail 원시

**UI / CLI 요점**

- 대화형 TUI 프롬프트 — 자연어 지시 → 계획 → 실행 → 검증
- `/a2a/mission` (API) — 자율 미션 실행
- Experience→Playbook 승격 — 반복 성공 패턴 저장

> **해석 팁.** 실패 시 output을 분석해 **근본 원인 교정**이 설계의 핵심. 증상 회피/땜빵은 금지.

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (8주차) 학습 주제와 직접 연관된 *실제* incident:

### 스피어 피싱 첨부파일 — HTA + PowerShell downloader

> **출처**: WitFoo Precinct 6 / `incident-2024-08-004` (anchor: `anc-cbdabf2e6c87`) · sanitized
> **시점**: 2024-08-18 (Initial Access)

**관찰**: user@victim.example 이 invoice.hta 첨부 실행 → mshta.exe → cmd → powershell -enc <base64 payload>.

**MITRE ATT&CK**: **T1566.001 (Spearphishing Attachment)**, **T1059.001 (PowerShell)**, **T1218.005 (Mshta)**

**IoC**:
  - `invoice.hta`
  - `mshta.exe → cmd → powershell -enc`

**학습 포인트**:
- HTA 가 IE/MSHTA 통해 신뢰 zone 으로 실행 — 클라이언트 측 첫 발판
- AppLocker 또는 Windows Defender ASR 룰로 mshta.exe child process 차단 가능
- 탐지: Sysmon EID 1 (process create), parent=mshta.exe child=cmd/powershell
- 방어: 이메일 게이트웨이 첨부 sandboxing, .hta 차단, ASR 룰, EDR 프로세스 트리


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.
