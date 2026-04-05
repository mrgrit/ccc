# Week 01: APT 시뮬레이션 기초 — 킬체인 7단계와 MITRE ATT&CK

## 학습 목표
- APT(Advanced Persistent Threat)의 정의와 일반 공격과의 차이를 명확히 구분한다
- 사이버 킬체인(Cyber Kill Chain) 7단계를 설명하고 각 단계별 공격·방어 기법을 매핑할 수 있다
- MITRE ATT&CK 프레임워크의 전체 구조(Tactic-Technique-Sub-technique-Procedure)를 이해한다
- ATT&CK Navigator를 활용하여 공격 시나리오를 시각화하고 방어 커버리지를 분석할 수 있다
- OpsClaw를 활용한 APT 시뮬레이션 프로젝트를 설계하고 실행할 수 있다
- 실제 APT 사례(SolarWinds, APT29, APT41)를 킬체인과 ATT&CK에 매핑할 수 있다

## 전제 조건
- 공방전 기초 과정(course11) 이수 완료
- 네트워크/시스템 보안 기본 개념 (TCP/IP, 방화벽, IDS/IPS)
- Linux CLI 기본 조작 (ssh, curl, grep, awk)
- REST API 호출 경험 (curl 사용)
- OpsClaw 플랫폼 기본 사용법 (프로젝트 생성, execute-plan)

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 기지 / Control Plane | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (JuiceShop, Apache) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh, OpenCTI) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: APT 개론 및 킬체인 7단계 | 강의 |
| 0:40-1:10 | Part 2: MITRE ATT&CK 프레임워크 심화 | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | Part 3: ATT&CK Navigator 실습 + 정찰 기법 실습 | 실습 |
| 2:00-2:40 | Part 4: OpsClaw APT 시뮬레이션 프로젝트 설계·실행 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 실제 APT 사례 심층 분석 + 토론 | 토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **APT** | Advanced Persistent Threat | 특정 조직을 장기간 은밀하게 공격하는 고도화된 위협 | 잠복 첩보원 |
| **킬체인** | Cyber Kill Chain | 공격의 전체 생명주기를 7단계로 분류한 모델 | 미사일 요격 단계 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술·기법·절차 | 범죄자의 수법 프로파일 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인) | 범죄 현장 증거물 |
| **IOA** | Indicator of Attack | 공격 행위 지표 (비정상 프로세스, 이상 트래픽) | 범행 중 행동 패턴 |
| **OSINT** | Open Source Intelligence | 공개 출처 정보 수집 | 인터넷 검색으로 정보 모으기 |
| **Lateral Movement** | 측면 이동 | 내부 네트워크에서 다른 시스템으로 이동 | 건물 안에서 방 옮기기 |
| **C2** | Command and Control | 공격자가 침투한 시스템을 원격 제어하는 채널 | 첩보원에게 지령 보내기 |
| **Persistence** | 지속성 | 재부팅 후에도 접근을 유지하는 메커니즘 | 비밀 뒷문 만들어두기 |
| **Defense Evasion** | 방어 회피 | 보안 도구의 탐지를 피하는 기법 | 변장·위장 |
| **Exfiltration** | 데이터 유출 | 내부 데이터를 외부로 빼돌리는 행위 | 기밀문서 반출 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표준 교환 형식 | 범죄 보고서 표준 양식 |
| **Navigator** | ATT&CK Navigator | ATT&CK 기법을 시각적으로 매핑하는 도구 | 전술 지도 |
| **Adversary Emulation** | 적대적 에뮬레이션 | 실제 APT 그룹의 TTP를 모방하여 테스트 | 모의 침투 훈련 |

---

# Part 1: APT 개론 및 킬체인 7단계 (40분)

## 1.1 APT란 무엇인가

APT(Advanced Persistent Threat)는 특정 조직을 대상으로 **장기간에 걸쳐** 은밀하게 수행되는 고도화된 사이버 공격이다. 일반적인 사이버 공격과 근본적으로 다른 특성을 가진다.

### APT의 세 가지 핵심 특성

| 특성 | 의미 | 세부 설명 |
|------|------|----------|
| **Advanced (고도화)** | 최신·복합 공격 기법 사용 | 제로데이 익스플로잇, 커스텀 멀웨어, 공급망 공격 등 다양한 벡터를 조합. 방어 도구 우회 기법을 사전에 테스트 |
| **Persistent (지속적)** | 장기간 은밀한 활동 | 수개월~수년간 네트워크에 잠복하며 정보 수집. 탐지 시 우회 경로 확보, 다중 백도어 유지 |
| **Threat (위협)** | 조직적·목적 지향적 | 국가 지원 해킹 그룹, 산업 스파이. 명확한 목표(군사 기밀, 지적 재산, 인프라 파괴)를 가지고 활동 |

### APT vs 일반 공격 비교

| 비교 항목 | 일반 공격 (Opportunistic) | APT (Targeted) |
|----------|--------------------------|----------------|
| **목표 선정** | 불특정 다수, 취약한 곳 아무나 | 특정 조직·기관을 사전 선정 |
| **공격 기간** | 수분~수시간 (hit-and-run) | 수주~수년 (장기 잠복) |
| **기법 수준** | 공개된 익스플로잇, 스크립트 | 제로데이, 커스텀 툴, 다단계 체인 |
| **은닉 수준** | 낮음 (노이즈 많음) | 극도로 높음 (정상 트래픽 위장) |
| **동기** | 금전(랜섬웨어), 과시 | 국가 안보, 산업 스파이, 정치적 목적 |
| **자원** | 개인 또는 소규모 그룹 | 국가급 조직, 대규모 예산 |
| **재침투** | 차단되면 포기 | 차단되면 우회 경로로 재침투 |
| **데이터 수집** | 즉시 금전화 가능한 데이터 | 장기적 전략 가치가 있는 기밀 |

### 주요 APT 그룹 일람

| 그룹명 | 별칭 | 배후 추정 | 주요 대상 | 대표 공격 |
|--------|------|----------|----------|----------|
| APT28 | Fancy Bear | 러시아 GRU | 정부, 군사, 미디어 | DNC 해킹(2016) |
| APT29 | Cozy Bear | 러시아 SVR | 정부, 외교, 에너지 | SolarWinds(2020) |
| APT41 | Winnti | 중국 | 게임, 통신, 의료 | CCleaner 공급망(2017) |
| Lazarus | Hidden Cobra | 북한 | 금융, 암호화폐, 방산 | Sony Pictures(2014), WannaCry(2017) |
| APT33 | Elfin | 이란 | 항공, 에너지 | Shamoon 변종 공격 |
| Equation Group | - | NSA(추정) | 통신, 에너지, 군사 | Stuxnet 연관 |

## 1.2 사이버 킬체인(Cyber Kill Chain) 7단계

Lockheed Martin이 2011년에 제안한 킬체인 모델은 APT 공격의 전체 생명주기를 7단계로 분류하여, 각 단계에서의 탐지·차단 기회를 체계적으로 분석하는 프레임워크이다.

```
+---------------------------------------------------------------------+
|                    사이버 킬체인 7단계                                |
+------------------+--------------------------------------------------+
| 1. 정찰           | 대상 조직의 네트워크, 인력, 기술 스택 정보 수집       |
| (Reconnaissance)  | OSINT, 소셜 엔지니어링, 포트 스캔                   |
+------------------┼--------------------------------------------------+
| 2. 무기화         | 취약점에 맞는 공격 페이로드(Exploit+Payload) 제작     |
| (Weaponization)  | 악성 문서, 트로이목마, 드롭퍼 생성                    |
+------------------┼--------------------------------------------------+
| 3. 전달           | 공격 페이로드를 대상에게 전달                        |
| (Delivery)       | 스피어 피싱, 워터링홀, USB, 공급망                   |
+------------------┼--------------------------------------------------+
| 4. 익스플로잇     | 전달된 페이로드가 취약점을 실행                      |
| (Exploitation)   | 버퍼 오버플로우, RCE, 매크로 실행                    |
+------------------┼--------------------------------------------------+
| 5. 설치           | 지속적 접근을 위한 백도어/RAT 설치                   |
| (Installation)   | 웹셸, 서비스 등록, 레지스트리 키                     |
+------------------┼--------------------------------------------------+
| 6. C2             | 공격자가 침투한 시스템을 원격 제어하는 채널 구축      |
| (Command&Control)| HTTP C2, DNS 터널링, 암호화 통신                    |
+------------------┼--------------------------------------------------+
| 7. 목표 달성      | 최종 목적 수행                                     |
| (Actions)        | 데이터 유출, 파괴, 랜섬, 정보 조작                   |
+------------------+--------------------------------------------------+
```

### 단계별 상세 분석

**1단계: 정찰(Reconnaissance)**

공격자가 대상 조직에 대한 정보를 수집하는 단계이다.

| 정찰 유형 | 기법 | 도구 | 탐지 가능성 |
|----------|------|------|------------|
| 수동 정찰 | WHOIS, DNS 조회, 소셜 미디어 | theHarvester, Maltego | 낮음 (외부 활동) |
| 능동 정찰 | 포트 스캔, 취약점 스캔 | nmap, Nessus, Shodan | 높음 (IDS 탐지) |
| 소셜 엔지니어링 | 피싱 이메일 발송 테스트, 전화 | SET, Gophish | 중간 |
| 기술 정찰 | 웹 스택 식별, S3 버킷 탐색 | Wappalyzer, AWS CLI | 낮음~중간 |

**2단계: 무기화(Weaponization)**

수집한 정보를 바탕으로 공격 도구를 제작한다. **방어자가 직접 관찰할 수 없는 유일한 단계**이다.

- 익스플로잇 코드 + 페이로드(백도어, RAT) 결합
- 악성 문서(Word 매크로, PDF 익스플로잇) 생성
- 커스텀 멀웨어 컴파일 및 AV 우회 테스트
- 인프라 준비: C2 서버, 도메인 등록, 인증서 발급

**3단계: 전달(Delivery)**

| 전달 방법 | 설명 | ATT&CK ID |
|----------|------|-----------|
| 스피어 피싱 | 특정 개인에게 맞춤형 악성 메일 | T1566.001 |
| 워터링홀 | 대상이 방문하는 웹사이트 감염 | T1189 |
| 공급망 공격 | 신뢰할 수 있는 소프트웨어에 악성코드 삽입 | T1195 |
| 이동식 미디어 | USB, 외장하드를 통한 전달 | T1091 |
| 드라이브바이 다운로드 | 웹 브라우저 취약점 악용 | T1189 |

**4단계: 익스플로잇(Exploitation)**

전달된 페이로드가 시스템의 취약점을 악용하여 코드를 실행하는 단계이다.

- 클라이언트 측: 브라우저, 오피스, PDF 리더 취약점
- 서버 측: 웹 애플리케이션 취약점 (SQLi, RCE)
- OS 취약점: 커널 익스플로잇, 권한 상승
- 제로데이: 패치가 없는 미공개 취약점

**5단계: 설치(Installation)**

재부팅이나 재접속 후에도 접근을 유지하기 위한 지속성 메커니즘을 설치한다.

| 지속성 기법 | 설명 | ATT&CK ID |
|-----------|------|-----------|
| 웹셸 | 웹서버에 명령 실행 가능한 스크립트 설치 | T1505.003 |
| 서비스 등록 | 시스템 서비스로 악성코드 등록 | T1543.003 |
| 크론/스케줄러 | 주기적으로 악성코드 실행 | T1053.003 |
| 레지스트리 Run 키 | 부팅 시 자동 실행 | T1547.001 |
| DLL 사이드로딩 | 정상 프로그램이 악성 DLL 로딩 | T1574.002 |

**6단계: C2(Command and Control)**

공격자가 침투한 시스템과 통신하는 은닉 채널을 구축한다.

| C2 방식 | 은닉 수준 | 탐지 방법 |
|---------|----------|----------|
| HTTP/HTTPS | 중간 | 프록시 로그, SSL 인스펙션 |
| DNS 터널링 | 높음 | DNS 쿼리 길이/빈도 이상 탐지 |
| 소셜 미디어 | 높음 | 알려진 C2 도메인 차단 |
| ICMP 터널 | 높음 | ICMP 페이로드 크기 이상 탐지 |
| 클라우드 서비스 | 매우 높음 | 행위 기반 분석 필요 |

**7단계: 목표 달성(Actions on Objectives)**

최종 목적을 수행하는 단계이다.

- 데이터 유출: 기밀 문서, 소스코드, 개인정보
- 데이터 파괴: 와이퍼 멀웨어, 디스크 암호화
- 랜섬웨어: 파일 암호화 후 금전 요구
- 정보 조작: 데이터 무결성 침해
- 추가 인프라 침투: 협력사, 고객사로 확장

### 킬체인의 방어 적용 원칙

> **핵심 원리**: 킬체인의 **어느 한 단계만 차단**하면 공격 전체가 실패한다. 방어자는 가능한 많은 단계에 탐지·차단 메커니즘을 배치해야 한다.

```
방어 심층(Defense in Depth) 매핑:

1. 정찰    → 공격 표면 최소화, 정보 노출 제한
2. 무기화   → (직접 방어 불가) → 위협 인텔리전스로 도구 정보 수집
3. 전달    → 이메일 필터링, 웹 프록시, USB 통제
4. 익스플로잇 → 패치 관리, 애플리케이션 화이트리스트, DEP/ASLR
5. 설치    → EDR, 무결성 모니터링, 실행 정책
6. C2      → 네트워크 모니터링, DNS 필터링, 프록시 분석
7. 목표 달성 → DLP, 데이터 암호화, 네트워크 세그멘테이션
```

## 1.3 킬체인 모델의 한계와 발전

킬체인 모델은 강력한 분석 도구이지만, 몇 가지 한계점이 존재한다.

| 한계 | 설명 | 보완책 |
|------|------|--------|
| 내부 위협 미고려 | 외부→내부 침투만 모델링 | 내부 위협 별도 프레임워크 |
| 선형적 구조 | 실제 공격은 비선형, 반복적 | MITRE ATT&CK로 보완 |
| 방어자 중심 편향 | 공격자의 적응을 반영하지 못함 | Diamond Model 등 병행 |
| 클라우드 환경 미반영 | 전통적 네트워크 경계 기반 | 클라우드 ATT&CK 매트릭스 |

---

# Part 2: MITRE ATT&CK 프레임워크 심화 (30분)

## 2.1 ATT&CK 구조 이해

MITRE ATT&CK(Adversarial Tactics, Techniques, and Common Knowledge)는 킬체인을 더욱 세분화한 체계적 위협 분류 프레임워크이다.

### 4계층 구조

```
Tactic (전술)     → "왜" 공격하는가 (목적)
  +- Technique (기법)  → "무엇을" 하는가 (행위)
       +- Sub-technique (하위 기법) → "어떻게" 하는가 (구체적 방법)
            +- Procedure (절차) → 실제 APT 그룹이 사용한 구현 방식
```

### 14개 전술(Tactic) 완전 매핑

| 전술 ID | 전술명 | 설명 | 킬체인 매핑 | 기법 수 |
|---------|--------|------|------------|--------|
| TA0043 | Reconnaissance (정찰) | 대상 정보 수집 | 1단계 | 10+ |
| TA0042 | Resource Development (자원 개발) | 공격 인프라 준비 | 2단계 | 8+ |
| TA0001 | Initial Access (초기 접근) | 네트워크 진입 | 3-4단계 | 9+ |
| TA0002 | Execution (실행) | 악성 코드 실행 | 4단계 | 14+ |
| TA0003 | Persistence (지속성) | 지속적 접근 유지 | 5단계 | 19+ |
| TA0004 | Privilege Escalation (권한 상승) | 높은 권한 획득 | 5단계 | 13+ |
| TA0005 | Defense Evasion (방어 회피) | 탐지 회피 | 전 단계 | 42+ |
| TA0006 | Credential Access (자격증명 접근) | 계정 정보 탈취 | 6단계 | 17+ |
| TA0007 | Discovery (발견) | 환경 정보 탐색 | 1단계 보충 | 31+ |
| TA0008 | Lateral Movement (측면 이동) | 내부 확산 | 7단계 | 9+ |
| TA0009 | Collection (수집) | 목표 데이터 수집 | 7단계 | 17+ |
| TA0011 | Command and Control (명령 제어) | C2 채널 운용 | 6단계 | 16+ |
| TA0010 | Exfiltration (유출) | 데이터 외부 전송 | 7단계 | 9+ |
| TA0040 | Impact (영향) | 가용성/무결성 파괴 | 7단계 | 13+ |

### ATT&CK 매트릭스의 활용 분야

| 활용 분야 | 설명 | 구체적 용도 |
|----------|------|-----------|
| **위협 모델링** | 조직 대상 위협 식별 | 산업별 주요 APT 그룹의 TTP 분석 |
| **탐지 엔지니어링** | 탐지 규칙 설계 | 각 기법별 Sigma/YARA 룰 매핑 |
| **레드팀 운영** | 공격 시나리오 설계 | APT 그룹 에뮬레이션 계획 수립 |
| **방어 평가** | 보안 커버리지 분석 | Navigator로 탐지 가능/불가 기법 시각화 |
| **인시던트 대응** | 공격 분석 체계화 | 발견된 IOC를 기법으로 매핑 |
| **보고서 작성** | 표준화된 용어 사용 | 조직 간 위협 정보 공유 (STIX/TAXII) |

## 2.2 ATT&CK과 킬체인의 매핑

```
킬체인 7단계        ATT&CK Tactics (14개)
===========        ======================
1. 정찰         ←→  Reconnaissance, Discovery
2. 무기화       ←→  Resource Development
3. 전달         ←→  Initial Access
4. 익스플로잇   ←→  Execution
5. 설치         ←→  Persistence, Privilege Escalation
6. C2           ←→  Command and Control, Credential Access
7. 목표 달성    ←→  Lateral Movement, Collection,
                     Exfiltration, Impact
(전 단계)       ←→  Defense Evasion
```

## 2.3 ATT&CK 데이터 소스와 탐지

ATT&CK v13부터 각 기법에 Data Source와 Data Component가 명시되어 있어, 어떤 로그를 수집해야 탐지할 수 있는지 직접 확인할 수 있다.

| Data Source | Data Component | 탐지 가능 기법 예시 |
|-------------|---------------|-------------------|
| Process | Process Creation | T1059 (Command-Line Interface) |
| Network Traffic | Network Connection Creation | T1071 (Application Layer Protocol) |
| File | File Creation | T1105 (Ingress Tool Transfer) |
| Windows Registry | Registry Key Modification | T1547.001 (Boot Autostart) |
| Active Directory | AD Object Modification | T1098 (Account Manipulation) |
| Command | Command Execution | T1053 (Scheduled Task) |

---

# Part 3: ATT&CK Navigator 실습 + 정찰 기법 실습 (40분)

## 실습 3.1: OpsClaw 환경 확인 및 API 키 설정

> **실습 목적**: APT 시뮬레이션을 수행하기 전에 OpsClaw 플랫폼과 전체 실습 환경이 정상 동작하는지 확인한다.
>
> **배우는 것**: 멀티 서버 환경에서의 사전 점검 절차, API 인증 메커니즘의 중요성을 이해한다.
>
> **결과 해석**: 모든 서버의 health 응답이 정상이면 실습 환경이 준비된 것이다. 연결 거부(Connection refused)는 SubAgent 미기동을 의미한다.
>
> **실전 활용**: 실제 레드팀 작전에서도 공격 인프라의 사전 점검은 필수이다. 작전 중 도구 오류는 탐지 위험을 높인다.

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# Manager API 상태 확인
curl -s http://localhost:8000/health | python3 -m json.tool
# 예상 출력:
# {
#     "status": "ok"
# }
```

```bash
# 전체 SubAgent 상태 확인
for host in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $host ==="
  curl -s --connect-timeout 3 http://$host:8002/health 2>/dev/null || echo "UNREACHABLE"
done
# 각 서버의 SubAgent 상태가 출력된다
```

> **명령어 해설**: `--connect-timeout 3`은 3초 내 연결되지 않으면 타임아웃 처리한다. 실제 침투 테스트에서도 네트워크 지연에 대한 타임아웃 설정은 필수이다.
>
> **트러블슈팅**: SubAgent가 응답하지 않으면 해당 서버에 SSH 접속 후 `systemctl status subagent` 또는 `ps aux | grep subagent`로 프로세스 상태를 확인한다.

## 실습 3.2: OSINT 기반 정찰 시뮬레이션

> **실습 목적**: 킬체인 1단계(정찰)의 핵심 기법인 OSINT 수집을 실습한다. 실제 환경(web 서버)에 대한 정보 수집을 통해 공격 표면을 식별한다.
>
> **배우는 것**: 수동/능동 정찰의 차이, 포트 스캔 기법, 웹 서버 핑거프린팅, OpsClaw를 활용한 자동화된 정찰 수행 방법을 이해한다.
>
> **결과 해석**: 열린 포트가 많을수록 공격 표면이 넓다. 버전 정보가 노출되면 CVE 검색이 용이해져 익스플로잇 가능성이 높아진다.
>
> **실전 활용**: 실제 침투 테스트 시 정찰 단계는 전체 작전의 60% 이상을 차지한다. 정확한 정찰이 성공적 침투의 핵심이다.

```bash
# OpsClaw 프로젝트 생성 (APT 정찰 시뮬레이션)
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week01-apt-recon",
    "request_text": "APT 킬체인 1단계: 대상 서버 정찰 수행",
    "master_mode": "external"
  }' | python3 -m json.tool
# 반환된 프로젝트 ID를 메모한다
```

```bash
# 프로젝트 ID 설정 (실제 반환된 값으로 교체)
export PROJECT_ID="반환된-프로젝트-ID"

# Stage 전환: plan → execute
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

> **명령어 해설**: OpsClaw 프로젝트의 생명주기는 `created → planning → executing → validating → reporting → closed`이다. execute-plan을 호출하려면 반드시 `plan` → `execute` stage 전환이 필요하다.
>
> **트러블슈팅**: "stage transition not allowed" 오류가 발생하면 현재 프로젝트 상태를 `GET /projects/{id}`로 확인한다. 이미 executing 상태라면 stage 전환이 불필요하다.

```bash
# 정찰 태스크 실행: 포트 스캔 + 서비스 식별 + 웹 핑거프린팅
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "nmap -sV -sC -p 1-1000 10.20.30.80 2>/dev/null | head -50",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "curl -s -I http://10.20.30.80:3000 | head -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "curl -s http://10.20.30.80:3000/api/ 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "dig ANY 10.20.30.80 @10.20.30.1 2>/dev/null; host 10.20.30.80 2>/dev/null",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 4개의 정찰 태스크가 병렬로 실행되어 결과가 반환된다
```

> **명령어 해설**:
> - `nmap -sV -sC`: 서비스 버전 탐지(-sV)와 기본 스크립트 실행(-sC)을 수행하는 포트 스캔
> - `curl -s -I`: HTTP 헤더만 요청하여 서버 소프트웨어, 버전 등 메타정보를 수집
> - `/api/` 경로 접근: REST API 엔드포인트 탐색으로 애플리케이션 구조를 파악
> - `dig ANY`: 대상 호스트의 DNS 레코드를 모두 조회하여 관련 도메인/서브도메인 탐색

```bash
# 정찰 결과 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool
# 각 태스크의 실행 결과(stdout, exit_code)가 기록되어 있다
```

## 실습 3.3: ATT&CK Navigator 활용

> **실습 목적**: ATT&CK Navigator를 사용하여 정찰에서 수집한 정보를 바탕으로 가능한 공격 경로를 매핑한다.
>
> **배우는 것**: ATT&CK Navigator의 레이어(Layer) 생성, 기법 색상 코딩, 여러 레이어 비교를 통한 커버리지 분석 방법을 이해한다.
>
> **결과 해석**: 색칠된 기법이 많을수록 해당 APT 그룹의 활동 범위가 넓다. 방어 레이어와 겹치지 않는 기법은 탐지 사각지대이다.
>
> **실전 활용**: 실무에서 Navigator는 보안 평가 보고서, 레드팀 작전 계획, SOC 탐지 커버리지 분석에 핵심적으로 사용된다.

```bash
# ATT&CK STIX 데이터 다운로드 (CLI에서 분석)
curl -s -o /tmp/attack.json \
  "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

# APT29의 사용 기법 조회
python3 << 'PYEOF'
import json

with open("/tmp/attack.json") as f:
    data = json.load(f)

# APT29 ID 찾기
apt29_id = None
for obj in data["objects"]:
    if obj.get("type") == "intrusion-set" and "APT29" in obj.get("aliases", []):
        apt29_id = obj["id"]
        print(f"APT29 ID: {apt29_id}")
        print(f"Description: {obj.get('description', '')[:300]}")
        break

# APT29가 사용하는 기법 찾기
if apt29_id:
    techniques = []
    for obj in data["objects"]:
        if obj.get("type") == "relationship" and \
           obj.get("source_ref") == apt29_id and \
           obj.get("relationship_type") == "uses":
            target_ref = obj.get("target_ref", "")
            if "attack-pattern" in target_ref:
                techniques.append(target_ref)
    
    print(f"\nAPT29 사용 기법 수: {len(techniques)}")
    
    # 기법 상세 출력 (상위 10개)
    count = 0
    for obj in data["objects"]:
        if obj.get("id") in techniques and obj.get("type") == "attack-pattern":
            ext = obj.get("external_references", [{}])
            tid = next((r["external_id"] for r in ext if "external_id" in r), "?")
            print(f"  {tid}: {obj['name']}")
            count += 1
            if count >= 10:
                break
PYEOF
# APT29의 주요 공격 기법이 ATT&CK ID와 함께 출력된다
```

> **트러블슈팅**: JSON 파일이 크므로(약 20MB) 다운로드에 시간이 걸릴 수 있다. `curl: (28) Connection timed out` 오류 시 네트워크 연결 상태를 확인하거나 로컬 캐시 파일을 사용한다.

```bash
# Navigator용 레이어 JSON 생성 (APT29 기법 하이라이팅)
python3 << 'PYEOF'
import json

with open("/tmp/attack.json") as f:
    data = json.load(f)

apt29_id = None
for obj in data["objects"]:
    if obj.get("type") == "intrusion-set" and "APT29" in obj.get("aliases", []):
        apt29_id = obj["id"]
        break

technique_ids = set()
if apt29_id:
    for obj in data["objects"]:
        if obj.get("type") == "relationship" and \
           obj.get("source_ref") == apt29_id and \
           "attack-pattern" in obj.get("target_ref", ""):
            technique_ids.add(obj["target_ref"])

# Navigator 레이어 생성
techniques = []
for obj in data["objects"]:
    if obj.get("id") in technique_ids and obj.get("type") == "attack-pattern":
        ext = obj.get("external_references", [{}])
        tid = next((r["external_id"] for r in ext if "external_id" in r), None)
        if tid:
            techniques.append({
                "techniqueID": tid,
                "color": "#ff6666",
                "comment": "APT29 사용 기법",
                "enabled": True
            })

layer = {
    "name": "APT29 Coverage",
    "versions": {"attack": "14", "navigator": "4.9.1", "layer": "4.5"},
    "domain": "enterprise-attack",
    "description": "APT29 (Cozy Bear) 사용 기법 매핑",
    "techniques": techniques
}

with open("/tmp/apt29_layer.json", "w") as f:
    json.dump(layer, f, indent=2)

print(f"Navigator 레이어 생성 완료: {len(techniques)}개 기법 매핑")
print(f"파일: /tmp/apt29_layer.json")
PYEOF
# Navigator에서 "Open Existing Layer" > "Upload from local" 로 이 파일을 업로드하면
# APT29의 공격 기법이 빨간색으로 하이라이팅된 매트릭스를 볼 수 있다
```

## 실습 3.4: 방어자 관점 — IPS 정찰 탐지 확인

> **실습 목적**: 공격자의 정찰 활동이 방어 시스템(Suricata IPS)에서 어떻게 탐지되는지 확인한다. 공격자와 방어자 양쪽 관점을 동시에 경험한다.
>
> **배우는 것**: Suricata 경보 로그 분석, nmap 스캔 탐지 시그니처, 정찰 행위의 네트워크 특성을 이해한다.
>
> **결과 해석**: `ET SCAN` 카테고리의 경보가 발생하면 포트 스캔이 탐지된 것이다. 경보가 없으면 Suricata 룰셋에 해당 패턴이 없거나 IPS가 비활성화된 상태이다.
>
> **실전 활용**: 실제 SOC에서는 정찰 탐지가 공격의 초기 경고 신호이다. 정찰 경보 분석 능력은 위협 헌팅의 기본이다.

```bash
# secu 서버의 Suricata 경보 확인 (직전 정찰에 대한 탐지)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "sudo tail -30 /var/log/suricata/fast.log 2>/dev/null || echo No Suricata logs",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -m json.tool
# nmap 스캔에 의한 ET SCAN 경보가 기록되어 있을 수 있다
```

```bash
# Wazuh SIEM에서 정찰 관련 경보 확인
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "sudo cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -5 | python3 -m json.tool 2>/dev/null || echo No Wazuh alerts",
    "subagent_url": "http://10.20.30.100:8002"
  }' | python3 -m json.tool
# Wazuh가 수집한 보안 경보 중 스캔 관련 항목을 확인한다
```

> **트러블슈팅**: Suricata 로그가 비어 있으면 `sudo systemctl status suricata`로 IPS 상태를 확인한다. Wazuh 경보가 없으면 `sudo systemctl status wazuh-manager`로 SIEM 상태를 확인한다.

---

# Part 4: OpsClaw APT 시뮬레이션 프로젝트 설계 (40분)

## 4.1 APT 시뮬레이션 프로젝트 설계 방법론

실제 APT 그룹의 TTP를 기반으로 시뮬레이션 프로젝트를 설계하는 체계적 방법론을 학습한다.

### 설계 프로세스

```
1. 위협 모델링    → 대상 조직에 가장 관련된 APT 그룹 선정
2. TTP 매핑       → 선정된 그룹의 ATT&CK 기법 목록화
3. 환경 매핑      → 실습 환경에서 구현 가능한 기법 필터링
4. 태스크 설계    → 각 기법을 OpsClaw 태스크로 변환
5. 위험도 분류    → low/medium/high/critical 분류
6. 실행 계획      → 태스크 실행 순서와 의존성 정의
7. 검증 계획      → 각 태스크의 성공/탐지 기준 정의
```

### 위험도 분류 기준

| 위험도 | 기준 | 예시 | OpsClaw 동작 |
|--------|------|------|-------------|
| low | 읽기 전용, 비파괴적 | 포트 스캔, 정보 조회 | 즉시 실행 |
| medium | 설정 변경, 일시적 영향 | 파일 생성, 서비스 상태 변경 | 즉시 실행 |
| high | 서비스 중단 가능성 | 방화벽 규칙 변경, 프로세스 종료 | 경고 후 실행 |
| critical | 데이터 손실, 복구 어려움 | 파일 삭제, 디스크 와이프 | dry_run 강제, 사용자 확인 필수 |

## 4.2 APT29 에뮬레이션 시나리오 설계

> **실습 목적**: 실제 APT29 그룹의 공격 TTP를 기반으로 5단계 시뮬레이션 시나리오를 설계하고, OpsClaw 프로젝트로 구현한다.
>
> **배우는 것**: 위협 모델링에서 실행 계획까지의 전체 프로세스, 각 단계의 위험도 분류 방법, OpsClaw execute-plan의 고급 사용법을 이해한다.
>
> **결과 해석**: 모든 태스크의 exit_code가 0이면 시뮬레이션이 성공한 것이다. 각 단계에서 수집한 정보가 다음 단계의 입력이 된다.
>
> **실전 활용**: 실제 레드팀 운영에서 APT 에뮬레이션 계획서는 고객 승인 문서의 핵심 구성요소이다. 체계적 시나리오 설계가 전문성의 척도이다.

```bash
# APT29 에뮬레이션 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "apt29-emulation-week01",
    "request_text": "APT29 에뮬레이션: 정찰→초기접근→실행→지속성→발견 5단계 시뮬레이션",
    "master_mode": "external"
  }' | python3 -m json.tool
# 반환된 프로젝트 ID를 APT29_PROJECT_ID로 설정
```

```bash
export APT29_PROJECT_ID="반환된-프로젝트-ID"

# Stage 전환
curl -s -X POST http://localhost:8000/projects/$APT29_PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

curl -s -X POST http://localhost:8000/projects/$APT29_PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# APT29 에뮬레이션 5단계 실행
curl -s -X POST http://localhost:8000/projects/$APT29_PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[RECON] 대상 서버 정찰\" && nmap -sV -p 22,80,443,3000,8080 10.20.30.80 2>/dev/null | grep -E \"open|filtered\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[INITIAL ACCESS] 웹 서비스 접근 시도\" && curl -s -w \"\\nHTTP_CODE: %{http_code}\\n\" http://10.20.30.80:3000/ | tail -5",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"[EXECUTION] 명령 실행 확인\" && whoami && id && hostname",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"[PERSISTENCE CHECK] 지속성 메커니즘 탐색\" && crontab -l 2>/dev/null; ls -la /etc/cron.d/ 2>/dev/null; systemctl list-unit-files --state=enabled 2>/dev/null | head -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "echo \"[DISCOVERY] 환경 정보 수집\" && cat /etc/passwd | grep -v nologin | grep -v false && ip addr show 2>/dev/null | grep inet && ps aux --sort=-rss | head -10",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 5단계의 에뮬레이션 태스크가 순차 실행된다
```

> **명령어 해설**:
> - order 1 (정찰): 대상 서버의 주요 포트 상태를 확인하여 서비스 맵을 작성
> - order 2 (초기 접근): 웹 서비스에 직접 접근하여 응답 상태와 기술 스택 확인
> - order 3 (실행): 대상 서버에서 기본 명령을 실행하여 현재 권한 확인
> - order 4 (지속성 점검): 기존 스케줄 작업과 자동 실행 서비스를 조사
> - order 5 (발견): 사용자 계정, 네트워크 구성, 실행 중 프로세스를 파악

## 4.3 결과 분석 및 PoW 확인

```bash
# 에뮬레이션 결과 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$APT29_PROJECT_ID/evidence/summary \
  | python3 -m json.tool
# 5단계 각각의 실행 결과와 수집된 정보가 evidence로 기록되어 있다
```

```bash
# PoW 블록 확인 — 모든 태스크가 블록체인에 기록됨
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?project_id=$APT29_PROJECT_ID" \
  | python3 -m json.tool
# 각 태스크마다 PoW 블록이 생성되어 실행 증거가 암호학적으로 보장된다
```

```bash
# 완료 보고서 작성
curl -s -X POST http://localhost:8000/projects/$APT29_PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "APT29 에뮬레이션 5단계 시뮬레이션 완료",
    "outcome": "success",
    "work_details": [
      "1단계 정찰: web 서버 포트 스캔 및 서비스 식별 완료",
      "2단계 초기접근: JuiceShop 웹 서비스 접근 확인",
      "3단계 실행: 대상 서버 명령 실행 및 권한 확인",
      "4단계 지속성: 기존 스케줄 작업 및 서비스 조사",
      "5단계 발견: 사용자, 네트워크, 프로세스 정보 수집"
    ]
  }' | python3 -m json.tool
# 프로젝트가 closed 상태로 전환된다
```

## 4.4 킬체인 단계별 방어 매트릭스 작성

이론에서 학습한 킬체인 방어 원칙을 실습 환경에 매핑한다.

```
실습 환경 방어 매트릭스:

+--------------+------------------------+--------------+
| 킬체인 단계    | 현재 방어 수단           | 담당 서버      |
+--------------┼------------------------┼--------------+
| 1. 정찰       | Suricata IPS (스캔 탐지) | secu         |
| 2. 무기화     | (직접 방어 불가)          | -            |
| 3. 전달       | BunkerWeb WAF           | web          |
| 4. 익스플로잇  | WAF 룰, 패치 관리        | web          |
| 5. 설치       | Wazuh FIM              | siem         |
| 6. C2        | nftables 방화벽          | secu         |
| 7. 목표 달성   | 네트워크 세그멘테이션      | secu         |
+--------------+------------------------+--------------+
```

---

## 실제 APT 사례 심층 분석 (30분)

### 사례 1: SolarWinds 공급망 공격 (2020)

APT29(Cozy Bear)가 수행한 것으로 추정되는 역사상 최대 규모의 공급망 공격이다.

**킬체인 매핑**:

| 단계 | 행위 | ATT&CK ID | 상세 |
|------|------|-----------|------|
| 정찰 | SolarWinds 빌드 시스템 구조 파악 | T1593 | Orion 빌드 파이프라인 분석, 개발자 계정 탈취 |
| 무기화 | SUNBURST 백도어 코드 제작 | T1587.001 | SolarWinds.Orion.Core.BusinessLayer.dll에 삽입 |
| 전달 | 정상 소프트웨어 업데이트로 배포 | T1195.002 | Orion v2019.4~2020.2.1 업데이트에 포함 |
| 익스플로잇 | DLL 사이드로딩으로 실행 | T1574.002 | Orion 서비스 기동 시 자동 실행 |
| 설치 | 레지스트리/파일 기반 지속성 | T1547.001 | 정상 서비스 내 동작하므로 별도 설치 불필요 |
| C2 | DNS 기반 은닉 통신 | T1071.004 | avsvmcloud[.]com 도메인, 정상 트래픽으로 위장 |
| 목표 달성 | 미국 정부기관 데이터 유출 | T1041 | Treasury, Commerce, DHS 등 18,000개 조직 영향 |

**핵심 교훈**:
- 공급망 공격은 신뢰 관계를 악용하므로 전통적 방어 모델로 탐지가 극히 어렵다
- SUNBURST는 2주간 잠복 후 활동을 시작하여 샌드박스 분석을 회피했다
- DNS C2는 정상 트래픽과 구분이 어려워 네트워크 모니터링만으로 탐지 불가
- 발견 과정: FireEye가 자체 레드팀 도구 유출을 조사하다 발견

### 사례 2: APT41 이중 활동 (국가 임무 + 금전 목적)

APT41은 국가 지원 사이버 첩보 활동과 금전 목적 범죄를 동시에 수행하는 독특한 그룹이다.

| 활동 유형 | 대상 | 기법 | ATT&CK ID |
|----------|------|------|-----------|
| 국가 임무 | 통신, 의료, 반도체 | 공급망 공격, 제로데이 | T1195, T1190 |
| 금전 목적 | 게임 회사, 암호화폐 | 랜섬웨어, 가상화폐 채굴 | T1486, T1496 |

### 사례 3: Lazarus SWIFT 공격 (2016)

북한 Lazarus 그룹이 방글라데시 중앙은행에서 8,100만 달러를 탈취한 사건이다.

```
킬체인 매핑:
1. 정찰: SWIFT 네트워크 구조 및 은행 직원 정보 수집
2. 무기화: 커스텀 RAT 및 SWIFT 메시지 위조 도구 제작
3. 전달: 스피어 피싱 이메일 (구직 제안 위장)
4. 익스플로잇: 직원 워크스테이션 장악
5. 설치: 다중 백도어 설치, SWIFT 시스템 접근
6. C2: 암호화된 HTTP 통신
7. 목표 달성: 위조된 SWIFT 메시지로 9.51억 달러 이체 시도
   → 오타 발견으로 대부분 차단, 8,100만 달러 유출
```

### 토론 주제

1. **공급망 신뢰**: SolarWinds 사례에서 "신뢰할 수 있는 소프트웨어"를 어떻게 검증할 수 있었을까?
2. **탐지 시점**: 각 사례에서 킬체인의 어느 단계에서 탐지가 가장 효과적이었을까?
3. **방어 투자**: 제한된 예산으로 킬체인 7단계 중 어디에 가장 먼저 투자해야 하는가?
4. **AI 활용**: 자율보안시스템이 SolarWinds 공급망 공격을 탐지할 수 있었을까? 어떤 조건에서?

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] APT의 세 가지 핵심 특성(Advanced, Persistent, Threat)을 설명할 수 있는가?
- [ ] 킬체인 7단계를 순서대로 나열하고 각 단계의 방어 수단을 말할 수 있는가?
- [ ] ATT&CK의 4계층 구조(Tactic-Technique-Sub-technique-Procedure)를 설명할 수 있는가?
- [ ] ATT&CK Navigator에서 특정 APT 그룹의 기법을 시각화할 수 있는가?
- [ ] OpsClaw에서 APT 시뮬레이션 프로젝트를 생성하고 execute-plan을 실행할 수 있는가?
- [ ] 정찰 단계의 수동/능동 정찰 차이를 설명할 수 있는가?
- [ ] SolarWinds 사례를 킬체인 7단계에 완전히 매핑할 수 있는가?
- [ ] ATT&CK 기법 ID(T번호)와 전술 ID(TA번호)의 차이를 이해하는가?
- [ ] PoW 블록이 태스크 실행의 증거로 어떻게 기능하는지 설명할 수 있는가?
- [ ] 킬체인 모델의 한계점과 ATT&CK의 보완 관계를 설명할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** APT의 "Persistent(지속적)"가 의미하는 바는?
- (a) 빠른 공격  (b) **장기간 은밀하게 네트워크에 잠복하며 활동**  (c) 대규모 DDoS  (d) 자동화된 공격

**Q2.** 사이버 킬체인에서 방어자가 직접 관찰할 수 없는 유일한 단계는?
- (a) 정찰  (b) **무기화(Weaponization)**  (c) 전달  (d) C2

**Q3.** MITRE ATT&CK에서 T1566.001이 의미하는 것은?
- (a) 포트 스캔  (b) DNS 터널링  (c) **스피어 피싱 첨부파일**  (d) 권한 상승

**Q4.** ATT&CK의 전술(Tactic)과 기법(Technique)의 관계는?
- (a) 기법이 전술을 포함  (b) **전술은 "왜"를, 기법은 "무엇을"을 나타냄**  (c) 동일한 개념  (d) 기법이 상위 분류

**Q5.** 킬체인에서 "3단계 전달(Delivery)"에 해당하지 않는 것은?
- (a) 스피어 피싱  (b) 워터링홀  (c) USB 미디어  (d) **버퍼 오버플로우**

**Q6.** SolarWinds 공격에서 C2 통신에 사용된 프로토콜은?
- (a) HTTPS  (b) ICMP  (c) **DNS**  (d) SMTP

**Q7.** OpsClaw에서 risk_level이 "critical"인 태스크의 동작은?
- (a) 즉시 실행  (b) 경고 후 실행  (c) **dry_run 강제, 사용자 확인 필수**  (d) 실행 거부

**Q8.** ATT&CK Navigator의 주요 활용 용도가 아닌 것은?
- (a) APT 그룹 기법 시각화  (b) 탐지 커버리지 분석  (c) **멀웨어 자동 분석**  (d) 레드팀 작전 계획

**Q9.** 능동 정찰(Active Reconnaissance)에 해당하는 것은?
- (a) WHOIS 조회  (b) 소셜 미디어 검색  (c) **포트 스캔 (nmap)**  (d) 뉴스 기사 분석

**Q10.** 킬체인 모델의 한계점으로 올바른 것은?
- (a) 너무 세분화되어 있다  (b) **내부 위협을 모델링하지 못한다**  (c) 방어 도구를 포함하지 않는다  (d) 기법을 분류하지 않는다

**정답:** Q1:b, Q2:b, Q3:c, Q4:b, Q5:d, Q6:c, Q7:c, Q8:c, Q9:c, Q10:b

---

## 과제

### 과제 1: APT 그룹 프로파일 작성 (필수)
APT28, APT41, Lazarus 중 하나를 선택하여 다음을 작성하라:
- 그룹 개요 (배후, 동기, 주요 대상)
- 사용하는 ATT&CK 기법 상위 10개 목록 (ID, 이름, 설명)
- 대표 공격 사례 1건을 킬체인 7단계에 매핑
- Navigator 레이어 JSON 파일 생성 (보너스)

### 과제 2: 방어 커버리지 분석 (필수)
실습에서 사용한 OpsClaw 환경의 방어 매트릭스를 기반으로:
- 각 킬체인 단계별 탐지 가능 여부를 분석
- 탐지 사각지대(탐지할 수 없는 기법) 3가지 이상 식별
- 각 사각지대에 대한 보완 방안 제시

### 과제 3: OpsClaw 정찰 시나리오 확장 (선택)
실습에서 수행한 정찰을 확장하여:
- 5가지 이상의 정찰 기법을 OpsClaw execute-plan으로 구현
- 각 기법의 ATT&CK ID를 매핑
- 정찰 결과를 종합하여 대상 서버의 공격 표면 보고서 작성

---

## 다음 주 예고

**Week 02: 다단계 침투 — Initial Access, Execution, Persistence**
- 실제 웹 취약점을 활용한 초기 접근(Initial Access) 실습
- 원격 코드 실행(RCE) 기법과 방어
- 다양한 지속성(Persistence) 메커니즘 구현 및 탐지
- OpsClaw를 활용한 다단계 침투 시뮬레이션 자동화
