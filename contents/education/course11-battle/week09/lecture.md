# Week 09: 인시던트 대응 -- NIST IR 프레임워크

## 학습 목표
- NIST SP 800-61 인시던트 대응 프레임워크의 4단계(준비, 탐지/분석, 봉쇄/근절/복구, 사후 활동)를 체계적으로 이해한다
- 인시던트 발생 시 네트워크 격리와 호스트 봉쇄를 nftables, ip 명령으로 즉시 수행할 수 있다
- 디지털 증거의 무결성을 보존하기 위한 수집 절차(메모리 덤프, 디스크 이미지, 로그 보존)를 수행할 수 있다
- 시스템 복구 절차를 계획하고 백업에서 서비스를 복원하는 과정을 실습한다
- 사후 분석(Post-Incident Analysis)을 통해 타임라인을 재구성하고 교훈 보고서를 작성할 수 있다
- MITRE ATT&CK 매핑을 활용하여 공격자의 TTP(전술, 기법, 절차)를 분류하고 문서화할 수 있다
- 공방전 환경에서 Blue Team의 인시던트 대응 역량을 강화하기 위한 전략을 수립할 수 있다

## 전제 조건
- 리눅스 기본 명령어 및 SSH 접속 숙달
- nftables 방화벽 규칙 기본 이해 (Week 05~06 복습)
- 로그 분석 기초 (journalctl, /var/log 구조) 이해
- Week 07~08의 IDS/IPS, 로그 모니터링 내용 복습 완료

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | NIST IR 프레임워크 이론 + 인시던트 분류 | 강의 |
| 0:40-1:10 | 격리/봉쇄 전략 + 증거 수집 원칙 | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 네트워크 격리 + 호스트 봉쇄 실습 | 실습 |
| 2:00-2:30 | 증거 보존 + 메모리/디스크 포렌식 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 복구 절차 + 사후 분석 실습 | 실습 |
| 3:10-3:40 | 타임라인 재구성 + 퀴즈 + 과제 안내 | 토론/퀴즈 |

---

# Part 1: NIST IR 프레임워크 이론 (40분)

## 1.1 인시던트 대응(Incident Response)이란?

인시던트 대응은 보안 사고가 발생했을 때 피해를 최소화하고, 원인을 규명하며, 재발을 방지하기 위한 체계적인 활동이다. 단순히 "문제를 해결하는 것"이 아니라 준비-탐지-봉쇄-복구-교훈의 순환 과정을 통해 조직의 보안 성숙도를 높이는 것이 핵심이다.

**MITRE ATT&CK 매핑:**
```
인시던트 대응은 공격자의 전체 Kill Chain에 대응한다:
  +-- TA0043 Reconnaissance  → 탐지 단계에서 식별
  +-- TA0001 Initial Access  → 봉쇄 단계에서 차단
  +-- TA0003 Persistence     → 근절 단계에서 제거
  +-- TA0005 Defense Evasion → 분석 단계에서 추적
  +-- TA0008 Lateral Movement → 격리 단계에서 차단
  +-- TA0010 Exfiltration    → 네트워크 봉쇄로 차단
  +-- TA0040 Impact          → 복구 단계에서 대응
```

### NIST SP 800-61 Revision 2 개요

NIST(National Institute of Standards and Technology)의 SP 800-61은 인시던트 대응의 사실상 표준 프레임워크이다. 2012년에 Revision 2가 발표되었으며, 전 세계 조직이 이를 기반으로 IR 프로세스를 구축한다.

```
+-------------------------------------------------------------+
|                    NIST IR 라이프사이클                        |
|                                                               |
|  +----------+   +--------------+   +---------------------+  |
|  | 1. 준비   |-->| 2. 탐지/분석  |-->| 3. 봉쇄/근절/복구    |  |
|  |Preparation|   |Detection &   |   |Containment,         |  |
|  |           |   |Analysis      |   |Eradication, Recovery|  |
|  +----------+   +--------------+   +----------+----------+  |
|       ↑                                         |             |
|       |         +--------------+                |             |
|       +---------| 4. 사후 활동  |<---------------+             |
|                 |Post-Incident |                              |
|                 |Activity      |                              |
|                 +--------------+                              |
+-------------------------------------------------------------+
```

### 4단계 상세

| 단계 | 핵심 활동 | 산출물 | 공방전 대응 |
|------|---------|--------|-----------|
| **1. 준비** | IR 팀 구성, 도구 준비, 절차 문서화, 훈련 | IR 플레이북, 연락처, 도구 키트 | Week 10 하드닝 |
| **2. 탐지/분석** | 이상 징후 식별, 로그 분석, 영향 범위 판단 | 인시던트 티켓, 초기 분석 보고서 | 실시간 모니터링 |
| **3. 봉쇄/근절/복구** | 격리, 악성코드 제거, 패치, 서비스 복원 | 봉쇄 기록, 복구 검증 결과 | 실전 대응 |
| **4. 사후 활동** | 타임라인 재구성, 교훈 도출, 프로세스 개선 | 사후 분석 보고서, 개선 계획 | Week 15 보고서 |

### NIST와 SANS 프레임워크 비교

두 프레임워크 모두 널리 사용되며, 본질적으로 유사하다. NIST는 4단계, SANS는 6단계로 나누지만 활동 내용은 대동소이하다.

| NIST 단계 | SANS 단계 | 차이점 |
|-----------|-----------|--------|
| 1. 준비 | 1. 준비 | 동일 |
| 2. 탐지/분석 | 2. 식별 | SANS는 "식별"로 명명 |
| 3. 봉쇄/근절/복구 | 3. 봉쇄 / 4. 근절 / 5. 복구 | NIST는 하나로 통합, SANS는 3단계로 분리 |
| 4. 사후 활동 | 6. 교훈 | SANS는 "교훈"으로 명명 |

## 1.2 인시던트 분류와 심각도 등급

### 인시던트 유형 분류

| 유형 | 설명 | 예시 | ATT&CK 전술 |
|------|------|------|-------------|
| **무단 접근** | 권한 없는 시스템 접근 | SSH 브루트포스 성공, 웹셸 업로드 | TA0001, TA0003 |
| **악성코드** | 멀웨어 감염 | 랜섬웨어, 트로이목마, 코인마이너 | TA0002, TA0003 |
| **서비스 거부** | 가용성 침해 | DDoS, 리소스 고갈 | TA0040 |
| **정보 유출** | 데이터 무단 반출 | DB 덤프, 파일 유출 | TA0009, TA0010 |
| **내부자 위협** | 내부 사용자의 악의적 행위 | 권한 남용, 데이터 삭제 | TA0006, TA0040 |
| **횡적 이동** | 내부 네트워크 확산 | Pass-the-Hash, SSH 피벗 | TA0008 |

### 심각도 등급 체계

```
+----------------------------------------------------------+
| 심각도     | 기준                    | 대응 시간 | 예시    |
+----------------------------------------------------------+
| Critical   | 핵심 시스템 침해,       | 즉시      | 랜섬웨어|
| (긴급)     | 데이터 대량 유출        | (15분내)  | 전파중  |
+----------------------------------------------------------+
| High       | 서버 침투 성공,         | 1시간내   | 웹셸   |
| (높음)     | 권한 상승               |           | 발견   |
+----------------------------------------------------------+
| Medium     | 의심스러운 활동 탐지,   | 4시간내   | 다수의 |
| (중간)     | 정책 위반               |           | 로그인 |
|            |                         |           | 실패   |
+----------------------------------------------------------+
| Low        | 정보성 이벤트,          | 24시간내  | 포트   |
| (낮음)     | 단일 실패 시도          |           | 스캔   |
+----------------------------------------------------------+
```

### 인시던트 분류 의사결정 흐름

```
이벤트 발생
    |
    +-- 보안 이벤트인가?
    |   +-- 아니오 → 일반 운영 이벤트 (IT Ops 처리)
    |   +-- 예 --> 보안 인시던트인가?
    |               +-- 아니오 → 보안 이벤트 (모니터링 유지)
    |               +-- 예 --> 심각도 분류
    |                           +-- Critical/High → IR 팀 즉시 소집
    |                           +-- Medium → IR 팀 알림, 분석 시작
    |                           +-- Low → 기록, 모니터링 강화
    |
    +-- 오탐(False Positive)인가?
        +-- 예 → 규칙 튜닝, 기록
        +-- 아니오 → 인시던트 확정, 티켓 생성
```

## 1.3 인시던트 대응 팀 구성

### CSIRT(Computer Security Incident Response Team) 역할

| 역할 | 책임 | 공방전 매핑 |
|------|------|-----------|
| **IR 리더** | 전체 대응 지휘, 의사결정 | Blue Team 리더 |
| **분석가** | 로그 분석, 악성코드 분석 | 로그 분석 담당 |
| **포렌식** | 증거 수집, 무결성 보존 | 증거 수집 담당 |
| **네트워크** | 트래픽 분석, 격리 실행 | 방화벽 운용 담당 |
| **시스템** | 서버 점검, 패치, 복구 | 시스템 관리 담당 |
| **커뮤니케이션** | 경영진/외부 소통 | 보고서 담당 |

### 공방전에서의 IR 프로세스

```
[공방전 시나리오]

Red Team 공격 시작
      |
      ▼
Blue Team 탐지 ← IDS 알림, 로그 이상
      |
      ▼
초기 분석 (5분) ← 어떤 공격인가? 영향 범위는?
      |
      ▼
봉쇄 결정 (2분) ← 네트워크 격리? 프로세스 종료?
      |
      ▼
봉쇄 실행 (즉시) ← nftables 차단, kill 프로세스
      |
      ▼
근절 (10분) ← 백도어 제거, 패치 적용
      |
      ▼
복구 (5분) ← 서비스 재시작, 정상 확인
      |
      ▼
증거 보존 ← 로그 백업, 스크린샷
```

## 1.4 증거 수집의 원칙

### 증거 수집 순서 (RFC 3227 -- 휘발성 순서)

디지털 증거는 휘발성이 높은 것부터 수집해야 한다. 시간이 지나면 사라지는 데이터를 먼저 확보하는 것이 핵심이다.

| 순서 | 대상 | 휘발성 | 수집 방법 | 예시 |
|------|------|--------|---------|------|
| 1 | CPU 레지스터/캐시 | 나노초 | 실시간 덤프 | (일반적으로 불가) |
| 2 | 메모리 (RAM) | 전원 차단 시 소실 | `dd`, `avml`, `LiME` | 프로세스 목록, 네트워크 연결 |
| 3 | 네트워크 상태 | 연결 종료 시 소실 | `ss`, `netstat` | 현재 연결, 라우팅 |
| 4 | 프로세스 상태 | 프로세스 종료 시 소실 | `ps`, `/proc` | 실행 중인 악성 프로세스 |
| 5 | 디스크 (임시 파일) | 재부팅/정리 시 소실 | `cp`, `tar` | /tmp, /var/tmp |
| 6 | 디스크 (로그) | 로테이션 시 덮어쓰기 | `cp`, `rsync` | /var/log/* |
| 7 | 디스크 (설정/데이터) | 비교적 안정 | `dd`, `tar` | /etc/*, 데이터베이스 |
| 8 | 외부 로그 | SIEM에 보존 | API 조회 | Wazuh 알림, 방화벽 로그 |

### 증거 무결성 보장 (Chain of Custody)

```
[증거 수집 프로세스]

1. 해시값 계산 (수집 전)
   sha256sum /var/log/auth.log → HASH_BEFORE

2. 증거 복사
   cp -a /var/log/auth.log /evidence/auth.log

3. 해시값 검증 (수집 후)
   sha256sum /evidence/auth.log → HASH_AFTER

4. 해시 비교
   HASH_BEFORE == HASH_AFTER → 무결성 확인

5. Chain of Custody 기록
   날짜/시간, 수집자, 위치, 해시값 → 증거 관리 대장
```

### Chain of Custody 양식

| 항목 | 기록 내용 | 예시 |
|------|---------|------|
| 증거 ID | 고유 식별자 | EVD-2026-001 |
| 수집 일시 | 정확한 타임스탬프 | 2026-04-03 14:35:22 KST |
| 수집자 | 담당자 이름/ID | analyst-kim |
| 수집 위치 | 호스트, 경로 | web:10.20.30.80:/var/log/auth.log |
| 수집 방법 | 사용한 도구/명령 | SSH + cp -a |
| 해시 (원본) | SHA-256 | a1b2c3d4e5f6... |
| 해시 (사본) | SHA-256 | a1b2c3d4e5f6... (동일 확인) |
| 보관 위치 | 증거 저장소 경로 | /evidence/IR-2026-001/ |
| 접근 기록 | 이후 접근한 사람 | analyst-park (2026-04-03 15:00) |

## 1.5 봉쇄 전략

### 봉쇄 유형 비교

| 전략 | 설명 | 장점 | 단점 | 적용 시나리오 |
|------|------|------|------|-------------|
| **네트워크 격리** | 감염 호스트의 네트워크 차단 | 확산 즉시 차단 | 서비스 중단 | 웜, 랜섬웨어 |
| **프로세스 종료** | 악성 프로세스만 kill | 서비스 유지 | 재실행 가능 | 코인마이너 |
| **계정 비활성화** | 침해 계정 잠금 | 추가 접근 차단 | 업무 영향 | 계정 탈취 |
| **DNS 싱크홀** | C2 도메인을 내부로 리다이렉트 | 은밀한 차단 | 우회 가능 | C2 통신 차단 |
| **VLAN 격리** | 별도 VLAN으로 이동 | 관찰 가능 유지 | 복잡한 설정 | 고급 APT |

### 봉쇄 의사결정 흐름도

```
인시던트 탐지
      |
      +-- 확산 중인가? --(예)--> 즉시 네트워크 격리
      |                            |
      |                            +-- 감염 범위 확인
      |                                    |
      |                                    +-- 단일 호스트 → 호스트 격리
      |                                    +-- 다수 호스트 → 세그먼트 격리
      |
      +-- 확산 아닌가? --(아니오)--> 프로세스/계정 수준 봉쇄
      |
      +-- 불확실한가? --> 일단 격리 후 분석 (안전 우선 원칙)
```

## 1.6 복구 전략

### 복구 우선순위 결정

```
[복구 우선순위 매트릭스]

           | 높은 영향도       | 낮은 영향도
-----------┼------------------┼------------------
높은       | 1순위: 즉시 복구  | 2순위: 빠른 복구
가용성     | (핵심 서비스)     | (보조 서비스)
요구       | 예: 웹 서버, DB   | 예: 모니터링
-----------┼------------------┼------------------
낮은       | 3순위: 계획 복구  | 4순위: 여유 복구
가용성     | (중요 데이터)     | (비핵심 시스템)
요구       | 예: 로그 서버     | 예: 테스트 환경
```

### 복구 절차 체크리스트

```
□ 1. 근절 확인 — 악성코드/백도어가 완전히 제거되었는가
□ 2. 패치 적용 — 침입에 사용된 취약점이 패치되었는가
□ 3. 자격증명 변경 — 모든 침해 계정의 비밀번호가 변경되었는가
□ 4. 백업 복원 — 감염 전 시점의 백업에서 복원하는가
□ 5. 서비스 재시작 — 서비스가 정상적으로 기동되는가
□ 6. 기능 검증 — 핵심 기능이 모두 동작하는가
□ 7. 모니터링 강화 — 재감염 징후를 감시하는 룰이 추가되었는가
□ 8. 단계적 복원 — 내부 네트워크부터 외부 개방 순서로 복원하는가
```

---

# Part 2: 격리/봉쇄 전략과 증거 수집 원칙 (30분)

## 2.1 네트워크 격리 기법

### nftables를 이용한 즉시 격리

네트워크 격리는 감염된 호스트가 다른 시스템으로 공격을 확산하는 것을 차단하는 가장 빠른 방법이다.

```
[격리 전]
공격자 --> 감염 호스트 --> 내부 서버들
                 |
                 +--> 데이터 유출 (C2 서버로)

[격리 후]
공격자 --X-- 감염 호스트 --X-- 내부 서버들
                 |
                 +--X-- 데이터 유출 차단
                 |
            관리자만 접근 가능 (SSH)
```

### 격리 수준 비교

| 수준 | 방법 | 허용 트래픽 | 사용 시나리오 |
|------|------|-----------|-------------|
| **완전 격리** | 모든 트래픽 차단 | 없음 | 랜섬웨어, 웜 |
| **관리 격리** | 관리 포트만 허용 | SSH(22) | 분석 필요 시 |
| **선택적 격리** | 특정 IP/포트만 차단 | 대부분 허용 | C2 차단 |
| **모니터링 격리** | 차단 없이 관찰 | 전체 허용 | APT 추적 |

## 2.2 호스트 봉쇄 기법

### 프로세스 수준 봉쇄

악성 프로세스를 식별하고 종료하는 것은 호스트 수준 봉쇄의 핵심이다.

```
[의심 프로세스 식별 흐름]

1. 비정상 프로세스 확인
   ps auxf | grep -v "^\[" | sort -k3 -rn | head -20

2. 네트워크 연결 확인
   ss -tnp | grep <PID>

3. 프로세스 실행 경로 확인
   ls -la /proc/<PID>/exe
   cat /proc/<PID>/cmdline | tr '\0' ' '

4. 프로세스 파일 디스크립터 확인
   ls -la /proc/<PID>/fd

5. 의사결정: 악성인가?
   +-- 예 → kill -9 <PID>
   +-- 불확실 → 메모리 덤프 후 분석
```

### 계정 수준 봉쇄

| 조치 | 명령어 | 효과 | 복원 |
|------|--------|------|------|
| 계정 잠금 | `passwd -l <user>` | 로그인 차단 | `passwd -u <user>` |
| 셸 변경 | `chsh -s /sbin/nologin <user>` | 대화형 접근 차단 | `chsh -s /bin/bash <user>` |
| SSH 키 제거 | `> ~/.ssh/authorized_keys` | 키 기반 접근 차단 | 키 재등록 |
| 세션 종료 | `pkill -u <user>` | 현재 세션 종료 | - |
| sudo 제거 | `deluser <user> sudo` | 권한 상승 차단 | `adduser <user> sudo` |

## 2.3 사후 분석 방법론

### 타임라인 재구성

사후 분석의 핵심은 이벤트의 시간순 재구성이다. 여러 소스의 로그를 통합하여 공격자의 행위를 시간 순서로 나열한다.

```
[타임라인 예시]

14:30:00  secu   nftables  10.20.30.80 → 외부IP:4444 허용 (outbound)
14:30:05  web    auth.log  Failed password for root (10회)
14:30:30  web    auth.log  Accepted password for www-data
14:30:45  web    apache    POST /upload.php 200 (웹셸 업로드)
14:31:00  siem   wazuh     Alert: New user created on web
14:31:10  web    auth.log  New user 'backdoor' added
14:31:30  web    ss        ESTABLISHED 10.20.30.80:4444 → 외부IP:9999
14:32:00  secu   suricata  ET TROJAN Reverse Shell Detected
14:32:05  secu   nftables  차단: 10.20.30.80 → 외부IP:9999 DROP
14:32:10  web    syslog    Process killed: PID 12345 (/tmp/.hidden)
```

### 교훈 도출 프레임워크

| 질문 | 목적 | 개선 영역 |
|------|------|---------|
| 공격은 언제 시작되었는가? | 탐지 지연 시간 측정 | 모니터링 강화 |
| 어떤 취약점이 이용되었는가? | 패치/설정 개선 | 취약점 관리 |
| 탐지는 언제, 어떻게 되었는가? | 모니터링 개선 | IDS 룰 튜닝 |
| 봉쇄까지 얼마나 걸렸는가? | 대응 시간 단축 | 자동화 |
| 어떤 데이터가 유출되었는가? | 데이터 보호 강화 | DLP |
| 복구는 얼마나 걸렸는가? | 복구 절차 최적화 | 백업/DR |
| 무엇을 개선해야 하는가? | 프로세스/도구 업그레이드 | 전반적 |

---

# Part 3: 네트워크 격리 + 증거 보존 실습 (40분)

## 실습 3.1: nftables를 이용한 호스트 격리

### Step 1: 현재 방화벽 상태 확인 및 백업

> **실습 목적**: 인시던트 발생 시 격리 조치를 위해 현재 방화벽 규칙을 먼저 파악한다. 격리 전후 상태를 비교하기 위한 기준선(Baseline)을 확보한다.
>
> **배우는 것**: nftables 규칙 조회, 현재 정책 백업, 격리 전 상태 문서화

```bash
# secu 서버의 현재 방화벽 규칙 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "echo 1 | sudo -S nft list ruleset 2>/dev/null"
# 예상 출력:
# table inet filter {
#   chain input { ... }
#   chain forward { ... }
#   chain output { ... }
# }

# 현재 규칙 백업 (격리 전 상태 보존)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "echo 1 | sudo -S nft list ruleset > /tmp/nft_backup_before.conf 2>/dev/null"
echo "격리 전 규칙 백업 완료"

# web 서버와의 현재 연결 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "echo 1 | sudo -S ss -tn | grep 10.20.30.80"
# 예상 출력: web 서버와의 기존 TCP 연결 목록

# web 서버의 열린 포트 확인 (격리 전 기준선)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ss -tlnp 2>/dev/null | head -10"
# 예상 출력: SSH(22), HTTP(80), JuiceShop(3000), SubAgent(8002)
```

> **결과 해석**:
> - `nft list ruleset`: 현재 적용된 모든 방화벽 규칙을 표시한다
> - 백업 파일은 격리 해제 후 원래 상태로 복원할 때 사용한다
> - `ss -tn`: 현재 활성 TCP 연결을 확인하여 격리 시 영향 범위를 예측한다
>
> **실전 활용**: 격리 전에 반드시 현재 상태를 백업해야 한다. 격리 해제 시 백업 없이 복원하면 기존 규칙을 잃을 수 있다.
>
> **명령어 해설**:
> - `nft list ruleset`: 전체 nftables 규칙 출력
> - `ss -tn`: TCP 연결만 숫자 형태로 표시 (-t: TCP, -n: 숫자 표시)
> - `ss -tlnp`: LISTEN 상태의 TCP 포트와 프로세스 표시
>
> **트러블슈팅**:
> - "Error: Could not process rule: No such file or directory": nftables 테이블이 없음 → `nft add table inet filter`
> - 권한 오류: sudo 없이 실행한 경우 → `echo 1 | sudo -S` 접두사 추가

### Step 2: 감염 호스트 네트워크 격리

> **실습 목적**: web 서버(10.20.30.80)가 침해당한 시나리오에서 즉시 네트워크를 격리하여 횡적 이동과 데이터 유출을 차단한다.
>
> **배우는 것**: nftables로 특정 호스트의 inbound/outbound 트래픽을 즉시 차단하는 방법

```bash
# 시나리오: web 서버(10.20.30.80)에서 리버스 셸이 탐지됨
# 조치: secu 서버(게이트웨이)에서 web 서버의 외부 통신을 차단

# 1. web 서버의 외부 통신 차단 (C2 연결 차단)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "echo 1 | sudo -S nft add rule inet filter forward \
   ip saddr 10.20.30.80 ip daddr != 10.20.30.0/24 drop 2>/dev/null"
echo "외부 통신 차단 완료 (outbound)"

# 2. web 서버로의 외부 유입 차단 (추가 공격 차단)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "echo 1 | sudo -S nft add rule inet filter forward \
   ip daddr 10.20.30.80 ip saddr != 10.20.30.0/24 drop 2>/dev/null"
echo "외부 유입 차단 완료 (inbound)"

# 3. 격리 확인: web에서 외부 접근 테스트
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "curl -s --connect-timeout 3 http://8.8.8.8 2>/dev/null || echo '외부 접근 차단됨 (격리 성공)'"
# 예상 출력: 외부 접근 차단됨 (격리 성공)

# 4. 내부 통신은 유지 확인 (관리 목적)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ping -c 2 10.20.30.1 2>/dev/null | tail -1"
# 예상 출력: 2 packets transmitted, 2 received, 0% packet loss

# 5. 격리 상태 요약
echo "=== 격리 상태 ==="
echo "외부 → web: 차단"
echo "web → 외부: 차단"
echo "내부 → web: 허용 (관리 접근)"
echo "web → 내부: 허용 (분석 통신)"
```

> **결과 해석**:
> - 외부 통신 차단: web 서버가 C2 서버와 통신할 수 없게 된다
> - 내부 통신 유지: 관리자가 SSH로 접속하여 분석/복구를 수행할 수 있다
> - `ip daddr != 10.20.30.0/24`: 내부 네트워크 외의 모든 목적지를 차단한다
>
> **실전 활용**: 실제 인시던트에서 가장 먼저 수행하는 조치이다. 격리하지 않으면 공격자가 데이터를 유출하거나 다른 서버로 확산할 수 있다. 격리 후 분석→근절→복구 순서로 진행한다.
>
> **명령어 해설**:
> - `nft add rule inet filter forward`: forward 체인에 규칙 추가 (라우터/게이트웨이 역할)
> - `ip saddr 10.20.30.80`: 출발지가 web 서버인 패킷
> - `ip daddr != 10.20.30.0/24 drop`: 내부 대역이 아닌 목적지면 차단
>
> **트러블슈팅**:
> - 내부 통신도 차단된 경우: 규칙 순서 확인 → `nft list chain inet filter forward`
> - SSH 끊김: opsclaw에서 직접 접근하는 경우 관리 IP 예외 추가 필요

### Step 3: 격리 해제 및 원상 복구

> **실습 목적**: 인시던트 대응이 완료된 후 격리를 안전하게 해제하는 절차를 익힌다.
>
> **배우는 것**: nftables 규칙 삭제, 백업에서 복원, 단계적 격리 해제

```bash
# 격리 규칙 확인 (handle 번호 확인)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "echo 1 | sudo -S nft -a list chain inet filter forward 2>/dev/null | grep 10.20.30.80"
# 예상 출력:
# ip saddr 10.20.30.80 ip daddr != 10.20.30.0/24 drop # handle 15
# ip daddr 10.20.30.80 ip saddr != 10.20.30.0/24 drop # handle 16

# 백업에서 규칙 복원 (가장 안전한 방법)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "echo 1 | sudo -S nft flush ruleset && \
   echo 1 | sudo -S nft -f /tmp/nft_backup_before.conf 2>/dev/null"
echo "격리 해제: 원래 규칙으로 복원 완료"

# 복원 확인: 외부 통신 가능 여부
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ping -c 1 -W 2 8.8.8.8 2>/dev/null | tail -1 || echo '외부 통신 여전히 불가'"
# 예상 출력: (환경에 따라 다름)

# 복원 후 규칙 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "echo 1 | sudo -S nft list ruleset 2>/dev/null | head -20"
echo "규칙 복원 상태 확인 완료"
```

> **결과 해석**:
> - `nft flush ruleset`: 현재 모든 규칙을 삭제한다 (주의: 일시적으로 방화벽 없음 상태)
> - `nft -f`: 파일에서 규칙을 일괄 로드한다 (flush 직후 즉시 적용)
> - 단계적 해제가 이상적: 외부 inbound 먼저 허용 → 서비스 정상 확인 → outbound 허용
>
> **실전 활용**: 격리 해제는 반드시 근절이 완료된 후에 수행해야 한다. 너무 일찍 해제하면 재감염 위험이 있다. 복구 후 최소 24시간은 집중 모니터링을 수행한다.
>
> **명령어 해설**:
> - `nft -a list`: `-a` 옵션으로 handle 번호를 표시 (개별 규칙 삭제에 필요)
> - `nft delete rule inet filter forward handle <N>`: 특정 규칙만 개별 삭제
> - `nft flush ruleset`: 모든 테이블과 규칙을 한 번에 삭제
>
> **트러블슈팅**:
> - 백업 파일이 없는 경우: 수동으로 격리 규칙만 삭제 → `nft delete rule inet filter forward handle <N>`
> - flush 후 SSH 끊김: 물리 콘솔 또는 IPMI로 접근 필요 → 원격 작업 시 항상 백업 확인

## 실습 3.2: 증거 보존 실습

### Step 1: 휘발성 데이터 수집

> **실습 목적**: 인시던트 발생 시 가장 먼저 사라지는 휘발성 데이터를 신속하게 수집한다. RFC 3227의 수집 순서를 따른다.
>
> **배우는 것**: 프로세스, 네트워크, 메모리 상태 수집 기법

```bash
# 증거 저장 디렉토리 생성
EVIDENCE_DIR="/tmp/evidence_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EVIDENCE_DIR"
echo "증거 디렉토리: $EVIDENCE_DIR"

# 1. 현재 프로세스 목록 수집 (휘발성 높음)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ps auxf" > "$EVIDENCE_DIR/ps_full.txt"
echo "프로세스 목록 수집 완료: $(wc -l < "$EVIDENCE_DIR/ps_full.txt") lines"

# 2. 네트워크 연결 상태 수집 (휘발성 높음)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ss -tnpa" > "$EVIDENCE_DIR/network_connections.txt"
echo "네트워크 연결 수집 완료"

# 3. 열린 파일 목록 수집
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S lsof -i -n 2>/dev/null | head -50" > "$EVIDENCE_DIR/open_files.txt"
echo "열린 파일 목록 수집 완료"

# 4. 라우팅 테이블 수집
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ip route" > "$EVIDENCE_DIR/routing_table.txt"
echo "라우팅 테이블 수집 완료"

# 5. ARP 캐시 수집 (최근 통신 호스트)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ip neigh" > "$EVIDENCE_DIR/arp_cache.txt"
echo "ARP 캐시 수집 완료"

# 6. 환경 변수 수집 (악성코드가 환경 변수 활용 가능)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "env" > "$EVIDENCE_DIR/environment.txt"
echo "환경 변수 수집 완료"

# 수집 결과 요약
echo "=== 수집된 증거 파일 ==="
ls -la "$EVIDENCE_DIR"/
```

> **결과 해석**:
> - `ps auxf`: 트리 형태로 모든 프로세스를 표시. 의심 프로세스의 부모-자식 관계를 파악할 수 있다
> - `ss -tnpa`: 모든 TCP 연결과 연결된 프로세스를 표시. 외부 C2 연결을 식별한다
> - `lsof -i -n`: 네트워크 소켓을 열고 있는 프로세스를 표시. 리버스 셸 탐지에 유용하다
> - ARP 캐시: 최근 통신한 호스트를 보여준다. 횡적 이동 흔적을 찾을 수 있다
>
> **실전 활용**: 이 데이터는 전원을 끄거나 프로세스를 종료하면 사라진다. 봉쇄 조치(kill 등)를 수행하기 전에 반드시 먼저 수집해야 한다.
>
> **명령어 해설**:
> - `ps auxf`: a(모든 사용자), u(상세), x(터미널 없는 프로세스), f(트리 형태)
> - `ss -tnpa`: t(TCP), n(숫자), p(프로세스), a(모든 상태)
> - `lsof -i -n`: i(네트워크 파일), n(DNS 해석 안 함)
>
> **트러블슈팅**:
> - SSH 접속 불가: 이미 격리된 상태일 수 있음 → 관리 IP 예외 확인
> - lsof 권한 부족: sudo 없이 실행하면 자기 프로세스만 보임 → sudo 필수

### Step 2: 로그 수집 및 해시 보존

> **실습 목적**: 비휘발성 증거(로그 파일)를 수집하고 무결성을 보장하는 해시값을 기록한다.
>
> **배우는 것**: 로그 파일 수집, SHA-256 해시 계산, Chain of Custody 기록

```bash
# 증거 디렉토리 설정
EVIDENCE_DIR="/tmp/evidence_$(date +%Y%m%d)"
mkdir -p "$EVIDENCE_DIR/logs"

# 주요 로그 파일 수집 (web 서버)
for logfile in auth.log syslog kern.log; do
  sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
    "cat /var/log/$logfile 2>/dev/null" > "$EVIDENCE_DIR/logs/$logfile"
  echo "수집: $logfile ($(wc -c < "$EVIDENCE_DIR/logs/$logfile") bytes)"
done

# Apache 로그 수집
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /var/log/apache2/access.log 2>/dev/null" > "$EVIDENCE_DIR/logs/apache_access.log"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /var/log/apache2/error.log 2>/dev/null" > "$EVIDENCE_DIR/logs/apache_error.log"
echo "Apache 로그 수집 완료"

# 해시값 계산 (무결성 보장)
echo "=== 증거 해시값 (SHA-256) ===" > "$EVIDENCE_DIR/hash_manifest.txt"
echo "생성 시각: $(date '+%Y-%m-%d %H:%M:%S')" >> "$EVIDENCE_DIR/hash_manifest.txt"
echo "---" >> "$EVIDENCE_DIR/hash_manifest.txt"
for file in "$EVIDENCE_DIR"/logs/*; do
  sha256sum "$file" >> "$EVIDENCE_DIR/hash_manifest.txt"
done
cat "$EVIDENCE_DIR/hash_manifest.txt"
# 예상 출력:
# === 증거 해시값 (SHA-256) ===
# 생성 시각: 2026-04-03 14:35:22
# ---
# a1b2c3d4... /tmp/evidence_20260403/logs/auth.log
# e5f6g7h8... /tmp/evidence_20260403/logs/syslog
# ...

# Chain of Custody 기록 생성
cat << EOF > "$EVIDENCE_DIR/chain_of_custody.txt"
=== Chain of Custody Record ===
인시던트 ID: IR-$(date +%Y%m%d)-001
수집 일시:   $(date '+%Y-%m-%d %H:%M:%S %Z')
수집자:      $(whoami)@$(hostname)
수집 대상:   10.20.30.80 (web server)
수집 방법:   SSH(sshpass)를 통한 원격 파일 복사
사유:        인시던트 대응 — 의심 침해 조사

수집 파일 목록:
$(ls -la "$EVIDENCE_DIR"/logs/ 2>/dev/null)

해시 매니페스트: hash_manifest.txt
검증 명령:      sha256sum -c hash_manifest.txt
EOF
echo "Chain of Custody 기록 완료"
```

> **결과 해석**:
> - SHA-256 해시: 파일이 수정되지 않았음을 증명한다. 법적 증거 능력을 위해 필수
> - Chain of Custody: 누가, 언제, 어떤 방법으로 증거를 수집했는지 기록한다
> - 해시 매니페스트: 나중에 `sha256sum -c hash_manifest.txt`로 일괄 검증 가능
>
> **실전 활용**: 실무 포렌식에서는 모든 증거 파일에 해시를 기록하고, 분석 과정에서 원본을 변경하지 않도록 복사본에서만 작업한다. 법적 증거로 사용하려면 Chain of Custody가 완벽해야 한다.
>
> **명령어 해설**:
> - `sha256sum <file>`: SHA-256 해시값 계산 (MD5보다 충돌 저항성이 강력)
> - `sha256sum -c <manifest>`: 매니페스트 파일로 해시 일괄 검증
>
> **트러블슈팅**:
> - 로그 파일이 비어 있는 경우: logrotate에 의해 아카이브됨 → `.gz` 파일도 수집 (`zcat`)
> - 해시 불일치: 수집 중 로그가 추가 기록된 경우 → 원격에서 먼저 해시 후 복사

### Step 3: 시스템 상태 스냅샷

> **실습 목적**: 현재 시스템의 전체 상태를 스냅샷으로 보존하여 사후 분석에 활용한다.
>
> **배우는 것**: 사용자, crontab, 서비스, 설정 파일 등 시스템 전반의 상태 수집

```bash
# 증거 디렉토리
EVIDENCE_DIR="/tmp/evidence_$(date +%Y%m%d)"
mkdir -p "$EVIDENCE_DIR/system"

# 사용자 계정 목록 (백도어 계정 탐지)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /etc/passwd" > "$EVIDENCE_DIR/system/passwd"
# 로그인 가능한 계정만 필터링
grep -v "nologin\|false" "$EVIDENCE_DIR/system/passwd" | \
  awk -F: '{print $1, $3, $6, $7}'
# 예상 출력:
# root 0 /root /bin/bash
# web 1000 /home/web /bin/bash
# (백도어 계정이 있다면 여기서 발견)

# 예약된 작업 확인 (지속성 메커니즘 탐지)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S crontab -l 2>/dev/null; \
   echo '--- system crontab ---'; \
   echo 1 | sudo -S cat /etc/crontab 2>/dev/null; \
   echo '--- cron.d ---'; \
   echo 1 | sudo -S ls -la /etc/cron.d/ 2>/dev/null" > "$EVIDENCE_DIR/system/crontabs.txt"
echo "크론탭 수집 완료"

# 실행 중인 서비스 목록
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "systemctl list-units --type=service --state=running --no-pager 2>/dev/null" \
  > "$EVIDENCE_DIR/system/services.txt"
echo "서비스 목록 수집 완료"

# SSH 설정 및 인증 키
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /etc/ssh/sshd_config 2>/dev/null" > "$EVIDENCE_DIR/system/sshd_config"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat ~/.ssh/authorized_keys 2>/dev/null" > "$EVIDENCE_DIR/system/authorized_keys"
echo "SSH 설정 수집 완료"

# 최근 변경된 파일 (최근 24시간)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "find / -mtime -1 -type f 2>/dev/null | \
   grep -v '/proc\|/sys\|/run\|/dev' | head -50" \
  > "$EVIDENCE_DIR/system/recent_files.txt"
echo "최근 변경 파일 수집 완료"

# SUID 파일 목록 (권한 상승 백도어 탐지)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S find / -perm -4000 -type f 2>/dev/null" \
  > "$EVIDENCE_DIR/system/suid_files.txt"
echo "SUID 파일 목록 수집 완료"

# 결과 요약
echo "=== 시스템 스냅샷 수집 완료 ==="
ls -la "$EVIDENCE_DIR"/system/
```

> **결과 해석**:
> - `/etc/passwd`에서 비정상 사용자 계정 발견 시 백도어 가능성이 높다
> - crontab에 의심스러운 항목이 있으면 지속성(Persistence) 메커니즘이다
> - `authorized_keys`에 알 수 없는 키가 있으면 공격자의 SSH 키이다
> - 최근 변경 파일 목록에서 `/tmp`나 `/dev/shm`의 실행 파일은 악성코드 의심
> - SUID 목록에서 `/usr/`, `/bin/` 이외 경로의 파일은 백도어 가능성
>
> **실전 활용**: 이 스냅샷을 감염 전 기준선(Baseline)과 비교하면 공격자가 변경한 내용을 정확히 파악할 수 있다. Week 10에서 기준선을 만든다.
>
> **명령어 해설**:
> - `find / -mtime -1 -type f`: 최근 1일(24시간) 이내 수정된 일반 파일 검색
> - `grep -v '/proc\|/sys\|/run'`: 가상 파일시스템 제외 (항상 변경됨)
> - `find / -perm -4000`: SUID 비트가 설정된 파일 검색
>
> **트러블슈팅**:
> - find 결과가 너무 많은 경우: `-mmin -60`으로 1시간으로 제한
> - 권한 부족: `sudo find`로 실행하거나 접근 가능한 경로만 검색

## 실습 3.3: OpsClaw를 활용한 자동화된 증거 수집

### Step 1: 멀티 호스트 증거 자동 수집

> **실습 목적**: OpsClaw의 execute-plan을 활용하여 여러 서버의 증거를 동시에 자동 수집한다.
>
> **배우는 것**: OpsClaw를 통한 멀티 호스트 증거 수집 오케스트레이션

```bash
# OpsClaw 프로젝트 생성
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week09-ir-evidence","request_text":"인시던트 대응 증거 수집","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Project ID: $PID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 증거 수집 태스크 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"web 프로세스 수집","instruction_prompt":"ps auxf","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":2,"title":"web 네트워크 수집","instruction_prompt":"ss -tnpa","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":3,"title":"web 로그인 로그","instruction_prompt":"tail -100 /var/log/auth.log 2>/dev/null || echo no auth.log","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":4,"title":"secu 방화벽 로그","instruction_prompt":"dmesg | grep -i nft | tail -20 2>/dev/null || echo no nft log","risk_level":"low","subagent_url":"http://10.20.30.1:8002"},
      {"order":5,"title":"web SUID 감사","instruction_prompt":"find / -perm -4000 -type f 2>/dev/null | head -30","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]}')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]:20s} -> {t[\"status\"]}')
"
# 예상 출력:
# 결과: success
#   [1] web 프로세스 수집     -> ok
#   [2] web 네트워크 수집     -> ok
#   [3] web 로그인 로그       -> ok
#   [4] secu 방화벽 로그      -> ok
#   [5] web SUID 감사        -> ok
```

> **결과 해석**: OpsClaw를 통해 실행하면 모든 증거가 evidence로 자동 기록되어 추적 가능하다. PoW 블록도 자동 생성되어 작업 이력이 블록체인에 보존된다.
>
> **실전 활용**: 다수의 서버에서 동시에 증거를 수집해야 할 때 수동으로 하면 시간이 오래 걸린다. OpsClaw 자동화로 수 분 내에 전체 인프라의 증거를 확보할 수 있다.

---

# Part 4: 복구 + 사후 분석 실습 (30분)

## 실습 4.1: 시스템 복구 절차

### Step 1: 악성 흔적 제거 (근절)

> **실습 목적**: 공격자가 남긴 백도어, 악성 사용자, 지속성 메커니즘을 식별하고 제거한다.
>
> **배우는 것**: 백도어 탐지 기법과 안전한 제거 절차

```bash
# 시나리오: web 서버에서 다음 침해 흔적을 발견했다고 가정
# 1) 백도어 사용자 'backdoor' 생성됨
# 2) /tmp/.hidden에 리버스 셸 바이너리
# 3) crontab에 지속성 설정

# 백도어 사용자 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "grep -E 'bash|sh$' /etc/passwd | grep -v 'root\|web\|sshd\|nologin'"
# 예상 출력: (백도어 사용자가 있다면 여기서 표시)

# 숨겨진 파일 탐지 (악성코드가 자주 숨는 경로)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "find /tmp /var/tmp /dev/shm -name '.*' -type f 2>/dev/null"
# 예상 출력: /tmp/.hidden 등 숨겨진 파일 목록

# 의심스러운 crontab 항목 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S crontab -l 2>/dev/null"
# 예상 출력: (악성 cron 항목이 있다면 표시)

# SUID 비트 설정된 의심 파일 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S find / -perm -4000 -type f 2>/dev/null | \
   grep -v '/usr/\|/bin/\|/sbin/'"
# 예상 출력: 비표준 경로의 SUID 파일 (백도어 가능성)

# SSH authorized_keys 확인 (공격자 키)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S find /home -name authorized_keys -exec cat {} \; 2>/dev/null"
# 예상 출력: 등록된 SSH 공개키 목록

# 근절 조치 예시 (실습 환경에서만 수행)
# sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
#   "echo 1 | sudo -S userdel -r backdoor 2>/dev/null"
# sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
#   "echo 1 | sudo -S rm -f /tmp/.hidden 2>/dev/null"
echo "근절 조치 시뮬레이션 완료 (주석 해제하여 실제 수행)"
```

> **결과 해석**:
> - `/etc/passwd`에서 비표준 셸을 가진 알 수 없는 사용자는 백도어일 가능성이 높다
> - `/tmp`, `/var/tmp`, `/dev/shm`의 숨겨진 파일은 악성코드의 일반적인 위치이다
> - 비표준 경로의 SUID 파일은 권한 상승 백도어일 수 있다
> - authorized_keys에 알 수 없는 키가 있으면 공격자의 지속적 접근 수단이다
>
> **실전 활용**: 근절은 반드시 증거 수집 이후에 수행해야 한다. 먼저 삭제하면 포렌식 분석이 불가능해진다. "증거 먼저, 삭제 나중" 원칙을 준수한다.
>
> **명령어 해설**:
> - `find / -perm -4000`: SUID 비트가 설정된 파일 검색 (-4000은 SUID 비트)
> - `userdel -r`: 사용자 계정과 홈 디렉토리를 함께 삭제
> - `grep -v 'root\|web\|sshd'`: 정상 계정 제외
>
> **트러블슈팅**:
> - userdel 실패: 사용자가 현재 로그인 중 → `pkill -u <user>` 후 재시도
> - SUID 파일이 정상인지 구분: `dpkg -S <file>`로 패키지 소속 확인 (Debian/Ubuntu)

### Step 2: 서비스 복구 및 검증

> **실습 목적**: 근절 후 서비스를 안전하게 재시작하고 정상 동작을 검증한다.
>
> **배우는 것**: 서비스 복구 순서, 기능 검증, 단계적 복원 전략

```bash
# 서비스 상태 확인 (web 서버)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "systemctl status apache2 2>/dev/null | head -5; \
   echo '---'; \
   systemctl status docker 2>/dev/null | head -5"
# 예상 출력: 각 서비스의 현재 상태

# 웹 서비스 정상 동작 확인
echo "=== 서비스 가용성 확인 ==="
HTTP_80=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://10.20.30.80:80/)
HTTP_3000=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://10.20.30.80:3000/)
echo "Apache (80):     HTTP $HTTP_80"
echo "JuiceShop (3000): HTTP $HTTP_3000"

# SSH 접속 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 'SSH 접속 정상'" 2>/dev/null || echo "SSH 접속 실패"

# 포트 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ss -tlnp 2>/dev/null | grep -E ':(22|80|3000|8002)'"
# 예상 출력:
# LISTEN 0 128 *:22    *:*   users:(("sshd",...))
# LISTEN 0 128 *:80    *:*   users:(("apache2",...))
# LISTEN 0 128 *:3000  *:*   users:(("node",...))
# LISTEN 0 128 *:8002  *:*   users:(("python",...))

echo "=== 서비스 복구 검증 완료 ==="
```

> **결과 해석**:
> - HTTP 200 또는 403: 웹 서비스가 정상적으로 응답한다
> - `ss -tlnp`: 예상되는 포트에서 예상되는 프로세스가 LISTEN 상태이다
> - 모든 서비스가 정상이면 단계적으로 외부 접근을 허용한다
>
> **실전 활용**: 복구 후 최소 24시간은 집중 모니터링을 수행하여 재감염 징후를 관찰해야 한다. 모니터링 없이 복구를 완료하면 안 된다.
>
> **명령어 해설**:
> - `curl -s -o /dev/null -w "%{http_code}"`: 응답 본문은 버리고 상태 코드만 출력
> - `ss -tlnp`: t(TCP), l(LISTEN), n(숫자), p(프로세스)
>
> **트러블슈팅**:
> - HTTP 500: 서비스 내부 오류 → `journalctl -u apache2 -n 20`으로 로그 확인
> - 포트 LISTEN 없음: 서비스가 시작되지 않음 → `systemctl start <service>` 후 `journalctl`

## 실습 4.2: 사후 분석 및 타임라인 재구성

### Step 1: 로그 기반 타임라인 작성

> **실습 목적**: 여러 소스의 로그를 통합하여 인시던트의 시간순 타임라인을 재구성한다.
>
> **배우는 것**: 다중 소스 로그 통합, 시간 동기화, 이벤트 상관분석

```bash
# auth.log에서 인증 이벤트 추출 (web 서버)
echo "=== 인증 이벤트 타임라인 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "grep -E 'Failed|Accepted|session opened|session closed|useradd|usermod|passwd' \
   /var/log/auth.log 2>/dev/null | tail -30"
# 예상 출력:
# Apr  3 14:30:05 web sshd[1234]: Failed password for root from 10.20.30.201
# Apr  3 14:30:30 web sshd[1234]: Accepted password for web from 10.20.30.201
# ...

# syslog에서 시스템 이벤트 추출
echo ""
echo "=== 시스템 이벤트 타임라인 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "grep -E 'started|stopped|error|warning|cron' /var/log/syslog 2>/dev/null | tail -20"

# Apache 액세스 로그에서 의심 요청 추출
echo ""
echo "=== 웹 의심 요청 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "grep -iE 'POST.*upload|shell|cmd|exec|union|select|script' \
   /var/log/apache2/access.log 2>/dev/null | tail -20"
# 예상 출력: 웹셸 업로드, SQL Injection, XSS 시도 등

# Suricata IDS 알림 확인
echo ""
echo "=== IDS 알림 타임라인 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "tail -30 /var/log/suricata/fast.log 2>/dev/null || echo 'Suricata 로그 없음'"

echo ""
echo "=== 타임라인 재구성 완료 ==="
```

> **결과 해석**:
> - `Failed password` 반복: 브루트포스 공격 시도
> - `Accepted password` 직후 `useradd`: 침투 성공 후 백도어 계정 생성
> - POST upload 요청: 웹셸 업로드 시도
> - Suricata 알림과 시스템 로그를 시간순으로 정렬하면 공격의 전체 흐름이 보인다
>
> **실전 활용**: 타임라인 재구성은 사후 보고서의 핵심이다. "언제, 무엇이, 왜 발생했는지"를 명확히 설명할 수 있어야 한다.
>
> **명령어 해설**:
> - `grep -E`: 확장 정규식 사용 (여러 패턴 OR 매칭)
> - `grep -iE`: 대소문자 무시 + 확장 정규식
>
> **트러블슈팅**:
> - 시간대 불일치: 서버 간 시간 동기화 확인 → `date` 명령으로 비교
> - 로그 로테이션: 이전 로그는 `.1` 또는 `.gz` 형태 → `zgrep`으로 검색

### Step 2: ATT&CK 매핑 보고서 작성

> **실습 목적**: 수집한 증거를 MITRE ATT&CK 프레임워크에 매핑하여 공격자의 TTP를 분류한다.
>
> **배우는 것**: ATT&CK 매핑 실무, 인시던트 보고서의 TTP 섹션 작성

```bash
# ATT&CK 매핑 보고서 템플릿
cat << 'REPORT'
=== 인시던트 사후 분석 보고서 ===

1. 개요
   - 인시던트 ID: IR-2026-001
   - 발생 일시: 2026-04-03 14:30:00 KST
   - 탐지 일시: 2026-04-03 14:32:00 KST
   - 탐지 지연: 2분
   - 심각도: High
   - 영향 범위: web 서버 (10.20.30.80)

2. ATT&CK TTP 매핑

   전술                  기법                     증거
   ------------------------------------------------------
   TA0043 Reconnaissance T1595.001 Scanning IP    IDS: ET SCAN 알림
   TA0001 Initial Access T1190 Exploit Public App Apache access.log
   TA0002 Execution      T1059.004 Unix Shell     ps: /tmp/.hidden
   TA0003 Persistence    T1136.001 Local Account  /etc/passwd: backdoor
   TA0003 Persistence    T1053.003 Cron           crontab: */5 curl...
   TA0005 Defense Evasion T1070.004 File Deletion  syslog: rm 흔적
   TA0006 Credential     T1110.001 Brute Force    auth.log: 10회 실패
   TA0008 Lateral Move   T1021.004 SSH            ss: 내부 SSH 연결
   TA0010 Exfiltration   T1041 Exfil Over C2      ss: 외부 4444 연결

3. 타임라인 요약

   14:30:00  공격 시작 — SSH 브루트포스 (10회 실패 후 성공)
   14:30:30  초기 접근 — www-data 계정으로 로그인 성공
   14:30:45  웹셸 업로드 — POST /upload.php 200
   14:31:00  권한 상승 — 로컬 취약점 악용
   14:31:10  지속성 확보 — backdoor 계정 생성 + cron 설정
   14:31:30  C2 연결 — 외부 서버로 리버스 셸 수립
   14:32:00  탐지 — Suricata에서 리버스 셸 패턴 탐지
   14:32:05  봉쇄 — nftables로 외부 통신 차단
   14:32:10  근절 — 악성 프로세스 종료, 계정 삭제

4. 교훈 (Lessons Learned)
   - SSH 비밀번호 인증이 활성화되어 브루트포스에 취약했음
   - 파일 업로드 검증이 미흡하여 웹셸 업로드 가능했음
   - Suricata 탐지까지 2분 소요 — 임계값 조정 필요
   - 격리까지 추가 5초 소요 — 자동화 스크립트 필요

5. 개선 권고
   - SSH 비밀번호 인증 비활성화 → 키 기반 인증만 허용
   - 웹 업로드 디렉토리 실행 권한 제거
   - Suricata 룰 민감도 상향
   - 자동 격리 스크립트 구현 (탐지 즉시 nftables 차단)
   - fail2ban 설치 (SSH 브루트포스 자동 차단)
REPORT
```

> **실전 활용**: 이 보고서 형태는 실제 기업의 인시던트 사후 분석 보고서와 동일한 구조이다. MITRE ATT&CK 매핑은 업계 표준으로, 다른 조직과 위협 정보를 공유할 때도 활용된다. STIX/TAXII 형식으로 변환하여 CTI(Cyber Threat Intelligence) 플랫폼에 공유할 수 있다.

### Step 3: OpsClaw 완료 보고서

> **실습 목적**: OpsClaw에 인시던트 대응 결과를 완료 보고서로 기록한다.
>
> **배우는 것**: OpsClaw completion-report API 활용법

```bash
# 앞서 생성한 프로젝트 ID 사용 (변수 PID)
curl -s -X POST "http://localhost:8000/projects/$PID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "summary": "인시던트 대응 실습 완료 — NIST IR 프레임워크 전 과정 수행",
    "outcome": "success",
    "work_details": [
      "Phase 1: nftables 격리 — web 서버 외부 통신 차단/복원",
      "Phase 2: RFC 3227 순서 증거 수집 — 프로세스/네트워크/로그/시스템",
      "Phase 3: SHA-256 해시 및 Chain of Custody 기록",
      "Phase 4: 악성 흔적 탐지 — 백도어 계정/SUID/cron",
      "Phase 5: 서비스 복구 및 정상 동작 검증",
      "Phase 6: ATT&CK 매핑 기반 사후 분석 보고서 작성"
    ]
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'보고서 상태: {d.get(\"status\",\"ok\")}')
"
# 예상 출력: 보고서 상태: ok
```

> **결과 해석**: OpsClaw에 모든 작업 이력이 기록되어 감사(Audit) 추적이 가능하다. 실무에서는 이 증적이 규정 준수(Compliance) 증거로 활용된다.

---

## 검증 체크리스트
- [ ] NIST SP 800-61의 4단계를 순서대로 설명할 수 있는가
- [ ] 인시던트 심각도 등급을 분류하고 적절한 대응 시간을 지정할 수 있는가
- [ ] nftables로 감염 호스트를 네트워크 격리하고 관리 접근은 유지할 수 있는가
- [ ] 격리 전 방화벽 규칙을 백업하고 격리 해제 후 복원할 수 있는가
- [ ] RFC 3227 휘발성 순서에 따라 증거를 수집할 수 있는가
- [ ] 수집한 증거의 SHA-256 해시를 계산하고 매니페스트를 작성할 수 있는가
- [ ] Chain of Custody 기록을 완전하게 작성할 수 있는가
- [ ] 백도어 계정, 숨겨진 파일, SUID 백도어를 탐지할 수 있는가
- [ ] 서비스를 안전하게 복구하고 정상 동작을 검증할 수 있는가
- [ ] 다중 소스 로그를 통합하여 타임라인을 재구성할 수 있는가
- [ ] MITRE ATT&CK에 매핑하여 TTP를 분류하고 보고서를 작성할 수 있는가

## 자가 점검 퀴즈

1. NIST SP 800-61의 4단계를 순서대로 나열하고 각 단계의 핵심 활동을 1줄로 설명하라.

2. RFC 3227에 따른 증거 수집 순서에서 메모리(RAM)를 디스크보다 먼저 수집해야 하는 이유를 설명하라.

3. 네트워크 격리(Network Isolation)와 프로세스 종료(Process Kill) 중 어떤 봉쇄를 먼저 수행해야 하는가? 시나리오별로 설명하라.

4. SHA-256 해시를 이용한 증거 무결성 보장 절차를 단계별로 설명하라.

5. Chain of Custody란 무엇이며, 기록해야 하는 필수 항목 5가지를 나열하라.

6. SUID 비트가 설정된 비표준 경로의 파일이 보안 위험인 이유를 설명하라.

7. 인시던트 사후 분석에서 "Lessons Learned" 회의의 목적과 필수 참석자를 설명하라.

8. `nft flush ruleset`을 원격으로 실행할 때의 위험성과 안전한 대안을 설명하라.

9. 공방전에서 Blue Team이 인시던트를 탐지한 후 가장 먼저 해야 할 3가지 조치를 우선순위 순으로 나열하라.

10. MITRE ATT&CK 매핑이 인시던트 보고서에서 중요한 이유를 3가지 이상 설명하라.

## 과제

### 과제 1: 인시던트 대응 시뮬레이션 (필수)
- web 서버에 대한 가상 침해 시나리오를 설정하고 전체 IR 프로세스를 수행하라
- 수행 내용: 탐지 → 분석 → 격리 → 증거 수집 → 근절 → 복구 → 사후 분석
- 각 단계에서 실행한 명령어와 결과를 캡처하여 보고서 형태로 제출
- MITRE ATT&CK 매핑을 포함할 것 (최소 5개 TTP)

### 과제 2: 자동 격리 스크립트 작성 (선택)
- 특정 IP의 외부 통신을 즉시 차단하는 bash 스크립트를 작성하라
- 입력: 격리 대상 IP, 허용할 관리 IP
- 동작: nftables 격리 규칙 추가, 현재 상태 백업, 격리 확인
- 해제 기능도 포함할 것 (`--release` 옵션)

### 과제 3: 포렌식 수집 자동화 (도전)
- RFC 3227 순서에 따라 원격 호스트의 휘발성/비휘발성 데이터를 자동 수집하는 스크립트를 작성하라
- 수집 데이터: 프로세스, 네트워크, 로그, 사용자, crontab, 최근 변경 파일
- 모든 증거에 SHA-256 해시를 계산하고 매니페스트 파일을 자동 생성할 것
- Chain of Custody 기록도 자동 생성할 것
