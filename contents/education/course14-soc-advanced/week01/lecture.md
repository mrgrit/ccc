# Week 01: SOC 성숙도 모델

## 학습 목표
- SOC-CMM(SOC Capability Maturity Model) 5단계를 이해하고 자체 SOC 수준을 평가할 수 있다
- Tier 1/2/3 분석가의 역할과 책임을 심화 수준에서 설명할 수 있다
- SOC KPI(MTTD, MTTR, 탐지율, 오탐률 등)를 설계하고 측정할 수 있다
- SOC 운영 성숙도 자가진단 체크리스트를 작성할 수 있다
- Wazuh 환경에서 실제 KPI 데이터를 추출하여 성숙도 평가를 수행할 수 있다

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
| 0:00-0:50 | SOC 성숙도 모델 이론 (Part 1) | 강의 |
| 0:50-1:30 | Tier 심화 + KPI 설계 (Part 2) | 강의/토론 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | KPI 측정 실습 (Part 3) | 실습 |
| 2:30-3:10 | 성숙도 자가진단 + OpsClaw 연동 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOC-CMM** | SOC Capability Maturity Model | SOC 역량 성숙도 모델 (5레벨) | 기업 경영품질 인증 등급 |
| **MTTD** | Mean Time to Detect | 평균 탐지 시간 | 화재 발생~경보 울림까지 평균 시간 |
| **MTTR** | Mean Time to Respond | 평균 대응 시간 | 경보~소방차 도착까지 평균 시간 |
| **MTTC** | Mean Time to Contain | 평균 봉쇄 시간 | 화재 확산 차단까지 걸리는 시간 |
| **오탐률** | False Positive Rate | 전체 경보 중 오탐 비율 | 화재 경보 중 요리 연기 비율 |
| **탐지율** | Detection Rate | 실제 위협 중 탐지된 비율 | CCTV가 실제 침입자를 잡은 비율 |
| **Tier 1** | SOC Analyst L1 | 초기 모니터링/트리아지 담당 | 응급실 접수 간호사 |
| **Tier 2** | SOC Analyst L2 | 심화 분석/에스컬레이션 담당 | 전공의 |
| **Tier 3** | SOC Analyst L3 | 위협 헌팅/포렌식 전문가 | 교수급 전문의 |
| **KPI** | Key Performance Indicator | 핵심 성과 지표 | 성적표 |
| **KRI** | Key Risk Indicator | 핵심 위험 지표 | 건강검진 위험 수치 |
| **SLA** | Service Level Agreement | 서비스 수준 합의 | 배달 보장 시간 |
| **NIST CSF** | NIST Cybersecurity Framework | 미국 표준 사이버보안 프레임워크 | 국가 표준 보안 교과서 |
| **CISO** | Chief Information Security Officer | 최고 정보보안 책임자 | 보안 총괄 사령관 |
| **에스컬레이션** | Escalation | 상위 분석가/관리자에게 이관 | 상급자에게 보고 |
| **트리아지** | Triage | 경보 우선순위 분류 | 응급 환자 분류 |
| **플레이북** | Playbook | 인시던트 유형별 대응 절차 | 소방 매뉴얼 |

---

# Part 1: SOC 성숙도 모델 이론 (50분)

## 1.1 SOC 성숙도란?

SOC 성숙도(SOC Maturity)는 보안관제센터가 위협을 탐지하고 대응하는 **역량 수준**을 체계적으로 측정하는 개념이다. 단순히 장비를 도입했다고 성숙한 SOC가 아니다. 인력, 프로세스, 기술, 거버넌스가 유기적으로 작동해야 한다.

### 왜 성숙도를 측정해야 하는가?

```
[현실 시나리오]

A 기업: Wazuh 도입, 분석가 2명, 룰 300개
  → "우리 SOC는 잘 운영되고 있다"
  → 실제: 경보 10,000개/일, 오탐 85%, 분석가 피로 누적
  → MTTD: 4시간, MTTR: 12시간

B 기업: Wazuh 도입, 분석가 2명, 룰 120개
  → "우리 SOC는 아직 부족하다"
  → 실제: 경보 800개/일, 오탐 15%, 자동화 대응 70%
  → MTTD: 8분, MTTR: 25분

→ 장비와 인력 수는 비슷하지만 성숙도는 하늘과 땅 차이
→ 측정하지 않으면 개선할 수 없다
```

## 1.2 SOC-CMM (SOC Capability Maturity Model)

SOC-CMM은 네덜란드의 Rob van Os가 개발한 SOC 역량 성숙도 모델이다. Carnegie Mellon의 CMM/CMMI에서 영감을 받았으며, SOC에 특화된 5가지 도메인과 5단계 성숙도 레벨을 정의한다.

### 5가지 도메인

```
+------------------------------------------------------------------+
|                        SOC-CMM 5 Domains                         |
+------------------------------------------------------------------+
|                                                                  |
|  [Business]     [People]      [Process]    [Technology]  [Services]
|  비즈니스       인력          프로세스      기술          서비스
|  +---------+   +---------+   +---------+  +---------+  +---------+
|  | 거버넌스 |   | 채용    |   | 모니터링|  | SIEM    |  | 탐지    |
|  | 예산    |   | 교육    |   | 분석    |  | EDR     |  | 대응    |
|  | 보고    |   | 역량    |   | 대응    |  | SOAR    |  | 헌팅    |
|  | 규정    |   | 유지    |   | 개선    |  | 자동화  |  | 포렌식  |
|  +---------+   +---------+   +---------+  +---------+  +---------+
|                                                                  |
+------------------------------------------------------------------+
```

### 5단계 성숙도 레벨

| 레벨 | 이름 | 설명 | 특징 |
|------|------|------|------|
| **1** | Initial (초기) | 비공식, 임시적 운영 | 문서화 없음, 개인 역량에 의존 |
| **2** | Managed (관리) | 기본 프로세스 수립 | 플레이북 존재, 역할 정의됨 |
| **3** | Defined (정의) | 표준화된 프로세스 | 메트릭 측정, 교육 체계화 |
| **4** | Quantitatively Managed (정량 관리) | 데이터 기반 의사결정 | KPI/KRI 추적, 지속적 측정 |
| **5** | Optimizing (최적화) | 지속적 개선 문화 | AI/ML 활용, 프로액티브 헌팅 |

### 레벨별 상세 비교

```
Level 1 (Initial)
+--------------------------------------------+
| - "사고 나면 그때 대응하자"                  |
| - 분석가가 경험으로 판단                     |
| - 로그는 쌓이지만 체계적 분석 없음           |
| - 인시던트 기록이 개인 노트에만 존재         |
| - 교대 근무 체계 없음                        |
+--------------------------------------------+

Level 2 (Managed)
+--------------------------------------------+
| - 기본 플레이북 5-10개 존재                  |
| - Tier 1/2 역할 구분                         |
| - SIEM 룰 기본 세트 운용                     |
| - 인시던트 티켓 시스템 사용                  |
| - 월간 보고서 작성                           |
+--------------------------------------------+

Level 3 (Defined)
+--------------------------------------------+
| - 플레이북 30개+ (유형별 세분화)             |
| - Tier 1/2/3 + 헌팅 팀 운영                 |
| - MTTD/MTTR 측정 시작                        |
| - 정기 교육/훈련 프로그램                    |
| - ATT&CK 매핑된 탐지 룰                     |
+--------------------------------------------+

Level 4 (Quantitatively Managed)
+--------------------------------------------+
| - KPI 대시보드 실시간 운영                   |
| - 탐지율/오탐률 정량 추적                    |
| - 위협 인텔리전스 피드 연동                  |
| - SOAR 기반 자동 대응 50%+                   |
| - 분기별 성숙도 자체 평가                    |
+--------------------------------------------+

Level 5 (Optimizing)
+--------------------------------------------+
| - AI/ML 기반 이상 탐지                       |
| - 프로액티브 위협 헌팅 상시 운영             |
| - 자동 대응 80%+, 분석가는 고급 분석 집중   |
| - Purple Team 정기 훈련                      |
| - 업계 벤치마크 대비 상위 10%               |
+--------------------------------------------+
```

## 1.3 다른 성숙도 프레임워크 비교

| 프레임워크 | 개발 기관 | 특징 | SOC 특화 |
|------------|----------|------|----------|
| **SOC-CMM** | Rob van Os | SOC 전용, 5도메인 25영역 | O (최고) |
| **NIST CSF** | NIST | 범용 사이버보안, 5기능 | 부분적 |
| **C2M2** | DoE | 에너지 분야, 사이버보안 역량 | X |
| **CMMI** | CMMI Institute | 소프트웨어 개발 프로세스 | X |
| **CREST SOC** | CREST | 영국 기반, SOC 인증 | O |
| **MITRE ATT&CK** | MITRE | 위협 기법 분류 (성숙도 아님) | 보완적 |

### SOC-CMM vs NIST CSF 매핑

```
SOC-CMM Domain        NIST CSF Function
+-----------+         +----------+
| Business  | ------> | Govern   |
| People    | ------> | (없음)   |  ← NIST CSF에는 인력 도메인이 약함
| Process   | ------> | Detect   |
|           | ------> | Respond  |
| Technology| ------> | Protect  |
| Services  | ------> | Recover  |
+-----------+         +----------+

→ SOC-CMM이 SOC 운영에 더 구체적이고 실용적
```

## 1.4 SOC-CMM 평가 방법론

### 평가 절차

```
Step 1: 범위 정의
  → 평가 대상 SOC 식별
  → 도메인별 담당자 지정

Step 2: 자료 수집
  → 문서 리뷰 (플레이북, 정책, 보고서)
  → 인터뷰 (Tier 1/2/3 분석가, 매니저)
  → 기술 환경 검토 (SIEM, EDR, SOAR)

Step 3: 레벨 판정
  → 도메인별 성숙도 점수 산정
  → 증거 기반 평가 (자기 주장 아닌 실증)

Step 4: 갭 분석
  → 현재 레벨 vs 목표 레벨
  → 도메인별 개선 과제 도출

Step 5: 로드맵 수립
  → 우선순위 기반 개선 계획
  → 3/6/12개월 마일스톤
```

### 자가진단 점수 기준 (도메인별 0-5점)

| 점수 | 기준 |
|------|------|
| 0 | 해당 활동이 전혀 없음 |
| 1 | 비공식적으로 일부 수행 |
| 2 | 기본 프로세스가 문서화됨 |
| 3 | 표준화되어 일관적으로 수행 |
| 4 | 정량적으로 측정/관리 |
| 5 | 지속적 개선, 업계 최고 수준 |

---

# Part 2: Tier 심화 + KPI 설계 (40분)

## 2.1 Tier 1/2/3 역할 심화

### Tier 1: SOC 모니터링 분석가

```
[Tier 1 일일 워크플로우]

09:00  교대 인수인계 (야간 미처리 경보 확인)
        |
09:15  SIEM 대시보드 경보 큐 확인
        |
09:30  경보 트리아지 시작
        |   +-- 심각도 판단 (Critical/High/Medium/Low/Info)
        |   +-- 오탐 판별 (알려진 오탐 패턴 체크)
        |   +-- 티켓 생성 또는 종결
        |
12:00  오전 경보 처리 현황 보고
        |
13:00  오후 경보 트리아지 계속
        |   +-- 반복 패턴 식별
        |   +-- 신규 오탐 룰 제안
        |
16:00  일일 보고서 작성
        |
17:00  교대 인수인계 (미처리 건 전달)
```

**핵심 역량:**
- SIEM 대시보드 운용 능력
- 경보 트리아지 기준 숙지
- 플레이북 기반 초기 대응
- 에스컬레이션 판단력
- 커뮤니케이션 (명확한 인수인계)

**KPI:**
- 경보 처리량 (건/시간)
- 초기 트리아지 시간 (분)
- 에스컬레이션 정확도 (%)
- 오탐 판별 정확도 (%)

### Tier 2: SOC 심화 분석가

```
[Tier 2 업무 범위]

Tier 1 에스컬레이션 접수
        |
        v
+---[심화 분석]---+
|                  |
| - 로그 상관분석  |
| - 패킷 분석     |
| - 악성코드 분석  |
| - IOC 추출      |
| - 영향도 평가    |
+--------+---------+
         |
    +----+----+
    |         |
  [대응]    [보고]
    |         |
  - IP 차단   - 인시던트 보고서
  - 계정 잠금 - 타임라인 작성
  - 격리      - 교훈(Lessons Learned)
```

**핵심 역량:**
- 네트워크 패킷 분석 (Wireshark)
- 로그 상관분석 (SIEM 고급 쿼리)
- 악성코드 기초 분석
- 인시던트 대응 리딩
- 포렌식 증거 보존

**KPI:**
- 심화 분석 완료 시간 (시간)
- 인시던트 봉쇄 시간 (MTTC)
- 근본 원인 분석 성공률 (%)
- IOC 추출 정확도 (%)

### Tier 3: SOC 전문가/헌팅

```
[Tier 3 업무 범위]

+--[프로액티브 활동]--+     +--[리액티브 활동]--+
|                      |     |                    |
| - 위협 헌팅          |     | - 고급 포렌식      |
| - 탐지 룰 개발       |     | - 악성코드 리버싱  |
| - ATT&CK 매핑       |     | - APT 분석         |
| - Purple Team        |     | - 법적 증거 수집   |
| - 인텔리전스 분석    |     | - CISO 보고        |
+----------+-----------+     +---------+----------+
           |                           |
           +----------+----------------+
                      |
              [SOC 역량 향상]
              - Tier 1/2 교육
              - 플레이북 개선
              - 도구 평가/도입
              - 벤더 관리
```

**핵심 역량:**
- 고급 포렌식 (디스크, 메모리, 네트워크)
- 악성코드 리버스 엔지니어링
- 위협 인텔리전스 분석
- SIGMA/YARA 룰 작성
- ATT&CK 프레임워크 전문가
- 보안 아키텍처 이해

**KPI:**
- 헌팅 캠페인 수/성공률
- 신규 탐지 룰 생성 수
- 탐지 격차(Detection Gap) 감소율
- Tier 1/2 교육 시간

## 2.2 SOC KPI 체계 설계

### 핵심 KPI 분류

```
+------------------------------------------------------------------+
|                        SOC KPI Framework                          |
+------------------------------------------------------------------+
|                                                                    |
|  [효율성 KPI]              [효과성 KPI]        [인력 KPI]          |
|  +-----------------+      +----------------+  +----------------+  |
|  | MTTD            |      | 탐지율          |  | 분석가 이직률  |  |
|  | MTTR            |      | 오탐률          |  | 교육 이수율    |  |
|  | MTTC            |      | 미탐률          |  | 인당 경보 처리 |  |
|  | 경보 처리 속도  |      | 인시던트 재발률 |  | 번아웃 지수    |  |
|  | 자동화 비율     |      | 커버리지(ATT&CK)|  | 야간 교대 비율 |  |
|  +-----------------+      +----------------+  +----------------+  |
|                                                                    |
|  [기술 KPI]                [비즈니스 KPI]                         |
|  +-----------------+      +-------------------+                   |
|  | 룰 수/품질      |      | 보안 사고 비용    |                   |
|  | 로그 수집률     |      | SLA 준수율        |                   |
|  | 시스템 가용성   |      | 규정 준수율       |                   |
|  | 자동화 커버리지 |      | 고객 만족도       |                   |
|  +-----------------+      +-------------------+                   |
+------------------------------------------------------------------+
```

### 주요 KPI 상세

| KPI | 산식 | 목표값 (Level 3) | 목표값 (Level 5) |
|-----|------|-------------------|-------------------|
| MTTD | sum(탐지시각-발생시각)/건수 | < 1시간 | < 5분 |
| MTTR | sum(대응완료-탐지시각)/건수 | < 4시간 | < 30분 |
| MTTC | sum(봉쇄완료-탐지시각)/건수 | < 2시간 | < 15분 |
| 오탐률 | 오탐 건수/전체 경보 x 100 | < 30% | < 5% |
| 탐지율 | 탐지 건수/실제 위협 x 100 | > 70% | > 95% |
| 자동화율 | 자동 대응/전체 대응 x 100 | > 30% | > 80% |
| 에스컬레이션 정확도 | 적절한 에스컬/전체 에스컬 | > 80% | > 95% |

### KPI 대시보드 설계 원칙

```
+--[좋은 KPI 대시보드]--+     +--[나쁜 KPI 대시보드]--+
|                        |     |                        |
| - 5-7개 핵심 지표      |     | - 50개+ 지표 나열     |
| - 추세 그래프 포함     |     | - 숫자만 나열          |
| - 목표 대비 현재 표시  |     | - 목표값 없음          |
| - 색상 코드 (Red/Amber |     | - 단색 테이블          |
|   /Green)              |     |                        |
| - 드릴다운 가능        |     | - 상세 확인 불가       |
| - 실시간 업데이트      |     | - 주 1회 수동 갱신     |
+------------------------+     +------------------------+
```

## 2.3 SOC 운영 모델

### 교대 근무 모델

| 모델 | 인원 요구 | 장점 | 단점 |
|------|----------|------|------|
| **24/7 3교대** | 12-15명 | 완전 커버리지 | 비용 높음 |
| **16/8 + 온콜** | 6-8명 | 비용 절감 | 야간 대응 지연 |
| **비즈니스 시간 + SOAR** | 3-5명 | 소규모 가능 | 자동화 의존 |
| **Follow-the-Sun** | 6-9명 (글로벌) | 야간 없음 | 글로벌 팀 필요 |

### 에스컬레이션 매트릭스

```
경보 심각도    Tier 1 처리    에스컬레이션 기준        최종 대응자
+----------+  +----------+  +-------------------+   +-----------+
| Info     |  | 자동 종결 |  | (에스컬 불필요)    |   | 자동화    |
| Low      |  | 30분 내   |  | 패턴 반복 시       |   | Tier 1    |
| Medium   |  | 15분 내   |  | 1시간 미해결 시    |   | Tier 2    |
| High     |  | 5분 내    |  | 즉시 에스컬        |   | Tier 2    |
| Critical |  | 즉시 보고 |  | 즉시 에스컬+보고   |   | Tier 3+관리|
+----------+  +----------+  +-------------------+   +-----------+
```

---

# Part 3: KPI 측정 실습 (50분)

## 3.1 Wazuh에서 경보 데이터 추출

> **실습 목적**: Wazuh API를 사용하여 실제 경보 데이터를 추출하고, SOC KPI를 계산하는 방법을 익힌다.
>
> **배우는 것**: Wazuh REST API 활용, JSON 데이터 파싱, KPI 산출 방법
>
> **실전 활용**: 실제 SOC에서 SIEM 데이터를 기반으로 주간/월간 KPI 보고서를 작성할 때 활용

```bash
# siem 서버 접속
sshpass -p1 ssh siem@10.20.30.100

# Wazuh API 토큰 발급
TOKEN=$(curl -s -u wazuh-wui:MyS3cr37P450r.*- \
  -k https://localhost:55000/security/user/authenticate \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

echo "Token: ${TOKEN:0:20}..."

# 최근 24시간 경보 요약 조회
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://localhost:55000/alerts?limit=500&pretty=true" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = data.get('data', {}).get('total_affected_items', 0)
print(f'총 경보 수: {total}')
"
```

> **결과 해석**: `total_affected_items` 값이 최근 경보 총 건수다. 이 수치가 일 기준 1,000건 이상이면 Tier 1 분석가의 업무 부하가 높은 상태로 판단한다.
>
> **명령어 해설**:
> - `curl -u`: HTTP Basic 인증으로 Wazuh API에 접근
> - `-k`: 자체 서명 인증서 무시 (실습 환경용)
> - `python3 -c`: 인라인 Python으로 JSON 파싱
>
> **트러블슈팅**:
> - "401 Unauthorized" → Wazuh 기본 계정/비밀번호 확인
> - "Connection refused" → Wazuh API 서비스 상태 확인: `systemctl status wazuh-manager`

## 3.2 경보 심각도별 분류

```bash
# 심각도별 경보 분포 확인
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://localhost:55000/alerts?limit=1000&pretty=true" \
  | python3 -c "
import sys, json
from collections import Counter

data = json.load(sys.stdin)
items = data.get('data', {}).get('affected_items', [])

severity_count = Counter()
for item in items:
    level = item.get('rule', {}).get('level', 0)
    if level <= 3:
        severity_count['Info'] += 1
    elif level <= 6:
        severity_count['Low'] += 1
    elif level <= 9:
        severity_count['Medium'] += 1
    elif level <= 12:
        severity_count['High'] += 1
    else:
        severity_count['Critical'] += 1

print('=== 경보 심각도 분포 ===')
total = sum(severity_count.values())
for sev in ['Critical', 'High', 'Medium', 'Low', 'Info']:
    count = severity_count.get(sev, 0)
    pct = (count/total*100) if total > 0 else 0
    bar = '#' * int(pct/2)
    print(f'{sev:10s}: {count:5d} ({pct:5.1f}%) {bar}')
print(f\"{'Total':10s}: {total:5d}\")
"
```

> **결과 해석**: 건전한 SOC에서는 Critical/High가 전체의 5-10% 이하여야 한다. 30% 이상이면 룰 튜닝이 필요하다. Info/Low가 80% 이상이면 자동 종결 룰을 강화할 필요가 있다.

## 3.3 MTTD 시뮬레이션 계산

```bash
# opsclaw 서버에서 OpsClaw API를 통해 MTTD 시뮬레이션
# 시뮬레이션: 공격 이벤트 발생 → 경보 생성까지 시간 측정

cat << 'SCRIPT' > /tmp/mttd_calc.py
#!/usr/bin/env python3
"""SOC KPI 계산기 - MTTD/MTTR 시뮬레이션"""
import random
import statistics
from datetime import datetime, timedelta

# 시뮬레이션 데이터: 인시던트 10건
incidents = []
for i in range(10):
    # 공격 발생 시각
    attack_time = datetime(2026, 4, 4, random.randint(0,23),
                           random.randint(0,59))
    # 탐지 시각 (Level 2 SOC: 5분~60분 랜덤)
    detect_delay = timedelta(minutes=random.randint(5, 60))
    detect_time = attack_time + detect_delay
    # 대응 완료 시각 (추가 15분~120분)
    respond_delay = timedelta(minutes=random.randint(15, 120))
    respond_time = detect_time + respond_delay
    # 봉쇄 시각 (대응의 50-80%)
    contain_delay = timedelta(minutes=random.randint(10, 90))
    contain_time = detect_time + contain_delay

    incidents.append({
        'id': f'INC-2026-{i+1:04d}',
        'attack': attack_time,
        'detect': detect_time,
        'contain': contain_time,
        'respond': respond_time,
        'ttd_min': detect_delay.total_seconds() / 60,
        'ttc_min': contain_delay.total_seconds() / 60,
        'ttr_min': (respond_time - detect_time).total_seconds() / 60,
    })

print("=" * 70)
print(f"{'ID':16s} {'공격시각':>8s} {'탐지시각':>8s} {'TTD(분)':>8s} {'TTR(분)':>8s}")
print("-" * 70)
for inc in incidents:
    print(f"{inc['id']:16s} "
          f"{inc['attack'].strftime('%H:%M'):>8s} "
          f"{inc['detect'].strftime('%H:%M'):>8s} "
          f"{inc['ttd_min']:8.0f} "
          f"{inc['ttr_min']:8.0f}")

ttd_values = [inc['ttd_min'] for inc in incidents]
ttr_values = [inc['ttr_min'] for inc in incidents]
ttc_values = [inc['ttc_min'] for inc in incidents]

print("-" * 70)
print(f"\n=== SOC KPI 결과 ===")
print(f"MTTD (평균 탐지 시간): {statistics.mean(ttd_values):.1f}분")
print(f"MTTR (평균 대응 시간): {statistics.mean(ttr_values):.1f}분")
print(f"MTTC (평균 봉쇄 시간): {statistics.mean(ttc_values):.1f}분")
print(f"MTTD 중앙값: {statistics.median(ttd_values):.1f}분")
print(f"MTTD 표준편차: {statistics.stdev(ttd_values):.1f}분")

# 성숙도 레벨 판정
mttd = statistics.mean(ttd_values)
if mttd > 240:
    level = 1
elif mttd > 60:
    level = 2
elif mttd > 15:
    level = 3
elif mttd > 5:
    level = 4
else:
    level = 5
print(f"\n→ MTTD 기준 SOC 성숙도: Level {level}")
SCRIPT

python3 /tmp/mttd_calc.py
```

> **결과 해석**: MTTD가 30분 이하이면 Level 3 수준이다. 중앙값과 평균의 차이가 크면 일부 인시던트에서 탐지가 크게 지연되는 것이므로 해당 유형의 탐지 룰을 강화해야 한다.
>
> **실전 활용**: 실제 SOC에서는 SIEM의 인시던트 타임스탬프를 기반으로 이 계산을 자동화한다. 월간 KPI 보고서에 추세 그래프를 포함하면 경영진 보고에 효과적이다.

## 3.4 Wazuh 룰 현황 분석

```bash
# siem 서버에서 활성 룰 수 확인
sshpass -p1 ssh siem@10.20.30.100 << 'EOF'
echo "=== Wazuh 활성 룰 현황 ==="
# 전체 룰 수
TOTAL_RULES=$(find /var/ossec/ruleset/rules/ -name "*.xml" -exec grep -c '<rule id' {} + 2>/dev/null | awk -F: '{sum+=$2} END{print sum}')
echo "전체 룰 수: $TOTAL_RULES"

# 커스텀 룰 수
CUSTOM_RULES=$(find /var/ossec/etc/rules/ -name "*.xml" -exec grep -c '<rule id' {} + 2>/dev/null | awk -F: '{sum+=$2} END{print sum}')
echo "커스텀 룰 수: $CUSTOM_RULES"

# 레벨별 룰 분포
echo ""
echo "=== 레벨별 룰 분포 ==="
for level in $(seq 1 15); do
    count=$(grep -r "level=\"$level\"" /var/ossec/ruleset/rules/ 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        bar=$(python3 -c "print('#' * min($count // 20, 40))")
        printf "Level %2d: %5d %s\n" "$level" "$count" "$bar"
    fi
done

# 최근 수정된 룰 파일
echo ""
echo "=== 최근 수정된 룰 파일 (최근 30일) ==="
find /var/ossec/etc/rules/ -name "*.xml" -mtime -30 -exec ls -la {} \; 2>/dev/null || echo "(최근 수정 없음)"
EOF
```

> **결과 해석**: 커스텀 룰이 전체의 10-20%면 양호하다. 0%면 기본 룰만 사용 중이므로 성숙도 Level 1-2에 해당한다. 레벨별 분포에서 Level 12+ 룰이 과도하게 많으면 경보 피로를 유발할 수 있다.

## 3.5 OpsClaw를 활용한 KPI 수집 자동화

```bash
# OpsClaw 프로젝트 생성 - KPI 수집
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 프로젝트 생성
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "soc-kpi-collection",
    "request_text": "SOC KPI 데이터 수집 - MTTD/MTTR/경보 분포",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Project ID: $PROJECT_ID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# SIEM 서버에서 KPI 데이터 수집
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "cat /var/ossec/logs/alerts/alerts.json | tail -100 | python3 -c \"import sys,json; lines=[json.loads(l) for l in sys.stdin if l.strip()]; levels=[e.get(\\\"rule\\\",{}).get(\\\"level\\\",0) for e in lines]; print(f\\\"최근 100건 평균 레벨: {sum(levels)/len(levels):.1f}\\\"); print(f\\\"Critical(12+): {sum(1 for l in levels if l>=12)}건\\\")\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "wc -l /var/ossec/logs/alerts/alerts.json",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://10.20.30.100:8002"
  }'
```

> **목적**: OpsClaw의 자동화 프레임워크를 활용하여 여러 서버에서 KPI 데이터를 원격 수집하는 패턴을 익힌다.
>
> **실전 활용**: 이 패턴을 스케줄러와 결합하면 일간/주간 KPI 자동 수집이 가능하다. OpsClaw의 evidence 기능으로 이력 관리도 자동화된다.

---

# Part 4: 성숙도 자가진단 실습 (40분)

## 4.1 SOC-CMM 자가진단 체크리스트

아래 체크리스트를 실습 환경에 적용하여 현재 성숙도를 평가하라.

### Business 도메인

```
[ ] 1. SOC 운영 목적/미션이 문서화되어 있는가?
[ ] 2. 연간 예산이 편성되어 있는가?
[ ] 3. 경영진에게 정기 보고를 하는가?
[ ] 4. 관련 규정(개인정보보호법 등) 준수 여부를 추적하는가?
[ ] 5. 서비스 카탈로그(제공 서비스 목록)가 존재하는가?

점수: ___/5  (체크 1개당 1점)
```

### People 도메인

```
[ ] 1. Tier 1/2/3 역할이 명확히 정의되어 있는가?
[ ] 2. 채용 기준(자격/역량)이 문서화되어 있는가?
[ ] 3. 정기 교육/훈련 프로그램이 있는가?
[ ] 4. 번아웃 방지 정책(교대근무 등)이 있는가?
[ ] 5. 경력 개발 경로가 정의되어 있는가?

점수: ___/5
```

### Process 도메인

```
[ ] 1. 인시던트 대응 플레이북이 5개 이상 있는가?
[ ] 2. 에스컬레이션 절차가 문서화되어 있는가?
[ ] 3. 변경 관리 프로세스가 있는가?
[ ] 4. 교훈(Lessons Learned) 회의를 정기적으로 하는가?
[ ] 5. KPI를 정기적으로 측정/보고하는가?

점수: ___/5
```

### Technology 도메인

```
[ ] 1. SIEM이 도입/운영되고 있는가?
[ ] 2. 로그 소스가 3개 이상 연동되어 있는가?
[ ] 3. 탐지 룰이 50개 이상 활성화되어 있는가?
[ ] 4. 자동 대응(SOAR) 기능이 있는가?
[ ] 5. 위협 인텔리전스 피드가 연동되어 있는가?

점수: ___/5
```

### Services 도메인

```
[ ] 1. 실시간 모니터링 서비스를 제공하는가?
[ ] 2. 인시던트 대응 서비스를 제공하는가?
[ ] 3. 위협 헌팅 서비스를 제공하는가?
[ ] 4. 취약점 관리 서비스를 제공하는가?
[ ] 5. 보안 교육 서비스를 제공하는가?

점수: ___/5
```

## 4.2 실습 환경 성숙도 평가 스크립트

```bash
# 실습 환경의 Technology 도메인 자동 평가
cat << 'SCRIPT' > /tmp/soc_maturity_check.sh
#!/bin/bash
echo "=============================================="
echo "  SOC 성숙도 자동 평가 (Technology 도메인)"
echo "=============================================="
echo ""

SCORE=0
TOTAL=10

# 1. SIEM 가동 여부
echo "[체크 1] SIEM(Wazuh) 가동 여부..."
if sshpass -p1 ssh -o ConnectTimeout=5 siem@10.20.30.100 \
   "systemctl is-active wazuh-manager" 2>/dev/null | grep -q "active"; then
    echo "  [PASS] Wazuh Manager 가동 중"
    SCORE=$((SCORE+1))
else
    echo "  [FAIL] Wazuh Manager 미가동"
fi

# 2. 에이전트 연결 수
echo "[체크 2] 연결된 에이전트 수..."
AGENTS=$(sshpass -p1 ssh -o ConnectTimeout=5 siem@10.20.30.100 \
   "/var/ossec/bin/agent_control -l 2>/dev/null | grep -c 'Active'" 2>/dev/null)
AGENTS=${AGENTS:-0}
echo "  연결된 에이전트: ${AGENTS}개"
if [ "$AGENTS" -ge 2 ]; then
    echo "  [PASS] 에이전트 2개 이상 연결"
    SCORE=$((SCORE+1))
else
    echo "  [WARN] 에이전트 부족 (권장: 3개 이상)"
fi

# 3. 커스텀 룰 존재 여부
echo "[체크 3] 커스텀 탐지 룰 존재 여부..."
CUSTOM=$(sshpass -p1 ssh -o ConnectTimeout=5 siem@10.20.30.100 \
   "ls /var/ossec/etc/rules/*.xml 2>/dev/null | wc -l" 2>/dev/null)
CUSTOM=${CUSTOM:-0}
echo "  커스텀 룰 파일: ${CUSTOM}개"
if [ "$CUSTOM" -ge 1 ]; then
    echo "  [PASS] 커스텀 룰 존재"
    SCORE=$((SCORE+1))
else
    echo "  [FAIL] 커스텀 룰 없음"
fi

# 4. IPS(Suricata) 가동 여부
echo "[체크 4] IPS(Suricata) 가동 여부..."
if sshpass -p1 ssh -o ConnectTimeout=5 secu@10.20.30.1 \
   "systemctl is-active suricata" 2>/dev/null | grep -q "active"; then
    echo "  [PASS] Suricata IPS 가동 중"
    SCORE=$((SCORE+1))
else
    echo "  [FAIL] Suricata IPS 미가동"
fi

# 5. 방화벽(nftables) 활성 여부
echo "[체크 5] 방화벽(nftables) 활성 여부..."
if sshpass -p1 ssh -o ConnectTimeout=5 secu@10.20.30.1 \
   "nft list tables" 2>/dev/null | grep -q "table"; then
    echo "  [PASS] nftables 활성"
    SCORE=$((SCORE+1))
else
    echo "  [FAIL] nftables 비활성"
fi

# 6. 웹 로그 수집 여부
echo "[체크 6] 웹서버 로그 수집 여부..."
if sshpass -p1 ssh -o ConnectTimeout=5 web@10.20.30.80 \
   "test -f /var/ossec/etc/ossec.conf && grep -q 'localfile' /var/ossec/etc/ossec.conf" 2>/dev/null; then
    echo "  [PASS] 웹서버 로그 수집 설정 존재"
    SCORE=$((SCORE+1))
else
    echo "  [WARN] 웹서버 로그 수집 미확인"
fi

# 7. OpsClaw 자동화 가동 여부
echo "[체크 7] OpsClaw 자동화 플랫폼 가동 여부..."
if curl -s -o /dev/null -w "%{http_code}" \
   -H "X-API-Key: opsclaw-api-key-2026" \
   http://localhost:8000/projects 2>/dev/null | grep -q "200"; then
    echo "  [PASS] OpsClaw Manager API 가동 중"
    SCORE=$((SCORE+1))
else
    echo "  [FAIL] OpsClaw Manager API 미가동"
fi

# 8. 위협 인텔리전스(OpenCTI) 가동 여부
echo "[체크 8] 위협 인텔리전스(OpenCTI) 가동 여부..."
if curl -s -o /dev/null -w "%{http_code}" \
   http://10.20.30.100:9400 2>/dev/null | grep -q "200\|301\|302"; then
    echo "  [PASS] OpenCTI 접근 가능"
    SCORE=$((SCORE+1))
else
    echo "  [WARN] OpenCTI 미접근 (설치 필요 가능)"
fi

# 9. 로그 보존 기간 확인
echo "[체크 9] 로그 보존 정책..."
RETENTION=$(sshpass -p1 ssh -o ConnectTimeout=5 siem@10.20.30.100 \
   "ls /var/ossec/logs/alerts/ 2>/dev/null | wc -l" 2>/dev/null)
RETENTION=${RETENTION:-0}
echo "  경보 로그 디렉토리: ${RETENTION}개"
if [ "$RETENTION" -ge 7 ]; then
    echo "  [PASS] 7일 이상 로그 보존"
    SCORE=$((SCORE+1))
else
    echo "  [WARN] 로그 보존 기간 부족"
fi

# 10. AI/LLM 연동 여부
echo "[체크 10] AI/LLM 연동 여부..."
if curl -s -o /dev/null -w "%{http_code}" \
   http://192.168.0.105:11434/v1/models 2>/dev/null | grep -q "200"; then
    echo "  [PASS] Ollama LLM 연동 가능"
    SCORE=$((SCORE+1))
else
    echo "  [WARN] LLM 연동 미확인"
fi

# 결과
echo ""
echo "=============================================="
echo "  평가 결과: ${SCORE}/${TOTAL}"
echo "=============================================="

if [ "$SCORE" -ge 9 ]; then
    echo "  성숙도 수준: Level 4-5 (Quantitatively Managed/Optimizing)"
elif [ "$SCORE" -ge 7 ]; then
    echo "  성숙도 수준: Level 3 (Defined)"
elif [ "$SCORE" -ge 4 ]; then
    echo "  성숙도 수준: Level 2 (Managed)"
else
    echo "  성숙도 수준: Level 1 (Initial)"
fi
SCRIPT

bash /tmp/soc_maturity_check.sh
```

> **실습 목적**: 자동화 스크립트로 실습 환경의 SOC 성숙도를 객관적으로 평가한다.
>
> **배우는 것**: 성숙도 평가의 자동화 가능성, SSH 기반 원격 점검, 정량적 평가 기준
>
> **결과 해석**: 10점 만점에서 7점 이상이면 Level 3 수준의 기술 인프라를 갖추고 있다. 부족한 항목은 개선 로드맵에 포함한다.
>
> **트러블슈팅**:
> - SSH 연결 실패 → `sshpass` 설치 확인: `which sshpass`
> - API 연결 실패 → 해당 서비스 가동 상태 확인
> - 점수가 낮게 나와도 정상 → 실습 환경은 모든 구성 요소가 완비되지 않을 수 있음

## 4.3 성숙도 레이더 차트 데이터 생성

```bash
# Python으로 레이더 차트 데이터 생성
cat << 'SCRIPT' > /tmp/maturity_radar.py
#!/usr/bin/env python3
"""SOC-CMM 성숙도 레이더 차트 데이터 생성"""

# 현재 수준 (실습 환경 기준 예시)
current = {
    'Business': 2,
    'People': 2,
    'Process': 3,
    'Technology': 3,
    'Services': 2,
}

# 목표 수준 (6개월 후)
target = {
    'Business': 3,
    'People': 3,
    'Process': 4,
    'Technology': 4,
    'Services': 3,
}

print("=" * 50)
print("  SOC-CMM 성숙도 레이더 차트 데이터")
print("=" * 50)
print(f"\n{'도메인':12s} {'현재':>6s} {'목표':>6s} {'갭':>6s}")
print("-" * 36)

total_current = 0
total_target = 0
for domain in current:
    gap = target[domain] - current[domain]
    total_current += current[domain]
    total_target += target[domain]
    cur_bar = ">" * current[domain]
    tgt_bar = ">" * target[domain]
    print(f"{domain:12s} {current[domain]:>6d} {target[domain]:>6d} {gap:>+6d}")

avg_current = total_current / len(current)
avg_target = total_target / len(target)
print("-" * 36)
print(f"{'평균':12s} {avg_current:>6.1f} {avg_target:>6.1f} {avg_target-avg_current:>+6.1f}")

# 시각화 (텍스트 기반)
print("\n=== 현재 vs 목표 시각화 ===")
for domain in current:
    cur = current[domain]
    tgt = target[domain]
    print(f"\n{domain}:")
    print(f"  현재: {'|' * cur}{'.' * (5-cur)} [{cur}/5]")
    print(f"  목표: {'|' * tgt}{'.' * (5-tgt)} [{tgt}/5]")

# 개선 우선순위
print("\n=== 개선 우선순위 (갭 크기순) ===")
gaps = [(d, target[d]-current[d]) for d in current]
gaps.sort(key=lambda x: -x[1])
for i, (domain, gap) in enumerate(gaps, 1):
    priority = "HIGH" if gap >= 2 else "MEDIUM" if gap >= 1 else "LOW"
    print(f"  {i}. {domain:12s} (갭: +{gap}) - 우선순위: {priority}")
SCRIPT

python3 /tmp/maturity_radar.py
```

> **실전 활용**: 이 데이터를 엑셀이나 Grafana에 넣으면 경영진 보고용 레이더 차트를 만들 수 있다. 갭 분석 결과는 다음 분기 예산 요청의 근거가 된다.

## 4.4 KPI 기반 개선 로드맵 작성

```bash
cat << 'SCRIPT' > /tmp/soc_roadmap.py
#!/usr/bin/env python3
"""SOC 성숙도 개선 로드맵 생성기"""

roadmap = {
    "3개월 (Quick Wins)": [
        {"task": "Wazuh 커스텀 룰 20개 추가", "domain": "Technology", "effort": "Low"},
        {"task": "Tier 1/2 에스컬레이션 절차 문서화", "domain": "Process", "effort": "Low"},
        {"task": "주간 KPI 보고서 템플릿 작성", "domain": "Business", "effort": "Low"},
        {"task": "OpsClaw 자동화 플레이북 5개 작성", "domain": "Technology", "effort": "Medium"},
    ],
    "6개월 (Foundation)": [
        {"task": "위협 인텔리전스 피드 3개 연동", "domain": "Technology", "effort": "Medium"},
        {"task": "Tier 1/2/3 교육 프로그램 수립", "domain": "People", "effort": "Medium"},
        {"task": "인시던트 대응 플레이북 15개 작성", "domain": "Process", "effort": "Medium"},
        {"task": "SOAR 자동 대응 30% 목표 달성", "domain": "Services", "effort": "High"},
    ],
    "12개월 (Maturation)": [
        {"task": "Purple Team 분기별 훈련 시작", "domain": "Services", "effort": "High"},
        {"task": "AI/LLM 기반 경보 분류 도입", "domain": "Technology", "effort": "High"},
        {"task": "SOC-CMM Level 3 인증 추진", "domain": "Business", "effort": "High"},
        {"task": "위협 헌팅 프로그램 상시 운영", "domain": "Services", "effort": "High"},
    ],
}

for phase, tasks in roadmap.items():
    print(f"\n{'='*60}")
    print(f"  {phase}")
    print(f"{'='*60}")
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. [{task['domain']:12s}] {task['task']}")
        print(f"     Effort: {task['effort']}")
SCRIPT

python3 /tmp/soc_roadmap.py
```

> **실전 활용**: 성숙도 평가 결과를 기반으로 구체적인 개선 로드맵을 수립하는 것이 SOC-CMM 활용의 핵심이다. "Quick Wins"로 빠르게 성과를 보이고, 장기 과제는 예산과 인력 확보 후 추진한다.

---

## 체크리스트

학습을 마친 후 아래 항목을 점검하라.

- [ ] SOC-CMM 5개 도메인을 열거할 수 있다
- [ ] SOC-CMM 5단계 성숙도 레벨의 차이를 설명할 수 있다
- [ ] Tier 1/2/3 분석가의 역할과 핵심 역량을 구분할 수 있다
- [ ] MTTD, MTTR, MTTC의 정의와 산식을 알고 있다
- [ ] 오탐률과 탐지율의 관계를 설명할 수 있다
- [ ] KPI 대시보드의 설계 원칙 5가지를 알고 있다
- [ ] 에스컬레이션 매트릭스를 설명할 수 있다
- [ ] Wazuh API로 경보 데이터를 추출할 수 있다
- [ ] SOC-CMM 자가진단 체크리스트를 작성할 수 있다
- [ ] 성숙도 갭 분석 기반 개선 로드맵을 수립할 수 있다

---

## 복습 퀴즈

**Q1.** SOC-CMM의 5가지 도메인을 모두 나열하시오.

<details><summary>정답</summary>
Business, People, Process, Technology, Services
</details>

**Q2.** SOC-CMM Level 3(Defined)의 핵심 특징은 무엇인가?

<details><summary>정답</summary>
표준화된 프로세스가 수립되어 일관적으로 수행되며, 메트릭 측정이 시작되고, 교육이 체계화된 단계이다.
</details>

**Q3.** MTTD가 240분이고 MTTR이 480분인 SOC의 성숙도 레벨은 대략 몇인가?

<details><summary>정답</summary>
Level 1-2 수준이다. MTTD 240분(4시간)은 탐지가 매우 느린 상태이며, MTTR 480분(8시간)도 대응이 크게 지연되는 것을 의미한다.
</details>

**Q4.** Tier 2 분석가의 핵심 역할 3가지를 설명하시오.

<details><summary>정답</summary>
1) 심화 로그 상관분석 및 패킷 분석, 2) 인시던트 대응 리딩 (IP 차단, 계정 잠금, 격리), 3) 인시던트 보고서 작성 및 근본 원인 분석
</details>

**Q5.** 오탐률(False Positive Rate)이 80%인 SOC에서 발생하는 문제는?

<details><summary>정답</summary>
경보 피로(Alert Fatigue)가 발생한다. 분석가가 대부분의 경보를 무시하게 되어, 실제 공격도 놓칠 위험이 높아진다. 미탐(False Negative) 증가로 이어진다.
</details>

**Q6.** SOC-CMM에서 People 도메인이 별도로 존재하는 이유는?

<details><summary>정답</summary>
SOC 운영에서 인력(채용, 교육, 역량 개발, 번아웃 방지)이 기술 못지않게 중요하기 때문이다. NIST CSF 등 다른 프레임워크에서 인력 도메인이 약한 것을 보완한다.
</details>

**Q7.** Follow-the-Sun 교대 모델의 장단점을 설명하시오.

<details><summary>정답</summary>
장점: 야간 근무가 없어 분석가 번아웃을 줄일 수 있다. 단점: 글로벌 팀(서로 다른 시간대 3개 지역)이 필요하며, 인수인계와 문화 차이 관리가 어렵다.
</details>

**Q8.** KPI 대시보드에 50개 이상의 지표를 표시하면 왜 문제가 되는가?

<details><summary>정답</summary>
정보 과부하로 핵심 지표에 집중하기 어렵다. 의사결정자가 중요한 변화를 놓칠 수 있다. 5-7개의 핵심 KPI에 집중하고, 나머지는 드릴다운으로 제공하는 것이 효과적이다.
</details>

**Q9.** SOC 성숙도 Level 1에서 Level 3으로 개선하려면 가장 먼저 해야 할 것은?

<details><summary>정답</summary>
Process 도메인에서 기본 인시던트 대응 플레이북을 작성하고, Tier 역할을 정의하며, KPI 측정을 시작하는 것이다. 기술 도입보다 프로세스 정립이 우선이다.
</details>

**Q10.** 우리 실습 환경(Wazuh + OpsClaw + Suricata)의 Technology 도메인 강점과 약점을 각각 1개씩 말하시오.

<details><summary>정답</summary>
강점: 오픈소스 기반으로 SIEM(Wazuh), IPS(Suricata), 자동화(OpsClaw)가 통합되어 있다. 약점: EDR이 부재하고, 위협 인텔리전스 피드 자동 연동이 미구현 상태이다.
</details>

---

## 과제

### 과제 1: SOC-CMM 자가진단 보고서 (필수)

실습 환경에 대해 SOC-CMM 5개 도메인 자가진단을 수행하고, 다음을 포함하는 보고서를 작성하라.

1. **도메인별 현재 점수** (0-5점, 증거 기반)
2. **레이더 차트 데이터** (Part 4.3 스크립트 활용)
3. **상위 3개 개선 과제** (우선순위 근거 포함)
4. **3개월 개선 로드맵** (구체적 액션 아이템)

### 과제 2: KPI 대시보드 설계 (선택)

가상의 SOC(분석가 5명, 일 경보 3,000건)를 위한 KPI 대시보드를 설계하라.

1. **핵심 KPI 5-7개** 선정 (산식 포함)
2. **목표값** 설정 (Level 3 기준)
3. **시각화 방법** 제안 (그래프 유형, 색상 코드)
4. **데이터 소스** 명시 (어디서 어떻게 수집하는지)

---

## 다음 주 예고

**Week 02: SIEM 고급 상관분석**에서는 Wazuh의 상관 룰을 심화 학습하고, 다중 소스 이벤트를 연계하여 고도화된 탐지를 구현한다. 단일 이벤트로는 탐지할 수 없는 복합 공격 패턴을 상관분석으로 잡아내는 방법을 다룬다.
