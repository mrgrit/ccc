# Week 01: 보안관제(SOC) 개론

## 학습 목표
- 보안관제센터(SOC)의 개념과 필요성을 이해한다
- SOC 분석가의 역할 분류(L1/L2/L3)와 업무 범위를 설명할 수 있다
- SOC 운영 워크플로우(모니터링 → 탐지 → 분석 → 대응 → 보고)를 이해한다
- 주요 SOC 성과 지표(MTTD, MTTR)의 의미를 파악한다
- Wazuh 대시보드에 접속하여 기본 알림 구조를 이해할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

---

## 용어 해설 (보안관제/SOC 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOC** | Security Operations Center | 보안 관제 센터 (24/7 모니터링) | 경찰 112 상황실 |
| **관제** | Monitoring/Surveillance | 보안 이벤트를 실시간 감시하는 활동 | CCTV 관제 |
| **경보** | Alert | 보안 이벤트가 탐지 규칙에 매칭되어 발생한 알림 | 화재 경보기 울림 |
| **이벤트** | Event | 시스템에서 발생한 모든 활동 기록 | 일어난 일 하나하나 |
| **인시던트** | Incident | 보안 정책을 위반한 이벤트 (실제 위협) | 실제 화재 발생 |
| **오탐** | False Positive | 정상 활동을 공격으로 잘못 탐지 | 화재 경보기가 요리 연기에 울림 |
| **미탐** | False Negative | 실제 공격을 놓침 | 도둑이 CCTV에 안 잡힘 |
| **TTD** | Time to Detect | 공격 발생~탐지까지 걸리는 시간 | 화재 발생~경보 울림 시간 |
| **TTR** | Time to Respond | 탐지~대응까지 걸리는 시간 | 경보~소방차 도착 시간 |
| **SIGMA** | SIGMA | SIEM 벤더에 무관한 범용 탐지 룰 포맷 | 국제 표준 수배서 양식 |
| **Tier 1/2/3** | SOC Tiers | 관제 인력 수준 (L1:모니터링, L2:분석, L3:전문가) | 일반의→전문의→교수 |
| **트리아지** | Triage | 경보를 우선순위별로 분류하는 작업 | 응급실 환자 분류 |
| **플레이북** | Playbook (IR) | 인시던트 유형별 대응 절차 매뉴얼 | 화재 대응 매뉴얼 |
| **포렌식** | Forensics | 사이버 범죄 수사를 위한 증거 수집·분석 | 범죄 현장 감식 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 도메인, 해시) | 수배범의 지문, 차량번호 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술·기법·절차 | 범인의 범행 수법 |
| **위협 헌팅** | Threat Hunting | 탐지 룰에 걸리지 않는 위협을 능동적으로 찾는 활동 | 잠복 수사 |
| **syslog** | syslog | 시스템 로그를 원격 전송하는 프로토콜 (UDP 514) | 모든 부서 보고서를 본사로 모으는 시스템 |

---

# Week 01: 보안관제(SOC) 개론

## 학습 목표
- 보안관제센터(SOC)의 개념과 필요성을 이해한다
- SOC 분석가의 역할 분류(L1/L2/L3)와 업무 범위를 설명할 수 있다
- SOC 운영 워크플로우(모니터링 → 탐지 → 분석 → 대응 → 보고)를 이해한다
- 주요 SOC 성과 지표(MTTD, MTTR)의 의미를 파악한다
- Wazuh 대시보드에 접속하여 기본 알림 구조를 이해할 수 있다

## 전제 조건
- Course 2 (보안 솔루션 운영) Week 01 수강 완료 또는 동등 수준
- SIEM의 기본 개념 이해 (로그 수집/분석 도구)
- 실습 인프라 SSH 접속 가능
- 웹 브라우저 사용 가능 (Wazuh 대시보드 접속용)

---

## 1. 보안관제센터(SOC)란? (30분)

### 1.1 정의

**SOC (Security Operations Center)**는 조직의 정보 자산을 **24/7 실시간으로 모니터링**하고, 보안 위협을 **탐지, 분석, 대응**하는 전담 조직이다.

### 1.2 비유: 119 소방관제센터

```
119 소방관제센터                 보안관제센터(SOC)

화재 감지기 --> 신고 접수        보안 장비 --> 로그/알림 수집
상황 판단 (진짜 화재?)           이벤트 분석 (진짜 공격?)
소방차 출동                      사고 대응 (차단, 격리)
진화 완료 보고                   사고 종료 보고서 작성
화재 원인 조사                   사후 분석 (포렌식)
재발 방지 대책                   재발 방지 조치
```

### 1.3 SOC가 없다면?

```
공격자: SQL Injection 시도 (월요일 02:00)
  ↓
방화벽: 로그 기록만 함 (아무도 안 봄)
  ↓
IDS: 알림 생성 (아무도 확인 안 함)
  ↓
공격자: 데이터베이스 탈취 성공 (월요일 02:30)
  ↓
...
  ↓
운영팀: 화요일 출근 후 "어? DB가 이상하다" 발견
  ↓
결과: 24시간+ 동안 공격을 인지하지 못함
      → 대규모 데이터 유출
```

### 1.4 SOC가 있다면?

```
공격자: SQL Injection 시도 (월요일 02:00)
  ↓
SIEM: 알림 생성 + SOC 대시보드에 표시
  ↓
SOC L1 분석가: "SQL Injection 알림 확인" (02:01)
  ↓
SOC L1: "패턴 분석 결과 실제 공격" → L2로 에스컬레이션
  ↓
SOC L2 분석가: WAF 규칙 추가 + 공격 IP 차단 (02:15)
  ↓
결과: 15분 내 탐지 및 차단
      → 피해 최소화
```

### 1.5 SOC의 유형

| 유형 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **자체 SOC** | 조직 내부에 직접 구축/운영 | 완전한 통제권, 맞춤형 | 비용 높음, 인력 확보 어려움 |
| **MSSP** | 외부 업체에 관제 위탁 (Managed Security Service Provider) | 비용 효율적, 전문 인력 | 커스터마이징 제한, 대응 속도 |
| **하이브리드** | 내부 SOC + MSSP 연계 | 균형 잡힌 접근 | 협업 복잡성 |
| **가상 SOC** | 물리적 센터 없이 원격 운영 | 유연성, 분산 가능 | 소통 어려움 |

> 우리 실습 환경은 **자체 SOC** 모델로, siem 서버의 Wazuh가 SIEM 역할을 하고, OpsClaw가 관제 자동화를 지원한다.

---

## 2. SOC 인력 구조 (30분)

> **이 실습을 왜 하는가?**
> "보안관제(SOC) 개론" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안관제/SOC 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 SOC 분석가 레벨

SOC에는 보통 3단계의 분석가가 있다. 각 레벨은 경험, 역할, 권한이 다르다.

```
[L3] 위협 헌터 / 시니어 분석가
  (Threat Hunter / Senior Analyst)
  --> 사전 위협 탐색, 포렌식, 도구 개발
  --> 경력 5년+

[L2] 사고 대응 분석가
  (Incident Responder)
  --> 심층 분석, 사고 대응, 에스컬레이션 판단
  --> 경력 2~5년

[L1] 알림 분석가 (가장 많은 인원)
  (Alert Analyst / Triage Analyst)
  --> 알림 확인, 1차 분류, 오탐 필터링
  --> 경력 0~2년
```

### 2.2 각 레벨의 상세 업무

#### L1: 알림 분석가 (Alert Analyst)

| 항목 | 내용 |
|------|------|
| **주요 업무** | SIEM 대시보드 모니터링, 알림 1차 분류 |
| **핵심 역량** | 알림의 진짜/거짓(True/False Positive) 판별 |
| **도구** | SIEM 대시보드, 티켓 시스템, 체크리스트 |
| **판단 기준** | 사전 정의된 분류 매뉴얼(Playbook)에 따라 처리 |
| **에스컬레이션** | 매뉴얼로 처리 불가 시 L2로 전달 |
| **근무 패턴** | 교대 근무 (24/7) |

**L1의 일반적인 업무 흐름**:
```
1. 대시보드에서 새 알림 확인
2. 알림 내용 검토 (규칙, 소스 IP, 목적지, 시간)
3. Playbook에서 해당 알림 유형 찾기
4. 오탐 여부 판단
   → 오탐: 알림 종료 + 사유 기록
   → 진짜: L2로 에스컬레이션 + 초기 분석 결과 첨부
5. 티켓 시스템에 처리 내역 기록
```

#### L2: 사고 대응 분석가 (Incident Responder)

| 항목 | 내용 |
|------|------|
| **주요 업무** | L1이 에스컬레이션한 사건의 심층 분석 및 대응 |
| **핵심 역량** | 공격 기법 분석, 영향 범위 파악, 대응 조치 실행 |
| **도구** | SIEM, 패킷 캡처, 로그 분석, EDR, 포렌식 도구 |
| **판단 기준** | 경험과 전문 지식 기반 분석 |
| **에스컬레이션** | APT, 대규모 사고 시 L3/CISO에게 보고 |

#### L3: 위협 헌터 (Threat Hunter)

| 항목 | 내용 |
|------|------|
| **주요 업무** | 사전 위협 탐색, 탐지 규칙 개발, 디지털 포렌식 |
| **핵심 역량** | 고급 공격 기법 이해, 리버스 엔지니어링, 도구 개발 |
| **도구** | 맞춤형 스크립트, CTI 플랫폼, 고급 분석 도구 |
| **접근 방식** | "아직 탐지되지 않은 공격이 있다"고 가정하고 능동적 탐색 |

### 2.3 SOC의 기타 역할

| 역할 | 설명 |
|------|------|
| **SOC Manager** | SOC 팀 관리, KPI 관리, 경영진 보고 |
| **Detection Engineer** | SIEM 탐지 규칙 개발/최적화 |
| **SOC Architect** | SOC 인프라/도구 설계 및 관리 |
| **CTI Analyst** | 위협 인텔리전스 수집/분석/배포 |

---

## 3. SOC 운영 워크플로우 (30분)

### 3.1 5단계 워크플로우

```
1.모니터링 --> 2.탐지 --> 3.분석 --> 4.대응 --> 5.보고
 (Monitor)   (Detect)  (Analyze)  (Respond)  (Report)
     ^                                          |
     +-------------- 피드백/개선 ---------------+
```

### 3.2 각 단계 상세

#### 1단계: 모니터링 (Monitor)

```
입력: 다양한 소스에서 로그/이벤트 수집
- 네트워크 장비 (방화벽, 라우터, IDS/IPS)
- 서버 (OS 로그, 애플리케이션 로그)
- 엔드포인트 (EDR, 안티바이러스)
- 클라우드 (AWS CloudTrail, Azure AD)
- 이메일 (피싱 탐지)

출력: SIEM 대시보드에 이벤트 표시
```

**핵심**: SIEM이 모든 로그를 한곳에 모아서 **정규화(Normalization)**하고, **상관분석(Correlation)**하여 의미 있는 알림을 생성한다.

#### 2단계: 탐지 (Detect)

```
알림 유형:
True Positive (TP)  : 진짜 공격을 올바르게 탐지    <-- 이것이 목표
False Positive (FP) : 정상인데 공격으로 잘못 판단   <-- 가장 흔함 (오탐)
True Negative (TN)  : 정상을 정상으로 판단          <-- 문제 없음
False Negative (FN) : 공격인데 놓침                <-- 가장 위험
```

> SOC의 가장 큰 과제 중 하나는 **오탐(False Positive) 관리**이다. 하루 수천~수만 건의 알림 중 실제 공격은 극소수이며, 나머지는 오탐이다. L1 분석가의 핵심 역량이 바로 이 판별이다.

#### 3단계: 분석 (Analyze)

```
분석 항목:

1. 공격 유형 식별
   --> MITRE ATT&CK 매핑 (어떤 전술/기법?)

2. 공격자 정보
   --> 소스 IP, 지리 정보, IOC 조회

3. 영향 범위
   --> 어떤 시스템이 영향받았는가?
   --> 데이터 유출이 발생했는가?

4. 타임라인 구성
   --> 공격이 언제 시작되어 어떻게 진행되었는가?
```

#### 4단계: 대응 (Respond)

```
대응 조치 예시:
- 즉시 차단: 공격 IP 방화벽 차단
- 격리: 감염된 호스트 네트워크 분리
- 계정 잠금: 침해된 계정 비활성화
- 패치 적용: 취약점 긴급 패치
- 복구: 백업에서 시스템 복원
- 증거 보전: 포렌식을 위한 로그/이미지 보존
```

#### 5단계: 보고 (Report)

```
보고서 구성:
1. 사고 개요 (Executive Summary)
2. 타임라인 (사고 발생 --> 탐지 --> 대응 --> 종료)
3. 기술 분석 (공격 기법, IOC, 영향 범위)
4. 대응 조치 내역
5. 교훈 (Lessons Learned)
6. 재발 방지 권고안
```

---

## 4. SOC 핵심 지표 (KPI/KRI) (20분)

### 4.1 주요 성과 지표

| 지표 | 정의 | 목표 |
|------|------|------|
| **MTTD** (Mean Time To Detect) | 공격 발생부터 탐지까지 평균 시간 | **최소화** |
| **MTTR** (Mean Time To Respond) | 탐지부터 대응 완료까지 평균 시간 | **최소화** |
| **MTTC** (Mean Time To Contain) | 탐지부터 확산 차단까지 평균 시간 | **최소화** |
| **FPR** (False Positive Rate) | 전체 알림 중 오탐 비율 | **최소화** |

### 4.2 MTTD와 MTTR의 중요성

```
공격 시작 ---MTTD---> 탐지 ---MTTR---> 대응 완료

  (이 구간이 길수록        (이 구간이 길수록
   피해 증가)               피해 증가)

이상적: MTTD < 1시간, MTTR < 4시간
현실: 평균 MTTD = 197일 (IBM 2025 보고서)
```

> **충격적인 사실**: 데이터 유출 사고의 평균 탐지 시간은 약 **197일**이다. 즉, 공격자가 6개월 이상 시스템에 잠복하는 경우가 흔하다. SOC의 존재 이유가 바로 이 MTTD를 줄이는 것이다.

### 4.3 업계 벤치마크

| 지표 | 하위권 | 평균 | 상위권 |
|------|--------|------|--------|
| MTTD | 수개월 | 수일~수주 | 수분~수시간 |
| MTTR | 수주 | 수일 | 수시간 |
| FPR | 80%+ | 50~70% | 30% 미만 |

---

## 5. SOC 핵심 도구 (20분)

### 5.1 도구 분류

| 도구 유형 | 역할 | 실습 환경 |
|----------|------|----------|
| **SIEM** | 로그 수집, 상관분석, 알림 | Wazuh (siem:443) |
| **SOAR** | 대응 자동화, Playbook 실행 | OpsClaw (opsclaw:8000) |
| **EDR** | 엔드포인트 탐지/대응 | Wazuh Agent |
| **CTI** | 위협 인텔리전스 | OpenCTI (siem:9400) |
| **Ticketing** | 사고 관리/추적 | OpsClaw 프로젝트 |
| **Forensics** | 디지털 증거 분석 | (별도 도구) |

### 5.2 SIEM의 핵심 기능 (Wazuh)

```
secu (Agent)    --+
web (Agent)     --+--> Wazuh Manager --> Wazuh Indexer
opsclaw (Agent) --+    (로그 수집/분석)   (로그 저장/검색)
                            |
                            v
                       Wazuh Dashboard
                       (시각화/알림 관리)
```

### 5.3 SOAR (Security Orchestration, Automation and Response)

**SOAR**는 보안 대응을 **자동화**하는 플랫폼이다.

```
예: SQL Injection 알림이 발생하면 자동으로:
1. SIEM에서 알림 수신
2. 소스 IP 자동 조회 (CTI)
3. 위험도가 높으면 방화벽에 자동 차단 규칙 추가
4. 관련 로그 자동 수집
5. 담당자에게 알림 발송
6. 티켓 자동 생성

→ L1 분석가가 수동으로 해야 할 작업을 자동화!
```

> 우리 실습 환경에서 **OpsClaw**가 SOAR 역할을 수행한다.

---

## 6. 실습 1: Wazuh 대시보드 접속 (20분)

### 6.1 Wazuh 서비스 상태 확인

먼저 siem 서버에서 Wazuh 서비스가 정상 동작하는지 확인하자.

> **실습 목적**: SOC 관제의 핵심 도구인 Wazuh SIEM이 정상 동작하는지 확인하는 것은, 관제 업무 시작 전 반드시 수행하는 점검이다.
>
> **배우는 것**: systemctl로 보안 서비스 상태를 확인하는 방법과, Wazuh의 구성 요소(manager, dashboard)를 이해한다.
>
> **결과 해석**: `Active: active (running)`이면 정상이다. `inactive`나 `failed`면 서비스 장애로, 이 동안 로그 수집과 경보가 중단되어 보안 사각지대가 발생한다.
>
> **실전 활용**: SOC L1 분석가의 첫 업무는 SIEM 서비스 정상 여부를 확인하는 것이다. 서비스 장애 시 즉시 에스컬레이션해야 한다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo systemctl status wazuh-manager --no-pager | head -10"
```

**예상 출력**:
```
● wazuh-manager.service - Wazuh manager
     Loaded: loaded (...)
     Active: active (running) since ...
```

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo systemctl status wazuh-dashboard --no-pager | head -10"
```

### 6.2 대시보드 접근 확인

```bash
# 대시보드 포트 열림 확인
curl -sk -o /dev/null -w "Wazuh Dashboard: HTTP %{http_code}\n" https://10.20.30.100:443/
```

**예상 출력**:
```
Wazuh Dashboard: HTTP 200 (또는 302)
```

### 6.3 웹 브라우저로 접속

1. 브라우저에서 `https://10.20.30.100:443` 접속
2. "연결이 비공개가 아닙니다" 경고 → **고급** → **안전하지 않음 (계속)** 클릭
3. 로그인 화면에서:
   - Username: `admin`
   - Password: (관리자가 안내하는 비밀번호)
4. 로그인 후 메인 대시보드 확인

### 6.4 대시보드 주요 화면

로그인 후 다음 화면들을 탐색한다:

```
Wazuh Dashboard 주요 메뉴:
+-- Modules
|   +-- Security Events       # 보안 이벤트 전체 조회
|   +-- Integrity Monitoring  # 파일 무결성 감시
|   +-- Vulnerabilities       # 취약점 스캔 결과
|   +-- MITRE ATT&CK         # ATT&CK 매핑 뷰
|
+-- Management
|   +-- Rules                 # 탐지 규칙 관리
|   +-- Decoders              # 로그 파서 관리
|   +-- Groups                # 에이전트 그룹 관리
|
+-- Agents                    # 연결된 에이전트 목록
```

---

## 7. 실습 2: Wazuh 에이전트 상태 확인 (15분)

### 7.1 에이전트 목록 조회

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo /var/ossec/bin/agent_control -l 2>/dev/null || sudo /var/ossec/bin/manage_agents -l 2>/dev/null"
```

**예상 출력**:
```
Available agents:
   ID: 001, Name: secu, IP: 10.20.30.1, Active
   ID: 002, Name: web, IP: 10.20.30.80, Active
   ID: 003, Name: opsclaw, IP: 10.20.30.201, Active
```

### 7.2 에이전트 상세 정보 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 에이전트 001 (secu) 상세 정보
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo /var/ossec/bin/agent_control -i 001 2>/dev/null"
```

### 7.3 에이전트 연결 아키텍처 이해

```
secu (10.20.30.1)      --> Wazuh Agent --> TCP 1514 --> Wazuh Manager (siem)
web (10.20.30.80)      --> Wazuh Agent --> TCP 1514 --> Wazuh Manager (siem)
opsclaw (10.20.30.201) --> Wazuh Agent --> TCP 1514 --> Wazuh Manager (siem)

각 Agent가 수집하는 정보:
- 시스템 로그 (syslog, auth.log)
- 파일 무결성 변경 사항
- 프로세스 목록 변화
- 네트워크 연결 상태
- 보안 설정 변경
```

---

## 8. 실습 3: Wazuh 알림 확인 및 구조 이해 (30분)

### 8.1 최근 알림 확인 (명령줄)

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo tail -5 /var/ossec/logs/alerts/alerts.json" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -50
```

### 8.2 알림(Alert) 구조 분석

Wazuh 알림의 JSON 구조를 이해해보자:

```json
{
  "timestamp": "2026-03-27T10:15:30.123+0900",
  "rule": {
    "level": 5,
    "description": "sshd: Authentication failed",
    "id": "5710",
    "mitre": {
      "id": ["T1110"],
      "tactic": ["Credential Access"],
      "technique": ["Brute Force"]
    },
    "groups": ["syslog", "sshd", "authentication_failed"],
    "gdpr": ["IV_35.7.d", "IV_32.2"],
    "pci_dss": ["10.2.4", "10.2.5"]
  },
  "agent": {
    "id": "003",
    "name": "opsclaw",
    "ip": "10.20.30.201"
  },
  "data": {
    "srcip": "192.168.1.100",
    "srcport": "54321",
    "dstuser": "admin"
  },
  "location": "/var/log/auth.log",
  "full_log": "Mar 27 10:15:30 opsclaw sshd[12345]: Failed password for admin from 192.168.1.100 port 54321 ssh2"
}
```

### 8.3 알림 필드 설명

| 필드 | 설명 | SOC 분석 시 활용 |
|------|------|----------------|
| `timestamp` | 이벤트 발생 시간 | 타임라인 구성 |
| `rule.level` | 위험도 (0~15) | 우선순위 판단 |
| `rule.id` | 탐지 규칙 번호 | 규칙 세부 내용 확인 |
| `rule.description` | 규칙 설명 | 이벤트 유형 파악 |
| `rule.mitre` | MITRE ATT&CK 매핑 | 공격 전술/기법 분류 |
| `agent.name` | 이벤트 발생 서버 | 영향 받은 시스템 식별 |
| `data.srcip` | 공격자(추정) IP | IOC 조회, 차단 판단 |
| `full_log` | 원본 로그 | 상세 분석 |

### 8.4 Wazuh 규칙 레벨 체계

| 레벨 | 의미 | SOC 대응 |
|------|------|---------|
| 0~3 | 정보성 이벤트 | 일반적으로 무시 |
| 4~7 | 주의 필요 이벤트 | L1 확인 필요 |
| 8~11 | 중요 이벤트 | L1 분석 + 필요 시 L2 에스컬레이션 |
| 12~15 | 긴급 이벤트 | 즉시 L2/L3 대응 + 관리자 통보 |

### 8.5 레벨별 알림 분포 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
levels = {}
for line in sys.stdin:                                 # 반복문 시작
    try:
        alert = json.loads(line.strip())
        level = alert.get('rule', {}).get('level', 0)
        levels[level] = levels.get(level, 0) + 1
    except:
        pass
for level in sorted(levels.keys()):                    # 반복문 시작
    print(f'Level {level:2d}: {levels[level]:5d}건')
\" 2>/dev/null" || echo "알림 데이터가 아직 충분하지 않을 수 있습니다"
```

---

## 9. 실습 4: MITRE ATT&CK 매핑 이해 (20분)

### 9.1 MITRE ATT&CK이란?

**MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge)**는 실제 사이버 공격에서 관찰된 전술(Tactics)과 기법(Techniques)을 체계적으로 분류한 지식 기반이다.

### 9.2 ATT&CK 매트릭스 구조

```
전술(Tactics) = "무엇을 하려는가?" (목적)
기법(Techniques) = "어떻게 하는가?" (방법)

전술 흐름:
초기 접근 → 실행 → 지속성 → 권한상승 → 방어회피 →
인증정보접근 → 탐색 → 횡이동 → 수집 → 유출 → 영향
```

| 전술 (Tactic) | 설명 | Wazuh 탐지 예시 |
|---------------|------|----------------|
| Initial Access (TA0001) | 초기 침투 | SSH 무차별 대입 |
| Execution (TA0002) | 악성 코드 실행 | 의심스러운 프로세스 생성 |
| Persistence (TA0003) | 지속적 접근 유지 | crontab 변경, 서비스 등록 |
| Privilege Escalation (TA0004) | 권한 상승 | sudo 사용, SUID 파일 실행 |
| Defense Evasion (TA0005) | 탐지 회피 | 로그 삭제, 타임스탬프 변조 |
| Credential Access (TA0006) | 인증 정보 획득 | 비밀번호 파일 접근, 무차별 대입 |
| Lateral Movement (TA0008) | 내부 횡이동 | SSH를 이용한 다른 서버 접근 |
| Exfiltration (TA0010) | 데이터 유출 | 대량 데이터 외부 전송 |

### 9.3 Wazuh에서 MITRE 매핑 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
# MITRE ATT&CK ID가 포함된 알림 조회
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
mitre_count = {}
for line in sys.stdin:                                 # 반복문 시작
    try:
        alert = json.loads(line.strip())
        mitre = alert.get('rule', {}).get('mitre', {})
        for technique_id in mitre.get('id', []):       # 반복문 시작
            tactic = mitre.get('tactic', ['Unknown'])[0] if mitre.get('tactic') else 'Unknown'
            key = f'{technique_id} ({tactic})'
            mitre_count[key] = mitre_count.get(key, 0) + 1
    except:
        pass
for key in sorted(mitre_count.keys(), key=lambda x: mitre_count[x], reverse=True)[:10]:  # 반복문 시작
    print(f'{key}: {mitre_count[key]}건')
\" 2>/dev/null" || echo "MITRE 매핑 데이터를 확인할 수 없습니다"
```

### 9.4 MITRE 정보의 SOC 활용

SOC 분석가는 MITRE ATT&CK을 다음과 같이 활용한다:

```
1. 알림 분류: "이 알림은 T1110 (Brute Force)에 해당한다"
2. 공격 단계 파악: "초기 접근 단계이므로 아직 침투 성공 전이다"
3. 다음 행동 예측: "무차별 대입 성공 시 T1078 (유효 계정)으로 진행할 것"
4. 방어 조치: "계정 잠금 정책 강화, 2FA 적용 필요"
```

---

## 10. 실습 5: SOC 분석가 체험 — 알림 트리아지 (20분)

### 10.1 SSH 실패 알림 생성 및 관찰

의도적으로 SSH 로그인 실패를 발생시켜 Wazuh 알림을 관찰해보자.

**1단계: 로그인 실패 발생시키기** (opsclaw 서버에서)

```bash
# 잘못된 비밀번호로 secu에 SSH 시도 (의도적 실패)
sshpass -p wrongpassword ssh -o StrictHostKeyChecking=no secu@10.20.30.1 "echo test" 2>/dev/null  # 비밀번호 자동입력 SSH
sshpass -p wrongpassword ssh -o StrictHostKeyChecking=no secu@10.20.30.1 "echo test" 2>/dev/null  # 비밀번호 자동입력 SSH
sshpass -p wrongpassword ssh -o StrictHostKeyChecking=no secu@10.20.30.1 "echo test" 2>/dev/null  # 비밀번호 자동입력 SSH
echo "3회 로그인 실패 생성 완료"
```

**2단계: 알림 확인** (10~30초 대기 후)

```bash
# 최근 SSH 관련 알림 확인
sleep 15
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo tail -20 /var/ossec/logs/alerts/alerts.json 2>/dev/null" | \
  python3 -c "                                         # Python 코드 실행
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        alert = json.loads(line.strip())
        if 'ssh' in alert.get('rule', {}).get('description', '').lower() or \
           'authentication' in alert.get('rule', {}).get('description', '').lower():
            print(f\"Time: {alert.get('timestamp', 'N/A')}\")
            print(f\"Rule: [{alert['rule']['id']}] {alert['rule']['description']}\")
            print(f\"Level: {alert['rule']['level']}\")
            print(f\"Agent: {alert.get('agent', {}).get('name', 'N/A')}\")
            mitre = alert.get('rule', {}).get('mitre', {})
            if mitre:
                print(f\"MITRE: {mitre.get('id', [])} - {mitre.get('technique', [])}\")
            print('---')
    except:
        pass
" 2>/dev/null
```

**3단계: L1 분석가처럼 판단하기**

다음 질문에 답해보자:
1. 이 알림의 rule level은 몇인가? 어느 정도의 위험인가?
2. 소스 IP는 어디인가? 내부인가 외부인가?
3. MITRE ATT&CK 어떤 전술/기법에 매핑되는가?
4. 오탐(False Positive)일 가능성은? 아니면 실제 공격 시도인가?
5. 에스컬레이션이 필요한가?

### 10.2 알림 트리아지 연습

다음 가상 알림들을 보고 L1 분석가로서 판단해보자:

**알림 A**:
```
Rule: [5710] sshd: Authentication failed
Level: 5
Source IP: 10.20.30.201 (opsclaw)
Target: secu
Count: 3회
```

**판단**: ( ) 오탐 / ( ) 정탐 / ( ) 추가 분석 필요
**사유**: _______________

**알림 B**:
```
Rule: [5712] sshd: brute force detected (10+ failures)
Level: 10
Source IP: 203.0.113.50 (외부 IP)
Target: web
Count: 50회/5분
```

**판단**: ( ) 오탐 / ( ) 정탐 / ( ) 추가 분석 필요
**사유**: _______________

**알림 C**:
```
Rule: [550] Integrity checksum changed
Level: 7
File: /etc/passwd
Agent: secu
```

**판단**: ( ) 오탐 / ( ) 정탐 / ( ) 추가 분석 필요
**사유**: _______________

---

## 과제

### 과제 1: SOC 일일 보고서 작성 (개인)
Wazuh 대시보드에서 오늘의 알림을 조회하고 다음 양식으로 일일 보고서를 작성하라:

```
[SOC 일일 보고서]

일자: 2026-03-27
작성자: (학번/이름)

1. 알림 현황 요약
   - 전체 알림 수: ___건
   - 레벨별 분포: Level 0-3: ___건, Level 4-7: ___건, Level 8+: ___건
   - 에이전트별 분포: secu: ___건, web: ___건, opsclaw: ___건

2. 주요 알림 Top 5
   (rule_id, description, level, 발생 횟수)

3. MITRE ATT&CK 매핑
   (발견된 전술/기법 목록)

4. 소견
   (특이사항, 에스컬레이션 필요 건, 개선 제안)
```

### 과제 2: SOC 역할 조사 (개인)
L1/L2/L3 분석가 중 하나를 선택하여 다음을 조사하라:
- 필요한 자격증 (예: CompTIA Security+, GCIH 등)
- 필요한 기술 스킬 3가지
- 일반적인 하루 업무 일정
- 해당 역할의 연봉 범위 (한국 기준)

### 과제 3: 알림 트리아지 실습 (조별)
실습 10.2의 알림 A/B/C에 대해 조별로 토론하고 다음을 결정하라:
- 각 알림의 True Positive / False Positive 판단 및 근거
- True Positive인 경우의 대응 절차
- MTTD/MTTR을 줄이기 위한 개선 방안

---

## 검증 체크리스트

- [ ] SOC의 정의와 필요성을 설명할 수 있다
- [ ] L1/L2/L3 분석가의 역할 차이를 설명할 수 있다
- [ ] SOC 워크플로우 5단계를 순서대로 나열할 수 있다
- [ ] MTTD, MTTR의 의미와 중요성을 설명할 수 있다
- [ ] Wazuh Manager 서비스 상태 확인 완료
- [ ] Wazuh Dashboard 접속 성공 (또는 curl로 HTTP 응답 확인)
- [ ] Wazuh 에이전트 목록 조회 성공
- [ ] 알림 JSON 구조의 주요 필드(rule.id, level, mitre)를 이해
- [ ] SSH 실패 알림 생성 및 관찰 완료
- [ ] MITRE ATT&CK 매핑의 의미를 이해
- [ ] 알림 트리아지(분류/판단)를 수행할 수 있다

---

## 다음 주 예고

**Week 02: SIEM 심화 — Wazuh 규칙과 로그 분석**

- Wazuh 규칙 구조 (XML 형식) 상세 학습
- 커스텀 탐지 규칙 작성
- 로그 검색 쿼리 (KQL/Lucene) 사용법
- 실습: 특정 공격 패턴을 탐지하는 커스텀 규칙 작성
- 실습: 대시보드에서 알림 필터링 및 조사

> 다음 주에는 Wazuh의 탐지 규칙을 직접 분석하고, 새로운 규칙을 작성합니다. SOC 분석가의 핵심 역량인 로그 분석을 본격적으로 연습합니다!

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** SOC에서 False Positive(오탐)란?
- (a) 공격을 정확히 탐지  (b) **정상 활동을 공격으로 잘못 탐지**  (c) 공격을 놓침  (d) 로그 미수집

**Q2.** SIGMA 룰의 핵심 장점은?
- (a) 특정 SIEM에서만 동작  (b) **SIEM 벤더에 독립적인 범용 포맷**  (c) 자동 차단 기능  (d) 로그 압축

**Q3.** TTD(Time to Detect)를 줄이기 위한 방법은?
- (a) 경보를 비활성화  (b) **실시간 경보 규칙 최적화 + 자동화**  (c) 분석 인력 감축  (d) 로그 보관 기간 단축

**Q4.** 인시던트 대응 NIST 6단계에서 첫 번째는?
- (a) 탐지(Detection)  (b) **준비(Preparation)**  (c) 격리(Containment)  (d) 근절(Eradication)

**Q5.** Wazuh logtest의 용도는?
- (a) 서버 성능 측정  (b) **탐지 룰을 실제 배포 전에 테스트**  (c) 네트워크 속도 측정  (d) 디스크 점검

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): Wazuh alerts.json/logtest/agent_control, SIGMA 룰, 경보 분석
