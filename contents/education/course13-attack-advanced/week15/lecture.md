# Week 15: 보고서 작성 + 윤리 — 보고서 작성법, 책임 있는 공개

## 학습 목표
- **전문적인 모의해킹 보고서**의 구조와 작성법을 완전히 이해하고 작성할 수 있다
- **CVSS v3.1** 점수를 정확하게 계산하고 위험도를 분류할 수 있다
- 비기술 경영진과 기술팀 **양쪽 모두에게 효과적인** 보고서를 작성할 수 있다
- **책임 있는 공개(Responsible Disclosure)**의 절차와 윤리적 원칙을 설명할 수 있다
- **Bug Bounty** 프로그램의 구조와 참여 방법을 이해한다
- 모의해킹 수행 시 **법적 고려사항**과 윤리적 경계를 명확히 이해한다
- **포트폴리오**와 커리어 발전을 위한 전략을 수립할 수 있다

## 전제 조건
- Week 01~14의 전체 과정을 이수하고 실습을 완료해야 한다
- Week 14의 종합 모의해킹 결과를 보유하고 있어야 한다
- 기술 문서 작성 경험이 있으면 좋다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 보고서 작성 환경 | `ssh opsclaw@10.20.30.201` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 보고서 구조 + CVSS 계산 | 강의 |
| 0:40-1:10 | 보고서 작성 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:50 | 책임 있는 공개 + 법적 고려 | 강의 |
| 1:50-2:30 | 윤리 사례 토론 + Bug Bounty | 토론 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 커리어 가이드 + 최종 퀴즈 | 강의/퀴즈 |
| 3:10-3:30 | 과정 총정리 + Q&A | 토론 |

---

# Part 1: 모의해킹 보고서 작성 (40분)

## 1.1 보고서 구조

```
+------------------------------------------------------------------+
|                  모의해킹 보고서 구조                               |
+------------------------------------------------------------------+
| 1. 표지                   프로젝트명, 기간, 작성자, 기밀등급       |
| 2. Executive Summary      비기술 경영진용 요약 (1-2페이지)         |
| 3. 범위와 방법론          대상, 규칙, 도구, PTES/OSSTMM           |
| 4. 발견사항 요약          위험도별 통계, 트렌드                    |
| 5. 상세 발견사항          각 취약점 상세 (CVSS, 재현, 증거)       |
| 6. 공격 내러티브          시간순 공격 흐름, Kill Chain            |
| 7. 위험 평가              비즈니스 영향 분석                      |
| 8. 권고사항               우선순위별 개선 방안                    |
| 9. 부록                   도구, 명령어, 원시 데이터               |
+------------------------------------------------------------------+
```

### Executive Summary 작성 원칙

| 원칙 | 설명 | 예시 |
|------|------|------|
| **비즈니스 언어** | 기술 용어 최소화 | "SQL Injection" → "웹 로그인 우회" |
| **영향 중심** | 기술 세부보다 영향 | "관리자 권한 획득" → "전체 고객 데이터 노출 위험" |
| **수치 활용** | 정량적 결과 제시 | "7개 취약점 중 2개 Critical" |
| **행동 요구** | 즉시 조치 사항 명시 | "SSH 비밀번호 즉시 변경 권고" |
| **비유 활용** | 이해 가능한 비유 | "현관문에 열쇠 없이 누구나 입장 가능" |

## 1.2 CVSS v3.1 계산

### CVSS 기본 메트릭

| 메트릭 | 옵션 | 설명 |
|--------|------|------|
| **Attack Vector (AV)** | Network / Adjacent / Local / Physical | 공격 접근 경로 |
| **Attack Complexity (AC)** | Low / High | 공격 조건 복잡도 |
| **Privileges Required (PR)** | None / Low / High | 필요 권한 |
| **User Interaction (UI)** | None / Required | 사용자 개입 필요 |
| **Scope (S)** | Unchanged / Changed | 영향 범위 변경 |
| **Confidentiality (C)** | None / Low / High | 기밀성 영향 |
| **Integrity (I)** | None / Low / High | 무결성 영향 |
| **Availability (A)** | None / Low / High | 가용성 영향 |

### 위험도 분류

| 점수 범위 | 등급 | 색상 |
|----------|------|------|
| 9.0-10.0 | **Critical** | 빨강 |
| 7.0-8.9 | **High** | 주황 |
| 4.0-6.9 | **Medium** | 노랑 |
| 0.1-3.9 | **Low** | 초록 |
| 0.0 | **None** | 회색 |

## 실습 1.1: CVSS 점수 계산 실습

> **실습 목적**: Week 14에서 발견한 취약점에 CVSS v3.1 점수를 정확하게 부여한다
>
> **배우는 것**: CVSS 각 메트릭의 의미와 점수 계산 방법, 위험도 분류를 배운다
>
> **결과 해석**: 각 취약점의 CVSS 점수와 등급이 정확하면 평가 성공이다
>
> **실전 활용**: 모의해킹 보고서의 취약점 위험도 평가에 직접 활용한다
>
> **명령어 해설**: Python으로 CVSS 점수를 계산하는 간이 계산기를 사용한다
>
> **트러블슈팅**: CVSS 계산이 복잡하면 FIRST.org 온라인 계산기를 참조한다

```bash
python3 << 'PYEOF'
print("=== CVSS v3.1 점수 계산 실습 ===")
print()

# 실습 환경 취약점 CVSS 평가
vulnerabilities = [
    {
        "id": "VULN-001",
        "name": "SQL Injection (Juice Shop)",
        "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
        "score": 9.1,
        "rating": "Critical",
        "justification": {
            "AV:N": "네트워크를 통해 원격 공격 가능",
            "AC:L": "특별한 조건 없이 항상 재현",
            "PR:N": "인증 없이 공격 가능",
            "UI:N": "사용자 상호작용 불필요",
            "S:U": "웹 앱 범위 내 영향",
            "C:H": "전체 사용자 데이터 노출",
            "I:H": "데이터 변조 가능",
            "A:N": "가용성 영향 없음",
        },
    },
    {
        "id": "VULN-002",
        "name": "약한 SSH 비밀번호",
        "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
        "score": 10.0,
        "rating": "Critical",
        "justification": {
            "AV:N": "SSH는 네트워크에서 접근 가능",
            "AC:L": "단순 비밀번호 입력",
            "PR:N": "사전 인증 불필요",
            "UI:N": "사용자 개입 불필요",
            "S:C": "다른 서버로 측면 이동 (범위 변경)",
            "C:H": "전체 시스템 파일 접근",
            "I:H": "시스템 변조 가능",
            "A:H": "서비스 중단 가능",
        },
    },
    {
        "id": "VULN-003",
        "name": "SubAgent API 무인증",
        "vector": "CVSS:3.1/AV:A/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:L",
        "score": 8.3,
        "rating": "High",
        "justification": {
            "AV:A": "내부 네트워크에서만 접근",
            "AC:L": "직접 API 호출",
            "PR:N": "인증 불필요",
            "UI:N": "사용자 개입 불필요",
            "S:U": "해당 서버 범위 내",
            "C:H": "명령 실행으로 데이터 접근",
            "I:H": "시스템 변조 가능",
            "A:L": "서비스 일시 영향",
        },
    },
]

for v in vulnerabilities:
    print(f"[{v['id']}] {v['name']}")
    print(f"  CVSS Vector: {v['vector']}")
    print(f"  Score: {v['score']} ({v['rating']})")
    print(f"  근거:")
    for metric, reason in v['justification'].items():
        print(f"    {metric}: {reason}")
    print()

print("=== CVSS 계산 참고 ===")
print("  온라인 계산기: https://www.first.org/cvss/calculator/3.1")
print("  AV: Network=0.85, Adjacent=0.62, Local=0.55, Physical=0.20")
print("  AC: Low=0.77, High=0.44")
print("  PR(S:U): None=0.85, Low=0.62, High=0.27")
print("  UI: None=0.85, Required=0.62")
PYEOF
```

## 실습 1.2: 취약점 상세 기술 작성

> **실습 목적**: 단일 취약점에 대한 전문적인 상세 기술을 작성한다
>
> **배우는 것**: 취약점 설명, 재현 단계, 증거, 영향, 권고의 작성 기법을 배운다
>
> **결과 해석**: 제3자가 보고서만으로 취약점을 재현할 수 있으면 작성 성공이다
>
> **실전 활용**: 모의해킹 보고서의 핵심 섹션 작성에 직접 활용한다
>
> **명령어 해설**: 보고서 템플릿의 각 항목을 채워 작성한다
>
> **트러블슈팅**: 기술 수준이 다른 독자를 고려하여 용어 설명을 포함한다

```bash
cat << 'FINDING'
=== 취약점 상세 기술 예시 ===

[VULN-001] SQL Injection — Juice Shop 로그인 API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

위험도: Critical (CVSS 9.1)
CVSS Vector: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N
CWE: CWE-89 (SQL Injection)
OWASP: A03:2021 Injection
MITRE ATT&CK: T1190 (Exploit Public-Facing Application)

설명:
  Juice Shop 로그인 API(/rest/user/login)의 email 파라미터에
  SQL Injection 취약점이 존재합니다. 공격자는 인증 없이 관리자
  계정으로 로그인하여 전체 사용자 데이터에 접근할 수 있습니다.

영향:
  - 전체 사용자 계정 정보(이메일, 역할) 노출
  - 관리자 권한으로 시스템 설정 변경 가능
  - 추가 공격(XSS, SSRF 등)의 발판

재현 단계:
  1. 로그인 API에 조작된 이메일 전송:
     curl -X POST http://10.20.30.80:3000/rest/user/login \
       -H "Content-Type: application/json" \
       -d '{"email":"'"'"' OR 1=1--","password":"a"}'

  2. 응답에서 JWT 토큰 확인:
     {"authentication":{"token":"eyJ...","bid":1,"umail":"admin@juice-sh.op"}}

  3. 토큰으로 관리자 API 접근:
     curl -H "Authorization: Bearer eyJ..." \
       http://10.20.30.80:3000/api/Users/

증거:
  [스크린샷 1] SQL Injection 성공 응답
  [스크린샷 2] 관리자 JWT로 사용자 목록 조회

권고:
  즉시 조치:
    - Juice Shop을 프로덕션 네트워크에서 분리
    - WAF에 SQL Injection 탐지 규칙 추가

  장기 조치:
    - Parameterized Query(준비된 구문) 사용
    - 입력 유효성 검증 (화이트리스트)
    - WAF + IDS 규칙 지속 업데이트
    - 정기적 취약점 스캔 (분기 1회)

참고:
  - OWASP SQL Injection Prevention Cheat Sheet
  - CWE-89: https://cwe.mitre.org/data/definitions/89.html
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINDING
```

---

# Part 2: 책임 있는 공개와 법적 고려 (30분)

## 2.1 책임 있는 공개 (Responsible Disclosure)

### 공개 유형 비교

| 유형 | 절차 | 장점 | 단점 |
|------|------|------|------|
| **Full Disclosure** | 즉시 전체 공개 | 빠른 패치 압박 | 제로데이 악용 위험 |
| **Responsible Disclosure** | 벤더에 먼저 알림 → 기간 후 공개 | 패치 시간 확보 | 벤더 무반응 시 지연 |
| **Coordinated Disclosure** | CERT/CC 등 조정 기관 경유 | 중립적 조정 | 시간 소요 |
| **Non-Disclosure** | 공개하지 않음 | - | 사용자 보호 불가 |

### 책임 있는 공개 절차

```
1. 취약점 발견
   ↓
2. 벤더에 비공개 보고
   (security@vendor.com, HackerOne 등)
   ↓
3. 벤더 확인 (7일 이내)
   ↓
4. 수정 기간 (보통 90일)
   ↓
5. 패치 배포 + CVE 발급
   ↓
6. 공개 (기술 상세 + 타임라인)
```

### 주요 공개 타임라인

| 기관/기업 | 공개 기한 | 특이사항 |
|----------|----------|---------|
| Google Project Zero | 90일 | 연장 14일 (활발한 소통 시) |
| Microsoft | 90일 | MSRC 조정 |
| CERT/CC | 45일 | 정부 기관 |
| ZDI (Zero Day Initiative) | 120일 | 보상 프로그램 포함 |

## 2.2 법적 고려사항

### 한국 관련 법률

| 법률 | 관련 조항 | 내용 |
|------|----------|------|
| **정보통신망법** | 제48조 | 정보통신망 침입 금지 (3년 이하 징역) |
| **정보통신망법** | 제49조 | 비밀 침해 금지 (5년 이하 징역) |
| **정보통신망법** | 제71조 | 벌칙 (타인 정보 훼손, 변경 등) |
| **형법** | 제316조 | 비밀침해 |
| **형법** | 제366조 | 재물손괴 (데이터 파괴) |
| **개인정보보호법** | 전체 | 개인정보 수집/처리 제한 |

### 모의해킹 법적 보호 조건

```
모의해킹이 합법인 조건:
  1. 서면 계약 (Statement of Work, SOW)
  2. 범위 명시 (IP, 도메인, 시스템 목록)
  3. 허용 기법 명시 (DoS 제외 등)
  4. 기간 명시 (시작~종료)
  5. 비상 연락처
  6. 면책 조항 (Authorization Letter)

"Get Out of Jail Free Card" — 항상 서면 허가증을 소지해야 함
```

## 실습 2.1: 윤리적 판단 사례 토론

> **실습 목적**: 모의해킹과 취약점 공개에서 발생하는 윤리적 딜레마를 토론한다
>
> **배우는 것**: 실제 상황에서의 윤리적 판단 기준과 법적 고려사항을 배운다
>
> **결과 해석**: 각 시나리오에 대해 근거 있는 윤리적 판단을 내릴 수 있으면 성공이다
>
> **실전 활용**: 실무에서 윤리적 딜레마에 직면했을 때 올바른 판단을 내리는 데 활용한다
>
> **명령어 해설**: 해당 없음 (토론 활동)
>
> **트러블슈팅**: 정답이 없는 문제도 있으므로 다양한 관점을 수용한다

```bash
cat << 'ETHICS'
=== 윤리적 판단 사례 토론 ===

[사례 1] 범위 외 발견
  모의해킹 중 범위 외 시스템에서 Critical 취약점 발견.
  고객의 다른 서비스가 즉각 위험에 노출됨.
  → 보고해야 하는가? 어떻게?

[사례 2] 벤더 무반응
  오픈소스 라이브러리에서 RCE 취약점 발견.
  90일 전에 보고했지만 벤더가 응답 없음.
  해당 라이브러리는 10만+ 프로젝트에서 사용 중.
  → Full Disclosure 해야 하는가?

[사례 3] 내부 고발
  회사의 보안 시스템에서 고객 데이터 유출 가능 취약점 발견.
  경영진이 수정 비용을 이유로 수정을 거부.
  → 외부에 알려야 하는가?

[사례 4] Bug Bounty 범위
  Bug Bounty 프로그램에 참여 중 범위 외 서버에서
  SQL Injection 발견. 범위 내 서버 테스트 중 우연히 발견.
  → 보고해야 하는가? 보상을 받을 수 있는가?

[사례 5] 경쟁사 취약점
  경쟁사의 웹사이트에서 고객 데이터가 노출된 것을 발견.
  (Google Dorking으로 우연히 발견)
  → 어떻게 해야 하는가?

판단 기준:
  1. 법률: 해당 국가의 법률에 위반되는가?
  2. 피해: 행동/비행동으로 인한 피해는?
  3. 동의: 대상의 허가가 있었는가?
  4. 비례성: 수단이 목적에 비례하는가?
  5. 투명성: 공개적으로 정당화할 수 있는가?
ETHICS
```

---

# Part 3: Bug Bounty와 커리어 (30분)

## 3.1 Bug Bounty 프로그램

| 플랫폼 | 특징 | 평균 보상 |
|--------|------|----------|
| **HackerOne** | 최대 플랫폼, 다양한 프로그램 | $500~$50,000 |
| **Bugcrowd** | 관리형 프로그램, 트리아지 | $300~$30,000 |
| **Intigriti** | 유럽 중심 | $500~$25,000 |
| **자체 프로그램** | Google, Microsoft, Apple | $500~$1,500,000 |

### Bug Bounty 보고서 작성 팁

```
좋은 보고서:
  제목: IDOR in /api/users/{id} allows accessing other users' PII
  영향: 모든 사용자의 개인정보(이름, 이메일, 전화번호) 노출
  재현:
    1. POST /api/auth/login → token 획득
    2. GET /api/users/2 → 다른 사용자 정보 반환
    3. GET /api/users/3 → 또 다른 사용자 정보
  PoC: curl -H "Authorization: Bearer TOKEN" https://target/api/users/2
  영향: 10만+ 사용자 PII 노출 가능

나쁜 보고서:
  제목: Security bug found
  내용: I found a vulnerability in your website. Please fix.
  → 구체적 정보 없음, 재현 불가, 영향 불명
```

## 3.2 사이버보안 커리어 경로

| 분야 | 역할 | 필요 기술 | 자격증 |
|------|------|----------|--------|
| **Red Team** | 공격 시뮬레이션 | 모의해킹, 0-day | OSCP, OSEP, CRTO |
| **Blue Team** | 방어, 탐지, 대응 | SIEM, EDR, IR | GCIH, CySA+, BTL1 |
| **Purple Team** | 공격+방어 통합 | 양쪽 모두 | OSCP+GCIH |
| **Bug Bounty** | 취약점 발견 | 웹/모바일/API | 자격증보다 실력 |
| **AppSec** | 애플리케이션 보안 | SAST/DAST, SDL | CSSLP, GWEB |
| **Cloud Security** | 클라우드 보안 | AWS/Azure/GCP | AWS SAA, CKS |
| **Malware Analysis** | 악성코드 분석 | 리버싱, 샌드박스 | GREM |
| **Digital Forensics** | 디지털 포렌식 | 메모리/디스크 분석 | GCFE, EnCE |

## 실습 3.1: 과정 총정리

> **실습 목적**: 15주 과정에서 학습한 내용을 체계적으로 정리한다
>
> **배우는 것**: 전체 과정의 연결 관계와 실무 적용 방법을 종합적으로 이해한다
>
> **결과 해석**: MITRE ATT&CK에 전체 기법을 매핑할 수 있으면 과정 완료이다
>
> **실전 활용**: 보안 전문가로서의 체계적 지식 체계 구축에 활용한다
>
> **명령어 해설**: 해당 없음 (정리 활동)
>
> **트러블슈팅**: 부족한 영역은 추가 학습 계획을 수립한다

```bash
cat << 'SUMMARY'
=== 15주 과정 총정리 — MITRE ATT&CK 매핑 ===

Week 01: APT 킬체인         → Cyber Kill Chain 전체 전술
Week 02: OSINT 고급          → Reconnaissance (T1593, T1596)
Week 03: 네트워크 우회       → Defense Evasion (T1205, T1572)
Week 04: 웹 고급 공격        → Initial Access (T1190)
Week 05: 인증 공격 심화      → Credential Access (T1558)
Week 06: 권한 상승 체인      → Privilege Escalation (T1548, T1068)
Week 07: C2 인프라 구축      → Command and Control (T1071, T1572)
Week 08: 측면 이동           → Lateral Movement (T1021, T1550)
Week 09: AD 공격             → Credential Access + Persistence
Week 10: 데이터 유출         → Exfiltration (T1048)
Week 11: 안티포렌식          → Defense Evasion (T1070)
Week 12: 공급망 공격         → Initial Access (T1195)
Week 13: 클라우드 공격       → Cloud (T1078.004, T1530)
Week 14: 종합 모의해킹       → PTES 전체 수행
Week 15: 보고서 + 윤리       → Reporting + Ethics

전체 커버리지:
  12/14 MITRE ATT&CK 전술
  50+ MITRE ATT&CK 기법
  30+ 실전 도구
  20+ 실습 시나리오
SUMMARY
```

## 실습 3.2: Bug Bounty 보고서 작성 실습

> **실습 목적**: 실제 Bug Bounty 플랫폼에 제출할 수 있는 수준의 취약점 보고서를 작성한다
>
> **배우는 것**: HackerOne/Bugcrowd 형식의 보고서 구조, 재현 단계, 영향 평가 작성을 배운다
>
> **결과 해석**: 보고서가 트리아저가 이해하고 재현할 수 있는 수준이면 성공이다
>
> **실전 활용**: Bug Bounty 프로그램 참여와 보상 획득에 직접 활용한다
>
> **명령어 해설**: 해당 없음 (보고서 작성)
>
> **트러블슈팅**: 보상 금액은 영향도와 보고서 품질에 비례한다

```bash
cat << 'BB_REPORT'
=== Bug Bounty 보고서 예시 ===

[HackerOne 형식]

Title: IDOR in /api/users/{id} allows accessing other users' PII

Weakness: Insecure Direct Object Reference (CWE-639)

Severity: High (CVSS 7.5)

Description:
  The /api/users/{id} endpoint does not verify that the
  authenticated user is authorized to access the requested
  user's data. An attacker can enumerate user IDs and access
  any user's personal information including name, email,
  phone number, and address.

Steps to Reproduce:
  1. Login as user A (ID: 5)
     POST /api/auth/login
     {"email":"userA@example.com","password":"***"}
     → Receive JWT token

  2. Request own profile (expected)
     GET /api/users/5
     Authorization: Bearer <token_A>
     → 200 OK (own data)

  3. Request another user's profile (vulnerability)
     GET /api/users/2
     Authorization: Bearer <token_A>
     → 200 OK (user B's data!)

  4. Enumerate all users
     for i in $(seq 1 100); do
       curl -H "Authorization: Bearer <token_A>" \
         https://target.com/api/users/$i
     done

Impact:
  - 100,000+ users' PII (name, email, phone, address) exposed
  - GDPR/CCPA compliance violation
  - Potential identity theft and phishing attacks

Proof of Concept:
  [Screenshot 1] User A's profile (authorized)
  [Screenshot 2] User B's profile (unauthorized access)
  [Screenshot 3] Enumeration script output

Remediation:
  - Implement authorization check: verify request.user.id == {id}
  - Use indirect references (UUIDs instead of sequential IDs)
  - Add rate limiting on user endpoints
  - Log and alert on bulk user data access

BB_REPORT

echo ""
echo "=== 보고서 품질 체크리스트 ==="
echo "  [ ] 명확한 제목 (취약점 유형 + 영향)"
echo "  [ ] 재현 가능한 단계 (curl 명령 포함)"
echo "  [ ] 스크린샷/동영상 증거"
echo "  [ ] 영향 평가 (데이터 규모, 비즈니스)"
echo "  [ ] CVSS 점수"
echo "  [ ] 수정 권고"
echo "  [ ] 예의 바른 어조"
```

## 실습 3.3: 15주 과정 ATT&CK 종합 매핑

> **실습 목적**: 전체 15주 과정에서 학습한 기법을 MITRE ATT&CK에 체계적으로 매핑한다
>
> **배우는 것**: ATT&CK 매트릭스의 전체 구조와 각 주차의 기법 위치를 종합적으로 이해한다
>
> **결과 해석**: 12개 이상의 전술에 50개 이상의 기법이 매핑되면 성공이다
>
> **실전 활용**: 보안 전문가로서 ATT&CK을 기반으로 위협을 분석하고 대응하는 데 활용한다
>
> **명령어 해설**: 해당 없음 (정리 활동)
>
> **트러블슈팅**: 매핑이 불완전하면 각 주차 교안을 다시 참조한다

```bash
cat << 'FULL_MAPPING'
=== 15주 전체 MITRE ATT&CK 매핑 ===

[Reconnaissance] Week 01-02
  T1593 Search Open Websites — OSINT, Google Dorking
  T1593.001 Social Media — LinkedIn, GitHub 정찰
  T1593.002 Search Engines — Google Dorking
  T1593.003 Code Repositories — GitHub 시크릿 검색
  T1595 Active Scanning — nmap, masscan
  T1596 Search Open Technical DB — Shodan, Censys
  T1592 Gather Victim Host Info — 배너 그래빙

[Resource Development] Week 01, 07
  T1587.001 Develop Capabilities: Malware — C2 구현
  T1584 Acquire Infrastructure — C2 인프라
  T1588.005 Exploits — 익스플로잇 수집

[Initial Access] Week 04, 12
  T1190 Exploit Public-Facing Application — SQLi, SSRF
  T1195 Supply Chain Compromise — 종속성 혼동
  T1566 Phishing — 스피어피싱 이론
  T1189 Drive-by Compromise — 워터링홀

[Execution] Week 04, 06
  T1059 Command and Scripting — Python, bash 실행
  T1047 WMI — 원격 명령 실행
  T1204 User Execution — 악성 문서

[Persistence] Week 01, 06
  T1053 Scheduled Task/Job — cron 악용
  T1543 Create/Modify System Process — systemd
  T1547 Boot/Logon Autostart — bashrc, SSH 키
  T1505.003 Web Shell — 웹셸 설치

[Privilege Escalation] Week 06
  T1548.001 SUID/SGID — SUID 바이너리 악용
  T1548.003 Sudo Caching — sudo 규칙 악용
  T1068 Exploitation for Privilege Escalation — 커널 익스플로잇

[Defense Evasion] Week 03, 11
  T1070 Indicator Removal — 로그 삭제
  T1070.003 Clear Command History — 히스토리 클리어
  T1070.006 Timestomp — 타임스탬프 조작
  T1027 Obfuscated Files — 인코딩, 암호화
  T1014 Rootkit — LKM, LD_PRELOAD
  T1572 Protocol Tunneling — SSH, DNS 터널

[Credential Access] Week 05, 09
  T1558.003 Kerberoasting — 서비스 티켓 크래킹
  T1558.004 AS-REP Roasting — 사전 인증 없는 계정
  T1558.001 Golden Ticket — TGT 위조
  T1003 OS Credential Dumping — LSASS, shadow
  T1110 Brute Force — SSH 비밀번호

[Discovery] Week 02, 06, 08
  T1046 Network Service Discovery — 서비스 스캔
  T1082 System Information — uname, OS 정보
  T1083 File and Directory — find, ls

[Lateral Movement] Week 08
  T1021.004 Remote Services: SSH — SSH 접속
  T1550.002 Pass the Hash — NTLM PtH
  T1021.001 RDP — 원격 데스크톱
  T1021.002 SMB — 파일 공유

[Collection] Week 10
  T1005 Data from Local System — 민감 파일
  T1074 Data Staged — 스테이징
  T1560 Archive Collected Data — 압축, 암호화

[Command and Control] Week 07
  T1071.001 Web Protocols — HTTP C2
  T1071.004 DNS — DNS C2
  T1095 Non-Application Layer — ICMP C2
  T1573 Encrypted Channel — 암호화 C2
  T1090 Proxy — 리디렉터

[Exfiltration] Week 10
  T1048.002 Encrypted Non-C2 — HTTPS 유출
  T1048.003 Unencrypted Non-C2 — DNS 유출
  T1041 Exfiltration Over C2 — C2 채널 유출
  T1567 Web Service — 클라우드 유출

[Impact] Week 01
  T1485 Data Destruction — 와이퍼
  T1486 Data Encrypted for Impact — 랜섬웨어

총계: 14 전술, 55+ 기법

FULL_MAPPING
```

## 실습 3.4: 커리어 개발 가이드

> **실습 목적**: 사이버보안 커리어 발전을 위한 구체적인 학습 경로를 설계한다
>
> **배우는 것**: 자격증, 실전 플랫폼, 커뮤니티, 포트폴리오 구축 전략을 배운다
>
> **결과 해석**: 6개월, 1년, 3년의 구체적 목표가 수립되면 성공이다
>
> **실전 활용**: 취업, 이직, 전문성 강화에 직접 활용한다
>
> **명령어 해설**: 해당 없음 (계획 수립)
>
> **트러블슈팅**: 분야별 수요와 급여를 조사하여 현실적 목표를 설정한다

```bash
cat << 'CAREER'
=== 사이버보안 커리어 개발 가이드 ===

[6개월 목표]
  자격증: CompTIA Security+ 또는 eJPT
  실습: TryHackMe 학습 경로 완료 (200+ rooms)
  프로젝트: 개인 홈랩 구축 (AD 환경)
  커뮤니티: 보안 컨퍼런스 1회 참석
  포트폴리오: 블로그 5개 이상 기술 글

[1년 목표]
  자격증: OSCP (Offensive Security Certified Professional)
  실습: HackTheBox 50+ 머신 해결
  Bug Bounty: HackerOne/Bugcrowd 5+ 유효 보고서
  프로젝트: 오픈소스 보안 도구 기여
  네트워킹: 보안 커뮤니티 활동

[3년 목표]
  자격증: OSEP, CRTO 또는 CISSP
  경력: Red Team / Penetration Tester 2+ 년
  발표: 컨퍼런스 발표 1+ 회
  연구: CVE 1+ 건 발견 및 공개
  멘토링: 주니어 보안 전문가 멘토링

[추천 학습 리소스]
  무료:
    - TryHackMe (tryhackme.com)
    - OverTheWire (overthewire.org)
    - PicoCTF (picoctf.org)
    - CyberDefenders (cyberdefenders.org)

  유료:
    - HackTheBox Academy ($)
    - PortSwigger Web Security Academy (무료!)
    - Offensive Security (OSCP, OSEP)
    - SANS Institute (GPEN, GCIH)

  도서:
    - "The Web Application Hacker's Handbook"
    - "Penetration Testing" by Georgia Weidman
    - "Red Team Field Manual" (RTFM)
    - "Blue Team Field Manual" (BTFM)

CAREER
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | 보고서 구조 | 9개 섹션 | 모든 섹션 이해 |
| 2 | CVSS 계산 | 점수 산출 | 3개 취약점 계산 |
| 3 | Executive Summary | 작성 | 비기술 독자 이해 가능 |
| 4 | 취약점 상세 | 템플릿 작성 | 재현 가능한 수준 |
| 5 | Responsible Disclosure | 절차 설명 | 6단계 절차 |
| 6 | 법적 고려 | 법률 나열 | 3개 이상 법률 |
| 7 | SOW 요소 | 목록 | 6개 필수 요소 |
| 8 | Bug Bounty | 보고서 작성 | 구조화된 보고 |
| 9 | ATT&CK 매핑 | 전체 과정 | 12+ 전술 매핑 |
| 10 | 윤리적 판단 | 토론 | 근거 있는 의견 |

---

## 자가 점검 퀴즈

**Q1.** 모의해킹 보고서에서 Executive Summary의 핵심 원칙 3가지는?

<details><summary>정답</summary>
1. 비즈니스 언어 사용 (기술 용어 최소화)
2. 영향 중심 기술 (기술적 세부사항보다 비즈니스 영향)
3. 행동 요구 포함 (즉시 조치해야 할 사항 명시)
</details>

**Q2.** CVSS v3.1에서 Scope: Changed가 의미하는 바는?

<details><summary>정답</summary>
취약점의 영향이 취약한 구성 요소의 범위를 넘어 다른 구성 요소에도 미치는 경우이다. 예: 웹 애플리케이션의 취약점으로 호스트 OS까지 접근 가능하거나, 한 서버의 취약점으로 다른 서버까지 측면 이동이 가능한 경우. Scope Changed는 점수를 크게 높인다.
</details>

**Q3.** Responsible Disclosure에서 일반적인 공개 기한은?

<details><summary>정답</summary>
일반적으로 90일이다. Google Project Zero는 90일(+14일 연장), CERT/CC는 45일, ZDI는 120일을 기한으로 한다. 이 기간 내에 벤더가 패치를 배포해야 하며, 기한이 지나면 연구자가 취약점을 공개할 수 있다.
</details>

**Q4.** 한국에서 모의해킹이 합법이 되기 위한 필수 조건은?

<details><summary>정답</summary>
1. 대상 시스템 소유자/관리자의 서면 허가 (계약서/SOW)
2. 테스트 범위, 기간, 허용 기법이 명시된 문서
3. 비상 연락처와 중단 조건 명시
4. 면책 조항(Authorization Letter) 포함
서면 허가 없는 침투 테스트는 정보통신망법 제48조 위반으로 처벌받을 수 있다.
</details>

**Q5.** Bug Bounty 보고서에서 반드시 포함해야 하는 요소 5가지는?

<details><summary>정답</summary>
1. 취약점 유형과 위치 (URL, 파라미터)
2. 재현 단계 (Step-by-step, 누구나 따라할 수 있게)
3. PoC (Proof of Concept) — curl 명령, 스크린샷
4. 영향 (어떤 데이터/기능에 접근 가능한지)
5. CVSS 점수 또는 위험도 평가
</details>

**Q6.** "범위 외 발견" 딜레마에서 가장 적절한 대응은?

<details><summary>정답</summary>
1. 즉시 테스트를 중단 (범위 외이므로 추가 행위 금지)
2. 고객의 프로젝트 매니저에게 구두/이메일로 알림
3. 보고서에 "범위 외 발견사항"으로 별도 기재
4. 범위 확장에 대한 추가 계약 제안
절대 범위 외 시스템을 추가로 테스트하면 안 된다.
</details>

**Q7.** OSCP와 OSEP 자격증의 차이는?

<details><summary>정답</summary>
OSCP(Offensive Security Certified Professional)는 기초~중급 모의해킹 자격증으로, 네트워크/웹/시스템 공격의 기본을 평가한다. OSEP(Offensive Security Experienced Penetration Tester)는 고급 자격증으로, AV 우회, 매크로 공격, AD 공격, 코드 실행 등 고급 기법을 평가한다. OSCP가 선수 과정이다.
</details>

**Q8.** 취약점 보고서에서 "재현 단계"가 중요한 이유는?

<details><summary>정답</summary>
1. 개발팀이 취약점을 확인하고 수정할 수 있어야 함
2. QA팀이 수정 후 검증할 수 있어야 함
3. 오탐(False Positive)을 배제하기 위한 증거
4. 제3자(감사인)가 독립적으로 검증 가능
재현할 수 없는 취약점은 수정되지 않는다.
</details>

**Q9.** 15주 과정에서 학습한 MITRE ATT&CK 전술을 5개 이상 나열하라.

<details><summary>정답</summary>
1. Reconnaissance (정찰) — Week 01-02
2. Initial Access (초기 접근) — Week 04, 12
3. Execution (실행) — Week 04
4. Privilege Escalation (권한 상승) — Week 06
5. Defense Evasion (방어 회피) — Week 03, 11
6. Credential Access (크레덴셜 접근) — Week 05, 09
7. Lateral Movement (측면 이동) — Week 08
8. Command and Control (C2) — Week 07
9. Exfiltration (유출) — Week 10
10. Collection (수집) — Week 10
</details>

**Q10.** 이 과정을 마친 후 다음 학습 단계로 권장하는 것 3가지는?

<details><summary>정답</summary>
1. OSCP 자격증 취득 (실습 기반 모의해킹 인증)
2. HackTheBox/TryHackMe 플랫폼에서 실전 CTF 문제 풀이
3. Bug Bounty 프로그램 참여 (HackerOne/Bugcrowd에서 실제 취약점 발견)
(추가: 특정 분야 심화 — 웹(BSCP), AD(CRTO), 클라우드(AWS SAA))
</details>

---

## 과제

### 과제 1: 최종 모의해킹 보고서 (개인)
Week 14의 결과를 기반으로 완전한 모의해킹 보고서를 작성하라. Executive Summary, 상세 발견사항(CVSS 포함), 공격 내러티브, 권고사항을 반드시 포함할 것. 최소 5개 취약점을 문서화하라.

### 과제 2: Responsible Disclosure 시나리오 (팀)
가상의 취약점 발견 시나리오를 설정하고, 벤더 보고부터 공개까지의 전체 Responsible Disclosure 과정을 시뮬레이션하라. 보고 이메일, 타임라인, 공개 문서를 포함할 것.

### 과제 3: 커리어 개발 계획 (개인)
6개월, 1년, 3년의 사이버보안 커리어 개발 계획을 수립하라. 목표 분야, 취득할 자격증, 참여할 프로젝트, 학습 리소스를 포함할 것. 이 과정에서 학습한 내용이 어떻게 활용되는지 매핑하라.
